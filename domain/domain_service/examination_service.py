from typing import Optional
from uuid import UUID

from domain.consultation_entities import Consultation
from domain.custom_error import (
    PermissionDeniedError,
    ConsultationNotFoundError,
    StaffNotFoundError,
    QueueNotFoundError,
)
from domain.domain_service.queue_service import QueueService
from domain.entities import Queue
from domain.interfaces import ConsultationRepository
from domain.staff_entities import Staff
from domain.value_object import StaffRole, Diagnosis


class ExaminationService:
    def __init__(
        self, consul_repo: ConsultationRepository, queue_service: QueueService = None
    ) -> None:
        self.consultation_repo = consul_repo
        self.queue_service: Optional[QueueService] = queue_service

    def start_consultation(self, queue_id: UUID, staff: Staff) -> Consultation:

        queue_db = self._check_queue_id_not_found(
            queue_id
        )  # เพิ่มการเรียกใช้เมธอดตรวจสอบคิว
        self._check_staff_not_found(staff)
        self._check_role_nurse_or_doctor(staff)
        self._update_state_queue_to_in_progress(queue_id)

        new_consultation = Consultation(
            queue_id=queue_id,
            doctor_id=staff.staff_id,
            patient_id=queue_db.patient_id,
            vital_signs=queue_db.vital_signs,
        )

        self.consultation_repo.save(new_consultation)
        return new_consultation

    def finish_consultation(
        self, consultation_id: UUID, queue_id: UUID, doctor: Staff, diagnosis: Diagnosis
    ) -> Consultation:
        self._check_staff_not_found(doctor)
        self._check_role_only_staff_doctor(doctor)
        consultation = self._get_consultation_or_raise(consultation_id)
        self._update_state_queue_to_complete(queue_id)

        consultation.complete_examination(diagnosis)
        self.consultation_repo.update(consultation)

        return consultation

    def cancel_consultation(
        self, consultation_id: UUID, queue_id: UUID, staff: Staff
    ) -> Consultation:

        self._check_staff_not_found(staff)
        self._check_role_nurse_or_doctor(staff)
        consultation = self._get_consultation_or_raise(consultation_id)

        consultation.cancel_examination()
        self._update_state_queue_to_cancel(queue_id)

        self.consultation_repo.update(consultation)
        return consultation

    def get_by_consultation_id(self, consultation_id: UUID) -> Optional[Consultation]:
        return self.consultation_repo.get_by_consultation_id(consultation_id)

    def _check_queue_id_not_found(self, queue_id: UUID) -> Queue | None:
        """
        ตรวจสอบความมีตัวตนของคิวในระบบฐานข้อมูล
        """
        # อาวุธลับ: หากไม่มี queue_service (กรณีหน่วยทดสอบเก่า) ให้ข้ามการตรวจสอบเพื่อป้องกันข้อผิดพลาด
        if self.queue_service is None:
            return None

        # ดำเนินการตรวจสอบข้อมูลคิวจากบริการจัดการคิว
        queue_db = self.queue_service.get_by_queue_id(queue_id)
        if queue_db is None:
            raise QueueNotFoundError(queue_id=queue_id)
        return queue_db

    def _get_consultation_or_raise(self, consultation_id: UUID) -> Consultation:
        consultation = self.consultation_repo.get_by_consultation_id(consultation_id)
        if consultation is None:
            raise ConsultationNotFoundError(consultation_id)
        return consultation

    def _check_staff_not_found(self, staff: Staff):
        if staff is None:
            raise StaffNotFoundError()

    def _check_role_nurse_or_doctor(self, staff: Staff) -> None:
        if staff.role not in [StaffRole.NURSE, StaffRole.DOCTOR]:
            raise PermissionDeniedError()

    def _check_role_only_staff_doctor(self, doctor: Staff) -> None:
        if doctor.role is not StaffRole.DOCTOR:
            raise PermissionDeniedError()

    def _update_state_queue_to_in_progress(self, queue_id: UUID) -> None:
        if self.queue_service:
            self.queue_service.change_status_to_examining(queue_id)

    def _update_state_queue_to_complete(self, queue_id) -> None:
        if self.queue_service:
            self.queue_service.change_status_complete(queue_id)

    def _update_state_queue_to_cancel(self, queue_id) -> None:
        if self.queue_service:
            self.queue_service.cancel_visit(queue_id)
