from sqlalchemy.orm import Session

from app.models import ProductHypothesis
from app.schemas.hypothesis import ProductHypothesisCreate


class ProductHypothesisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: ProductHypothesisCreate) -> ProductHypothesis:
        entity = ProductHypothesis(**payload.model_dump())
        self.db.add(entity)
        self.db.flush()
        return entity

    def get(self, hypothesis_id: int) -> ProductHypothesis | None:
        return self.db.get(ProductHypothesis, hypothesis_id)
