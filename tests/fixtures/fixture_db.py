import os

from pytest import fixture

from domain.hospital_registry import HospitalRegistry


# =====================================================================
# 1. SYSTEM & DATABASE SETUP (ตัวคุมระบบและฐานข้อมูล)
# =====================================================================
# 🚩 1. ตัวคุมระบบ: เคลียร์ทุกอย่างก่อนเริ่มเทสแต่ละครั้ง
@fixture(autouse=True)
def setup_database():
    # 1. ตั้งค่าให้ใช้ DB สำหรับเทส
    HospitalRegistry.set_test_db()
    HospitalRegistry.init_database()

    yield  # รันเทสตรงนี้...

    # 2. หลังเทสจบ ปิดการเชื่อมต่อ และลบไฟล์ทิ้ง (ถ้ามี)
    HospitalRegistry.reset()
    db_path = HospitalRegistry.get_db_path()

    # ถ้าไม่ใช่ของจริง และไฟล์มีอยู่จริง ให้ลบทิ้ง
    if "test_database.db" in db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # ถ้า Windows ล็อกไฟล์ไว้ ไม่ต้องตกใจครับ ปล่อยผ่านไปก่อน
            pass
