"""
xAI Native Social Client
=========================

Uses xAI Responses API for X intelligence:
- x_search: Find relevant cannabis/crypto posts
- Generate on-brand social content with Grok's voice

For actual posting, falls back to Twitter API (for now).
When xAI adds x_post tool, this will switch to native.
"""

import os
import asyncio
import httpx
import json
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from src.voice.personality import get_tweet_prompt, enforce_voice
import logging

logger = logging.getLogger(__name__)


@dataclass
class XSearchResult:
    """Result from X search"""
    query: str
    posts: List[dict]
    raw_output: str


@dataclass 
class GeneratedPost:
    """AI-generated social post"""
    text: str
    hashtags: List[str]
    suggested_image: bool
    context: str


class XAINativeSocial:
    """
    xAI-native social intelligence client.
    
    Uses Grok's Responses API with x_search tool for:
    - Finding trending cannabis/crypto conversations
    - Generating on-brand Mon updates
    - Crafting engagement-optimized posts
    
    Example:
        client = XAINativeSocial()
        
        # Search X for relevant posts
        results = await client.search_x("#AICannabis OR #Monad")
        
        # Generate a post about Mon
        post = await client.generate_mon_post(
            day=15,
            vpd=1.05,
            health="EXCELLENT",
            event="First true leaves spotted!"
        )
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set")
        
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-4-1-fast-non-reasoning"
        
    async def search_x(self, query: str, limit: int = 10) -> XSearchResult:
        """
        Search X/Twitter using Grok's native x_search tool.
        
        Args:
            query: Search query (hashtags, keywords, etc.)
            limit: Max results
            
        Returns:
            XSearchResult with posts and analysis
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "tools": [{"type": "x_search"}],
                    "input": f"Search X for: {query}. Return the top {limit} most relevant recent posts with usernames, dates, and engagement.",
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                logger.error(f"X search failed: {response.text}")
                return XSearchResult(query=query, posts=[], raw_output="")
            
            data = response.json()
            
            # Extract output text
            output_text = ""
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            output_text = content.get("text", "")
            
            return XSearchResult(
                query=query,
                posts=[],  # Would need to parse structured data
                raw_output=output_text
            )
    
    async def generate_mon_post(
        self,
        day: int,
        vpd: float,
        health: str,
        stage: str = "vegetative",
        event: Optional[str] = None,
        include_price: Optional[str] = None,
    ) -> GeneratedPost:
        """
        Generate an on-brand Mon status post using Grok's voice.
        
        Args:
            day: Current grow day
            vpd: VPD reading
            health: Health status (EXCELLENT, GOOD, FAIR, etc.)
            stage: Growth stage
            event: Optional special event to highlight
            include_price: Optional $MON token price to include
            
        Returns:
            GeneratedPost ready for tweeting
        """
        prompt = get_tweet_prompt(
            day=day, vpd=vpd, health=health, stage=stage,
            event=event or "", include_price=include_price or "",
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    "temperature": 0.8
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Post generation failed: {response.text}")
                return GeneratedPost(
                    text=f"Day {day}: Mon vibing at {vpd} VPD. {health} health! Dat blasted wassie still inna di corner tho.",
                    hashtags=[],
                    suggested_image=True,
                    context="Fallback post"
                )
            
            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()
            text = enforce_voice(text)

            # Extract any remaining hashtags (should be empty after enforce_voice)
            hashtags = [word for word in text.split() if word.startswith("#")]
            
            return GeneratedPost(
                text=text,
                hashtags=hashtags,
                suggested_image=True,
                context=f"Day {day} {stage} update"
            )
    
    async def find_engagement_opportunities(self) -> List[dict]:
        """
        Find posts to engage with in the cannabis/crypto community.
        
        Uses x_search to find:
        - #AICannabis mentions
        - Monad blockchain discussions
        - Cannabis grow updates from others
        
        Returns list of engagement opportunities.
        """
        results = await self.search_x(
            "#AICannabis OR #Monad OR #AutonomousGrow OR #AIGrow",
            limit=5
        )
        
        # For now, return raw - would parse into structured opportunities
        return [{"raw": results.raw_output}]
    
    async def analyze_sentiment(self, topic: str) -> dict:
        """
        Analyze X sentiment around a topic.
        
        Useful for timing posts or understanding community mood.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "tools": [{"type": "x_search"}],
                    "input": f"Analyze the current sentiment on X about '{topic}'. Search for recent posts and summarize: 1) Overall sentiment (bullish/bearish/neutral), 2) Key themes, 3) Notable influencers discussing it.",
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                return {"sentiment": "unknown", "error": response.text}
            
            data = response.json()
            output_text = ""
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            output_text = content.get("text", "")
            
            return {
                "topic": topic,
                "analysis": output_text,
                "timestamp": datetime.now().isoformat()
            }


# =============================================================================
# Convenience Functions
# =============================================================================

async def generate_daily_post(day: int, vpd: float, health: str, stage: str) -> str:
    """Quick helper to generate a daily post."""
    client = XAINativeSocial()
    post = await client.generate_mon_post(day, vpd, health, stage)
    return post.text


async def search_cannabis_x(query: str = "#AICannabis") -> str:
    """Quick helper to search X for cannabis content."""
    client = XAINativeSocial()
    results = await client.search_x(query)
    return results.raw_output


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    async def test():
        client = XAINativeSocial()
        
        print("Testing X Search...")
        results = await client.search_x("#cannabis #AI", limit=5)
        print(f"Search results:\n{results.raw_output[:500]}...")
        
        print("\n" + "="*50 + "\n")
        
        print("Generating Mon post...")
        post = await client.generate_mon_post(
            day=15,
            vpd=1.05,
            health="EXCELLENT",
            stage="vegetative",
            event="First LST tie-down complete!"
        )
        print(f"Generated post:\n{post.text}")
        
    asyncio.run(test())
