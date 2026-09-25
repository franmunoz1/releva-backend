from typing import Optional
from fastapi import Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.vialidad import ArchivoZona, AsignacionZonaContratista, AvanceTramoVialidad, MarcacionVialidad
from app.routers.base import APIRouter
from app.services import vialidad as svc

router = APIRouter(prefix="/api/vialidad", tags=["vialidad"])


@router.get("/marcaciones/{zona}", response_model=list[MarcacionVialidad])
def get_marcaciones(zona: str, usuario=Depends(get_usuario_actual)):
    return svc.listar_marcaciones(zona)


class MarcacionBody(BaseModel):
    id: str
    poligonoId: str
    zona: str
    lat: float
    lng: float
    creadaEn: str


@router.post("/marcaciones", response_model=MarcacionVialidad, status_code=201)
def agregar_marcacion(body: MarcacionBody, usuario=Depends(get_usuario_actual)):
    return svc.agregar_marcacion(body.id, body.poligonoId, body.zona, usuario["id"], body.lat, body.lng, body.creadaEn)


@router.delete("/marcaciones/{marcacion_id}", response_model=dict)
def eliminar_marcacion(marcacion_id: str, usuario=Depends(get_usuario_actual)):
    svc.eliminar_marcacion(marcacion_id)
    return {"ok": True}


@router.get("/avance/{poligono_id}", response_model=Optional[AvanceTramoVialidad])
def get_avance(poligono_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_avance(poligono_id)


class AvanceBody(BaseModel):
    poligonoId: str
    porcentaje: float
    observacion: Optional[str] = None


@router.post("/avance", response_model=AvanceTramoVialidad)
def guardar_avance(body: AvanceBody, usuario=Depends(get_usuario_actual)):
    return svc.guardar_avance(body.poligonoId, usuario["id"], body.porcentaje, body.observacion)


@router.delete("/avance/{poligono_id}", response_model=dict)
def deshacer_avance(poligono_id: str, usuario=Depends(get_usuario_actual)):
    svc.deshacer_avance(poligono_id)
    return {"ok": True}


@router.get("/archivos/{zona}", response_model=list[ArchivoZona])
def get_archivos(zona: str, usuario=Depends(get_usuario_actual)):
    return svc.listar_archivos(zona)


@router.post("/archivos", response_model=ArchivoZona, status_code=201)
async def subir_archivo(
    archivo_id: str = Form(...),
    zona: str = Form(...),
    nombre: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    contenido = await file.read()
    return await svc.subir_archivo(
        archivo_id, zona, nombre, usuario["id"], contenido, file.content_type or "application/octet-stream"
    )


@router.delete("/archivos/{archivo_id}", response_model=dict)
def eliminar_archivo(archivo_id: str, usuario=Depends(get_usuario_actual)):
    svc.eliminar_archivo(archivo_id)
    return {"ok": True}


@router.get("/asignaciones", response_model=list[AsignacionZonaContratista])
def get_asignaciones(usuario=Depends(get_usuario_actual)):
    return svc.listar_asignaciones()


class AsignacionBody(BaseModel):
    zona: str
    contratistaId: str


@router.post("/asignaciones", response_model=AsignacionZonaContratista, status_code=201)
def asignar_zona(body: AsignacionBody, usuario=Depends(get_usuario_actual)):
    return svc.asignar_zona(body.zona, body.contratistaId)


@router.delete("/asignaciones/{asignacion_id}", response_model=dict)
def eliminar_asignacion(asignacion_id: str, usuario=Depends(get_usuario_actual)):
    svc.eliminar_asignacion(asignacion_id)
    return {"ok": True}
