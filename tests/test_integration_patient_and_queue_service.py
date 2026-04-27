from pytest import raises

from domain.custom_error import InvalidCancelRequestError
from domain.value_object import QueueStatus
from tests.conftest import today_date, new_queue


def test_doctor_starts_consultation_should_change_status_to_IN_PROGRESS(new_patient, queue_service, vital_signs, today_date):

    new_queue = queue_service.issue_new_queue(new_patient.id, today_date, vital_signs)
    # --- 1. เตรียมของ (Arrange) ---
    assert new_queue.patient_id == new_patient.id
    # ดึงคิวที่เพิ่งสร้างตอนลงทะเบียนมาดู (มันควรจะเป็นสถานะ WAITING)
    active_queue = queue_service.get_active_queue_by_patient(new_queue.patient_id, today_date)
    assert active_queue is not None
    assert active_queue.status == QueueStatus.WAITING

    # --- 2. ลงมือทำ (Act) ---
    # หมอกดปุ่มเรียกคิวเข้าห้องตรวจ
    updated_queue = queue_service.start_consultation(active_queue.id)
    assert updated_queue.status == QueueStatus.IN_PROGRESS

    # 🚩 พิสูจน์ความชัวร์: ไปแอบเปิดตู้เหล็กดูอีกรอบ ว่าในฐานข้อมูลมันเปลี่ยนจริงๆ ไหม!
    db_queue = queue_service.get_active_queue_by_patient(updated_queue.patient_id, today_date)
    assert db_queue is not None
    assert db_queue.status == QueueStatus.IN_PROGRESS
    assert db_queue.version.number == 2


def test_doctor_complete_visit_should_change_status_to_COMPLETE(new_patient, queue_service, diagnosis, today_date,
                                                                vital_signs):
    # --- 1. เตรียมของ (Arrange) ---
    new_queue = queue_service.issue_new_queue(new_patient.id, today_date, vital_signs)

    # ดึงคิวที่เพิ่งสร้างตอนลงทะเบียนมาดู (มันควรจะเป็นสถานะ WAITING)
    active_queue = queue_service.get_active_queue_by_patient(new_queue.patient_id, today_date)
    assert active_queue is not None
    assert active_queue.status == QueueStatus.WAITING

    # --- 2. ลงมือทำ (Act) ---
    # หมอกดปุ่มเรียกคิวเข้าห้องตรวจ
    updated_queue = queue_service.start_consultation(queue_id=active_queue.id)
    assert updated_queue.status == QueueStatus.IN_PROGRESS

    completed_queue = queue_service.complete_visit(updated_queue.id, diagnosis)
    assert completed_queue.status == QueueStatus.COMPLETED
    assert completed_queue.version.number == 3

    # 🚩 พิสูจน์ความชัวร์: ไปแอบเปิดตู้เหล็กดูอีกรอบ ว่าในฐานข้อมูลมันเปลี่ยนจริงๆ ไหม!
    db_queue = queue_service.queue_repo.get_by_queue_id(completed_queue.id)
    assert db_queue.status == QueueStatus.COMPLETED
    assert db_queue.version.number == 3


def test_doctor_cancel_visit_should_change_status_to_CANCELLED(new_patient, queue_service, today_date, new_queue):
    active_queue = queue_service.get_active_queue_by_patient(new_queue.patient_id, today_date)
    assert active_queue.status == QueueStatus.WAITING
    assert active_queue.version.number == 1

    cancelled_queue = queue_service.cancel_visit(active_queue.id)
    assert cancelled_queue.status == QueueStatus.CANCELLED
    assert cancelled_queue.version.number == 2

    db_queue = queue_service.queue_repo.get_by_queue_id(cancelled_queue.id)
    assert db_queue.status == QueueStatus.CANCELLED


def test_doctor_cancel_visit_should_change_status_to_CANCELLED_when_status_IN_PROGRESS(new_patient, queue_service,
                                                                                       today_date, new_queue):
    active_queue = queue_service.get_active_queue_by_patient(new_queue.patient_id, today_date)
    assert active_queue.status == QueueStatus.WAITING
    assert active_queue.version.number == 1

    in_progress_queue = queue_service.start_consultation(active_queue.id)
    db_active = queue_service.get_active_queue_by_patient(in_progress_queue.patient_id, today_date)
    assert db_active.status == QueueStatus.IN_PROGRESS

    cancelled_queue = queue_service.cancel_visit(in_progress_queue.id)
    assert cancelled_queue.status == QueueStatus.CANCELLED
    assert cancelled_queue.version.number == 3

    db_queue = queue_service.queue_repo.get_by_queue_id(cancelled_queue.id)
    assert db_queue.status == QueueStatus.CANCELLED
    assert db_queue.version.number == 3


def test_doctor_cannot_cancel_visit_should_raise_error_when_status_COMPLETE(new_patient, queue_service, diagnosis,
                                                                            today_date, new_queue):
    # --- 1. เตรียมของ (Arrange) ---
    # ดึงคิวที่เพิ่งสร้างตอนลงทะเบียนมาดู (มันควรจะเป็นสถานะ WAITING)
    active_queue = queue_service.get_active_queue_by_patient(new_queue.patient_id, today_date)
    assert active_queue.status == QueueStatus.WAITING

    # --- 2. ลงมือทำ (Act) ---
    # หมอกดปุ่มเรียกคิวเข้าห้องตรวจ
    updated_queue = queue_service.start_consultation(queue_id=active_queue.id)
    assert updated_queue.status == QueueStatus.IN_PROGRESS

    completed_queue = queue_service.complete_visit(updated_queue.id, diagnosis)
    assert completed_queue.status == QueueStatus.COMPLETED
    assert completed_queue.version.number == 3

    # 🚩 พิสูจน์ความชัวร์: ไปแอบเปิดตู้เหล็กดูอีกรอบ ว่าในฐานข้อมูลมันเปลี่ยนจริงๆ ไหม!
    db_queue = queue_service.queue_repo.get_by_queue_id(completed_queue.id)
    assert db_queue.status == QueueStatus.COMPLETED
    assert db_queue.version.number == 3

    with raises(InvalidCancelRequestError) as error:
        queue_service.cancel_visit(completed_queue.id)

    assert 'ไม่สามารถยกเลิกการตรวจได้ เพราะสถานะปัจจุบันคือ' in str(error.value)
