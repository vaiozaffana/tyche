from fastapi import APIRouter, HTTPException

from api.dependencies import CurrentAuthDependency, DatabaseDependency
from api.modules.auth.router import user_response
from api.modules.profile.service import ProfileNotFoundError, update_profile
from api.schemas import ProfileResponse, UpdateProfileInput

router = APIRouter(prefix="/profile", tags=["profile"])


@router.patch("", response_model=ProfileResponse)
def patch_profile(
    input: UpdateProfileInput,
    auth: CurrentAuthDependency,
    database: DatabaseDependency,
) -> ProfileResponse:
    try:
        user = update_profile(
            database,
            auth.user.id,
            name=input.name,
            image=str(input.image) if input.image is not None else None,
            update_image="image" in input.model_fields_set,
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail="user_not_found") from error
    return ProfileResponse(user=user_response(user))
