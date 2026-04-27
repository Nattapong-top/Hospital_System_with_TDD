# Unit Tests for Hospital_System
from datetime import date
from decimal import Decimal
from pydantic import ValidationError
from pytest import raises, fixture

from domain.value_object import (
    Name, PhoneNumber, DateOfBirth, Address, Province, PatientRights, Rights,
    BloodPressure, Weight, Height, Temperature, VitalSigns,
    Diagnosis, MedicineInfo, Payment, PaymentType, NationalID, LicenseNumber,
    Specialization, MedicalSpecialty, Version, Username, HashedPassword)


# ส่วนของ VO Name เทสชื่อและนามสกุล
def test_should_create_Name_is_valid():
    first_name = Name(value='นนทพัฒน์')
    last_name = Name(value='คนสุขภาพดี')

    assert first_name.value == 'นนทพัฒน์'
    assert last_name.value == 'คนสุขภาพดี'


def test_should_raise_error_Name_is_too_long():
    with raises(ValueError):
        Name(value='นนทพัฒน์' * 20)


def test_should_raise_error_Name_is_emtpy():
    with raises(ValueError):
        Name(value='')


def test_should_raise_error_Name_is_number():
    with raises(ValueError):
        Name(value='123456789')


def test_should_raise_error_Name_is_whitespace():
    with raises(ValueError):
        Name(value='       ')


def test_should_raise_error_Name_is_str_and_number():
    with raises(ValueError):
        Name(value='ชื่อภาษาไทยบวกตัวเลข1')


# ส่วนของ VO PhoneNumber เทสเบอร์โทรศัพท์
def test_should_create_PhoneNumber_is_valid():
    phone = PhoneNumber(value='0123456789')
    assert phone.value == '0123456789'


def test_should_raise_error_PhoneNumber_is_too_long():
    with raises(ValueError):
        PhoneNumber(value='05456123456789')


def test_should_raise_error_PhoneNumber_is_emtpy():
    with raises(ValueError):
        PhoneNumber(value='')


def test_should_raise_error_PhoneNumber_is_whitespace():
    with raises(ValueError):
        PhoneNumber(value='   ')


def test_should_raise_error_PhoneNumber_is_str_and_number():
    with raises(ValueError):
        PhoneNumber(value='0234567dfg')


def test_should_create_PhoneNumber_is_Hyphen_and_number():
    phone = PhoneNumber(value='012-345-6789')
    assert phone.value == '0123456789'


def test_should_raise_PhoneNumber_start_Not_zero():
    with raises(ValueError):
        PhoneNumber(value='9123456789')


# ส่วนของ VO Age เทสอายุ
def test_should_create_DateOfBirth_is_valid():
    dob = DateOfBirth(year=1990, month=12, day=31)
    assert dob.year == 1990
    assert dob.month == 12
    assert dob.day == 31


def test_should_raise_error_DateOfBirth_month_out_of_range():
    with raises(ValueError):
        DateOfBirth(year=1990, month=13, day=31)


def test_should_raise_error_DateOfBirth_day_out_of_range():
    with raises(ValueError):
        DateOfBirth(year=1990, month=12, day=32)


def test_should_raise_error_DateOfBirth_is_future_dae():
    with raises(ValueError):
        DateOfBirth(year=2026, month=12, day=31)


def test_should_raise_error_DateOfBirth_is_Over_150_years():
    today = date.today()
    with raises(ValueError):
        DateOfBirth(year=today.year - 151, month=12, day=31)


def test_should_create_DateOfBirth_is_today():
    today = date.today()
    dob = DateOfBirth(year=today.year, month=today.month, day=today.day)
    assert dob.year == today.year
    assert dob.month == today.month
    assert dob.day == today.day


# ส่วนของ VO Address เทสที่อยู่
def test_should_create_registered_Address_is_valid():
    registered_address = Address(
        house_number='10',
        street='วิวิธสุรการ',
        sub_district='มุกดาหาร',
        district='เมือง',
        province=Province.MUKDAHAN,
        postal_code='49000'
    )  # เลขที่ 10 ถนนวิวิธสุรการ ต.มุกดาหาร อ.เมือง จ.มุกดาหาร 49000

    assert registered_address.house_number == '10'
    assert registered_address.street == 'วิวิธสุรการ'
    assert registered_address.sub_district == 'มุกดาหาร'
    assert registered_address.district == 'เมือง'
    assert registered_address.province == Province.MUKDAHAN
    assert registered_address.postal_code == '49000'


