"""
Subagent Task Executor — spawns parallel LLM workers for research & strategy.

Each subagent is an async task that:
1. Gets a focused mission (research question, strategy task, etc.)
2. Has access to web search + browse tools
3. Uses OpenRouter or xAI for reasoning
4. Writes structured results to a shared output file
5. Runs concurrently with other subagents (up to max_concurrent)

Usage:
    from src.tools.subagent import SubagentExecutor

    executor = SubagentExecutor()
    # Fire off multiple research tasks in parallel
    results = await executor.run_batch([
        {"task": "Research Moltiverse hackathon judges", "type": "research"},
        {"task": "Analyze competitor projects on nad.fun", "type": "research"},
        {"task": "Draft email to Haseeb at Dragonfly", "type": "draft"},
    ])
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class SubagentResult:
    """Result from a subagent task."""

    def __init__(self, task_id: str, task: str, task_type: str):
        self.task_id = task_id
        self.task = task
        self.task_type = task_type
        self.status: str = "pending"  # pending, running, completed, failed
        self.output: str = ""
        self.findings: list = []
        self.action_items: list = []
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.tokens_used: int = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task": self.task,
            "type": self.task_type,
            "status": self.status,
            "output": self.output[:2000],
            "findings": self.findings,
            "action_items": self.action_items,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "tokens_used": self.tokens_used,
        }


class SubagentExecutor:
    """Manages parallel LLM-powered subagents."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.xai_key = os.getenv("XAI_API_KEY", "")
        self.xai_base = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        self.xai_model = os.getenv("GROK_MODEL", "grok-3-fast")
        self.results_dir = Path("data/subagent_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0

    async def run_batch(self, tasks: list[dict]) -> list[SubagentResult]:
        """
        Run multiple subagent tasks in parallel.

        Each task dict should have:
            - task: str — the mission description
            - type: str — "research", "draft", "analyze", "strategy"
            - context: str (optional) — additional context
            - priority: str (optional) — "critical", "high", "medium", "low"
        """
        results = []
        async_tasks = []

        for i, task_spec in enumerate(tasks):
            result = SubagentResult(
                task_id=f"sa-{int(time.time())}-{i}",
                task=task_spec.get("task", ""),
                task_type=task_spec.get("type", "research"),
            )
            results.append(result)
            context = task_spec.get("context", "")
            async_tasks.append(self._run_single(result, context))

        # Run all concurrently (semaphore limits parallelism)
        await asyncio.gather(*async_tasks, return_exceptions=True)

        # Save batch results
        self._save_results(results)

        completed = sum(1 for r in results if r.status == "completed")
        failed = sum(1 for r in results if r.status == "failed")
        logger.info(f"[SUBAGENT] Batch done: {completed} completed, {failed} failed out of {len(results)}")

        return results

    async def run_single(self, task: str, task_type: str = "research", context: str = "") -> SubagentResult:
        """Run a single subagent task."""
        result = SubagentResult(
            task_id=f"sa-{int(time.time())}",
            task=task,
            task_type=task_type,
        )
        await self._run_single(result, context)
        self._save_results([result])
        return result

    async def _run_single(self, result: SubagentResult, context: str = ""):
        """Execute a single subagent with web search + LLM reasoning."""
        async with self._semaphore:
            self._active_count += 1
            result.status = "running"
            result.started_at = datetime.now().isoformat()
            logger.info(f"[SUBAGENT] Starting {result.task_id}: {result.task[:80]} (active: {self._active_count})")

            try:
                if result.task_type == "research":
                    await self._research_agent(result, context)
                elif result.task_type == "draft":
                    await self._draft_agent(result, context)
                elif result.task_type == "analyze":
                    await self._analyze_agent(result, context)
                elif result.task_type == "strategy":
                    await self._strategy_agent(result, context)
                else:
                    await self._research_agent(result, context)  # default

                result.status = "completed"
            except Exception as e:
                result.status = "failed"
                result.error = str(e)
                logger.error(f"[SUBAGENT] {result.task_id} failed: {e}")
            finally:
                result.completed_at = datetime.now().isoformat()
                self._active_count -= 1
                logger.info(f"[SUBAGENT] {result.task_id} {result.status} (active: {self._active_count})")

    # ------------------------------------------------------------------
    # Agent types
    # ------------------------------------------------------------------

    async def _research_agent(self, result: SubagentResult, context: str):
        """Research agent: web search → browse → synthesize."""
        from src.tools.web_search import get_web_search
        ws = get_web_search()

        # Step 1: Web search
        search_answer = await ws.smart_search(result.task)
        web_context = search_answer or ""

        # Step 2: If smart_search gave results, also browse any URLs mentioned
        search_results = await ws.search(result.task, max_results=3)
        for sr in search_results[:2]:
            if not isinstance(sr, dict):
                continue
            url = sr.get("url", "")
            if url:
                page_text = await ws.browse(url, max_chars=2000)
                if page_text:
                    web_context += f"\n\n--- Source: {url} ---\n{page_text}"

        # Step 3: Synthesize with LLM
        synthesis = await self._llm_call(
            system="You are a research analyst. Provide structured findings as JSON with keys: "
                   "findings (list of strings), action_items (list of strings), "
                   "priority_contacts (list of {name, platform, approach}).",
            prompt=f"RESEARCH TASK: {result.task}\n\n"
                   f"ADDITIONAL CONTEXT: {context[:2000]}\n\n"
                   f"WEB RESEARCH:\n{web_context[:8000]}\n\n"
                   f"Provide actionable findings. Return ONLY valid JSON.",
            max_tokens=1500,
        )

        result.output = synthesis
        try:
            import re
            clean = synthesis.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean)
            data = json.loads(clean)
            result.findings = data.get("findings", [])
            result.action_items = data.get("action_items", [])
        except (json.JSONDecodeError, Exception):
            result.findings = [synthesis[:500]]

    async def _draft_agent(self, result: SubagentResult, context: str):
        """Draft agent: creates content (emails, posts, etc.)."""
        draft = await self._llm_call(
            system="You are GanjaMon's communications specialist. Write professional but warm content "
                   "with subtle Rasta flavor. Be substantive and strategic.",
            prompt=f"DRAFT TASK: {result.task}\n\nCONTEXT: {context[:3000]}\n\n"
                   f"Write the requested content. Be concise and impactful.",
            max_tokens=1000,
        )
        result.output = draft
        result.findings = [f"Draft created: {len(draft)} chars"]

    async def _analyze_agent(self, result: SubagentResult, context: str):
        """Analysis agent: evaluates data, strategies, or decisions."""
        from src.tools.web_search import get_web_search
        ws = get_web_search()

        # Get relevant web context
        web_answer = await ws.smart_search(result.task)

        analysis = await self._llm_call(
            system="You are a strategic analyst. Provide clear, actionable analysis as JSON with keys: "
                   "analysis (string), strengths (list), weaknesses (list), recommendations (list).",
            prompt=f"ANALYSIS TASK: {result.task}\n\nCONTEXT: {context[:2000]}\n\n"
                   f"WEB CONTEXT: {web_answer[:3000]}\n\nReturn ONLY valid JSON.",
            max_tokens=1500,
        )

        result.output = analysis
        try:
            import re
            clean = analysis.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean)
            data = json.loads(clean)
            result.findings = data.get("recommendations", [])
            result.action_items = data.get("recommendations", [])
        except (json.JSONDecodeError, Exception):
            result.findings = [analysis[:500]]

    async def _strategy_agent(self, result: SubagentResult, context: str):
        """Strategy agent: research + analysis combined for strategic planning."""
        from src.tools.web_search import get_web_search
        ws = get_web_search()

        # Deep research
        research = await ws.deep_research(result.task, max_sources=3)

        # Additional strategic reasoning
        strategy = await self._llm_call(
            system="You are a hackathon strategy expert. Based on research, create an actionable strategy. "
                   "Return JSON with: strategy (string), steps (list of strings), "
                   "risks (list), timeline (string), expected_impact (string).",
            prompt=f"STRATEGY TASK: {result.task}\n\nCONTEXT: {context[:2000]}\n\n"
                   f"RESEARCH FINDINGS:\n{json.dumps(research.get('findings', []))}\n"
                   f"ACTION ITEMS:\n{json.dumps(research.get('action_items', []))}\n\n"
                   f"Create a concrete strategy. Return ONLY valid JSON.",
            max_tokens=1500,
        )

        result.output = strategy
        result.findings = research.get("findings", [])
        result.action_items = research.get("action_items", [])
        try:
            import re
            clean = strategy.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean)
            data = json.loads(clean)
            if data.get("steps"):
                result.action_items = data["steps"]
        except (json.JSONDecodeError, Exception):
            pass

    # ------------------------------------------------------------------
    # LLM call (multi-provider)
    # ------------------------------------------------------------------

    async def _llm_call(self, system: str, prompt: str, max_tokens: int = 1000) -> str:
        """Make an LLM call, trying xAI first then OpenRouter."""
        providers = [
            ("xAI", self.xai_base, self.xai_key, self.xai_model),
            ("OpenRouter", "https://openrouter.ai/api/v1", self.openrouter_key, "google/gemini-2.0-flash-001"),
        ]

        for name, base_url, key, model in providers:
            if not key:
                continue
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": 0.3,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        logger.debug(f"[SUBAGENT] LLM call via {name}: {len(content)} chars")
                        return content
                    else:
                        logger.warning(f"[SUBAGENT] {name} returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"[SUBAGENT] {name} call failed: {e}")

        return ""

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_results(self, results: list[SubagentResult]):
        """Save subagent results to disk."""
        try:
            output_file = self.results_dir / "latest_batch.json"
            data = [r.to_dict() for r in results]
            output_file.write_text(json.dumps(data, indent=2))

            # Also append to history
            history_file = self.results_dir / "history.json"
            history = []
            if history_file.exists():
                try:
                    history = json.loads(history_file.read_text())
                except Exception:
                    history = []
            history.extend(data)
            # Keep last 100
            if len(history) > 100:
                history = history[-100:]
            history_file.write_text(json.dumps(history, indent=2))
        except Exception as e:
            logger.error(f"[SUBAGENT] Failed to save results: {e}")


# Singleton
_executor: Optional[SubagentExecutor] = None


def get_subagent_executor() -> SubagentExecutor:
    global _executor
    if _executor is None:
        _executor = SubagentExecutor()
    return _executor
