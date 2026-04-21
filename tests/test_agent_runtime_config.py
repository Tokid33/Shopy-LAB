from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AgentRun
from app.models.enums import AgentRunStatus
from app.schemas.agents import ProductScoutRunRequest
from app.services.agents.providers import (
    FakeSearchProvider,
    ProviderResolutionError,
    get_search_provider,
    provider_health,
)
from app.services.agents.services import AgentExecutionError, ProductScoutAgentService


def test_provider_factory_mock_mode_returns_fake() -> None:
    provider = get_search_provider(force_mode="mock")
    assert isinstance(provider, FakeSearchProvider)


def test_provider_factory_real_mode_requires_key() -> None:
    old_provider = settings.search_provider
    old_key = settings.search_api_key
    settings.search_provider = "brave"
    settings.search_api_key = None
    try:
        with pytest.raises(ProviderResolutionError):
            get_search_provider(force_mode="real")
    finally:
        settings.search_provider = old_provider
        settings.search_api_key = old_key


def test_provider_health_endpoint_reports_missing_env() -> None:
    old_mode = settings.agent_mode
    old_search = settings.search_provider
    old_llm = settings.llm_provider
    old_search_key = settings.search_api_key
    old_llm_key = settings.llm_api_key
    old_llm_url = settings.llm_base_url

    settings.agent_mode = "real"
    settings.search_provider = "brave"
    settings.llm_provider = "openai_compatible"
    settings.search_api_key = None
    settings.llm_api_key = None
    settings.llm_base_url = None

    try:
        health = provider_health()
        assert health["mode"] == "real"
        assert "SEARCH_API_KEY" in health["missing_env"]
        assert "LLM_API_KEY" in health["missing_env"]
        assert health["real_mode_ready"] is False
    finally:
        settings.agent_mode = old_mode
        settings.search_provider = old_search
        settings.llm_provider = old_llm
        settings.search_api_key = old_search_key
        settings.llm_api_key = old_llm_key
        settings.llm_base_url = old_llm_url


def test_real_endpoint_misconfiguration_controlled_failure() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def _get_db():
        with Session(engine) as db:
            yield db

    old_search = settings.search_provider
    old_key = settings.search_api_key
    settings.search_provider = "brave"
    settings.search_api_key = None

    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app)
    try:
        response = client.post(
            "/agents/product-scout/run-real",
            json={"market": "US", "categories": ["kitchen"], "limit": 1},
        )
        assert response.status_code == 400
        assert "SEARCH_API_KEY" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        settings.search_provider = old_search
        settings.search_api_key = old_key


def test_structured_validation_failure_marks_run_failed() -> None:
    class BadExtractor:
        name = "bad"

        def extract_product_candidate(self, raw_text: str, prompt: str) -> dict:
            return {"product_name": "", "signal": "purple"}

        def extract_supplier_candidate(self, raw_text: str, prompt: str) -> dict:
            return {}

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        service = ProductScoutAgentService(db, mode="mock", extractor=BadExtractor())
        with pytest.raises(AgentExecutionError):
            service.run(ProductScoutRunRequest(market="US", categories=["kitchen"], limit=1))

        run = db.query(AgentRun).order_by(AgentRun.id.desc()).first()
        assert run is not None
        assert run.status == AgentRunStatus.failed
