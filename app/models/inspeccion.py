from __future__ import annotations
from typing import Optional
from app.models.base import APIModel


class Observacion(APIModel):
    id: str
    texto: str
    creada_en: str


class Fotografia(APIModel):
    id: str
    nombre_archivo: str
    preview_url: str
    creada_en: str


class Inspeccion(APIModel):
    id: str
    poligono_id: str
    poligono_nombre: str
    inspector_id: str
    inspector_nombre: str
    fecha_inicio: str
    fecha_fin: Optional[str] = None
    tiempo_total_segundos: Optional[int] = None
    observaciones: list[Observacion] = []
    observacion_final: Optional[str] = None
    fotografias: list[Fotografia] = []
    estado: str
    estado_resultante: Optional[str] = None


class InspeccionEnCursoResumen(APIModel):
    id: str
    poligono_id: str
    poligono_nombre: str
    inspector_id: str
    fecha_inicio: str


class InspeccionRecienteResumen(APIModel):
    id: str
    poligono_nombre: str
    inspector_nombre: str
    fecha_fin: str
    estado_resultante: str
    avance_obra_resultante: float


class ValoresRestauracion(APIModel):
    avance_obra: float
    estado: str
    acta_municipal: bool
