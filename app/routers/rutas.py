from typing import Optional
from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.ruta import RutaPlanificada
from app.routers.base import APIRouter
from app.services import rutas as svc

router = APIRouter(prefix="/api/rutas", tags=["rutas"])


@router.get("", response_model=list[RutaPlanificada])
def get_rutas(usuario=Depends(get_usuario_actual)):
    return svc.listar()


@router.get("/{inspector_id}", response_model=Optional[RutaPlanificada])
def get_ruta(inspector_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_por_inspector(inspector_id)


class ParadaBody(BaseModel):
    poligonoId: str
    poligonoNombre: str
    orden: int
    visitada: bool


class RutaBody(BaseModel):
    inspectorNombre: str
    fecha: str
    paradas: list[ParadaBody]


@router.put("", response_model=RutaPlanificada)
def guardar_ruta(body: RutaBody, usuario=Depends(get_usuario_actual)):
    paradas = [
        {"poligono_id": p.poligonoId, "poligono_nombre": p.poligonoNombre,
         "orden": p.orden, "visitada": p.visitada}
        for p in body.paradas
    ]
    return svc.guardar(usuario["id"], body.inspectorNombre, body.fecha, paradas)


@router.delete("", response_model=dict)
def eliminar_ruta(usuario=Depends(get_usuario_actual)):
    svc.eliminar(usuario["id"])
    return {"ok": True}
