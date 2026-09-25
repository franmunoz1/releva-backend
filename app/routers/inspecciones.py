from typing import Optional
from fastapi import Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.inspeccion import Inspeccion, InspeccionEnCursoResumen, InspeccionRecienteResumen, ValoresRestauracion
from app.routers.base import APIRouter
from app.services import inspecciones as svc

router = APIRouter(prefix="/api/inspecciones", tags=["inspecciones"])


@router.get("", response_model=list[Inspeccion])
def get_inspecciones(usuario=Depends(get_usuario_actual)):
    return svc.listar()


@router.get("/en-curso-resumen", response_model=list[InspeccionEnCursoResumen])
def get_en_curso_resumen(usuario=Depends(get_usuario_actual)):
    return svc.listar_en_curso_resumen()


@router.get("/finalizadas-hoy", response_model=dict)
def contar_finalizadas_hoy(usuario=Depends(get_usuario_actual)):
    return {"count": svc.contar_finalizadas_hoy()}


@router.get("/recientes", response_model=list[InspeccionRecienteResumen])
def get_recientes(limite: int = 10, usuario=Depends(get_usuario_actual)):
    return svc.listar_recientes(limite)


@router.get("/en-curso/{poligono_id}/{inspector_id}", response_model=Optional[Inspeccion])
def get_en_curso_por_poligono(poligono_id: str, inspector_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_en_curso_por_poligono(poligono_id, inspector_id)


@router.get("/conflicto/{poligono_id}", response_model=Optional[dict])
def get_conflicto(poligono_id: str, inspector_id_propio: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_conflicto(poligono_id, inspector_id_propio)


@router.get("/{inspeccion_id}/restauracion", response_model=ValoresRestauracion)
def get_restauracion(inspeccion_id: str, poligono_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_restauracion(inspeccion_id, poligono_id)


@router.get("/{inspeccion_id}", response_model=Optional[Inspeccion])
def get_por_id(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_por_id(inspeccion_id)


class IniciarBody(BaseModel):
    inspeccionId: str
    poligonoId: str
    poligonoNombre: str
    inspectorId: str
    inspectorNombre: str
    fechaInicio: str


@router.post("", response_model=Inspeccion, status_code=201)
def iniciar_inspeccion(body: IniciarBody, usuario=Depends(get_usuario_actual)):
    return svc.iniciar(
        body.inspeccionId, body.poligonoId, body.poligonoNombre,
        body.inspectorId, body.inspectorNombre, body.fechaInicio,
    )


class ObservacionBody(BaseModel):
    observacionId: str
    texto: str
    creadaEn: str


@router.post("/{inspeccion_id}/observacion", response_model=Inspeccion)
def agregar_observacion(inspeccion_id: str, body: ObservacionBody, usuario=Depends(get_usuario_actual)):
    return svc.agregar_observacion(inspeccion_id, body.observacionId, body.texto, body.creadaEn)


@router.post("/{inspeccion_id}/fotografias", response_model=Inspeccion)
async def agregar_fotografia(
    inspeccion_id: str,
    fotografia_id: str = Form(...),
    nombre_archivo: str = Form(...),
    creada_en: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    contenido = await file.read()
    return await svc.agregar_fotografia(
        inspeccion_id, fotografia_id, nombre_archivo, creada_en,
        contenido, file.content_type or "image/jpeg",
    )


class FinalizarBody(BaseModel):
    observacionFinal: str
    estado: str
    actaMunicipal: bool
    empresa: Optional[str] = None
    estadoObra212: Optional[str] = None
    fechaFin: str
    tiempoTotalSegundos: int


@router.post("/{inspeccion_id}/finalizar", response_model=Inspeccion)
def finalizar(inspeccion_id: str, body: FinalizarBody, usuario=Depends(get_usuario_actual)):
    return svc.finalizar(
        inspeccion_id, body.observacionFinal, body.estado, body.actaMunicipal,
        body.fechaFin, body.tiempoTotalSegundos, body.empresa, body.estadoObra212,
    )


@router.post("/{inspeccion_id}/cancelar", response_model=dict)
def cancelar(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    return svc.cancelar(inspeccion_id)


@router.delete("/{inspeccion_id}", response_model=dict)
def eliminar(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    return svc.eliminar(inspeccion_id)


@router.delete("/{inspeccion_id}/fotografias/{fotografia_id}", response_model=Inspeccion)
def eliminar_fotografia(inspeccion_id: str, fotografia_id: str, usuario=Depends(get_usuario_actual)):
    return svc.eliminar_fotografia(inspeccion_id, fotografia_id)
