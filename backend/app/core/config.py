from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Wafer Intelligence"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/map-test.db"
    static_dir: str = "/app/static"

    admin_username: str = "admin"
    admin_password: str = ""
    admin_session_secret: str = ""
    admin_session_max_age_seconds: int = 12 * 60 * 60
    admin_cookie_secure: bool = False

    upload_max_files: int = 2
    upload_max_file_bytes: int = 2 * 1024 * 1024
    upload_max_total_bytes: int = 4 * 1024 * 1024
    upload_max_lines: int = 5000
    upload_max_line_bytes: int = 8192
    upload_allowed_extensions: str = ".pat,.cp1,.cp,.map,.txt"

    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_settings_admin_token: str = ""
    llm_timeout_seconds: float = 45.0
    llm_max_retries: int = 2
    llm_max_output_tokens: int = 8192

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def admin_auth_configured(self) -> bool:
        return bool(
            self.admin_username.strip()
            and self.admin_password
            and len(self.admin_session_secret) >= 32
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
