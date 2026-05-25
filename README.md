# 🏥 Hospital System with TDD

![Pytest Status](https://github.com/nattapong-top/Hospital_System_with_TDD/actions/workflows/python-app.yml/badge.svg)

ระบบบริหารจัดการงานบริการโรงพยาบาล (Core Domain & API) พัฒนาด้วยสถาปัตยกรรม **Domain-Driven Design (DDD)** และควบคุมคุณภาพโค้ดผ่านกระบวนการ **Test-Driven Development (TDD)**

---

## 🚀 สถานะโครงการ (Project Status)
- **Total Tests:** 210+ Passed (ครอบคลุม Unit, Integration, Repository และ API)
- **Architecture:** Clean Architecture / Layered Architecture
- **API Framework:** FastAPI พร้อมระบบจัดการ Lifespan และการเชื่อมต่อฐานข้อมูลอัตโนมัติ

---

## 🏗️ โครงสร้างสถาปัตยกรรม (Architecture Layers)

### 1. Domain Layer (ชั้นข้อมูลหลักและกฎทางธุรกิจ)
- **Entities:** `Patient`, `Queue`, `Consultation`, `Staff`
- **Value Objects:** - ข้อมูลส่วนบุคคล: `NationalID`, `Name`, `PhoneNumber`, `DateOfBirth`, `Address`
  - ข้อมูลสุขภาพ: `VitalSigns` (BP, Weight, Height, Temp), `Diagnosis`, `MedicineInfo`
  - ข้อมูลระบบ: `Number` (รันคิว), `Username`, `StaffRole`, `QueueStatus`, `HashedPassword`
- **Interfaces:** `PatientRecord`, `QueueRecord`, `StaffRepository`, `ConsultationRepository`

### 2. Service Layer (ชั้นจัดการกระบวนการทำงาน)
- **`PatientRegistrar`**: จัดการการลงทะเบียนผู้ป่วยและตรวจสอบข้อมูลซ้ำ
- **`QueueService`**: จัดการสถานะคิวและการออกเลขคิวประจำวัน
- **`ExaminationService`**: จัดการกระบวนการตรวจรักษา บันทึกการจ่ายยา และปรับปรุงสถานะคิว
- **`StaffService`**: จัดการข้อมูลพนักงานและระบบยืนยันตัวตน (Authentication)

### 3. Infrastructure Layer (ชั้นเชื่อมต่อระบบภายนอก)
- **Database:** SQLite สำหรับการใช้งานจริง และ In-Memory สำหรับการทดสอบ
- **Repository:** `SqlPatientRepository`, `SqlQueueRepository`, `SqlStaffRepository`
- **Registry:** `HospitalRegistry` ทำหน้าที่จัดการ Dependency Injection ทั้งระบบ

---

## 📖 คู่มือระบบ: โดเมนพนักงาน (Staff Domain Guide)
ระบบจัดการพนักงานถูกออกแบบโดยเน้นความถูกต้องและปลอดภัยของข้อมูล มีการแบ่งหน้าที่ดังนี้:

**ระดับ Domain (`staff_entities.py`)**
- `Staff.register()`: รับข้อมูลตั้งต้น เข้ารหัสผ่าน (`HashedPassword`) และกำหนดสถานะการทำงาน
- `Staff.__setattr__()`: ป้องกันการแก้ไขตัวแปรที่ไม่อนุญาตให้เปลี่ยนแปลง เช่น `staff_id` และ `national_id`
- `Staff.suspend()` / `reactivate()`: ระงับและคืนสิทธิ์การใช้งาน พร้อมระบบ `version` สำหรับจัดการการแก้ไขข้อมูลพร้อมกัน (Optimistic Concurrency Control)

**ระดับ Service (`staff_service.py`)**
- `register_staff()`: ตรวจสอบความซ้ำซ้อนของชื่อผู้ใช้ (Username) ก่อนสร้างข้อมูลพนักงานใหม่
- `authenticate_staff()`: ตรวจสอบสถานะบัญชีและยืนยันรหัสผ่านเพื่อเข้าสู่ระบบ (Login)

**ระดับ API (`staff.py`)**
- ตรวจสอบความถูกต้องของข้อมูล (Schema Validation) ผ่าน Pydantic และแปลงรูปแบบข้อมูลให้ตรงกับระบบก่อนส่งให้ Service ดำเนินการ

---

## 🎯 กฎทางธุรกิจที่สำคัญ (Core Business Rules)
1. **การรีเซ็ตคิวรายวัน:** ระบบจะเริ่มนับเลขคิวใหม่โดยอัตโนมัติเมื่อเปลี่ยนวันทำการ
2. **การป้องกันข้อมูลซ้ำ:** ไม่อนุญาตให้ผู้ป่วยจองคิวซ้ำในวันเดียวกัน และไม่อนุญาตให้พนักงานใช้ชื่อผู้ใช้ซ้ำ
3. **การจัดการสิทธิ์ (RBAC):** กำหนดสิทธิ์การเข้าถึงอย่างเคร่งครัด เช่น แพทย์เท่านั้นที่สามารถบันทึกผลการตรวจรักษาได้
4. **ความครบถ้วนของข้อมูล:** ต้องบันทึกข้อมูลสัญญาณชีพ (Vital Signs) ให้ครบถ้วนก่อนทำการออกคิวเสมอ

---

## 👷 การตรวจสอบและการทดสอบ (CI/CD & Testing)
ระบบใช้ **GitHub Actions** สำหรับรัน Automated Testing เมื่อมีการอัปเดตโค้ด:
- **เครื่องมือ:** ใช้ `pytest` สำหรับการทดสอบร่วมกับ `ruff` และ `black` สำหรับจัดรูปแบบโค้ด
- **ความครอบคลุม:** ทดสอบทั้งกรณีการใช้งานปกติ (Happy Path) และกรณีเกิดข้อผิดพลาด (Sad Path)

**คำสั่งสำหรับรันการทดสอบในเครื่อง:**
```bash
make check
make fix
make all