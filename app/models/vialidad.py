from typing import Optional
from app.models.base import APIModel


class MarcacionVialidad(APIModel):
    id: str
    poligono_id: str
    inspector_id: str
    lat: float
    lng: float
    creada_en: str


class AvanceTramoVialidad(APIModel):
    poligono_id: str
    contratista_id: str
    porcentaje: float
    observacion: Optional[str] = None
    actualizado_en: str


class ArchivoZona(APIModel):
    id: str
    zona: str
    nombre: str
    storage_path: str
    url: str
    subido_por: str
    creado_en: str


class AsignacionZonaContratista(APIModel):
    id: str
    zona: str
    contratista_id: str
    contratista_nombre: str
    asignado_en: str
