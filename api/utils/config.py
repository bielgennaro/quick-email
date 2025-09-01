import os
from functools import lru_cache
from typing import Optional, List

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    ai_model: str = Field(
        default="google/gemma-3-270m",
        env="AI_MODEL", 
        description="gemma-3"
    )
    
    classification_prompt: str = Field(
        default="""Você é um assistente especializado em classificar emails corporativos.
        Sua tarefa é classificar emails como PRODUTIVO ou IMPRODUTIVO baseado no conteúdo e intenção.

        PRODUTIVO: Emails com perguntas específicas, solicitações claras, interesse genuíno em produtos/serviços, propostas de negócio, ou que requerem ação específica.

        IMPRODUTIVO: Emails genéricos, spam, promoções não solicitadas, conteúdo vago sem propósito claro, ou que não requerem resposta específica.

        Analise o conteúdo e responda apenas com a classificação.""",
                env="CLASSIFICATION_PROMPT",
                description="Prompt usado para classificação de emails"
    )
    
    debug_mode: bool = Field(
        default=False,
        env="DEBUG_MODE",
        description="Ativa modo debug com informações adicionais"
    )
    
    app_name: str = Field(
        default="Quick Email API",
        env="APP_NAME",
        description="Nome da aplicação"
    )
    
    app_version: str = Field(
        default="1.0.0",
        env="APP_VERSION", 
        description="Versão da aplicação"
    )
    
    allowed_hosts: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS",
        description="Lista de hosts permitidos (separados por vírgula)"
    )

    
    max_content_length: int = Field(
        default=10000000,
        env="MAX_CONTENT_LENGTH",
        description="Tamanho máximo do conteúdo do email em caracteres"
    )
    
    model_cache_size: int = Field(
        default=1,
        env="MODEL_CACHE_SIZE",
        description="Tamanho do cache para instâncias do modelo"
    )
    
    request_timeout: int = Field(
        default=30,
        env="REQUEST_TIMEOUT",
        description="Timeout para requisições em segundos"
    )
    
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Nível de logging (DEBUG, INFO, WARNING, ERROR)"
    )
    
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Formato das mensagens de log"
    )
    
    nltk_data_path: Optional[str] = Field(
        default=None,
        env="NLTK_DATA_PATH",
        description="Caminho personalizado para dados do NLTK"
    )
    
    model_device: str = Field(
        default="cpu",
        env="MODEL_DEVICE",
        description="Dispositivo para execução do modelo (cpu/cuda)"
    )
    
    model_max_tokens: int = Field(
        default=50,
        env="MODEL_MAX_TOKENS",
        description="Número máximo de tokens gerados pelo modelo"
    )
    
    model_temperature: float = Field(
        default=0.3,
        env="MODEL_TEMPERATURE",
        description="Temperatura para geração do modelo (0.0-1.0)"
    )
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level deve ser um de: {valid_levels}')
        return v.upper()
    
    @field_validator("model_temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Temperatura deve estar entre 0.0 e 1.0')
        return v
    
    @field_validator("max_content_length")
    @classmethod
    def validate_content_length(cls, v):
        if v < 1 or v > 100000:
            raise ValueError('Tamanho máximo deve estar entre 1 e 100000 caracteres')
        return v
    
    @field_validator("request_timeout")
    @classmethod
    def validate_timeout(cls, v):
        if v < 1 or v > 300:
            raise ValueError('Timeout deve estar entre 1 e 300 segundos')
        return v
    
    def setup_nltk_data_path(self):
        if self.nltk_data_path:
            import nltk
            nltk.data.path.append(self.nltk_data_path)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    
    # configurar nltk se necessário
    settings.setup_nltk_data_path()
    
    return settings

def reload_settings():
    get_settings.cache_clear()
    return get_settings()
