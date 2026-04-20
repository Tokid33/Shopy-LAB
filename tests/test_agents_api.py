from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import AgentRun
from app.models.enums import AgentRunStatus


def _override_get_db(engine):
    def _get_db():
        with Session(engine) as db:
            yield db

    return _get_db


def test_product_scout_and_supplier_check_flow() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    app.dependency_overrides[get_db] = _override_get_db(engine)
    client = TestClient(app)

    scout_response = client.post(
        "/agents/product-scout/run",
        json={"market": "US", "categories": ["kitchen"], "limit": 2, "cycle_id": None},
    )
    assert scout_response.status_code == 200
    scout_data = scout_response.json()
    assert scout_data["agent_type"] == "product_scout"
    assert scout_data["status"] == "completed"

    run_lookup = client.get(f"/agents/runs/{scout_data['run_id']}")
    assert run_lookup.status_code == 200
    assert run_lookup.json()["status"] == "completed"

    supplier_response = client.post(
        "/agents/supplier-check/run",
        json={
            "shortlist_items": [
                {
                    "product_name": "Demo Product",
                    "target_price": 39,
                    "cost_of_goods": 11,
                    "shipping_cost": 4,
                }
            ],
            "cycle_id": None,
        },
    )
    assert supplier_response.status_code == 200
    supplier_data = supplier_response.json()
    assert supplier_data["agent_type"] == "supplier_check"
    assert supplier_data["status"] == "completed"
    assert supplier_data["final_recommendation"] in {"go_to_site", "reserve", "fail"}

    app.dependency_overrides.clear()


def test_agent_run_is_persisted_with_completed_status() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        from app.schemas.agents import ProductScoutRunRequest
        from app.services.agents.services import ProductScoutAgentService

        service = ProductScoutAgentService(db)
        response = service.run(ProductScoutRunRequest(market="US", categories=["wellness"], limit=1, cycle_id=None))

        run = db.get(AgentRun, response.run_id)
        assert run is not None
        assert run.status == AgentRunStatus.completed


def test_backward_compat_demo_cycle_endpoint_still_works() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    app.dependency_overrides[get_db] = _override_get_db(engine)
    client = TestClient(app)

    response = client.post("/demo-cycle")
    assert response.status_code == 200
    data = response.json()
    assert "hypothesis_id" in data
    assert "status" in data

    app.dependency_overrides.clear()
