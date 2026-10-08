from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:1234567890@localhost:5432/cpcms"
    TEST_DATABASE_URL: str = "postgresql+psycopg://postgres:1234567890@localhost:5432/cpcms_test"
    SECRET_KEY: str = "cpcms-super-secret-key-change-in-production-12345678"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FACULTY_INVITE_CODE: str = "FACULTY2026"
    ALLOWED_EMAIL_DOMAINS: str = ""
    STUDENT_REG_PATTERN: str = r"^[0-9]{2}[A-Z]{3}[0-9]{4}$"
    UPLOAD_DIR: str = "./uploads"
    GITHUB_TOKEN: Optional[str] = None

    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@cpcms.univ.edu"

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_email_domains_list(self) -> List[str]:
        if not self.ALLOWED_EMAIL_DOMAINS:
            return []
        return [d.strip().lower() for d in self.ALLOWED_EMAIL_DOMAINS.split(",") if d.strip()]


settings = Settings()
