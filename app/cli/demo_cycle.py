from app.db.session import SessionLocal
from app.services.workflow import run_demo_cycle


if __name__ == "__main__":
    with SessionLocal() as db:
        hypothesis = run_demo_cycle(db)
        print(f"Demo cycle completed: hypothesis_id={hypothesis.id}, status={hypothesis.status.value}")
