from typing import LiteralString, Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from domain.consultation_entities import Consultation
from domain.custom_error import ConcurrentUpdateError
from domain.interfaces import ConsultationRepository
from domain.value_object import VitalSigns, Diagnosis, QueueStatus, Version


class PostgresConsultationRepository(ConsultationRepository):

    _INSERT_CONSULTATION_QUERY: LiteralString = """
        INSERT INTO 
        consultations (
                id, queue_id, doctor_id,
                patient_id, vital_signs,
                diagnosis, status, started_at,
                finished_at, version
        )
        VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    _UPDATE_CONSULTATION_QUERY: LiteralString = """
        UPDATE consultations SET
        vital_signs = %s, diagnosis = %s, 
        status = %s, started_at = %s,
        finished_at = %s, version = %s
        WHERE id = %s AND version = %s
    """

    _SELECT_CONSULTATION_ID_QUERY: LiteralString = """
        SELECT * FROM consultations WHERE id  = %s
    """

    _SELECT_QUEUE_ID_QUERY: LiteralString = """
        SELECT * FROM consultations WHERE queue_id  = %s
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        self.connection = connection

    # ==========================================
    # 📝 1. Helper Methods (ตัวช่วยแปลภาษาไป-กลับ)
    # ==========================================
    @staticmethod
    def _map_entity_to_tuple(consultation: Consultation) -> tuple:
        return (
            consultation.id,
            consultation.queue_id,
            consultation.doctor_id,
            consultation.patient_id,
            consultation.vital_signs.model_dump_json(),
            (
                consultation.diagnosis.model_dump_json()
                if consultation.diagnosis
                else None
            ),
            consultation.status.value,
            consultation.started_at,
            consultation.finished_at if consultation.finished_at else None,
            consultation.version.number,
        )

    @staticmethod
    def _map_row_to_entity(row: Any) -> Consultation:
        return Consultation(
            id=row["id"],
            queue_id=row["queue_id"],
            doctor_id=row["doctor_id"],
            patient_id=row["patient_id"],
            vital_signs=VitalSigns.model_validate_json(row["vital_signs"]),
            diagnosis=(
                Diagnosis.model_validate_json(row["diagnosis"])
                if row["diagnosis"]
                else None
            ),
            status=QueueStatus(row["status"]),
            started_at=row["started_at"],
            finished_at=(row["finished_at"]),
            version=Version(number=row["version"]),
        )

    @staticmethod
    def _map_update_entity_to_tuple(consultation: Consultation) -> tuple:
        return (
            consultation.vital_signs.model_dump_json(),
            (
                consultation.diagnosis.model_dump_json()
                if consultation.diagnosis
                else None
            ),
            consultation.status.value,
            consultation.started_at,
            consultation.finished_at if consultation.finished_at else None,
            consultation.version.number,
            consultation.id,
            consultation.version.previous.number,
        )

    # ==========================================
    # 🚀 2. Main Methods (เมธอดหลักที่ Domain เรียกใช้)
    # ==========================================
    def save(self, consultation: Consultation) -> None:

        value = self._map_entity_to_tuple(consultation)

        with self.connection.cursor() as cursor:
            cursor.execute(self._INSERT_CONSULTATION_QUERY, value)

        self.connection.commit()

    def update(self, consultation: Consultation) -> None:
        value = self._map_update_entity_to_tuple(consultation)

        with self.connection.cursor() as cursor:
            cursor.execute(self._UPDATE_CONSULTATION_QUERY, value)

            if cursor.rowcount == 0:
                raise ConcurrentUpdateError(
                    entity_name="ใบตรวจรักษา", entity_id=consultation.id
                )
        self.connection.commit()

    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation | None:

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_CONSULTATION_ID_QUERY, (str(consultation_id),))
            row = cursor.fetchone()

        if not row:
            return None
        return self._map_row_to_entity(row)

    def get_by_queue_id(self, queue_id: UUID) -> Consultation | None:

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_QUEUE_ID_QUERY, (str(queue_id),))
            row = cursor.fetchone()

        if not row:
            return None
        return self._map_row_to_entity(row)
