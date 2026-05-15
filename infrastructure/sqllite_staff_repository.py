import sqlite3
from contextlib import closing
from uuid import UUID

from domain.custom_error import ConcurrentUpdateError
from domain.staff_entities import Staff
from domain.value_object import (
    Username,
    HashedPassword,
    NationalID,
    Name,
    DateOfBirth,
    PhoneNumber,
    StaffRole,
    Version,
)


class SqlStaffRepository:
    # =====================================================================
    # 1. SQL CONSTANTS (ศูนย์รวมคำสั่ง DB)
    # =====================================================================
    _CREATE_SCHEMA_QUERY = """
        CREATE TABLE IF NOT EXISTS staffs (
            staff_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            national_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            role TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    """

    _INSERT_STAFF_QUERY = """
        INSERT INTO staffs
        (staff_id, username, hashed_password, national_id, first_name, 
         last_name, date_of_birth, phone_number, role, version, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    _UPDATE_STAFF_QUERY = """
            UPDATE staffs SET
            hashed_password = ?, first_name = ?, 
            last_name = ?, date_of_birth = ?, phone_number = ?, role = ?, 
            version = ?, is_active = ?
            WHERE staff_id = ? AND version = ? 
        """

    _SELECT_BY_ID_QUERY = "SELECT * FROM staffs WHERE staff_id = ?"
    _SELECT_BY_USERNAME_QUERY = "SELECT * FROM staffs WHERE username = ?"

    # =====================================================================
    # 2. CORE METHODS (กระชับ อ่านปรู๊ดเดียวรู้เรื่อง)
    # =====================================================================
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._create_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_schema(self) -> None:
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(self._CREATE_SCHEMA_QUERY)

    def save(self, staff: Staff) -> None:
        """แปลงของลงกล่อง -> ยัดใส่ DB (ตอนนี้เน้น Insert ก่อน)"""
        with closing(self._get_connection()) as conn:
            with conn:
                # ในที่นี้สมมติว่าถ้าเรียก save คือสมัครใหม่ (Insert) เสมอ ถ้าวันหน้ามีระบบแก้ไขโปรไฟล์ ค่อยเติม
                # Update แบบที่ป๋าทำใน Queue ครับ
                data_tuple = self._map_entity_to_tuple(staff)
                conn.execute(self._INSERT_STAFF_QUERY, data_tuple)

    def update(self, staff: Staff) -> None:
        # ดึงเลขเวอร์ชันปัจจุบันจากในตู้ (ที่ส่งมาจาก Entity คือตัวที่ increment แล้ว)
        current_version, old_version = self._check_version(staff)

        data = self._map_staff_to_data_for_sql(staff, current_version, old_version)

        with closing(self._get_connection()) as conn:
            with conn:
                cursor = conn.execute(self._UPDATE_STAFF_QUERY, data)
                if cursor.rowcount == 0:
                    raise ConcurrentUpdateError(
                        entity_name="ข้อมูลพนักงาน", entity_id=staff.staff_id
                    )

    def get_by_username(self, username_str: str) -> Staff | None:
        """เอาไว้ใช้ตอนทำระบบ Login"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                self._SELECT_BY_USERNAME_QUERY, (username_str,)
            ).fetchone()
            if not row:
                return None
            return self._map_row_to_entity(row)

    def get_by_staff_id(self, staff_id: UUID) -> Staff | None:
        """เอาไว้ดึงข้อมูลประจำตัวทั่วไป"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(self._SELECT_BY_ID_QUERY, (str(staff_id),)).fetchone()
            if not row:
                return None
            return self._map_row_to_entity(row)

    # =====================================================================
    # 3. HELPER METHODS (ลูกมือรับจบงานถึกทน)
    # =====================================================================
    def _map_entity_to_tuple(self, staff: Staff) -> tuple:
        return (
            str(staff.staff_id),
            staff.username.id,  # หรือ .value ขึ้นอยู่กับที่ป๋าตั้งไว้ใน Value Object
            staff.hashed_password.value,
            staff.national_id.id,
            staff.first_name.value,
            staff.last_name.value,
            staff.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            staff.phone_number.value,
            staff.role.value,
            staff.version.number,
            staff.is_active,
        )

    def _map_row_to_entity(self, row: sqlite3.Row) -> Staff:
        return Staff(
            staff_id=UUID(row["staff_id"]),
            username=Username(
                id=row["username"]
            ),  # เปลี่ยนพารามิเตอร์ตาม Value Object ป๋า
            hashed_password=HashedPassword(value=row["hashed_password"]),
            national_id=NationalID(id=row["national_id"]),
            first_name=Name(value=row["first_name"]),
            last_name=Name(value=row["last_name"]),
            date_of_birth=DateOfBirth.model_validate_json(row["date_of_birth"]),
            phone_number=PhoneNumber(value=row["phone_number"]),
            role=StaffRole(row["role"]),
            version=Version(number=row["version"]),
            is_active=bool(row["is_active"]),
        )

    def _check_version(self, staff: Staff) -> tuple[int, int]:
        current_version = (
            staff.version.number
        )  # เวอร์ชันเดิมที่จะเอาไปค้นหาใน DB (WHERE)
        old_version = current_version - 1  # เวอร์ชันใหม่ที่จะเอาไปเซฟทับ (SET)
        return current_version, old_version

    def _map_staff_to_data_for_sql(
        self,
        staff: Staff,
        current_version,
        old_version,
    ) -> tuple:
        data = (
            staff.hashed_password.value,
            staff.first_name.value,
            staff.last_name.value,
            staff.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            staff.phone_number.value,
            staff.role.value,
            current_version,
            staff.is_active,
            str(staff.staff_id),
            old_version,
        )
        return data