def test_should_create_current_Address_is_valid():
    current_address = Address(  # ตั้งอยู่ที่ 173 ถนนดินสอ แขวงเสาชิงช้า เขตพระนคร กรุงเทพมหานคร 10200
        house_number='173',
        street='ดินสอ',
        sub_district='เสาชิงช้า',
        district='พระนคร',
        province=Province.BANGKOK,
        postal_code='10200'
    )
    assert current_address.house_number == '173'
    assert current_address.street == 'ดินสอ'
    assert current_address.sub_district == 'เสาชิงช้า'
    assert current_address.district == 'พระนคร'
    assert current_address.province == Province.BANGKOK
    assert current_address.postal_code == '10200'


def test_should_raise_error_when_province_is_invalid_NotInEnum():
    with raises(ValueError):
        Address(
            house_number='10',
            street='วิวิธสุรการ',
            sub_district='มุกดาหาร',
            district='เมือง',
            province='มุกดา',
            postal_code='49000'
        )


def test_should_raise_error_when_postal_code_is_invalid_str_over_5():
    with raises(ValueError):
        registered_address = Address(
            house_number='10',
            street='วิวิธสุรการ',
            sub_district='มุกดาหาร',
            district='เมือง',
            province=Province.MUKDAHAN,
            postal_code='49000dfg'
        )


def test_should_create_Address_when_without_street_is_valid():
    address = Address(
        house_number='10',
        street=None,
        sub_district='มกดาหาร',
        district='เมือง',
        province=Province.MUKDAHAN,
        postal_code='49000'
    )
    assert address.street is None


def test_should_create_PatientRights_is_valid():
    rights = PatientRights.GOLD_CARD
    assert rights == PatientRights.GOLD_CARD


def test_should_raise_error_when_PatientRights_is_invalid_NotInEnum():
    with raises(ValueError):
        PatientRights('บัตรหมดอายุ')


def test_should_create_Rights_is_valid():
    rights = Rights(rights_type=PatientRights.COMPANY_INSURANCE)
    assert rights.rights_type == PatientRights.COMPANY_INSURANCE


def test_should_raise_error_when_PatientRights_type_is_invalid_NotInEnum():
    with raises(ValueError):
        Rights(rights_type='บัตรดำ')


# ส่วนของ VO BloodPressure เทสวัดชีพจร
def test_should_create_BloodPressure_is_valid():
    blood_pressure = BloodPressure(systolic=120, diastolic=80)
    assert blood_pressure == BloodPressure(systolic=120, diastolic=80)


def test_should_raise_error_when_BloodPressure_systolic_over_of_range():
    with raises(ValueError):
        BloodPressure(systolic=200, diastolic=80)


def test_should_raise_error_when_BloodPressure_systolic_lower_of_range():
    with raises(ValueError):
        BloodPressure(systolic=120, diastolic=8)


def test_should_raise_error_when_BloodPressure_diastolic_over_range():
    with raises(ValueError):
        BloodPressure(systolic=120, diastolic=91)


def test_should_raise_error_when_BloodPressure_diastolic_lower_of_range():
    with raises(ValueError):
        BloodPressure(systolic=120, diastolic=9)


# ส่วนของ VO Weight เทสน้ำหนัก
def test_should_create_Weight_is_valid():
    weight = Weight(value=80)
    assert weight == Weight(value=80)


def test_should_raise_error_when_Weight_over_of_range():
    with raises(ValueError):
        Weight(value=301)


def test_should_raise_error_when_Weight_lower_of_range():
    with raises(ValueError):
        Weight(value=0.1)


def test_should_raise_error_when_Weight_input_str():
    with raises(ValueError):
        Weight(value='สิบ')


def test_should_raise_error_when_Weight_is_negative():
    with raises(ValueError):
        Weight(value=-1)


# ส่วนของ VO Height เทสส่วนสูง
def test_should_create_Height_is_valid():
    height = Height(value=80)
    assert height == Height(value=80)


def test_should_raise_error_when_Height_over_of_range():
    with raises(ValueError):
        Height(value=301)


def test_should_raise_error_when_Height_lower_of_range():
    with raises(ValueError):
        Height(value=0.1)


def test_should_raise_error_when_Height_input_str():
    with raises(ValueError):
        Height(value='สิบ')


def test_should_raise_error_when_Height_is_negative():
    with raises(ValueError):
        Height(value=-1)


# ส่วนของ VO Temperature เทสอุณหภูมิร่างกาย
def test_should_create_Temperature_is_valid():
    temp = Temperature(value=35.0)
    assert temp == Temperature(value=35)


def test_should_raise_error_when_Temperature_over_of_range():
    with raises(ValueError):
        Temperature(value=301)


def test_should_raise_error_when_Temperature_lower_of_range():
    with raises(ValueError):
        Temperature(value=0.1)


def test_should_raise_error_when_Temperature_input_str():
    with raises(ValueError):
        Temperature(value='สิบ')


def test_should_raise_error_when_Temperature_is_negative():
    with raises(ValueError):
        Temperature(value=-1)


