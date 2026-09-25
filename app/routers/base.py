from typing import Any

from fastapi.routing import APIRouter as _FastAPIRouter


class APIRouter(_FastAPIRouter):
    """Router que serializa responses usando aliases (camelCase) por defecto."""

    def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
        kwargs.setdefault("response_model_by_alias", True)
        super().add_api_route(path, endpoint, **kwargs)
