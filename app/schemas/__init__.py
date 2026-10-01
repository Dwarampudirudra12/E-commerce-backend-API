"""Pydantic v2 schemas: API conventions (doc M1) — versioned, envelope errors, pagination."""
from typing import Generic, TypeVar
from pydantic import BaseModel, EmailStr, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorResponse(BaseModel):
    detail: str
    code: str = "bad_request"
    request_id: str | None = None


# --- Auth schemas ---
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)
    role: str = Field(default="CUSTOMER", description="CUSTOMER|SELLER (SUPPORT/ADMIN by admin only)")


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    status: str
    email_verified: bool

    class Config:
        from_attributes = True


class AddressIn(BaseModel):
    label: str = "home"
    street: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    zip_code: str = ""
    is_default: bool = False


class AddressOut(AddressIn):
    id: int

    class Config:
        from_attributes = True


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailIn(BaseModel):
    token: str
