from uuid import uuid4

from domain.custom_error import ConcurrentUpdateError
from domain.hospital_registry import HospitalRegistry
from infrastructure.sqlite_consultation_repository import SqlConsultationRepository
from tests.conftest import new_consultation
from tests.fake_repository.fake_repository import InMemConsulRepo


def test_consultation_repository_should_save_and_get_consultation_success(new_consultation):
    # 1. Arrange: สร้าง Repository จำลอง (InMemory)
    repo = InMemConsulRepo()
    # 2. Act: บันทึกใบตรวจลงตู้
    repo.save(new_consultation)
    # 3. Assert: ลองดึงออกมาด้วย ID เดิม
    found = repo.get_by_consultation_id(new_consultation.id)

    assert found is not None
    assert found.id == new_consultation.id
    assert found.doctor_id == new_consultation.doctor_id


def test_consultation_repo_return_none_if_not_found():
    repo = InMemConsulRepo()
    import uuid
    assert repo.get_by_consultation_id(uuid.uuid4()) is None


def test_consultation_repo_save_and_get_by_consultation_id_should_success(new_consultation):
    repo = SqlConsultationRepository(HospitalRegistry.set_test_db())
    repo.save(new_consultation)
    found = repo.get_by_consultation_id(new_consultation.id)
    assert found is not None
    assert found.id == new_consultation.id
    assert found.doctor_id == new_consultation.doctor_id
    assert found.diagnosis is None
    assert found.vital_signs == new_consultation.vital_signs

def test_consultation_repo_update_and_get_by_queue_id_should_success(new_consultation, consul_repo, diagnosis, new_queue):
    assert new_queue.patient_id == new_consultation.patient_id
    assert new_queue.id == new_consultation.queue_id
    assert new_consultation.status.value == 'กำลังพบหมอ'
    consul_repo.save(new_consultation)
    found = consul_repo.get_by_queue_id(new_consultation.queue_id)
    assert found.status.value == 'กำลังพบหมอ'
    found.complete_examination(diagnosis)
    consul_repo.update(found)
    consul_complete = consul_repo.get_by_queue_id(found.queue_id)
    assert consul_complete is not None
    assert consul_complete.status.value == 'ตรวจเสร็จแล้ว'

def test_consultation_repo_get_id_return_none_if_not_found(new_consultation, consul_repo):
    assert consul_repo.get_by_consultation_id(uuid4) is None
    assert consul_repo.get_by_queue_id(uuid4) is None

# เทส Optimistic Locking (ป้องกันคนเซฟทับกัน)
def test_consultation_repo_concurrent_update_should_raise_error(new_consultation, consul_repo, diagnosis):
    consul_repo.save(new_consultation)
    # 2. จำลองสถานการณ์: พยาบาล กับ หมอ เปิดหน้าจอใบตรวจนี้ขึ้นมาพร้อมกัน
    screen_nurse = consul_repo.get_by_consultation_id(new_consultation.id)
    screen_doctor = consul_repo.get_by_consultation_id(new_consultation.id)
    # 3. พยาบาล กด "ยกเลิกการตรวจ" แล้วกดเซฟ (ลงตู้สำเร็จ เวอร์ชันในตู้กลายเป็น 2)
    screen_nurse.cancel_examination()
    consul_repo.update(screen_nurse)

    # 4. หมอ ไม่รู้ว่าพยาบาลยกเลิกไปแล้ว หมอพิมพ์วินิจฉัยเสร็จแล้วกด "จบการตรวจ" (ตอนหมอกดเซฟ
    # ข้อมูลในมือหมอยังเป็นเวอร์ชัน 1 อยู่)
    screen_doctor.complete_examination(diagnosis)
    # 5. หมอกด Save ทับ -> ต้องระเบิด Error ทันที เพราะหาเวอร์ชันเก่าใน DB ไม่เจอแล้ว!
    import pytest
    with pytest.raises(ConcurrentUpdateError) as exc_info:
        consul_repo.update(screen_doctor)
    # 6. เช็คว่า Error Message แจ้งเตือนถูกต้อง
    assert 'เนื่องจากมีคนอื่นแก้ไขข้อมูลนี้ไปแล้วก่อนหน้านี้' in str(exc_info.value)



