from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            name="uq_leave_balance_employee_type"
        ),
    )
    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False
    )
    leave_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    total_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    used_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )