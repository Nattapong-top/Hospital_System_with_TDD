from pydantic import ValidationError
from domain.custom_error import MissingDiagnosisError
from domain.domain_service.patient_registrar import PatientRegistrar
from domain.entities import Patient
from domain.value_object import (
    Address,
    NationalID,
    Name,
    PhoneNumber,
    DateOfBirth,
    Rights,
    VitalSigns,
    BloodPressure,
    Weight,
    Height,
    Temperature,
    Diagnosis,
    MedicineInfo,
)
from api.schema import (
    DiagnosisSchema,
    AddressSchema,
    RegisterRequest,
    TriageRequest,
    VitalSignsSchema,
)


def to_diagnosis_vo(diagnosis: DiagnosisSchema) -> Diagnosis:
    """แปลงข้อมูลคำวินิจฉัยจาก API Schema ไปเป็น Domain Value Object"""
    medicines_vo = [
        MedicineInfo(name=m.name, strength=m.strength, frequency=m.frequency)
        for m in diagnosis.medicine_prescribed
    ]
    return Diagnosis(
        disease=diagnosis.disease,
        treatment=diagnosis.treatment,
        medicine_prescribed=medicines_vo,
    )


def to_address_vo(addr_schema: AddressSchema) -> Address:
    """แปลงข้อมูลที่อยู่จาก API Schema ไปเป็น Domain Value Object"""
    return Address(
        house_number=addr_schema.house_number,
        street=addr_schema.street,
        sub_district=addr_schema.sub_district,
        district=addr_schema.district,
        province=addr_schema.province,
        postal_code=addr_schema.postal_code,
    )


def registrar_patient_detail(
    current_addr: Address,
    registered_addr: Address,
    registrar: PatientRegistrar,
    request: RegisterRequest,
) -> Patient:
    """ประสานงานเพื่อแปลง Request Schema และบันทึกข้อมูลคนไข้ใหม่เข้า Domain Service"""
    return registrar.register_new_patient(
        national_id=NationalID(id=request.national_id),
        first_name=Name(value=request.first_name),
        last_name=Name(value=request.last_name),
        phone_number=PhoneNumber(value=request.phone_number),
        date_of_birth=DateOfBirth(
            year=request.dob_year, month=request.dob_month, day=request.dob_day
        ),
        registered_address=registered_addr,
        current_address=current_addr,
        rights=Rights(rights_type=request.rights_type),
    )


def _to_vital_signs_vo(request: TriageRequest) -> VitalSigns:
    """แปลงสัญญาณชีพจาก Triage Request เป็น Domain Value Object"""
    return VitalSigns(
        blood_pressure=BloodPressure(
            systolic=request.vitals.systolic, diastolic=request.vitals.diastolic
        ),
        weight=Weight(value=request.vitals.weight),
        height=Height(value=request.vitals.height),
        temperature=Temperature(value=request.vitals.temperature),
        symptom=request.vitals.symptom,
    )


def exam_to_vital_signs_vo(vital_signs: VitalSignsSchema) -> VitalSigns:
    """แปลงสัญญาณชีพจาก VitalSigns Schema เป็น Domain Value Object สำหรับห้องตรวจ"""
    return VitalSigns(
        blood_pressure=BloodPressure(
            systolic=vital_signs.systolic, diastolic=vital_signs.diastolic
        ),
        weight=Weight(value=vital_signs.weight),
        height=Height(value=vital_signs.height),
        temperature=Temperature(value=vital_signs.temperature),
        symptom=vital_signs.symptom,
    )


def _prepare_diagnostic_vo(diagnosis_payload: dict) -> Diagnosis:
    """ดักจับและแปลง Payload คำวินิจฉัยดิบให้กลายเป็น Domain Value Object พร้อมพ่น Domain Error หากไม่ถูกต้อง"""
    if not diagnosis_payload or not diagnosis_payload.get("disease"):
        raise MissingDiagnosisError()
    try:
        meds_data = diagnosis_payload.get("medicine_prescribed", [])
        meds = [MedicineInfo(**m) for m in meds_data]
        return Diagnosis(
            disease=diagnosis_payload.get("disease"),
            treatment=diagnosis_payload.get("treatment"),
            medicine_prescribed=meds,
        )
    except (ValidationError, TypeError, ValueError) as e:
        raise MissingDiagnosisError(f"ข้อมูลวินิจฉัยไม่ถูกต้อง: {str(e)}")
