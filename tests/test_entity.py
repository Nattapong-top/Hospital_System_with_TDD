import uuid
from datetime import date

from pytest import fixture, raises

from domain.custom_error import MissingDiagnosisError, InvalidStatusTransitionError, \
    InvalidCancelRequestError
from domain.entities import Doctor, Queue
from domain.value_object import (
    Name, PhoneNumber, Address, Province,
    PatientRights, NationalID, Rights, LicenseNumber,
    MedicalSpecialty, Specialization, Number, QueueStatus,
    VitalSigns, BloodPressure, Weight, Height, Temperature,
    Diagnosis, MedicineInfo, Version)


def test_create_patient_is_validate(patient):
    assert patient.id is not None
    assert patient.national_id.id == '1234567890123'
    assert patient.first_name.value == 'นนทพัฒน์'
    assert patient.phone_number == PhoneNumber(value='0123456789')
    assert patient.rights == Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    assert patient.version == Version(number=1)


def test_should_raise_error_when_update_patient_id(patient):
    with raises(ValueError):
        patient.id = uuid.uuid4()


def test_should_raise_error_when_update_patient_national_id(patient):
    with raises(ValueError):
        patient.national_id = NationalID(id='1111111111111')


def test_should_update_patient_phone_number(patient):
    new_phone_number = PhoneNumber(value='0999999999')
    patient.update_phone_number(new_phone_number)
    assert patient.phone_number == new_phone_number
    assert patient.version == Version(number=2)


def test_should_update_current_address(patient):
    new_current_address = Address(  # ตั้งอยู่ที่ 173 ถนนดินสอ แขวงเสาชิงช้า เขตพระนคร กรุงเทพมหานคร 10200
        house_number='57',
        street='อุดมสุข',
        sub_district='บางนาเหนือ',
        district='บางนา',
        province=Province.BANGKOK,
        postal_code='10260'
    )
    patient.update_current_address(new_current_address)
    assert patient.current_address == new_current_address
    assert patient.version == Version(number=2)


def test_should_update_rights(patient):
    new_rights = Rights(rights_type=PatientRights.COMPANY_INSURANCE)
    patient.update_rights(new_rights)
    assert patient.rights == new_rights
    assert patient.version == Version(number=2)


def test_should_raise_error_when_update_rights_invalid_type(patient):
    with raises(ValueError):
        patient.update_rights(PhoneNumber(value='0123456789'))


def test_should_update_first_name(patient):
    new_first_name = Name(value='นันทวัน')
    patient.update_first_name(new_first_name)
    assert patient.first_name == new_first_name
    assert patient.version == Version(number=2)


def test_should_update_last_name(patient):
    new_last_name = Name(value='คนมั่งคั่ง')
    patient.update_last_name(new_last_name)
    assert patient.last_name == new_last_name
    assert patient.version == Version(number=2)


# ส่วนทดสอบ Entity Doctor
@fixture
def doctor():
    return Doctor(
        license_number=LicenseNumber(id='ว.11231'),
        first_name=Name(value='รักษาหาย'),
        last_name=Name(value='คนหายป่วย'),
        phone_number=PhoneNumber(value='0123456789'),
        medical_specialty=MedicalSpecialty(value=Specialization.INTERNAL_MEDICINE)
    )


def test_should_create_Doctor(doctor):
    assert doctor.first_name == Name(value='รักษาหาย')
    assert doctor.license_number == LicenseNumber(id='ว.11231')
    assert doctor.medical_specialty == MedicalSpecialty(value=Specialization.INTERNAL_MEDICINE)


def test_should_raise_error_when_update_id_doctor(doctor):
    with raises(ValueError):
        doctor.id = uuid.uuid4()


def test_should_raise_error_when_update_License_number_doctor(doctor):
    with raises(ValueError):
        doctor.license_number = LicenseNumber(id='ว.11231')


def test_should_update_first_name_doctor(doctor):
    new_first_name_doctor = Name(value='รักษาดี')
    doctor.update_first_name(new_first_name_doctor)
    assert doctor.first_name == Name(value='รักษาดี')


def test_should_update_last_name_doctor(doctor):
    new_last_name_doctor = Name(value='คนสุขภาพดี')
    doctor.update_last_name(new_last_name_doctor)
    assert doctor.last_name == new_last_name_doctor


