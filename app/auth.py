import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()

_jwks_cache: dict | None = None


def _get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        res = httpx.get(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")
        res.raise_for_status()
        _jwks_cache = res.json()
    return _jwks_cache


def _find_key(kid: str) -> dict:
    # Intenta con cache; si no encuentra el kid, refresca una vez (rotación de claves)
    for force_refresh in (False, True):
        for key in _get_jwks(force_refresh=force_refresh).get("keys", []):
            if key.get("kid") == kid:
                return key
    raise JWTError(f"Clave pública no encontrada: kid={kid}")


def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "ES256")

        public_key = _find_key(kid) if kid else None
        if public_key is None:
            raise JWTError("Token sin kid")

        payload = jwt.decode(token, public_key, algorithms=[alg], options={"verify_aud": False})

        user_id: str = payload.get("sub", "")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")

        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "rol": payload.get("user_metadata", {}).get("rol"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
