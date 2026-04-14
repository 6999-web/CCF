from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text

from .database import Base


def new_id() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=new_id)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(80), nullable=False)
    role = Column(String(32), index=True, nullable=False)
    allowed_roles = Column(JSON, nullable=False, default=list)
    organization = Column(String(120), default="")
    phone = Column(String(40), default="")
    status = Column(String(24), default="active")
    avatar = Column(String(255), default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    nickname = Column(String(80), default="")
    avatar = Column(String(255), default="")
    signature = Column(String(160), default="")
    bio = Column(Text, default="")
    hobbies = Column(JSON, nullable=False, default=list)
    interests = Column(JSON, nullable=False, default=list)
    favorite_color = Column(String(40), default="")
    favorite_subject = Column(String(80), default="")
    theme_key = Column(String(80), default="")
    assistant_name = Column(String(80), default="")
    extra = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    parent_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(80), nullable=False)
    gender = Column(String(10), default="unknown")
    age = Column(Integer, default=0)
    grade = Column(String(40), default="")
    school = Column(String(120), default="")
    guardian_name = Column(String(80), default="")
    risk_level = Column(String(24), default="medium")
    assessment_score = Column(Float, default=0.0)
    learning_tags = Column(JSON, nullable=False, default=list)
    notes = Column(Text, default="")
    status = Column(String(24), default="active")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ScreeningReport(Base):
    __tablename__ = "screening_reports"

    id = Column(String(32), primary_key=True, default=new_id)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=False, index=True)
    source = Column(String(40), default="manual")
    score = Column(Float, default=0.0)
    risk_level = Column(String(24), default="medium")
    dimensions = Column(JSON, nullable=False, default=dict)
    conclusion = Column(Text, default="")
    recommendations = Column(JSON, nullable=False, default=list)
    report_url = Column(String(255), default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class QuestionnaireResult(Base):
    __tablename__ = "questionnaire_results"

    id = Column(String(32), primary_key=True, default=new_id)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=False, index=True)
    parent_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    answers = Column(JSON, nullable=False, default=dict)
    score = Column(Float, default=0.0)
    risk_level = Column(String(24), default="medium")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)


class GameLevel(Base):
    __tablename__ = "game_levels"

    id = Column(String(32), primary_key=True, default=new_id)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(60), default="")
    age_range = Column(String(40), default="")
    difficulty = Column(String(24), default="medium")
    description = Column(Text, default="")
    config = Column(JSON, nullable=False, default=dict)
    reward = Column(JSON, nullable=False, default=dict)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String(32), primary_key=True, default=new_id)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=False, index=True)
    level_code = Column(String(64), nullable=False, index=True)
    status = Column(String(24), default="active")
    score = Column(Float, default=0.0)
    duration_seconds = Column(Integer, default=0)
    started_at = Column(DateTime, default=utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    device = Column(String(80), default="web")
    telemetry_summary = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(String(32), primary_key=True, default=new_id)
    session_id = Column(String(32), ForeignKey("game_sessions.id"), nullable=False, index=True)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=False, index=True)
    event_type = Column(String(60), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ConsultationOrder(Base):
    __tablename__ = "consultation_orders"

    id = Column(String(32), primary_key=True, default=new_id)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=True, index=True)
    parent_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    counselor_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(160), nullable=False)
    channel = Column(String(40), default="online")
    status = Column(String(32), default="pending")
    scheduled_at = Column(DateTime, nullable=True)
    summary = Column(Text, default="")
    source_portal = Column(String(40), default="parent")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class InterventionPlan(Base):
    __tablename__ = "intervention_plans"

    id = Column(String(32), primary_key=True, default=new_id)
    child_id = Column(String(32), ForeignKey("child_profiles.id"), nullable=False, index=True)
    counselor_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(160), nullable=False)
    template_code = Column(String(64), default="")
    status = Column(String(24), default="draft")
    progress = Column(Float, default=0.0)
    tasks = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(String(32), primary_key=True, default=new_id)
    title = Column(String(200), nullable=False)
    category = Column(String(80), default="科普")
    source = Column(String(80), default="manual")
    tags = Column(JSON, nullable=False, default=list)
    content = Column(Text, default="")
    content_type = Column(String(40), default="text/markdown")
    published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class AIChatSession(Base):
    __tablename__ = "ai_chat_sessions"

    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    role = Column(String(32), default="parent")
    topic = Column(String(160), default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)


class AIChatMessage(Base):
    __tablename__ = "ai_chat_messages"

    id = Column(String(32), primary_key=True, default=new_id)
    session_id = Column(String(32), ForeignKey("ai_chat_sessions.id"), nullable=False, index=True)
    sender = Column(String(24), nullable=False)
    content = Column(Text, default="")
    citations = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(32), primary_key=True, default=new_id)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(160), nullable=False)
    content = Column(Text, default="")
    type = Column(String(40), default="info")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(80), primary_key=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(32), primary_key=True, default=new_id)
    actor_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(120), nullable=False)
    target_type = Column(String(80), default="")
    target_id = Column(String(32), default="")
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow, nullable=False)
