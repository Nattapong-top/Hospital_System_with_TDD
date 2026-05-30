from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from api.schema import TriageRequest
from api.mapper import _to_vital_signs_vo
from domain.hospital_registry import HospitalRegistry
from infrastructure.auth.jwt_service import get_current_staff

queues_router = APIRouter(
    prefix="/api/queues",
    tags=["Queues"],
    dependencies=[Depends(get_current_staff)],
)


# 🚩 จุดที่ 1: ต้องเอา /today ไว้ข้างบน {queue_id} เสมอ!
@queues_router.get("/today")
def get_all_queues_today() -> list:
    """เมนูสำหรับพยาบาล: ดูรายชื่อคิวทุกคนของวันนี้"""
    qs = HospitalRegistry.queue_service()

    queues = qs.get_all_queues_today(date.today())

    return [
        {
            "queue_id": str(q.id),
            "queue_number": str(q.queue_number.id),
            "status": q.status.value,
            "patient_id": str(q.patient_id),
            # isoformat(): คือการแปลงจาก Object(วันที่) -> String(ตัวหนังสือ)...(ใช้ตอนจะเอาข้อมูลไปโชว์)
            "queue_date": str(q.queue_date.isoformat()),
        }
        for q in queues
    ]


@queues_router.get("/{queue_id}")
def get_queue_status(queue_id: UUID) -> dict:
    qs = HospitalRegistry.queue_service()
    queue = qs.get_by_queue_id(queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="ไม่พบใบคิวนี้ในระบบ")

    return {
        "queue_id": str(queue.id),
        "status": queue.status.value,
        "queue_number": queue.queue_number.id,
    }


@queues_router.post("/triage")
def record_triage(request: TriageRequest) -> dict:
    if request.vitals is None:
        raise HTTPException(
            status_code=400, detail="ลืมส่งสัญญาณชีพมานะ ออกคิวไม่ได้ครับ"
        )

    # 1. เรียกใช้ Service (สมมติป๋ามี QueueService ใน Registry แล้ว)
    queue_service = HospitalRegistry.queue_service()

    # 2. แปลงข้อมูลจาก Schema เป็น Value Objects (VO)
    # 💡 นี่คือจุดที่ป๋าเอา "ความรู้ DDD" มาใช้ป้องกันข้อมูลเน่าเข้าสู่ระบบ
    vitals = _to_vital_signs_vo(request)

    # 3. สั่งออกคิวจริง
    new_queue = queue_service.issue_new_queue(
        patient_id=request.patient_id, today=date.today(), vital_signs=vitals
    )

    return {
        "message": "ซักประวัติสำเร็จ และออกคิวเรียบร้อย",
        "queue_id": str(new_queue.id),
        "patient_id": str(new_queue.patient_id),
        "queue_date": str(new_queue.queue_date.isoformat()),
        "queue_number": str(new_queue.queue_number.id),
        "status": str(new_queue.status.value),
    }
