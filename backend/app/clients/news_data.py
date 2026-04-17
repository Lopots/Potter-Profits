from __future__ import annotations

import hashlib
from typing import Any

import httpx

from app.core.config import settings


def _keyword_query(text: str) -> str:
    cleaned = text.replace("?", " ").replace(">", " ").replace("<", " ").replace("$", " ")
    parts = [part.strip() for part in cleaned.split() if len(part.strip()) > 2]
    return " ".join(parts[:6])


def fetch_newsapi_articles(queries: list[str]) -> list[dict[str, Any]]:
    if not settings.newsapi_api_key:
        return []

    articles: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    with httpx.Client(timeout=20.0) as client:
        for query in queries[: settings.news_fetch_limit]:
            response = client.get(
                f"{settings.newsapi_api_url}/everything",
                params={
                    "q": _keyword_query(query),
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": settings.news_fetch_limit,
                },
                headers={"X-Api-Key": settings.newsapi_api_key},
            )
            response.raise_for_status()
            payload = response.json()
            for article in payload.get("articles", []):
                url = article.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                articles.append(article)

    return articles


def normalize_newsapi_article(article: dict[str, Any]) -> dict[str, Any]:
    url = article.get("url", "")
    external_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return {
        "source": "newsapi",
        "external_id": f"newsapi:{external_id}",
        "title": article.get("title") or "Untitled article",
        "url": url,
        "summary": article.get("description") or article.get("content") or "",
        "published_at": article.get("publishedAt"),
        "raw_payload": article,
    }


def get_news_client_status() -> dict[str, dict[str, str | bool]]:
    return {
        "newsapi": {
            "configured": bool(settings.newsapi_api_key),
            "base_url": settings.newsapi_api_url,
            "notes": "Recommended first news source for headline ingestion.",
        },
        "gnews": {
            "configured": bool(settings.gnews_api_key),
            "base_url": settings.gnews_api_url,
            "notes": "Optional backup headline source.",
        },
        "reddit": {
            "configured": bool(settings.reddit_client_id and settings.reddit_client_secret),
            "base_url": "https://www.reddit.com",
            "notes": "Useful for niche market sentiment once you add app credentials.",
        },
    }
