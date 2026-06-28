from datetime import date
from typing import List, LiteralString, Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from domain.custom_error import ConcurrentUpdateError
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
    Diagnosis,
    MedicineInfo,
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

    _UPDATE_QUEUE_QUERY: LiteralString = """
        UPDATE queue
            SET status = %s, ver = %s,
                bp_sys = %s, bp_dia = %s, w_kg = %s, h_cm = %s, temp_c = %s, symptom = %s,
                diag_disease = %s, diag_treatment = %s, diag_meds = %s
            WHERE q_id = %s AND ver = %s
        """

    _SELECT_BY_ID_QUERY: LiteralString = "SELECT * FROM queue WHERE q_id = %s"

    _SELECT_LAST_QUEUE_QUERY: LiteralString = """
        SELECT * FROM queue 
            WHERE q_date = %s
            ORDER BY p_num DESC
            LIMIT 1
    """

    _SELECT_ACTIVE_QUEUE_QUERY: LiteralString = """
        SELECT * FROM queue 
            WHERE p_id = %s
                AND  q_date = %s
                AND status NOT IN (%s, %s) 
            LIMIT 1
    """

    _SELECT_ALL_TODAY_QUERY: LiteralString = """
        SELECT * FROM queue 
            WHERE q_date = %s
            ORDER BY p_num ASC
    """

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
        # 1. ประกอบร่าง VitalSigns (เหมือนเดิม)
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

        # 2. ประกอบร่าง Diagnosis 🌟 (อัปเกรดใหม่ ดึง JSONB ได้แล้ว!)
        diagnosis_obj = None
        if row["diag_disease"] is not None:
            meds_list = []
            if row["diag_meds"]:
                raw_meds = row["diag_meds"]
                # Postgres อาจจะคืนค่ากลับมาเป็น String หรือ List Dict ขึ้นอยู่กับ Driver
                # เราเลยดักแปลงเป็น Dict แล้วโยนเข้า Pydantic ให้ประกอบเป็น MedicineInfo
                import json

                if isinstance(raw_meds, str):
                    raw_meds = json.loads(raw_meds)

                for m_dict in raw_meds:
                    meds_list.append(MedicineInfo(**m_dict))

            diagnosis_obj = Diagnosis(
                disease=row["diag_disease"],
                treatment=row["diag_treatment"],
                medicine_prescribed=meds_list,
            )

        # 3. ประกอบร่าง Queue (เหมือนเดิม)
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

    @staticmethod
    def _map_entity_for_update(queue: Queue) -> tuple:
        """แพ็กข้อมูล Queue เป็น Tuple สำหรับคำสั่ง UPDATE (เรียงตาม _UPDATE_QUEUE_QUERY)"""
        vs = queue.vital_signs
        diag = queue.diagnosis

        # จัดการ JSONB ยา
        meds_json = None
        if diag and diag.medicine_prescribed:
            meds_json = (
                "["
                + ",".join([m.model_dump_json() for m in diag.medicine_prescribed])
                + "]"
            )

        # คำนวณ Version เก่าสำหรับเงื่อนไข WHERE
        old_version = queue.version.number - 1

        return (
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
            # ----- ส่วนของ WHERE -----
            str(queue.id),
            old_version,
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

    def update(self, queue: Queue) -> None:
        """อัปเดตข้อมูลคิว พร้อมระบบป้องกันชนกัน (Optimistic Locking)"""
        # 1. โยนให้ Helper Method จัดการแปลงเป็น Tuple
        values = self._map_entity_for_update(queue)

        # 2. คุยกับ Database
        with self.connection.cursor() as cursor:
            cursor.execute(self._UPDATE_QUEUE_QUERY, values)

            # 3. เช็ค Optimistic Locking
            if cursor.rowcount == 0:
                raise ConcurrentUpdateError(
                    f"คิว {queue.id} ถูกแก้ไขโดยผู้อื่นไปแล้ว กรุณาโหลดข้อมูลใหม่"
                )

        self.connection.commit()

    def get_last_queue(self) -> Queue | None:
        """ดึงคิวล่าสุดของ 'วันนี้' เพื่อนำไปคำนวณเลขคิวถัดไป"""

        today = date.today()

        with self.connection.cursor(row_factory=dict_row) as cursor:
            # โยนวันที่วันนี้เข้าไปค้นหา
            cursor.execute(self._SELECT_LAST_QUEUE_QUERY, (today,))
            row = cursor.fetchone()

        if not row:
            return None

        # 🌟 เราให้ Helper ประกอบร่างจบเลย ไม่ต้องเขียนใหม่!
        return self._map_row_to_entity(row)

    def find_active_queue_by_patient(self, patient_id, queue_date) -> Queue | None:
        """หาคิวที่ยังไม่เสร็จสิ้นของคนไข้ในวันที่กำหนด เพื่อป้องกันการออกคิวซ้ำ"""
        with self.connection.cursor(row_factory=dict_row) as cursor:

            values = (
                str(patient_id),
                queue_date,
                QueueStatus.COMPLETED.value,
                QueueStatus.CANCELLED.value,
            )

            # โยน patient_id (แปลงเป็น string) และ queue_date เข้าไป
            cursor.execute(self._SELECT_ACTIVE_QUEUE_QUERY, values)
            row = cursor.fetchone()

        if not row:
            return None

        # 🌟 เรียกใช้นักประกอบร่างสุดหล่อของเรา
        return self._map_row_to_entity(row)

    def get_all_queues_today(self, today: date) -> List[Queue]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(self._SELECT_ALL_TODAY_QUERY, (today,))

            # 🌟 ใช้ fetchall() เพื่อดึงข้อมูลทั้งหมดที่เจอออกมาเป็น List of Dict
            rows = cursor.fetchall()

        # 🌟 ใช้ List Comprehension โยนแต่ละแถวให้ Helper ประกอบร่างกลับเป็น Queue
        return [self._map_row_to_entity(row) for row in rows]
