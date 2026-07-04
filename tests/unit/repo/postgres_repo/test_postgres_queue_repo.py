import copy
from datetime import date, timedelta
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
    assert updated_queue.version.current_number == 2
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


def test_pg_queue_repo_should_find_active_queue(pg_queue_table, queue):

    repo = PostgresQueueRepository(pg_queue_table)

    # 1. บันทึกคิวใหม่ (สถานะตั้งต้นคือ WAITING ถือว่าเป็น Active Queue)
    queue.queue_date = date.today()
    repo.save(queue)

    # Act 1: ลองค้นหาคิว Active ของคนไข้คนนี้
    active_queue = repo.find_active_queue_by_patient(queue.patient_id, date.today())

    # Assert 1: ต้องเจอคิวที่เพิ่งบันทึกไป
    assert active_queue is not None
    assert active_queue.id == queue.id
    assert active_queue.status.value == "รอ"

    # 2. จำลองเหตุการณ์: คนไข้ตรวจเสร็จแล้ว (สถานะเปลี่ยนเป็น COMPLETED)
    queue.status = queue.status.COMPLETED
    queue.version = queue.version.increment()
    repo.update(queue)

    # Act 2: ลองค้นหาคิว Active อีกรอบ
    completed_queue = repo.find_active_queue_by_patient(queue.patient_id, date.today())

    # Assert 2: คราวนี้ต้อง "หาไม่เจอ" (ได้ None) เพราะคิวจบไปแล้ว ไม่ Active แล้ว
    assert completed_queue is None


def test_pg_queue_repo_should_get_all_queues_today(pg_queue_table, queue):
    repo = PostgresQueueRepository(pg_queue_table)

    today = date.today()
    yesterday = today - timedelta(days=1)

    queue.queue_date = today
    repo.save(queue)

    queue_2 = copy.deepcopy(queue)
    queue_2.id = uuid4()
    queue_2.queue_number = Number(id=2)
    repo.save(queue_2)

    queue_yesterday = copy.deepcopy(queue)
    queue_yesterday.id = uuid4()
    queue_yesterday.queue_number = Number(id=1)
    queue_yesterday.queue_date = yesterday
    repo.save(queue_yesterday)

    all_queues_today = repo.get_all_queues_today(today)

    assert all_queues_today is not None
    assert len(all_queues_today) == 2
    assert all_queues_today[0].id == queue.id
    assert all_queues_today[0].queue_number.id == 1
    assert all_queues_today[1].id == queue_2.id
    assert all_queues_today[1].queue_number.id == 2
