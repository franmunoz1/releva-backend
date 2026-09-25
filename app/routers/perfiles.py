from fastapi import Depends, HTTPException, UploadFile, File

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.models.domain import InspectorSeleccionable, Usuario
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/perfiles", tags=["perfiles"])

_AVATAR_BUCKET = "avatares"
_AVATAR_EXPIRACION = 3600


def _firmar_foto(sb, path: str | None) -> str | None:
    if not path:
        return None
    try:
        res = sb.storage.from_(_AVATAR_BUCKET).create_signed_url(path, _AVATAR_EXPIRACION)
        return res.get("signedURL")
    except Exception:
        return None


def _construir_usuario(sb, user_id: str, email: str) -> Usuario:
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


@router.get("/me", response_model=Usuario)
def get_perfil_propio(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    return _construir_usuario(sb, usuario["id"], usuario["email"])


@router.get("/inspectores", response_model=list[InspectorSeleccionable])
def get_inspectores(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").eq("rol", "inspector").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


@router.get("/contratistas", response_model=list[InspectorSeleccionable])
def get_contratistas(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").eq("rol", "contratista").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


@router.get("", response_model=list[InspectorSeleccionable])
def get_todos(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    res = sb.from_("perfiles").select("id, nombre").order("nombre").execute()
    return [InspectorSeleccionable(id=r["id"], nombre=r["nombre"]) for r in res.data]


@router.put("/me/foto", response_model=Usuario)
async def subir_foto(
    file: UploadFile = File(...),
    usuario=Depends(get_usuario_actual),
):
    sb = get_supabase()
    contenido = await file.read()
    path = f"{usuario['id']}/avatar"

    sb.storage.from_(_AVATAR_BUCKET).upload(
        path,
        contenido,
        file_options={"content-type": file.content_type or "image/jpeg", "upsert": "true"},
    )
    sb.from_("perfiles").update({"foto_path": path}).eq("id", usuario["id"]).execute()
    return _construir_usuario(sb, usuario["id"], usuario["email"])


@router.delete("/me/foto", response_model=Usuario)
def eliminar_foto(usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    path = f"{usuario['id']}/avatar"
    try:
        sb.storage.from_(_AVATAR_BUCKET).remove([path])
    except Exception:
        pass
    sb.from_("perfiles").update({"foto_path": None}).eq("id", usuario["id"]).execute()
    return _construir_usuario(sb, usuario["id"], usuario["email"])
