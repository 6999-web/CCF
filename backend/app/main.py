from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .config import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MAX_TOKENS, NVIDIA_MODEL, NVIDIA_TIMEOUT, NVIDIA_USE_REMOTE
from .database import Base, SessionLocal, engine, get_db
from .models import (
    AIChatMessage,
    AIChatSession,
    AuditLog,
    ChildProfile,
    ConsultationOrder,
    GameLevel,
    GameSession,
    InterventionPlan,
    KnowledgeArticle,
    Notification,
    QuestionnaireResult,
    ScreeningReport,
    SystemSetting,
    TelemetryEvent,
    User,
)
from .schemas import (
    ArticleRequest,
    AuthResponse,
    ChatRequest,
    ChildCreateRequest,
    DashboardSnapshot,
    EntryPointCard,
    InterventionPlanRequest,
    LoginRequest,
    NotificationCreateRequest,
    OrderCreateRequest,
    OrderUpdateRequest,
    PortalOverview,
    PublicChatRequest,
    QuestionnaireRequest,
    RegisterParentRequest,
    ScreeningRequest,
    SessionEndRequest,
    SessionPauseRequest,
    SessionStartRequest,
    SettingUpdateRequest,
    UserProfileUpdateRequest,
    SwitchRoleRequest,
    TelemetryRequest,
    TransferRequest,
    UserCreateRequest,
    UserOut,
)
from .security import create_access_token, decode_token, hash_password, verify_password
from .services import (
    build_parent_children_progress,
    build_entry_points,
    build_portal_overview,
    build_public_dashboard,
    calculate_questionnaire_score,
    create_transfer_order,
    ensure_seed_data,
    get_or_create_user_profile,
    generate_ai_answer,
    get_level_questions,
    iso,
    log_audit,
    now,
    risk_label,
    risk_tier,
    search_articles,
    serialize_article,
    serialize_child,
    serialize_level,
    serialize_notification,
    serialize_order,
    serialize_plan,
    serialize_questionnaire,
    serialize_report,
    serialize_session,
    serialize_setting,
    serialize_user_profile,
    serialize_user,
    update_user_profile,
    upsert_setting,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
NVIDIA_CHAT_ENDPOINT = f"{NVIDIA_BASE_URL}/chat/completions"

CURATED_QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "rhyme_match": [
        {
            "id": "cur-rhy-001",
            "prompt": "下面哪一组词语押韵？",
            "options": ["星星 - 月亮", "花朵 - 火锅", "小猫 - 脚套", "风筝 - 白云"],
            "answer": "小猫 - 脚套",
            "skill": "韵脚识别",
            "explanation": "“猫/套”尾音接近，听起来更押韵。",
            "source_basis": {
                "phonological": "rhyme awareness",
                "comprehension": "auditory discrimination",
                "curriculum": "CCSS.ELA-Literacy.RF.1.2",
            },
        },
        {
            "id": "cur-rhy-002",
            "prompt": "“太阳高高照，____轻轻飘”，最适合填入哪个词？",
            "options": ["云朵", "铅笔", "桌子", "篮球"],
            "answer": "云朵",
            "skill": "语境押韵与词义",
            "explanation": "句子描述天空场景，“云朵”最贴合语义与节奏。",
            "source_basis": {
                "phonological": "rhythm and rhyme",
                "comprehension": "context matching",
                "curriculum": "CCSS.ELA-Literacy.RF.1.2",
            },
        },
    ],
    "sentence_complete": [
        {
            "id": "cur-sen-001",
            "prompt": "“小鸟在树上____。” 哪个词最合适？",
            "options": ["唱歌", "游泳", "睡觉", "跳绳"],
            "answer": "唱歌",
            "skill": "句子补全",
            "explanation": "小鸟在树上的常见动作是唱歌，语义最合理。",
            "source_basis": {
                "phonological": "basic decoding",
                "comprehension": "sentence meaning",
                "curriculum": "CCSS.ELA-Literacy.RF.1.4",
            },
        },
        {
            "id": "cur-sen-002",
            "prompt": "“下雨天要记得带____。”",
            "options": ["雨伞", "墨镜", "风筝", "积木"],
            "answer": "雨伞",
            "skill": "生活语境理解",
            "explanation": "下雨天使用雨伞最符合生活常识。",
            "source_basis": {
                "phonological": "word recognition",
                "comprehension": "contextual inference",
                "curriculum": "CCSS.ELA-Literacy.RF.1.4",
            },
        },
    ],
    "story_quiz": [
        {
            "id": "cur-sto-001",
            "prompt": "故事里“小熊把书借给朋友”，最能说明小熊什么品质？",
            "options": ["自私", "友善", "粗心", "懒惰"],
            "answer": "友善",
            "skill": "人物品质判断",
            "explanation": "愿意分享书本通常体现友善与乐于助人。",
            "source_basis": {
                "phonological": "reading fluency",
                "comprehension": "character trait inference",
                "curriculum": "CCSS.ELA-Literacy.RL.1.3",
            },
        },
        {
            "id": "cur-sto-002",
            "prompt": "如果故事结尾写“大家一起把教室整理干净”，最可能发生在什么时候？",
            "options": ["上课前", "活动结束后", "睡觉时", "吃饭时"],
            "answer": "活动结束后",
            "skill": "情节顺序理解",
            "explanation": "“整理干净”通常发生在活动完成后。",
            "source_basis": {
                "phonological": "guided reading",
                "comprehension": "sequence reasoning",
                "curriculum": "CCSS.ELA-Literacy.RL.1.2",
            },
        },
    ],
    "memory_chain": [
        {
            "id": "cur-mat-001",
            "prompt": "一年级数学：7 + 5 等于几？",
            "options": ["10", "11", "12", "13"],
            "answer": "12",
            "skill": "20以内加法",
            "explanation": "7 和 5 合起来是 12。",
            "source_basis": {
                "domain": "math",
                "grade": "grade-1",
                "curriculum": "CN-MATH-1-addition-within-20",
            },
        },
        {
            "id": "cur-mat-002",
            "prompt": "二年级数学：15 - 8 等于几？",
            "options": ["5", "6", "7", "8"],
            "answer": "7",
            "skill": "20以内减法",
            "explanation": "从 15 去掉 8，剩下 7。",
            "source_basis": {
                "domain": "math",
                "grade": "grade-2",
                "curriculum": "CN-MATH-2-subtraction-within-20",
            },
        },
    ],
    "rapid_naming": [
        {
            "id": "cur-eng-001",
            "prompt": "英语启蒙：'apple' 对应哪张图片含义？",
            "options": ["苹果", "香蕉", "橙子", "葡萄"],
            "answer": "苹果",
            "skill": "英语词汇识别",
            "explanation": "apple 的中文是苹果。",
            "source_basis": {
                "domain": "english",
                "grade": "grade-1",
                "curriculum": "CEFR-A1-basic-vocabulary",
            },
        },
        {
            "id": "cur-eng-002",
            "prompt": "英语基础：'I ___ happy.' 填入哪个词最合适？",
            "options": ["am", "is", "are", "be"],
            "answer": "am",
            "skill": "基础语法",
            "explanation": "主语 I 搭配 am。",
            "source_basis": {
                "domain": "english",
                "grade": "grade-2",
                "curriculum": "CEFR-A1-basic-grammar",
            },
        },
    ],
    "word_train": [
        {
            "id": "cur-chn-001",
            "prompt": "语文：下列哪个词语搭配最恰当？",
            "options": ["明亮的阳光", "明亮的声音", "明亮的味道", "明亮的脚步"],
            "answer": "明亮的阳光",
            "skill": "词语搭配",
            "explanation": "“明亮”常与“阳光、灯光”等视觉词搭配。",
            "source_basis": {
                "domain": "chinese",
                "grade": "grade-2",
                "curriculum": "CN-CHN-2-word-collocation",
            },
        },
        {
            "id": "cur-chn-002",
            "prompt": "语文：'他认真地___作业。' 填哪个词最合理？",
            "options": ["完成", "奔跑", "呼吸", "下雨"],
            "answer": "完成",
            "skill": "句子语义理解",
            "explanation": "“完成作业”是固定且合理的语义搭配。",
            "source_basis": {
                "domain": "chinese",
                "grade": "grade-1",
                "curriculum": "CN-CHN-1-sentence-completion",
            },
        },
    ],
}


