import sqlite3
from contextlib import closing
from typing import Optional
from uuid import UUID

from domain.custom_error import DuplicateNationalIDError
from domain.entities import Patient
from domain.interfaces import PatientRecord
from domain.value_object import (
    NationalID, PhoneNumber, Name, Address, Rights,
    PatientRights, DateOfBirth, Version
)


class SqlPatientRepository(PatientRecord):
    """
    IMPLEMENTATION: สถาปัตยกรรมระดับ Infrastructure
    ทำหน้าที่คุยกับ SQLite โดยเฉพาะ โดยใช้หลักการ Hybrid (Flat Columns + JSON)
    """

    # --- 1. SQL Constants: แยกคำสั่ง SQL ออกมาให้แก้ไขง่ายที่จุดเดียว ---
    _CREATE_SCHEMA_QUERY = """
        CREATE TABLE IF NOT EXISTS patient (
            id TEXT PRIMARY KEY,
            national_id TEXT UNIQUE,
            first_name TEXT,
            last_name TEXT,
            phone_number TEXT,
            date_of_birth TEXT,    -- เก็บเป็น JSON
            registered_address TEXT, -- เก็บเป็น JSON
            current_address TEXT,    -- เก็บเป็น JSON
            rights TEXT,
            version INTEGER DEFAULT 1
        )
    """

    _INSERT_PATIENT_QUERY = """
        INSERT INTO patient (
            id, 
            national_id, 
            first_name, 
            last_name, 
            phone_number, 
            date_of_birth, 
            registered_address, 
            current_address, 
            rights,
            version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    _UPDATE_QUERY = """
        UPDATE patient SET 
            first_name = ?, 
            last_name = ?, 
            phone_number = ?, 
            date_of_birth = ?, 
            registered_address = ?, 
            current_address = ?, 
            rights = ?,
            version = ?
            WHERE id = ? AND version = ?
    """

    _SELECT_BY_NATIONAL_ID_QUERY = "SELECT * FROM patient WHERE national_id = ?"

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._auto_create_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # ช่วยให้ดึงข้อมูลด้วยชื่อคอลัมน์ได้ (row['id'])
        return conn

    def _auto_create_schema(self):
        """สร้างตารางอัตโนมัติเมื่อเริ่มใช้งาน (Idempotent)"""
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(self._CREATE_SCHEMA_QUERY)

    # --- 2. Interface Methods: ทำตามสัญญาที่ให้ไว้กับ Domain ---

    def save(self, patient: Patient) -> None:
        """บันทึกข้อมูล และจัดการ Error ของ Database ให้เป็นภาษา Domain"""
        try:
            with closing(self._get_connection()) as conn:
                with conn:
                    data = self._map_entity_to_tuple(patient)
                    conn.execute(self._INSERT_PATIENT_QUERY, data)
        except sqlite3.IntegrityError as error:
            # ดักจับ 'UNIQUE constraint failed' แล้วแปลงเป็น Domain Error
            if 'national_id' in str(error):
                raise DuplicateNationalIDError(f'เลขบัตรประชาชนนี้มีในระบบแล้ว: {patient.national_id.id}')
            raise error

    def update(self, patient: Patient) -> None:
        # ดึงเลขเวอร์ชันปัจจุบันจากในตู้ (ที่ส่งมาจาก Entity คือตัวที่ increment แล้ว)
        current_version, old_version = self._check_version(patient)

        data = self._map_entity_patient_update(current_version, old_version, patient)

        with closing(self._get_connection()) as conn:
            with conn:
                cursor = conn.execute(self._UPDATE_QUERY, data)
                if cursor.rowcount == 0:
                    raise RuntimeError(f'มีคนอื่น update ข้อมูลคนไข้ไปแล้วก่อนหน้านี้')

    def get_by_national_id(self, national_id: NationalID) -> Optional[Patient]:
        """ค้นหาและปั้นร่าง (Rehydrate) ข้อมูลกลับเป็น Entity"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(self._SELECT_BY_NATIONAL_ID_QUERY, (str(national_id.id),)).fetchone()
            return self._map_row_to_entity(row) if row else None

    # --- 3. Mapper Logic: แยกส่วนการแปลงข้อมูลออกไปให้ชัดเจน ---

    def _map_entity_to_tuple(self, patient: Patient) -> tuple:
        """แปลงก้อน Entity ให้เป็น Tuple สำหรับยัดลง SQL (Flattening)"""
        return (
            str(patient.id),
            patient.national_id.id,
            patient.first_name.value,
            patient.last_name.value,
            patient.phone_number.value,
            patient.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            patient.registered_address.model_dump_json(),  # แปลง VO เป็น JSON
            patient.current_address.model_dump_json(),  # แปลง VO เป็น JSON
            patient.rights.rights_type.value,
            patient.version.number,
        )

    def _map_row_to_entity(self, row: sqlite3.Row) -> Patient:
        """แปลง Row จากฐานข้อมูลกลับเป็น Entity (Rehydration)"""
        return Patient(
            id=UUID(row['id']),
            national_id=NationalID(id=row['national_id']),
            first_name=Name(value=row['first_name']),
            last_name=Name(value=row['last_name']),
            phone_number=PhoneNumber(value=row['phone_number']),
            date_of_birth=DateOfBirth.model_validate_json(row['date_of_birth']),
            registered_address=Address.model_validate_json(row['registered_address']),
            current_address=Address.model_validate_json(row['current_address']),
            rights=Rights(rights_type=PatientRights(row['rights'])),
            version=Version(number=row['version'])
        )

    def _check_version(self, patient: Patient) -> tuple[int, int]:
        current_version = patient.version.number
        old_version = current_version - 1
        return current_version, old_version

    def _map_entity_patient_update(self, current_version: int, old_version: int,
                                   patient: Patient) -> tuple[str, str, str, str,
    str, str, str, int, str, int]:

        data = (
            patient.first_name.value,
            patient.last_name.value,
            patient.phone_number.value,
            patient.date_of_birth.model_dump_json(),  # แปลง VO เป็น JSON
            patient.registered_address.model_dump_json(),  # แปลง VO เป็น JSON
            patient.current_address.model_dump_json(),  # แปลง VO เป็น JSON
            patient.rights.rights_type.value,
            current_version,
            str(patient.id),
            old_version
        )
        return data
