from fastapi import APIRouter
import logging


from api.schema import (
    ExamRequestSchema,
    ExamResponseSchema,
    ExamFinishResponseSchema,
    FinishRequestSchema,
    to_diagnosis_vo,
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


@examination_router.post("/finish")
def finish_examination(finish_request: FinishRequestSchema) -> ExamFinishResponseSchema:
    logger.info("--> [API] มีคำสั่งเริ่มตรวจยิงเข้ามา!")
    logger.info(f"--> [API] ข้อมูลที่หน้าเว็บส่งมาใน payload คือ: {finish_request}")

    exam_service = HospitalRegistry.consultation_service()
    staff_service = HospitalRegistry.staff_service()
    doctor = staff_service.get_by_staff_id(finish_request.doctor_id)

    diagnosis_vo = to_diagnosis_vo(finish_request.diagnosis)

    finished_exam = exam_service.finish_consultation(
        consultation_id=finish_request.consultation_id,
        doctor=doctor,
        diagnosis=diagnosis_vo,
    )
    logger.info("<-- [API] ทำงานเสร็จสิ้น เตรียมตอบกลับสถานะ 'ตรวจเสร็จแล้ว'")

    return ExamFinishResponseSchema(
        consultation_id=finished_exam.id,
        queue_id=finished_exam.queue_id,
        patient_id=finished_exam.patient_id,
        doctor_id=finished_exam.doctor_id,
        disease=finished_exam.diagnosis.disease,
        treatment=finished_exam.diagnosis.treatment,
        medicines=finished_exam.diagnosis.medicine_prescribed,
        finished_at=finished_exam.finished_at,
    )
