# domain/hospital_registry.py
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from core.config import settings  # settings ไว้ที่หัวได้ เพราะเป็นแค่ข้อมูลตั้งค่า (Config)

# บล็อกนี้จะทำงานเฉพาะในสายตาของ PyCharm/Mypy เท่านั้นครับป๋า
if TYPE_CHECKING:
    from domain.domain_service.examination_service import ExaminationService
    from domain.domain_service.patient_registrar import PatientRegistrar
    from domain.domain_service.queue_service import QueueService
    from domain.domain_service.staff_service import StaffService
    from infrastructure.sqlite_patient_repository import SqlPatientRepository
    from infrastructure.sqlite_queue_repository import SqlQueueRepository
    from infrastructure.sqllite_staff_repository import SqlStaffRepository
    from infrastructure.sqlite_consultation_repository import SqlConsultationRepository


class HospitalRegistry:
    """
    HospitalRegistry: ศูนย์บัญชาการ (Registry Pattern)
    ทำหน้าที่จัดการการสร้างและส่งมอบ Service/Repository ต่างๆ ให้กับระบบ
    """
    _BASE_DIR = Path(__file__).resolve().parent.parent
    _DB_PATH = None

    # ตู้เก็บพนักงาน (Singleton Cache)
    _patient_registrar = None
    _queue_service = None
    _examination_service = None
    _staff_service = None
    _patient_repo = None
    _consultation_repo = None


    @classmethod
    def get_db_path(cls) -> str:
        """ดึงตำแหน่งฐานข้อมูลจาก Config"""
        if cls._DB_PATH is None:
            cls._DB_PATH = str(cls._BASE_DIR / "database" / settings.DB_NAME)
        return cls._DB_PATH

    @classmethod
    def set_test_db(cls) -> str:
        """🚩 สลับมาใช้ไฟล์สำหรับเทสโดยเฉพาะ"""
        cls.reset()
        cls._DB_PATH = str(cls._BASE_DIR / "database" / "test_database.db")
        return cls._DB_PATH

    @classmethod
    def reset(cls) -> None:
        """ล้าง Instance พนักงาน (ล้างเฉพาะพนักงาน เพื่อให้ Integration Test ไม่พัง)"""
        cls._patient_registrar = None
        cls._queue_service = None
        cls._examination_service = None
        cls._patient_repo = None
        cls._staff_service = None


    @classmethod
    def hard_reset(cls) -> None:
        """ล้างให้หมดจดจริงๆ รวมทั้งเส้นทาง DB"""
        cls.reset()
        cls._DB_PATH = None

    @classmethod
    def init_database(cls) -> None:
        """เตรียมความพร้อม: สร้างโฟลเดอร์และตารางเริ่มต้น (ใช้ Local Import)"""
        # นำเข้างานช่างเฉพาะตอนจะใช้งานเท่านั้น
        from infrastructure.sqlite_patient_repository import SqlPatientRepository
        from infrastructure.sqlite_queue_repository import SqlQueueRepository
        from infrastructure.sqllite_staff_repository import SqlStaffRepository
        from infrastructure.sqlite_consultation_repository import SqlConsultationRepository

        path = cls.get_db_path()
        if path != "test_database.db":
            db_dir = Path(path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        SqlPatientRepository(db_path=path)
        SqlQueueRepository(db_path=path)
        SqlStaffRepository(db_path=path)
        SqlConsultationRepository(db_path=path)

    @classmethod
    def patient_registrar(cls) -> PatientRegistrar:
        """เบิกตัวพยาบาลทะเบียน (Local Import)"""
        if cls._patient_registrar is None:
            from domain.domain_service.patient_registrar import PatientRegistrar
            from infrastructure.sqlite_patient_repository import SqlPatientRepository

            repo = SqlPatientRepository(db_path=cls.get_db_path())
            cls._patient_registrar = PatientRegistrar(patient_repo=repo)
        return cls._patient_registrar

    @classmethod
    def queue_service(cls) -> QueueService:
        """เบิกตัวแผนกคิว (Local Import)"""
        if cls._queue_service is None:
            from domain.domain_service.queue_service import QueueService
            from infrastructure.sqlite_queue_repository import SqlQueueRepository

            repo = SqlQueueRepository(db_path=cls.get_db_path())
            cls._queue_service = QueueService(queue_repo=repo)
        return cls._queue_service

    @classmethod
    def staff_service(cls) -> StaffService:
        """เบิกตัวแผนกบุคคล/พนักงาน (Local Import)"""
        if cls._staff_service is None:
            from domain.domain_service.staff_service import StaffService
            from infrastructure.sqllite_staff_repository import SqlStaffRepository

            repo = SqlStaffRepository(db_path=cls.get_db_path())
            cls._staff_service = StaffService(staff_repo=repo)
        return cls._staff_service

    @classmethod
    def consultation_service(cls) -> QueueService | ExaminationService:
        """จุดสลับร่างระบบตรวจรักษา (Branch by Abstraction)"""
        if settings.ENABLE_NEW_EXAMINATION_FLOW:
            return cls._set_switch_to_new_exam_service()
        return cls.queue_service()


    @classmethod
    def patient_repo(cls) -> SqlPatientRepository:
        """เบิกตู้เก็บคนไข้ (Local Import)"""
        if cls._patient_repo is None:
            from infrastructure.sqlite_patient_repository import SqlPatientRepository
            cls._patient_repo = SqlPatientRepository(db_path=cls.get_db_path())
        return cls._patient_repo

    @classmethod
    def consultation_repo(cls):
        """เบิกตู้เก็บใบตรวจรักษา (สร้างแบบ Singleton)"""
        if cls._consultation_repo is None:
            from infrastructure.sqlite_consultation_repository import SqlConsultationRepository
            cls._consultation_repo = SqlConsultationRepository(db_path=cls.get_db_path())
        return cls._consultation_repo

    @classmethod
    def _set_switch_to_new_exam_service(cls) -> ExaminationService:
        """สร้างพนักงานใหม่ (Local Import)"""
        if cls._examination_service is None:
            from domain.domain_service.examination_service import ExaminationService
            from infrastructure.sqlite_consultation_repository import SqlConsultationRepository

            repo = SqlConsultationRepository(db_path=cls.get_db_path())
            cls._examination_service = ExaminationService(
                consul_repo=repo,
                queue_service=cls.queue_service()
            )
        return cls._examination_service

    @classmethod
    def configure_queue(cls, queue_repo: SqlQueueRepository) -> None:
        """เมธอดสำหรับขาโมดิฟาย: ยัด Repo เองกับมือ"""
        from domain.domain_service.queue_service import QueueService
        cls._queue_service = QueueService(queue_repo=queue_repo)
