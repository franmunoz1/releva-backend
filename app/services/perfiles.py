from typing import Optional
from fastapi import HTTPException
from app.db.supabase_client import get_supabase
from app.models.perfil import InspectorSeleccionable, Usuario

_AVATAR_BUCKET = "avatares"
_AVATAR_EXPIRACION = 3600


def _firmar_foto(sb, path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        res = sb.storage.from_(_AVATAR_BUCKET).create_signed_url(path, _AVATAR_EXPIRACION)
        return res.get("signedURL")
    except Exception:
        return None


def construir_usuario(user_id: str, email: str) -> Usuario:
    sb = get_supabase()
    res = (
        sb.from_("perfiles")
        .select("nombre, rol, municipio, foto_path")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    p = res.data
    return Usuario(
        id=user_id,
        email=email,
        nombre=p["nombre"],
        rol=p["rol"],
        municipio=p["municipio"],
        foto_url=_firmar_foto(sb, p.get("foto_path")),
    )


def listar_inspectores() -> list[InspectorSeleccionable]:
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").eq("rol", "inspector").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


def listar_contratistas() -> list[InspectorSeleccionable]:
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").eq("rol", "contratista").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


def listar_todos() -> list[InspectorSeleccionable]:
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


async def subir_foto(user_id: str, email: str, contenido: bytes, content_type: str) -> Usuario:
    sb = get_supabase()
    path = f"{user_id}/avatar"
    sb.storage.from_(_AVATAR_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": content_type or "image/jpeg", "upsert": "true"},
    )
    sb.from_("perfiles").update({"foto_path": path}).eq("id", user_id).execute()
    return construir_usuario(user_id, email)


def eliminar_foto(user_id: str, email: str) -> Usuario:
    sb = get_supabase()
    path = f"{user_id}/avatar"
    try:
        sb.storage.from_(_AVATAR_BUCKET).remove([path])
    except Exception:
        pass
    sb.from_("perfiles").update({"foto_path": None}).eq("id", user_id).execute()
    return construir_usuario(user_id, email)
