from typing import Optional
from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.ubicacion import UbicacionTrabajoContratista, VehiculoContratista
from app.routers.base import APIRouter
from app.services import contratistas as svc

router = APIRouter(prefix="/api/contratistas", tags=["contratistas"])


@router.get("/vehiculo", response_model=Optional[VehiculoContratista])
def get_vehiculo(usuario=Depends(get_usuario_actual)):
    return svc.obtener_vehiculo(usuario["id"])


class VehiculoBody(BaseModel):
    patente: str
    marca: str
    modelo: str


@router.put("/vehiculo", response_model=VehiculoContratista)
def guardar_vehiculo(body: VehiculoBody, usuario=Depends(get_usuario_actual)):
    return svc.guardar_vehiculo(usuario["id"], body.patente, body.marca, body.modelo)


@router.get("/ubicacion-trabajo", response_model=list[UbicacionTrabajoContratista])
def get_ubicaciones_trabajo(usuario=Depends(get_usuario_actual)):
    return svc.listar_ubicaciones_trabajo()


class UbicacionTrabajoBody(BaseModel):
    lat: float
    lng: float


@router.put("/ubicacion-trabajo", response_model=UbicacionTrabajoContratista)
def guardar_ubicacion_trabajo(body: UbicacionTrabajoBody, usuario=Depends(get_usuario_actual)):
    return svc.guardar_ubicacion_trabajo(usuario["id"], body.lat, body.lng)


@router.delete("/ubicacion-trabajo", response_model=dict)
def eliminar_ubicacion_trabajo(usuario=Depends(get_usuario_actual)):
    svc.eliminar_ubicacion_trabajo(usuario["id"])
    return {"ok": True}
