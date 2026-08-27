from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Role = Literal["ADMIN", "ENGINEER", "VIEWER"]


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("valid email required")
        return value


class LoginRequest(RegisterRequest):
    pass


class UserResponse(BaseModel):
    id: str
    email: str
    role: Role
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse