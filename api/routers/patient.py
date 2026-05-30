from fastapi import APIRouter, HTTPException, Depends

from api.schema import RegisterRequest
from api.mapper import to_address_vo, registrar_patient_detail
from domain.hospital_registry import HospitalRegistry
from infrastructure.auth.jwt_service import get_current_staff

patient_router = APIRouter(
    prefix="/api/patients", tags=["Patients"], dependencies=[Depends(get_current_staff)]
)


@patient_router.post("/register")
def register_patient(request: RegisterRequest) -> dict:
    try:
        registrar = HospitalRegistry.patient_registrar()

        registered_addr = to_address_vo(request.registered_address)

        current_addr = to_address_vo(request.current_address)

        registered_patient = registrar_patient_detail(
            current_addr, registered_addr, registrar, request
        )

        return {
            "message": "ลงทะเบียนสำเร็จ!",
            "id": str(registered_patient.id),
            "national_id": str(registered_patient.national_id.id),
            "first_name": str(registered_patient.first_name.value),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
