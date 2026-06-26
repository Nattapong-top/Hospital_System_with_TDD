import copy
from datetime import date
from uuid import uuid4

from domain.value_object import Number
from infrastructure.postgres_queue_repository import PostgresQueueRepository


def test_pg_queue_repo_should_save_and_retrieve_queue(pg_queue_table, new_queue):
    repo = PostgresQueueRepository(pg_queue_table)
    repo.save(new_queue)

    retrieve_queue = repo.get_by_queue_id(new_queue.id)

    assert retrieve_queue is not None
    assert new_queue.id == retrieve_queue.id
    assert new_queue.patient_id == retrieve_queue.patient_id


def test_pg_queue_repo_should_update_queue(pg_queue_table, queue, diagnosis):
    repo = PostgresQueueRepository(pg_queue_table)
    repo.save(queue)

    queue.diagnosis = diagnosis
    queue.status = queue.status.COMPLETED
    queue.version = queue.version.increment()
    repo.update(queue)

    updated_queue = repo.get_by_queue_id(queue.id)

    assert updated_queue is not None
    assert queue.id == updated_queue.id
    assert updated_queue.status.value == "ตรวจเสร็จแล้ว"
    assert updated_queue.version.number == 2
    assert updated_queue.diagnosis is not None

    assert updated_queue.diagnosis.disease == "ไข้หวัดใหญ่"
    assert len(updated_queue.diagnosis.medicine_prescribed) == 1
    assert updated_queue.diagnosis.medicine_prescribed[0].name == "Paracetamol"


def test_pg_queue_repo_should_get_last_queue_of_today(pg_queue_table, queue):
    repo = PostgresQueueRepository(pg_queue_table)

    assert repo.get_last_queue() is None

    queue.queue_date = date.today()
    repo.save(queue)

    queue_2 = copy.deepcopy(queue)
    queue_2.id = uuid4()
    queue_2.queue_number = Number(id=2)
    repo.save(queue_2)

    last_queue = repo.get_last_queue()

    assert last_queue is not None
    assert queue_2.id == last_queue.id
    assert queue_2.queue_number.id == 2