def test_should_update_phone_number_doctor(doctor):
    new_phone_number_doctor = PhoneNumber(value='0888888888')
    doctor.update_phone_number(new_phone_number_doctor)
    assert doctor.phone_number == new_phone_number_doctor


def test_should_update_medical_specialty(doctor):
    new_medical_specialty = MedicalSpecialty(value=Specialization.CARDIOLOGY)
    doctor.update_medical_specialty(new_medical_specialty)
    assert doctor.medical_specialty == new_medical_specialty


def test_should_raise_error_when_update_medical_specialty_invalid_type(doctor):
    with raises(ValueError):
        doctor.update_medical_specialty(LicenseNumber(id='ว.11231'))


# ส่วนทดสอบ Entity Queue
@fixture
def queue(patient):
    return Queue(
        patient_id=patient.id,
        queue_number=Number(id=1),
        queue_date=date.today(),
        vital_signs=VitalSigns(
            blood_pressure=BloodPressure(systolic=120, diastolic=80),
            weight=Weight(value=80),
            height=Height(value=177),
            temperature=Temperature(value=39.0),
            symptom='น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น'
        ),
        status=QueueStatus.WAITING,
        version=Version(number=1)
    )
@fixture
def diagnosis(patient):
    return Diagnosis(
        disease='ไข้ทั่วไป',
        treatment='พักผ่านให้เพียงพอและดื่มน้ำมากๆ',
        medicine_prescribed=[MedicineInfo(
            name='Paracetamol',
            strength='500mg',
            frequency='วันละ 3 ครั้ง หลักอาหาร'
        )]
    )

def test_should_create_queue_entity_is_valid(patient, queue):
    assert queue.patient_id == patient.id
    assert queue.queue_date == date.today()
    assert queue.vital_signs == VitalSigns(
        blood_pressure=BloodPressure(systolic=120, diastolic=80),
        weight=Weight(value=80),
        height=Height(value=177),
        temperature=Temperature(value=39.0),
        symptom='น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น'
    )
    assert queue.status == QueueStatus.WAITING
    assert queue.version == Version(number=1)

def test_Queue_with_Version_should_next_version_when_is_valid(patient, queue):
    assert queue.version == Version(number=1)
    assert queue.patient_id == patient.id

    queue.start_consultation()
    assert queue.status == QueueStatus.IN_PROGRESS
    assert queue.version == Version(number=2)


def test_should_update_queue_entity_is_valid(queue):
    assert queue.status == QueueStatus.WAITING
    assert queue.version == Version(number=1)

    queue.start_consultation()
    assert queue.status == QueueStatus.IN_PROGRESS
    assert queue.version == Version(number=2)

def test_should_raise_error_when_start_consultation_but_status_is_not_waiting(queue):
    queue.status = QueueStatus.COMPLETED
    with raises(InvalidStatusTransitionError, match='ไม่สามารถเริ่มตรวจได้'):
        queue.start_consultation()

def test_should_change_status_from_in_progress_to_completed(queue, diagnosis):
    queue.status = QueueStatus.IN_PROGRESS
    queue.complete_visit(diagnosis=diagnosis)
    assert queue.status == QueueStatus.COMPLETED
    assert queue.diagnosis == diagnosis

def test_should_raise_error_when_complete_visit_but_not_diagnosis(queue):
    queue.status = QueueStatus.IN_PROGRESS
    with raises(MissingDiagnosisError):
        queue.complete_visit(diagnosis=None)


def test_should_raise_error_when_IN_PROGRESS_but_status_is_WAITTING(queue):
    queue.status = QueueStatus.IN_PROGRESS
    with raises(InvalidStatusTransitionError):
        queue.start_consultation()

def test_should_raise_error_when_complete_visit_but_status_is_WAITTING(queue, diagnosis):
    assert queue.status == QueueStatus.WAITING
    with raises(InvalidStatusTransitionError):
        queue.complete_visit(diagnosis=diagnosis)

def test_should_change_status_to_cancelled(queue):
    queue.cancel_visit()
    assert queue.status == QueueStatus.CANCELLED

def test_should_raise_error_when_complete_visit_but_status_is_CANCELLED(queue):
    queue.status = QueueStatus.COMPLETED
    with raises(InvalidCancelRequestError):
        queue.cancel_visit()

def test_should_change_status_to_in_progress(queue):
    queue.status = QueueStatus.IN_PROGRESS
    assert queue.status == QueueStatus.IN_PROGRESS
    queue.cancel_visit()
    assert queue.status == QueueStatus.CANCELLED