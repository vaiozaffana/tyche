from datetime import UTC, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_serializer,
    field_validator,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.title() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    @field_serializer("*", check_fields=False, when_used="json")
    def serialize_datetime_as_utc(self, value: object) -> object:
        if not isinstance(value, datetime):
            return value
        utc_value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return utc_value.isoformat().replace("+00:00", "Z")


class UserResponse(ApiModel):
    id: str
    name: str
    email: EmailStr
    email_verified: bool
    image: str | None
    created_at: datetime
    updated_at: datetime
    role: str | None
    banned: bool | None = None
    ban_reason: str | None = None
    ban_expires: datetime | None = None


class SessionResponse(ApiModel):
    id: str
    user_id: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    ip_address: str | None
    user_agent: str | None


class AuthResponse(ApiModel):
    user: UserResponse


class CurrentSessionResponse(ApiModel):
    session: SessionResponse
    user: UserResponse


class RegisterInput(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Name is required.")
        return value


class LoginInput(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileInput(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    image: HttpUrl | None = None

    @field_validator("name")
    @classmethod
    def strip_profile_name(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Name is required.")
        return value

    @field_validator("image", mode="before")
    @classmethod
    def empty_image_is_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


class ProfileResponse(ApiModel):
    user: UserResponse


class UserListItem(ApiModel):
    id: str
    email: EmailStr
    name: str
    role: str | None
    created_at: datetime
    updated_at: datetime


class UsersResponse(ApiModel):
    next_cursor: str | None
    users: list[UserListItem]
