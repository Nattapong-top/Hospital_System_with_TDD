import os
import sys
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.routers import patient, staff, queues
from domain.custom_error import (
    DomainError,
    InvalidCancelRequestError,
    InvalidStatusTransitionError,
    MissingDiagnosisError,
    QueueNotFoundError,
)

# ฝัง GPS ให้ Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.hospital_registry import HospitalRegistry
from domain.value_object import (
    Diagnosis,
    MedicineInfo,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: เปิดโรงพยาบาล ---
    HospitalRegistry.init_database()
    print("🏥 ระบบฐานข้อมูลและศูนย์บัญชาการพร้อมให้บริการ!")
    yield
    # --- Shutdown: ปิดโรงพยาบาล ---
    print("🔒 ปิดระบบเรียบร้อย พักผ่อนครับป๋า!")


app = FastAPI(title="Hospital Queue API - Paa Top IT", lifespan=lifespan)
app.include_router(staff.router)
app.include_router(patient.patient_router)
app.include_router(queues.queues_router)


# =====================================================================
# 🔮 วุ้นแปลภาษาครอบจักรวาล (Global Exception Handler)
# =====================================================================
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """
    เมื่อไหร่ที่ Service พ่น Error อะไรก็ตามที่สืบทอดมาจาก DomainError
    ให้ตอบกลับเป็น 400 Bad Request พร้อมข้อความที่ป๋าตั้งไว้!
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.message
        },  # ดึงข้อความภาษาไทยสวยๆ จาก custom_error.py มาโชว์เลย!
    )


@app.get("/")
def health_check():
    return {"message": "API Online ปลอดภัยดีครับป๋า", "status": "Ready"}


@app.post("/api/consultations/{queue_id}/start")
def start_consultation(queue_id: UUID) -> dict:
    try:
        queue_service = HospitalRegistry.queue_service()
        updated_queue = queue_service.start_consultation(queue_id)

        return {
            "message": "เริ่มการตรวจสำเร็จ",
            "queue_id": str(updated_queue.id),
            "status": updated_queue.status.value,
        }
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QueueNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดภายในระบบ {str(e)}")


@app.post("/api/consultations/{queue_id}/complete")
def complete_visit(queue_id: UUID, diagnosis_payload: dict):
    try:
        queue_service = HospitalRegistry.queue_service()
        # 🚩 ถ้าข้างล่างนี้พ่น MissingDiagnosisError มันจะวิ่งไปหา except 400 ทันที
        diagnosis_vo = _prepare_diagnostic_vo(diagnosis_payload)
        updated_queue = queue_service.complete_visit(queue_id, diagnosis_vo)

        return {
            "message": "บันทึกผลการตรวจเรียบร้อย",
            "queue_id": str(updated_queue.id),
            "status": updated_queue.status.value,
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


@app.post("/api/consultations/{queue_id}/cancel")
def cancel_visit(queue_id: UUID):
    try:
        queue_service = HospitalRegistry.queue_service()
        queue_cancel = queue_service.cancel_visit(queue_id)

        return {
            "message": "ยกเลิกคิวเรียบร้อย",
            "queue_id": str(queue_id),
            "queue_number": str(queue_cancel.queue_number.id),
            "status": queue_cancel.status.value,
        }
    except (
        InvalidStatusTransitionError,
        MissingDiagnosisError,
        InvalidCancelRequestError,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QueueNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # ⚠️ ตัวนี้จะดักเฉพาะเรื่องที่เราคาดไม่ถึงจริงๆ (เช่น DB ล่ม)
        print(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail="ระบบขัดข้องชั่วคราว")


def _prepare_diagnostic_vo(diagnosis_payload: dict) -> Diagnosis:
    # 🚩 เช็คเบื้องต้นก่อนส่งให้ Pydantic
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
        # พ่นเป็น Domain Error ออกไปแทน
        raise MissingDiagnosisError(f"ข้อมูลวินิจฉัยไม่ถูกต้อง: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
