from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import AdminAuthDependency, DatabaseDependency
from api.modules.users.service import InvalidUsersCursorError, list_recent_users
from api.schemas import UserListItem, UsersResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UsersResponse)
def users(
    _auth: AdminAuthDependency,
    database: DatabaseDependency,
    cursor: Annotated[str | None, Query(min_length=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UsersResponse:
    try:
        rows, next_cursor = list_recent_users(database, cursor=cursor, limit=limit)
    except InvalidUsersCursorError as error:
        raise HTTPException(status_code=400, detail="invalid_cursor") from error
    return UsersResponse(
        next_cursor=next_cursor,
        users=[UserListItem.model_validate(row, from_attributes=True) for row in rows],
    )
