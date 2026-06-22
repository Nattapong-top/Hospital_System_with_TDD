import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from domain.custom_error import ConcurrentUpdateError, DuplicateNationalIDError
from domain.entities import Patient
from domain.interfaces import PatientRecord  # เรียกใช้ Interface เดิมจาก Domain
from domain.value_object import (
    NationalID,
    Name,
    PhoneNumber,
    DateOfBirth,
    Address,
    Rights,
    Version,
    PatientRights,
)


class PostgresPatientRepository(PatientRecord):
    """
    Adapter สำหรับจัดการข้อมูล Patient กับฐานข้อมูล PostgreSQL
    """

    # --- SQL Constants: รวม SQL ไว้ที่เดียว ---

    _INSERT_PATIENT_QUERY = """
        INSERT INTO patient (
            id, national_id, first_name, last_name, phone_number,
            date_of_birth, registered_address, current_address, rights, version
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """

    _SELECT_BY_NATIONAL_ID_QUERY = """
        SELECT id, national_id, first_name, last_name, phone_number,
            date_of_birth, registered_address, current_address, rights, version 
            FROM patient WHERE national_id = %s;
            """

    _UPDATE_PATIENT_QUERY = """
        UPDATE patient 
            SET first_name = %s,
                last_name = %s,
                phone_number = %s,
                date_of_birth = %s,
                registered_address = %s,
                current_address = %s,
                rights = %s,
                version = %s
            WHERE id = %s AND version = %s;
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        self.connection = connection

    def save(self, patient: Patient) -> None:
        values = (
            patient.id,
            patient.national_id.id,
            patient.first_name.value,
            patient.last_name.value,
            patient.phone_number.value,
            patient.date_of_birth.model_dump_json(),
            patient.registered_address.model_dump_json(),
            patient.current_address.model_dump_json(),
            patient.rights.rights_type.value,
            patient.version.number,
        )

        try:
            with self.connection.cursor() as cur:
                cur.execute(self._INSERT_PATIENT_QUERY, values)
            self.connection.commit()

        except UniqueViolation:
            # กฎเหล็ก Postgres: ถ้าเกิด Error ใน Transaction ต้อง Rollback ก่อนเสมอ!
            self.connection.rollback()

            # แปลงร่าง Database Error ให้กลายเป็น Domain Error
            raise DuplicateNationalIDError(
                f"เลขบัตรประชาชนนี้มีในระบบแล้ว: {patient.national_id.id}"
            )

    def get_by_national_id(self, national_id: NationalID) -> Patient | None:

        with self.connection.cursor(row_factory=dict_row) as cur:
            cur.execute(self._SELECT_BY_NATIONAL_ID_QUERY, (national_id.id,))
            row_patient = cur.fetchone()

        if not row_patient:
            return None

        return Patient(
            id=row_patient["id"],
            national_id=NationalID(id=row_patient["national_id"]),
            first_name=Name(value=row_patient["first_name"]),
            last_name=Name(value=row_patient["last_name"]),
            phone_number=PhoneNumber(value=row_patient["phone_number"]),
            date_of_birth=(
                DateOfBirth.model_validate(row_patient["date_of_birth"])
                if isinstance(row_patient["date_of_birth"], dict)
                else DateOfBirth.model_validate_json(row_patient["date_of_birth"])
            ),
            registered_address=(
                Address.model_validate(row_patient["registered_address"])
                if isinstance(row_patient["registered_address"], dict)
                else Address.model_validate_json(row_patient["registered_address"])
            ),
            current_address=(
                Address.model_validate(row_patient["current_address"])
                if isinstance(row_patient["current_address"], dict)
                else Address.model_validate_json(row_patient["current_address"])
            ),
            rights=Rights(rights_type=PatientRights(row_patient["rights"])),
            version=Version(number=row_patient["version"]),
        )

    def update(self, patient: Patient) -> None:
        current_version = patient.version.number
        old_version = current_version - 1

        values = (
            patient.first_name.value,
            patient.last_name.value,
            patient.phone_number.value,
            patient.date_of_birth.model_dump_json(),
            patient.registered_address.model_dump_json(),
            patient.current_address.model_dump_json(),
            patient.rights.rights_type.value,
            current_version,
            patient.id,
            old_version,
        )

        with self.connection.cursor() as cur:
            cur.execute(self._UPDATE_PATIENT_QUERY, values)

            if cur.rowcount == 0:
                self.connection.rollback()
                raise ConcurrentUpdateError()

        self.connection.commit()
