from fastapi import FastAPI

from app.api.routes import router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="Shopify Lab MVP")
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
