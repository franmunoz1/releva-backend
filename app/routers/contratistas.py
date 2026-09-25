from typing import Optional
from datetime import datetime, timezone

from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import UbicacionTrabajoContratista, VehiculoContratista
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/contratistas", tags=["contratistas"])


# ---------------------------------------------------------------------------
# Vehículo
# ---------------------------------------------------------------------------

@router.get("/vehiculo", response_model=Optional[VehiculoContratista])
def get_vehiculo(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("vehiculos_contratista")
        .select("*")
        .eq("contratista_id", usuario["id"])
        .maybe_single()
        .execute()
    )
    if not res.data:
        return None
    r = res.data
    return VehiculoContratista(
        contratista_id=r["contratista_id"],
        patente=r["patente"],
        marca=r["marca"],
        modelo=r["modelo"],
        actualizado_en=r["actualizado_en"],
    )


class VehiculoBody(BaseModel):
    patente: str
    marca: str
    modelo: str


@router.put("/vehiculo", response_model=VehiculoContratista)
def guardar_vehiculo(body: VehiculoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("vehiculos_contratista").upsert(
        {
            "contratista_id": usuario["id"],
            "patente": body.patente,
            "marca": body.marca,
            "modelo": body.modelo,
            "actualizado_en": ahora,
        },
        on_conflict="contratista_id",
    ).execute()
    res = (
        sb.from_("vehiculos_contratista")
        .select("*")
        .eq("contratista_id", usuario["id"])
        .single()
        .execute()
    )
    r = res.data
    return VehiculoContratista(
        contratista_id=r["contratista_id"],
        patente=r["patente"],
        marca=r["marca"],
        modelo=r["modelo"],
        actualizado_en=r["actualizado_en"],
    )


# ---------------------------------------------------------------------------
# Ubicación de trabajo
# ---------------------------------------------------------------------------

@router.get("/ubicacion-trabajo", response_model=list[UbicacionTrabajoContratista])
def get_ubicaciones_trabajo(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("ubicaciones_trabajo_contratista")
        .select("*, perfiles(nombre)")
        .execute()
    )
    resultado = []
    for r in res.data:
        perfil = r.get("perfiles") or {}
        if isinstance(perfil, list):
            perfil = perfil[0] if perfil else {}
        resultado.append(
            UbicacionTrabajoContratista(
                contratista_id=r["contratista_id"],
                nombre_empresa=perfil.get("nombre", ""),
                lat=r["lat"],
                lng=r["lng"],
                actualizado_en=r["actualizado_en"],
            )
        )
    return resultado


class UbicacionTrabajoBody(BaseModel):
    lat: float
    lng: float


@router.put("/ubicacion-trabajo", response_model=UbicacionTrabajoContratista)
def guardar_ubicacion_trabajo(body: UbicacionTrabajoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("ubicaciones_trabajo_contratista").upsert(
        {
            "contratista_id": usuario["id"],
            "lat": body.lat,
            "lng": body.lng,
            "actualizado_en": ahora,
        },
        on_conflict="contratista_id",
    ).execute()
    res = (
        sb.from_("ubicaciones_trabajo_contratista")
        .select("*, perfiles(nombre)")
        .eq("contratista_id", usuario["id"])
        .single()
        .execute()
    )
    r = res.data
    perfil = r.get("perfiles") or {}
    if isinstance(perfil, list):
        perfil = perfil[0] if perfil else {}
    return UbicacionTrabajoContratista(
        contratista_id=r["contratista_id"],
        nombre_empresa=perfil.get("nombre", ""),
        lat=r["lat"],
        lng=r["lng"],
        actualizado_en=r["actualizado_en"],
    )


@router.delete("/ubicacion-trabajo", response_model=dict)
def eliminar_ubicacion_trabajo(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("ubicaciones_trabajo_contratista").delete().eq("contratista_id", usuario["id"]).execute()
    return {"ok": True}
