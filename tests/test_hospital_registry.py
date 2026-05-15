# tests/test_hospital_registry.py
from core.config import settings
from domain.domain_service.examination_service import ExaminationService

from domain.domain_service.patient_registrar import PatientRegistrar
from domain.domain_service.queue_service import QueueService
from domain.domain_service.staff_service import StaffService

# --- โซนงานบริหาร (Domain Service): นำเข้าตัวพยาบาลและเจ้าหน้าที่ ---
from domain.hospital_registry import HospitalRegistry
from infrastructure.sqlite_patient_repository import SqlPatientRepository

# --- โซนงานช่าง (Infrastructure): นำเข้าตู้เก็บของจริง ---
from infrastructure.sqlite_queue_repository import SqlQueueRepository
from infrastructure.sqllite_staff_repository import SqlStaffRepository
from infrastructure.sqlite_consultation_repository import SqlConsultationRepository


def test_hospital_registry_should_return_queue_service_when_fake_repo(fake_repo):
    HospitalRegistry.configure_queue(queue_repo=fake_repo)
    service = HospitalRegistry.queue_service()

    assert isinstance(service, QueueService)
    assert isinstance(HospitalRegistry.queue_service(), QueueService)
    assert service.queue_repo == fake_repo  # เช็คว่าได้ของปลอมตามที่สั่ง


def test_hospital_registry_should_auto_wire_real_sqlite_repo(queue_sql):
    queue_sql.create_schema()
    HospitalRegistry.configure_queue(queue_repo=queue_sql)
    service = HospitalRegistry.queue_service()

    assert isinstance(service, QueueService)
    assert isinstance(service.queue_repo, SqlQueueRepository)
    assert service.queue_repo == queue_sql


def test_hospital_registry_should_real_sqlite_repository():
    service = HospitalRegistry.queue_service()
    assert isinstance(service, QueueService)
    assert isinstance(service.queue_repo, SqlQueueRepository)

    assert isinstance(HospitalRegistry.queue_service(), QueueService)


def test_hospital_registry_should_get_patient_registrar_with_auto_wiring():
    """เทสว่า Registry สามารถประกอบร่างพยาบาลทะเบียนกับตู้ SQLite ให้เราได้เอง"""
    registrar = HospitalRegistry.patient_registrar()

    # ตรวจความถูกต้อง
    assert isinstance(registrar, PatientRegistrar)
    # ตรวจว่าพยาบาลถือตู้ SQLite จริงหรือเปล่า
    assert isinstance(registrar.patient_repo, SqlPatientRepository)


def test_hospital_registry_should_get_staff_service_with_auto_wiring():
    """เทสว่า Registry สามารถประกอบร่างพยาบาลทะเบียนกับตู้ SQLite ให้เราได้เอง"""
    registrar = HospitalRegistry.staff_service()

    # ตรวจความถูกต้อง
    assert isinstance(registrar, StaffService)
    # ตรวจว่าพยาบาลถือตู้ SQLite จริงหรือเปล่า
    assert isinstance(registrar.staff_repo, SqlStaffRepository)


def test_hospital_registry_should_return_same_when_call_patient_registrar_instance():
    """เทสว่าเรียกกี่ครั้งก็ได้พยาบาลคนเดิม (Singleton) ไม่สร้างใหม่ฟุ่มเฟือย"""
    first_call = HospitalRegistry.patient_registrar()
    second_call = HospitalRegistry.patient_registrar()

    assert first_call == second_call


def test_hospital_registry_should_switch_to_new_exam_service(monkeypatch):
    # 1. Arrange: ปลอมค่า Config ให้เปิดใช้งานของใหม่
    # (สมมติป๋าทำไฟล์ core/config.py ไว้แล้ว)
    monkeypatch.setattr(settings, "ENABLE_NEW_EXAMINATION_FLOW", True)
    HospitalRegistry.reset()  # เคลียร์ของเก่าในตู้ Singleton ทิ้งก่อนครับป๋า
    # 2. Act: ไปเบิกตัว Service มา
    service = HospitalRegistry.consultation_service()
    # 3. Assert: เช็คว่าได้ของใหม่จริงๆ
    assert isinstance(service, ExaminationService)
    assert not isinstance(service, QueueService)


def test_hospital_registry_should_switch_to_queue_service_when_false(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_NEW_EXAMINATION_FLOW", False)
    HospitalRegistry.reset()
    service = HospitalRegistry.consultation_service()
    assert isinstance(service, QueueService)
    assert isinstance(service.queue_repo, SqlQueueRepository)
    assert not isinstance(service, ExaminationService)


def test_hospital_registry_should_auto_wire_consultation_repo_service(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_NEW_EXAMINATION_FLOW", True)
    HospitalRegistry.reset()

    service = HospitalRegistry.consultation_service()

    assert isinstance(service, ExaminationService)
    assert isinstance(service.consultation_repo, SqlConsultationRepository)
    assert not isinstance(service, QueueService)
    assert not isinstance(service.consultation_repo, SqlQueueRepository)
