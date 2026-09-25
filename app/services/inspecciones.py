from datetime import datetime, timezone
from typing import Optional

from app.db.supabase_client import get_supabase
from app.models.inspeccion import (
    Fotografia,
    Inspeccion,
    InspeccionEnCursoResumen,
    InspeccionRecienteResumen,
    Observacion,
    ValoresRestauracion,
)

_COLS = "*, observaciones(*), fotografias(*)"
_FOTO_BUCKET = "fotografias"
_FOTO_EXPIRACION = 3600


def _firmar_urls(sb, paths: list[str]) -> dict[str, str]:
    if not paths:
        return {}
    res = sb.storage.from_(_FOTO_BUCKET).create_signed_urls(paths, _FOTO_EXPIRACION)
    return {item["path"]: item.get("signedURL", "") for item in (res or [])}


def _map_observaciones(rows: list[dict]) -> list[Observacion]:
    return [
        Observacion(id=r["id"], texto=r["texto"], creada_en=r["creada_en"])
        for r in sorted(rows, key=lambda r: r["creada_en"])
    ]


def _map_fotografias(rows: list[dict], urls: dict[str, str]) -> list[Fotografia]:
    return [
        Fotografia(
            id=r["id"],
            nombre_archivo=r["nombre_archivo"],
            preview_url=urls.get(r["storage_path"], ""),
            creada_en=r["creada_en"],
        )
        for r in sorted(rows, key=lambda r: r["creada_en"])
    ]


def _map(row: dict, sb) -> Inspeccion:
    fotos_rows = row.get("fotografias") or []
    paths = [f["storage_path"] for f in fotos_rows]
    urls = _firmar_urls(sb, paths)
    return Inspeccion(
        id=row["id"],
        poligono_id=row["poligono_id"],
        poligono_nombre=row["poligono_nombre"],
        inspector_id=row["inspector_id"],
        inspector_nombre=row["inspector_nombre"],
        fecha_inicio=row["fecha_inicio"],
        fecha_fin=row.get("fecha_fin"),
        tiempo_total_segundos=row.get("tiempo_total_segundos"),
        observaciones=_map_observaciones(row.get("observaciones") or []),
        observacion_final=row.get("observacion_final"),
        fotografias=_map_fotografias(fotos_rows, urls),
        estado=row["estado"],
        estado_resultante=row.get("estado_resultante"),
    )


def fetch_inspeccion(inspeccion_id: str) -> Inspeccion:
    sb = get_supabase()
    res = sb.from_("inspecciones").select(_COLS).eq("id", inspeccion_id).single().execute()
    return _map(res.data, sb)


def listar() -> list[Inspeccion]:
    sb = get_supabase()
    res = sb.from_("inspecciones").select(_COLS).order("fecha_inicio", desc=True).execute()
    return [_map(r, sb) for r in res.data]


def listar_en_curso_resumen() -> list[InspeccionEnCursoResumen]:
    sb = get_supabase()
    res = (
        sb.from_("inspecciones")
        .select("id, poligono_id, poligono_nombre, inspector_id, fecha_inicio")
        .eq("estado", "en_curso")
        .execute()
    )
    return [
        InspeccionEnCursoResumen(
            id=r["id"],
            poligono_id=r["poligono_id"],
            poligono_nombre=r["poligono_nombre"],
            inspector_id=r["inspector_id"],
            fecha_inicio=r["fecha_inicio"],
        )
        for r in res.data
    ]


def contar_finalizadas_hoy() -> int:
    sb = get_supabase()
    inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    res = (
        sb.from_("inspecciones")
        .select("id", count="exact")
        .eq("estado", "finalizada")
        .gte("fecha_fin", inicio.isoformat())
        .execute()
    )
    return res.count or 0


def listar_recientes(limite: int) -> list[InspeccionRecienteResumen]:
    sb = get_supabase()
    res = (
        sb.from_("inspecciones")
        .select("id, poligono_nombre, inspector_nombre, fecha_fin, estado_resultante, avance_obra_resultante")
        .eq("estado", "finalizada")
        .order("fecha_fin", desc=True)
        .limit(limite)
        .execute()
    )
    return [
        InspeccionRecienteResumen(
            id=r["id"],
            poligono_nombre=r["poligono_nombre"],
            inspector_nombre=r["inspector_nombre"],
            fecha_fin=r["fecha_fin"],
            estado_resultante=r["estado_resultante"],
            avance_obra_resultante=r.get("avance_obra_resultante") or 0,
        )
        for r in res.data
        if r.get("estado_resultante") and r.get("fecha_fin")
    ]


