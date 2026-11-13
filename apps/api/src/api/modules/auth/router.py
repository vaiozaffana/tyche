from fastapi import APIRouter, HTTPException, Request, Response
from repo_db import Session, User

from api.dependencies import (
    CurrentAuthDependency,
    DatabaseDependency,
    OptionalAuthDependency,
)
from api.modules.auth.service import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    issue_session,
    register_user,
)
from api.schemas import (
    AuthResponse,
    CurrentSessionResponse,
    LoginInput,
    RegisterInput,
    SessionResponse,
    UserResponse,
)
from api.settings import Settings

router = APIRouter()


def user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


def session_response(session: Session) -> SessionResponse:
    return SessionResponse.model_validate(session, from_attributes=True)


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        "session",
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


@router.post("/api/auth/sign-up/email", response_model=AuthResponse)
def register(
    input: RegisterInput,
    request: Request,
    response: Response,
    database: DatabaseDependency,
) -> AuthResponse:
    try:
        user = register_user(
            database,
            email=str(input.email),
            name=input.name,
            password=input.password,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status_code=400, detail="Email is already registered.") from error
    _, token = issue_session(
        database,
        user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    set_session_cookie(response, token, request.app.state.settings)
    return AuthResponse(user=user_response(user))


@router.post("/api/auth/sign-in/email", response_model=AuthResponse)
def login(
    input: LoginInput,
    request: Request,
    response: Response,
    database: DatabaseDependency,
) -> AuthResponse:
    user = authenticate_user(database, str(input.email), input.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _, token = issue_session(
        database,
        user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    set_session_cookie(response, token, request.app.state.settings)
    return AuthResponse(user=user_response(user))


@router.post("/api/auth/sign-out")
def logout(
    response: Response,
    database: DatabaseDependency,
    auth: OptionalAuthDependency,
) -> dict[str, bool]:
    if auth:
        database.delete(auth.session)
        database.commit()
    response.delete_cookie("session", path="/")
    return {"success": True}


@router.get("/session", response_model=CurrentSessionResponse)
def current_session(auth: CurrentAuthDependency) -> CurrentSessionResponse:
    return CurrentSessionResponse(
        session=session_response(auth.session), user=user_response(auth.user)
    )
