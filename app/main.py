from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    asistente,
    auth,
    contratistas,
    health,
    incidentes_urbanos,
    inspecciones,
    perfiles,
    poligonos,
    rutas,
    ubicaciones,
    vialidad,
)

app = FastAPI(title="Releva Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:4173",   # Vite preview
        "https://releva-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(poligonos.router)
app.include_router(inspecciones.router)
app.include_router(perfiles.router)
app.include_router(ubicaciones.router)
app.include_router(incidentes_urbanos.router)
app.include_router(vialidad.router)
app.include_router(rutas.router)
app.include_router(contratistas.router)
app.include_router(asistente.router)


@app.get("/")
def root():
    return {"message": "Releva Backend", "docs": "/docs"}
