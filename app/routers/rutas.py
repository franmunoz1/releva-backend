from typing import Optional
from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import ParadaRuta, RutaPlanificada
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/rutas", tags=["rutas"])


def _map(row: dict) -> RutaPlanificada:
    return RutaPlanificada(
        inspector_id=row["inspector_id"],
        inspector_nombre=row["inspector_nombre"],
        fecha=row["fecha"],
        paradas=[
            ParadaRuta(
                poligono_id=p["poligono_id"],
                poligono_nombre=p["poligono_nombre"],
                orden=p["orden"],
                visitada=p["visitada"],
            )
            for p in (row.get("paradas") or [])
        ],
        actualizado_en=row["actualizado_en"],
    )


@router.get("", response_model=list[RutaPlanificada])
def get_rutas(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("rutas_planificadas").select("*").execute()
    return [_map(r) for r in res.data]


@router.get("/{inspector_id}", response_model=Optional[RutaPlanificada])
def get_ruta(inspector_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = (
        sb.from_("rutas_planificadas")
        .select("*")
        .eq("inspector_id", inspector_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return None
    return _map(res.data)


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
    from datetime import datetime, timezone
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    paradas = [
        {"poligono_id": p.poligonoId, "poligono_nombre": p.poligonoNombre, "orden": p.orden, "visitada": p.visitada}
        for p in body.paradas
    ]
    sb.from_("rutas_planificadas").upsert(
        {
            "inspector_id": usuario["id"],
            "inspector_nombre": body.inspectorNombre,
            "fecha": body.fecha,
            "paradas": paradas,
            "actualizado_en": ahora,
        },
        on_conflict="inspector_id",
    ).execute()
    res = sb.from_("rutas_planificadas").select("*").eq("inspector_id", usuario["id"]).single().execute()
    return _map(res.data)


@router.delete("", response_model=dict)
def eliminar_ruta(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("rutas_planificadas").delete().eq("inspector_id", usuario["id"]).execute()
    return {"ok": True}
