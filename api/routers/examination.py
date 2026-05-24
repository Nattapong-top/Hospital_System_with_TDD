from fastapi import APIRouter
import logging


from api.schema import (
    ExamRequestSchema,
    ExamResponseSchema,
)
from domain.hospital_registry import HospitalRegistry

examination_router = APIRouter(prefix="/api/examination", tags=["examination"])
logger = logging.getLogger(__name__)


@examination_router.post("/start")
def start_examination(exam_request: ExamRequestSchema) -> ExamResponseSchema:
    # 📸 จุดที่ 1: ติดกล้องดักฟังตอนของเพิ่งวิ่งมาถึงประตูห้องตรวจ
    logger.info("--> [API] มีคำสั่งเริ่มตรวจยิงเข้ามา!")
    logger.info(f"--> [API] ข้อมูลที่หน้าเว็บส่งมาใน payload คือ: {exam_request}")

    exam_service = HospitalRegistry.consultation_service()
    staff_service = HospitalRegistry.staff_service()
    staff = staff_service.get_by_staff_id(exam_request.staff_id)

    # vital_signs = exam_to_vital_signs_vo(exam_request.vital_signs)

    new_exam = exam_service.start_consultation(
        queue_id=exam_request.queue_id, staff=staff
    )

    # 📸 จุดที่ 2: ติดกล้องส่องส่งท้ายก่อนจะเปิดประตูให้คนไข้ไปพบหมอ
    logger.info("<-- [API] ทำงานเสร็จสิ้น เตรียมตอบกลับสถานะ 'กำลังพบหมอ'")

    return ExamResponseSchema(
        consultation_id=new_exam.id,
        queue_id=new_exam.queue_id,
        patient_id=new_exam.patient_id,
        doctor_id=new_exam.doctor_id,
        status=new_exam.status,
    )
