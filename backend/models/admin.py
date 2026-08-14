from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.database.connection import Base


class Admin(Base):
    __tablename__ = "admin"

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

    role = Column(
        String(20),
        nullable=False,
        default="admin"
    )

    status = Column(
        String(20),
        nullable=False,
        default="active"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )