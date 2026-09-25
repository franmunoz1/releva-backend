from __future__ import annotations
from typing import Optional
from app.models.base import APIModel


class EventoIncidenteUrbano(APIModel):
    estado_anterior: Optional[str] = None
    estado_nuevo: str
    nota: Optional[str] = None
    cambiado_por: str
    cambiado_por_nombre: str
    cambiado_en: str


class IncidenteUrbano(APIModel):
    id: str
    numero: int
    tipo: str
    estado: str
    lat: float
    lng: float
    origen_ubicacion: str
    observacion: Optional[str] = None
    referencia: Optional[str] = None
    creado_por: str
    creado_por_nombre: str
    creado_en: str
    actualizado_en: str
    fotos: list[str] = []
    eventos: list[EventoIncidenteUrbano] = []
