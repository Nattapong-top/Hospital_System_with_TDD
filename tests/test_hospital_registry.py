# tests/test_hospital_registry.py
import os

from domain.domain_service.patient_registrar import PatientRegistrar
from domain.domain_service.queue_service import QueueService
# --- โซนงานบริหาร (Domain Service): นำเข้าตัวพยาบาลและเจ้าหน้าที่ ---
from domain.hospital_registry import HospitalRegistry
from infrastructure.sqlite_patient_repository import SqlPatientRepository
# --- โซนงานช่าง (Infrastructure): นำเข้าตู้เก็บของจริง ---
from infrastructure.sqlite_queue_repository import SqlQueueRepository


def test_hospital_registry_should_return_queue_service_when_fake_repo(fake_repo):
    HospitalRegistry.configure_queue(queue_repo=fake_repo)
    service = HospitalRegistry.queue_service()

    assert isinstance(service, QueueService)
    assert isinstance(HospitalRegistry.queue_service(), QueueService)
    assert service.queue_repo == fake_repo # เช็คว่าได้ของปลอมตามที่สั่ง


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


def test_hospital_registry_should_return_same_when_call_patient_registrar_instance():
    """เทสว่าเรียกกี่ครั้งก็ได้พยาบาลคนเดิม (Singleton) ไม่สร้างใหม่ฟุ่มเฟือย"""
    first_call = HospitalRegistry.patient_registrar()
    second_call = HospitalRegistry.patient_registrar()

    assert first_call == second_call
