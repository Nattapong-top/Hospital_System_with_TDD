# 🏥 Hospital_System_with_TDD

ระบบบริหารจัดการงานบริการโรงพยาบาล (Core Domain & API) พัฒนาด้วยสถาปัตยกรรม **Domain-Driven Design (DDD)** โดยยึดหลักความถูกต้องและเสถียรภาพสูงสุดผ่านกระบวนการ **TDD (Test-Driven Development)**

---

## 🚀 สถานะโครงการ (Project Status)
- ✅ **Total Tests:** `195 Passed` 🟢 (ครอบคลุม Unit, Integration, Repository และ API)
- ✅ **Architecture:** Clean Architecture / Layered Architecture
- ✅ **API Layer:** พัฒนาด้วย **FastAPI** พร้อมระบบจัดการ Lifespan และ Database Initialization

---

## 🏗️ โครงสร้างสถาปัตยกรรม (Architecture Layers)

### 1. Domain Layer (หัวใจของระบบ)
- **Entities & staff_entities:** `Patient`, `Queue`, `Consultation`, `Staff`
- **Value Objects:** - ข้อมูลส่วนบุคคล: `NationalID`, `Name`, `PhoneNumber`, `DateOfBirth`, `Address`
  - ข้อมูลสุขภาพ: `VitalSigns` (BP, Weight, Height, Temp), `Diagnosis`, `MedicineInfo`
  - ข้อมูลระบบ: `Number` (รันคิว), `Username`, `StaffRole`, `QueueStatus`
- **Interfaces (ABCs):** `PatientRecord`, `QueueRecord`, `StaffRepository`, `ConsultationRepository`

### 2. Service Layer (Domain Services)
- **`PatientRegistrar`**: จัดการการลงทะเบียนคนไข้ใหม่และตรวจสอบการลงทะเบียนซ้ำ
- **`QueueService`**: จัดการ Life-cycle ของคิว, การออกเลขคิวใหม่ตามวัน, และการจบการรักษา (`complete_visit`)
- **`ExaminationService`**: ประสานงานการตรวจรักษา, ตรวจสอบสิทธิ์แพทย์ (RBAC), และซิงค์สถานะกับระบบคิว
- **`StaffService`**: จัดการการลงทะเบียนบุคลากร และระบบยืนยันตัวตน (`authenticate_staff`)

### 3. Infrastructure Layer (การเชื่อมต่อภายนอก)
- **Database:** รองรับ **SQLite** สำหรับการใช้งานจริง และ **In-Memory** สำหรับการทดสอบ
- **Repository Implementations:** `SqlPatientRepository`, `SqlQueueRepository`
- **Registry Pattern:** `HospitalRegistry` ทำหน้าที่เป็นศูนย์กลางการสร้างและส่งมอบ Service (Dependency Injection)

### 4. API Layer (Entry Point)
- **FastAPI Framework**: รองรับ Endpoint สำคัญ เช่น การลงทะเบียนคนไข้ผ่าน JSON Payload
- **Lifespan Management**: ระบบเปิด-ปิดฐานข้อมูลอัตโนมัติเมื่อ Start/Stop Server

---

## 🎯 กฎทางธุรกิจที่สำคัญ (Core Business Rules)
1. **Queue Daily Reset:** ระบบจะรีเซ็ตเลขคิวใหม่ทุกครั้งที่ขึ้นวันใหม่โดยอัตโนมัติ
2. **Duplicate Prevention:** ป้องกันคนไข้จองคิวซ้ำซ้อนในวันเดียวกัน
3. **Strict RBAC:** "หมอเท่านั้นที่มีสิทธิ์ตรวจ" และระบบความปลอดภัยในการเข้าถึงข้อมูล
4. **Data Integrity:** ข้อมูลสัญญาณชีพ (Vital Signs) ต้องครบถ้วนก่อนทำการออกคิว

---

## 🧪 การทดสอบ (Testing)
ระบบมี Test Coverage ที่แข็งแกร่งถึง 195 เคส แบ่งเป็น:
- `test_api.py`: ทดสอบ Endpoints และ Schema Validation
- `test_examination_service.py`: ทดสอบ Logic การประสานงานข้าม Service
- `test_staff_service.py`: ทดสอบการสมัครงานและเข้าระบบของพนักงาน
- `test_value_object.py`: ทดสอบความถูกต้องของข้อมูล (Deep Validation)

```bash
# รันเทสทั้งหมดในเครื่องป๋า
pytest tests/