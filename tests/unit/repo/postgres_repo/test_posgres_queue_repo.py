from infrastructure.postgres_queue_repository import PostgresQueueRepository


def test_pg_queue_repo_should_save_and_retrieve_queue(pg_queue_table, new_queue):
    repo = PostgresQueueRepository(pg_queue_table)
    repo.save(new_queue)

    retrieve_queue = repo.get_by_queue_id(new_queue.id)

    assert retrieve_queue is not None
    assert new_queue.id == retrieve_queue.id
    assert new_queue.patient_id == retrieve_queue.patient_id
