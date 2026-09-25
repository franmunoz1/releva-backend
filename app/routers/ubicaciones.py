from pydantic import BaseModel

from fastapi import Depends

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import UbicacionInspector, UbicacionTrabajoContratista
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/ubicaciones", tags=["ubicaciones"])


@router.get("", response_model=list[UbicacionInspector])
def get_ubicaciones(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("ubicaciones_actuales")
        .select("usuario_id, lat, lng, accuracy, actualizado_en, perfiles(nombre, rol)")
        .execute()
    )
    resultado = []
    for r in res.data:
        perfil = r.get("perfiles") or {}
        if isinstance(perfil, list):
            perfil = perfil[0] if perfil else {}
        resultado.append(
            UbicacionInspector(
                usuario_id=r["usuario_id"],
                nombre=perfil.get("nombre", ""),
                rol=perfil.get("rol", "inspector"),
                lat=r["lat"],
                lng=r["lng"],
                accuracy=r.get("accuracy", 0),
                actualizado_en=r["actualizado_en"],
            )
        )
    return resultado


class UbicacionBody(BaseModel):
    lat: float
    lng: float
    accuracy: float


@router.put("", response_model=dict)
def actualizar_ubicacion(body: UbicacionBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    from datetime import datetime, timezone

    sb.from_("ubicaciones_actuales").upsert(
        {
            "usuario_id": usuario["id"],
            "lat": body.lat,
            "lng": body.lng,
            "accuracy": body.accuracy,
            "actualizado_en": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="usuario_id",
    ).execute()
    return {"ok": True}


@router.delete("", response_model=dict)
def eliminar_ubicacion(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("ubicaciones_actuales").delete().eq("usuario_id", usuario["id"]).execute()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Ubicaciones de trabajo de contratistas
# ---------------------------------------------------------------------------

@router.get("/contratistas", response_model=list[UbicacionTrabajoContratista])
def get_ubicaciones_contratistas(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("ubicaciones_trabajo_contratista")
        .select("contratista_id, lat, lng, actualizado_en, perfiles(nombre), vehiculos_contratista(patente, marca, modelo)")
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
