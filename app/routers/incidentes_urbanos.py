from typing import Optional
from fastapi import Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.incidente_urbano import IncidenteUrbano
from app.routers.base import APIRouter
from app.services import incidentes_urbanos as svc

router = APIRouter(prefix="/api/incidentes-urbanos", tags=["incidentes urbanos"])


@router.get("", response_model=list[IncidenteUrbano])
def get_incidentes(usuario=Depends(get_usuario_actual)):
    return svc.listar()


class CrearIncidenteBody(BaseModel):
    id: str
    tipo: str
    lat: float
    lng: float
    origenUbicacion: str
    observacion: Optional[str] = None
    referencia: Optional[str] = None
    creadoPorNombre: str
    creadoEn: str


@router.post("", response_model=IncidenteUrbano, status_code=201)
def crear_incidente(body: CrearIncidenteBody, usuario=Depends(get_usuario_actual)):
    return svc.crear(
        body.id, body.tipo, body.lat, body.lng, body.origenUbicacion,
        body.observacion, body.referencia, usuario["id"], body.creadoPorNombre, body.creadoEn,
    )


class CambiarEstadoBody(BaseModel):
    estadoNuevo: str
    nota: Optional[str] = None
    cambiadoPorNombre: str
    cambiadoEn: str


@router.patch("/{incidente_id}/estado", response_model=IncidenteUrbano)
def cambiar_estado(incidente_id: str, body: CambiarEstadoBody, usuario=Depends(get_usuario_actual)):
    return svc.cambiar_estado(
        incidente_id, body.estadoNuevo, body.nota,
        usuario["id"], body.cambiadoPorNombre, body.cambiadoEn,
    )


@router.post("/{incidente_id}/fotos", response_model=IncidenteUrbano)
async def agregar_foto(
    incidente_id: str,
    foto_id: str = Form(...),
    creada_en: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    contenido = await file.read()
    return await svc.agregar_foto(
        incidente_id, foto_id, creada_en,
        file.filename or foto_id, contenido, file.content_type or "image/jpeg",
    )
