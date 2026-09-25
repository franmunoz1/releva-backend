from fastapi import Depends
from pydantic import BaseModel

from app.auth import get_usuario_actual
from app.db.supabase_client import get_supabase
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/asistente", tags=["asistente"])


class PreguntaBody(BaseModel):
    pregunta: str
    contexto: str = ""


@router.post("/preguntar", response_model=dict)
def preguntar(body: PreguntaBody, usuario=Depends(get_usuario_actual)):
    sb = get_supabase()
    # Delega al edge function de Supabase que maneja el asistente IA
    res = sb.functions.invoke(
        "preguntar",
        invoke_options={"body": {"pregunta": body.pregunta, "contexto": body.contexto}},
    )
    return {"respuesta": res.get("respuesta", "")}
