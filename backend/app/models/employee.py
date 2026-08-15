from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    position: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    date_hired: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )