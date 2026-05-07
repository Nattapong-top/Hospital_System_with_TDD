# queue_service.py
from datetime import datetime, date
from typing import Tuple, Optional
from uuid import UUID

from domain.custom_error import DuplicationQueueError, QueueNotFoundError, VitalSignsMissingError
from domain.entities import Queue
from domain.interfaces import QueueRecord
from domain.value_object import Number, VitalSigns, QueueStatus, Diagnosis


class QueueService:
    def __init__(self, queue_repo: QueueRecord) -> None:
        self.queue_repo = queue_repo

    def issue_new_queue(self, patient_id: UUID, today: date, vital_signs: Optional[VitalSigns]) -> Queue:
        self._ensure_no_duplicate_queue_and_no_vital_signs(patient_id, today, vital_signs)
        last_date, last_num = self._check_queue_of_day()
        next_date, next_num = self._get_next_number(last_date, last_num, today)
        new_queue = self._create_new_queue(patient_id, next_date, next_num, vital_signs)
        self.queue_repo.save(new_queue)
        return new_queue

    def start_consultation(self, queue_id: UUID) -> Queue:
        queue = self._get_queue_or_raise(queue_id)
        queue.start_consultation()
        self.queue_repo.update(queue)
        return queue

    def complete_visit(self, queue_id: UUID, diagnosis: Diagnosis) -> Queue:
        queue = self._get_queue_or_raise(queue_id=queue_id)
        queue.complete_visit(diagnosis)
        self.queue_repo.update(queue)
        return queue

    def cancel_visit(self, queue_id: UUID) -> Queue:
        queue = self._get_queue_or_raise(queue_id=queue_id)
        queue.cancel_visit()
        self.queue_repo.update(queue)
        return queue

    def get_active_queue_by_patient(self, patient_id: UUID, search_date: date = None) -> Queue | None:
        """เป็นปุ่มกดให้คนนอก (เช่น เทส หรือ Registrar) มาถามหาคิวที่ยัง Active อยู่"""
        # 🚩 ถ้าป๋าส่งวันที่มาให้ใช้วันนั้น ถ้าไม่ส่งให้ใช้วันนี้
        target_date = search_date or date.today()
        # 2. สั่งให้ช่างเหล็ก (Repo) มุดตู้ไปหามาให้
        # (นี่คือจุดที่มันจะวิ่งไปเรียก SQL
        return self.queue_repo.find_active_queue_by_patient(patient_id=patient_id, queue_date=target_date)

    def get_next_number(self, last_number: Number, last_date: date, time_now: date,
                        today: date) -> Tuple[Number, date, date]:
        last_number, last_date = self._reset_date_and_number(last_number, last_date, today)
        now_number = Number(id=last_number.id + 1)
        return now_number, last_date, time_now

    def _create_new_queue(self, patient_id: UUID, next_date: date, next_num: Number,
                          vital_signs: VitalSigns) -> Queue:
        new_queue = Queue(
            patient_id=patient_id,
            queue_date=next_date,
            queue_number=next_num,
            vital_signs=vital_signs,
            status=QueueStatus.WAITING
        )
        return new_queue

    def _get_next_number(self, last_date: date, last_num: Number, today: date) -> tuple[date, Number]:
        next_num, next_date, _ = self.get_next_number(
            last_number=last_num, last_date=last_date,
            today=today, time_now=datetime.now())
        return next_date, next_num

    def _check_queue_of_day(self) -> tuple[date, Number]:
        last_queue = self.queue_repo.get_last_queue()
        last_num: Number = last_queue.queue_number if last_queue else Number(id=0)
        last_date = last_queue.queue_date if last_queue else date(1990, 1, 1)
        return last_date, last_num

    def _ensure_no_duplicate_queue_and_no_vital_signs(self, patient_id: UUID, today: date, vital_signs:Optional[VitalSigns]) -> None:
        if vital_signs is None:
            raise VitalSignsMissingError()
        existing_queue = self.queue_repo.find_active_queue_by_patient(patient_id=patient_id, queue_date=today)
        if existing_queue:
            raise DuplicationQueueError(f'คนไข้ ID {patient_id} จองคิวซ้ำไม่ได้ครับ')

    def _reset_date_and_number(self, last_number: Number, last_date: date, today: date) -> tuple[Number, date]:
        if last_date < today:
            last_date = today
            last_number = Number(id=0)
        return last_number, last_date

    def _get_queue_or_raise(self, queue_id: UUID) -> Queue:
        queue = self.queue_repo.get_by_queue_id(queue_id=queue_id)
        if queue is None:
            raise QueueNotFoundError(queue_id)
        return queue

    def get_by_queue_id(self, queue_id: UUID) -> Queue | None:
        return self.queue_repo.get_by_queue_id(queue_id)

    def get_all_queues_today(self, today: date) -> list[Queue]:
        return self.queue_repo.get_all_queues_today(today)