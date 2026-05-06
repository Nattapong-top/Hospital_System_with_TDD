# domain.interfaces
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
from uuid import UUID

from domain.consultation_entities import Consultation
from domain.entities import Queue, Patient
from domain.staff_entities import Staff
from domain.value_object import NationalID, Username


class QueueRecord(ABC):
    @abstractmethod
    def get_last_queue(self) -> Optional[Queue]:
        """ดึงคิวล่าสุดเพื่อเอามาออกเลขคิวถัดไป"""
        pass

    @abstractmethod
    def save(self, queue: Queue) -> None:
        """บันทึกคิวใหม่"""
        pass

    @abstractmethod
    def update(self, queue: Queue) -> None:
        """อัปเดตข้อมูลคิว (เช่น เปลี่ยนสถานะ)"""
        pass

    @abstractmethod
    def find_active_queue_by_patient(self, patient_id: UUID, queue_date: date) -> Optional[Queue]:
        """เช็คว่าคนไข้คนนี้มีคิวที่ยังตรวจไม่เสร็จในวันนี้ไหม"""
        pass

    @abstractmethod
    def get_by_queue_id(self, queue_id: UUID) -> Optional[Queue]:
        """หาคิวจาก ID"""
        pass

    @abstractmethod
    def get_all_queues_today(self, today: date) -> List[Queue]:
        """ดึงคิวทั้งหมดของวันนี้ (สำหรับพยาบาล)"""
        pass


class PatientRecord(ABC):
    @abstractmethod
    def save(self, patient: Patient) -> None:
        """บันทึกข้อมูลคนไข้ใหม่"""
        pass

    @abstractmethod
    def update(self, patient: Patient) -> None:
        """อัปเดตข้อมูลคนไข้"""
        pass

    @abstractmethod
    def get_by_national_id(self, national_id: NationalID) -> Optional[Patient]:
        """หาคนไข้จากเลขบัตรประชาชน"""
        pass


class StaffRepository(ABC):
    @abstractmethod
    def save(self, staff: Staff) -> None:
        """บันทึกพนักงานใหม่"""
        pass

    @abstractmethod
    def update(self, staff: Staff) -> None:
        """อัพเดทข้อมูลพนักงาน"""
        pass

    @abstractmethod
    def get_by_username(self, username: Username) -> Optional[Staff]:
        """ค้นหาพนักงานด้วย username"""
        pass

    @abstractmethod
    def get_by_staff_id(self, staff_id: UUID) -> Optional[Staff]:
        """ค้าหาพนักงานด้วย staff_id"""
        pass

    @abstractmethod
    def get_by_national_id_staff(self, national_id: NationalID) -> Optional[NationalID]:
        """ค้นหาพนักงานด้วย national_id"""
        pass

class ConsultationRepository(ABC):
    @abstractmethod
    def save(self, consultation: Consultation) -> None:
        pass

    @abstractmethod
    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation:
        pass