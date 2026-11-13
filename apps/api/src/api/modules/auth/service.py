import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from pwdlib import PasswordHash
from repo_db import Account, Session, User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

password_hash = PasswordHash.recommended()


class EmailAlreadyRegisteredError(Exception):
    pass


def is_user_banned(user: User, now: datetime | None = None) -> bool:
    if not user.banned:
        return False
    return user.ban_expires is None or user.ban_expires > (
        now or datetime.now(UTC).replace(tzinfo=None)
    )


def register_user(
    database: DatabaseSession,
    *,
    email: str,
    name: str,
    password: str,
    role: str = "user",
) -> User:
    user_id = secrets.token_urlsafe(16)
    user = User(
        id=user_id,
        email=email.strip().lower(),
        name=name.strip(),
        role=role,
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    database.add(user)
    try:
        database.flush()
    except IntegrityError as error:
        database.rollback()
        raise EmailAlreadyRegisteredError from error
    database.add(
        Account(
            id=secrets.token_urlsafe(16),
            account_id=user_id,
            provider_id="credential",
            user_id=user_id,
            password=password_hash.hash(password),
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    try:
        database.commit()
    except Exception:
        database.rollback()
        raise
    database.refresh(user)
    return user


def authenticate_user(database: DatabaseSession, email: str, password: str) -> User | None:
    row = database.execute(
        select(User, Account)
        .join(Account, Account.user_id == User.id)
        .where(User.email == email.strip().lower(), Account.provider_id == "credential")
    ).one_or_none()
    if not row:
        return None
    user, account = row
    if (
        is_user_banned(user)
        or not account.password
        or not password_hash.verify(password, account.password)
    ):
        return None
    return user


def issue_session(
    database: DatabaseSession,
    user: User,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[Session, str]:
    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(UTC).replace(tzinfo=None)
    session = Session(
        id=secrets.token_urlsafe(16),
        user_id=user.id,
        token=sha256(raw_token.encode()).hexdigest(),
        expires_at=now + timedelta(days=30),
        created_at=now,
        updated_at=now,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    database.add(session)
    database.commit()
    database.refresh(session)
    return session, raw_token
