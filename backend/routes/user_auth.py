from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.models.user import User
from backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["User Authentication"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=TokenResponse)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        mobile_number=request.mobile_number or ""
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(user_id=new_user.id, role="user")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "user",
        "user": UserResponse.model_validate(new_user)
    }


@router.post("/login", response_model=TokenResponse)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(user_id=user.id, role="user")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "user",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the logged-in user's profile details.
    """
    if request.email != current_user.email:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered by another user"
            )

    current_user.name = request.name
    current_user.email = request.email
    current_user.mobile_number = request.mobile_number or ""

    if request.password:
        current_user.password_hash = hash_password(request.password)

    db.commit()
    db.refresh(current_user)
    return current_user