def test_should_create_VitalSigns_is_valid(vital_signs):
    assert vital_signs == VitalSigns(
        blood_pressure=BloodPressure(systolic=120, diastolic=80),
        weight=Weight(value=80),
        height=Height(value=177),
        temperature=Temperature(value=39.0),
        symptom='น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น'
    )


def test_should_raise_error_when_VitalSigns_symptom_empty_and_whitespace():
    with raises(ValueError):
        VitalSigns(
            blood_pressure=BloodPressure(systolic=120, diastolic=80),
            weight=Weight(value=80),
            height=Height(value=177),
            temperature=Temperature(value=39.0),
            symptom='      '
        )


def test_should_raise_error_when_VitalSigns_symptom_too_long():
    with raises(ValueError):
        VitalSigns(
            blood_pressure=BloodPressure(systolic=120, diastolic=80),
            weight=Weight(value=80),
            height=Height(value=177),
            temperature=Temperature(value=39.0),
            symptom='น้ำหมูกไหล ปวดหัว ตัวร้อน หนาวสั่น' * 20
        )


def test_create_Diagnosis_is_valid(diagnosis):
    assert diagnosis == Diagnosis(
        disease='ไข้หวัดใหญ่',
        treatment='พักผ่อนน ดิ่มน้ำมากๆ',
        medicine_prescribed=[MedicineInfo(
            name='Paracetamol',
            strength='500mg',
            frequency='วันละ 3 ครั้ง หลักอาหาร'
        )]
    )


def test_should_raise_error_when_Diagnosis_empty_and_whitespace():
    with raises(ValueError):
        Diagnosis(
            disease='   ',
            treatment='   ',
            medicine_prescribed=[]
        )


def test_should_create_Diagnosis_without_medicine_prescribed():
    diagnosis = Diagnosis(
        disease='เครียดสะสม',
        treatment='พักผ่อน ออกกำลังกาย',
        medicine_prescribed=[]  #ไม่มียา
    )
    assert diagnosis == Diagnosis(
        disease='เครียดสะสม',
        treatment='พักผ่อน ออกกำลังกาย',
        medicine_prescribed=[]  # ไม่มียา
    )


def test_should_raise_error_when_Diagnosis_max_length():
    with raises(ValueError):
        Diagnosis(
            disease='เครียดสะสม' * 30,
            treatment='พักผ่อน ออกกำลังกาย' * 30,
            medicine_prescribed=[]  # ไม่มียา
        )


# ส่วนของ VO MedicineInfo เทสข้อมูลยา
def test_should_create_MedicineInfo_is_valid():
    medicine = MedicineInfo(
        name='Paracetamol',
        strength='500mg',
        frequency='วันละ 3 ครั้ง หลักอาหาร'
    )
    assert medicine == MedicineInfo(
        name='Paracetamol',
        strength='500mg',
        frequency='วันละ 3 ครั้ง หลักอาหาร'
    )


def test_should_raise_error_when_MedicineInfo_empty_and_whitespace():
    with raises(ValueError):
        MedicineInfo(
            name='    ',
            strength='    ',
            frequency='    ',
        )


def test_should_raise_error_when_MedicineInfo_too_long():
    with raises(ValueError):
        MedicineInfo(
            name='Paracetamol' * 100,
            strength='500mg',
            frequency='วันละ 3 ครั้ง',
        )


# ส่วนของ VO Payment เทสการจ่ายเงิน
def test_should_Payment_is_valid():
    payment = Payment(amount=Decimal('500.11'), payment_type=PaymentType.SOCIAL_SECURITY)
    result = payment.amount / payment.amount
    assert payment == Payment(amount=Decimal('500.11'), payment_type=PaymentType.SOCIAL_SECURITY)
    assert result == Decimal('1')


def test_should_raise_error_when_Payment_is_negative():
    with raises(ValueError):
        Payment(amount=Decimal('-0.1'), payment_type=PaymentType.SOCIAL_SECURITY)


def test_should_raise_error_when_Payment_is_zero():
    with raises(ValueError):
        Payment(amount=Decimal('0.0'), payment_type=PaymentType.SOCIAL_SECURITY)


def test_should_raise_error_when_Payment_is_over_limit_10_000_000():
    with raises(ValueError):
        Payment(amount=Decimal('10000000.01'), payment_type=PaymentType.SOCIAL_SECURITY)


def test_create_Payment_with_cash_is_valid():
    payment = Payment(amount=Decimal('1000.00'), payment_type=PaymentType.CASH)
    assert payment.payment_type == PaymentType.CASH


def test_create_Payment_with_QR_PAYMANT_is_valid():
    payment = Payment(amount=Decimal('100.00'), payment_type=PaymentType.QR_PAYMENT)
    assert payment.payment_type == PaymentType.QR_PAYMENT


