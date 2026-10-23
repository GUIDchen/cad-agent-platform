from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    role: str
    active: bool = True


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    owner_id: int
    status: str


class DrawingCreate(BaseModel):
    project_id: int
    drawing_no: str = Field(pattern=r"^SW-\d{4}-\d{3}$")
    title: str = Field(min_length=1, max_length=128)


class DrawingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    drawing_no: str
    title: str
    status: str
    current_version_id: int | None
    locked_by: int | None
    lock_expires_at: datetime | None


class Hole(BaseModel):
    x: float = Field(ge=0, le=2000)
    y: float = Field(ge=0, le=2000)
    d: float = Field(gt=0, le=100)


class Point(BaseModel):
    x: float = Field(ge=0, le=2000)
    y: float = Field(ge=0, le=2000)


class Cutout(BaseModel):
    x: float = Field(ge=0, le=2000)
    y: float = Field(ge=0, le=2000)
    width: float = Field(gt=0, le=2000)
    height: float = Field(gt=0, le=2000)


class Slot(BaseModel):
    x: float = Field(ge=0, le=2000)
    y: float = Field(ge=0, le=2000)
    length: float = Field(gt=0, le=2000)
    width: float = Field(gt=0, le=200)


class GenerateIn(BaseModel):
    job_type: str = Field(default="generate_bracket", pattern=r"^generate_(bracket|solidworks|altium)$")
    length: float = Field(gt=10, le=2000)
    width: float = Field(gt=10, le=2000)
    thickness: float = Field(default=6, gt=0.5, le=50)
    corner_radius: float = Field(default=0, ge=0, le=100)
    chamfer: float = Field(default=0, ge=0, le=100)
    material: str = Field(default="304", max_length=32)
    surface: str = Field(default="拉丝", max_length=32)
    holes: list[Hole] = Field(min_length=1, max_length=50)
    slots: list[Slot] = Field(default_factory=list, max_length=50)
    cutouts: list[Cutout] = Field(default_factory=list, max_length=50)
    outline: list[Point] | None = Field(default=None, min_length=3, max_length=64)


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drawing_id: int
    version: int
    sha256: str
    params_json: str
    created_by: int
    created_at: datetime


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    drawing_id: int
    type: str
    status: str
    attempts: int
    error: str | None


class DeadJobOut(BaseModel):
    id: str
    drawing_id: int
    drawing_no: str
    title: str
    type: str
    attempts: int
    error: str | None
    created_at: datetime


class BatchGenerateItem(BaseModel):
    drawing_id: int
    spec: GenerateIn


class BatchGenerateIn(BaseModel):
    items: list[BatchGenerateItem] = Field(min_length=1, max_length=20)


class JobCreated(BaseModel):
    job_id: str
    status: str


class ApproveIn(BaseModel):
    comment: str = Field(default="", max_length=2000)


class RejectIn(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: str = Field(default="member", pattern=r"^(owner|member)$")


class ProjectMemberUpdate(BaseModel):
    role: Literal["owner", "member"]


class ProjectMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    user_id: int
    role: str
    user_name: str | None = None


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    role: str = Field(default="viewer", pattern=r"^(admin|designer|reviewer|viewer)$")


class UserUpdate(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(admin|designer|reviewer|viewer)$")
    active: bool | None = None


class ParseIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class AgentIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ImageIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    negative_prompt: str = Field(default="", max_length=500)
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=768, ge=256, le=2048)


class KnowledgeIn(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1, max_length=20000)


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    created_by: int
    created_at: datetime


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    content: str | None = Field(default=None, min_length=1, max_length=20000)


class KnowledgeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doc_id: int
    title: str
    content: str
    created_by: int
    created_at: datetime


class KnowledgeHit(BaseModel):
    id: int
    title: str
    snippet: str
    score: float


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    version_id: int | None = None


class CommentOut(BaseModel):
    id: int
    drawing_id: int
    version_id: int | None
    author_id: int
    author_name: str
    body: str
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    title: str
    body: str
    link: str
    read: bool
    created_at: datetime


class PendingApprovalOut(BaseModel):
    version_id: int
    drawing_id: int
    drawing_no: str
    title: str
    version: int
    created_at: datetime


class WecomActionIn(BaseModel):
    action: Literal["approve", "reject"]
    version_id: int
    reviewer_id: int | None = None
    comment: str = ""


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actor_id: int | None
    action: str
    object_type: str
    object_id: str
    detail_json: str
    ip: str | None = None
    created_at: datetime
