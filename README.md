# 🏥 Hospital System with TDD

![Pytest Status](https://github.com/nattapong-top/Hospital_System_with_TDD/actions/workflows/python-app.yml/badge.svg)

ระบบบริหารจัดการงานบริการโรงพยาบาล (Core Domain & API) พัฒนาด้วยสถาปัตยกรรม **Domain-Driven Design (DDD)** และควบคุมคุณภาพโค้ดผ่านกระบวนการ **Test-Driven Development (TDD)**

---

## 🚀 สถานะโครงการ (Project Status)
- **Total Tests:** 249 Passed (ครอบคลุม Unit, Integration, Repository และ API)
- **Architecture:** Clean Architecture / Layered Architecture
- **API Framework:** FastAPI พร้อมระบบจัดการ Lifespan และการเชื่อมต่อฐานข้อมูลอัตโนมัติ
- **Authentication:** JWT Login + Refresh Token พร้อมระบบ RBAC (Role-Based Access Control)

---

## 🔄 การทำงานของระบบ (System Workflow)

### ขั้นตอนการให้บริการผู้ป่วย (Patient Service Flow)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HOSPITAL PATIENT FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

  👤 ผู้ป่วยมาโรงพยาบาล
        │
        ▼
┌───────────────────┐
│  พยาบาลทะเบียน   │  ← RBAC: NURSE / RECEPTIONIST
│  ลงทะเบียนคนไข้  │     PatientRegistrar.register_patient()
│  (ตรวจสอบซ้ำ)    │     ✦ ห้ามซ้ำ NationalID
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  วัดสัญญาณชีพ    │  ← พยาบาลกรอก VitalSigns
│  (Vital Signs)   │     • Blood Pressure
│                  │     • Weight / Height
│                  │     • Temperature
└────────┬──────────┘
         │  ✦ บังคับกรอกครบก่อนออกคิว
         ▼
┌───────────────────┐
│   ออกเลขคิว      │  ← QueueService.create_queue()
│  (Issue Queue)   │     • รีเซ็ตเลขคิวทุกวัน
│                  │     • ห้ามจองซ้ำในวันเดียวกัน
└────────┬──────────┘
         │
         ▼
   ┌─────────────┐
   │   WAITING   │  ◄── สถานะเริ่มต้น "รอ"
   └──────┬──────┘
          │  พยาบาล หรือ หมอ กด "เรียกคนไข้เข้าพบ"
          │  QueueService.start_consultation()
          ▼              RBAC: NURSE / DOCTOR
   ┌─────────────┐
   │ IN_PROGRESS │  ──── "กำลังพบหมอ"
   └──────┬──────┘
          │  หมอกด "บันทึกผลการตรวจ"
          │  ExaminationService.complete_examination()
          ▼              RBAC: DOCTOR เท่านั้น
   ┌─────────────┐
   │  COMPLETED  │  ──── "ตรวจเสร็จแล้ว" ✅
   └─────────────┘

   ┌─────────────┐
   │  CANCELLED  │  ──── "ยกเลิกการตรวจ" ❌
   └─────────────┘  (ยกเลิกได้จาก WAITING และ IN_PROGRESS เท่านั้น)
```

### การเปลี่ยนสถานะคิว (Queue Status Transition)

```
                    ┌──────────────────────────────────────┐
                    │         QueueStatus Transitions       │
                    └──────────────────────────────────────┘

   WAITING ──────────────────────────────────► CANCELLED
     │                                        (ยกเลิกก่อนพบหมอ)
     │ start_consultation()
     │ [NURSE / DOCTOR]
     ▼
 IN_PROGRESS ────────────────────────────────► CANCELLED
     │                                        (ยกเลิกระหว่างพบหมอ)
     │ complete_examination()
     │ [DOCTOR only]
     ▼
 COMPLETED  (ยกเลิกไม่ได้)
```

| สถานะ | ค่า | ผู้มีสิทธิ์เปลี่ยน | เปลี่ยนได้จากสถานะ |
|---|---|---|---|
| `WAITING` | `"รอ"` | ระบบ (อัตโนมัติ) | — (สถานะเริ่มต้น) |
| `IN_PROGRESS` | `"กำลังพบหมอ"` | NURSE, DOCTOR | WAITING |
| `COMPLETED` | `"ตรวจเสร็จแล้ว"` | DOCTOR | IN_PROGRESS |
| `CANCELLED` | `"ยกเลิกการตรวจ"` | NURSE, DOCTOR | WAITING, IN_PROGRESS |

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
- **Repository:** `SqlPatientRepository`, `SqlQueueRepository`, `SqlStaffRepository`, `SqlConsultationRepository`
- **Registry:** `HospitalRegistry` ทำหน้าที่จัดการ Dependency Injection ทั้งระบบ

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