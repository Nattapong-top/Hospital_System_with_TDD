from uuid import UUID
from typing import Optional, Union


# =====================================================================
# Base Error (ตัวแม่)
# =====================================================================
class DomainError(Exception):
    """
    Base class สำหรับ Error ทั้งหมดใน Domain Layer
    คลาสลูกสามารถตั้ง default_message ได้เลย หรือจะส่ง message ใหม่ตอนเรียกใช้ก็ได้
    """

    default_message = "เกิดข้อผิดพลาดในระบบ"

    def __init__(self, message: Optional[str] = None):
        self.message = message or self.default_message
        super().__init__(self.message)


# =====================================================================
# Queue Errors (เกี่ยวกับคิว)
# =====================================================================
class QueueNotFoundError(DomainError):
    def __init__(
        self, queue_id: Optional[Union[str, UUID]] = None, message: Optional[str] = None
    ):
        if queue_id and not message:
            message = f"ไม่พบคิว ID: {queue_id} ในระบบครับ"
        super().__init__(message or "ไม่พบคิวที่ระบุครับ")


class DuplicationQueueError(DomainError):
    default_message = "คนไข้มีคิวที่กำลังดำเนินการอยู่แล้ว ไม่สามารถจองคิวซ้ำได้ครับ"


class VitalSignsMissingError(DomainError):
    default_message = "ป๋าครับ! ไม่มีสัญญาณชีพ ออกคิวให้ไม่ได้นะ!"


# =====================================================================
# Consultation / Examination Errors (เกี่ยวกับการตรวจรักษา)
# =====================================================================
class ConsultationNotFoundError(DomainError):
    def __init__(
        self,
        consultation_id: Optional[Union[str, UUID]] = None,
        message: Optional[str] = None,
    ):
        if consultation_id and not message:
            message = f"ไม่พบใบตรวจรักษา ID: {consultation_id} ในระบบครับ"
        super().__init__(message or "ไม่พบใบตรวจรักษาที่ระบุครับ")


class InvalidStatusTransitionError(DomainError):
    default_message = "ไม่สามารถเปลี่ยนสถานะได้ เนื่องจากสถานะปัจจุบันไม่ถูกต้อง"


class MissingDiagnosisError(DomainError):
    default_message = "กรุณากรอกข้อมูลการวินิจฉัยโรคด้วยครับ"


class InvalidCancelRequestError(DomainError):
    default_message = "คำขอยกเลิกไม่ถูกต้อง หรือไม่สามารถยกเลิกได้ในสถานะปัจจุบัน"


# =====================================================================
# Staff / Auth / Permission Errors (เกี่ยวกับพนักงานและสิทธิ์)
# =====================================================================
class PermissionDeniedError(DomainError):
    default_message = "คุณไม่มีสิทธิ์ในการทำรายการนี้"


class DuplicateUsernameError(DomainError):
    default_message = "Username นี้มีผู้ใช้งานแล้วในระบบ"


# =====================================================================
# Patient & Generic Errors (ทั่วไปและคนไข้)
# =====================================================================
class DuplicateNationalIDError(DomainError):
    default_message = "หมายเลขบัตรประชาชนนี้ ถูกลงทะเบียนในระบบแล้ว"


class DoNotChangeIDError(DomainError):
    default_message = "ไม่อนุญาตให้แก้ไข ID หลักของระบบได้"


class RegistryNotConfiguredError(DomainError):
    default_message = "ระบบ Registry ยังไม่ได้ตั้งค่าหรือเชื่อมต่ออย่างถูกต้อง"


# =====================================================================
# Database / Concurrency Errors (เกี่ยวกับการชนกันของข้อมูล)
# =====================================================================
class ConcurrentUpdateError(DomainError):
    """ใช้ดักตอนที่มีคนพยายามเซฟข้อมูลทับกัน (Optimistic Locking)"""

    def __init__(
        self, entity_name: str = "ข้อมูล", entity_id: Optional[Union[str, UUID]] = None
    ):
        if entity_id:
            self.message = f"ไม่สามารถอัปเดต{entity_name} (ID: {entity_id}) ได้ เนื่องจากมีคนอื่นแก้ไขข้อมูลนี้ไปแล้วก่อนหน้านี้ กรุณารีเฟรชแล้วลองใหม่ครับ"
        else:
            self.message = (
                f"มีคนอื่นอัปเดต{entity_name}ไปแล้วก่อนหน้านี้ กรุณารีเฟรชหน้าจอครับ"
            )

        super().__init__(self.message)
