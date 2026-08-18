from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime

from backend.database.connection import SessionLocal
from backend.models.user import User
from backend.models.admin import Admin
from backend.models.booking import Booking
from backend.schemas.auth import UserResponse
from backend.services.auth_service import get_current_admin

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin User Management"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    role: str

class UserStatusUpdate(BaseModel):
    status: str


@router.get("", response_model=List[UserResponse])
def get_all_users(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for email conflict
    if user.email != user_data.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")

    user.name = user_data.name
    user.email = user_data.email
    user.role = user_data.role

    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if status_data.status not in ["active", "inactive"]:
        raise HTTPException(status_code=422, detail="Invalid status value")

    user.status = status_data.status
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user has active bookings
    bookings = db.query(Booking).filter(Booking.user_id == user_id).count()
    if bookings > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete user with existing bookings. Please deactivate instead."
        )

    db.delete(user)
    db.commit()
    return


@router.get("/{user_id}/bookings")
def get_user_bookings(
    user_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()

    return {
        "success": True,
        "bookings": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "user_id": b.user_id,
                "flight_id": b.flight_id,
                "number_of_seats": b.number_of_seats,
                "total_price": b.total_price,
                "status": b.status,
                "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else None,
            }
            for b in bookings
        ],
    }

