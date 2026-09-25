from datetime import datetime, timezone
from typing import Optional
from app.db.supabase_client import get_supabase
from app.models.ubicacion import UbicacionTrabajoContratista, VehiculoContratista


def obtener_vehiculo(contratista_id: str) -> Optional[VehiculoContratista]:
    sb = get_supabase()
    res = (
        sb.from_("vehiculos_contratista")
        .select("*")
        .eq("contratista_id", contratista_id)
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


def guardar_vehiculo(contratista_id: str, patente: str, marca: str, modelo: str) -> VehiculoContratista:
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("vehiculos_contratista").upsert(
        {
            "contratista_id": contratista_id,
            "patente": patente,
            "marca": marca,
            "modelo": modelo,
            "actualizado_en": ahora,
        },
        on_conflict="contratista_id",
    ).execute()
    res = (
        sb.from_("vehiculos_contratista")
        .select("*")
        .eq("contratista_id", contratista_id)
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


def listar_ubicaciones_trabajo() -> list[UbicacionTrabajoContratista]:
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


def guardar_ubicacion_trabajo(contratista_id: str, lat: float, lng: float) -> UbicacionTrabajoContratista:
    sb = get_supabase()
    ahora = datetime.now(timezone.utc).isoformat()
    sb.from_("ubicaciones_trabajo_contratista").upsert(
        {
            "contratista_id": contratista_id,
            "lat": lat,
            "lng": lng,
            "actualizado_en": ahora,
        },
        on_conflict="contratista_id",
    ).execute()
    res = (
        sb.from_("ubicaciones_trabajo_contratista")
        .select("*, perfiles(nombre)")
        .eq("contratista_id", contratista_id)
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


def eliminar_ubicacion_trabajo(contratista_id: str) -> None:
    sb = get_supabase()
    sb.from_("ubicaciones_trabajo_contratista").delete().eq("contratista_id", contratista_id).execute()
