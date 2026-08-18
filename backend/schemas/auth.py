from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile_number: Optional[str] = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    mobile: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):
    name: str
    email: EmailStr
    mobile_number: Optional[str] = ""
    password: Optional[str] = None

    class Config:
        from_attributes = True


class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user: Optional[UserResponse] = None
    admin: Optional[AdminResponse] = None
