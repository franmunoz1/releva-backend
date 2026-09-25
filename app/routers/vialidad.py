from typing import Optional

from fastapi import Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import (
    ArchivoZona,
    AsignacionZonaContratista,
    AvanceTramoVialidad,
    MarcacionVialidad,
)
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/vialidad", tags=["vialidad"])

_ARCHIVOS_BUCKET = "archivos-zona"
_ARCHIVOS_EXPIRACION = 3600


# ---------------------------------------------------------------------------
# Marcaciones
# ---------------------------------------------------------------------------

@router.get("/marcaciones/{zona}", response_model=list[MarcacionVialidad])
def get_marcaciones(zona: str, usuario=Depends(get_usuario_actual)):
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


class MarcacionBody(BaseModel):
    id: str
    poligonoId: str
    zona: str
    lat: float
    lng: float
    creadaEn: str


@router.post("/marcaciones", response_model=MarcacionVialidad, status_code=201)
def agregar_marcacion(body: MarcacionBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("marcaciones_vialidad").upsert(
        {
            "id": body.id,
            "poligono_id": body.poligonoId,
            "zona": body.zona,
            "inspector_id": usuario["id"],
            "lat": body.lat,
            "lng": body.lng,
            "creada_en": body.creadaEn,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    res = sb.from_("marcaciones_vialidad").select("*").eq("id", body.id).single().execute()
    r = res.data
    return MarcacionVialidad(
        id=r["id"], poligono_id=r["poligono_id"], inspector_id=r["inspector_id"],
        lat=r["lat"], lng=r["lng"], creada_en=r["creada_en"],
    )


@router.delete("/marcaciones/{marcacion_id}", response_model=dict)
def eliminar_marcacion(marcacion_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("marcaciones_vialidad").delete().eq("id", marcacion_id).execute()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Avance de tramo
# ---------------------------------------------------------------------------

@router.get("/avance/{poligono_id}", response_model=Optional[AvanceTramoVialidad])
def get_avance(poligono_id: str, usuario=Depends(get_usuario_actual)):
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


class AvanceBody(BaseModel):
    poligonoId: str
    porcentaje: float
    observacion: Optional[str] = None


@router.post("/avance", response_model=AvanceTramoVialidad)
def guardar_avance(body: AvanceBody, usuario=Depends(get_usuario_actual)):
    from datetime import datetime, timezone
    sb = get_supabase()
    sb.from_("avance_tramo_vialidad").upsert(
        {
            "poligono_id": body.poligonoId,
            "contratista_id": usuario["id"],
            "porcentaje": body.porcentaje,
            "observacion": body.observacion,
            "actualizado_en": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="poligono_id",
    ).execute()
    res = sb.from_("avance_tramo_vialidad").select("*").eq("poligono_id", body.poligonoId).single().execute()
    r = res.data
    return AvanceTramoVialidad(
        poligono_id=r["poligono_id"],
        contratista_id=r["contratista_id"],
        porcentaje=r["porcentaje"],
        observacion=r.get("observacion"),
        actualizado_en=r["actualizado_en"],
    )


@router.delete("/avance/{poligono_id}", response_model=dict)
def deshacer_avance(poligono_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("deshacer_avance_tramo", {"p_poligono_id": poligono_id}).execute()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Archivos de zona
# ---------------------------------------------------------------------------

@router.get("/archivos/{zona}", response_model=list[ArchivoZona])
def get_archivos(zona: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("archivos_zona_vialidad").select("*").eq("zona", zona).order("creado_en", desc=True).execute()
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


@router.post("/archivos", response_model=ArchivoZona, status_code=201)
async def subir_archivo(
    archivo_id: str = Form(...),
    zona: str = Form(...),
    nombre: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    from datetime import datetime, timezone
    sb = get_supabase()
    contenido = await file.read()
    path = f"{zona}/{archivo_id}-{nombre}"
    sb.storage.from_(_ARCHIVOS_BUCKET).upload(
        path, contenido,
        file_options={"content-type": file.content_type or "application/octet-stream", "upsert": "true"},
    )
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("archivos_zona_vialidad").insert(
        {"id": archivo_id, "zona": zona, "nombre": nombre, "storage_path": path,
         "subido_por": usuario["id"], "creado_en": ahora}
    ).execute()
    url_res = sb.storage.from_(_ARCHIVOS_BUCKET).create_signed_url(path, _ARCHIVOS_EXPIRACION)
    return ArchivoZona(
        id=archivo_id, zona=zona, nombre=nombre, storage_path=path,
        url=url_res.get("signedURL", ""), subido_por=usuario["id"], creado_en=ahora,
    )


@router.delete("/archivos/{archivo_id}", response_model=dict)
def eliminar_archivo(archivo_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("archivos_zona_vialidad").select("storage_path").eq("id", archivo_id).single().execute()
    sb.from_("archivos_zona_vialidad").delete().eq("id", archivo_id).execute()
    try:
        sb.storage.from_(_ARCHIVOS_BUCKET).remove([res.data["storage_path"]])
    except Exception:
        pass
    return {"ok": True}


# ---------------------------------------------------------------------------
# Asignaciones de zona a contratistas
# ---------------------------------------------------------------------------

@router.get("/asignaciones", response_model=list[AsignacionZonaContratista])
def get_asignaciones(usuario=Depends(get_usuario_actual)):
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


class AsignacionBody(BaseModel):
    zona: str
    contratistaId: str


@router.post("/asignaciones", response_model=AsignacionZonaContratista, status_code=201)
def asignar_zona(body: AsignacionBody, usuario=Depends(get_usuario_actual)):
    from datetime import datetime, timezone
    import uuid
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    nuevo_id = str(uuid.uuid4())
    sb.from_("asignaciones_zona_contratista").insert(
        {"id": nuevo_id, "zona": body.zona, "contratista_id": body.contratistaId, "asignado_en": ahora}
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


@router.delete("/asignaciones/{asignacion_id}", response_model=dict)
def eliminar_asignacion(asignacion_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("asignaciones_zona_contratista").delete().eq("id", asignacion_id).execute()
    return {"ok": True}
