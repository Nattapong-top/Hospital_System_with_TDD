# test_queue_service.py
import uuid
from datetime import date, datetime

from pytest import raises

from domain.custom_error import (DuplicationQueueError, InvalidStatusTransitionError,
                                                 InvalidCancelRequestError, QueueNotFoundError)
from domain.domain_service.queue_service import QueueService
from domain.value_object import (
    Number, QueueStatus, Version)


def test_should_queue_service_issue_first_number_of_the_day(queue_repo):
    service = QueueService(queue_repo)

    today = date(2026, 3, 28)
    now = datetime(2026, 3, 28, 22, 43, 53, 302903)
    next_number, last_date, time_now = service.get_next_number(
        last_number=Number(id=0), last_date=today, time_now=now, today=today)
    assert next_number == Number(id=1)
    assert last_date == date(2026, 3, 28)
    assert time_now == datetime(2026, 3, 28, 22, 43, 53, 302903)


def test_should_queue_service_reset_number_and_last_date(queue_repo, today_date, now):
    service = QueueService(queue_repo)
    next_number, last_date, time_now = service.get_next_number(
        last_number=Number(id=99), last_date=date(2026, 3, 27),
        time_now=now, today=today_date)
    assert next_number == Number(id=1)
    assert last_date == today_date
    assert time_now == now


def test_should_queue_service_issue_first_queue_successfully(queue_repo, queue_service, patient, vital_signs, today_date):
    new_queue = queue_service.issue_new_queue(
        patient_id=patient.id,
        today=today_date,
        vital_signs=vital_signs,
    )
    assert new_queue.queue_number == Number(id=1)
    assert new_queue.queue_date == date(2026, 3, 28)
    assert len(queue_repo.get_all()) == 1


def test_should_queue_service_raise_error_duplication_queue(queue_repo, queue_service, patient, vital_signs, today_date):
    new_queue = queue_service.issue_new_queue(
        patient_id=patient.id,
        today=today_date,
        vital_signs=vital_signs,
    )
    with raises(DuplicationQueueError) as excinfo:
        queue_service.issue_new_queue(
            patient_id=patient.id,
            today=today_date,
            vital_signs=vital_signs,
        )
    assert 'จองคิวซ้ำไม่ได้' in str(excinfo.value)


def test_should_start_consultation_successfully(queue_repo, queue_service, patient, vital_signs, today_date):
    new_queue = queue_service.issue_new_queue(
        patient_id=patient.id,
        today=today_date,
        vital_signs=vital_signs,
    )
    updated_queue = queue_service.start_consultation(queue_id=new_queue.id)
    assert updated_queue.id == new_queue.id
    assert updated_queue.queue_date == new_queue.queue_date
    assert updated_queue.status == QueueStatus.IN_PROGRESS
    assert queue_repo.get_by_queue_id(queue_id=new_queue.id).status == QueueStatus.IN_PROGRESS


def test_should_start_consultation_with_invalid_id_raises_error(queue_service):
    invalid_id = uuid.uuid4()
    with raises(QueueNotFoundError) as excinfo:
        queue_service.start_consultation(queue_id=invalid_id)
    assert 'ไม่พบคิว' in str(excinfo.value)


def test_queue_service_should_complete_visit_when_is_valid(new_queue, diagnosis, patient, queue_service, queue_repo):
    assert new_queue.status == QueueStatus.WAITING
    update_queue = queue_service.start_consultation(queue_id=new_queue.id)
    assert update_queue.status == QueueStatus.IN_PROGRESS
    update_queue = queue_service.complete_visit(queue_id=new_queue.id, diagnosis=diagnosis)

    assert update_queue.status == QueueStatus.COMPLETED
    assert update_queue.diagnosis == diagnosis
    assert update_queue.patient_id == patient.id
    assert update_queue.version == Version(number=3)

    save_queue = queue_repo.get_by_queue_id(new_queue.id)
    assert save_queue.status == QueueStatus.COMPLETED


def test_queue_service_should_raise_error_when_complete_visit_patient_id_invalid(queue_service, diagnosis):
    with raises(QueueNotFoundError) as excinfo:
        queue_service.complete_visit(queue_id=uuid.uuid4(), diagnosis=diagnosis)
    assert 'ไม่พบคิว' in str(excinfo.value)


def test_queue_service_should_raise_error_when_complete_visit_status_witting(queue_service, diagnosis, new_queue, ):
    assert new_queue.status == QueueStatus.WAITING
    with raises(InvalidStatusTransitionError) as excinfo:
        queue_service.complete_visit(queue_id=new_queue.id, diagnosis=diagnosis)
    assert 'ไม่สามารถจบการตรวจได้' in str(excinfo.value)


def test_queue_service_should_cancel_visit_when_status_witting(new_queue, diagnosis, patient,
                                                               queue_service, queue_repo):
    assert new_queue.status == QueueStatus.WAITING
    assert new_queue.version == Version(number=1)

    update_queue = queue_service.cancel_visit(queue_id=new_queue.id)
    assert update_queue.status == QueueStatus.CANCELLED
    assert update_queue.version == Version(number=2)
    save_queue = queue_repo.get_by_queue_id(new_queue.id)
    assert save_queue.status == QueueStatus.CANCELLED


def test_queue_service_should_cancel_visit_when_status_in_progress(new_queue, queue_service, queue_repo):
    update_queue = queue_service.start_consultation(queue_id=new_queue.id)
    assert update_queue.status == QueueStatus.IN_PROGRESS
    assert update_queue.version == Version(number=2)

    cancel_queue = queue_service.cancel_visit(queue_id=new_queue.id)
    assert cancel_queue.status == QueueStatus.CANCELLED
    assert cancel_queue.version == Version(number=3)
    save_queue_repo = queue_repo.get_by_queue_id(new_queue.id)
    assert save_queue_repo.status == QueueStatus.CANCELLED


def test_queue_service_should_raise_error_when_cancel_visit_whit_status_complete(new_queue, queue_service, queue_repo, diagnosis):
    with raises(InvalidCancelRequestError) as excinfo:
        queue_service.start_consultation(queue_id=new_queue.id)
        queue_service.complete_visit(queue_id=new_queue.id, diagnosis=diagnosis)
        queue_service.cancel_visit(queue_id=new_queue.id)
    assert 'ไม่สามารถยกเลิกการตรวจได้' in str(excinfo.value)
