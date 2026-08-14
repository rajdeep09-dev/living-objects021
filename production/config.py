"""Environment-driven production configuration.

The application is intentionally configured through environment variables so
the same image can run in Compose, Kubernetes, or a managed cloud service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    environment: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./state/living_objects.sqlite3"
    redis_url: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_ttl_seconds: int = 3600
    operator_username: str = "operator"
    operator_password: str = "living-objects"
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)
    organism_limit: int = 10_000
    event_buffer_size: int = 500

    @classmethod
    def from_env(cls) -> "Settings":
        raw_database_url = os.getenv("LIVING_OBJECTS_DATABASE_URL") or os.getenv(
            "DATABASE_URL", cls.database_url
        )
        # Some hosting shells inject a database URL for an unrelated service.
        # Do not let that value prevent importing the control plane; production
        # deployments should provide an explicit SQLite or PostgreSQL URL.
        if not raw_database_url.startswith(("sqlite:///", "postgresql://", "postgres://")):
            raw_database_url = cls.database_url
        origins = tuple(
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        )
        return cls(
            environment=os.getenv("APP_ENV", "dev"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            database_url=raw_database_url,
            redis_url=os.getenv("REDIS_URL", ""),
            jwt_secret=os.getenv("JWT_SECRET", cls.jwt_secret),
            jwt_ttl_seconds=int(os.getenv("JWT_TTL_SECONDS", "3600")),
            operator_username=os.getenv("LO_OPERATOR_USERNAME", cls.operator_username),
            operator_password=os.getenv("LO_OPERATOR_PASSWORD", cls.operator_password),
            cors_origins=origins,
            organism_limit=int(os.getenv("ORGANISM_LIMIT", "10000")),
            event_buffer_size=int(os.getenv("EVENT_BUFFER_SIZE", "500")),
        )

    def ensure_local_state(self) -> None:
        """Create the parent directory for local SQLite state if applicable."""
        if self.database_url.startswith("sqlite:///"):
            path = Path(self.database_url.removeprefix("sqlite:///"))
            if path.parent != Path("."):
                path.parent.mkdir(parents=True, exist_ok=True)
