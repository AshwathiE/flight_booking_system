from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database.connection import Base
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    mobile_number = Column(
        String(50),
        nullable=True,
        default="",
        server_default=""
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")),
        nullable=False
    )

    role = Column(
        String(50),
        default="user",
        nullable=False
    )

    status = Column(
        String(50),
        default="active",
        nullable=False
    )
