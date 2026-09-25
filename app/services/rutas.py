from datetime import datetime, timezone
from typing import Optional
from app.db.supabase_client import get_supabase
from app.models.ruta import ParadaRuta, RutaPlanificada


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


def listar() -> list[RutaPlanificada]:
    sb = get_supabase()
    res = sb.from_("rutas_planificadas").select("*").execute()
    return [_map(r) for r in res.data]


def obtener_por_inspector(inspector_id: str) -> Optional[RutaPlanificada]:
    sb = get_supabase()
    res = (
        sb.from_("rutas_planificadas")
        .select("*")
        .eq("inspector_id", inspector_id)
        .maybe_single()
        .execute()
    )
    return _map(res.data) if res.data else None


def guardar(
    inspector_id: str,
    inspector_nombre: str,
    fecha: str,
    paradas: list[dict],
) -> RutaPlanificada:
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("rutas_planificadas").upsert(
        {
            "inspector_id": inspector_id,
            "inspector_nombre": inspector_nombre,
            "fecha": fecha,
            "paradas": paradas,
            "actualizado_en": ahora,
        },
        on_conflict="inspector_id",
    ).execute()
    res = sb.from_("rutas_planificadas").select("*").eq("inspector_id", inspector_id).single().execute()
    return _map(res.data)


def eliminar(inspector_id: str) -> None:
    sb = get_supabase()
    sb.from_("rutas_planificadas").delete().eq("inspector_id", inspector_id).execute()
