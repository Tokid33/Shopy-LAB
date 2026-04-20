from typing import Protocol


class SearchProvider(Protocol):
    def search(self, query: str, limit: int = 5) -> list[dict]:
        ...


class WebPageFetcher(Protocol):
    def fetch(self, url: str) -> str:
        ...


class LLMExtractor(Protocol):
    def extract_product_candidate(self, raw_text: str) -> dict:
        ...


class FakeSearchProvider:
    def search(self, query: str, limit: int = 5) -> list[dict]:
        return [
            {
                "title": f"{query} candidate #{idx + 1}",
                "url": f"https://fake-search.local/{idx + 1}",
                "snippet": "Portable solution with daily-use utility",
            }
            for idx in range(limit)
        ]


class FakeWebPageFetcher:
    def fetch(self, url: str) -> str:
        return f"Mock page content for {url}. Problem solving product with visual demo potential."


class FakeLLMExtractor:
    def extract_product_candidate(self, raw_text: str) -> dict:
        return {
            "product_name": "Demo Utility Product",
            "category": "General",
            "problem_or_desire_score": 8,
            "visual_potential_score": 7,
            "margin_score": 7,
            "ad_risk_score": 6,
            "logistics_risk_score": 7,
            "cost_of_goods": 11.0,
            "target_price": 34.0,
            "shipping_cost": 4.0,
        }
