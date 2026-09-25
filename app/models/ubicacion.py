from app.models.base import APIModel


class UbicacionInspector(APIModel):
    usuario_id: str
    nombre: str
    rol: str
    lat: float
    lng: float
    accuracy: float
    actualizado_en: str


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
