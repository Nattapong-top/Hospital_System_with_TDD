from uuid import UUID

from domain.consultation_entities import Consultation
from domain.value_object import VitalSigns


class ExaminationService:
    def __init__(self, consul_repo=None):
        self.consultation_repo = consul_repo

    def start_consultation(self, queue_id: UUID, doctor_id: UUID,
                 patient_id: UUID, vital_signs: VitalSigns) -> Consultation:

        new_consultation = Consultation(
            queue_id=queue_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            vital_signs=vital_signs
        )

        return new_consultation




