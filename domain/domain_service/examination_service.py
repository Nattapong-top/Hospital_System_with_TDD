from uuid import UUID

from domain.consultation_entities import Consultation
from domain.custom_error import PermissionDeniedError, ConsultationNotFoundError
from domain.domain_service.queue_service import QueueService
from domain.interfaces import ConsultationRepository
from domain.staff_entities import Staff
from domain.value_object import VitalSigns, StaffRole, Diagnosis


class ExaminationService:
    def __init__(self, consul_repo: ConsultationRepository, queue_service: QueueService = None) -> None:
        self.consultation_repo = consul_repo
        self.queue_service = queue_service

    def start_consultation(self, queue_id: UUID, doctor: Staff,
                           patient_id: UUID, vital_signs: VitalSigns) -> Consultation:

        self._check_role_only_staff_doctor(doctor)
        self._update_state_queue_to_in_progress(queue_id)

        new_consultation = Consultation(
            queue_id=queue_id,
            doctor_id=doctor.staff_id,
            patient_id=patient_id,
            vital_signs=vital_signs
        )

        self.consultation_repo.save(new_consultation)
        return new_consultation

    def finish_consultation(self, consultation_id: UUID, queue_id: UUID, doctor: Staff, diagnosis: Diagnosis) -> Consultation:
        self._check_role_only_staff_doctor(doctor)
        self._update_state_queue_to_complete(queue_id)

        consultation = self._get_consultation_or_raise(consultation_id=consultation_id)
        consultation.complete_examination(diagnosis)

        self.consultation_repo.update(consultation)
        return consultation

    def _get_consultation_or_raise(self, consultation_id: UUID) -> Consultation:
        consultation = self.consultation_repo.get_by_consultation_id(consultation_id=consultation_id)
        if consultation is None:
            raise ConsultationNotFoundError(consultation_id)
        return consultation

    def _check_role_only_staff_doctor(self, doctor: Staff):
        if doctor.role is not StaffRole.DOCTOR:
            raise PermissionDeniedError('หมอเท่านั้นที่มีสิทธิ์ตรวจ')

    def _update_state_queue_to_in_progress(self, queue_id: UUID):
        if self.queue_service:
            self.queue_service.start_consultation(queue_id)

    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation | None:
        return self.consultation_repo.get_by_consultation_id(consultation_id)

    def _update_state_queue_to_complete(self, queue_id):
        if self.queue_service:
            self.queue_service.complete_visit(queue_id)
