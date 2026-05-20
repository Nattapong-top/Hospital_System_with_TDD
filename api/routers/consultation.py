from uuid import UUID

from fastapi import APIRouter, HTTPException

from domain.custom_error import (
    InvalidStatusTransitionError,
    QueueNotFoundError,
    MissingDiagnosisError,
    InvalidCancelRequestError,
)
from domain.hospital_registry import HospitalRegistry

consultation_router = APIRouter(prefix="/api/consultations", tags=["consultation"])


@consultation_router.post("/{queue_id}/start")
def start_consultation(queue_id: UUID) -> dict:
    try:
        queue_service = HospitalRegistry.queue_service()
        updated_queue = queue_service.change_status_to_examining(queue_id)

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


@consultation_router.post("/{queue_id}/complete")
def complete_visit(queue_id: UUID):
    try:
        queue_service = HospitalRegistry.queue_service()
        # 🚩 ถ้าข้างล่างนี้พ่น MissingDiagnosisError มันจะวิ่งไปหา except 400 ทันที
        # diagnosis_vo = _prepare_diagnostic_vo(diagnosis_payload)
        updated_queue = queue_service.change_status_complete(queue_id)

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


@consultation_router.post("/{queue_id}/cancel")
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
