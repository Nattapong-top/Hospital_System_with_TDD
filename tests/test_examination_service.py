from pytest import raises

from domain.custom_error import PermissionDeniedError
from domain.domain_service.examination_service import ExaminationService
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