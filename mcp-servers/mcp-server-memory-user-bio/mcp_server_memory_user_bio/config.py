from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    storage_root: str = ".data"


settings = Settings()
