from typing import Optional
from fastapi import HTTPException
from app.db.supabase_client import get_supabase
from app.models.poligono import Poligono

_ROLES_EQUIPO = {"inspector", "jefe", "administrador"}

_COLS = (
    "id, nombre, tipo, cuadrante, jurisdiccion, acta_municipal, avance_obra, estado, "
    "observaciones, municipio, coordenadas, inspector_asignado_id, asignado_en, "
    "listo_para_encender, empresa, seccion, estado_obra_212, segmentos, perfiles(nombre)"
)


def _map(row: dict) -> Poligono:
    perfil = row.get("perfiles")
    nombre_inspector = None
    if isinstance(perfil, dict):
        nombre_inspector = perfil.get("nombre")
    elif isinstance(perfil, list) and perfil:
        nombre_inspector = perfil[0].get("nombre")

    return Poligono(
        id=row["id"],
        nombre=row["nombre"],
        tipo=row["tipo"],
        cuadrante=row.get("cuadrante", ""),
        jurisdiccion=row.get("jurisdiccion", "Municipal"),
        acta_municipal=row.get("acta_municipal", False),
        avance_obra=row.get("avance_obra", 0),
        estado=row["estado"],
        observaciones=row.get("observaciones", ""),
        municipio=row.get("municipio", ""),
        coordenadas=row.get("coordenadas", []),
        inspector_asignado_id=row.get("inspector_asignado_id"),
        inspector_asignado_nombre=nombre_inspector,
        asignado_en=row.get("asignado_en"),
        listo_para_encender=row.get("listo_para_encender", False),
        empresa=row.get("empresa"),
        seccion=row.get("seccion"),
        estado_obra_212=row.get("estado_obra_212"),
        segmentos=row.get("segmentos"),
    )


def _fetch_one(poligono_id: str) -> Poligono:
    sb = get_supabase()
    res = sb.from_("poligonos").select(_COLS).eq("id", poligono_id).single().execute()
    return _map(res.data)


def listar() -> list[Poligono]:
    sb = get_supabase()
    res = sb.from_("poligonos").select(_COLS).eq("activo", True).order("nombre").execute()
    return [_map(r) for r in res.data]


def obtener_por_id(poligono_id: str) -> Poligono:
    sb = get_supabase()
    res = (
        sb.from_("poligonos")
        .select(_COLS)
        .eq("id", poligono_id)
        .eq("activo", True)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Polígono no encontrado")
    return _map(res.data)


def actualizar_avance(poligono_id: str, avance: float, rol: Optional[str]) -> Poligono:
    if rol not in _ROLES_EQUIPO:
        raise HTTPException(status_code=403, detail="Sin permiso para actualizar el avance de obra")
    sb = get_supabase()
    sb.from_("poligonos").update({"avance_obra": avance}).eq("id", poligono_id).execute()
    return _fetch_one(poligono_id)


def asignar_trabajo(poligono_id: str, inspector_id: Optional[str]) -> Poligono:
    sb = get_supabase()
    sb.rpc("asignar_trabajo", {"p_poligono_id": poligono_id, "p_inspector_id": inspector_id}).execute()
    return _fetch_one(poligono_id)


def marcar_listo_encender(poligono_id: str, valor: bool) -> Poligono:
    sb = get_supabase()
    sb.rpc("marcar_listo_para_encender", {"p_poligono_id": poligono_id, "p_valor": valor}).execute()
    return _fetch_one(poligono_id)


def asignar_empresa(poligono_id: str, empresa: Optional[str]) -> Poligono:
    sb = get_supabase()
    sb.rpc("asignar_empresa", {"p_poligono_id": poligono_id, "p_empresa": empresa}).execute()
    return _fetch_one(poligono_id)


def asignar_estado(poligono_id: str, estado: Optional[str], estado_obra_212: Optional[str]) -> Poligono:
    sb = get_supabase()
    sb.rpc(
        "asignar_estado",
        {"p_poligono_id": poligono_id, "p_estado": estado, "p_estado_obra_212": estado_obra_212},
    ).execute()
    return _fetch_one(poligono_id)


def asignar_estado_vialidad(poligono_id: str, estado_obra_212: Optional[str]) -> Poligono:
    sb = get_supabase()
    sb.rpc(
        "asignar_estado_obra_tramo_vialidad",
        {"p_poligono_id": poligono_id, "p_estado_obra_212": estado_obra_212},
    ).execute()
    return _fetch_one(poligono_id)


def renombrar(poligono_id: str, nombre: str) -> Poligono:
    sb = get_supabase()
    sb.rpc("renombrar_poligono", {"p_poligono_id": poligono_id, "p_nombre": nombre}).execute()
    return _fetch_one(poligono_id)
