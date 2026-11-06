from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AnswerRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: UUID
    concept_id: str = Field(min_length=1, max_length=100)
    stage: int = Field(ge=0, le=4)
    q_id: str = Field(min_length=1, max_length=100)
    selected_option: str = Field(min_length=1, max_length=1000)
    time_ms: int = Field(ge=0, le=3_600_000)


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Literal["student", "teacher", "parent", "admin"]
    language: Literal["ta", "ml", "kn", "te", "en"] = "ta"
    board: Literal["CBSE"] = "CBSE"
    grade: str | None = Field(default="10", max_length=20)
    class_id: str | None = Field(default=None, max_length=100)
    linked_students: list[str] = Field(default_factory=list)
    consent: bool = False
    active: bool = True


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Literal["student", "teacher", "parent", "admin"] | None = None
    language: Literal["ta", "ml", "kn", "te", "en"] | None = None
    board: Literal["CBSE"] | None = None
    grade: str | None = Field(default=None, max_length=20)
    class_id: str | None = Field(default=None, max_length=100)
    linked_students: list[str] | None = None
    consent: bool | None = None
    active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=128)


class ClassRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    class_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=120)
    teacher_id: str
    student_ids: list[str] = Field(default_factory=list)


class CurriculumRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    concept_id: str = Field(min_length=1, max_length=100)
    board: Literal["CBSE"] = "CBSE"
    grade: str = Field(default="10", max_length=20)
    subject: str = Field(min_length=1, max_length=100)
    chapter: str = Field(min_length=1, max_length=160)
    lesson: str = Field(min_length=1, max_length=160)
    title: dict[str, str]
    keywords: list[dict[str, str]]
    content: dict[str, dict[str, str]]
    quiz: list[dict[str, object]]
    review_status: Literal["draft", "reviewed", "approved"] = "draft"
    translation_status: dict[str, str] = Field(default_factory=dict)


class SettingsRequest(BaseModel):
    bkt: dict[str, float]
    thresholds: dict[str, float | int]