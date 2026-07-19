from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.staff_entities import Staff
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
from infrastructure.orm.staff_orm_model import StaffOrmModel


class SqlAlchemyStaffRepository:

    # method helper
    @staticmethod
    def _to_staff_entity(staff_orm: StaffOrmModel) -> Staff:
        staff = Staff(
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
        return staff

    # main method
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
        staff = self._to_staff_entity(staff_orm)
        return staff

    def get_by_username(self, username: Username) -> Staff | None:

        statement = select(StaffOrmModel).where(StaffOrmModel.username == username.id)

        staff_orm = self.session.scalars(statement).one_or_none()

        if staff_orm is None:
            return None
        staff = self._to_staff_entity(staff_orm)
        return staff
