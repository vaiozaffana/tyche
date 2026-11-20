from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"
    __table_args__ = (Index("User_email_key", "email", unique=True),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    email_verified: Mapped[bool] = mapped_column("emailVerified", Boolean, default=False)
    image: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime, default=utc_now, onupdate=utc_now
    )
    role: Mapped[str | None] = mapped_column(Text, default="user")
    banned: Mapped[bool | None] = mapped_column(Boolean)
    ban_reason: Mapped[str | None] = mapped_column("banReason", Text)
    ban_expires: Mapped[datetime | None] = mapped_column("banExpires", DateTime)


class Session(Base):
    __tablename__ = "Session"
    __table_args__ = (Index("Session_token_key", "token", unique=True),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    expires_at: Mapped[datetime] = mapped_column("expiresAt", DateTime)
    token: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime, default=utc_now, onupdate=utc_now
    )
    ip_address: Mapped[str | None] = mapped_column("ipAddress", Text)
    user_agent: Mapped[str | None] = mapped_column("userAgent", Text)
    user_id: Mapped[str] = mapped_column(
        "userId",
        Text,
        ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    impersonated_by: Mapped[str | None] = mapped_column("impersonatedBy", Text)


class Account(Base):
    __tablename__ = "Account"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    account_id: Mapped[str] = mapped_column("accountId", Text)
    provider_id: Mapped[str] = mapped_column("providerId", Text)
    user_id: Mapped[str] = mapped_column(
        "userId",
        Text,
        ForeignKey("User.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    access_token: Mapped[str | None] = mapped_column("accessToken", Text)
    refresh_token: Mapped[str | None] = mapped_column("refreshToken", Text)
    id_token: Mapped[str | None] = mapped_column("idToken", Text)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(
        "accessTokenExpiresAt", DateTime
    )
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        "refreshTokenExpiresAt", DateTime
    )
    scope: Mapped[str | None] = mapped_column(Text)
    password: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updatedAt", DateTime, default=utc_now, onupdate=utc_now
    )


class Verification(Base):
    __tablename__ = "Verification"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    identifier: Mapped[str] = mapped_column(Text)
    value: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column("expiresAt", DateTime)
    created_at: Mapped[datetime | None] = mapped_column(
        "createdAt", DateTime, server_default=func.now(), default=utc_now
    )
    updated_at: Mapped[datetime | None] = mapped_column("updatedAt", DateTime, onupdate=utc_now)
