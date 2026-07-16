from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session
from domain.staff_entities import Staff
from infrastructure.orm.staff_orm_model import StaffOrmModel

from domain.value_object import (
    NationalID,
    Username,
    HashedPassword,
    Name,
    DateOfBirth,
    PhoneNumber,
    StaffRole,
    Version,
)


class SqlAlchemyStaffRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, staff: Staff) -> None:
        staff_orm = StaffOrmModel(
            staff_id=staff.staff_id,
            username=staff.username.id,
            hashed_password=staff.hashed_password.value,
            national_id=staff.national_id.id,
            first_name=staff.first_name.value,
            last_name=staff.last_name.value,
            date_of_birth=date(
                staff.date_of_birth.year,
                staff.date_of_birth.month,
                staff.date_of_birth.day,
            ),
            phone_number=staff.phone_number.value,
            role=staff.role.value,
            version=staff.version.current_number,
            is_active=staff.is_active,
        )

        self.session.add(staff_orm)
        self.session.commit()

    def get_by_staff_id(self, staff_id: UUID) -> Staff | None:
        staff_orm = self.session.get(StaffOrmModel, staff_id)

        if staff_orm is None:
            return None
        return Staff(
            staff_id=staff_orm.staff_id,
            username=Username(id=staff_orm.username),
            hashed_password=HashedPassword(value=staff_orm.hashed_password),
            national_id=NationalID(id=staff_orm.national_id),
            first_name=Name(value=staff_orm.first_name),
            last_name=Name(value=staff_orm.last_name),
            date_of_birth=DateOfBirth(
                year=staff_orm.date_of_birth.year,
                month=staff_orm.date_of_birth.month,
                day=staff_orm.date_of_birth.day,
            ),
            phone_number=PhoneNumber(value=staff_orm.phone_number),
            role=StaffRole(staff_orm.role),
            version=Version(
                current_number=staff_orm.version,
                previous_number=staff_orm.version,
            ),
            is_active=bool(staff_orm.is_active),
        )
