"""Production-safe CORS origin validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class CORSConfig:
    environment: str = "dev"

    def validate_origins(self, origins: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(origin.strip() for origin in origins if origin.strip())
        if not cleaned:
            raise ValueError("at least one CORS origin is required")
        if self.environment.lower() in {"production", "prod"}:
            for origin in cleaned:
                if origin == "*":
                    raise ValueError("Wildcard CORS origin forbidden in production")
                if not origin.startswith("https://"):
                    raise ValueError(f"Non-HTTPS CORS origin forbidden in production: {origin}")
                if "localhost" in origin or "127.0.0.1" in origin:
                    warnings.warn(
                        f"Localhost CORS origin configured in production: {origin}",
                        RuntimeWarning,
                        stacklevel=2,
                    )
        elif "*" in cleaned and len(cleaned) > 1:
            raise ValueError("Wildcard CORS origin cannot be combined with explicit origins")
        return cleaned


__all__ = ["CORSConfig"]
