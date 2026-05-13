from uuid import uuid4

from pytest import raises

from domain.custom_error import PermissionDeniedError, InvalidStatusTransitionError, ConsultationNotFoundError, \
    MissingDiagnosisError
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
    assert consul_db.doctor_id == new_staff_doctor.staff_id
    assert consul_db.patient_id == new_queue.patient_id
    assert consul_db.status.value == 'กำลังพบหมอ'

def test_exam_service_start_consul_should_get_by_consul_id_form_repo(new_examination,new_queue, new_staff_doctor,exam_service):
    service = exam_service
    consul_db = service.get_by_consultation_id(new_examination.id)
    assert consul_db is not None
    assert consul_db.queue_id == new_queue.id
    assert consul_db.doctor_id == new_staff_doctor.staff_id
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


def test_finished_consultation_should_update_queue_completed(new_examination, diagnosis, exam_service, new_staff_doctor,
                                                             queue_service):
    finish_consul = exam_service.finish_consultation(
        consultation_id=new_examination.id,
        queue_id=new_examination.queue_id,
        doctor=new_staff_doctor,
        diagnosis=diagnosis,
    )
    assert finish_consul.status.value == new_examination.status.value
    assert finish_consul is not None
    assert finish_consul.id == new_examination.id
    assert finish_consul.queue_id == new_examination.queue_id
    assert finish_consul.doctor_id == new_examination.doctor_id

    finish_consul_db = exam_service.get_by_consultation_id(finish_consul.id)
    assert finish_consul_db is not None
    assert finish_consul_db.id == new_examination.id
    assert finish_consul_db.patient_id == finish_consul.patient_id
    assert finish_consul_db.status.value == QueueStatus.COMPLETED.value

    updated_queue = queue_service.get_by_queue_id(new_examination.queue_id)
    assert updated_queue.status.value == QueueStatus.COMPLETED.value


def test_finish_consultation_with_invalid_id_should_raise_error(exam_service, new_staff_doctor, diagnosis):
    # Arrange: สร้าง ID ปลอมที่ไม่มีในโลก
    random_id = uuid4()

    # Act & Assert
    with raises(ConsultationNotFoundError):
        exam_service.finish_consultation(
            consultation_id=random_id,
            queue_id=uuid4(),  # มั่วไปก่อน
            doctor=new_staff_doctor,
            diagnosis=diagnosis
        )


def test_cannot_finish_consultation_twice(new_examination, diagnosis, exam_service, new_staff_doctor):
    # 1. ครั้งแรกต้องผ่าน
    exam_service.finish_consultation(
        consultation_id=new_examination.id,
        queue_id=new_examination.queue_id,
        doctor=new_staff_doctor,
        diagnosis=diagnosis
    )

    # 2. ครั้งที่สองต้องระเบิด!
    with raises(InvalidStatusTransitionError):
        exam_service.finish_consultation(
            consultation_id=new_examination.id,
            queue_id=new_examination.queue_id,
            doctor=new_staff_doctor,
            diagnosis=diagnosis
        )

def test_finish_consultation_forget_diagnosis_should_raise_error(
        exam_service, new_staff_doctor,new_examination):
    with raises(MissingDiagnosisError):
        exam_service.finish_consultation(
            consultation_id=new_examination.id,
            queue_id=new_examination.queue_id,
            doctor=new_staff_doctor,
            diagnosis=None
        )


def test_finish_consultation_invalid_status_should_raise_error(
        new_examination, diagnosis, exam_service, new_staff_doctor):
    # 1. Arrange: แอบไปเปลี่ยนสถานะเป็น CANCELLED ก่อน (จำลองว่าถูกยกเลิกไปแล้ว)
    new_examination.status = QueueStatus.CANCELLED
    # ต้องเซฟลง Repo ด้วยเพื่อให้ Service ไปดึงสถานะที่แก้แล้วออกมา
    exam_service.consultation_repo.save(new_examination)

    # 2. Act & Assert: ลองสั่งจบการตรวจ ต้องระเบิด Error ทันที!
    with raises(InvalidStatusTransitionError) as exc:
        exam_service.finish_consultation(
            consultation_id=new_examination.id,
            queue_id=new_examination.queue_id,
            doctor=new_staff_doctor,
            diagnosis=diagnosis
        )

    # เช็คคำด่า เอ้ย! คำอธิบาย Error นิดนึงว่าตรงไหม
    assert "ไม่สามารถจบการตรวจได้" in str(exc.value)


