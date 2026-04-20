import json
import re
from collections import OrderedDict

import httpx
from pydantic import BaseModel, ValidationError
from typing import Protocol

from app.core.config import settings


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, limit: int = 5) -> list[dict]:
        ...


class WebPageFetcher(Protocol):
    name: str

    def fetch(self, url: str) -> str:
        ...


class LLMExtractor(Protocol):
    name: str

    def extract_product_candidate(self, raw_text: str, prompt: str) -> dict:
        ...

    def extract_supplier_candidate(self, raw_text: str, prompt: str) -> dict:
        ...


class FakeSearchProvider:
    name = "fake"

    def search(self, query: str, limit: int = 5) -> list[dict]:
        return [
            {
                "title": f"{query} candidate #{idx + 1}",
                "url": f"https://fake-search.local/{idx + 1}",
                "snippet": "Portable solution with daily-use utility",
            }
            for idx in range(limit)
        ]


class BraveSearchProvider:
    name = "brave"

    def __init__(self, api_key: str, timeout_seconds: int):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int = 5) -> list[dict]:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {"q": query, "count": limit}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        web_results = data.get("web", {}).get("results", [])
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
            }
            for item in web_results
            if item.get("url")
        ]


class SerpApiSearchProvider:
    name = "serpapi"

    def __init__(self, api_key: str, timeout_seconds: int):
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int = 5) -> list[dict]:
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": limit,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        return [
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in data.get("organic_results", [])
            if item.get("link")
        ]


class FakeWebPageFetcher:
    name = "fake"

    def fetch(self, url: str) -> str:
        return f"Mock page content for {url}. Problem solving product with visual demo potential."


class HttpWebPageFetcher:
    name = "http"

    def __init__(self, timeout_seconds: int, max_chars: int):
        self.timeout_seconds = timeout_seconds
        self.max_chars = max_chars
        self._seen_hashes: set[int] = set()

    def fetch(self, url: str) -> str:
        headers = {"User-Agent": "ShopifyLabAgent/0.1 (+https://shopify-lab.local)"}
        attempts = 2
        error: Exception | None = None
        for _ in range(attempts):
            try:
                with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                    response = client.get(url, headers=headers)
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        return ""
                    text = self._sanitize(response.text)
                    if not text:
                        return ""
                    text_hash = hash(text[:500])
                    if text_hash in self._seen_hashes:
                        return ""
                    self._seen_hashes.add(text_hash)
                    return text[: self.max_chars]
            except Exception as exc:
                error = exc
        if error:
            raise error
        return ""

    @staticmethod
    def _sanitize(raw_html: str) -> str:
        no_script = re.sub(r"<script[\\s\\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
        no_style = re.sub(r"<style[\\s\\S]*?</style>", " ", no_script, flags=re.IGNORECASE)
        plain = re.sub(r"<[^>]+>", " ", no_style)
        plain = re.sub(r"\\s+", " ", plain).strip()
        return plain


class FakeLLMExtractor:
    name = "fake"

    def extract_product_candidate(self, raw_text: str, prompt: str) -> dict:
        return {
            "product_name": "Demo Utility Product",
            "category": "General",
            "signal": "green",
            "problem_or_desire_score": 8,
            "visual_potential_score": 7,
            "margin_score": 7,
            "ad_risk_score": 6,
            "logistics_risk_score": 7,
            "cost_of_goods": 11.0,
            "target_price": 34.0,
            "shipping_cost": 4.0,
        }

    def extract_supplier_candidate(self, raw_text: str, prompt: str) -> dict:
        return {
            "supplier_name": "Demo Supplier Co.",
            "signal": "green",
            "unit_cost": 11.0,
            "ship_cost": 4.0,
            "lead_time_days": 12,
        }


class _ProductExtractionSchema(BaseModel):
    product_name: str
    category: str
    signal: str
    problem_or_desire_score: int
    visual_potential_score: int
    margin_score: int
    ad_risk_score: int
    logistics_risk_score: int
    cost_of_goods: float
    target_price: float
    shipping_cost: float


class _SupplierExtractionSchema(BaseModel):
    supplier_name: str
    signal: str
    unit_cost: float
    ship_cost: float
    lead_time_days: int


class OpenAICompatibleLLMExtractor:
    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def extract_product_candidate(self, raw_text: str, prompt: str) -> dict:
        schema_hint = (
            "Return ONLY JSON with fields: product_name, category, signal(green|yellow|red), "
            "problem_or_desire_score, visual_potential_score, margin_score, ad_risk_score, logistics_risk_score, "
            "cost_of_goods, target_price, shipping_cost"
        )
        parsed = self._chat_json(prompt, raw_text, schema_hint)
        return self._safe_validate(parsed, _ProductExtractionSchema)

    def extract_supplier_candidate(self, raw_text: str, prompt: str) -> dict:
        schema_hint = (
            "Return ONLY JSON with fields: supplier_name, signal(green|yellow|red), unit_cost, ship_cost, lead_time_days"
        )
        parsed = self._chat_json(prompt, raw_text, schema_hint)
        return self._safe_validate(parsed, _SupplierExtractionSchema)

    def _chat_json(self, prompt: str, raw_text: str, schema_hint: str) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"{schema_hint}\n\nTEXT:\n{raw_text[:5000]}"},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    @staticmethod
    def _safe_validate(payload: dict, schema: type[BaseModel]) -> dict:
        try:
            return schema(**payload).model_dump()
        except ValidationError:
            return {}


