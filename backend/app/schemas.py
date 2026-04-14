from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    portal: str | None = None
    role: str | None = None


class SwitchRoleRequest(BaseModel):
    role: str


class RegisterParentRequest(BaseModel):
    username: str
    password: str
    display_name: str
    phone: str | None = None
    child_name: str | None = None
    child_age: int | None = None
    school: str | None = None


class SessionStartRequest(BaseModel):
    child_id: str | None = None
    level_code: str
    device: str | None = None


class SessionPauseRequest(BaseModel):
    session_id: str
    reason: str | None = None


class SessionEndRequest(BaseModel):
    session_id: str
    score: float | None = None
    duration_seconds: int | None = None
    status: str = "completed"
    telemetry_summary: dict[str, Any] = Field(default_factory=dict)


class TelemetryRequest(BaseModel):
    session_id: str
    child_id: str
    event_type: str
    level_code: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    score_delta: float | None = None
    duration_seconds: int | None = None


class QuestionnaireRequest(BaseModel):
    child_id: str
    parent_id: str | None = None
    answers: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None


class ChatRequest(BaseModel):
    question: str
    child_id: str | None = None
    session_id: str | None = None
    role: str = "parent"
    style_profile: str = "parent_calm"
    history: list[dict[str, str]] = Field(default_factory=list)


class PublicChatRequest(BaseModel):
    question: str
    role: str = "child"
    style_profile: str = "child_cute"
    child_id: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


class TransferRequest(BaseModel):
    question: str
    child_id: str | None = None
    parent_id: str | None = None
    contact: str | None = None
    reason: str | None = None


class OrderCreateRequest(BaseModel):
    child_id: str | None = None
    parent_id: str | None = None
    counselor_id: str | None = None
    title: str
    channel: str = "online"
    status: str = "pending"
    scheduled_at: datetime | None = None
    summary: str = ""
    source_portal: str = "parent"


class OrderUpdateRequest(BaseModel):
    status: str | None = None
    counselor_id: str | None = None
    summary: str | None = None
    scheduled_at: datetime | None = None


class InterventionPlanRequest(BaseModel):
    child_id: str
    counselor_id: str | None = None
    title: str
    template_code: str = ""
    status: str = "draft"
    progress: float = 0.0
    tasks: list[dict[str, Any]] = Field(default_factory=list)


class ArticleRequest(BaseModel):
    title: str
    category: str = "科普"
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)
    content: str = ""
    content_type: str = "text/markdown"
    published: bool = True


class SettingUpdateRequest(BaseModel):
    items: dict[str, Any] = Field(default_factory=dict)


class ScreeningRequest(BaseModel):
    child_id: str
    source: str = "manual"
    score: float
    risk_level: str | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    conclusion: str = ""
    recommendations: list[str] = Field(default_factory=list)
    report_url: str = ""


class ChildCreateRequest(BaseModel):
    user_id: str | None = None
    parent_id: str | None = None
    name: str
    gender: str = "unknown"
    age: int = 0
    grade: str = ""
    school: str = ""
    guardian_name: str = ""
    risk_level: str = "medium"
    assessment_score: float = 0.0
    learning_tags: list[str] = Field(default_factory=list)
    notes: str = ""


class UserCreateRequest(BaseModel):
    username: str
    password: str = ""
    display_name: str
    role: str
    allowed_roles: list[str] = Field(default_factory=list)
    organization: str = ""
    phone: str = ""
    status: str = "active"


class UserProfileUpdateRequest(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    signature: str | None = None
    bio: str | None = None
    hobbies: list[str] | None = None
    interests: list[str] | None = None
    favorite_color: str | None = None
    favorite_subject: str | None = None
    theme_key: str | None = None
    assistant_name: str | None = None
    extra: dict[str, Any] | None = None


class NotificationCreateRequest(BaseModel):
    user_id: str | None = None
    title: str
    content: str = ""
    type: str = "info"


class EntryPointCard(BaseModel):
    code: str
    title: str
    subtitle: str
    description: str
    features: list[str]
    entry_roles: list[str]
    accent: str
    route: str
    login_required: bool = True


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str
    role: str
    allowed_roles: list[str]
    organization: str
    phone: str
    status: str
    avatar: str


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    nickname: str
    avatar: str
    signature: str
    bio: str
    hobbies: list[str]
    interests: list[str]
    favorite_color: str
    favorite_subject: str
    theme_key: str
    assistant_name: str
    extra: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    profile: UserProfileOut | None = None
    portal: str
    entry_role: str


class PortalOverview(BaseModel):
    role: str
    title: str
    subtitle: str
    kpis: list[dict[str, Any]]
    modules: list[dict[str, Any]]
    recent: list[dict[str, Any]]
    actions: list[dict[str, Any]]


class DashboardSnapshot(BaseModel):
    generated_at: str
    summary: dict[str, Any]
    ranking: list[dict[str, Any]]
    score_distribution: list[dict[str, Any]]
    school_compare: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    live: dict[str, Any]
    alerts: list[dict[str, Any]]
