from typing import Optional
from app.db.supabase_client import get_supabase
from app.models.incidente_urbano import EventoIncidenteUrbano, IncidenteUrbano

_BUCKET = "incidentes-urbanos"
_EXPIRACION = 3600
_COLS = "*, incidentes_urbanos_fotos(storage_path), incidentes_urbanos_eventos(*)"


def _firmar_fotos(sb, paths: list[str]) -> list[str]:
    if not paths:
        return []
    res = sb.storage.from_(_BUCKET).create_signed_urls(paths, _EXPIRACION)
    url_map = {item["path"]: item.get("signedURL", "") for item in (res or [])}
    return [url_map.get(p, "") for p in paths]


def _map(row: dict, sb) -> IncidenteUrbano:
    fotos_rows = row.get("incidentes_urbanos_fotos") or []
    paths = [f["storage_path"] for f in fotos_rows]
    urls = _firmar_fotos(sb, paths)

    eventos_rows = row.get("incidentes_urbanos_eventos") or []
    eventos = [
        EventoIncidenteUrbano(
            estado_anterior=e.get("estado_anterior"),
            estado_nuevo=e["estado_nuevo"],
            nota=e.get("nota"),
            cambiado_por=e["cambiado_por"],
            cambiado_por_nombre=e["cambiado_por_nombre"],
            cambiado_en=e["cambiado_en"],
        )
        for e in sorted(eventos_rows, key=lambda e: e["cambiado_en"])
    ]

    return IncidenteUrbano(
        id=row["id"],
        numero=row["numero"],
        tipo=row["tipo"],
        estado=row["estado"],
        lat=row["lat"],
        lng=row["lng"],
        origen_ubicacion=row.get("origen_ubicacion", "gps"),
        observacion=row.get("observacion"),
        referencia=row.get("referencia"),
        creado_por=row["creado_por"],
        creado_por_nombre=row["creado_por_nombre"],
        creado_en=row["creado_en"],
        actualizado_en=row["actualizado_en"],
        fotos=urls,
        eventos=eventos,
    )


def listar() -> list[IncidenteUrbano]:
    sb = get_supabase()
    res = sb.from_("incidentes_urbanos").select(_COLS).order("creado_en", desc=True).execute()
    return [_map(r, sb) for r in res.data]


def crear(
    incidente_id: str,
    tipo: str,
    lat: float,
    lng: float,
    origen_ubicacion: str,
    observacion: Optional[str],
    referencia: Optional[str],
    creado_por: str,
    creado_por_nombre: str,
    creado_en: str,
) -> IncidenteUrbano:
    sb = get_supabase()
    sb.from_("incidentes_urbanos").upsert(
        {
            "id": incidente_id,
            "tipo": tipo,
            "estado": "iniciado",
            "lat": lat,
            "lng": lng,
            "origen_ubicacion": origen_ubicacion,
            "observacion": observacion,
            "referencia": referencia,
            "creado_por": creado_por,
            "creado_por_nombre": creado_por_nombre,
            "creado_en": creado_en,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", incidente_id).single().execute()
    return _map(res.data, sb)


def cambiar_estado(
    incidente_id: str,
    estado_nuevo: str,
    nota: Optional[str],
    cambiado_por: str,
    cambiado_por_nombre: str,
    cambiado_en: str,
) -> IncidenteUrbano:
    sb = get_supabase()
    res_actual = sb.from_("incidentes_urbanos").select("estado").eq("id", incidente_id).single().execute()
    estado_anterior = res_actual.data["estado"]

    sb.from_("incidentes_urbanos").update({"estado": estado_nuevo}).eq("id", incidente_id).execute()
    sb.from_("incidentes_urbanos_eventos").insert(
        {
            "incidente_id": incidente_id,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "nota": nota,
            "cambiado_por": cambiado_por,
            "cambiado_por_nombre": cambiado_por_nombre,
            "cambiado_en": cambiado_en,
        }
    ).execute()

    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", incidente_id).single().execute()
    return _map(res.data, sb)


async def agregar_foto(
    incidente_id: str,
    foto_id: str,
    creada_en: str,
    nombre_archivo: str,
    contenido: bytes,
    content_type: str,
) -> IncidenteUrbano:
    sb = get_supabase()
    path = f"{incidente_id}/{foto_id}-{nombre_archivo}"
    sb.storage.from_(_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": content_type or "image/jpeg", "upsert": "true"},
    )
    sb.from_("incidentes_urbanos_fotos").insert(
        {"incidente_id": incidente_id, "storage_path": path, "creada_en": creada_en}
    ).execute()
    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", incidente_id).single().execute()
    return _map(res.data, sb)