class ProviderResolutionError(ValueError):
    pass


def get_search_provider(force_mode: str | None = None) -> SearchProvider:
    mode = force_mode or settings.agent_mode
    provider_name = settings.search_provider if mode == "real" else "fake"

    if provider_name == "fake":
        return FakeSearchProvider()
    if provider_name in {"brave", "serpapi"} and not settings.search_api_key:
        raise ProviderResolutionError("SEARCH_API_KEY is required for real search provider")
    if provider_name == "brave":
        return BraveSearchProvider(settings.search_api_key or "", settings.request_timeout_seconds)
    if provider_name == "serpapi":
        return SerpApiSearchProvider(settings.search_api_key or "", settings.request_timeout_seconds)
    raise ProviderResolutionError(f"Unsupported search provider: {provider_name}")


def get_fetch_provider(force_mode: str | None = None) -> WebPageFetcher:
    mode = force_mode or settings.agent_mode
    provider_name = settings.fetch_provider if mode == "real" else "fake"
    if provider_name == "fake":
        return FakeWebPageFetcher()
    if provider_name == "http":
        return HttpWebPageFetcher(settings.request_timeout_seconds, settings.max_page_text_chars)
    raise ProviderResolutionError(f"Unsupported fetch provider: {provider_name}")


def get_llm_extractor(force_mode: str | None = None) -> LLMExtractor:
    mode = force_mode or settings.agent_mode
    provider_name = settings.llm_provider if mode == "real" else "fake"
    if provider_name == "fake":
        return FakeLLMExtractor()
    if provider_name == "openai_compatible":
        if not settings.llm_base_url or not settings.llm_api_key:
            raise ProviderResolutionError("LLM_BASE_URL and LLM_API_KEY are required for openai_compatible provider")
        return OpenAICompatibleLLMExtractor(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.request_timeout_seconds,
        )
    raise ProviderResolutionError(f"Unsupported llm provider: {provider_name}")


def provider_snapshot(force_mode: str | None = None) -> dict:
    mode = force_mode or settings.agent_mode
    return {
        "mode": mode,
        "search_provider": settings.search_provider if mode == "real" else "fake",
        "fetch_provider": settings.fetch_provider if mode == "real" else "fake",
        "llm_provider": settings.llm_provider if mode == "real" else "fake",
        "llm_model": settings.llm_model,
        "timeout_seconds": settings.request_timeout_seconds,
        "max_search_results": settings.max_search_results,
        "max_fetch_pages": settings.max_fetch_pages,
        "max_page_text_chars": settings.max_page_text_chars,
    }


def provider_health(force_mode: str | None = None) -> dict:
    mode = force_mode or settings.agent_mode
    selected = provider_snapshot(mode)
    missing_env: list[str] = []

    if mode == "real":
        if selected["search_provider"] in {"brave", "serpapi"} and not settings.search_api_key:
            missing_env.append("SEARCH_API_KEY")
        if selected["llm_provider"] == "openai_compatible":
            if not settings.llm_base_url:
                missing_env.append("LLM_BASE_URL")
            if not settings.llm_api_key:
                missing_env.append("LLM_API_KEY")

    available = {
        "search": ["fake", "brave", "serpapi"],
        "fetch": ["fake", "http"],
        "llm": ["fake", "openai_compatible"],
    }

    return {
        "mode": mode,
        "selected_providers": selected,
        "available_providers": available,
        "missing_env": list(OrderedDict.fromkeys(missing_env)),
        "real_mode_ready": mode == "real" and len(missing_env) == 0,
    }
