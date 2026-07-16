from datetime import date
from uuid import UUID

from sqlalchemy import BOOLEAN, INTEGER, TEXT, String, DATE
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.orm.base import Base


class StaffOrmModel(Base):
    __tablename__ = "staffs"

    staff_id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(60), nullable=False)
    national_id: Mapped[str] = mapped_column(String(13), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(DATE, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(10), nullable=False)
    role: Mapped[str] = mapped_column(TEXT, nullable=False)
    version: Mapped[int] = mapped_column(INTEGER, nullable=False)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, nullable=False)
