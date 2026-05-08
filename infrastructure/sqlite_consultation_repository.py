# infrastructure/sqlite_consultation_repository.py
from uuid import UUID
from domain.consultation_entities import Consultation
from domain.interfaces import ConsultationRepository


class SqlConsultationRepository(ConsultationRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def save(self, consultation: Consultation) -> None:
        # เดี๋ยวเราค่อยมาเขียนไส้ใน SQL กันครับป๋า ตอนนี้เอาให้ Import ผ่านก่อน
        pass

    def get_by_queue_id(self, queue_id: UUID) -> Consultation | None:
        # จำลองค่าไว้ก่อนครับป๋า
        return None

    def get_by_consultation_id(self, consultation_id: UUID) -> Consultation | None:
        pass
