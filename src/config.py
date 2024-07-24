import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# barbatrucco to make .env file path work on windows
current_directory = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(current_directory, "..", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_file_path)

    service_port: int = 8000

    secret_key: SecretStr = "secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    notifications_url: str = "http://localhost:7777/v1/email_service"


settings = Settings()