def test_finish_consultation_should_increment_version(
        new_examination, diagnosis, exam_service, new_staff_doctor):
    # 1. Arrange: เช็คก่อนว่าตอนเริ่ม Version คือ 1
    assert new_examination.version.number == 1

    # 2. Act: สั่งจบการตรวจ
    finished_consul = exam_service.finish_consultation(
        consultation_id=new_examination.id,
        queue_id=new_examination.queue_id,
        doctor=new_staff_doctor,
        diagnosis=diagnosis
    )

    # 3. Assert: เลข Version ต้องขยับเป็น 2
    assert finished_consul.version.number == 2

    # และในตู้เหล็ก (Repo) ก็ต้องเป็นเลข 2 ด้วย
    consul_in_db = exam_service.get_by_consultation_id(new_examination.id)
    assert consul_in_db.version.number == 2


def test_cancel_consultation_should_succeed_and_increment_version(
        new_examination, exam_service, new_staff_doctor):
    """เทสการยกเลิกปกติ: สถานะต้องเปลี่ยน และเวอร์ชันต้องขยับ"""
    # 1. Arrange: เช็คเวอร์ชันก่อนยกเลิก
    assert new_examination.version.number == 1

    # 2. Act: สั่งยกเลิก
    cancelled_consul = exam_service.cancel_consultation(
        consultation_id=new_examination.id,
        queue_id=new_examination.queue_id,
        staff=new_staff_doctor
    )

    # 3. Assert
    assert cancelled_consul.status == QueueStatus.CANCELLED
    assert cancelled_consul.version.number == 2
    assert cancelled_consul.finished_at is not None  # ต้องมีการประทับเวลายกเลิก


def test_cannot_cancel_already_completed_consultation(
        new_examination, diagnosis, exam_service, new_staff_doctor):
    """เทสป้องกันบั๊ก: ถ้าตรวจเสร็จไปแล้ว ห้ามมากดยกเลิกทีหลัง!"""
    # 1. Arrange: หมอตรวจเสร็จไปแล้ว
    exam_service.finish_consultation(
        consultation_id=new_examination.id,
        queue_id=new_examination.queue_id,
        doctor=new_staff_doctor,
        diagnosis=diagnosis
    )

    # 2. Act & Assert: พยายามกดยกเลิกคิวที่จบไปแล้ว ต้องระเบิด Error
    # (สมมติว่าใน Entity ป๋า raise Error ตัวนี้นะครับ ถ้าเป็นชื่ออื่น ป๋าเปลี่ยนได้เลย)
    with raises(Exception) as exc:
        exam_service.cancel_consultation(
            consultation_id=new_examination.id,
            queue_id=new_examination.queue_id,
            staff=new_staff_doctor
        )

    # หรือ assert ข้อความ error ควบคู่ไปด้วย
    assert "ไม่สามารถยกเลิกการตรวจได้" in str(exc.value)


def test_cancel_consultation_with_invalid_id_should_raise_error(
        exam_service, new_staff_doctor):
    """เทสถ้าส่ง ID มั่วๆ มายกเลิก ต้องหาไม่เจอ"""
    from uuid import uuid4
    from domain.custom_error import ConsultationNotFoundError

    with raises(ConsultationNotFoundError):
        exam_service.cancel_consultation(
            consultation_id=uuid4(),
            queue_id=uuid4(),
            staff=new_staff_doctor
        )