def resolve_frontend_dir() -> Path | None:
    if (FRONTEND_DIST / "index.html").exists():
        return FRONTEND_DIST
    if (FRONTEND_ROOT / "index.html").exists():
        return FRONTEND_ROOT
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_seed_data(db)
    yield


app = FastAPI(title="星萌乐学统一平台", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5052", "http://101.33.210.169:5052", "http://localhost:5051", "http://101.33.210.169:5051", "http://127.0.0.1:5052"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

public_router = APIRouter(prefix="/public", tags=["public"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])
child_router = APIRouter(prefix="/child", tags=["child"])
parent_router = APIRouter(prefix="/parent", tags=["parent"])
counselor_router = APIRouter(prefix="/counselor", tags=["counselor"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
ai_router = APIRouter(prefix="/ai", tags=["ai"])
screening_router = APIRouter(prefix="/screening", tags=["screening"])
knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])
games_router = APIRouter(prefix="/games", tags=["games"])
legacy_router = APIRouter(tags=["legacy"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


@dataclass
class AuthContext:
    user: User
    payload: dict[str, Any]


def token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    value = authorization.strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value


def get_current_context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> AuthContext:
    token = token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="登录令牌无效") from exc
    user = db.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return AuthContext(user=user, payload=payload)


def build_auth_payload(db: Session, user: User, entry_role: str | None = None, portal: str | None = None) -> dict[str, Any]:
    token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=entry_role or user.role,
        allowed_roles=user.allowed_roles or [],
        portal=portal or user.role,
        extra={"display_name": user.display_name},
    )
    profile = get_or_create_user_profile(db, user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
        "profile": serialize_user_profile(profile),
        "portal": portal or user.role,
        "entry_role": entry_role or user.role,
    }


def ensure_role_allowed(user: User, requested_role: str | None) -> str:
    role = requested_role or user.role
    allowed = set(user.allowed_roles or [])
    if role == user.role or role in allowed:
        return role
    raise HTTPException(status_code=403, detail=f"褰撳墠璐﹀彿涓嶆敮鎸佽鑹?{role}")


def merge_curated_questions(level_code: str, base_questions: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    curated = CURATED_QUESTION_BANK.get(level_code, [])
    if not curated:
        merged = base_questions[:count]
        for item in merged:
            item.setdefault("difficulty", "easy")
            item.setdefault("ability_tags", [item.get("skill", "综合能力")])
            item.setdefault("source_tag", "internal_core")
            item.setdefault("hint", "先排除明显不合理选项，再结合句意作答。")
            item.setdefault("age_band", "6-10")
        return merged

    existing_ids = {str(item.get("id", "")) for item in base_questions}
    merged = list(base_questions)
    for item in curated:
        if str(item.get("id", "")) not in existing_ids:
            merged.append(
                {
                    **item,
                    "difficulty": item.get("difficulty", "easy"),
                    "ability_tags": item.get("ability_tags", [item.get("skill", "综合能力")]),
                    "source_tag": item.get("source_tag", "curated_public_rewrite"),
                    "hint": item.get("hint", "先读题干，再排除不符合语境的选项。"),
                    "age_band": item.get("age_band", "6-10"),
                }
            )
    merged = merged[:count]
    for item in merged:
        item.setdefault("difficulty", "easy")
        item.setdefault("ability_tags", [item.get("skill", "综合能力")])
        item.setdefault("source_tag", "internal_core")
        item.setdefault("hint", "先排除明显不合理选项，再结合句意作答。")
        item.setdefault("age_band", "6-10")
    return merged


def generate_ai_answer_with_nvidia(question: str, role: str = "parent", style_profile: str = "parent_calm") -> dict[str, Any] | None:
    runtime_key = os.getenv("NVIDIA_API_KEY") or NVIDIA_API_KEY
    if not NVIDIA_USE_REMOTE or not runtime_key:
        return None

    system_prompt = (
        "你是‘悦读相伴’儿童学习助手。语气必须友好、简短、积极。"
        "面向儿童时优先鼓励与引导，不输出危险建议，不输出成人化内容。"
        "如果用户答错，先鼓励再给出可执行提示。"
    )
    if role == "child" or style_profile == "child_cute":
        system_prompt += " 当前用户是儿童，请使用更简明易懂句子。"
    if style_profile == "parent_calm":
        system_prompt += " 当前用户是家长或老师，请给出结构化、可执行建议。"

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": 0.45,
        "max_tokens": NVIDIA_MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {runtime_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=NVIDIA_TIMEOUT) as client:
            response = client.post(NVIDIA_CHAT_ENDPOINT, json=payload, headers=headers)
        if response.status_code >= 400:
            return None
        data = response.json()
        text = ""
        if data.get("choices"):
            text = (
                data["choices"][0].get("message", {}).get("content")
                or data["choices"][0].get("text")
                or ""
            )
        text = (text or "").strip()
        if not text:
            return None
        return {
            "answer": text,
            "citations": ["nvidia-nim"],
            "engine": "nvidia",
        }
    except Exception:
        return None


def generate_ai_answer_unified(
    db: Session,
    question: str,
    *,
    child_id: str | None = None,
    role: str = "parent",
    user_profile: dict[str, Any] | None = None,
    style_profile: str = "parent_calm",
) -> dict[str, Any]:
    remote = generate_ai_answer_with_nvidia(question, role=role, style_profile=style_profile)
    if remote is not None:
        return remote
    return generate_ai_answer(
        db,
        question,
        child_id=child_id,
        role=role,
        user_profile=user_profile,
    )


def make_user_from_request(payload: UserCreateRequest) -> User:
    return User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role,
        allowed_roles=payload.allowed_roles or [payload.role],
        organization=payload.organization,
        phone=payload.phone,
        status=payload.status,
    )


def create_child_from_request(db: Session, payload: ChildCreateRequest) -> ChildProfile:
    child = ChildProfile(
        user_id=payload.user_id,
        parent_id=payload.parent_id,
        name=payload.name,
        gender=payload.gender,
        age=payload.age,
        grade=payload.grade,
        school=payload.school,
        guardian_name=payload.guardian_name,
        risk_level=payload.risk_level,
        assessment_score=payload.assessment_score,
        learning_tags=payload.learning_tags,
        notes=payload.notes,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def create_screening_from_request(db: Session, payload: ScreeningRequest) -> ScreeningReport:
    report = ScreeningReport(
        child_id=payload.child_id,
        source=payload.source,
        score=payload.score,
        risk_level=payload.risk_level or risk_tier(payload.score),
        dimensions=payload.dimensions,
        conclusion=payload.conclusion,
        recommendations=payload.recommendations,
        report_url=payload.report_url,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def create_order_from_request(db: Session, payload: OrderCreateRequest) -> ConsultationOrder:
    order = ConsultationOrder(
        child_id=payload.child_id,
        parent_id=payload.parent_id,
        counselor_id=payload.counselor_id,
        title=payload.title,
        channel=payload.channel,
        status=payload.status,
        scheduled_at=payload.scheduled_at,
        summary=payload.summary,
        source_portal=payload.source_portal,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def create_plan_from_request(db: Session, payload: InterventionPlanRequest) -> InterventionPlan:
    plan = InterventionPlan(
        child_id=payload.child_id,
        counselor_id=payload.counselor_id,
        title=payload.title,
        template_code=payload.template_code,
        status=payload.status,
        progress=payload.progress,
        tasks=payload.tasks,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def create_article_from_request(db: Session, payload: ArticleRequest) -> KnowledgeArticle:
    article = KnowledgeArticle(
        title=payload.title,
        category=payload.category,
        source=payload.source,
        tags=payload.tags,
        content=payload.content,
        content_type=payload.content_type,
        published=payload.published,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def create_notification_from_request(db: Session, payload: NotificationCreateRequest) -> Notification:
    notification = Notification(
        user_id=payload.user_id,
        title=payload.title,
        content=payload.content,
        type=payload.type,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@app.get("/api/v1/public/health")
@app.get("/api/public/health")
def public_health() -> dict[str, Any]:
    return {"status": "ok", "service": "星萌乐学统一平台"}


@public_router.get("/entry-points")
def api_entry_points() -> dict[str, Any]:
    return build_entry_points()


@public_router.get("/dashboard/overview", response_model=DashboardSnapshot)
def api_dashboard_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    return build_public_dashboard(db)


@public_router.get("/dashboard/trends")
def api_dashboard_trends(db: Session = Depends(get_db)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {"timeline": snapshot["timeline"], "updated_at": snapshot["generated_at"]}


@public_router.get("/dashboard/rankings")
def api_dashboard_rankings(db: Session = Depends(get_db)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {"ranking": snapshot["ranking"], "score_distribution": snapshot["score_distribution"]}


@public_router.get("/dashboard/live")
def api_dashboard_live(db: Session = Depends(get_db)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {"live": snapshot["live"], "alerts": snapshot["alerts"], "updated_at": snapshot["generated_at"]}


@public_router.post("/ai/chat")
def public_ai_chat(payload: PublicChatRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    answer_payload = generate_ai_answer_unified(
        db,
        payload.question,
        child_id=payload.child_id,
        role=payload.role,
        user_profile=None,
        style_profile=payload.style_profile,
    )
    return answer_payload


@app.post("/api/public/ai/chat")
def public_ai_chat_legacy(payload: PublicChatRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    return public_ai_chat(payload, db)


@app.websocket("/api/v1/public/dashboard/stream")
async def dashboard_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            with SessionLocal() as db:
                payload = build_public_dashboard(db)
            await websocket.send_json(payload)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()


@app.websocket("/api/public/dashboard/stream")
async def dashboard_stream_legacy(websocket: WebSocket) -> None:
    await dashboard_stream(websocket)


@auth_router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    selected_role = ensure_role_allowed(user, payload.role)
    portal = payload.portal or user.role
    token_payload = build_auth_payload(db, user, entry_role=selected_role, portal=portal)
    log_audit(db, actor_id=user.id, action="auth.login", target_type="user", target_id=user.id, detail=f"portal={portal}, role={selected_role}")
    return token_payload


@auth_router.post("/register/parent", response_model=AuthResponse)
def register_parent(payload: RegisterParentRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    parent = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role="parent",
        allowed_roles=["parent"],
        phone=payload.phone or "",
        organization="Parent Portal",
        status="active",
    )
    db.add(parent)
    db.flush()
    if payload.child_name:
        child = ChildProfile(
            parent_id=parent.id,
            name=payload.child_name,
            age=payload.child_age or 0,
            school=payload.school or "",
            guardian_name=payload.display_name,
            assessment_score=70,
            risk_level="medium",
            learning_tags=["new"],
            notes="Auto-created child profile from parent registration",
        )
        db.add(child)
    db.commit()
    db.refresh(parent)
    log_audit(db, actor_id=parent.id, action="auth.register.parent", target_type="user", target_id=parent.id, detail="家长注册成功")
    return build_auth_payload(db, parent, entry_role="parent", portal="parent")


@auth_router.get("/me")
def me(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    profile = get_or_create_user_profile(db, auth.user)
    return {
        "user": serialize_user(auth.user),
        "profile": serialize_user_profile(profile),
        "portal": auth.payload.get("portal", auth.user.role),
        "entry_role": auth.payload.get("role", auth.user.role),
    }


@auth_router.get("/profile")
def get_profile(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    profile = get_or_create_user_profile(db, auth.user)
    return {"profile": serialize_user_profile(profile)}


@auth_router.put("/profile")
def put_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    profile = update_user_profile(db, auth.user, payload)
    log_audit(
        db,
        actor_id=auth.user.id,
        action="auth.profile.update",
        target_type="user_profile",
        target_id=profile.id,
        detail=profile.nickname or auth.user.display_name,
    )
    return {"user": serialize_user(auth.user), "profile": serialize_user_profile(profile)}


@auth_router.post("/logout")
def logout(auth: AuthContext = Depends(get_current_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    log_audit(db, actor_id=auth.user.id, action="auth.logout", target_type="user", target_id=auth.user.id)
    return {"success": True}


@auth_router.post("/switch-role", response_model=AuthResponse)
def switch_role(payload: SwitchRoleRequest, auth: AuthContext = Depends(get_current_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    selected_role = ensure_role_allowed(auth.user, payload.role)
    log_audit(db, actor_id=auth.user.id, action="auth.switch_role", target_type="user", target_id=auth.user.id, detail=selected_role)
    return build_auth_payload(db, auth.user, entry_role=selected_role, portal=auth.payload.get("portal", auth.user.role))


def resolve_child_profile(db: Session, auth: AuthContext, child_id: str | None = None) -> ChildProfile | None:
    if child_id:
        child = db.get(ChildProfile, child_id)
        if child is not None:
            if auth.user.role == "child" and child.user_id != auth.user.id:
                raise HTTPException(status_code=403, detail="无权访问该儿童档案")
            if auth.user.role == "parent" and child.parent_id != auth.user.id:
                raise HTTPException(status_code=403, detail="无权访问该儿童档案")
            return child
        child = db.query(ChildProfile).filter(ChildProfile.user_id == child_id).first()
        if child is not None:
            if auth.user.role == "child" and child.user_id != auth.user.id:
                raise HTTPException(status_code=403, detail="无权访问该儿童档案")
            if auth.user.role == "parent" and child.parent_id != auth.user.id:
                raise HTTPException(status_code=403, detail="无权访问该儿童档案")
            return child
        return None
    if auth.user.role == "child":
        return db.query(ChildProfile).filter(ChildProfile.user_id == auth.user.id).first()
    if auth.user.role == "parent":
        return (
            db.query(ChildProfile)
            .filter(ChildProfile.parent_id == auth.user.id)
            .order_by(ChildProfile.created_at.asc())
            .first()
        )
    return db.query(ChildProfile).order_by(ChildProfile.created_at.asc()).first()


@child_router.get("/levels")
def child_levels(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    levels = db.query(GameLevel).order_by(GameLevel.order_index.asc()).all()
    child = resolve_child_profile(db, auth)
    completed_count = 0
    if child:
        completed_count = db.query(GameSession).filter(GameSession.child_id == child.id, GameSession.status == "completed").count()
    return {
        "levels": [serialize_level(level) for level in levels],
        "completed_count": completed_count,
        "child": serialize_child(child) if child else None,
    }


@child_router.get("/level-config/{level_code}")
def child_level_config(level_code: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    level = db.query(GameLevel).filter(GameLevel.code == level_code).one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Not found")
    return serialize_level(level)


def build_level_questions_payload(level: GameLevel, count: int) -> dict[str, Any]:
    questions = get_level_questions(level.code, count=max(count, 8))
    questions = merge_curated_questions(level.code, questions, count=count)
    return {"level": serialize_level(level), "questions": questions, "count": len(questions)}


@child_router.get("/questions/{level_code}")
def child_level_questions(
    level_code: str,
    count: int = 8,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    level = db.query(GameLevel).filter(GameLevel.code == level_code).one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="关卡不存在")
    return build_level_questions_payload(level, count)


@games_router.get("/questions/{level_code}")
def game_level_questions(
    level_code: str,
    count: int = 8,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    level = db.query(GameLevel).filter(GameLevel.code == level_code).one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="关卡不存在")
    return build_level_questions_payload(level, count)

@child_router.post("/session/start")
def child_session_start(payload: SessionStartRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth, payload.child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    level = db.query(GameLevel).filter(GameLevel.code == payload.level_code).one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Not found")
    session = GameSession(
        child_id=child.id,
        level_code=level.code,
        status="active",
        score=0.0,
        duration_seconds=0,
        started_at=now(),
        device=payload.device or "web",
        telemetry_summary={"events": 0, "accuracy": 0.0},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="child.session.start", target_type="game_session", target_id=session.id, detail=level.code)
    return {"session": serialize_session(session), "level": serialize_level(level), "child": serialize_child(child)}


@child_router.post("/session/pause")
def child_session_pause(payload: SessionPauseRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = db.get(GameSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Not found")
    session.status = "paused"
    session.updated_at = now()
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="child.session.pause", target_type="game_session", target_id=session.id, detail=payload.reason or "")
    return {"session": serialize_session(session)}


@child_router.put("/session/end")
def child_session_end(payload: SessionEndRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = db.get(GameSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Not found")
    session.status = payload.status
    session.score = payload.score if payload.score is not None else session.score
    session.duration_seconds = payload.duration_seconds if payload.duration_seconds is not None else session.duration_seconds
    if payload.telemetry_summary:
        session.telemetry_summary = payload.telemetry_summary
    session.ended_at = now()
    session.updated_at = now()
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="child.session.end", target_type="game_session", target_id=session.id, detail=payload.status)
    return {"session": serialize_session(session)}


@child_router.post("/telemetry")
def child_telemetry(payload: TelemetryRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = db.get(GameSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Not found")
    child = resolve_child_profile(db, auth, payload.child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    event = TelemetryEvent(
        session_id=payload.session_id,
        child_id=child.id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    session.telemetry_summary = dict(session.telemetry_summary or {})
    session.telemetry_summary["events"] = int(session.telemetry_summary.get("events", 0)) + 1
    if payload.score_delta is not None:
        session.score = round(float(session.score or 0) + float(payload.score_delta), 1)
    if payload.duration_seconds is not None:
        session.duration_seconds = int(payload.duration_seconds)
    session.updated_at = now()
    db.add(event)
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="child.telemetry", target_type="telemetry_event", target_id=event.id, detail=payload.event_type)
    return {"event_id": event.id, "session": serialize_session(session)}


@child_router.get("/rewards/status")
def child_reward_status(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    completed_sessions = db.query(GameSession).filter(GameSession.child_id == child.id, GameSession.status == "completed").all()
    unlocked = len(completed_sessions)
    latest_level = completed_sessions[-1].level_code if completed_sessions else None
    return {
        "child": serialize_child(child),
        "unlocked": unlocked,
        "latest_level": latest_level,
        "badge": f"{max(1, unlocked)} 星徽章",
    }


@child_router.post("/rewards/unlock")
def child_reward_unlock(child_id: str | None = None, reward_name: str = "星星徽章", db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    notification = Notification(
        user_id=auth.user.id,
        title="奖励已解锁",
        content=f"{child.name} 获得 {reward_name}",
        type="success",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    log_audit(db, actor_id=auth.user.id, action="child.reward.unlock", target_type="notification", target_id=notification.id, detail=reward_name)
    return {"success": True, "notification": serialize_notification(notification)}


@child_router.get("/reports")
def child_reports(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    reports = db.query(ScreeningReport).filter(ScreeningReport.child_id == child.id).order_by(ScreeningReport.created_at.desc()).all()
    return {"child": serialize_child(child), "reports": [serialize_report(report) for report in reports]}


@child_router.get("/dashboard")
def child_dashboard(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return build_portal_overview(db, auth.user, "child")


@parent_router.get("/children")
def parent_children(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    children = db.query(ChildProfile).filter(ChildProfile.parent_id == auth.user.id).order_by(ChildProfile.created_at.asc()).all()
    if auth.user.role == "management":
        children = db.query(ChildProfile).order_by(ChildProfile.created_at.asc()).all()
    return {"children": [serialize_child(child) for child in children]}


@parent_router.get("/children/progress")
def parent_children_progress(
    include_ai: bool = True,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    return build_parent_children_progress(db, auth.user, include_ai=include_ai)


@parent_router.post("/children")
def parent_create_child(payload: ChildCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    if auth.user.role not in {"parent", "management"}:
        raise HTTPException(status_code=403, detail="鏃犳潈鍒涘缓鍎跨妗ｆ")
    if payload.parent_id is None:
        payload.parent_id = auth.user.id
    child = create_child_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="parent.child.create", target_type="child_profile", target_id=child.id, detail=child.name)
    return {"child": serialize_child(child)}


@parent_router.get("/reports")
def parent_reports(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    children = db.query(ChildProfile).filter(ChildProfile.parent_id == auth.user.id).all()
    if auth.user.role == "management":
        children = db.query(ChildProfile).all()
    child_ids = [child.id for child in children]
    reports = (
        db.query(ScreeningReport)
        .filter(ScreeningReport.child_id.in_(child_ids))
        .order_by(ScreeningReport.created_at.desc())
        .all()
    )
    return {"reports": [serialize_report(report) for report in reports], "children": [serialize_child(child) for child in children]}


@parent_router.post("/questionnaire")
def parent_questionnaire(payload: QuestionnaireRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = db.get(ChildProfile, payload.child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    score, label = calculate_questionnaire_score(payload.answers)
    result = QuestionnaireResult(
        child_id=child.id,
        parent_id=payload.parent_id or auth.user.id,
        answers=payload.answers,
        score=score,
        risk_level=risk_tier(score),
        summary=payload.summary or f"问卷结果：{label}",
    )
    report = ScreeningReport(
        child_id=child.id,
        source="questionnaire",
        score=score,
        risk_level=risk_tier(score),
        dimensions={
            "家长观察": score - 6,
            "阅读速度": score - 9,
            "书写表现": score - 8,
        },
        conclusion=payload.summary or "家长问卷已提交，建议结合人工咨询继续跟进。",
        recommendations=["短时高频训练", "观察书写错误", "联系咨询师复核"],
        report_url=f"/reports/{child.id}-questionnaire.json",
    )
    db.add(result)
    db.add(report)
    db.commit()
    db.refresh(result)
    db.refresh(report)
    log_audit(db, actor_id=auth.user.id, action="parent.questionnaire.submit", target_type="questionnaire", target_id=result.id, detail=child.name)
    return {"questionnaire": serialize_questionnaire(result), "report": serialize_report(report)}


@parent_router.get("/chat/history")
def parent_chat_history(session_id: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = None
    if session_id:
        session = db.get(AIChatSession, session_id)
    else:
        session = (
            db.query(AIChatSession)
            .filter(AIChatSession.user_id == auth.user.id)
            .order_by(AIChatSession.created_at.desc())
            .first()
        )
    if session is None:
        return {"session": None, "messages": []}
    messages = db.query(AIChatMessage).filter(AIChatMessage.session_id == session.id).order_by(AIChatMessage.created_at.asc()).all()
    return {
        "session": {"id": session.id, "topic": session.topic, "role": session.role, "created_at": iso(session.created_at)},
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "citations": msg.citations or [],
                "created_at": iso(msg.created_at),
            }
            for msg in messages
        ],
    }


@parent_router.post("/chat")
def parent_chat(payload: ChatRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = (
        db.query(AIChatSession)
        .filter(AIChatSession.user_id == auth.user.id)
        .order_by(AIChatSession.created_at.desc())
        .first()
    )
    if session is None or (payload.session_id and session.id != payload.session_id):
        session = AIChatSession(user_id=auth.user.id, role=payload.role, topic=payload.question[:40])
        db.add(session)
        db.flush()
    user_message = AIChatMessage(session_id=session.id, sender="user", content=payload.question, citations=[])
    answer_payload = generate_ai_answer_unified(
        db,
        payload.question,
        child_id=payload.child_id,
        role=payload.role or auth.user.role,
        style_profile=payload.style_profile,
    )
    ai_message = AIChatMessage(session_id=session.id, sender="assistant", content=answer_payload["answer"], citations=answer_payload["citations"])
    db.add(user_message)
    db.add(ai_message)
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="parent.chat", target_type="ai_chat_session", target_id=session.id, detail=payload.question[:120])
    return {"session_id": session.id, **answer_payload}


@parent_router.get("/appointments")
def parent_appointments(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    orders = (
        db.query(ConsultationOrder)
        .filter(ConsultationOrder.parent_id == auth.user.id)
        .order_by(ConsultationOrder.created_at.desc())
        .all()
    )
    if auth.user.role == "management":
        orders = db.query(ConsultationOrder).order_by(ConsultationOrder.created_at.desc()).all()
    return {"orders": [serialize_order(order) for order in orders]}


@parent_router.post("/appointments")
def parent_create_appointment(payload: OrderCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    if payload.parent_id is None:
        payload.parent_id = auth.user.id
    if not payload.child_id:
        child = resolve_child_profile(db, auth)
        payload.child_id = child.id if child else None
    order = create_order_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="parent.order.create", target_type="consultation_order", target_id=order.id, detail=order.title)
    return {"order": serialize_order(order)}


@parent_router.get("/knowledge")
def parent_knowledge(q: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    articles = search_articles(db, query=q, limit=20)
    return {"articles": articles}


@parent_router.get("/health")
def parent_health(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    overview = build_portal_overview(db, auth.user, "parent")
    return {"summary": overview["shared"]["summary"], "recent": overview["recent"]}


@counselor_router.get("/orders")
def counselor_orders(status: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    query = db.query(ConsultationOrder).order_by(ConsultationOrder.created_at.desc())
    if status:
        query = query.filter(ConsultationOrder.status == status)
    orders = query.all()
    return {"orders": [serialize_order(order) for order in orders]}


@counselor_router.patch("/orders/{order_id}")
def counselor_update_order(order_id: str, payload: OrderUpdateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    order = db.get(ConsultationOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    if payload.status is not None:
        order.status = payload.status
    if payload.counselor_id is not None:
        order.counselor_id = payload.counselor_id
    if payload.summary is not None:
        order.summary = payload.summary
    if payload.scheduled_at is not None:
        order.scheduled_at = payload.scheduled_at
    order.updated_at = now()
    db.commit()
    db.refresh(order)
    log_audit(db, actor_id=auth.user.id, action="counselor.order.update", target_type="consultation_order", target_id=order.id, detail=order.status)
    return {"order": serialize_order(order)}


@counselor_router.get("/schedules")
def counselor_schedules(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    orders = db.query(ConsultationOrder).order_by(ConsultationOrder.scheduled_at.asc().nullslast()).all()
    schedules = []
    for order in orders:
        schedules.append(
            {
                "order_id": order.id,
                "title": order.title,
                "scheduled_at": iso(order.scheduled_at),
                "status": order.status,
                "child_id": order.child_id,
            }
        )
    return {"schedules": schedules}


@counselor_router.get("/interventions")
def counselor_interventions(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    plans = db.query(InterventionPlan).order_by(InterventionPlan.created_at.desc()).all()
    return {"plans": [serialize_plan(plan) for plan in plans]}


@counselor_router.post("/interventions")
def counselor_create_intervention(payload: InterventionPlanRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    if payload.counselor_id is None:
        payload.counselor_id = auth.user.id
    plan = create_plan_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="counselor.intervention.create", target_type="intervention_plan", target_id=plan.id, detail=plan.title)
    return {"plan": serialize_plan(plan)}


@counselor_router.get("/interventions/templates")
def counselor_templates() -> dict[str, Any]:
    return {
        "templates": [
            {"code": "T1", "name": "基础语音意识训练", "tasks": ["韵脚配对", "音节拍手", "音素捕捉"]},
            {"code": "T2", "name": "汉字识别强化", "tasks": ["找出异类字", "汉字拼图", "词语小火车"]},
            {"code": "T3", "name": "阅读流畅性提升", "tasks": ["快速命名", "句子补全", "故事测验"]},
        ]
    }


@counselor_router.get("/knowledge")
def counselor_knowledge(q: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return {"articles": search_articles(db, query=q, limit=20)}


@counselor_router.get("/statistics/summary")
def counselor_statistics(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {
        "kpis": snapshot["summary"],
        "ranking": snapshot["ranking"][:5],
        "distribution": snapshot["score_distribution"],
        "recent_alerts": snapshot["alerts"],
    }


@screening_router.get("")
def screening_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    reports = db.query(ScreeningReport).order_by(ScreeningReport.created_at.desc()).all()
    return {"reports": [serialize_report(report) for report in reports]}


@screening_router.post("")
def screening_create(payload: ScreeningRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    report = create_screening_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="screening.create", target_type="screening_report", target_id=report.id, detail=report.risk_level)
    return {"report": serialize_report(report)}


@screening_router.get("/{report_id}")
def screening_detail(report_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    report = db.get(ScreeningReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"report": serialize_report(report)}


@knowledge_router.get("")
def knowledge_list(q: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return {"articles": search_articles(db, query=q, limit=50)}


@knowledge_router.post("")
def knowledge_create(payload: ArticleRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    article = create_article_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="knowledge.create", target_type="knowledge_article", target_id=article.id, detail=article.title)
    return {"article": serialize_article(article)}


@ai_router.post("/chat")
def ai_chat(payload: ChatRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = (
        db.query(AIChatSession)
        .filter(AIChatSession.user_id == auth.user.id)
        .order_by(AIChatSession.created_at.desc())
        .first()
    )
    if session is None or (payload.session_id and session.id != payload.session_id):
        session = AIChatSession(user_id=auth.user.id, role=payload.role, topic=payload.question[:40])
        db.add(session)
        db.flush()
    db.add(AIChatMessage(session_id=session.id, sender="user", content=payload.question, citations=[]))
    profile = get_or_create_user_profile(db, auth.user)
    answer_payload = generate_ai_answer_unified(
        db,
        payload.question,
        child_id=payload.child_id,
        role=payload.role or auth.user.role,
        user_profile=serialize_user_profile(profile),
        style_profile=payload.style_profile,
    )
    db.add(AIChatMessage(session_id=session.id, sender="assistant", content=answer_payload["answer"], citations=answer_payload["citations"]))
    db.commit()
    db.refresh(session)
    log_audit(db, actor_id=auth.user.id, action="ai.chat", target_type="ai_chat_session", target_id=session.id, detail=payload.question[:120])
    return {"session_id": session.id, **answer_payload}


@ai_router.post("/transfer")
def ai_transfer(payload: TransferRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    order = create_transfer_order(
        db,
        question=payload.question,
        child_id=payload.child_id,
        parent_id=payload.parent_id or auth.user.id,
        contact=payload.contact,
        reason=payload.reason,
        source_portal=auth.payload.get("portal", auth.user.role),
    )
    notification = Notification(
        user_id=auth.user.id,
        title="宸茶浆浜哄伐鍜ㄨ",
        content=f"咨询单 {order.id} 已创建，咨询师将尽快联系你。",
        type="success",
    )
    db.add(notification)
    db.commit()
    db.refresh(order)
    db.refresh(notification)
    log_audit(db, actor_id=auth.user.id, action="ai.transfer", target_type="consultation_order", target_id=order.id, detail=payload.question[:120])
    return {"order": serialize_order(order), "notification": serialize_notification(notification)}


@notifications_router.get("")
def notifications_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    items = (
        db.query(Notification)
        .filter((Notification.user_id == auth.user.id) | (Notification.user_id.is_(None)))
        .order_by(Notification.created_at.desc())
        .all()
    )
    return {"notifications": [serialize_notification(item) for item in items]}


@notifications_router.post("")
def notifications_create(payload: NotificationCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    notification = create_notification_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="notification.create", target_type="notification", target_id=notification.id, detail=notification.title)
    return {"notification": serialize_notification(notification)}


@notifications_router.patch("")
def notifications_mark_all_read(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    items = db.query(Notification).filter(Notification.user_id == auth.user.id, Notification.read_at.is_(None)).all()
    for item in items:
        item.read_at = now()
    db.commit()
    return {"updated": len(items)}


@notifications_router.patch("/{notification_id}")
def notifications_mark_read(notification_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    item = db.get(Notification, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Not found")
    item.read_at = now()
    db.commit()
    db.refresh(item)
    return {"notification": serialize_notification(item)}


@admin_router.get("/users")
def admin_users(role: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    query = db.query(User).order_by(User.created_at.desc())
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return {"users": [serialize_user(user) for user in users]}


@admin_router.post("/users")
def admin_create_user(payload: UserCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if not payload.password:
        raise HTTPException(status_code=400, detail="密码不能为空")
    user = make_user_from_request(payload)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, actor_id=auth.user.id, action="admin.user.create", target_type="user", target_id=user.id, detail=user.username)
    return {"user": serialize_user(user)}


@admin_router.patch("/users/{user_id}")
def admin_update_user(user_id: str, payload: UserCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Not found")
    user.display_name = payload.display_name
    user.role = payload.role
    user.allowed_roles = payload.allowed_roles or [payload.role]
    user.organization = payload.organization
    user.phone = payload.phone
    user.status = payload.status
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    log_audit(db, actor_id=auth.user.id, action="admin.user.update", target_type="user", target_id=user.id, detail=user.status)
    return {"user": serialize_user(user)}


@admin_router.get("/counselors")
def admin_counselors(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    counselors = db.query(User).filter(User.role.in_(["counselor", "management", "teacher_research"])).order_by(User.created_at.desc()).all()
    return {"counselors": [serialize_user(user) for user in counselors]}


@admin_router.get("/games")
def admin_games(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    levels = db.query(GameLevel).order_by(GameLevel.order_index.asc()).all()
    sessions = db.query(GameSession).order_by(GameSession.created_at.desc()).all()
    return {
        "levels": [serialize_level(level) for level in levels],
        "sessions": [serialize_session(session) for session in sessions[:50]],
    }


@admin_router.get("/articles")
def admin_articles(q: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return {"articles": search_articles(db, query=q, limit=50)}


@admin_router.post("/articles")
def admin_create_article(payload: ArticleRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    article = create_article_from_request(db, payload)
    log_audit(db, actor_id=auth.user.id, action="admin.article.create", target_type="knowledge_article", target_id=article.id, detail=article.title)
    return {"article": serialize_article(article)}


@admin_router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    snapshot["summary"]["users"] = db.query(User).count()
    snapshot["summary"]["articles"] = db.query(KnowledgeArticle).count()
    snapshot["summary"]["audit_logs"] = db.query(AuditLog).count()
    return snapshot


@admin_router.get("/dashboard/screen-data")
def admin_screen_data(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {
        "ranking": snapshot["ranking"],
        "distribution": snapshot["score_distribution"],
        "school_compare": snapshot["school_compare"],
        "live": snapshot["live"],
    }


@admin_router.get("/dashboard/trends")
def admin_trends(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    return {"timeline": snapshot["timeline"], "live": snapshot["live"]}


@admin_router.get("/settings")
def admin_settings(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    items = db.query(SystemSetting).order_by(SystemSetting.key.asc()).all()
    return {"settings": [serialize_setting(item) for item in items]}


@admin_router.put("/settings")
def admin_update_settings(payload: SettingUpdateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    updated = []
    for key, value in payload.items.items():
        setting = upsert_setting(db, key, value)
        updated.append(serialize_setting(setting))
    log_audit(db, actor_id=auth.user.id, action="admin.settings.update", target_type="setting", target_id="*")
    return {"settings": updated}


@admin_router.get("/audit-logs")
def admin_audit_logs(limit: int = 50, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    items = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {
        "logs": [
            {
                "id": item.id,
                "actor_id": item.actor_id,
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "detail": item.detail,
                "created_at": iso(item.created_at),
            }
            for item in items
        ]
    }


@admin_router.get("/orders")
def admin_orders(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    orders = db.query(ConsultationOrder).order_by(ConsultationOrder.created_at.desc()).all()
    return {"orders": [serialize_order(order) for order in orders]}


@admin_router.post("/orders/{order_id}/refund")
def admin_refund_order(order_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    order = db.get(ConsultationOrder, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    order.status = "refunded"
    order.updated_at = now()
    db.commit()
    db.refresh(order)
    log_audit(db, actor_id=auth.user.id, action="admin.order.refund", target_type="consultation_order", target_id=order.id, detail=order.title)
    return {"order": serialize_order(order)}


@games_router.get("/levels")
def game_levels(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    levels = db.query(GameLevel).order_by(GameLevel.order_index.asc()).all()
    return {"levels": [serialize_level(level) for level in levels]}


@games_router.get("/config/{level_id}")
def game_config(level_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    level = db.query(GameLevel).filter((GameLevel.id == level_id) | (GameLevel.code == level_id)).one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Not found")
    return serialize_level(level)


@games_router.post("/records/sync")
def game_records_sync(payload: TelemetryRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = db.get(GameSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Not found")
    event = TelemetryEvent(
        session_id=payload.session_id,
        child_id=payload.child_id,
        event_type=payload.event_type,
        payload=payload.payload,
    )
    session.telemetry_summary = dict(session.telemetry_summary or {})
    session.telemetry_summary["events"] = int(session.telemetry_summary.get("events", 0)) + 1
    if payload.score_delta is not None:
        session.score = round(float(session.score or 0) + float(payload.score_delta), 1)
    if payload.duration_seconds is not None:
        session.duration_seconds = int(payload.duration_seconds)
    db.add(event)
    db.commit()
    db.refresh(session)
    return {"event_id": event.id, "session": serialize_session(session)}


@games_router.post("/records/pause")
def game_records_pause(payload: SessionPauseRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    session = db.get(GameSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Not found")
    session.status = "paused"
    session.updated_at = now()
    db.commit()
    db.refresh(session)
    return {"session": serialize_session(session)}


@games_router.get("/rewards/status")
def game_rewards_status(child_id: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    completed = db.query(GameSession).filter(GameSession.child_id == child.id, GameSession.status == "completed").count()
    return {"child_id": child.id, "completed": completed, "badge": f"{max(1, completed)} 星徽章"}


@games_router.post("/rewards/unlock")
def game_rewards_unlock(child_id: str | None = None, reward_name: str = "星星徽章", db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = resolve_child_profile(db, auth, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    notification = Notification(
        user_id=auth.user.id,
        title="奖励已解锁",
        content=f"{child.name} 获得 {reward_name}",
        type="success",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {"notification": serialize_notification(notification)}


@legacy_router.post("/auth/login")
def legacy_login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    return login(payload, db)


@legacy_router.post("/auth/register")
def legacy_register_parent(payload: RegisterParentRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    return register_parent(payload, db)


@legacy_router.get("/auth/me")
def legacy_me(auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return me(auth)


@legacy_router.post("/auth/logout")
def legacy_logout(auth: AuthContext = Depends(get_current_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    return logout(auth, db)


@legacy_router.post("/auth/switch")
def legacy_switch(payload: SwitchRoleRequest, auth: AuthContext = Depends(get_current_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    return switch_role(payload, auth, db)


@legacy_router.get("/profiles")
def legacy_profiles(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    items = db.query(ChildProfile).order_by(ChildProfile.created_at.desc()).all()
    return {"profiles": [serialize_child(item) for item in items]}


@legacy_router.post("/profiles")
def legacy_create_profile(payload: ChildCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    if payload.parent_id is None and auth.user.role == "parent":
        payload.parent_id = auth.user.id
    child = create_child_from_request(db, payload)
    return {"profile": serialize_child(child)}


@legacy_router.delete("/profiles/{profile_id}")
def legacy_delete_profile(profile_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    child = db.get(ChildProfile, profile_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(child)
    db.commit()
    return {"success": True}


@legacy_router.get("/screening")
def legacy_screening_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return screening_list(db, auth)


@legacy_router.post("/screening")
def legacy_screening_create(payload: ScreeningRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return screening_create(payload, db, auth)


@legacy_router.get("/screening/{report_id}")
def legacy_screening_detail(report_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return screening_detail(report_id, db, auth)


@legacy_router.get("/orders")
def legacy_orders_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return parent_appointments(db, auth)


@legacy_router.post("/orders")
def legacy_orders_create(payload: OrderCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return parent_create_appointment(payload, db, auth)


@legacy_router.patch("/orders/{order_id}")
def legacy_orders_update(order_id: str, payload: OrderUpdateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return counselor_update_order(order_id, payload, db, auth)


@legacy_router.get("/interventions")
def legacy_interventions_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return counselor_interventions(db, auth)


@legacy_router.post("/interventions")
def legacy_interventions_create(payload: InterventionPlanRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return counselor_create_intervention(payload, db, auth)


@legacy_router.get("/interventions/templates")
def legacy_interventions_templates() -> dict[str, Any]:
    return counselor_templates()


@legacy_router.get("/knowledge")
def legacy_knowledge_list(q: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return knowledge_list(q, db, auth)


@legacy_router.post("/knowledge")
def legacy_knowledge_create(payload: ArticleRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return knowledge_create(payload, db, auth)


@legacy_router.post("/ai/chat")
def legacy_ai_chat(payload: ChatRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return ai_chat(payload, db, auth)


@legacy_router.post("/ai/transfer")
def legacy_ai_transfer(payload: TransferRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return ai_transfer(payload, db, auth)


@legacy_router.get("/notifications")
def legacy_notifications_list(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return notifications_list(db, auth)


@legacy_router.post("/notifications")
def legacy_notifications_create(payload: NotificationCreateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return notifications_create(payload, db, auth)


@legacy_router.patch("/notifications")
def legacy_notifications_mark_all_read(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return notifications_mark_all_read(db, auth)


@legacy_router.patch("/notifications/{notification_id}")
def legacy_notifications_mark_read(notification_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return notifications_mark_read(notification_id, db, auth)


@legacy_router.get("/statistics/summary")
def legacy_statistics_summary(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return counselor_statistics(db, auth)


@legacy_router.get("/settings")
def legacy_settings_get(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return admin_settings(db, auth)


@legacy_router.put("/settings")
def legacy_settings_put(payload: SettingUpdateRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return admin_update_settings(payload, db, auth)


@legacy_router.get("/init")
def legacy_init(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_seed_data(db)
    return {"success": True, "message": "示例数据已初始化"}


@legacy_router.get("/games/levels")
def legacy_games_levels(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_levels(db, auth)


@legacy_router.get("/games/config/{level_id}")
def legacy_games_config(level_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_config(level_id, db, auth)


@legacy_router.get("/games/questions/{level_code}")
def legacy_games_questions(
    level_code: str,
    count: int = 8,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    return game_level_questions(level_code, count, db, auth)


@legacy_router.get("/child/questions/{level_code}")
def legacy_child_questions(
    level_code: str,
    count: int = 8,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_context),
) -> dict[str, Any]:
    return child_level_questions(level_code, count, db, auth)


@legacy_router.post("/games/records/sync")
def legacy_games_records_sync(payload: TelemetryRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_records_sync(payload, db, auth)


@legacy_router.post("/games/records/pause")
def legacy_games_records_pause(payload: SessionPauseRequest, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_records_pause(payload, db, auth)


@legacy_router.get("/rewards/status")
def legacy_rewards_status(child_id: str | None = None, db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_rewards_status(child_id, db, auth)


@legacy_router.post("/rewards/unlock")
def legacy_rewards_unlock(child_id: str | None = None, reward_name: str = "星星徽章", db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return game_rewards_unlock(child_id, reward_name, db, auth)


@legacy_router.get("/dashboard")
def legacy_dashboard(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return admin_dashboard(db, auth)


@legacy_router.get("/dashboard/screen-data")
def legacy_dashboard_screen_data(db: Session = Depends(get_db), auth: AuthContext = Depends(get_current_context)) -> dict[str, Any]:
    return admin_screen_data(db, auth)


@app.get("/")
def root() -> Any:
    frontend_dir = resolve_frontend_dir()
    if frontend_dir is not None:
        return FileResponse(frontend_dir / "index.html")
    return {"name": "星萌乐学统一平台", "docs": "/docs", "health": "/api/v1/public/health"}


app.include_router(public_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(child_router, prefix="/api/v1")
app.include_router(parent_router, prefix="/api/v1")
app.include_router(counselor_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(screening_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(games_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(legacy_router, prefix="/api")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> Any:
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
        raise HTTPException(status_code=404, detail="Not Found")

    frontend_dir = resolve_frontend_dir()
    if frontend_dir is None:
        raise HTTPException(status_code=404, detail="Not Found")

    index_file = frontend_dir / "index.html"
    requested = (frontend_dir / full_path).resolve()
    try:
        requested.relative_to(frontend_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not Found") from exc

    if requested.is_file():
        return FileResponse(requested)

    source_requested = (FRONTEND_ROOT / full_path).resolve()
    try:
        source_requested.relative_to(FRONTEND_ROOT.resolve())
    except ValueError:
        source_requested = None
    if source_requested is not None and source_requested.is_file():
        return FileResponse(source_requested)

    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Not Found")

