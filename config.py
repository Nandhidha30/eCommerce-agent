"""Central configuration — all settings loaded from environment."""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ──────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    @property
    def llm_mode(self) -> str:
        if self.gemini_api_key:
            return "gemini"
        if self.openai_api_key:
            return "openai"
        return "mock"

    # ── Financial Guardrails ─────────────────────────────────
    refund_auto_approve_cap: float = Field(default=150.0, alias="REFUND_AUTO_APPROVE_CAP")
    refund_human_approval_cap: float = Field(default=500.0, alias="REFUND_HUMAN_APPROVAL_CAP")
    max_refunds_rolling_window: int = Field(default=3, alias="MAX_REFUNDS_ROLLING_WINDOW")
    refund_rolling_window_days: int = Field(default=30, alias="REFUND_ROLLING_WINDOW_DAYS")

    # ── Logic Guardrails ─────────────────────────────────────
    max_conversation_turns: int = Field(default=8, alias="MAX_CONVERSATION_TURNS")
    loop_detection_threshold: int = Field(default=3, alias="LOOP_DETECTION_THRESHOLD")
    agent_timeout_seconds: int = Field(default=45, alias="AGENT_TIMEOUT_SECONDS")

    # ── Router ───────────────────────────────────────────────
    intent_confidence_threshold: float = Field(default=0.72, alias="INTENT_CONFIDENCE_THRESHOLD")

    # ── Session ──────────────────────────────────────────────
    session_ttl_seconds: int = Field(default=1800, alias="SESSION_TTL_SECONDS")

    # ── Database ─────────────────────────────────────────────
    database_url: str = Field(default="sqlite:///./nexus.db", alias="DATABASE_URL")

    # ── Audit ────────────────────────────────────────────────
    audit_log_path: str = Field(default="./audit.jsonl", alias="AUDIT_LOG_PATH")

    # ── API ──────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = Field(default="", alias="REDIS_URL")

    # ── Security ─────────────────────────────────────────────
    secret_key: str = Field(default="nexus-dev-secret", alias="SECRET_KEY")

    # ── Vector Store ─────────────────────────────────────────
    vector_store_path: str = Field(default="./nexus_vectors", alias="VECTOR_STORE_PATH")


# Singleton
settings = Settings()
