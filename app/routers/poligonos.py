from typing import Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import Poligono
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/poligonos", tags=["polígonos"])

_COLS = (
    "id, nombre, tipo, cuadrante, jurisdiccion, acta_municipal, avance_obra, estado, "
    "observaciones, municipio, coordenadas, inspector_asignado_id, asignado_en, "
    "listo_para_encender, empresa, seccion, estado_obra_212, segmentos, perfiles(nombre)"
)


def _map(row: dict) -> Poligono:
    perfil = row.get("perfiles")
    nombre_inspector = None
    if isinstance(perfil, dict):
        nombre_inspector = perfil.get("nombre")
    elif isinstance(perfil, list) and perfil:
        nombre_inspector = perfil[0].get("nombre")

    return Poligono(
        id=row["id"],
        nombre=row["nombre"],
        tipo=row["tipo"],
        cuadrante=row.get("cuadrante", ""),
        jurisdiccion=row.get("jurisdiccion", "Municipal"),
        acta_municipal=row.get("acta_municipal", False),
        avance_obra=row.get("avance_obra", 0),
        estado=row["estado"],
        observaciones=row.get("observaciones", ""),
        municipio=row.get("municipio", ""),
        coordenadas=row.get("coordenadas", []),
        inspector_asignado_id=row.get("inspector_asignado_id"),
        inspector_asignado_nombre=nombre_inspector,
        asignado_en=row.get("asignado_en"),
        listo_para_encender=row.get("listo_para_encender", False),
        empresa=row.get("empresa"),
        seccion=row.get("seccion"),
        estado_obra_212=row.get("estado_obra_212"),
        segmentos=row.get("segmentos"),
    )


def _fetch_one(sb, poligono_id: str) -> Poligono:
    res = sb.from_("poligonos").select(_COLS).eq("id", poligono_id).single().execute()
    return _map(res.data)


@router.get("", response_model=list[Poligono])
def get_poligonos(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("poligonos").select(_COLS).eq("activo", True).order("nombre").execute()
    return [_map(r) for r in res.data]


@router.get("/{poligono_id}", response_model=Poligono)
def get_poligono(poligono_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("poligonos")
        .select(_COLS)
        .eq("id", poligono_id)
        .eq("activo", True)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Polígono no encontrado")
    return _map(res.data)


class AvanceBody(BaseModel):
    avanceObra: float


_ROLES_EQUIPO = {"inspector", "jefe", "administrador"}


@router.patch("/{poligono_id}/avance", response_model=Poligono)
def actualizar_avance(poligono_id: str, body: AvanceBody, usuario=Depends(get_usuario_actual)):
    if usuario.get("rol") not in _ROLES_EQUIPO:
        raise HTTPException(status_code=403, detail="Sin permiso para actualizar el avance de obra")
    sb = get_supabase()
    sb.from_("poligonos").update({"avance_obra": body.avanceObra}).eq("id", poligono_id).execute()
    return _fetch_one(sb, poligono_id)


class AsignarTrabajoBody(BaseModel):
    inspectorId: Optional[str] = None


@router.post("/{poligono_id}/asignar-trabajo", response_model=Poligono)
def asignar_trabajo(poligono_id: str, body: AsignarTrabajoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("asignar_trabajo", {"p_poligono_id": poligono_id, "p_inspector_id": body.inspectorId}).execute()
    return _fetch_one(sb, poligono_id)


class ListoParaEncenderBody(BaseModel):
    valor: bool


@router.post("/{poligono_id}/listo-para-encender", response_model=Poligono)
def listo_para_encender(poligono_id: str, body: ListoParaEncenderBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("marcar_listo_para_encender", {"p_poligono_id": poligono_id, "p_valor": body.valor}).execute()
    return _fetch_one(sb, poligono_id)


class EmpresaBody(BaseModel):
    empresa: Optional[str] = None


@router.post("/{poligono_id}/empresa", response_model=Poligono)
def asignar_empresa(poligono_id: str, body: EmpresaBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("asignar_empresa", {"p_poligono_id": poligono_id, "p_empresa": body.empresa}).execute()
    return _fetch_one(sb, poligono_id)


class EstadoBody(BaseModel):
    estado: Optional[str] = None
    estadoObra212: Optional[str] = None


@router.post("/{poligono_id}/estado", response_model=Poligono)
def asignar_estado(poligono_id: str, body: EstadoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc(
        "asignar_estado",
        {"p_poligono_id": poligono_id, "p_estado": body.estado, "p_estado_obra_212": body.estadoObra212},
    ).execute()
    return _fetch_one(sb, poligono_id)


@router.post("/{poligono_id}/estado-vialidad", response_model=Poligono)
def asignar_estado_vialidad(poligono_id: str, body: EstadoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc(
        "asignar_estado_obra_tramo_vialidad",
        {"p_poligono_id": poligono_id, "p_estado_obra_212": body.estadoObra212},
    ).execute()
    return _fetch_one(sb, poligono_id)


class NombreBody(BaseModel):
    nombre: str


@router.patch("/{poligono_id}/nombre", response_model=Poligono)
def renombrar(poligono_id: str, body: NombreBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("renombrar_poligono", {"p_poligono_id": poligono_id, "p_nombre": body.nombre}).execute()
    return _fetch_one(sb, poligono_id)
