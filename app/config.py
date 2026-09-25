from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Releva Backend"
    debug: bool = False
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    class Config:
        env_file = ".env"


settings = Settings()
