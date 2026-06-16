import psycopg
from testcontainers.postgres import PostgresContainer


def test_postgres_container_spins_up_successfully():
    # Arrange: เตรียมสภาพแวดล้อม (สร้าง Container ของ PostgreSQL เวอร์ชัน 16)
    # เราใช้ Context Manager (with) เพื่อให้มันลบ Container ทิ้งอัตโนมัติเมื่อจบ block
    with PostgresContainer("postgres:16-alpine") as postgres:
        # Act: ดึง Connection String และลองเชื่อมต่อ Database
        raw_url = postgres.get_connection_url()

        # คลีนข้อมูล: ลบคำว่า '+psycopg2' ออก เพื่อให้ได้ URL มาตรฐาน
        # เปลี่ยนจาก 'postgresql+psycopg2://...' เป็น 'postgresql://...'
        db_url = raw_url.replace("+psycopg2", "")

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # ลองเขียน SQL ดิบๆ แบบง่ายที่สุด
                cur.execute("SELECT 1;")
                result = cur.fetchone()

        # Assert: ตรวจสอบผลลัพธ์ว่า Database ตอบกลับมาถูกต้องหรือไม่
        assert result[0] == 1
