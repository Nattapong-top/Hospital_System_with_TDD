from uuid import UUID

from domain.consultation_entities import Consultation
from domain.custom_error import PermissionDeniedError
from domain.staff_entities import Staff
from domain.value_object import VitalSigns, StaffRole


class ExaminationService:
    def __init__(self, consul_repo=None):
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

        return new_consultation




