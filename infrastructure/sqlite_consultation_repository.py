# infrastructure/sqlite_consultation_repository.py
import sqlite3
from contextlib import closing
from datetime import datetime
from uuid import UUID

from domain.consultation_entities import Consultation
from domain.custom_error import ConcurrentUpdateError
from domain.interfaces import ConsultationRepository
from domain.value_object import VitalSigns, Diagnosis, QueueStatus, Version


class SqlConsultationRepository(ConsultationRepository):
    # =====================================================================
    # 1. SQL CONSTANTS (ศูนย์รวมคำสั่ง DB)
    # =====================================================================
    _AUTO_CREATE_SCHEMA_QUERY = """
        CREATE TABLE IF NOT EXISTS consultations (
            id TEXT PRIMARY KEY,
            queue_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            vital_signs TEXT NOT NULL,       -- เก็บเป็น JSON
            diagnosis TEXT,                  -- เก็บเป็น JSON (เป็น NULL ได้ตอนเริ่มตรวจ)
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,        -- เก็บ ISO format
            finished_at TEXT,                -- เก็บ ISO format (เป็น NULL ได้)
            version INTEGER NOT NULL DEFAULT 1
        )
    """

    _INSERT_CONSULTATION_QUERY = """
        INSERT INTO consultations
        (id, queue_id, doctor_id, patient_id, vital_signs, diagnosis, 
         status, started_at, finished_at, version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    _UPDATE_CONSULTATION_QUERY = """
        UPDATE consultations SET
        vital_signs = ?, diagnosis = ?, status = ?, 
        finished_at = ?, version = ?
        WHERE id = ? AND version = ?
    """

    _SELECT_BY_QUEUE_ID_QUERY = """
        SELECT * FROM consultations WHERE queue_id = ?
    """

    _SELECT_BY_CONSULTATION_ID_QUERY = """
        SELECT * FROM consultations WHERE id = ?
    """

    # =====================================================================
    # 2. LIFECYCLE & DB CONNECTION
    # =====================================================================
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._auto_create_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _auto_create_schema(self) -> None:
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(self._AUTO_CREATE_SCHEMA_QUERY)

    # =====================================================================
    # 3. PUBLIC METHODS (ตู้เหล็กรับแขก)
    # =====================================================================
    def save(self, consultation: Consultation) -> None:
        with closing(self._get_connection()) as conn:
            with conn:
                data = self._map_entity_to_sql_schema(consultation)
                conn.execute(self._INSERT_CONSULTATION_QUERY, data)

    def update(self, consultation: Consultation) -> None:
        """อัปเดตใบตรวจ พร้อม Optimistic Locking ป้องกันหมอเซฟทับกัน"""
        current_version, old_version = self._check_version(consultation)

        data = self._map_update_entity_to_sql_schema(
            consultation, current_version, old_version
        )

        with closing(self._get_connection()) as conn:
            with conn:
                cursor = conn.execute(self._UPDATE_CONSULTATION_QUERY, data)
                if cursor.rowcount == 0:
                    raise ConcurrentUpdateError(
                        entity_name="ใบตรวจรักษา", entity_id=consultation.id
                    )

    def get_by_queue_id(self, queue_id: UUID) -> Consultation | None:
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                self._SELECT_BY_QUEUE_ID_QUERY, (str(queue_id),)
            ).fetchone()
            if not row:
                return None
            return self._map_sql_schema_to_entity(row)

    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation | None:
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                self._SELECT_BY_CONSULTATION_ID_QUERY, (str(consultation_id),)
            ).fetchone()
            if not row:
                return None
            return self._map_sql_schema_to_entity(row)

    # =====================================================================
    # 4. PRIVATE MAPPERS (ลูกมือแปลงร่างข้อมูล)
    # =====================================================================
    def _check_version(self, consultation: Consultation) -> tuple[int, int]:
        current_version = consultation.version.number
        old_version = current_version - 1
        return current_version, old_version

    def _map_entity_to_sql_schema(self, consultation: Consultation) -> tuple:
        return (
            str(consultation.id),
            str(consultation.queue_id),
            str(consultation.doctor_id),
            str(consultation.patient_id),
            consultation.vital_signs.model_dump_json(),
            (
                consultation.diagnosis.model_dump_json()
                if consultation.diagnosis
                else None
            ),
            consultation.status.value,
            consultation.started_at.isoformat(),
            consultation.finished_at.isoformat() if consultation.finished_at else None,
            consultation.version.number,
        )

    def _map_sql_schema_to_entity(self, row: sqlite3.Row) -> Consultation:
        return Consultation(
            id=UUID(row["id"]),
            queue_id=UUID(row["queue_id"]),
            doctor_id=UUID(row["doctor_id"]),
            patient_id=UUID(row["patient_id"]),
            vital_signs=VitalSigns.model_validate_json(row["vital_signs"]),
            diagnosis=(
                Diagnosis.model_validate_json(row["diagnosis"])
                if row["diagnosis"]
                else None
            ),
            status=QueueStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=(
                datetime.fromisoformat(row["finished_at"])
                if row["finished_at"]
                else None
            ),
            version=Version(number=row["version"]),
        )

    def _map_update_entity_to_sql_schema(
        self, consultation: Consultation, current_version: int, old_version: int
    ) -> tuple[str, str | None, str, str | None, int, str, int]:
        data = (
            consultation.vital_signs.model_dump_json(),
            (
                consultation.diagnosis.model_dump_json()
                if consultation.diagnosis
                else None
            ),
            consultation.status.value,
            consultation.finished_at.isoformat() if consultation.finished_at else None,
            current_version,
            str(consultation.id),
            old_version,
        )
        return data
