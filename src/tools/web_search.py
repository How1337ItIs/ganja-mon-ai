"""
Web Search & Browse — gives the agent real internet access.

Primary search: Perplexity Sonar via OpenRouter (has live web search built in).
Browse: Direct HTTP fetch + BeautifulSoup extraction.

Usage:
    from src.tools.web_search import WebSearchTool

    tool = WebSearchTool()
    results = await tool.search("Moltiverse hackathon judges 2026")
    text = await tool.browse("https://example.com/article")
    context = await tool.research("who are the judges")
    findings = await tool.deep_research("hackathon winning strategies", max_sources=5)
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Rate limiting
_last_search_time = 0.0
_MIN_SEARCH_INTERVAL = 3.0  # seconds between searches
_last_browse_time = 0.0
_MIN_BROWSE_INTERVAL = 1.0


class WebSearchTool:
    """Web search and browsing for the autonomous agent."""

    def __init__(self):
        self.xai_base = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        self.xai_key = os.getenv("XAI_API_KEY", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("GROK_MODEL", "grok-3-fast")
        self._search_cache: dict[str, tuple[float, str]] = {}  # query -> (ts, response)
        self._browse_cache: dict[str, tuple[float, str]] = {}  # url -> (ts, text)
        self._cache_ttl = 1800  # 30 min

    # ------------------------------------------------------------------
    # 1. Search (Perplexity Sonar via OpenRouter — has live web search)
    # ------------------------------------------------------------------

    async def search(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Search the web. Returns structured results with title, url, body.

        Uses Perplexity Sonar (via OpenRouter) which has built-in live web search.
        Falls back to DuckDuckGo if OpenRouter is unavailable.
        """
        global _last_search_time

        # Cache check
        cache_key = f"{query}:{max_results}"
        if cache_key in self._search_cache:
            ts, cached = self._search_cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                logger.info(f"[WEB-SEARCH] Cache hit for: {query[:60]}")
                return json.loads(cached)

        # Rate limit
        now = time.time()
        wait = _MIN_SEARCH_INTERVAL - (now - _last_search_time)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_search_time = time.time()

        # Primary: Perplexity Sonar via OpenRouter
        if self.openrouter_key:
            results = await self._sonar_search(query, max_results)
            if results:
                self._search_cache[cache_key] = (time.time(), json.dumps(results))
                return results

        # Fallback: DuckDuckGo
        results = await self._ddg_search(query, max_results)
        if results:
            self._search_cache[cache_key] = (time.time(), json.dumps(results))
        return results

    async def _sonar_search(self, query: str, max_results: int) -> list[dict]:
        """Search via Perplexity Sonar (has built-in web search)."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "perplexity/sonar",
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are a search engine. For the user's query, search the web and return results "
                                    "as a JSON array of objects with keys: title, url, body (snippet). "
                                    f"Return up to {max_results} results. Return ONLY the JSON array, no other text."
                                ),
                            },
                            {"role": "user", "content": query},
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.1,
                    },
                )
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"].strip()
                    # Strip markdown fences
                    if raw.startswith("```"):
                        raw = re.sub(r"^```(?:json)?\s*", "", raw)
                        raw = re.sub(r"\s*```$", "", raw)
                    try:
                        results = json.loads(raw)
                        if isinstance(results, list):
                            logger.info(f"[WEB-SEARCH] Sonar: '{query[:60]}' → {len(results)} results")
                            return results[:max_results]
                    except json.JSONDecodeError:
                        # Sonar returned prose — parse it as a single result
                        logger.info(f"[WEB-SEARCH] Sonar returned prose for: {query[:60]}")
                        return [{"title": query, "url": "", "body": raw[:1000]}]
                else:
                    logger.warning(f"[WEB-SEARCH] Sonar failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"[WEB-SEARCH] Sonar error: {e}")
        return []

    async def _ddg_search(self, query: str, max_results: int) -> list[dict]:
        """Fallback: DuckDuckGo search."""
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("link", "")),
                        "body": r.get("body", r.get("snippet", "")),
                    })
            if results:
                logger.info(f"[WEB-SEARCH] DDG: '{query[:60]}' → {len(results)} results")
            return results
        except Exception as e:
            logger.warning(f"[WEB-SEARCH] DDG failed: {e}")
            return []

    # ------------------------------------------------------------------
    # 2. Smart Search (Perplexity answers with citations)
    # ------------------------------------------------------------------

    async def smart_search(self, question: str) -> str:
        """
        Ask a question and get a sourced answer with citations.
        Uses Perplexity Sonar which searches the web and synthesizes.
        Returns the answer text directly.
        """
        if not self.openrouter_key:
            return "No OpenRouter API key — cannot perform smart search."

        # Cache check
        cache_key = f"smart:{question}"
        if cache_key in self._search_cache:
            ts, cached = self._search_cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return cached

        global _last_search_time
        now = time.time()
        wait = _MIN_SEARCH_INTERVAL - (now - _last_search_time)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_search_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "perplexity/sonar",
                        "messages": [
                            {"role": "user", "content": question},
                        ],
                        "max_tokens": 1000,
                        "temperature": 0.2,
                    },
                )
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"].strip()
                    logger.info(f"[WEB-SMART] '{question[:60]}' → {len(answer)} chars")
                    self._search_cache[cache_key] = (time.time(), answer)
                    return answer
                else:
                    logger.warning(f"[WEB-SMART] Sonar failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"[WEB-SMART] Error: {e}")
        return ""

    # ------------------------------------------------------------------
    # 3. Browse (fetch + extract text from URL)
    # ------------------------------------------------------------------

    async def browse(self, url: str, max_chars: int = 8000) -> str:
        """Fetch a URL and extract readable text content."""
        global _last_browse_time

        if not url:
            return ""

        # Cache check
        if url in self._browse_cache:
            ts, cached = self._browse_cache[url]
            if time.time() - ts < self._cache_ttl:
                return cached[:max_chars]

        # Rate limit
        now = time.time()
        wait = _MIN_BROWSE_INTERVAL - (now - _last_browse_time)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_browse_time = time.time()

        text = await self._direct_fetch(url)
        if text:
            self._browse_cache[url] = (time.time(), text)

        return (text or "")[:max_chars]

    async def _direct_fetch(self, url: str) -> str:
        """Direct HTTP fetch + BeautifulSoup extraction."""
        try:
            from bs4 import BeautifulSoup
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; GanjaMonAgent/1.0; +https://grokandmon.com)",
                },
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return ""
                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    return resp.text[:8000]
                if "html" not in content_type and "text" not in content_type:
                    return ""

                soup = BeautifulSoup(resp.text, "lxml")

                # Remove noise
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                    tag.decompose()

                main = soup.find("article") or soup.find("main") or soup.find("div", {"role": "main"})
                text = (main or soup).get_text(separator="\n", strip=True)
                text = re.sub(r"\n{3,}", "\n\n", text)
                logger.info(f"[WEB-BROWSE] {url[:80]} → {len(text)} chars")
                return text
        except Exception as e:
            logger.warning(f"[WEB-BROWSE] Fetch failed for {url[:80]}: {e}")
        return ""

    # ------------------------------------------------------------------
    # 4. Research (search + browse top results + combine)
    # ------------------------------------------------------------------

    async def research(self, query: str, max_sources: int = 3, max_chars_per_source: int = 3000) -> str:
        """Search, optionally read top results, return combined context string."""
        results = await self.search(query, max_results=max_sources + 2)
        if not results:
            # Fallback: use smart_search for a direct answer
            answer = await self.smart_search(query)
            return answer if answer else f"No results found for: {query}"

        chunks = [f"## Search Results for: {query}\n"]
        read_count = 0
        for r in results:
            if read_count >= max_sources:
                break
            url = r.get("url", "")
            title = r.get("title", "")
            body = r.get("body", "")

            if not url:
                # Sonar result without URL — include the body directly
                if body:
                    chunks.append(f"### {title}\n{body}\n")
                continue

            # Skip non-text URLs
            if any(skip in url for skip in ["youtube.com/watch", "tiktok.com", "instagram.com/p/"]):
                chunks.append(f"### {title}\nURL: {url}\nSnippet: {body}\n")
                continue

            text = await self.browse(url, max_chars=max_chars_per_source)
            if text and len(text) > 100:
                chunks.append(f"### {title}\nURL: {url}\n\n{text}\n")
                read_count += 1
            else:
                chunks.append(f"### {title}\nURL: {url}\nSnippet: {body}\n")

        combined = "\n".join(chunks)
        logger.info(f"[WEB-RESEARCH] '{query[:60]}' → {read_count} pages read, {len(combined)} chars")
        return combined

    # ------------------------------------------------------------------
    # 5. Deep Research (search + browse + LLM synthesis)
    # ------------------------------------------------------------------

    async def deep_research(
        self,
        question: str,
        max_sources: int = 5,
        save_to: Optional[str] = None,
    ) -> dict:
        """
        Full research pipeline: search → browse → synthesize.

        Returns dict with findings, action_items, sources, etc.
        """
        # Step 1: Get raw research context
        raw_context = await self.research(question, max_sources=max_sources)

        # Step 2: Also get a smart search answer for additional context
        smart_answer = await self.smart_search(question)
        if smart_answer:
            raw_context += f"\n\n## Direct Answer (Perplexity):\n{smart_answer}\n"

        # Step 3: Synthesize with LLM
        synthesis = await self._synthesize(question, raw_context)

        result = {
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "findings": synthesis.get("findings", []),
            "action_items": synthesis.get("action_items", []),
            "priority_contacts": synthesis.get("priority_contacts", []),
            "sources_read": max_sources,
            "raw_context_length": len(raw_context),
        }

        # Save
        save_path = save_to or "data/research_results.json"
        try:
            p = Path(save_path)
            existing = json.loads(p.read_text()) if p.exists() else []
            if not isinstance(existing, list):
                existing = []
            existing.append(result)
            if len(existing) > 50:
                existing = existing[-50:]
            p.write_text(json.dumps(existing, indent=2))
            logger.info(f"[WEB-RESEARCH] Deep research saved to {save_path}")
        except Exception as e:
            logger.error(f"[WEB-RESEARCH] Failed to save: {e}")

        return result

    async def _synthesize(self, question: str, context: str) -> dict:
        """Use LLM to synthesize research into structured findings."""
        prompt = (
            f"Based on the web research below, answer this question:\n\n"
            f"QUESTION: {question}\n\n"
            f"WEB RESEARCH:\n{context[:12000]}\n\n"
            f"Return a JSON object with:\n"
            f"- findings: list of 3-8 key findings (strings)\n"
            f"- action_items: list of 2-5 recommended actions (strings)\n"
            f"- priority_contacts: list of relevant people (objects with name, platform, approach)\n\n"
            f"Return ONLY valid JSON."
        )

        # Try xAI first, then OpenRouter with a cheap model
        providers = [
            ("xAI", self.xai_base, self.xai_key, self.model),
            ("OpenRouter", "https://openrouter.ai/api/v1", self.openrouter_key, "google/gemini-2.0-flash-001"),
        ]
        for provider, base_url, key, model in providers:
            if not key:
                continue
            try:
                async with httpx.AsyncClient(timeout=45.0) as hc:
                    resp = await hc.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": "You are a research analyst. Return valid JSON only."},
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": 1500,
                            "temperature": 0.2,
                        },
                    )
                    if resp.status_code == 200:
                        raw = resp.json()["choices"][0]["message"]["content"].strip()
                        if raw.startswith("```"):
                            raw = re.sub(r"^```(?:json)?\s*", "", raw)
                            raw = re.sub(r"\s*```$", "", raw)
                        result = json.loads(raw)
                        logger.info(f"[WEB-RESEARCH] Synthesis via {provider}: {len(result.get('findings', []))} findings")
                        return result
            except json.JSONDecodeError:
                logger.warning(f"[WEB-RESEARCH] {provider} returned non-JSON")
                continue
            except Exception as e:
                logger.warning(f"[WEB-RESEARCH] {provider} failed: {e}")
                continue

        return {"findings": ["LLM synthesis unavailable"], "action_items": [], "priority_contacts": []}

    # ------------------------------------------------------------------
    # 6. News search
    # ------------------------------------------------------------------

    async def search_news(self, query: str, max_results: int = 5) -> list[dict]:
        """Search for recent news. Uses Sonar or DDG news."""
        # Try DDG news first (structured)
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.news(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", r.get("link", "")),
                        "body": r.get("body", ""),
                        "date": r.get("date", ""),
                        "source": r.get("source", ""),
                    })
            if results:
                logger.info(f"[WEB-NEWS] DDG: '{query[:60]}' → {len(results)} articles")
                return results
        except Exception:
            pass

        # Fallback: Sonar search with news focus
        answer = await self.smart_search(f"Latest news: {query}")
        if answer:
            return [{"title": query, "url": "", "body": answer, "date": "", "source": "Perplexity"}]
        return []


# Singleton
_instance: Optional[WebSearchTool] = None


def get_web_search() -> WebSearchTool:
    global _instance
    if _instance is None:
        _instance = WebSearchTool()
    return _instance
