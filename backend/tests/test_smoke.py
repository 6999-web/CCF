from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("NVIDIA_USE_REMOTE", "0")

from app.main import app

@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str = "123456", role: str | None = None, portal: str | None = None) -> str:
    payload = {"username": username, "password": password}
    if role is not None:
        payload["role"] = role
    if portal is not None:
        payload["portal"] = portal
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_public_entry_points_and_health(client: TestClient):
    health = client.get("/api/v1/public/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    entry_points = client.get("/api/v1/public/entry-points")
    assert entry_points.status_code == 200
    data = entry_points.json()
    assert len(data["cards"]) >= 4
    assert data["screen"]["login_required"] is False


def test_auth_and_dashboard_flow(client: TestClient):
    token = login(client, "management01", role="review_group", portal="management")
    me = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["entry_role"] == "review_group"

    dashboard = client.get("/api/v1/admin/dashboard", headers=auth_headers(token))
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert "summary" in data
    assert data["summary"]["children"] >= 1


def test_profile_update_and_role_payload(client: TestClient):
    token = login(client, "management01", role="review_group", portal="management")

    profile = client.get("/api/v1/auth/profile", headers=auth_headers(token))
    assert profile.status_code == 200
    original = profile.json()["profile"]
    assert original["assistant_name"]

    updated = client.put(
        "/api/v1/auth/profile",
        headers=auth_headers(token),
        json={
            "nickname": "冒烟家长",
            "avatar": "🌸",
            "signature": "认真陪伴",
            "bio": "关注家庭训练与阅读习惯",
            "hobbies": ["阅读", "散步"],
            "interests": ["阅读障碍", "亲子沟通"],
            "favorite_color": "蓝色",
            "favorite_subject": "语文",
            "assistant_name": "星萌家长助手",
            "theme_key": "coffee-warm",
            "extra": {"goal": "提升阅读陪伴"},
        },
    )
    assert updated.status_code == 200, updated.text
    payload = updated.json()
    assert payload["profile"]["nickname"] == "冒烟家长"
    assert payload["profile"]["assistant_name"] == "星萌家长助手"
    assert payload["profile"]["theme_key"] == "coffee-warm"

    me = client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["profile"]["nickname"] == "冒烟家长"

    switched = client.post("/api/v1/auth/switch-role", headers=auth_headers(token), json={"role": "management"})
    assert switched.status_code == 200
    assert switched.json()["profile"]["nickname"] == "冒烟家长"


def test_parent_questionnaire_creates_report(client: TestClient):
    token = login(client, "parent01", portal="parent")
    children_response = client.get("/api/v1/parent/children", headers=auth_headers(token))
    assert children_response.status_code == 200
    children = children_response.json()["children"]
    assert children
    child_id = children[0]["id"]

    questionnaire = client.post(
        "/api/v1/parent/questionnaire",
        headers=auth_headers(token),
        json={
            "child_id": child_id,
            "answers": {
                "b_d_confusion": 3,
                "mirror_writing": 2,
                "skip_line": 4,
                "slow_reading": 3,
            },
            "summary": "冒烟测试问卷",
        },
    )
    assert questionnaire.status_code == 200, questionnaire.text
    payload = questionnaire.json()
    assert "report" in payload

    reports = client.get("/api/v1/parent/reports", headers=auth_headers(token))
    assert reports.status_code == 200
    assert reports.json()["reports"]


def test_ai_chat_and_legacy_aliases(client: TestClient):
    token = login(client, "parent01", portal="parent")

    chat = client.post(
        "/api/v1/ai/chat",
        headers=auth_headers(token),
        json={"question": "孩子经常把 b 和 d 混淆，怎么办？", "role": "parent"},
    )
    assert chat.status_code == 200, chat.text
    answer = chat.json()
    assert "answer" in answer
    assert answer["citations"] is not None

    legacy_profiles = client.get("/api/profiles", headers=auth_headers(token))
    assert legacy_profiles.status_code == 200
    assert legacy_profiles.json()["profiles"]

    legacy_summary = client.get("/api/statistics/summary", headers=auth_headers(token))
    assert legacy_summary.status_code == 200
    assert "kpis" in legacy_summary.json()


def test_games_and_notifications(client: TestClient):
    token = login(client, "child01", portal="child")
    levels = client.get("/api/v1/games/levels", headers=auth_headers(token))
    assert levels.status_code == 200
    level_items = levels.json()["levels"]
    assert level_items

    reward = client.get("/api/v1/games/rewards/status", headers=auth_headers(token))
    assert reward.status_code == 200
    assert "badge" in reward.json()

    notifications = client.get("/api/v1/notifications", headers=auth_headers(token))
    assert notifications.status_code == 200
    assert notifications.json()["notifications"]


def test_child_training_flow_accepts_profile_id_and_persists_summary(client: TestClient):
    token = login(client, "child01", portal="child")
    levels_response = client.get("/api/v1/child/levels", headers=auth_headers(token))
    assert levels_response.status_code == 200
    payload = levels_response.json()
    assert payload["child"]
    assert payload["levels"]

    child_id = payload["child"]["id"]
    level_code = payload["levels"][0]["code"]

    session_start = client.post(
        "/api/v1/child/session/start",
        headers=auth_headers(token),
        json={"child_id": child_id, "level_code": level_code, "device": "storybook-web"},
    )
    assert session_start.status_code == 200, session_start.text
    session = session_start.json()["session"]

    telemetry = client.post(
        "/api/v1/child/telemetry",
        headers=auth_headers(token),
        json={
            "session_id": session["id"],
            "child_id": child_id,
            "event_type": "answer_submit",
            "level_code": level_code,
            "duration_seconds": 12,
            "payload": {"answer": "沙", "correct": True},
        },
    )
    assert telemetry.status_code == 200, telemetry.text
    assert telemetry.json()["session"]["telemetry_summary"]["events"] >= 1

    session_end = client.put(
        "/api/v1/child/session/end",
        headers=auth_headers(token),
        json={
            "session_id": session["id"],
            "score": 100,
            "duration_seconds": 18,
            "status": "completed",
            "telemetry_summary": {"events": 2, "accuracy": 1},
        },
    )
    assert session_end.status_code == 200, session_end.text
    assert session_end.json()["session"]["telemetry_summary"]["accuracy"] == 1


def test_child_question_bank_and_parent_progress_analysis(client: TestClient):
    child_token = login(client, "child01", portal="child")
    levels_response = client.get("/api/v1/child/levels", headers=auth_headers(child_token))
    assert levels_response.status_code == 200
    level_code = levels_response.json()["levels"][0]["code"]

    questions_response = client.get(f"/api/v1/child/questions/{level_code}?count=5", headers=auth_headers(child_token))
    assert questions_response.status_code == 200, questions_response.text
    questions_payload = questions_response.json()
    assert questions_payload["count"] == len(questions_payload["questions"])
    assert questions_payload["questions"]
    assert {"phonological", "comprehension", "curriculum"}.issubset(
        set(questions_payload["questions"][0]["source_basis"].keys())
    )
    assert "difficulty" in questions_payload["questions"][0]
    assert "ability_tags" in questions_payload["questions"][0]
    assert "source_tag" in questions_payload["questions"][0]
    assert "hint" in questions_payload["questions"][0]

    parent_token = login(client, "parent01", portal="parent")
    progress_response = client.get("/api/v1/parent/children/progress?include_ai=true", headers=auth_headers(parent_token))
    assert progress_response.status_code == 200, progress_response.text
    progress_payload = progress_response.json()
    assert "generated_at" in progress_payload
    assert progress_payload["children_progress"]
    first = progress_payload["children_progress"][0]
    assert "progress" in first
    assert "ai_analysis" in first
    assert "ai_weekly_summary" in first
    assert "streak_days" in first["progress"]
    assert "weak_skills" in first["progress"]
    assert "last_7d_trend" in first["progress"]


def test_parent_and_counselor_write_flows(client: TestClient):
    parent_token = login(client, "parent01", portal="parent")
    children_response = client.get("/api/v1/parent/children", headers=auth_headers(parent_token))
    child_id = children_response.json()["children"][0]["id"]

    appointment = client.post(
        "/api/v1/parent/appointments",
        headers=auth_headers(parent_token),
        json={
            "child_id": child_id,
            "title": "周末训练复盘咨询",
            "summary": "希望确认下一阶段训练重点",
            "channel": "online",
        },
    )
    assert appointment.status_code == 200, appointment.text
    order_id = appointment.json()["order"]["id"]

    chat = client.post(
        "/api/v1/parent/chat",
        headers=auth_headers(parent_token),
        json={"child_id": child_id, "question": "最近训练注意什么？", "role": "parent"},
    )
    assert chat.status_code == 200, chat.text
    assert chat.json()["answer"]

    counselor_token = login(client, "counselor01", portal="counselor")
    order_update = client.patch(
        f"/api/v1/counselor/orders/{order_id}",
        headers=auth_headers(counselor_token),
        json={"status": "scheduled", "summary": "已安排周末线上复盘"},
    )
    assert order_update.status_code == 200, order_update.text
    assert order_update.json()["order"]["status"] == "scheduled"

    plan_create = client.post(
        "/api/v1/counselor/interventions",
        headers=auth_headers(counselor_token),
        json={
            "child_id": child_id,
            "title": "阶段性语音意识训练方案",
            "template_code": "T1",
            "tasks": [{"title": "韵脚配对", "status": "todo"}],
        },
    )
    assert plan_create.status_code == 200, plan_create.text
    assert plan_create.json()["plan"]["title"] == "阶段性语音意识训练方案"


def test_admin_write_flows_and_notifications(client: TestClient):
    admin_token = login(client, "management01", role="management", portal="management")
    username = f"demo_teacher_{uuid.uuid4().hex[:8]}"

    user_create = client.post(
        "/api/v1/admin/users",
        headers=auth_headers(admin_token),
        json={
            "username": username,
            "password": "123456",
            "display_name": "示例教研老师",
            "role": "teacher_research",
            "allowed_roles": ["teacher_research"],
            "organization": "示例学校",
            "phone": "13800000000",
            "status": "active",
        },
    )
    assert user_create.status_code == 200, user_create.text
    user_id = user_create.json()["user"]["id"]

    user_update = client.patch(
        f"/api/v1/admin/users/{user_id}",
        headers=auth_headers(admin_token),
        json={
            "username": username,
            "password": "",
            "display_name": "示例教研主任",
            "role": "teacher_research",
            "allowed_roles": ["teacher_research"],
            "organization": "示例学校",
            "phone": "13800000001",
            "status": "active",
        },
    )
    assert user_update.status_code == 200, user_update.text
    assert user_update.json()["user"]["display_name"] == "示例教研主任"

    article_create = client.post(
        "/api/v1/admin/articles",
        headers=auth_headers(admin_token),
        json={
            "title": "测试知识文章",
            "category": "指导",
            "tags": ["训练", "测试"],
            "content": "这是一篇自动化测试创建的知识文章。",
        },
    )
    assert article_create.status_code == 200, article_create.text
    assert article_create.json()["article"]["title"] == "测试知识文章"

    settings_update = client.put(
        "/api/v1/admin/settings",
        headers=auth_headers(admin_token),
        json={"items": {"site.theme": {"value": "storybook-garden"}}},
    )
    assert settings_update.status_code == 200, settings_update.text
    assert settings_update.json()["settings"]

    child_token = login(client, "child01", portal="child")
    notifications = client.get("/api/v1/notifications", headers=auth_headers(child_token))
    assert notifications.status_code == 200, notifications.text
    notification_id = notifications.json()["notifications"][0]["id"]

    mark_read = client.patch(f"/api/v1/notifications/{notification_id}", headers=auth_headers(child_token))
    assert mark_read.status_code == 200, mark_read.text
    assert mark_read.json()["notification"]["read_at"] is not None


def test_frontend_spa_routes_are_served_by_backend(client: TestClient):
    index_response = client.get("/")
    assert index_response.status_code == 200
    assert "text/html" in index_response.headers.get("content-type", "")

    screen_response = client.get("/screen")
    assert screen_response.status_code == 200
    assert "text/html" in screen_response.headers.get("content-type", "")

    portal_response = client.get("/portal/child")
    assert portal_response.status_code == 200
    assert "text/html" in portal_response.headers.get("content-type", "")

    app_js = client.get("/app.js")
    assert app_js.status_code == 200
    assert "javascript" in app_js.headers.get("content-type", "")

    css = client.get("/src/styles/global.css")
    assert css.status_code == 200
    assert "text/css" in css.headers.get("content-type", "")


def test_child_profile_access_is_protected(client: TestClient):
    parent_token = login(client, "parent01", portal="parent")
    children_response = client.get("/api/v1/parent/children", headers=auth_headers(parent_token))
    assert children_response.status_code == 200
    child_id = children_response.json()["children"][0]["id"]

    outsider = client.post(
        "/api/v1/auth/register/parent",
        json={
            "username": f"parent_x_{uuid.uuid4().hex[:6]}",
            "password": "123456",
            "display_name": "外部家长",
            "phone": "13800000009",
        },
    )
    assert outsider.status_code == 200
    outsider_token = outsider.json()["access_token"]

    denied = client.post(
        "/api/v1/child/session/start",
        headers=auth_headers(outsider_token),
        json={"child_id": child_id, "level_code": "rhyme_match", "device": "web"},
    )
    assert denied.status_code == 403
