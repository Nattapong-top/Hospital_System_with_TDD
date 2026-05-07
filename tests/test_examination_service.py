from pytest import raises

from domain.custom_error import PermissionDeniedError
from domain.domain_service.examination_service import ExaminationService
from domain.value_object import QueueStatus
from tests.conftest import new_queue, new_staff_doctor, InMem_consul_repo
from tests.fake_repository.fake_repository import InMemConsulRepo


def test_exam_service_start_consul_should_succeed(new_queue, new_staff_doctor, InMem_consul_repo):
    consul = ExaminationService(InMem_consul_repo).start_consultation(
        queue_id=new_queue.id,
        doctor=new_staff_doctor,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )
    assert consul is not None
    assert consul.queue_id == new_queue.id
    assert consul.status.value == 'กำลังพบหมอ'


def test_start_consultation_by_nurse_should_raise_permission_denied_error(new_queue, new_staff_nurse, InMem_consul_repo):
    """โจทย์: ถ้าส่งพยาบาลมาเริ่มตรวจ ระบบต้องระเบิด Error ทันที"""
    # 1. Arrange: เตรียมพยาบาล (ที่มี role = NURSE)
    service = ExaminationService(InMem_consul_repo)

    # 2. Act & Assert: ลองของ! ส่งพยาบาลเข้าไปตรวจ
    with raises(PermissionDeniedError) as err:
        service.start_consultation(
            queue_id=new_queue.id,
            doctor=new_staff_nurse,  # 🚩 ส่งตัว Staff เข้าไปเลยจะได้เช็ค Role ได้
            patient_id=new_queue.patient_id,
            vital_signs=new_queue.vital_signs
        )
    assert 'หมอเท่านั้นที่มีสิทธิ์ตรวจ' in str(err.value)

def test_exam_service_start_consul_should_save_to_repo(new_queue, new_staff_doctor):
    repo = InMemConsulRepo()
    consul = ExaminationService(repo).start_consultation(
        queue_id=new_queue.id,
        doctor=new_staff_doctor,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )
    consul_db = repo.get_by_consultation_id(consul.id)
    assert consul_db is not None
    assert consul_db.queue_id == new_queue.id
    assert consul_db.doctor.staff_id == new_staff_doctor.staff_id
    assert consul_db.patient_id == new_queue.patient_id
    assert consul_db.status.value == 'กำลังพบหมอ'

def test_exam_service_start_consul_should_get_by_consul_id_form_repo(new_examination,new_queue, new_staff_doctor,exam_service):
    service = exam_service
    consul_db = service.get_by_consultation_id(new_examination.id)
    assert consul_db is not None
    assert consul_db.queue_id == new_queue.id
    assert consul_db.doctor.staff_id == new_staff_doctor.staff_id
    assert consul_db.patient_id == new_queue.patient_id
    assert consul_db.status.value == 'กำลังพบหมอ'


def test_start_consultation_should_update_queue_status_to_in_progress(new_queue, new_staff_doctor, queue_service,
                                                                      queue_repo):
    # 1. Arrange: เตรียมทั้ง Repo ของใบตรวจ และ Repo ของคิว
    consul_repo = InMemConsulRepo()
    queue_repo.save(new_queue)  # ใส่คิวเริ่มต้นเข้าไปก่อน (สถานะ WAITING)

    # ฉีด QueueRepo เข้าไปใน ExaminationService ด้วย (หรือฉีด QueueService ก็ได้)
    service = ExaminationService(consul_repo=consul_repo, queue_service=queue_service)

    # 2. Act: เริ่มการตรวจผ่าน ExaminationService
    service.start_consultation(
        queue_id=new_queue.id,
        doctor=new_staff_doctor,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs
    )

    # 3. Assert: ไปแอบดูที่ QueueRepo ว่าคิวโดนเปลี่ยนสถานะหรือยัง
    updated_queue = queue_service.get_by_queue_id(new_queue.id)
    assert updated_queue.status.value == QueueStatus.IN_PROGRESS.value