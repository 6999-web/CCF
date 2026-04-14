from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..security import hash_password
from ..models import (
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
    UserProfile,
)


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def risk_tier(score: float) -> str:
    if score >= 85:
        return 'high'
    if score >= 60:
        return 'medium'
    return 'low'


def risk_label(level: str) -> str:
    mapping = {
        'high': '高关注',
        'medium': '中等关注',
        'low': '低关注',
    }
    return mapping.get(level, '中等关注')


def serialize_user(user: User | None) -> dict[str, Any] | None:
    if user is None:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'role': user.role,
        'allowed_roles': user.allowed_roles or [],
        'organization': user.organization or '',
        'phone': user.phone or '',
        'status': user.status,
        'avatar': user.avatar or '',
        'created_at': iso(user.created_at),
    }


def serialize_user_profile(profile: UserProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        'id': profile.id,
        'user_id': profile.user_id,
        'nickname': profile.nickname or '',
        'avatar': profile.avatar or '',
        'signature': profile.signature or '',
        'bio': profile.bio or '',
        'hobbies': profile.hobbies or [],
        'interests': profile.interests or [],
        'favorite_color': profile.favorite_color or '',
        'favorite_subject': profile.favorite_subject or '',
        'theme_key': profile.theme_key or '',
        'assistant_name': profile.assistant_name or '小悦',
        'extra': profile.extra or {},
        'created_at': profile.created_at,
        'updated_at': profile.updated_at,
    }


def serialize_child(child: ChildProfile | None) -> dict[str, Any] | None:
    if child is None:
        return None
    return {
        'id': child.id,
        'user_id': child.user_id,
        'parent_id': child.parent_id,
        'name': child.name,
        'gender': child.gender,
        'age': child.age,
        'grade': child.grade,
        'school': child.school,
        'guardian_name': child.guardian_name,
        'risk_level': child.risk_level,
        'risk_text': risk_label(child.risk_level),
        'assessment_score': child.assessment_score,
        'learning_tags': child.learning_tags or [],
        'notes': child.notes or '',
        'status': child.status,
        'created_at': iso(child.created_at),
        'updated_at': iso(child.updated_at),
    }


def serialize_report(report: ScreeningReport | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        'id': report.id,
        'child_id': report.child_id,
        'source': report.source,
        'score': report.score,
        'risk_level': report.risk_level,
        'risk_text': risk_label(report.risk_level),
        'dimensions': report.dimensions or {},
        'conclusion': report.conclusion or '',
        'recommendations': report.recommendations or [],
        'report_url': report.report_url or '',
        'created_at': iso(report.created_at),
        'updated_at': iso(report.updated_at),
    }


def serialize_questionnaire(item: QuestionnaireResult | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        'id': item.id,
        'child_id': item.child_id,
        'parent_id': item.parent_id,
        'answers': item.answers or {},
        'score': item.score,
        'risk_level': item.risk_level,
        'summary': item.summary or '',
        'created_at': iso(item.created_at),
    }


def serialize_level(level: GameLevel | None) -> dict[str, Any] | None:
    if level is None:
        return None
    return {
        'id': level.id,
        'code': level.code,
        'name': level.name,
        'category': level.category,
        'age_range': level.age_range,
        'difficulty': level.difficulty,
        'description': level.description,
        'config': level.config or {},
        'reward': level.reward or {},
        'order_index': level.order_index,
    }


def serialize_session(session: GameSession | None) -> dict[str, Any] | None:
    if session is None:
        return None
    return {
        'id': session.id,
        'child_id': session.child_id,
        'level_code': session.level_code,
        'status': session.status,
        'score': session.score,
        'duration_seconds': session.duration_seconds,
        'started_at': iso(session.started_at),
        'ended_at': iso(session.ended_at),
        'device': session.device,
        'telemetry_summary': session.telemetry_summary or {},
        'created_at': iso(session.created_at),
        'updated_at': iso(session.updated_at),
    }


