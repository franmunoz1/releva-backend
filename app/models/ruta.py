from __future__ import annotations
from app.models.base import APIModel


class ParadaRuta(APIModel):
    poligono_id: str
    poligono_nombre: str
    orden: int
    visitada: bool


class RutaPlanificada(APIModel):
    inspector_id: str
    inspector_nombre: str
    fecha: str
    paradas: list[ParadaRuta]
    actualizado_en: str
