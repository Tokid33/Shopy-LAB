from app.db.session import SessionLocal
from app.services.workflow import run_demo_cycle


if __name__ == "__main__":
    with SessionLocal() as db:
        run_demo_cycle(db)
        print("Seed data created via demo cycle")
