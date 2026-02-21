import os
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    openai_vision_model: str = Field(default="gpt-4o-mini")

    upload_dir: str = Field(default="uploads")
    max_upload_size_mb: int = Field(default=10)

    app_env: str = Field(default="dev")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="sqlite:///nutribot.db")
    max_tool_rounds: int = Field(default=4, ge=1, le=8)
    requests_per_minute: int = Field(default=60, ge=1)
    frontend_origin: str = Field(default="http://localhost:5173")
    openfoodfacts_base_url: str = Field(default="https://world.openfoodfacts.org/api/v2/search")
    openfoodfacts_user_agent: str = Field(
        default="Nutribot/0.1 (https://github.com/example/nutribot; contact=maintainer@example.com)"
    )
    usda_api_key: str = Field(default="")
    usda_base_url: str = Field(default="https://api.nal.usda.gov/fdc/v1/foods/search")
    openfda_api_key: str = Field(default="")
    openfda_base_url: str = Field(default="https://api.fda.gov/drug/label.json")
    ncbi_api_key: str = Field(default="")
    ncbi_tool: str = Field(default="nutribot")
    ncbi_email: str = Field(default="maintainer@example.com")
    pubmed_esearch_url: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi")
    pubmed_esummary_url: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi")

    @model_validator(mode="after")
    def apply_vercel_defaults(self) -> "Settings":
        # Vercel serverless functions can only write under /tmp.
        if os.getenv("VERCEL") == "1":
            if self.database_url == "sqlite:///nutribot.db":
                self.database_url = "sqlite:////tmp/nutribot.db"
            if self.upload_dir == "uploads":
                self.upload_dir = "/tmp/uploads"
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
