from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.models.admin import Admin
from backend.models.user import User
from backend.models.flight import Flight
from backend.schemas.auth import (
    AdminLoginRequest,
    TokenResponse,
    AdminResponse,
)
from backend.services.auth_service import (
    verify_password,
    create_access_token,
    get_current_admin,
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


@router.post("/login", response_model=TokenResponse)
def admin_login(
    request: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    admin = db.query(Admin).filter(Admin.email == request.email).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if admin.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )

    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(user_id=admin.id, role="admin")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "admin",
        "admin": AdminResponse.model_validate(admin)
    }


@router.get("/me", response_model=AdminResponse)
def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin)
):
    return current_admin


@router.get("/dashboard-stats")
def get_admin_dashboard_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_admins = db.query(Admin).count()
    total_flights = db.query(Flight).count()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_flights": total_flights,
        "system_status": "Healthy",
        "mcp_server": "Connected"
    }
