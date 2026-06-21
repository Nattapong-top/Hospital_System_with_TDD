from pytest import fixture

from domain.hospital_registry import HospitalRegistry
from infrastructure.sqlite_consultation_repository import SqlConsultationRepository
from tests.fake_repository.fake_repository import (
    FakeQueueRecord,
    InMemoryStaffRepository,
    InMemConsulRepo,
)


# =====================================================================
# 3. REPOSITORIES (ตู้เหล็กเก็บข้อมูล)
# =====================================================================
@fixture
def fake_repo():
    return FakeQueueRecord()


@fixture
def queue_sql():
    return HospitalRegistry.queue_service().queue_repo


# 🚩 1. เพิ่ม Fixture สำหรับตู้เหล็กคิว (ที่เทสเก่าถามหา)
@fixture
def queue_repo():
    """เบิกตู้เหล็กเก็บคิวจากผู้อำนวยการ"""
    # ดึงมาจาก Service ที่ Registry เตรียมไว้ให้แล้ว
    return HospitalRegistry.queue_service().queue_repo


# 🚩 2. (แถม) เผื่อเทสไหนถามหาตู้เหล็กคนไข้
@fixture
def patient_repo():
    """เบิกตู้เหล็กเก็บคนไข้จากผู้อำนวยการ"""
    return HospitalRegistry.patient_repo()


@fixture
def InMem_staff_repo():
    return InMemoryStaffRepository()


@fixture
def InMem_consul_repo():
    return InMemConsulRepo()


@fixture
def consul_repo():
    return SqlConsultationRepository(HospitalRegistry.set_test_db())
