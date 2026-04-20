from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Shopify Lab MVP"
    database_url: str = "sqlite:///./shopify_lab.db"


settings = Settings()
