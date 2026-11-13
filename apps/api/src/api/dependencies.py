from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request
from repo_db import Session, User
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.orm import sessionmaker

from api.modules.auth.service import is_user_banned


@dataclass(frozen=True)
class AuthContext:
    session: Session
    user: User


def get_db(request: Request) -> Iterator[DatabaseSession]:
    factory = cast(sessionmaker[DatabaseSession], request.app.state.session_factory)
    with factory() as database:
        yield database


DatabaseDependency = Annotated[DatabaseSession, Depends(get_db)]


def get_optional_auth(request: Request, database: DatabaseDependency) -> AuthContext | None:
    raw_token = request.cookies.get("session")
    if not raw_token:
        return None
    stored = database.execute(
        select(Session, User)
        .join(User, Session.user_id == User.id)
        .where(Session.token == sha256(raw_token.encode()).hexdigest())
    ).one_or_none()
    if not stored:
        return None
    session, user = stored
    now = datetime.now(UTC).replace(tzinfo=None)
    if session.expires_at <= now or is_user_banned(user, now):
        database.delete(session)
        database.commit()
        return None
    return AuthContext(session=session, user=user)


OptionalAuthDependency = Annotated[AuthContext | None, Depends(get_optional_auth)]


def get_current_auth(auth: OptionalAuthDependency) -> AuthContext:
    if auth is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return auth


CurrentAuthDependency = Annotated[AuthContext, Depends(get_current_auth)]


def get_admin_auth(auth: CurrentAuthDependency) -> AuthContext:
    if "admin" not in (auth.user.role or "").split(","):
        raise HTTPException(status_code=403, detail="forbidden")
    return auth


AdminAuthDependency = Annotated[AuthContext, Depends(get_admin_auth)]
