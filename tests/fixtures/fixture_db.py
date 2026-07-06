import os
from typing import LiteralString

import psycopg
from pytest import fixture
from testcontainers.postgres import PostgresContainer

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


# 💡 เปลี่ยนจาก scope="module" เป็น scope="session"
@fixture(scope="session")
def postgres_container():
    """
    สร้าง PostgreSQL Container แค่ '1 ครั้งต่อการรันเทสต์ทั้งโปรเจค' (session)
    """
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@fixture
def db_connection(postgres_container):
    """
    จ่ายท่อ Connection ที่สะอาดให้แต่ละ Test (ฟังก์ชันนี้รันใหม่ทุก Test)
    """
    raw_url = postgres_container.get_connection_url()
    db_url = raw_url.replace("+psycopg2", "")

    with psycopg.connect(db_url) as conn:
        yield conn
        # (เมื่อ Test จบ จะกลับมาทำลาย Connection อัตโนมัติ เพราะใช้ with)


@fixture
def pg_patient_table(db_connection):  # <--- เรียกใช้ db_connection ส่วนกลางได้เลย!
    # 🌟 1. ป้องกัน Connection ค้างจากเทสต์ก่อนหน้า
    db_connection.rollback()

    """Fixture สร้างตาราง Patient ใน Postgres เฉพาะสำหรับไฟล์เทสต์นี้"""
    _CREATE_PATIENT_TABLE_QUERY: LiteralString = """
        CREATE TABLE IF NOT EXISTS patient (
            id UUID PRIMARY KEY,
            national_id VARCHAR(13) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20) NOT NULL,
            date_of_birth JSONB NOT NULL,
            registered_address JSONB NOT NULL,
            current_address JSONB NOT NULL,
            rights VARCHAR(50) NOT NULL,
            version INTEGER DEFAULT 1
        );
    """
    with db_connection.cursor() as cur:
        cur.execute(_CREATE_PATIENT_TABLE_QUERY)
    db_connection.commit()

    yield db_connection

    # ล้างตาราง (DROP/TRUNCATE) ทิ้งหลังเทสต์คิวเสร็จ เพื่อไม่ให้ขยะไปกวนเทสต์อื่น
    with db_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS patient;")
    db_connection.commit()


@fixture
def pg_queue_table(db_connection):
    """Fixture สร้างตาราง Queue พร้อมระบบป้องกันข้อมูลรั่วไหลข้าม Test"""

    # 🌟 1. ป้องกัน Connection ค้างจากเทสต์ก่อนหน้า
    db_connection.rollback()

    with db_connection.cursor() as cur:
        # 🌟 2. สั่งทุบตารางทิ้งก่อนเลย เพื่อความชัวร์ว่าคลีน 100%
        cur.execute("DROP TABLE IF EXISTS queue;")

        # 3. สร้างตารางใหม่
        _CREATE_QUEUE_TABLE_QUERY: LiteralString = """
            CREATE TABLE IF NOT EXISTS queue (
                q_id UUID PRIMARY KEY, 
                p_id UUID NOT NULL, 
                q_num INTEGER NOT NULL,
                q_date DATE NOT NULL,          -- 🌟 เปลี่ยนเป็น DATE
                status VARCHAR(50) NOT NULL,   -- 🌟 เปลี่ยนเป็น VARCHAR
                ver INTEGER DEFAULT 1,
                bp_sys INTEGER, 
                bp_dia INTEGER, 
                w_kg NUMERIC(5,2),             -- 🌟 เปลี่ยนเป็น NUMERIC แทน REAL (แม่นยำกว่า)                                                                                   
                h_cm NUMERIC(5,2),             -- 🌟 เปลี่ยนเป็น NUMERIC
                temp_c NUMERIC(4,2),           -- 🌟 เปลี่ยนเป็น NUMERIC
                symptom TEXT, 
                diag_disease TEXT, 
                diag_treatment TEXT, 
                diag_meds JSONB                -- 🌟 เปลี่ยนเป็น JSONB ท่าไม้ตายของ Postgres!                                                                                    
            )
        """
        cur.execute(_CREATE_QUEUE_TABLE_QUERY)
    db_connection.commit()

    yield db_connection

    # 4. ล้างตารางหลังเทสต์เสร็จ (ทำอีกรอบเพื่อความสะอาด)
    db_connection.rollback()
    with db_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS queue;")
    db_connection.commit()


@fixture
def pg_consul_table(db_connection):

    db_connection.rollback()

    _CREATE_CONSUL_TABLE_QUERY: LiteralString = """
        CREATE TABLE IF NOT EXISTS consultations (
            id UUID PRIMARY KEY,
            queue_id UUID NOT NULL,
            doctor_id UUID NOT NULL,
            patient_id UUID NOT NULL,
            vital_signs TEXT NOT NULL,       -- เก็บเป็น JSON
            diagnosis VARCHAR(500),                  -- เก็บเป็น JSON (เป็น NULL ได้ตอนเริ่มตรวจ)
            status VARCHAR(100) NOT NULL,
            started_at TIMESTAMP NOT NULL,        -- เก็บ ISO format
            finished_at TIMESTAMP,                -- เก็บ ISO format (เป็น NULL ได้)
            version INTEGER NOT NULL DEFAULT 1
        )
    """

    with db_connection.cursor() as cur:
        cur.execute(_CREATE_CONSUL_TABLE_QUERY)
    db_connection.commit()

    yield db_connection
    db_connection.rollback()

    with db_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS consultations;")
    db_connection.commit()


@fixture
def pg_staffs_table(db_connection):
    db_connection.rollback()

    _CREATE_STAFFS_TABLE_QUERY: LiteralString = """
        CREATE TABLE IF NOT EXISTS staffs (
            staff_id UUID PRIMARY KEY,
            username VARCHAR(20) UNIQUE NOT NULL,
            hashed_password VARCHAR(60) NOT NULL,
            national_id VARCHAR(13) UNIQUE NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            date_of_birth JSONB NOT NULL,
            phone_number VARCHAR(10) NOT NULL,
            role TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
    """

    with db_connection.cursor() as cur:
        cur.execute(_CREATE_STAFFS_TABLE_QUERY)
    db_connection.commit()

    yield db_connection
    db_connection.rollback()

    with db_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS staffs;")
    db_connection.commit()
