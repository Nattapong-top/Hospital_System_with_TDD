import os
import sys
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from domain.custom_error import VitalSignsMissingError, InvalidStatusTransitionError, \
    QueueNotFoundError, MissingDiagnosisError, InvalidCancelRequestError
from domain.domain_service.patient_registrar import PatientRegistrar
from domain.entities import Patient

# ฝัง GPS ให้ Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.hospital_registry import HospitalRegistry
from domain.value_object import (
    NationalID, Name, PhoneNumber, DateOfBirth, Address, Province,
    Rights, PatientRights, VitalSigns, BloodPressure, Weight, Height, Temperature, MedicineInfo, Diagnosis
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: เปิดโรงพยาบาล ---
    HospitalRegistry.init_database()
    print("🏥 ระบบฐานข้อมูลและศูนย์บัญชาการพร้อมให้บริการ!")
    yield
    # --- Shutdown: ปิดโรงพยาบาล ---
    print("🔒 ปิดระบบเรียบร้อย พักผ่อนครับป๋า!")


app = FastAPI(
    title="Hospital Queue API - Paa Top IT",
    lifespan=lifespan
)


# --- จุดบริการ (Endpoints) ---
class AddressSchema(BaseModel):
    house_number: str
    street: str
    sub_district: str
    district: str
    province: Province
    postal_code: str


# --- ข้อมูลรับเข้า (Request Schema) ---
class RegisterRequest(BaseModel):
    national_id: str
    first_name: str
    last_name: str
    phone_number: str
    dob_year: int
    dob_month: int
    dob_day: int
    registered_address: AddressSchema
    current_address: AddressSchema
    rights_type: PatientRights


# --- ข้อมูลสัญญาณชีพ (Schema) ---
class VitalSignsSchema(BaseModel):
    systolic: int
    diastolic: int
    weight: float
    height: float
    temperature: float
    symptom: str


# --- ข้อมูลรับเข้าสำหรับการออกคิว ---
class TriageRequest(BaseModel):
    patient_id: UUID  # ต้องส่ง ID ของคนไข้ที่ได้จากตอนลงทะเบียนมาด้วย
    vitals: Optional[VitalSignsSchema] = None


# 1. สร้างฟังก์ชันแปลงโฉม (Mapper)
# ให้มันรับ AddressSchema (ก้อนเล็ก) แล้วคืนค่าเป็น Address VO
def _to_address_vo(addr_schema: AddressSchema) -> Address:
    return Address(
        house_number=addr_schema.house_number,
        street=addr_schema.street,
        sub_district=addr_schema.sub_district,
        district=addr_schema.district,
        province=addr_schema.province,
        postal_code=addr_schema.postal_code
    )


@app.get("/")
def health_check():
    return {"message": "API Online ปลอดภัยดีครับป๋า", "status": "Ready"}


# 🚩 จุดที่ 1: ต้องเอา /today ไว้ข้างบน {queue_id} เสมอ!
@app.get("/api/nurse/queues/today")
def get_all_queues_today() -> list:
    """เมนูสำหรับพยาบาล: ดูรายชื่อคิวทุกคนของวันนี้"""
    qs = HospitalRegistry.queue_service()


    queues = qs.get_all_queues_today(date.today())

    return [{
        'queue_id': str(q.id),
        'queue_number': str(q.queue_number.id),
        'status': q.status.value,
        'patient_id': str(q.patient_id),
        # isoformat(): คือการแปลงจาก Object(วันที่) -> String(ตัวหนังสือ)...(ใช้ตอนจะเอาข้อมูลไปโชว์)
        'queue_date': str(q.queue_date.isoformat()),
    } for q in queues]




@app.get("/api/queues/{queue_id}")
def get_queue_status(queue_id: UUID) -> dict:
    qs = HospitalRegistry.queue_service()
    queue = qs.get_by_queue_id(queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="ไม่พบใบคิวนี้ในระบบ")

    return {
        "queue_id": str(queue.id),
        "status": queue.status.value,
        "queue_number": queue.queue_number.id
    }


@app.post("/api/patients/register")
def register_patient(request: RegisterRequest) -> dict:
    # 🚩 จุดที่ 2: ใช้ Try-Except เพื่อดักจับ Error จาก Domain (เช่น ID ซ้ำ)
    try:
        registrar = HospitalRegistry.patient_registrar()

        # 🚩 แกะที่อยู่ที่ 1: ตามทะเบียนบ้าน
        registered_addr = _to_address_vo(request.registered_address)

        # 🚩 แกะที่อยู่ที่ 2: ที่อยู่ปัจจุบัน
        current_addr = _to_address_vo(request.current_address)

        registered_patient = _registrar_patient_detail(current_addr, registered_addr,
                                                       registrar, request)

        return {
            "message": "ลงทะเบียนสำเร็จ!",
            'id': str(registered_patient.id),
            "national_id": str(registered_patient.national_id.id),
            'first_name': str(registered_patient.first_name.value)
        }

    except ValueError as e:
        # ถ้า National ID ซ้ำ หรือข้อมูลผิดกฎ Domain มันจะเด้งมาที่นี่
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 🚩 แก้บรรทัดนี้ชั่วคราวเพื่อให้เห็นว่ามันด่าอะไร
        print(f"❌ ป๋าครับ มันระเบิดเพราะ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/triage")
def record_triage(request: TriageRequest) -> dict:
    if request.vitals is None:
        raise HTTPException(status_code=400, detail='ลืมส่งสัญญาณชีพมานะ ออกคิวไม่ได้ครับ')
    try:
        # 1. เรียกใช้ Service (สมมติป๋ามี QueueService ใน Registry แล้ว)
        queue_service = HospitalRegistry.queue_service()

        # 2. แปลงข้อมูลจาก Schema เป็น Value Objects (VO)
        # 💡 นี่คือจุดที่ป๋าเอา "ความรู้ DDD" มาใช้ป้องกันข้อมูลเน่าเข้าสู่ระบบ
        vitals = _to_vital_signs_vo(request)

        # 3. สั่งออกคิวจริง
        new_queue = queue_service.issue_new_queue(
            patient_id=request.patient_id,
            today=date.today(),
            vital_signs=vitals
        )

        return {
            "message": "ซักประวัติสำเร็จ และออกคิวเรียบร้อย",
            "queue_id": str(new_queue.id),
            'queue_date': str(new_queue.queue_date.isoformat()),
            "queue_number": str(new_queue.queue_number.id),
            "status": str(new_queue.status.value)
        }

    except VitalSignsMissingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/consultations/{queue_id}/start')
def start_consultation(queue_id: UUID) -> dict:
    try:
        queue_service = HospitalRegistry.queue_service()
        updated_queue = queue_service.start_consultation(queue_id)

        return {
            'message': 'เริ่มการตรวจสำเร็จ',
            'queue_id': str(updated_queue.id),
            'status': updated_queue.status.value
        }
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QueueNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'เกิดข้อผิดพลาดภายในระบบ {str(e)}')


