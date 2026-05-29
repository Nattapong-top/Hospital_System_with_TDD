from fastapi import APIRouter, HTTPException

from api.schema import RegisterRequest
from api.mapper import to_address_vo, registrar_patient_detail
from domain.hospital_registry import HospitalRegistry

patient_router = APIRouter(prefix="/api/patients", tags=["Patients"])


@patient_router.post("/register")
def register_patient(request: RegisterRequest) -> dict:
    # 🚩 จุดที่ 2: ใช้ Try-Except เพื่อดักจับ Error จาก Domain (เช่น ID ซ้ำ)
    try:
        registrar = HospitalRegistry.patient_registrar()

        # 🚩 แกะที่อยู่ที่ 1: ตามทะเบียนบ้าน
        registered_addr = to_address_vo(request.registered_address)

        # 🚩 แกะที่อยู่ที่ 2: ที่อยู่ปัจจุบัน
        current_addr = to_address_vo(request.current_address)

        registered_patient = registrar_patient_detail(
            current_addr, registered_addr, registrar, request
        )

        return {
            "message": "ลงทะเบียนสำเร็จ!",
            "id": str(registered_patient.id),
            "national_id": str(registered_patient.national_id.id),
            "first_name": str(registered_patient.first_name.value),
        }

    except ValueError as e:
        # ถ้า National ID ซ้ำ หรือข้อมูลผิดกฎ Domain มันจะเด้งมาที่นี่
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 🚩 แก้บรรทัดนี้ชั่วคราวเพื่อให้เห็นว่ามันด่าอะไร
        print(f"❌ ป๋าครับ มันระเบิดเพราะ: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
