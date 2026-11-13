from datetime import UTC, datetime

from repo_db import User
from sqlalchemy.orm import Session as DatabaseSession


class ProfileNotFoundError(Exception):
    pass


def update_profile(
    database: DatabaseSession,
    user_id: str,
    *,
    name: str,
    image: str | None,
    update_image: bool,
) -> User:
    user = database.get(User, user_id)
    if not user:
        raise ProfileNotFoundError
    user.name = name
    if update_image:
        user.image = image
    user.updated_at = datetime.now(UTC).replace(tzinfo=None)
    database.commit()
    database.refresh(user)
    return user
