from __future__ import annotations
from typing import Optional
from app.models.base import APIModel


class Coordenada(APIModel):
    lat: float
    lng: float


class Poligono(APIModel):
    id: str
    nombre: str
    tipo: str
    cuadrante: str
    jurisdiccion: str
    acta_municipal: bool
    avance_obra: float
    estado: str
    observaciones: str
    municipio: str
    coordenadas: list[Coordenada]
    inspector_asignado_id: Optional[str] = None
    inspector_asignado_nombre: Optional[str] = None
    asignado_en: Optional[str] = None
    listo_para_encender: bool = False
    empresa: Optional[str] = None
    seccion: Optional[str] = None
    estado_obra_212: Optional[str] = None
    segmentos: Optional[list[list[Coordenada]]] = None
