from datetime import datetime, timezone
from app.db.supabase_client import get_supabase
from app.models.ubicacion import UbicacionInspector, UbicacionTrabajoContratista


def listar() -> list[UbicacionInspector]:
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


def actualizar(usuario_id: str, lat: float, lng: float, accuracy: float) -> None:
    sb = get_supabase()
    sb.from_("ubicaciones_actuales").upsert(
        {
            "usuario_id": usuario_id,
            "lat": lat,
            "lng": lng,
            "accuracy": accuracy,
            "actualizado_en": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="usuario_id",
    ).execute()


def eliminar(usuario_id: str) -> None:
    sb = get_supabase()
    sb.from_("ubicaciones_actuales").delete().eq("usuario_id", usuario_id).execute()


def listar_contratistas() -> list[UbicacionTrabajoContratista]:
    sb = get_supabase()
    res = (
        sb.from_("ubicaciones_trabajo_contratista")
        .select("contratista_id, lat, lng, actualizado_en, perfiles(nombre)")
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
