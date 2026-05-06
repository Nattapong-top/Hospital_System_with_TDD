from uuid import UUID

from domain.consultation_entities import Consultation
from domain.custom_error import PermissionDeniedError
from domain.interfaces import ConsultationRepository
from domain.staff_entities import Staff
from domain.value_object import VitalSigns, StaffRole


class ExaminationService:
    def __init__(self, consul_repo: ConsultationRepository) -> None:
        self.consultation_repo = consul_repo

    def start_consultation(self, queue_id: UUID, doctor: Staff,
                 patient_id: UUID, vital_signs: VitalSigns) -> Consultation:

        if doctor.role is not StaffRole.DOCTOR:
            raise PermissionDeniedError('หมอเท่านั้นที่มีสิทธิ์ตรวจ')

        new_consultation = Consultation(
            queue_id=queue_id,
            doctor=doctor,
            patient_id=patient_id,
            vital_signs=vital_signs
        )

        self.consultation_repo.save(new_consultation)
        return new_consultation

    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation:
        return self.consultation_repo.get_by_consultation_id(consultation_id)