def test_create_NationalID_is_valid():
    national_id = NationalID(id='1234567890123')
    assert national_id == NationalID(id='1234567890123')


def test_should_raise_error_when_NationalID_empty_and_whitespace():
    with raises(ValueError):
        NationalID(id='             ')


def test_should_raise_error_when_NationalID_too_long():
    with raises(ValueError):
        NationalID(id='12345678901231')


def test_should_raise_error_when_NationalID_too_short():
    with raises(ValueError):
        NationalID(id='123456789012')


def test_should_raise_error_when_NationalID_is_str():
    with raises(ValueError):
        NationalID(id='123456789012O')


def test_should_raise_error_when_NationalID_is_negative():
    with raises(ValueError):
        NationalID(id='-234567890124')


def test_should_create_LicenseNumber_doctor_is_valid():
    license_number = LicenseNumber(id='ว.12345')
    assert license_number == LicenseNumber(id='ว.12345')


def test_should_raise_error_when_LicenseNumber_too_long():
    with raises(ValueError):
        LicenseNumber(id='ว.123456')


def test_should_raise_error_when_LicenseNumber_too_short():
    with raises(ValueError):
        LicenseNumber(id='.123456')


def test_should_raise_error_when_LicenseNumber_is_str():
    with raises(ValueError):
        LicenseNumber(id='ว.1234X')


def test_should_create_MedicalSpecialty_in_Enum_is_valid():
    spacial = MedicalSpecialty(value=Specialization.INTERNAL_MEDICINE)
    assert spacial == MedicalSpecialty(value=Specialization.INTERNAL_MEDICINE)


def test_should_raises_error_when_MedicalSpecialty_is_invalid():
    with raises(ValueError):
        MedicalSpecialty(value='test')


def test_Version_should_create_version_is_valid():
    version = Version(number=1)
    assert version == Version(number=1)


def test_Version_should_raises_error_when_invalid_type():
    with raises(ValidationError):
        Version(number='A')


def test_Version_should_raises_error_when_number_zero():
    with raises(ValidationError) as excinfo:
        Version(number=0)

    assert excinfo.type == ValidationError


def test_Version_should_raises_error_when_number_negative():
    with raises(ValidationError) as excinfo:
        Version(number=-10)
    assert excinfo.type == ValidationError


def test_Version_should_create_increment_next_version_is_valid():
    current_version = Version(number=1)
    assert current_version == Version(number=1)
    next_version = current_version.increment()
    assert next_version == Version(number=2)


def test_Username_should_create_username_is_valid():
    username = Username(id='natta_pong-top')
    assert username.id == 'natta_pong-top'

def test_Username_should_raise_error_when_username_too_long():
    with raises(ValueError):
        Username(id='natta_pong-top'*20)

def test_Username_should_raise_error_when_username_too_short():
    with raises(ValueError):
        Username(id='natt')

def test_Username_should_raise_error_when_username_is_str_th():
    with raises(ValueError):
        Username(id='ณัฐ_พงศ์-ท๊อป')


def test_hashed_password_vo_should_store_value_and_equal():
    # 1. ทดสอบว่าเก็บค่าได้ และเปรียบเทียบกันได้ (Equality)
    hash_string = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31yy"
    hp1 = HashedPassword(value=hash_string)
    hp2 = HashedPassword(value=hash_string)

    assert hp1.value == hash_string
    assert hp1 == hp2  # Value Object ต้องเทียบกันที่ "ค่า" ไม่ใช่ "ตำแหน่งเมมโมรี่"


def test_hashed_password_full_flow():
    # 1. ป๋าปั่นรหัสจริง "paa1234"
    plain_pass = "paa1234"
    hp = HashedPassword.create(plain_pass)

    # 2. ตรวจสอบเบื้องต้น
    assert hp.value != plain_pass
    assert len(hp.value) > 20

    # 3. ทดสอบการ Verify
    # ✅ ต้องส่งรหัสจริง (plain_pass) เข้าไปเช็ค
    assert hp.verify(plain_pass) is True

    # ❌ ห้ามส่ง hp.value เข้าไปใน verify เด็ดขาด เพราะมันยาวเกิน 72 bytes!
    # ถ้าป๋าเขียน hp.verify(hp.value) มันจะระเบิดทันทีครับ
    assert hp.verify("wrongpass") is False


def test_very_long_password_should_pass_now():
    # ทดสอบรหัสยาว 200 ตัว (Bcrypt ปกติจะตาย แต่ระบบป๋าต้องรอด!)
    very_long_pass = "p" * 200
    hp = HashedPassword.create(very_long_pass)
    assert hp.verify(very_long_pass) is True