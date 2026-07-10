from typing import Optional, LiteralString, Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from domain.custom_error import ConcurrentUpdateError
from domain.interfaces import StaffRepository
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


class PostgresStaffRepository(StaffRepository):
    _INSERT_INTO_STAFFS_QUERY: LiteralString = """
        INSERT INTO staffs (
            staff_id, username,
            hashed_password, 
            national_id,
            first_name,
            last_name,
            date_of_birth,
            phone_number,
            role, version,
            is_active
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) 
    """

    _UPDATE_STAFF_QUERY: LiteralString = """
        UPDATE staffs SET 
        hashed_password = %s, 
        first_name = %s, 
        last_name = %s, 
        date_of_birth = %s, 
        phone_number = %s, 
        role = %s, 
        version = %s, 
        is_active = %s
        WHERE staff_id = %s 
        AND version = %s
    """

    _SELECT_STAFF_ID_QUERY: LiteralString = """
        SELECT * FROM staffs WHERE staff_id = %s
    """

    _SELECT_NATIONAL_ID_QUERY: LiteralString = """
        SELECT * FROM staffs WHERE national_id = %s
    """

    _SELECT_EXISTS_NATIONAL_ID_QUERY: LiteralString = """
        SELECT EXISTS (SELECT 1 FROM staffs WHERE national_id = %s)
    """

    @staticmethod
    def _map_staff_to_tuple(staff: Staff) -> tuple:
        return (
            staff.staff_id,
            staff.username.id,  # หรือ .value ขึ้นอยู่กับที่ป๋าตั้งไว้ใน Value Object
            staff.hashed_password.value,
            staff.national_id.id,
            staff.first_name.value,
            staff.last_name.value,
            staff.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            staff.phone_number.value,
            staff.role.value,
            staff.version.current_number,
            staff.is_active,
        )

    @staticmethod
    def _map_update_staff_to_tuple(staff: Staff) -> tuple:
        return (
            staff.hashed_password.value,
            staff.first_name.value,
            staff.last_name.value,
            staff.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            staff.phone_number.value,
            staff.role.value,
            staff.version.current_number,
            staff.is_active,
            staff.staff_id,
            staff.version.previous_number,
        )

    @staticmethod
    def _map_row_to_staff(row: Any) -> Staff:
        return Staff(
            staff_id=row["staff_id"],
            username=Username(id=row["username"]),
            hashed_password=HashedPassword(value=row["hashed_password"]),
            national_id=NationalID(id=row["national_id"]),
            first_name=Name(value=row["first_name"]),
            last_name=Name(value=row["last_name"]),
            date_of_birth=DateOfBirth.model_validate(row["date_of_birth"]),
            phone_number=PhoneNumber(value=row["phone_number"]),
            role=StaffRole(row["role"]),
            version=Version(
                current_number=row["version"],
                previous_number=row["version"],
            ),
            is_active=bool(row["is_active"]),
        )

    def __init__(self, db_connect: psycopg.Connection) -> None:
        self.db_connect = db_connect

    def save(self, staff: Staff) -> None:

        value = self._map_staff_to_tuple(staff)

        with self.db_connect.cursor() as cursor:
            cursor.execute(self._INSERT_INTO_STAFFS_QUERY, value)

        self.db_connect.commit()

    def update(self, staff: Staff) -> None:

        value = self._map_update_staff_to_tuple(staff)
        with self.db_connect.cursor() as cursor:
            cursor.execute(self._UPDATE_STAFF_QUERY, value)

            if cursor.rowcount != 1:
                self.db_connect.rollback()
                raise ConcurrentUpdateError(
                    entity_name="ข้อมูลพนักงาน", entity_id=staff.staff_id
                )

        self.db_connect.commit()

    def get_by_username(self, username: Username) -> Optional[Staff]:
        raise NotImplementedError

    def get_by_staff_id(self, staff_id: UUID) -> Optional[Staff]:
        with self.db_connect.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_STAFF_ID_QUERY, (str(staff_id),))
            row = cursor.fetchone()
        if row is None:
            return None
        return self._map_row_to_staff(row)

    def get_by_national_id_staff(self, national_id: NationalID) -> Optional[Staff]:
        with self.db_connect.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_NATIONAL_ID_QUERY, (str(national_id.id),))
            row = cursor.fetchone()
        if row is None:
            return None
        return self._map_row_to_staff(row)

    def is_national_id_exists(self, national_id: NationalID) -> bool:
        with self.db_connect.cursor() as cursor:
            cursor.execute(
                self._SELECT_EXISTS_NATIONAL_ID_QUERY, (str(national_id.id),)
            )
            boolean = cursor.fetchone()

            if boolean is None:
                return False

            return boolean[0]
