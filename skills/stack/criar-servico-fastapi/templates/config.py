# Caminho relativo: src/<pacote>/config.py
# Modelo da skill criar-servico-fastapi: configuração do ambiente, falhando cedo.
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="forbid")

    # SEM valor padrão: faltou a variável, o serviço não sobe. É o comportamento desejado —
    # subir com configuração de desenvolvimento em produção é pior que não subir.
    banco_url: PostgresDsn
    chave_jwt: str = Field(min_length=32)

    # Estes podem ter padrão, porque o padrão é o seguro.
    debug: bool = False
    origens_cors: list[str] = []          # explícito; nunca ["*"] com credenciais
    timeout_externo_s: float = 5.0        # toda chamada externa tem tempo limite


@lru_cache
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
