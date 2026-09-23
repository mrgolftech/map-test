from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Wafer Intelligence"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/map-test.db"
    static_dir: str = "/app/static"

    upload_max_files: int = 2
    upload_max_file_bytes: int = 2 * 1024 * 1024
    upload_max_total_bytes: int = 4 * 1024 * 1024
    upload_max_lines: int = 5000
    upload_max_line_bytes: int = 8192
    upload_allowed_extensions: str = ".pat,.cp1,.cp,.map,.txt"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_upload_extensions(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.upload_allowed_extensions.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
