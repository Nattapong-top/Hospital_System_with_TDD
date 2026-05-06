from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

from domain.custom_error import InvalidStatusTransitionError, MissingDiagnosisError, \
    InvalidCancelRequestError
from domain.entities import DomainEntity
from domain.staff_entities import Staff
from domain.value_object import VitalSigns, Diagnosis, Version, QueueStatus


class Consultation(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    queue_id: UUID
    doctor: Staff
    patient_id: UUID
    vital_signs: VitalSigns
    diagnosis: Optional[Diagnosis] = None
    status: QueueStatus = QueueStatus.IN_PROGRESS
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    version: Version = Field(default=Version(number=1))

    def complete_examination(self, diagnosis: Diagnosis) -> None:
        self._validate_in_progress_status_and_missing_diagnosis(diagnosis=diagnosis)
        self.status = QueueStatus.COMPLETED
        self.diagnosis = diagnosis
        self.finished_at = datetime.now()
        self.version = self.version.increment()

    def cancel_examination(self) -> None:
        self._validate_cancellation()
        self.status = QueueStatus.CANCELLED
        self.finished_at = datetime.now()
        self.version = self.version.increment()

    def _validate_in_progress_status_and_missing_diagnosis(self, diagnosis: Diagnosis) -> None:
        if self.status != QueueStatus.IN_PROGRESS:
            raise InvalidStatusTransitionError(f'ไม่สามารถจบการตรวจได้ เพราะสถานะปัจจุบันคือ {self.status.value}')

        if diagnosis is None:
            raise MissingDiagnosisError()

    def _validate_cancellation(self):
        if self.status == QueueStatus.COMPLETED:
            raise InvalidCancelRequestError(f'ไม่สามารถยกเลิกการตรวจได้ เพราะสถานะปัจจุบันคือ {self.status.value}')