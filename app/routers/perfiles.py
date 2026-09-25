from fastapi import Depends, UploadFile, File

from app.auth import get_usuario_actual
from app.models.perfil import InspectorSeleccionable, Usuario
from app.routers.base import APIRouter
from app.services import perfiles as svc

router = APIRouter(prefix="/api/perfiles", tags=["perfiles"])


@router.get("/me", response_model=Usuario)
def get_perfil_propio(usuario=Depends(get_usuario_actual)):
    return svc.construir_usuario(usuario["id"], usuario["email"])


@router.get("/inspectores", response_model=list[InspectorSeleccionable])
def get_inspectores(usuario=Depends(get_usuario_actual)):
    return svc.listar_inspectores()


@router.get("/contratistas", response_model=list[InspectorSeleccionable])
def get_contratistas(usuario=Depends(get_usuario_actual)):
    return svc.listar_contratistas()


@router.get("", response_model=list[InspectorSeleccionable])
def get_todos(usuario=Depends(get_usuario_actual)):
    return svc.listar_todos()


@router.put("/me/foto", response_model=Usuario)
async def subir_foto(file: UploadFile = File(...), usuario=Depends(get_usuario_actual)):
    contenido = await file.read()
    return await svc.subir_foto(usuario["id"], usuario["email"], contenido, file.content_type or "image/jpeg")


@router.delete("/me/foto", response_model=Usuario)
def eliminar_foto(usuario=Depends(get_usuario_actual)):
    return svc.eliminar_foto(usuario["id"], usuario["email"])
