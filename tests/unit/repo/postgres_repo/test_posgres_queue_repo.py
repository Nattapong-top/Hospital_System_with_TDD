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
