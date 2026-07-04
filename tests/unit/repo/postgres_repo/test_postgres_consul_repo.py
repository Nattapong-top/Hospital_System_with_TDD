from pytest import raises

from domain.custom_error import ConcurrentUpdateError
from domain.value_object import QueueStatus
from infrastructure.postgres_consultation_repo import PostgresConsultationRepository


def test_consul_repo_should_save_and_get_consul_id_success(
    pg_consul_table, new_consultation
):

    repo = PostgresConsultationRepository(pg_consul_table)

    repo.save(new_consultation)

    retrieved_consul = repo.get_by_consultation_id(new_consultation.id)

    assert retrieved_consul is not None
    assert retrieved_consul.id == new_consultation.id


def test_consul_repo_should_get_queue_id_success(pg_consul_table, new_consultation):
    repo = PostgresConsultationRepository(pg_consul_table)
    repo.save(new_consultation)
    retrieved = repo.get_by_queue_id(new_consultation.queue_id)
    assert retrieved is not None
    assert retrieved.id == new_consultation.id
    assert retrieved.queue_id == new_consultation.queue_id


def test_consul_repo_should_update_consul_success(
    pg_consul_table, new_consultation, diagnosis
):
    repo = PostgresConsultationRepository(pg_consul_table)

    repo.save(new_consultation)
    retrieved = repo.get_by_consultation_id(new_consultation.id)
    assert retrieved.status.value == "กำลังพบหมอ"

    retrieved.complete_examination(diagnosis)
    repo.update(retrieved)
    consul_completed = repo.get_by_consultation_id(retrieved.id)
    assert consul_completed is not None
    assert consul_completed.id == new_consultation.id
    assert consul_completed.status.value == QueueStatus.COMPLETED.value
    assert consul_completed.version.current_number == 2


def test_consul_repo_concurrent_update_should_raise_error(
    pg_consul_table, new_consultation, diagnosis
):
    repo = PostgresConsultationRepository(pg_consul_table)
    repo.save(new_consultation)
    nurse = repo.get_by_consultation_id(new_consultation.id)
    doctor = repo.get_by_consultation_id(new_consultation.id)

    nurse.cancel_examination()
    repo.update(nurse)

    doctor.complete_examination(diagnosis)

    with raises(ConcurrentUpdateError) as e:
        repo.update(doctor)

    assert "มีคนอื่นแก้ไขข้อมูลนี้ไปแล้ว" in str(e.value)
    latest = repo.get_by_consultation_id(new_consultation.id)

    assert latest.version.current_number == 2
    assert latest.status == QueueStatus.CANCELLED
