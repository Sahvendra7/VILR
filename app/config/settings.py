from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "VILR 2.0"
    redis_url: str = "redis://redis:6379/0"
    opa_url: str = "http://opa:8181"
    llm_provider: str = "mock"
    anthropic_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
