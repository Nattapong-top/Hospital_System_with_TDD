from typing import Optional
from uuid import UUID

from domain.interfaces import StaffRepository
from domain.staff_entities import Staff
from domain.value_object import Username, NationalID


class SqlStaffRepository(StaffRepository):
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def save(self, staff: Staff) -> None:
        """บันทึกพนักงานใหม่"""
        pass

    def update(self, staff: Staff) -> None:
        """อัพเดทข้อมูลพนักงาน"""
        pass

    def get_by_username(self, username: Username) -> Optional[Staff]:
        """ค้นหาพนักงานด้วย username"""
        pass

    def get_by_staff_id(self, staff_id: UUID) -> Optional[Staff]:
        """ค้าหาพนักงานด้วย staff_id"""
        pass

    def get_by_national_id_staff(self, national_id: NationalID) -> Optional[NationalID]:
        """ค้นหาพนักงานด้วย national_id"""
        pass