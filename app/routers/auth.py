import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.config import settings
from app.routers.base import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(body: LoginBody):
    url = f"{settings.supabase_url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json={"email": body.email, "password": body.password}, headers=headers)

    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    data = res.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }
