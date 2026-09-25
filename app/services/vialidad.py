import uuid
from datetime import datetime, timezone
from typing import Optional

from app.db.supabase_client import get_supabase
from app.models.vialidad import ArchivoZona, AsignacionZonaContratista, AvanceTramoVialidad, MarcacionVialidad

_ARCHIVOS_BUCKET = "archivos-zona"
_ARCHIVOS_EXPIRACION = 3600


# ---------------------------------------------------------------------------
# Marcaciones
# ---------------------------------------------------------------------------

def listar_marcaciones(zona: str) -> list[MarcacionVialidad]:
    sb = get_supabase()
    res = sb.from_("marcaciones_vialidad").select("*").eq("zona", zona).execute()
    return [
        MarcacionVialidad(
            id=r["id"],
            poligono_id=r["poligono_id"],
            inspector_id=r["inspector_id"],
            lat=r["lat"],
            lng=r["lng"],
            creada_en=r["creada_en"],
        )
        for r in res.data
    ]


def agregar_marcacion(
    marcacion_id: str,
    poligono_id: str,
    zona: str,
    inspector_id: str,
    lat: float,
    lng: float,
    creada_en: str,
) -> MarcacionVialidad:
    sb = get_supabase()
    sb.from_("marcaciones_vialidad").upsert(
        {
            "id": marcacion_id,
            "poligono_id": poligono_id,
            "zona": zona,
            "inspector_id": inspector_id,
            "lat": lat,
            "lng": lng,
            "creada_en": creada_en,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    res = sb.from_("marcaciones_vialidad").select("*").eq("id", marcacion_id).single().execute()
    r = res.data
    return MarcacionVialidad(
        id=r["id"], poligono_id=r["poligono_id"], inspector_id=r["inspector_id"],
        lat=r["lat"], lng=r["lng"], creada_en=r["creada_en"],
    )


def eliminar_marcacion(marcacion_id: str) -> None:
    sb = get_supabase()
    sb.from_("marcaciones_vialidad").delete().eq("id", marcacion_id).execute()


# ---------------------------------------------------------------------------
# Avance de tramo
# ---------------------------------------------------------------------------

def obtener_avance(poligono_id: str) -> Optional[AvanceTramoVialidad]:
    sb = get_supabase()
    res = (
        sb.from_("avance_tramo_vialidad")
        .select("*")
        .eq("poligono_id", poligono_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return None
    r = res.data
    return AvanceTramoVialidad(
        poligono_id=r["poligono_id"],
        contratista_id=r["contratista_id"],
        porcentaje=r["porcentaje"],
        observacion=r.get("observacion"),
        actualizado_en=r["actualizado_en"],
    )


def guardar_avance(
    poligono_id: str, contratista_id: str, porcentaje: float, observacion: Optional[str]
) -> AvanceTramoVialidad:
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("avance_tramo_vialidad").upsert(
        {
            "poligono_id": poligono_id,
            "contratista_id": contratista_id,
            "porcentaje": porcentaje,
            "observacion": observacion,
            "actualizado_en": ahora,
        },
        on_conflict="poligono_id",
    ).execute()
    res = sb.from_("avance_tramo_vialidad").select("*").eq("poligono_id", poligono_id).single().execute()
    r = res.data
    return AvanceTramoVialidad(
        poligono_id=r["poligono_id"],
        contratista_id=r["contratista_id"],
        porcentaje=r["porcentaje"],
        observacion=r.get("observacion"),
        actualizado_en=r["actualizado_en"],
    )


def deshacer_avance(poligono_id: str) -> None:
    sb = get_supabase()
    sb.rpc("deshacer_avance_tramo", {"p_poligono_id": poligono_id}).execute()


# ---------------------------------------------------------------------------
# Archivos de zona
# ---------------------------------------------------------------------------

def listar_archivos(zona: str) -> list[ArchivoZona]:
    sb = get_supabase()
    res = (
        sb.from_("archivos_zona_vialidad")
        .select("*")
        .eq("zona", zona)
        .order("creado_en", desc=True)
        .execute()
    )
    archivos = []
    for r in res.data:
        try:
            url_res = sb.storage.from_(_ARCHIVOS_BUCKET).create_signed_url(r["storage_path"], _ARCHIVOS_EXPIRACION)
            url = url_res.get("signedURL", "")
        except Exception:
            url = ""
        archivos.append(
            ArchivoZona(
                id=r["id"], zona=r["zona"], nombre=r["nombre"],
                storage_path=r["storage_path"], url=url,
                subido_por=r["subido_por"], creado_en=r["creado_en"],
            )
        )
    return archivos


async def subir_archivo(
    archivo_id: str,
    zona: str,
    nombre: str,
    subido_por: str,
    contenido: bytes,
    content_type: str,
) -> ArchivoZona:
    sb = get_supabase()
    path = f"{zona}/{archivo_id}-{nombre}"
    sb.storage.from_(_ARCHIVOS_BUCKET).upload(
        path, contenido,
        file_options={"content-type": content_type or "application/octet-stream", "upsert": "true"},
    )
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("archivos_zona_vialidad").insert(
        {"id": archivo_id, "zona": zona, "nombre": nombre, "storage_path": path,
         "subido_por": subido_por, "creado_en": ahora}
    ).execute()
    url_res = sb.storage.from_(_ARCHIVOS_BUCKET).create_signed_url(path, _ARCHIVOS_EXPIRACION)
    return ArchivoZona(
        id=archivo_id, zona=zona, nombre=nombre, storage_path=path,
        url=url_res.get("signedURL", ""), subido_por=subido_por, creado_en=ahora,
    )


def eliminar_archivo(archivo_id: str) -> None:
    sb = get_supabase()
    res = sb.from_("archivos_zona_vialidad").select("storage_path").eq("id", archivo_id).single().execute()
    sb.from_("archivos_zona_vialidad").delete().eq("id", archivo_id).execute()
    try:
        sb.storage.from_(_ARCHIVOS_BUCKET).remove([res.data["storage_path"]])
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Asignaciones de zona
# ---------------------------------------------------------------------------

def listar_asignaciones() -> list[AsignacionZonaContratista]:
    sb = get_supabase()
    res = (
        sb.from_("asignaciones_zona_contratista")
        .select("*, perfiles(nombre)")
        .order("zona")
        .execute()
    )
    resultado = []
    for r in res.data:
        perfil = r.get("perfiles") or {}
        if isinstance(perfil, list):
            perfil = perfil[0] if perfil else {}
        resultado.append(
            AsignacionZonaContratista(
                id=r["id"], zona=r["zona"], contratista_id=r["contratista_id"],
                contratista_nombre=perfil.get("nombre", ""), asignado_en=r["asignado_en"],
            )
        )
    return resultado


def asignar_zona(zona: str, contratista_id: str) -> AsignacionZonaContratista:
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    nuevo_id = str(uuid.uuid4())
    sb.from_("asignaciones_zona_contratista").insert(
        {"id": nuevo_id, "zona": zona, "contratista_id": contratista_id, "asignado_en": ahora}
    ).execute()
    res = (
        sb.from_("asignaciones_zona_contratista")
        .select("*, perfiles(nombre)")
        .eq("id", nuevo_id)
        .single()
        .execute()
    )
    r = res.data
    perfil = r.get("perfiles") or {}
    if isinstance(perfil, list):
        perfil = perfil[0] if perfil else {}
    return AsignacionZonaContratista(
        id=r["id"], zona=r["zona"], contratista_id=r["contratista_id"],
        contratista_nombre=perfil.get("nombre", ""), asignado_en=r["asignado_en"],
    )


def eliminar_asignacion(asignacion_id: str) -> None:
    sb = get_supabase()
    sb.from_("asignaciones_zona_contratista").delete().eq("id", asignacion_id).execute()
