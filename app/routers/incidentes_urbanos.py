from typing import Optional

from fastapi import Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import EventoIncidenteUrbano, IncidenteUrbano
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/incidentes-urbanos", tags=["incidentes urbanos"])

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


@router.get("", response_model=list[IncidenteUrbano])
def get_incidentes(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("incidentes_urbanos").select(_COLS).order("creado_en", desc=True).execute()
    return [_map(r, sb) for r in res.data]


class CrearIncidenteBody(BaseModel):
    id: str
    tipo: str
    lat: float
    lng: float
    origenUbicacion: str
    observacion: Optional[str] = None
    referencia: Optional[str] = None
    creadoPorNombre: str
    creadoEn: str


@router.post("", response_model=IncidenteUrbano, status_code=201)
def crear_incidente(body: CrearIncidenteBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    sb.from_("incidentes_urbanos").upsert(
        {
            "id": body.id,
            "tipo": body.tipo,
            "estado": "iniciado",
            "lat": body.lat,
            "lng": body.lng,
            "origen_ubicacion": body.origenUbicacion,
            "observacion": body.observacion,
            "referencia": body.referencia,
            "creado_por": usuario["id"],
            "creado_por_nombre": body.creadoPorNombre,
            "creado_en": body.creadoEn,
        },
        on_conflict="id",
        ignore_duplicates=True,
    ).execute()
    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", body.id).single().execute()
    return _map(res.data, sb)


class CambiarEstadoBody(BaseModel):
    estadoNuevo: str
    nota: Optional[str] = None
    cambiadoPorNombre: str
    cambiadoEn: str


@router.patch("/{incidente_id}/estado", response_model=IncidenteUrbano)
def cambiar_estado(incidente_id: str, body: CambiarEstadoBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res_actual = sb.from_("incidentes_urbanos").select("estado").eq("id", incidente_id).single().execute()
    estado_anterior = res_actual.data["estado"]

    sb.from_("incidentes_urbanos").update({"estado": body.estadoNuevo}).eq("id", incidente_id).execute()
    sb.from_("incidentes_urbanos_eventos").insert(
        {
            "incidente_id": incidente_id,
            "estado_anterior": estado_anterior,
            "estado_nuevo": body.estadoNuevo,
            "nota": body.nota,
            "cambiado_por": usuario["id"],
            "cambiado_por_nombre": body.cambiadoPorNombre,
            "cambiado_en": body.cambiadoEn,
        }
    ).execute()

    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", incidente_id).single().execute()
    return _map(res.data, sb)


@router.post("/{incidente_id}/fotos", response_model=IncidenteUrbano)
async def agregar_foto(
    incidente_id: str,
    foto_id: str = Form(...),
    creada_en: str = Form(...),
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    sb = get_supabase()
    contenido = await file.read()
    path = f"{incidente_id}/{foto_id}-{file.filename}"

    sb.storage.from_(_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": file.content_type or "image/jpeg", "upsert": "true"},
    )
    sb.from_("incidentes_urbanos_fotos").insert(
        {"incidente_id": incidente_id, "storage_path": path, "creada_en": creada_en}
    ).execute()

    res = sb.from_("incidentes_urbanos").select(_COLS).eq("id", incidente_id).single().execute()
    return _map(res.data, sb)
