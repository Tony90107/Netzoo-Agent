"""Fail-closed environment settings for the trace collector."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr


__all__ = ["CollectorSettings"]


class CollectorSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    credential_pepper: SecretStr
    agent_key: SecretStr
    admin_key: SecretStr
    database_url: str = "sqlite+pysqlite:///./netzoo-observer.db"
    object_store_bucket: str = "netzoo-traces"
    share_default_ttl_seconds: int = Field(default=604_800, ge=60, le=2_592_000)
    max_event_batch: int = Field(default=100, ge=1, le=100)
    max_blob_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    share_cookie_secure: bool = True

    @classmethod
    def from_environment(cls) -> "CollectorSettings":
        required = {
            "credential_pepper": "NETZOO_OBSERVER_CREDENTIAL_PEPPER",
            "agent_key": "NETZOO_OBSERVER_AGENT_KEY",
            "admin_key": "NETZOO_OBSERVER_ADMIN_KEY",
        }
        values: dict[str, object] = {}
        for field_name, environment_name in required.items():
            value = os.environ.get(environment_name, "")
            if len(value.encode("utf-8")) < 32:
                raise ValueError(
                    f"{environment_name} must contain at least 32 UTF-8 bytes"
                )
            values[field_name] = SecretStr(value)
        values["database_url"] = os.environ.get(
            "NETZOO_OBSERVER_DATABASE_URL",
            cls.model_fields["database_url"].default,
        )
        values["object_store_bucket"] = os.environ.get(
            "NETZOO_OBSERVER_OBJECT_BUCKET",
            cls.model_fields["object_store_bucket"].default,
        )
        secure_cookie = os.environ.get(
            "NETZOO_OBSERVER_SHARE_COOKIE_SECURE", "true"
        ).casefold()
        if secure_cookie not in {"true", "false"}:
            raise ValueError("NETZOO_OBSERVER_SHARE_COOKIE_SECURE must be true or false")
        values["share_cookie_secure"] = secure_cookie == "true"
        return cls.model_validate(values)
