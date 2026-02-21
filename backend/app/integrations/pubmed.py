from __future__ import annotations

from typing import Any

import requests

from app.config import Settings
from app.utils.retry import retry_requests


class PubMedClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.ncbi_api_key
        self._tool = settings.ncbi_tool
        self._email = settings.ncbi_email
        self._esearch_url = settings.pubmed_esearch_url
        self._esummary_url = settings.pubmed_esummary_url

    @retry_requests
    def search_evidence(self, query: str, max_results: int = 5) -> dict[str, Any]:
        if not query.strip():
            return {"articles": []}

        params = {
            "db": "pubmed",
            "retmode": "json",
            "term": query,
            "retmax": max_results,
            "tool": self._tool,
            "email": self._email,
        }
        if self._api_key:
            params["api_key"] = self._api_key

        search_res = requests.get(self._esearch_url, params=params, timeout=20)
        search_res.raise_for_status()
        ids = (search_res.json().get("esearchresult") or {}).get("idlist") or []
        if not ids:
            return {"articles": []}

        summary_params = {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(ids),
            "tool": self._tool,
            "email": self._email,
        }
        if self._api_key:
            summary_params["api_key"] = self._api_key

        summary_res = requests.get(self._esummary_url, params=summary_params, timeout=20)
        summary_res.raise_for_status()
        result = summary_res.json().get("result") or {}

        articles: list[dict[str, Any]] = []
        for pmid in ids:
            row = result.get(pmid)
            if not row:
                continue
            articles.append(
                {
                    "pmid": pmid,
                    "title": row.get("title"),
                    "pubdate": row.get("pubdate"),
                    "source": row.get("source"),
                    "authors": [a.get("name") for a in (row.get("authors") or [])[:3]],
                }
            )

        return {"articles": articles}
