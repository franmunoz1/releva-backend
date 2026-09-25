from typing import Optional
from app.models.base import APIModel


class Usuario(APIModel):
    id: str
    nombre: str
    email: str
    rol: str
    municipio: str
    foto_url: Optional[str] = None


class InspectorSeleccionable(APIModel):
    id: str
    nombre: str
