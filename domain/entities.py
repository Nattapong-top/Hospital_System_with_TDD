from datetime import date
from typing import Optional

from pydantic import Field
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from domain.custom_error import (
    InvalidStatusTransitionError, MissingDiagnosisError, InvalidCancelRequestError)
from domain.value_object import (
    Name, PhoneNumber, DateOfBirth, Address, NationalID, Rights,
    LicenseNumber, MedicalSpecialty, Number, QueueStatus, VitalSigns,
    Diagnosis, Version)


class DomainEntity(BaseModel):
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True
    )


class Patient(DomainEntity):
    id: UUID
    national_id: NationalID
    first_name: Name
    last_name: Name
    phone_number: PhoneNumber
    date_of_birth: DateOfBirth
    registered_address: Address
    current_address: Address
    rights: Rights
    version: Version = Field(default=Version(number=1))

    def __setattr__(self, name: str, value) -> None:
        # ป้องกันการเปลี่ยนค่า field ที่ห้ามแก้ไข
        # รันทุกครั้งที่มีการ set ค่า field ใดๆ ใน object นี้
        # hasattr เช็คว่า field นั้นมีค่าอยู่แล้วหรือยัง
        # (ถ้ายังไม่มี = กำลังสร้างครั้งแรก → ให้ผ่าน)
        if name in ('id', 'national_id') and hasattr(self, name):
            raise ValueError(f'ห้ามเปลี่ยน {name} ครับ')

        # ถ้าไม่ใช่ field ต้องห้าม → ให้ Pydantic จัดการต่อตามปกติ
        super().__setattr__(name, value)

    def update_phone_number(self, new_phone_number: PhoneNumber) -> None:
        self.phone_number = new_phone_number
        self.version = self.version.increment()

    def update_current_address(self, new_address: Address) -> None:
        self.current_address = new_address
        self.version = self.version.increment()

    def update_rights(self, new_rights: Rights) -> None:
        self.rights = new_rights
        self.version = self.version.increment()

    def update_first_name(self, new_first_name: Name) -> None:
        self.first_name = new_first_name
        self.version = self.version.increment()

    def update_last_name(self, new_last_name: Name) -> None:
        self.last_name = new_last_name
        self.version = self.version.increment()


class Doctor(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    license_number: LicenseNumber
    first_name: Name
    last_name: Name
    phone_number: PhoneNumber
    medical_specialty: MedicalSpecialty

    def __setattr__(self, name: str, value) -> None:
        # ป้องกันการเปลี่ยนค่า field ที่ห้ามแก้ไข
        # รันทุกครั้งที่มีการ set ค่า field ใดๆ ใน object นี้
        # hasattr เช็คว่า field นั้นมีค่าอยู่แล้วหรือยัง
        # (ถ้ายังไม่มี = กำลังสร้างครั้งแรก → ให้ผ่าน)
        if name in ('id', 'license_number') and hasattr(self, name):
            raise ValueError(f'ห้ามเปลี่ยน {name} ครับ')

        # ถ้าไม่ใช่ field ต้องห้าม → ให้ Pydantic จัดการต่อตามปกติ
        super().__setattr__(name, value)

    def update_first_name(self, new_first_name: Name) -> None:
        self.first_name = new_first_name

    def update_last_name(self, new_last_name: Name) -> None:
        self.last_name = new_last_name

    def update_phone_number(self, new_phone_number: PhoneNumber) -> None:
        self.phone_number = new_phone_number

    def update_medical_specialty(self, new_medical_specialty: MedicalSpecialty) -> None:
        self.medical_specialty = new_medical_specialty


class Queue(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    queue_number: Number
    queue_date: date
    vital_signs: Optional[VitalSigns] = None
    status: QueueStatus
    diagnosis: Optional[Diagnosis] = None
    version: Version = Field(default=Version(number=1))

    def start_consultation(self) -> None:
        self._validate_status()
        self.status = QueueStatus.IN_PROGRESS
        self.version = self.version.increment()

    def complete_visit(self, diagnosis: Diagnosis) -> None:
        self._validate_in_progress_status(diagnosis=diagnosis)
        self.status = QueueStatus.COMPLETED
        self.diagnosis = diagnosis
        self.version = self.version.increment()

    def cancel_visit(self) -> None:
        self._validate_cancellation()
        self.status = QueueStatus.CANCELLED
        self.version = self.version.increment()

    def _validate_cancellation(self):
        if self.status == QueueStatus.COMPLETED:
            raise InvalidCancelRequestError(f'ไม่สามารถยกเลิกการตรวจได้ เพราะสถานะปัจจุบันคือ {self.status.value}')

    def _validate_in_progress_status(self, diagnosis: Diagnosis) -> None:
        if self.status != QueueStatus.IN_PROGRESS:
            raise InvalidStatusTransitionError(f'ไม่สามารถจบการตรวจได้ เพราะสถานะปัจจุบันคือ {self.status.value}')

        if diagnosis is None:
            raise MissingDiagnosisError()

    def _validate_status(self):
        if self.status != QueueStatus.WAITING:
            raise InvalidStatusTransitionError(f'ไม่สามารถเริ่มตรวจได้ เพราะสถานปัจจบันคือ {self.status.value}')
