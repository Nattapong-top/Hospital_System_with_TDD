import psycopg
from domain.entities import Patient
from domain.interfaces import PatientRecord  # เรียกใช้ Interface เดิมจาก Domain


class PostgresPatientRepository(PatientRecord):
    """
    Adapter สำหรับจัดการข้อมูล Patient กับฐานข้อมูล PostgreSQL
    """

    # --- SQL Constants: รวม SQL ไว้ที่เดียว ---
    _CREATE_SCHEMA_QUERY = """
        CREATE TABLE IF NOT EXISTS patient (
            id UUID PRIMARY KEY,
            national_id VARCHAR(13) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            date_of_birth JSONB NOT NULL,
            registered_address JSONB NOT NULL,
            current_address JSONB NOT NULL,
            rights VARCHAR(50) NOT NULL,
            version INTEGER DEFAULT 1
        );
    """

    _INSERT_PATIENT_QUERY = """
        INSERT INTO patient (
            id, national_id, first_name, last_name, phone_number,
            date_of_birth, registered_address, current_address, rights, version
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        self.connection = connection

    def create_schema(self) -> None:
        """สร้างตารางสำหรับใช้ใน Test (Production ควรใช้ Migration Tool)"""
        with self.connection.cursor() as cur:
            cur.execute(self._CREATE_SCHEMA_QUERY)
        self.connection.commit()

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

        with self.connection.cursor() as cur:
            cur.execute(self._INSERT_PATIENT_QUERY, values)
        self.connection.commit()

    def get_by_national_id(self, national_id: int) -> Patient:
        pass

    def update(self, patient: Patient) -> None:
        pass
