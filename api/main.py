import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers import consultation, patient, queues, staff, examination
from domain.custom_error import (
    DomainError,
    StaffNotFoundError,
)

# ฝัง GPS ให้ Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.hospital_registry import HospitalRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: เปิดโรงพยาบาล ---
    HospitalRegistry.init_database()
    print("🏥 ระบบฐานข้อมูลและศูนย์บัญชาการพร้อมให้บริการ!")
    yield
    # --- Shutdown: ปิดโรงพยาบาล ---
    print("🔒 ปิดระบบเรียบร้อย พักผ่อนครับป๋า!")


app = FastAPI(title="Hospital Queue API - Paa Top IT", lifespan=lifespan)
app.include_router(staff.router)
app.include_router(patient.patient_router)
app.include_router(queues.queues_router)
app.include_router(consultation.consultation_router)
app.include_router(examination.examination_router)


# =====================================================================
# 🔮 วุ้นแปลภาษาครอบจักรวาล (Global Exception Handler)
# =====================================================================
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """
    เมื่อไหร่ที่ Service พ่น Error อะไรก็ตามที่สืบทอดมาจาก DomainError
    ให้ตอบกลับเป็น 400 Bad Request พร้อมข้อความที่ป๋าตั้งไว้!
    """
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.message
        },  # ดึงข้อความภาษาไทยสวยๆ จาก custom_error.py มาโชว์เลย!
    )


@app.exception_handler(StaffNotFoundError)
async def staff_not_found_error_handler(request: Request, exc: StaffNotFoundError):

    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )


@app.get("/")
def health_check():
    return {"message": "API Online ปลอดภัยดีครับป๋า", "status": "Ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
