from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import (
    Fotografia,
    Inspeccion,
    InspeccionEnCursoResumen,
    InspeccionRecienteResumen,
    Observacion,
    ValoresRestauracion,
)
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/inspecciones", tags=["inspecciones"])

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


def _fetch_one(sb, inspeccion_id: str) -> Inspeccion:
    res = sb.from_("inspecciones").select(_COLS).eq("id", inspeccion_id).single().execute()
    return _map(res.data, sb)


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

@router.get("", response_model=list[Inspeccion])
def get_inspecciones(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("inspecciones").select(_COLS).order("fecha_inicio", desc=True).execute()
    return [_map(r, sb) for r in res.data]


@router.get("/en-curso-resumen", response_model=list[InspeccionEnCursoResumen])
def get_en_curso_resumen(usuario=Depends(get_usuario_actual)):
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


@router.get("/finalizadas-hoy", response_model=dict)
def contar_finalizadas_hoy(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    res = (
        sb.from_("inspecciones")
        .select("id", count="exact")
        .eq("estado", "finalizada")
        .gte("fecha_fin", inicio.isoformat())
        .execute()
    )
    return {"count": res.count or 0}


@router.get("/recientes", response_model=list[InspeccionRecienteResumen])
def get_recientes(limite: int = 10, usuario=Depends(get_usuario_actual)):
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


@router.get("/en-curso/{poligono_id}/{inspector_id}", response_model=Optional[Inspeccion])
def get_en_curso_por_poligono(poligono_id: str, inspector_id: str, usuario=Depends(get_usuario_actual)):
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


@router.get("/conflicto/{poligono_id}", response_model=Optional[dict])
def get_conflicto(poligono_id: str, inspector_id_propio: str, usuario=Depends(get_usuario_actual)):
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


@router.get("/{inspeccion_id}/restauracion", response_model=ValoresRestauracion)
def get_restauracion(inspeccion_id: str, poligono_id: str, usuario=Depends(get_usuario_actual)):
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


@router.get("/{inspeccion_id}", response_model=Optional[Inspeccion])
def get_por_id(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("inspecciones").select(_COLS).eq("id", inspeccion_id).maybe_single().execute()
    if not res.data:
        return None
    return _map(res.data, sb)


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------

class IniciarBody(BaseModel):
    inspeccionId: str
    poligonoId: str
    poligonoNombre: str
    inspectorId: str
    inspectorNombre: str
    fechaInicio: str


@router.post("", response_model=Inspeccion, status_code=201)
def iniciar_inspeccion(body: IniciarBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("inspecciones").upsert(
        {
            "id": body.inspeccionId,
            "poligono_id": body.poligonoId,
            "poligono_nombre": body.poligonoNombre,
            "inspector_id": body.inspectorId,
            "inspector_nombre": body.inspectorNombre,
            "fecha_inicio": body.fechaInicio,
            "estado": "en_curso",
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    return _fetch_one(sb, body.inspeccionId)


class ObservacionBody(BaseModel):
    observacionId: str
    texto: str
    creadaEn: str


@router.post("/{inspeccion_id}/observacion", response_model=Inspeccion)
def agregar_observacion(inspeccion_id: str, body: ObservacionBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("observaciones").upsert(
        {
            "id": body.observacionId,
            "inspeccion_id": inspeccion_id,
            "texto": body.texto,
            "creada_en": body.creadaEn,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    return _fetch_one(sb, inspeccion_id)


@router.post("/{inspeccion_id}/fotografias", response_model=Inspeccion)
async def agregar_fotografia(
    inspeccion_id: str,
    fotografia_id: str = Form(...),
    nombre_archivo: str = Form(...),
    creada_en: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    sb = get_supabase()
    contenido = await file.read()
    path = f"{inspeccion_id}/{fotografia_id}-{nombre_archivo}"

    sb.storage.from_(_FOTO_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": file.content_type or "image/jpeg", "upsert": "true"},
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
    return _fetch_one(sb, inspeccion_id)


class FinalizarBody(BaseModel):
    observacionFinal: str
    estado: str
    actaMunicipal: bool
    empresa: Optional[str] = None
    estadoObra212: Optional[str] = None
    fechaFin: str
    tiempoTotalSegundos: int


@router.post("/{inspeccion_id}/finalizar", response_model=Inspeccion)
def finalizar(inspeccion_id: str, body: FinalizarBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc(
        "finalizar_inspeccion",
        {
            "p_inspeccion_id": inspeccion_id,
            "p_observacion_final": body.observacionFinal,
            "p_estado": body.estado,
            "p_acta_municipal": body.actaMunicipal,
            "p_fecha_fin": body.fechaFin,
            "p_tiempo_total_segundos": body.tiempoTotalSegundos,
            "p_empresa": body.empresa,
            "p_estado_obra_212": body.estadoObra212,
        },
    ).execute()
    return _fetch_one(sb, inspeccion_id)


@router.post("/{inspeccion_id}/cancelar", response_model=dict)
def cancelar(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.rpc("cancelar_inspeccion", {"p_inspeccion_id": inspeccion_id}).execute()
    return {"ok": True}


@router.delete("/{inspeccion_id}", response_model=dict)
def eliminar(inspeccion_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.rpc("eliminar_inspeccion", {"p_inspeccion_id": inspeccion_id}).execute()
    paths = [p["storage_path"] for p in (res.data or [])]
    if paths:
        sb.storage.from_(_FOTO_BUCKET).remove(paths)
    return {"ok": True}


@router.delete("/{inspeccion_id}/fotografias/{fotografia_id}", response_model=Inspeccion)
def eliminar_fotografia(inspeccion_id: str, fotografia_id: str, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("fotografias").select("storage_path").eq("id", fotografia_id).single().execute()
    path = res.data["storage_path"]
    sb.from_("fotografias").delete().eq("id", fotografia_id).execute()
    sb.storage.from_(_FOTO_BUCKET).remove([path])
    return _fetch_one(sb, inspeccion_id)
