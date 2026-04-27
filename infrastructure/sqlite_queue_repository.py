import json
import sqlite3
from contextlib import closing
from datetime import date
from uuid import UUID

from domain.entities import Queue
from domain.interfaces import QueueRecord
from domain.value_object import (
    QueueStatus, Version, VitalSigns, BloodPressure, Weight, Height,
    Temperature, Number, MedicineInfo, Diagnosis
)


class SqlQueueRepository(QueueRecord):
    # =====================================================================
    # 1. SQL CONSTANTS (ศูนย์รวมคำสั่ง DB ทั้งหมดอยู่ที่นี่ที่เดียว)
    # =====================================================================
    _CREATE_SCHEMA_QUERY = '''
        CREATE TABLE IF NOT EXISTS queue (
            q_id TEXT PRIMARY KEY, 
            p_id TEXT NOT NULL, 
            p_num INTEGER NOT NULL,
            q_date TEXT NOT NULL, 
            status TEXT NOT NULL, 
            ver INTEGER DEFAULT 1,
            bp_sys INTEGER, 
            bp_dia INTEGER, 
            w_kg REAL, 
            h_cm REAL, 
            temp_c REAL,
            symptom TEXT, 
            diag_disease TEXT, 
            diag_treatment TEXT, 
            diag_meds TEXT
        )
    '''

    _INSERT_QUEUE_QUERY = '''
        INSERT INTO queue
        (q_id, p_id, p_num, q_date, status, ver, bp_sys, bp_dia, 
        w_kg, h_cm, temp_c, symptom, diag_disease, diag_treatment, diag_meds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    _UPDATE_QUEUE_QUERY = '''
        UPDATE queue SET
        status = ?, ver = ?,
        bp_sys = ?, bp_dia = ?, w_kg = ?, h_cm = ?, temp_c = ?, 
        symptom = ?, diag_disease = ?, diag_treatment = ?, diag_meds = ?
        WHERE q_id = ? AND ver = ? 
    '''

    _SELECT_ACTIVE_BY_PATIENT_QUERY = """
        SELECT * FROM queue 
        WHERE p_id = ? AND q_date = ?
        AND status IN ('รอ', 'กำลังพบหมอ')
        LIMIT 1
    """

    _SELECT_LAST_QUEUE_QUERY = """
        SELECT * FROM queue 
        ORDER BY q_date DESC, p_num
        DESC LIMIT 1
    """

    _SELECT_ALL_QUEUES_TODAY_QUERY = """
        SELECT q_id, p_id, p_num, q_date, status FROM queue WHERE q_date = ?
    """

    _SELECT_BY_ID_QUERY = 'SELECT * FROM queue WHERE q_id = ?'
    _SELECT_ALL_QUERY = 'SELECT * FROM queue'

    # =====================================================================
    # 2. CORE METHODS (สั้น กระชับ อ่านปรู๊ดเดียวรู้เรื่อง)
    # =====================================================================
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.create_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_schema(self) -> None:
        with closing(self._get_connection()) as conn:
            with conn:
                conn.execute(self._CREATE_SCHEMA_QUERY)

    def save(self, queue: Queue) -> None:
        """เปิดประตู -> แปลงของลงกล่อง -> ยัดใส่ DB"""
        with closing(self._get_connection()) as conn:
            with conn:
                res = conn.execute(self._SELECT_BY_ID_QUERY, (str(queue.id),))
                row = res.fetchone()
                is_new = row is None

                diag_data = self._prepare_diagnosis(queue)

                if is_new:
                    # ถ้าเป็นของใหม่ ใช้ INSERT ธรรมดา
                    data_tuple = self._map_entity_to_tuple(queue, diag_data)
                    conn.execute(self._INSERT_QUEUE_QUERY, data_tuple)

    def update(self, queue: Queue) -> None:
        with closing(self._get_connection()) as conn:
            with conn:

                current_ver = queue.version.number
                old_ver = queue.version.number - 1
                diag_data = self._prepare_diagnosis(queue)
                data = self._map_patient_to_data_for_sql(
                    current_ver, diag_data, old_ver, queue)

                cursor = conn.execute(self._UPDATE_QUEUE_QUERY, data)

            # 🚩 3. ถ้าไม่มีแถวไหนถูกอัปเดต แปลว่า Version ไม่ตรง!
            if cursor.rowcount == 0:
                raise RuntimeError("ข้อมูลใบคิวถูก update โดยผู้อื่นไปก่อนหน้าแล้ว")

    def get_by_queue_id(self, queue_id: UUID) -> Queue | None:
        with closing(self._get_connection()) as conn:
            row = conn.execute(self._SELECT_BY_ID_QUERY, (str(queue_id),)).fetchone()
            if not row:
                return None
            return self._map_row_to_entity(row)

    def get_all(self) -> list[Queue]:
        with closing(self._get_connection()) as conn:
            rows = conn.execute(self._SELECT_ALL_QUERY).fetchall()
            return [self._map_row_to_entity(row) for row in rows]

    def get_last_queue(self) -> Queue | None:
        """ไปมุดตู้หาดูว่า ใบคิวใบสุดท้ายที่เพิ่งออกไปคือใบไหน"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(self._SELECT_LAST_QUEUE_QUERY).fetchone()

            if not row:
                return None

            # ถ้าเจอของ ก็แปลงจาก Row กลับมาเป็น Object ให้หัวหน้าใช้งานต่อได้
            return self._map_row_to_entity(row)

    def find_active_queue_by_patient(self, patient_id: UUID, queue_date: date) -> Queue | None:
        """ไปค้นในตู้เหล็กดูว่า วันนี้คนไข้คนนี้มีคิวที่ยังค้างอยู่ในระบบไหม
        ไปค้นในตู้เหล็กดูว่า วันนี้คนไข้คนนี้มีคิวที่ยังค้างอยู่ในระบบไหม"""
        with closing(self._get_connection()) as conn:
            # ส่งค่า p_id (รหัสคนไข้) และ q_date (วันที่วันนี้) เข้าไปเช็ค
            row = conn.execute(
                self._SELECT_ACTIVE_BY_PATIENT_QUERY,
                (str(patient_id), queue_date.isoformat())
            ).fetchone()

            if not row:
                return None
            return self._map_row_to_entity(row)

    def get_all_queues_today(self, today: date) -> list[Queue]:
        with closing(self._get_connection()) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                self._SELECT_ALL_QUEUES_TODAY_QUERY,
                (today.isoformat(),)).fetchall()

        if not rows:
            return []

        queues = []
        for row in rows:
            # แปลงข้อมูลแต่ละแถว (row) กลับมาเป็น Queue Object
            q = Queue(
                id=UUID(row['q_id']),
                patient_id=UUID(row['p_id']),
                queue_number=Number(id=row['p_num']),
                # fromisoformat(): คือการแปลงจาก String(ตัวหนังสือจาก DB)
                # -> Object(วันที่)...(ใช้ตอนจะเอาข้อมูลเข้าบ้าน / Domain)
                queue_date=date.fromisoformat(row['q_date']),
                status=QueueStatus(row['status']),
            )
            queues.append(q)
        return queues

    # =====================================================================
    # 3. HELPER METHODS (ลูกมือรับจบงานถึกทน)
    # =====================================================================
    def _prepare_diagnosis(self, queue: Queue) -> dict[str, str | None]:
        if not queue.diagnosis:
            return {"disease": None, "treatment": None, "meds": None}

        return {
            "disease": queue.diagnosis.disease,
            "treatment": queue.diagnosis.treatment,
            "meds": json.dumps([m.model_dump() for m in queue.diagnosis.medicine_prescribed])
        }

    def _map_entity_to_tuple(self, queue: Queue, diag_data: dict) -> tuple:
        """แปลง Object เป็น Tuple เพื่อส่งให้ SQLite"""
        return (
            str(queue.id),
            str(queue.patient_id),
            queue.queue_number.id,
            queue.queue_date.isoformat(),
            queue.status.value,
            queue.version.number,
            queue.vital_signs.blood_pressure.systolic,
            queue.vital_signs.blood_pressure.diastolic,
            queue.vital_signs.weight.value,
            queue.vital_signs.height.value,
            queue.vital_signs.temperature.value,
            queue.vital_signs.symptom,
            diag_data["disease"], diag_data["treatment"], diag_data["meds"]
        )

    def _map_row_to_entity(self, row: sqlite3.Row) -> Queue:
        """แปลง Row จาก SQLite คืนเป็น Object"""
        diagnosis_obj = None
        if row['diag_disease']:
            meds_data = json.loads(row['diag_meds']) if row['diag_meds'] else []
            meds = [MedicineInfo(**m) for m in meds_data]
            diagnosis_obj = Diagnosis(
                disease=row['diag_disease'], treatment=row['diag_treatment'], medicine_prescribed=meds,
            )

        return Queue(
            id=UUID(row['q_id']),
            patient_id=UUID(row['p_id']),
            queue_number=Number(id=row['p_num']),
            queue_date=date.fromisoformat(row['q_date']),
            status=QueueStatus(row['status']),
            version=Version(number=row['ver']),
            vital_signs=VitalSigns(
                blood_pressure=BloodPressure(systolic=row['bp_sys'], diastolic=row['bp_dia']),
                weight=Weight(value=row['w_kg']), height=Height(value=row['h_cm']),
                temperature=Temperature(value=row['temp_c']), symptom=row['symptom']
            ),
            diagnosis=diagnosis_obj
        )

    def _map_patient_to_data_for_sql(self, current_ver: int, diag_data: dict[str, str | None], old_ver: int,
                                     queue: Queue) -> \
    tuple[str, int, int, int, float, float, float, str, str | None, str | None, str | None, str, int]:
        data = (
            queue.status.value,
            current_ver,  # เลขใหม่
            queue.vital_signs.blood_pressure.systolic,
            queue.vital_signs.blood_pressure.diastolic,
            queue.vital_signs.weight.value,
            queue.vital_signs.height.value,
            queue.vital_signs.temperature.value,
            queue.vital_signs.symptom,
            diag_data["disease"],
            diag_data["treatment"],
            diag_data["meds"],
            str(queue.id),
            old_ver  # 🚩 ต้อง WHERE ด้วยเลขเก่า
        )
        return data