from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.models.admin import Admin
from backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AdminLoginRequest,
    AdminLoginResponse
)
from backend.services.auth_service import (
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Authentication"]
)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/login",
    response_model=AdminLoginResponse
)
def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):

    admin = (
        db.query(Admin)
        .filter(
            Admin.email == login_data.email
        )
        .first()
    )

    if not admin:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if admin.status != "active":

        raise HTTPException(
            status_code=403,
            detail="Admin account is inactive"
        )

    if not verify_password(
        login_data.password,
        admin.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        admin.uuid
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.post("/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = (
        db.query(Admin)
        .filter(Admin.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user
    new_user = Admin(
        email=request.email,
        password_hash=hash_password(request.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "email": new_user.email
    }