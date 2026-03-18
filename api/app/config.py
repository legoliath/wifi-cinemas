from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: List[str] = ["http://localhost:8081"]
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wifi_cinemas"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/wifi_cinemas"
    redis_url: str = "redis://localhost:6379/0"
    firebase_project_id: str = ""
    firebase_service_account_path: str = "./firebase-service-account.json"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    unifi_controller_url: str = "https://192.168.1.1:8443"
    unifi_username: str = "admin"
    unifi_password: str = ""
    unifi_site: str = "default"
    peplink_ic2_api_url: str = "https://api.ic2.peplink.com"
    peplink_client_id: str = ""
    peplink_client_secret: str = ""
    starlink_dish_address: str = "192.168.100.1:9200"
    fcm_server_key: str = ""
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