def serialize_order(order: ConsultationOrder | None) -> dict[str, Any] | None:
    if order is None:
        return None
    return {
        'id': order.id,
        'child_id': order.child_id,
        'parent_id': order.parent_id,
        'counselor_id': order.counselor_id,
        'title': order.title,
        'channel': order.channel,
        'status': order.status,
        'scheduled_at': iso(order.scheduled_at),
        'summary': order.summary or '',
        'source_portal': order.source_portal,
        'created_at': iso(order.created_at),
        'updated_at': iso(order.updated_at),
    }


def serialize_plan(plan: InterventionPlan | None) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        'id': plan.id,
        'child_id': plan.child_id,
        'counselor_id': plan.counselor_id,
        'title': plan.title,
        'template_code': plan.template_code,
        'status': plan.status,
        'progress': plan.progress,
        'tasks': plan.tasks or [],
        'created_at': iso(plan.created_at),
        'updated_at': iso(plan.updated_at),
    }


def serialize_article(article: KnowledgeArticle | None) -> dict[str, Any] | None:
    if article is None:
        return None
    return {
        'id': article.id,
        'title': article.title,
        'category': article.category,
        'source': article.source,
        'tags': article.tags or [],
        'content': article.content or '',
        'content_type': article.content_type,
        'published': article.published,
        'view_count': article.view_count,
        'created_at': iso(article.created_at),
        'updated_at': iso(article.updated_at),
    }


def serialize_notification(item: Notification | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        'id': item.id,
        'user_id': item.user_id,
        'title': item.title,
        'content': item.content,
        'type': item.type,
        'read_at': iso(item.read_at),
        'created_at': iso(item.created_at),
    }


def serialize_setting(item: SystemSetting | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        'key': item.key,
        'value': item.value,
        'updated_at': iso(item.updated_at),
    }


def calculate_questionnaire_score(answers: dict[str, Any]) -> tuple[float, str]:
    vals: list[float] = []
    for value in (answers or {}).values():
        try:
            vals.append(float(value))
        except Exception:
            continue
    if not vals:
        return 60.0, '中等关注'
    avg = sum(vals) / max(1, len(vals))
    score = round(min(100, max(0, avg * 20)), 1)
    return score, risk_label(risk_tier(score))


