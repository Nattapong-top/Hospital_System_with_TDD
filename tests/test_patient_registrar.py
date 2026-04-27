#tests.test_patient_registrar

from pydantic import ValidationError
from pytest import raises

from domain.domain_service.patient_registrar import PatientRegistrar
from domain.value_object import (
    NationalID, Name, PhoneNumber, DateOfBirth, Rights, PatientRights)
from tests.conftest import vital_signs
from tests.fake_repository.fake_repository import (
    BrokenPatientRecord)


def test_registrar_patient_when_patient_valid(registrar, patient_repo, registered_address, current_address):
    new_patient = registrar.register_new_patient(
        national_id=NationalID(id='1234567890123'),
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    )
    retrieve = new_patient

    assert retrieve.national_id == NationalID(id='1234567890123')
    assert retrieve.rights.rights_type == PatientRights.SOCIAL_SECURITY
    saved_patient = patient_repo.get_by_national_id(NationalID(id='1234567890123'))
    assert saved_patient is not None
    assert retrieve.id == saved_patient.id
    assert saved_patient.national_id == NationalID(id='1234567890123')
    assert saved_patient.version.number == 1

# ยกเลิกเทส เพราะเปลียน business logic จาก raise เป็น return patient
# def test_registrar_patient_should_raise_error_when_duplicate_national_id(registrar, registered_address,
#                                                                          current_address,vital_signs):
#     common_id = NationalID(id='1234567890123')
#     registrar.register_new_patient(
#         national_id=common_id,
#         first_name=Name(value='นนทพัฒน์'),
#         last_name=Name(value='คนสุขภาพดี'),
#         phone_number=PhoneNumber(value='0123456789'),
#         date_of_birth=DateOfBirth(year=1990, month=12, day=31),
#         registered_address=registered_address,
#         current_address=current_address,
#         rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
#     )
#     with raises(DuplicateNationalIDError) as error:
#         registrar.register_new_patient(
#             national_id=common_id,
#             first_name=Name(value='นนทพัฒน์'),
#             last_name=Name(value='คนสุขภาพดี'),
#             phone_number=PhoneNumber(value='0123456789'),
#             date_of_birth=DateOfBirth(year=1990, month=12, day=31),
#             registered_address=registered_address,
#             current_address=current_address,
#             rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)        )
#     assert 'เลขบัตรประชาชนนี้มีในระบบแล้ว' in str(error.value)


def test_registrar_patient_should_handle_when_duplicate_national_id(registrar, registered_address,
                                                                         current_address,vital_signs):
    common_id = NationalID(id='1234567890123')
    new_patient = registrar.register_new_patient(
        national_id=common_id,
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    )
    duplicate_patient = registrar.register_new_patient(
        national_id=common_id,
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    )

    assert new_patient.id == duplicate_patient.id
    assert new_patient.national_id.id == duplicate_patient.national_id.id
    assert new_patient.first_name.value == 'นนทพัฒน์'
    assert duplicate_patient.first_name.value == 'นนทพัฒน์'


def test_patient_registrar_should_raise_error_when_national_id_invalid(registrar, registered_address, current_address, vital_signs):
    with raises(ValidationError) as error:
        registrar.register_new_patient(
            national_id=NationalID(id='132456'),
            first_name=Name(value='นนทพัฒน์'),
            last_name=Name(value='คนสุขภาพดี'),
            phone_number=PhoneNumber(value='0123456789'),
            date_of_birth=DateOfBirth(year=1990, month=12, day=31),
            registered_address=registered_address,
            current_address=current_address,
            rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
        )
    assert '132456' in str(error.value)


def test_patient_registrar_should_handle_repository_failure(registered_address, current_address, queue_service, vital_signs):
    broken_repo = BrokenPatientRecord()
    unlucky_registrar = PatientRegistrar(patient_repo=broken_repo)

    with raises(RuntimeError) as excinfo:
        unlucky_registrar.register_new_patient(
            national_id=NationalID(id='1100110011001'),
            first_name=Name(value='สมชาย'),
            last_name=Name(value='โชคร้าย'),
            phone_number=PhoneNumber(value='0811111111'),
            date_of_birth=DateOfBirth(year=1980, month=1, day=1),
            registered_address=registered_address,
            current_address=current_address,
            rights=Rights(rights_type=PatientRights.GOLD_CARD)        )

    assert "Database พัง save ไม่ได้" in str(excinfo.value)


def test_patient_registrar_should_update_patient_info_through_repository(registered_address, current_address, registrar, patient_repo, vital_signs):
    new_patient = registrar.register_new_patient(
        national_id=NationalID(id='1234567890123'),
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)    )
    new_phone = PhoneNumber(value='099-999-9999')
    new_patient.update_phone_number(new_phone)

    registrar.update_patient_info(new_patient)

    updated_in_repo = patient_repo.get_by_national_id(new_patient.national_id)
    assert updated_in_repo.phone_number == new_phone
    assert updated_in_repo.version.number == 2

def test_patient_registrar_should_increment_version_when_update_patient_info(
        registered_address, current_address, registrar, patient_repo, vital_signs
):
    new_patient = registrar.register_new_patient(
        national_id=NationalID(id='1234567890123'),
        first_name=Name(value='นนทพัฒน์'),
        last_name=Name(value='คนสุขภาพดี'),
        phone_number=PhoneNumber(value='0123456789'),
        date_of_birth=DateOfBirth(year=1990, month=12, day=31),
        registered_address=registered_address,
        current_address=current_address,
        rights=Rights(rights_type=PatientRights.SOCIAL_SECURITY)
    )
    new_phone = PhoneNumber(value='099-999-9999')
    new_patient.update_phone_number(new_phone)
    registrar.update_patient_info(new_patient)
    updated_in_repo = patient_repo.get_by_national_id(new_patient.national_id)
    assert updated_in_repo.phone_number == new_phone
    assert updated_in_repo.version.number == 2

    new_right = Rights(rights_type=PatientRights.COMPANY_INSURANCE)
    new_patient.update_rights(new_right)
    registrar.update_patient_info(new_patient)
    updated_in_repo = patient_repo.get_by_national_id(new_patient.national_id)
    assert updated_in_repo.rights == new_right
    assert updated_in_repo.version.number == 3