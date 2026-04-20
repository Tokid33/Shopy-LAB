import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Shopify Lab MVP")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./shopify_lab.db")

    agent_mode: str = os.getenv("AGENT_MODE", "mock")
    search_provider: str = os.getenv("SEARCH_PROVIDER", "fake")
    fetch_provider: str = os.getenv("FETCH_PROVIDER", "fake")
    llm_provider: str = os.getenv("LLM_PROVIDER", "fake")

    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_base_url: str | None = os.getenv("LLM_BASE_URL")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    search_api_key: str | None = os.getenv("SEARCH_API_KEY")

    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    max_fetch_pages: int = int(os.getenv("MAX_FETCH_PAGES", "5"))
    max_page_text_chars: int = int(os.getenv("MAX_PAGE_TEXT_CHARS", "8000"))

    enable_prompt_tracing: bool = os.getenv("ENABLE_PROMPT_TRACING", "true").lower() == "true"
    enable_raw_artifact_capture: bool = os.getenv("ENABLE_RAW_ARTIFACT_CAPTURE", "true").lower() == "true"

    product_scout_prompt_path: str | None = os.getenv("PRODUCT_SCOUT_PROMPT_PATH")
    supplier_check_prompt_path: str | None = os.getenv("SUPPLIER_CHECK_PROMPT_PATH")


settings = Settings()
