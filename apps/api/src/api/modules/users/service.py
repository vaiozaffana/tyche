from repo_db import User
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session as DatabaseSession


class InvalidUsersCursorError(Exception):
    pass


def list_recent_users(
    database: DatabaseSession, *, cursor: str | None, limit: int
) -> tuple[list[User], str | None]:
    cursor_user = database.get(User, cursor) if cursor else None
    if cursor and not cursor_user:
        raise InvalidUsersCursorError

    query = select(User)
    if cursor_user:
        query = query.where(
            or_(
                User.created_at < cursor_user.created_at,
                and_(User.created_at == cursor_user.created_at, User.id < cursor_user.id),
            )
        )
    users = list(
        database.scalars(query.order_by(User.created_at.desc(), User.id.desc()).limit(limit + 1))
    )
    visible = users[:limit]
    return visible, visible[-1].id if len(users) > limit else None
