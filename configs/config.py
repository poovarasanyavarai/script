import os
from urllib.parse import urljoin
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CONFIG_STORE_BASE_URL: str = os.getenv("CONFIG_STORE_BASE_URL", "")
    CONFIG_STORE_API_KEY: str = os.getenv("CONFIG_STORE_API_KEY", "")


class ConfigStoreClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-api-key": api_key}

    def _build_url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path.lstrip("/"))
    

settings = Settings()
