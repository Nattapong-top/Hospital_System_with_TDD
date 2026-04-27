from pytest import raises
from domain.consultation_entities import Consultation
from domain.custom_error import MissingDiagnosisError, InvalidStatusTransitionError
from domain.value_object import QueueStatus
from tests.conftest import new_staff_doctor, new_patient


def test_create_consultation_should_have_correct_initial_data(new_queue, new_staff_doctor, new_patient):
    start_consul = Consultation(
        queue_id=new_queue.id,
        doctor_id=new_staff_doctor.staff_id,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )

    assert start_consul is not None
    assert isinstance(start_consul, Consultation)
    assert start_consul.queue_id == new_queue.id
    assert start_consul.patient_id == new_queue.patient_id
    assert start_consul.doctor_id == new_staff_doctor.staff_id
    assert start_consul.status.value == 'กำลังพบหมอ'
    assert start_consul.version.number == 1
    assert start_consul.started_at is not None


def test_complete_examination_should_update_diagnosis_and_increment_version(
        new_consultation, diagnosis):
    initial_version = new_consultation.version.number

    new_consultation.complete_examination(diagnosis)

    assert new_consultation.version.number == initial_version + 1
    assert new_consultation.status == QueueStatus.COMPLETED
    assert new_consultation.diagnosis == diagnosis
    assert new_consultation.finished_at is not None


def test_examination_should_none_when_missing_diagnosis(new_consultation):
    with raises(MissingDiagnosisError):
        new_consultation.complete_examination(None)


def test_cancel_examination_when_status_in_progress_should_success(new_consultation):
    consul = new_consultation
    consul.cancel_examination()
    assert consul.status == QueueStatus.CANCELLED


def test_cancel_examination_when_status_in_progress_should_fail(new_consultation, diagnosis):
    consul = new_consultation
    consul.status = QueueStatus.WAITING
    with raises(InvalidStatusTransitionError):
        consul.complete_examination(diagnosis)
