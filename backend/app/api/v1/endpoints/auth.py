import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LogoutResponse, Token, UserCreate, UserLogin, UserResponse

logger = logging.getLogger("retail_kpi.auth")
router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Registers a new platform user with email, username, and secure password.",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user:
    - Checks for unique email and username
    - Hashes password using bcrypt with salt rounds 12
    - Creates database record with assigned role
    - Returns JWT Bearer token and user profile
    """
    normalized_email = user_in.email.strip().lower()
    normalized_username = user_in.username.strip().lower()

    # 1. Check duplicate email
    existing_email = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # 2. Check duplicate username
    existing_username = (
        db.query(User)
        .filter(func.lower(User.username) == normalized_username)
        .first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )

    # 3. Validate & sanitize role
    role = (user_in.role or "analyst").strip().lower()
    if role not in ["admin", "analyst", "manager"]:
        role = "analyst"

    # 4. Hash password securely
    hashed_pwd = get_password_hash(user_in.password)

    # 5. Create user record
    new_user = User(
        email=normalized_email,
        username=user_in.username.strip(),
        full_name=user_in.full_name.strip() if user_in.full_name else None,
        hashed_password=hashed_pwd,
        role=role,
        is_active=True,
        is_superuser=(role == "admin"),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("New user registered: %s (%s)", new_user.username, new_user.role)

    # 6. Issue access token
    access_token = create_access_token(
        subject=str(new_user.id),
        extra_claims={
            "email": new_user.email,
            "username": new_user.username,
            "role": new_user.role,
        },
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User login & token issuance",
    description="Authenticates via JSON payload or Swagger form-data and returns a signed JWT access token.",
)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user credentials:
    - Supports JSON body { "username": "...", "password": "..." }
    - Supports OAuth2 form-data (for Swagger UI Authorize button)
    - Validates bcrypt hash
    - Checks active account status
    - Returns JWT access token
    """
    content_type = request.headers.get("content-type", "")
    username: str = ""
    password: str = ""

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))
    else:
        try:
            body = await request.json()
            username = str(body.get("username", "")).strip()
            password = str(body.get("password", ""))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid request body. Expected JSON with username and password.",
            )

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both username/email and password are required.",
        )

    # Look up user by case-insensitive email or username
    user = (
        db.query(User)
        .filter(
            (func.lower(User.email) == username.lower())
            | (func.lower(User.username) == username.lower())
        )
        .first()
    )

    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Failed login attempt for user identifier: %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Login attempted for disabled user: %s", username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive. Please contact your system administrator.",
        )

    logger.info("Successful login: %s (%s)", user.username, user.role)

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "email": user.email,
            "username": user.username,
            "role": user.role,
        },
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user identified by the Bearer token.",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Protected endpoint:
    Requires valid Bearer Authorization header. Returns user id, email, username,
    full name, role, and permissions.
    """
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
    description="Invalidates user session client-side and acknowledges logout.",
)
def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Protected logout endpoint:
    Confirms token validity and logs out user session.
    """
    logger.info("User logged out: %s", current_user.username)
    return LogoutResponse(
        message=f"User '{current_user.username}' successfully logged out."
    )