def search_articles(db: Session, query: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    q = db.query(KnowledgeArticle)
    if query:
        like = f'%{query.strip()}%'
        q = q.filter((KnowledgeArticle.title.like(like)) | (KnowledgeArticle.content.like(like)))
    rows = q.order_by(KnowledgeArticle.created_at.desc()).limit(limit).all()
    return [serialize_article(item) for item in rows]


def build_entry_points() -> dict[str, Any]:
    cards = [
        {
            'code': 'child',
            'title': '儿童端',
            'subtitle': '安全答题训练',
            'description': '进入受控答题空间，聚焦训练任务与即时反馈。',
            'features': ['答题闭环', '安全屏蔽', '奖励反馈'],
            'entry_roles': ['child'],
            'accent': 'blue',
            'route': '/portal/child',
            'login_required': True,
        },
        {
            'code': 'parent',
            'title': '家长端',
            'subtitle': '报告与咨询协同',
            'description': '查看报告、管理问卷、获取 AI 辅助建议和预约咨询。',
            'features': ['报告追踪', '问卷提交', '咨询预约'],
            'entry_roles': ['parent'],
            'accent': 'pink',
            'route': '/portal/parent',
            'login_required': True,
        },
        {
            'code': 'counselor',
            'title': '咨询师端',
            'subtitle': '订单干预工作台',
            'description': '围绕订单处理、干预计划与知识支持的专业工作流。',
            'features': ['订单处理', '计划创建', '知识支持'],
            'entry_roles': ['counselor'],
            'accent': 'green',
            'route': '/portal/counselor',
            'login_required': True,
        },
        {
            'code': 'management',
            'title': '管理端',
            'subtitle': '运营控制中心',
            'description': '统一管理用户、内容、审计与平台运行配置。',
            'features': ['用户治理', '内容管理', '审计追踪'],
            'entry_roles': ['management'],
            'accent': 'orange',
            'route': '/portal/management',
            'login_required': True,
        },
    ]
    return {
        'cards': cards,
        'login_roles': {'management': ['management']},
        'screen': {'route': '/screen', 'login_required': False},
    }


def _seed_user(db: Session, username: str, display_name: str, role: str, allowed_roles: list[str] | None = None) -> User:
    user = db.query(User).filter(User.username == username).one_or_none()
    if user:
        return user
    user = User(
        username=username,
        password_hash=hash_password('123456'),
        display_name=display_name,
        role=role,
        allowed_roles=allowed_roles or [role],
        organization='悦读相伴',
        phone='13800000000',
        status='active',
    )
    db.add(user)
    db.flush()
    return user


def _seed_levels(db: Session) -> None:
    if db.query(GameLevel).count() > 0:
        return
    level_defs = [
        ('rhyme_match', '韵脚配对', 'phonological'),
        ('syllable_clap', '音节拍手', 'phonological'),
        ('phoneme_hunt', '音素捕捉', 'phonological'),
        ('find_odd_char', '找出异类字', 'character'),
        ('char_puzzle', '汉字拼图', 'character'),
        ('word_train', '词语小火车', 'character'),
        ('rapid_naming', '快速命名', 'fluency'),
        ('color_stroop', '颜色干扰', 'attention'),
        ('memory_chain', '记忆接龙', 'memory'),
        ('echo_sentence', '复述句子', 'language'),
        ('sentence_complete', '句子补全', 'language'),
        ('story_quiz', '故事测验', 'comprehension'),
    ]
    for idx, (code, name, category) in enumerate(level_defs, start=1):
        db.add(
            GameLevel(
                code=code,
                name=name,
                category=category,
                age_range='6-10',
                difficulty='easy' if idx <= 4 else 'medium',
                description=f'{name} 训练',
                config={'target_time_sec': 180, 'questions': 8},
                reward={'stars': 1 + (idx % 3)},
                order_index=idx,
            )
        )


def _seed_articles(db: Session) -> None:
    if db.query(KnowledgeArticle).count() > 0:
        return
    samples = [
        ('家庭阅读陪伴清单', '指导'),
        ('读写困难儿童日常训练建议', '科普'),
        ('答题激励话术模板', '工具'),
    ]
    for title, category in samples:
        db.add(
            KnowledgeArticle(
                title=title,
                category=category,
                source='system',
                tags=['儿童', '阅读', '训练'],
                content=f'【{title}】\n- 每日固定 20 分钟\n- 先鼓励后纠错\n- 一周复盘一次',
                content_type='text/markdown',
                published=True,
            )
        )


def ensure_seed_data(db: Session) -> None:
    child_user = _seed_user(db, 'child01', '示例儿童', 'child')
    parent_user = _seed_user(db, 'parent01', '示例家长', 'parent')
    _seed_user(db, 'counselor01', '示例咨询师', 'counselor')
    _seed_user(db, 'management01', '示例管理者', 'management', ['management', 'review_group', 'review_office', 'academic_affairs'])
    _seed_user(db, 'research01', '示例教研', 'teacher_research', ['teacher_research'])
    _seed_user(db, 'admin01', '超级管理员', 'management', ['management', 'review_group', 'review_office', 'academic_affairs'])

    child = db.query(ChildProfile).filter(ChildProfile.user_id == child_user.id).one_or_none()
    if child is None:
        child = ChildProfile(
            user_id=child_user.id,
            parent_id=parent_user.id,
            name='小星',
            gender='unknown',
            age=8,
            grade='二年级',
            school='阳光小学',
            guardian_name=parent_user.display_name,
            risk_level='medium',
            assessment_score=72,
            learning_tags=['phonological', 'reading'],
            notes='系统示例儿童档案',
            status='active',
        )
        db.add(child)
        db.flush()

    if db.query(ScreeningReport).filter(ScreeningReport.child_id == child.id).count() == 0:
        db.add(
            ScreeningReport(
                child_id=child.id,
                source='baseline',
                score=72,
                risk_level='medium',
                dimensions={'phonological': 68, 'fluency': 70, 'comprehension': 74},
                conclusion='建议保持每周 4 次训练。',
                recommendations=['每次 15-20 分钟', '坚持正向反馈'],
                report_url='',
            )
        )

    _seed_levels(db)
    _seed_articles(db)

    for user in db.query(User).all():
        get_or_create_user_profile(db, user)

    if db.query(Notification).count() == 0:
        for user in db.query(User).all():
            db.add(Notification(user_id=user.id, title='欢迎使用悦读相伴', content='系统已准备就绪', type='info'))

    db.commit()


def get_or_create_user_profile(db: Session, user: User) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).one_or_none()
    if profile:
        return profile
    profile = UserProfile(
        user_id=user.id,
        nickname=user.display_name,
        assistant_name='小悦',
        theme_key='sunlit',
        hobbies=['阅读'],
        interests=['成长'],
        extra={'created_from': 'seed'},
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_user_profile(db: Session, user: User, payload: Any) -> UserProfile:
    profile = get_or_create_user_profile(db, user)
    fields = [
        'nickname',
        'avatar',
        'signature',
        'bio',
        'hobbies',
        'interests',
        'favorite_color',
        'favorite_subject',
        'theme_key',
        'assistant_name',
        'extra',
    ]
    for key in fields:
        value = getattr(payload, key, None)
        if value is not None:
            setattr(profile, key, value)
    profile.updated_at = now()
    db.commit()
    db.refresh(profile)
    return profile


def upsert_setting(db: Session, key: str, value: Any) -> SystemSetting:
    item = db.get(SystemSetting, key)
    if item is None:
        item = SystemSetting(key=key, value=str(value), updated_at=now())
        db.add(item)
    else:
        item.value = str(value)
        item.updated_at = now()
    db.commit()
    db.refresh(item)
    return item


def log_audit(db: Session, actor_id: str | None, action: str, target_type: str, target_id: str, detail: str = '') -> AuditLog:
    item = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _base_questions(level_code: str) -> list[dict[str, Any]]:
    common_source = {
        'phonological': 'phonemic awareness progression',
        'comprehension': 'age-appropriate reading comprehension',
        'curriculum': 'CCSS.ELA-Literacy.RF.1',
    }
    return [
        {
            'id': f'{level_code}-q1',
            'prompt': '请选出最符合句意的词语：小朋友在操场上快乐地____。',
            'options': ['飞翔', '奔跑', '潜水', '发芽'],
            'answer': '奔跑',
            'skill': '语境理解',
            'explanation': '操场上最常见的动作是奔跑。',
            'source_basis': common_source,
        },
        {
            'id': f'{level_code}-q2',
            'prompt': '“花/家/画”中，和“花”发音最接近的是？',
            'options': ['家', '画', '都不是', '都一样'],
            'answer': '画',
            'skill': '音韵辨识',
            'explanation': '花和画都属于相近韵母组合。',
            'source_basis': common_source,
        },
        {
            'id': f'{level_code}-q3',
            'prompt': '阅读一句话后回答：小明先洗手，再吃点心。小明先做什么？',
            'options': ['吃点心', '洗手', '写作业', '看电视'],
            'answer': '洗手',
            'skill': '顺序理解',
            'explanation': '句子中先后顺序很明确。',
            'source_basis': common_source,
        },
        {
            'id': f'{level_code}-q4',
            'prompt': '哪一个词语和“明亮”意思最接近？',
            'options': ['昏暗', '清晰', '闪亮', '沉重'],
            'answer': '闪亮',
            'skill': '词义理解',
            'explanation': '“闪亮”与“明亮”语义接近。',
            'source_basis': common_source,
        },
    ]


def get_level_questions(level_code: str, count: int = 8) -> list[dict[str, Any]]:
    base = _base_questions(level_code)
    result: list[dict[str, Any]] = []
    while len(result) < count:
        result.extend(base)
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(result[:count], start=1):
        question = dict(item)
        question.setdefault("difficulty", "easy" if idx <= 3 else "medium")
        question.setdefault("ability_tags", [question.get("skill", "综合能力")])
        question.setdefault("source_tag", "internal_core")
        question.setdefault("hint", "先排除明显不合适的选项，再选择最合理答案。")
        question.setdefault("age_band", "6-10")
        normalized.append(question)
    return normalized


def generate_ai_answer(
    db: Session,
    question: str,
    child_id: str | None = None,
    role: str = 'parent',
    user_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    q = question or ''
    lower = q.lower()
    if any(token in lower for token in ['不会', '答错', '错', '失败']):
        answer = '别担心，答错是学习的一部分。先夸奖孩子愿意尝试，再给一个小提示，下一题会更好。'
    elif any(token in lower for token in ['计划', '怎么学', '训练']):
        answer = '建议每天 20 分钟：10 分钟音韵训练 + 5 分钟句子理解 + 5 分钟复盘。每周复盘一次错题。'
    else:
        answer = '这是个很好的问题。建议保持“先鼓励、再纠错、再练习”的节奏，孩子会更愿意持续学习。'
    citations = ['internal-knowledge-base']
    return {'answer': answer, 'citations': citations, 'engine': 'local'}


def create_transfer_order(
    db: Session,
    question: str,
    child_id: str | None,
    parent_id: str | None,
    contact: str | None,
    reason: str | None,
    source_portal: str,
) -> ConsultationOrder:
    summary = f'问题：{question}\n联系方式：{contact or "未提供"}\n原因：{reason or "AI转人工"}'
    order = ConsultationOrder(
        child_id=child_id,
        parent_id=parent_id,
        counselor_id=None,
        title='AI转人工咨询',
        channel='online',
        status='pending',
        summary=summary,
        source_portal=source_portal,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def build_public_dashboard(db: Session) -> dict[str, Any]:
    children = db.query(ChildProfile).count()
    reports = db.query(ScreeningReport).count()
    orders_pending = db.query(ConsultationOrder).filter(ConsultationOrder.status.in_(['pending', 'scheduled'])).count()
    sessions = db.query(GameSession).count()

    ranking_rows = (
        db.query(ChildProfile.name, ChildProfile.school, func.avg(GameSession.score))
        .join(GameSession, GameSession.child_id == ChildProfile.id, isouter=True)
        .group_by(ChildProfile.id)
        .all()
    )
    ranking = []
    for idx, row in enumerate(sorted(ranking_rows, key=lambda x: float(x[2] or 0), reverse=True), start=1):
        ranking.append(
            {
                'rank': idx,
                'name': row[0],
                'school': row[1] or '未填写',
                'score': round(float(row[2] or 0), 1),
                'status': '持续训练中',
            }
        )

    score_distribution = [
        {'name': '80-100', 'value': max(1, children // 3), 'color': '#52b6ff'},
        {'name': '60-79', 'value': max(1, children // 2), 'color': '#57d3b8'},
        {'name': '0-59', 'value': max(1, children // 4), 'color': '#ffb567'},
    ]

    school_compare = []
    schools = db.query(ChildProfile.school).filter(ChildProfile.school != '').distinct().all()
    for school in schools[:6]:
        name = school[0]
        avg_score = (
            db.query(func.avg(GameSession.score))
            .join(ChildProfile, ChildProfile.id == GameSession.child_id)
            .filter(ChildProfile.school == name)
            .scalar()
        )
        school_compare.append({'name': name, 'value': round(float(avg_score or 70), 1)})
    if not school_compare:
        school_compare = [
            {'name': '阳光小学', 'value': 76},
            {'name': '未来小学', 'value': 73},
            {'name': '星河小学', 'value': 79},
        ]

    today = now().date()
    timeline = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        timeline.append({'date': day.isoformat(), 'screening': 60 + (i * 2 + reports) % 25})

    alerts = [
        {'title': '学习连续性提醒', 'content': '建议保持每周至少 4 次训练。', 'time': iso(now())},
        {'title': '答题反馈质量', 'content': '答错后鼓励语覆盖率已提升。', 'time': iso(now())},
    ]

    snapshot = {
        'generated_at': iso(now()),
        'summary': {
            'children': children,
            'screening_reports': reports,
            'pending_orders': orders_pending,
            'sessions': sessions,
        },
        'ranking': ranking[:10],
        'score_distribution': score_distribution,
        'school_compare': school_compare,
        'timeline': timeline,
        'live': {
            'children': children,
            'screening_reports': reports,
            'pending_orders': orders_pending,
            'pulse': 70 + (sessions % 20),
            'refresh_hint': '每3秒更新',
        },
        'alerts': alerts,
    }
    return snapshot


def _user_scope_children(db: Session, user: User) -> list[ChildProfile]:
    if user.role == 'parent':
        return db.query(ChildProfile).filter(ChildProfile.parent_id == user.id).all()
    if user.role == 'child':
        return db.query(ChildProfile).filter(ChildProfile.user_id == user.id).all()
    return db.query(ChildProfile).all()


def build_parent_children_progress(db: Session, user: User, include_ai: bool = True) -> dict[str, Any]:
    children = _user_scope_children(db, user)
    result = []
    for child in children:
        sessions = db.query(GameSession).filter(GameSession.child_id == child.id).order_by(GameSession.created_at.desc()).all()
        total = len(sessions)
        completed = len([s for s in sessions if s.status == 'completed'])
        avg_score = round(sum(float(s.score or 0) for s in sessions) / total, 1) if total else 0
        accuracy_vals = []
        for s in sessions:
            summary = s.telemetry_summary or {}
            acc = summary.get('accuracy')
            if acc is None:
                continue
            try:
                acc_num = float(acc)
                if acc_num <= 1:
                    acc_num = acc_num * 100
                accuracy_vals.append(acc_num)
            except Exception:
                continue
        accuracy = round(sum(accuracy_vals) / len(accuracy_vals), 1) if accuracy_vals else (avg_score if avg_score <= 100 else 100)
        completion_rate = round((completed / total) * 100, 1) if total else 0
        latest_level = sessions[0].level_code if sessions else '暂无'
        last_7d_trend = []
        for i in range(6, -1, -1):
            day = (now().date() - timedelta(days=i)).isoformat()
            daily = [s for s in sessions if s.created_at and s.created_at.date().isoformat() == day]
            daily_score = round(sum(float(s.score or 0) for s in daily) / len(daily), 1) if daily else 0
            daily_done = len([s for s in daily if s.status == "completed"])
            last_7d_trend.append(
                {
                    "date": day,
                    "sessions": len(daily),
                    "completed": daily_done,
                    "avg_score": daily_score,
                }
            )

        completed_sessions_sorted = sorted(
            [s for s in sessions if s.status == "completed" and s.created_at],
            key=lambda s: s.created_at,
            reverse=True,
        )
        streak_days = 0
        if completed_sessions_sorted:
            expected = now().date()
            completed_days = {s.created_at.date() for s in completed_sessions_sorted}
            while expected in completed_days:
                streak_days += 1
                expected -= timedelta(days=1)

        weak_scores: dict[str, list[float]] = {}
        for s in sessions:
            summary = s.telemetry_summary or {}
            for key in ("weak_skills", "weak_skill", "mistake_tags"):
                val = summary.get(key)
                if isinstance(val, list):
                    for skill in val:
                        weak_scores.setdefault(str(skill), []).append(float(s.score or 0))
                elif isinstance(val, str) and val:
                    weak_scores.setdefault(val, []).append(float(s.score or 0))
        weak_skills = sorted(
            [
                {"name": name, "signal": round(sum(vals) / max(1, len(vals)), 1), "count": len(vals)}
                for name, vals in weak_scores.items()
            ],
            key=lambda x: (x["signal"], -x["count"]),
        )[:3]
        if not weak_skills and latest_level and latest_level != "暂无":
            weak_skills = [{"name": latest_level, "signal": avg_score, "count": max(1, completed)}]

        ai_analysis = ''
        ai_weekly_summary = ""
        if include_ai:
            if completion_rate >= 80 and accuracy >= 75:
                ai_analysis = '孩子保持了较好的学习稳定性，建议增加一点点阅读理解难度。'
            elif completion_rate < 50:
                ai_analysis = '完成率偏低，建议把单次任务控制在 10-15 分钟，并固定时间开始。'
            else:
                ai_analysis = '建议延续当前训练节奏，重点复盘最近两次错误类型。'
            ai_weekly_summary = (
                f"本周完成率 {completion_rate}% ，正确率 {accuracy}% ，连续学习 {streak_days} 天。"
                f"建议优先巩固：{', '.join([item['name'] for item in weak_skills]) if weak_skills else '综合能力'}。"
            )

        result.append(
            {
                'child': serialize_child(child),
                'progress': {
                    'total_sessions': total,
                    'completed_sessions': completed,
                    'completion_rate': completion_rate,
                    'accuracy': accuracy,
                    'average_score': avg_score,
                    'latest_level': latest_level,
                    'streak_days': streak_days,
                    'weak_skills': weak_skills,
                    'last_7d_trend': last_7d_trend,
                },
                'ai_analysis': ai_analysis,
                'ai_weekly_summary': ai_weekly_summary,
            }
        )

    return {'generated_at': iso(now()), 'children_progress': result}


def build_portal_overview(db: Session, user: User, role: str) -> dict[str, Any]:
    snapshot = build_public_dashboard(db)
    if role == 'child':
        child = _user_scope_children(db, user)[0] if _user_scope_children(db, user) else None
        reports = []
        if child:
            reports = db.query(ScreeningReport).filter(ScreeningReport.child_id == child.id).order_by(ScreeningReport.created_at.desc()).all()
        return {
            'role': role,
            'title': '儿童安全答题中心',
            'subtitle': '专注学习任务',
            'kpis': [
                {'label': '报告数', 'value': len(reports)},
                {'label': '训练会话', 'value': db.query(GameSession).count()},
            ],
            'modules': [{'name': '答题任务'}, {'name': '奖励反馈'}],
            'recent': [serialize_report(item) for item in reports[:5]],
            'actions': [{'title': '开始答题', 'key': 'start_quiz'}],
            'summary': {'recent_alerts': snapshot['alerts']},
        }

    if role == 'parent':
        children = _user_scope_children(db, user)
        return {
            'role': role,
            'title': '家校协同中心',
            'subtitle': '进度与陪伴',
            'kpis': [{'label': '儿童数量', 'value': len(children)}],
            'modules': [{'name': '儿童档案'}, {'name': '报告追踪'}, {'name': '咨询预约'}],
            'recent': snapshot['alerts'],
            'actions': [{'title': '查看进度', 'key': 'view_progress'}],
            'summary': {'recent_alerts': snapshot['alerts']},
        }

    if role == 'counselor':
        return {
            'role': role,
            'title': '咨询协作中心',
            'subtitle': '订单与干预',
            'kpis': [{'label': '待处理订单', 'value': snapshot['summary']['pending_orders']}],
            'modules': [{'name': '咨询订单'}, {'name': '干预计划'}],
            'recent': snapshot['alerts'],
            'actions': [{'title': '处理订单', 'key': 'process_order'}],
            'summary': {'recent_alerts': snapshot['alerts']},
        }

    return {
        'role': role,
        'title': '运营管理中心',
        'subtitle': '全局指标',
        'kpis': [{'label': '儿童总数', 'value': snapshot['summary']['children']}],
        'modules': [{'name': '用户治理'}, {'name': '内容管理'}, {'name': '审计'}],
        'recent': snapshot['alerts'],
        'actions': [{'title': '查看大屏', 'key': 'open_screen'}],
        'summary': {'recent_alerts': snapshot['alerts']},
    }
