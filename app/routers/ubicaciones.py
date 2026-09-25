from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.ubicacion import UbicacionInspector, UbicacionTrabajoContratista
from app.routers.base import APIRouter
from app.services import ubicaciones as svc

router = APIRouter(prefix="/api/ubicaciones", tags=["ubicaciones"])


@router.get("", response_model=list[UbicacionInspector])
def get_ubicaciones(usuario=Depends(get_usuario_actual)):
    return svc.listar()


class UbicacionBody(BaseModel):
    lat: float
    lng: float
    accuracy: float


@router.put("", response_model=dict)
def actualizar_ubicacion(body: UbicacionBody, usuario=Depends(get_usuario_actual)):
    svc.actualizar(usuario["id"], body.lat, body.lng, body.accuracy)
    return {"ok": True}


@router.delete("", response_model=dict)
def eliminar_ubicacion(usuario=Depends(get_usuario_actual)):
    svc.eliminar(usuario["id"])
    return {"ok": True}


@router.get("/contratistas", response_model=list[UbicacionTrabajoContratista])
def get_ubicaciones_contratistas(usuario=Depends(get_usuario_actual)):
    return svc.listar_contratistas()
