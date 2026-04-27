#domain.domain_service.patient_registrar
from uuid import uuid4

from domain.entities import Patient
from domain.value_object import (
    NationalID, Name, PhoneNumber, DateOfBirth, Address, Rights)


class PatientRegistrar:
    def __init__(self,patient_repo) -> None:
        self.patient_repo = patient_repo

    def register_new_patient(self,
                             national_id: NationalID, first_name: Name, last_name: Name,
                             phone_number: PhoneNumber, date_of_birth: DateOfBirth,
                             registered_address: Address, current_address: Address,
                             rights: Rights) -> Patient:

        existing_patient = self.patient_repo.get_by_national_id(national_id=national_id)
        if existing_patient:
            return existing_patient

        new_patient = Patient(
            id=uuid4(),
            national_id=national_id,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            registered_address=registered_address,
            current_address=current_address,
            rights=rights
        )

        self._save_patient(new_patient)
        return new_patient

    def update_patient_info(self, patient: Patient) -> None:
        self.patient_repo.update(patient=patient)

    # ยกเลิก เพราะเปลียน business logic จาก raise เป็น return patient
    # def _check_duplicate_national_id(self, national_id: NationalID) -> None:
    #     existing_patient = self.patient_repo.get_by_national_id(national_id=national_id)
    #     if existing_patient:
    #         raise DuplicateNationalIDError(f'เลขบัตรประชาชนนี้มีในระบบแล้ว: {national_id.id}')

    def _save_patient(self, patient: Patient) -> Patient:
        self.patient_repo.save(patient=patient)
        return patient

    # ใน patient_registrar.py
    def get_patient(self, national_id: NationalID) -> Patient:
        return self.patient_repo.get_by_national_id(national_id=national_id)