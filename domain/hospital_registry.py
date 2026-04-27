# domain/hospital_registry.py
from pathlib import Path

# --- โซนงานบริหาร (Domain Service) ---
from domain.domain_service.patient_registrar import PatientRegistrar
from domain.domain_service.queue_service import QueueService

# --- โซนงานช่าง (Infrastructure) ---
from infrastructure.sqlite_patient_repository import SqlPatientRepository
from infrastructure.sqlite_queue_repository import SqlQueueRepository


class HospitalRegistry:
    """
    HospitalRegistry: ศูนย์บัญชาการ (Registry Pattern)
    ทำหน้าที่จัดการการสร้างและส่งมอบ Service/Repository ต่างๆ ให้กับระบบ
    """

    _DB_PATH = None
    _patient_registrar = None
    _queue_service = None

    @classmethod
    def get_db_path(cls) -> str:
        """ดึงตำแหน่งฐานข้อมูล (ถ้ายังไม่มีจะใช้ค่า Default)"""
        if cls._DB_PATH is None:
            # หาตำแหน่งโฟลเดอร์หลัก Hospital_System/ แล้วชี้ไปที่ database/hospital_database.db
            base_dir = Path(__file__).resolve().parent.parent
            cls._DB_PATH = str(base_dir / "database" / "hospital_database.db")
        return cls._DB_PATH

    @classmethod
    def set_test_db(cls):
        """🚩 สลับมาใช้ไฟล์สำหรับเทสโดยเฉพาะ (แทน :memory:)"""
        cls.reset()
        base_dir = Path(__file__).resolve().parent.parent
        # ใช้ชื่อไฟล์แยกออกมา เพื่อไม่ให้ปนกับของจริง
        cls._DB_PATH = str(base_dir / "database" / "test_database.db")

    @classmethod
    def reset(cls):
        """ล้าง Instance ที่ค้างอยู่ (จำเป็นมากเวลาเทสหลายๆ รอบ)"""
        cls._patient_registrar = None
        cls._queue_service = None

    @classmethod
    def init_database(cls):
        """เตรียมความพร้อม: สร้างโฟลเดอร์และตารางเริ่มต้น"""
        path = cls.get_db_path()

        # ถ้าไม่ใช่โหมด "test_database.db" ให้สร้างโฟลเดอร์รอไว้เลย
        if path != "test_database.db":
            db_dir = Path(path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        # สั่งให้ Repository ตรวจสอบและสร้างตาราง
        SqlPatientRepository(db_path=path)
        SqlQueueRepository(db_path=path)

    @classmethod
    def patient_registrar(cls) -> PatientRegistrar:
        """เบิกตัวพยาบาลทะเบียน (Singleton)"""
        if cls._patient_registrar is None:
            repo = SqlPatientRepository(db_path=cls.get_db_path())

            cls._patient_registrar = PatientRegistrar(patient_repo=repo)
        return cls._patient_registrar

    @classmethod
    def queue_service(cls) -> QueueService:
        """เบิกตัวแผนกคิว (Singleton)"""
        if cls._queue_service is None:
            repo = SqlQueueRepository(db_path=cls.get_db_path())
            cls._queue_service = QueueService(queue_repo=repo)
        return cls._queue_service

    @classmethod
    def patient_repo(cls) -> SqlPatientRepository:
        """เบิกตู้เหล็กเก็บคนไข้โดยตรง"""
        return SqlPatientRepository(db_path=cls.get_db_path())

    @classmethod
    def configure_queue(cls, queue_repo):
        """เมธอดสำหรับขาโมดิฟาย: ยัด Repo เองกับมือ"""
        cls._queue_service = QueueService(queue_repo=queue_repo)