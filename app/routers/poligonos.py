from typing import Optional
from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.models.poligono import Poligono
from app.routers.base import APIRouter
from app.services import poligonos as svc

router = APIRouter(prefix="/api/poligonos", tags=["polígonos"])


@router.get("", response_model=list[Poligono])
def get_poligonos(usuario=Depends(get_usuario_actual)):
    return svc.listar()


@router.get("/{poligono_id}", response_model=Poligono)
def get_poligono(poligono_id: str, usuario=Depends(get_usuario_actual)):
    return svc.obtener_por_id(poligono_id)


class AvanceBody(BaseModel):
    avanceObra: float


@router.patch("/{poligono_id}/avance", response_model=Poligono)
def actualizar_avance(poligono_id: str, body: AvanceBody, usuario=Depends(get_usuario_actual)):
    return svc.actualizar_avance(poligono_id, body.avanceObra, usuario.get("rol"))


class AsignarTrabajoBody(BaseModel):
    inspectorId: Optional[str] = None


@router.post("/{poligono_id}/asignar-trabajo", response_model=Poligono)
def asignar_trabajo(poligono_id: str, body: AsignarTrabajoBody, usuario=Depends(get_usuario_actual)):
    return svc.asignar_trabajo(poligono_id, body.inspectorId)


class ListoParaEncenderBody(BaseModel):
    valor: bool


@router.post("/{poligono_id}/listo-para-encender", response_model=Poligono)
def listo_para_encender(poligono_id: str, body: ListoParaEncenderBody, usuario=Depends(get_usuario_actual)):
    return svc.marcar_listo_encender(poligono_id, body.valor)


class EmpresaBody(BaseModel):
    empresa: Optional[str] = None


@router.post("/{poligono_id}/empresa", response_model=Poligono)
def asignar_empresa(poligono_id: str, body: EmpresaBody, usuario=Depends(get_usuario_actual)):
    return svc.asignar_empresa(poligono_id, body.empresa)


class EstadoBody(BaseModel):
    estado: Optional[str] = None
    estadoObra212: Optional[str] = None


@router.post("/{poligono_id}/estado", response_model=Poligono)
def asignar_estado(poligono_id: str, body: EstadoBody, usuario=Depends(get_usuario_actual)):
    return svc.asignar_estado(poligono_id, body.estado, body.estadoObra212)


@router.post("/{poligono_id}/estado-vialidad", response_model=Poligono)
def asignar_estado_vialidad(poligono_id: str, body: EstadoBody, usuario=Depends(get_usuario_actual)):
    return svc.asignar_estado_vialidad(poligono_id, body.estadoObra212)


class NombreBody(BaseModel):
    nombre: str


@router.patch("/{poligono_id}/nombre", response_model=Poligono)
def renombrar(poligono_id: str, body: NombreBody, usuario=Depends(get_usuario_actual)):
    return svc.renombrar(poligono_id, body.nombre)
