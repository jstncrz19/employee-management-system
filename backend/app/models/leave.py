from datetime import date, datetime
from enum import Enum

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class LeaveType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    EMERGENCY = "emergency"
    OTHER = "other"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Leave(Base):
    __tablename__ = "leaves"

    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="ck_leaves_valid_date_range"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False
    )
    leave_type: Mapped[LeaveType] = mapped_column(
        String(20),
        nullable=False
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    status: Mapped[LeaveStatus] = mapped_column(
        String(20),
        nullable=False,
        default=LeaveStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
