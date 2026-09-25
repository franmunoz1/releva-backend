from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Coordenadas
# ---------------------------------------------------------------------------

class Coordenada(APIModel):
    lat: float
    lng: float


# ---------------------------------------------------------------------------
# Polígonos
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Inspecciones
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Perfiles / Usuarios
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Ubicaciones
# ---------------------------------------------------------------------------

class UbicacionInspector(APIModel):
    usuario_id: str
    nombre: str
    rol: str
    lat: float
    lng: float
    accuracy: float
    actualizado_en: str


# ---------------------------------------------------------------------------
# Contratistas
# ---------------------------------------------------------------------------

class VehiculoContratista(APIModel):
    contratista_id: str
    patente: str
    marca: str
    modelo: str
    actualizado_en: str


class UbicacionTrabajoContratista(APIModel):
    contratista_id: str
    nombre_empresa: str
    lat: float
    lng: float
    actualizado_en: str


# ---------------------------------------------------------------------------
# Incidentes urbanos
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Rutas planificadas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Vialidad
# ---------------------------------------------------------------------------

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