def obtener_en_curso_por_poligono(poligono_id: str, inspector_id: str) -> Optional[Inspeccion]:
    sb = get_supabase()
    res = (
        sb.from_("inspecciones")
        .select(_COLS)
        .eq("poligono_id", poligono_id)
        .eq("estado", "en_curso")
        .eq("inspector_id", inspector_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return None
    return _map(res.data, sb)


def obtener_conflicto(poligono_id: str, inspector_id_propio: str) -> Optional[dict]:
    sb = get_supabase()
    res = (
        sb.from_("inspecciones")
        .select("inspector_nombre")
        .eq("poligono_id", poligono_id)
        .eq("estado", "en_curso")
        .neq("inspector_id", inspector_id_propio)
        .limit(1)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return None
    return {"inspectorNombre": res.data["inspector_nombre"]}


def obtener_restauracion(inspeccion_id: str, poligono_id: str) -> ValoresRestauracion:
    sb = get_supabase()
    res = (
        sb.from_("inspecciones")
        .select("estado_resultante, avance_obra_resultante, acta_municipal_resultante")
        .eq("poligono_id", poligono_id)
        .eq("estado", "finalizada")
        .neq("id", inspeccion_id)
        .order("fecha_fin", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    if not res.data or res.data.get("estado_resultante") is None:
        return ValoresRestauracion(avance_obra=0, estado="no_relevada", acta_municipal=False)
    return ValoresRestauracion(
        avance_obra=res.data.get("avance_obra_resultante") or 0,
        estado=res.data["estado_resultante"],
        acta_municipal=res.data.get("acta_municipal_resultante") or False,
    )


def obtener_por_id(inspeccion_id: str) -> Optional[Inspeccion]:
    sb = get_supabase()
    res = sb.from_("inspecciones").select(_COLS).eq("id", inspeccion_id).maybe_single().execute()
    if not res.data:
        return None
    return _map(res.data, sb)


def iniciar(
    inspeccion_id: str,
    poligono_id: str,
    poligono_nombre: str,
    inspector_id: str,
    inspector_nombre: str,
    fecha_inicio: str,
) -> Inspeccion:
    sb = get_supabase()
    sb.from_("inspecciones").upsert(
        {
            "id": inspeccion_id,
            "poligono_id": poligono_id,
            "poligono_nombre": poligono_nombre,
            "inspector_id": inspector_id,
            "inspector_nombre": inspector_nombre,
            "fecha_inicio": fecha_inicio,
            "estado": "en_curso",
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    return fetch_inspeccion(inspeccion_id)


def agregar_observacion(
    inspeccion_id: str,
    observacion_id: str,
    texto: str,
    creada_en: str,
) -> Inspeccion:
    sb = get_supabase()
    sb.from_("observaciones").upsert(
        {
            "id": observacion_id,
            "inspeccion_id": inspeccion_id,
            "texto": texto,
            "creada_en": creada_en,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    return fetch_inspeccion(inspeccion_id)


async def agregar_fotografia(
    inspeccion_id: str,
    fotografia_id: str,
    nombre_archivo: str,
    creada_en: str,
    contenido: bytes,
    content_type: str,
) -> Inspeccion:
    sb = get_supabase()
    path = f"{inspeccion_id}/{fotografia_id}-{nombre_archivo}"
    sb.storage.from_(_FOTO_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": content_type or "image/jpeg", "upsert": "true"},
    )
    sb.from_("fotografias").upsert(
        {
            "id": fotografia_id,
            "inspeccion_id": inspeccion_id,
            "nombre_archivo": nombre_archivo,
            "storage_path": path,
            "creada_en": creada_en,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    return fetch_inspeccion(inspeccion_id)


def finalizar(
    inspeccion_id: str,
    observacion_final: str,
    estado: str,
    acta_municipal: bool,
    fecha_fin: str,
    tiempo_total_segundos: int,
    empresa: Optional[str],
    estado_obra_212: Optional[str],
) -> Inspeccion:
    sb = get_supabase()
    sb.rpc(
        "finalizar_inspeccion",
        {
            "p_inspeccion_id": inspeccion_id,
            "p_observacion_final": observacion_final,
            "p_estado": estado,
            "p_acta_municipal": acta_municipal,
            "p_fecha_fin": fecha_fin,
            "p_tiempo_total_segundos": tiempo_total_segundos,
            "p_empresa": empresa,
            "p_estado_obra_212": estado_obra_212,
        },
    ).execute()
    return fetch_inspeccion(inspeccion_id)


def cancelar(inspeccion_id: str) -> dict:
    sb = get_supabase()
    sb.rpc("cancelar_inspeccion", {"p_inspeccion_id": inspeccion_id}).execute()
    return {"ok": True}


def eliminar(inspeccion_id: str) -> dict:
    sb = get_supabase()
    res = sb.rpc("eliminar_inspeccion", {"p_inspeccion_id": inspeccion_id}).execute()
    paths = [p["storage_path"] for p in (res.data or [])]
    if paths:
        sb.storage.from_(_FOTO_BUCKET).remove(paths)
    return {"ok": True}


def eliminar_fotografia(inspeccion_id: str, fotografia_id: str) -> Inspeccion:
    sb = get_supabase()
    res = sb.from_("fotografias").select("storage_path").eq("id", fotografia_id).single().execute()
    path = res.data["storage_path"]
    sb.from_("fotografias").delete().eq("id", fotografia_id).execute()
    sb.storage.from_(_FOTO_BUCKET).remove([path])
    return fetch_inspeccion(inspeccion_id)