@app.post('/api/consultations/{queue_id}/complete')
def complete_visit(queue_id: UUID, diagnosis_payload: dict):
    try:
        queue_service = HospitalRegistry.queue_service()
        # 🚩 ถ้าข้างล่างนี้พ่น MissingDiagnosisError มันจะวิ่งไปหา except 400 ทันที
        diagnosis_vo = _prepare_diagnostic_vo(diagnosis_payload)
        updated_queue = queue_service.complete_visit(queue_id, diagnosis_vo)

        return {
            "message": "บันทึกผลการตรวจเรียบร้อย",
            "queue_id": str(updated_queue.id),
            "status": updated_queue.status.value
        }
    except (InvalidStatusTransitionError, MissingDiagnosisError) as e:
        # ✅ ตัวนี้จะดักได้ทั้งจาก Helper และจาก Service เลยครับ
        raise HTTPException(status_code=400, detail=str(e))
    except QueueNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # ⚠️ ตัวนี้จะดักเฉพาะเรื่องที่เราคาดไม่ถึงจริงๆ (เช่น DB ล่ม)
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail="ระบบขัดข้องชั่วคราว")


@app.post('/api/consultations/{queue_id}/cancel')
def cancel_visit(queue_id: UUID):
    try:
        queue_service = HospitalRegistry.queue_service()
        queue_cancel = queue_service.cancel_visit(queue_id)

        return {
            'message': 'ยกเลิกคิวเรียบร้อย',
            'queue_id': str(queue_id),
            'queue_number': str(queue_cancel.queue_number.id),
            'status': queue_cancel.status.value
        }
    except (InvalidStatusTransitionError, MissingDiagnosisError, InvalidCancelRequestError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QueueNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # ⚠️ ตัวนี้จะดักเฉพาะเรื่องที่เราคาดไม่ถึงจริงๆ (เช่น DB ล่ม)
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail="ระบบขัดข้องชั่วคราว")




def _to_vital_signs_vo(request: TriageRequest) -> VitalSigns:
    vitals = VitalSigns(
        blood_pressure=BloodPressure(
            systolic=request.vitals.systolic,
            diastolic=request.vitals.diastolic
        ),
        weight=Weight(value=request.vitals.weight),
        height=Height(value=request.vitals.height),
        temperature=Temperature(value=request.vitals.temperature),
        symptom=request.vitals.symptom
    )
    return vitals


def _registrar_patient_detail(current_addr: Address, registered_addr: Address, registrar: PatientRegistrar,
                              request: RegisterRequest) -> Patient:
    registered_patient = registrar.register_new_patient(
        national_id=NationalID(id=request.national_id),
        first_name=Name(value=request.first_name),
        last_name=Name(value=request.last_name),
        phone_number=PhoneNumber(value=request.phone_number),
        date_of_birth=DateOfBirth(year=request.dob_year, month=request.dob_month, day=request.dob_day),
        registered_address=registered_addr,
        current_address=current_addr,
        rights=Rights(rights_type=request.rights_type)
    )
    return registered_patient


def _prepare_diagnostic_vo(diagnosis_payload: dict) -> Diagnosis:
    # 🚩 เช็คเบื้องต้นก่อนส่งให้ Pydantic
    if not diagnosis_payload or not diagnosis_payload.get('disease'):
        raise MissingDiagnosisError()

    try:
        meds_data = diagnosis_payload.get('medicine_prescribed', [])
        meds = [MedicineInfo(**m) for m in meds_data]

        return Diagnosis(
            disease=diagnosis_payload.get('disease'),
            treatment=diagnosis_payload.get('treatment'),
            medicine_prescribed=meds,
        )
    except (ValidationError, TypeError, ValueError) as e:
        # พ่นเป็น Domain Error ออกไปแทน
        raise MissingDiagnosisError(f"ข้อมูลวินิจฉัยไม่ถูกต้อง: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
