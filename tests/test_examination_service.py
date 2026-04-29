from domain.domain_service.examination_service import ExaminationService
from tests.conftest import new_queue, new_staff_doctor


def test_exam_service_start_consul_should_succeed(new_queue, new_staff_doctor):
    consul = ExaminationService().start_consultation(
        queue_id=new_queue.id,
        doctor_id=new_staff_doctor.staff_id,
        patient_id=new_queue.patient_id,
        vital_signs=new_queue.vital_signs,
    )
    assert consul is not None
    assert consul.queue_id == new_queue.id
