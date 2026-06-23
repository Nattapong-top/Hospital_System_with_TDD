from datetime import date
from typing import Optional, List, LiteralString, Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from domain.entities import Queue
from domain.interfaces import QueueRecord
from domain.value_object import (
    QueueStatus,
    Version,
    VitalSigns,
    BloodPressure,
    Weight,
    Height,
    Temperature,
    Number,
)


class PostgresQueueRepository(QueueRecord):
    _INSERT_QUEUE_QUERY: LiteralString = """
        INSERT INTO queue (
            q_id, p_id, p_num, q_date, status, ver,
            bp_sys, bp_dia, w_kg, h_cm, temp_c, symptom,
            diag_disease, diag_treatment, diag_meds
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        );
    """

    _SELECT_BY_ID_QUERY: LiteralString = "SELECT * FROM queue WHERE q_id = %s"

    def __init__(self, connection: psycopg.Connection):
        self.connection = connection

    # ==========================================
    # 📝 1. Helper Methods (ตัวช่วยแปลภาษาไป-กลับ)
    # ==========================================
    @staticmethod
    def _map_entity_to_tuple(queue: Queue) -> tuple:
        """แปลงจาก Domain Entity เป็น Tuple เพื่อยัดลง DB"""
        vs = queue.vital_signs
        diag = queue.diagnosis

        # จัดการ JSONB ของยา
        meds_json = None
        if diag and diag.medicine_prescribed:
            meds_json = (
                "["
                + ",".join([m.model_dump_json() for m in diag.medicine_prescribed])
                + "]"
            )

        return (
            str(queue.id),
            str(queue.patient_id),
            queue.queue_number.id,
            queue.queue_date,
            queue.status.value,
            queue.version.number,
            vs.blood_pressure.systolic if vs else None,
            vs.blood_pressure.diastolic if vs else None,
            vs.weight.value if vs else None,
            vs.height.value if vs else None,
            vs.temperature.value if vs else None,
            vs.symptom if vs else None,
            diag.disease if diag else None,
            diag.treatment if diag else None,
            meds_json,
        )

    @staticmethod
    def _map_row_to_entity(row: dict | Any) -> Queue:
        """ประกอบร่างจาก Data Row ใน DB กลับเป็น Domain Entity"""
        # 1. ประกอบร่าง VitalSigns (ถ้ามีความดันหรืออาการป่วย ถือว่ามีข้อมูล)
        vital_signs_obj = None
        if row["bp_sys"] is not None or row["symptom"] is not None:
            vital_signs_obj = VitalSigns(
                blood_pressure=BloodPressure(
                    systolic=row["bp_sys"], diastolic=row["bp_dia"]
                ),
                weight=Weight(value=row["w_kg"]),
                height=Height(value=row["h_cm"]),
                temperature=Temperature(value=row["temp_c"]),
                symptom=row["symptom"],
            )

        # 2. ประกอบร่าง Diagnosis (ละไว้ก่อน เพราะตอนสร้างคิวใหม่จะยังเป็น None)
        diagnosis_obj = None

        # 3. ประกอบร่าง Queue
        return Queue(
            id=row["q_id"],
            patient_id=row["p_id"],
            queue_number=Number(id=row["p_num"]),
            queue_date=row["q_date"],
            status=QueueStatus(row["status"]),
            version=Version(number=row["ver"]),
            vital_signs=vital_signs_obj,
            diagnosis=diagnosis_obj,
        )

    # ==========================================
    # 🚀 2. Main Methods (เมธอดหลักที่ Domain เรียกใช้)
    # ==========================================
    def save(self, queue: Queue) -> None:
        """บันทึกคิวใหม่ (ตอนนี้โค้ดสั้นและสะอาดมาก!)"""
        values = self._map_entity_to_tuple(queue)
        with self.connection.cursor() as cursor:
            cursor.execute(self._INSERT_QUEUE_QUERY, values)
        self.connection.commit()

    def get_by_queue_id(self, queue_id: UUID) -> Queue | None:
        """ค้นหาคิวจาก ID"""
        # ใช้ dict_row เพื่อให้ดึงข้อมูลจากชื่อคอลัมน์ได้ (เช่น row["bp_sys"])
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_BY_ID_QUERY, (str(queue_id),))
            row = cursor.fetchone()

        if not row:
            return None

        return self._map_row_to_entity(row)

    def get_last_queue(self) -> Optional[Queue]:
        pass

    def update(self, queue: Queue) -> None:
        pass

    def find_active_queue_by_patient(
        self, patient_id: UUID, queue_date: date
    ) -> Optional[Queue]:
        pass

    def get_all_queues_today(self, today: date) -> List[Queue]:
        pass
