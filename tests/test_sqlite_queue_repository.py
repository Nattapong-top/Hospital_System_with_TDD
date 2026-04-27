import os

from pytest import raises

from domain.value_object import (
    QueueStatus, Diagnosis, MedicineInfo)


def test_sqlite_queue_repo_should_save_and_retrieve_queue(patient, queue, queue_repo):
    queue_repo.create_schema()
    pa_queue = queue
    queue_repo.save(pa_queue)

    retrieved = queue_repo.get_by_queue_id(pa_queue.id)
    assert retrieved.id == pa_queue.id
    assert retrieved.patient_id == pa_queue.patient_id
    assert retrieved.vital_signs.blood_pressure.systolic == 120
    assert retrieved.vital_signs.temperature.value == 39.0
    assert retrieved.vital_signs.symptom == 'น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น'

    os.remove(queue_repo.db_path)

def test_sqlite_queue_repo_should_update_existing_queue(patient, queue, queue_repo):
    queue_repo.create_schema()
    sample_queue = queue
    assert sample_queue.status == QueueStatus.WAITING

    queue_repo.save(sample_queue)
    sample_queue.start_consultation()
    queue_repo.update(sample_queue)
    updated_queue = queue_repo.get_by_queue_id(sample_queue.id)

    assert updated_queue.status == QueueStatus.IN_PROGRESS
    assert updated_queue.version.number == 2

    queue_all = queue_repo.get_all()
    assert len(queue_all) == 1
    os.remove(queue_repo.db_path)


def test_sqlite_queue_repo_should_return_none_when_queue_not_found(queue_repo):
    queue_repo.create_schema()
    import uuid
    random_id = uuid.uuid4()
    result_queue = queue_repo.get_by_queue_id(random_id)
    assert result_queue is None
    os.remove(queue_repo.db_path)


def test_sqlite_queue_repo_should_return_empty_list_when_db_is_empty(queue_repo):
    queue_repo.create_schema()

    result = queue_repo.get_all()
    assert isinstance(result, list)
    assert len(result) == 0
    os.remove(queue_repo.db_path)


def test_sqlite_queue_repo_should_save_extremely_long_diagnosis(queue_repo, queue):
    queue_repo.create_schema()
    queue.start_consultation()
    max_disease = 'ปวดหั' * 5
    max_treatment = 'ตัวร้อ' * 5
    queue.complete_visit(Diagnosis(
        disease=max_disease,
        treatment=max_treatment,
        medicine_prescribed=[MedicineInfo(
            name='Paracetamol',
            strength='500mg',
            frequency='วันละ 3 ครั้ง หลังอาหาร')]
        )
    )
    queue_repo.save(queue)
    retrieved = queue_repo.get_by_queue_id(queue.id)

    assert retrieved.id == queue.id
    assert retrieved.patient_id == queue.patient_id
    assert retrieved.status == QueueStatus.COMPLETED
    assert retrieved.diagnosis.disease == max_disease
    assert retrieved.diagnosis.treatment == max_treatment
    os.remove(queue_repo.db_path)


def test_sqlite_queue_queue_repo_should_raise_error_when_concurrency_conflict(queue_repo, queue):
    queue_repo.create_schema()
    queue_repo.save(queue)

    nurse_a_view = queue_repo.get_by_queue_id(queue.id)
    nurse_b_view = queue_repo.get_by_queue_id(queue.id)
    assert nurse_a_view.version.number == nurse_b_view.version.number
    assert nurse_a_view.version.number == 1

    nurse_a_view.start_consultation()
    queue_repo.update(nurse_a_view)
    assert nurse_a_view.version.number == 2

    nurse_b_view.cancel_visit()

    with raises(RuntimeError) as error:
        queue_repo.update(nurse_b_view)
        os.remove(queue_repo.db_path)

    assert 'ข้อมูลใบคิวถูก update โดยผู้อื่นไปก่อนหน้าแล้ว' in str(error.value)


def test_sqlite_queue_repo_should_update_queue_when_have_id_(queue_repo, queue):
    queue_repo.save(queue)
    retrieved = queue_repo.get_by_queue_id(queue.id)
    assert retrieved is not None
    assert retrieved.id == queue.id
    assert retrieved.version.number == 1

    retrieved.start_consultation()
    assert retrieved.version.number == 2

    queue_repo.update(retrieved)

    db_queue = queue_repo.get_by_queue_id(queue.id)
    assert db_queue.status == QueueStatus.IN_PROGRESS
    assert db_queue.version.number == 2
