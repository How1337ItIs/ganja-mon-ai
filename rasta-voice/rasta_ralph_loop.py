#!/usr/bin/env python3
"""
RASTA VOICE RALPH LOOP - Intelligent Iterative Voice Perfection

Based on Geoffrey Huntley's Ralph Wiggum methodology:
- Fresh context each iteration
- State persists in files
- ACTUALLY MODIFY the prompt based on learning
- Use research when stuck
- Deep analysis before changes

This loop doesn't just evaluate - it IMPROVES the prompt each iteration
until the completion criteria are met.

Usage:
    python rasta_ralph_loop.py                    # Run until complete
    python rasta_ralph_loop.py --continue         # Resume from last state
    python rasta_ralph_loop.py --status           # Show current progress
"""

import os
import sys
import json
import time
import random
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Tuple

from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv(Path(__file__).parent / ".env")

# =============================================================================
# Configuration
# =============================================================================

GROQ_KEY = os.getenv("GROQ_API_KEY")

STATE_FILE = Path(__file__).parent / "ralph_state.json"
PROMPT_FILE = Path(__file__).parent / "rasta_live.py"
LEARNINGS_FILE = Path(__file__).parent / "ralph_learnings.md"
LOGS_DIR = Path(__file__).parent / "ralph_logs"
EXPRESSION_BANK_FILE = Path(__file__).parent / "expression_bank.json"  # Rich vocabulary store

# Completion thresholds - ALL must be met
# Priority: VARIETY #1 > ENTERTAINING > AUTHENTIC
THRESHOLDS = {
    "variety": 9,          # #1 PRIORITY - NOT repetitive or predictable
    "humor": 7,            # Makes you smile, cheeky
    "entertainment": 7,    # NOT boring - keeps attention
    "warmth": 7,           # Friendly, approachable
    "flow": 6,             # Good for live conversation
    "naturalness": 6,      # Sounds like a person (not AI)
    "authenticity": 6,     # Patois can be a bit stereotypical, that's OK
}

# Circuit breakers (per frankbria/ralph-claude-code best practices)
MAX_NO_PROGRESS_LOOPS = 3       # CB_NO_PROGRESS_THRESHOLD
MAX_SAME_ERROR_LOOPS = 5        # CB_SAME_ERROR_THRESHOLD
OUTPUT_DECLINE_THRESHOLD = 0.7  # CB_OUTPUT_DECLINE_THRESHOLD (70%)
MIN_PROGRESS_THRESHOLD = 0.3    # Must improve avg by at least this much

# Rate limiting (per Huntley best practices - 100 calls/hour default)
MAX_CALLS_PER_HOUR = 100
CALL_LOG_FILE = Path(__file__).parent / "ralph_calls.json"

# Session management
SESSION_FILE = Path(__file__).parent / ".ralph_session"
SESSION_TIMEOUT_HOURS = 24

# Dual-gate completion detection patterns (heuristics)
COMPLETION_PATTERNS = [
    r"complete",
    r"finished",
    r"done",
    r"all.*pass",
    r"ready for review",
    r"EXIT_SIGNAL:\s*true",
    r"criteria\s*met",
    r"success",
]
MIN_COMPLETION_INDICATORS = 0  # Disabled - scores passing is sufficient

# Model configuration - with fallback for rate limits
PRIMARY_MODEL = "llama-3.3-70b-versatile"    # Best quality, 100K tokens/day on free tier
FALLBACK_MODEL = "llama-3.1-8b-instant"       # Smaller, faster, separate quota
CURRENT_MODEL = PRIMARY_MODEL                  # Mutable - switches on rate limit

# Custom exception for rate limit that requires session pause
class DailyLimitExceeded(Exception):
    """Raised when we hit daily token limit and should pause the session"""
    def __init__(self, wait_seconds: int = 0, message: str = ""):
        self.wait_seconds = wait_seconds
        self.message = message
        super().__init__(message)

def groq_chat_with_retry(groq: Groq, messages: list, max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    Make Groq API call with rate limit handling.
    - Tries PRIMARY_MODEL first
    - Falls back to FALLBACK_MODEL on rate limit
    - Raises DailyLimitExceeded if both models are exhausted
    """
    global CURRENT_MODEL

    models_to_try = [CURRENT_MODEL]
    if CURRENT_MODEL == PRIMARY_MODEL:
        models_to_try.append(FALLBACK_MODEL)

    last_error = None
    for model in models_to_try:
        try:
            response = groq.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # If we got here with fallback, stick with it for this session
            if model == FALLBACK_MODEL and CURRENT_MODEL != FALLBACK_MODEL:
                CURRENT_MODEL = FALLBACK_MODEL
                print(f"      [RATE LIMIT] Switched to fallback model: {FALLBACK_MODEL}")
            return response.choices[0].message.content.strip()
        except RateLimitError as e:
            last_error = e
            error_msg = str(e)

            # Parse wait time from error message (e.g., "try again in 32m24s")
            wait_match = re.search(r'try again in (\d+)m(\d+)s', error_msg)
            if wait_match:
                wait_seconds = int(wait_match.group(1)) * 60 + int(wait_match.group(2))
            else:
                wait_seconds = 60  # Default 1 minute

            # Check if it's a daily limit (TPD) vs minute limit
            if "tokens per day" in error_msg.lower() or "tpd" in error_msg.lower():
                if model == FALLBACK_MODEL:
                    # Both models exhausted - need to pause session
                    raise DailyLimitExceeded(wait_seconds, f"Daily token limit exceeded for all models. Try again in {wait_seconds//60}m{wait_seconds%60}s")
                else:
                    print(f"      [RATE LIMIT] {PRIMARY_MODEL} daily limit hit, trying fallback...")
                    continue
            else:
                # Short-term rate limit - wait and retry same model
                print(f"      [RATE LIMIT] Minute limit hit, waiting {wait_seconds}s...")
                time.sleep(min(wait_seconds, 120))  # Cap wait at 2 minutes
                # Retry same model after wait
                try:
                    response = groq.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].message.content.strip()
                except RateLimitError:
                    continue  # Try fallback model

    # If we get here, all retries failed
    raise DailyLimitExceeded(1800, f"All rate limit retries exhausted: {last_error}")

# =============================================================================
# Test Scenarios - Real Twitter Spaces / Livestream Situations
# =============================================================================

TEST_SCENARIOS = {
    "greetings": [
        {"input": "Hello everyone", "context": "Opening a Twitter Space"},
        {"input": "What's up", "context": "Casual greeting"},
        {"input": "Hey hey hey", "context": "Energetic welcome"},
        {"input": "Welcome back", "context": "Returning viewers"},
        {"input": "Good morning", "context": "Morning stream"},
    ],
    "reactions": [
        {"input": "That's amazing!", "context": "Reacting to good news"},
        {"input": "No way!", "context": "Surprised"},
        {"input": "I love that", "context": "Appreciation"},
        {"input": "That's terrible", "context": "Bad news"},
        {"input": "Interesting", "context": "Thoughtful"},
        {"input": "I agree", "context": "Agreement"},
        {"input": "I disagree", "context": "Polite disagreement"},
        {"input": "That's funny", "context": "Reacting to humor"},
    ],
    "questions": [
        {"input": "What do you think?", "context": "Asking opinion"},
        {"input": "Can you explain?", "context": "Clarification"},
        {"input": "How does that work?", "context": "Understanding"},
        {"input": "Why is that?", "context": "Seeking reason"},
        {"input": "What's your take?", "context": "Viewpoint"},
    ],
    "explanations": [
        {"input": "Let me tell you about this", "context": "Starting explanation"},
        {"input": "The thing is", "context": "Making a point"},
        {"input": "Here's what I learned", "context": "Sharing knowledge"},
        {"input": "The way I see it", "context": "Perspective"},
        {"input": "Check this out", "context": "Showing something"},
    ],
    "transitions": [
        {"input": "Anyway", "context": "Topic change"},
        {"input": "Moving on", "context": "Transition"},
        {"input": "Speaking of which", "context": "Connection"},
        {"input": "But yeah", "context": "Casual transition"},
        {"input": "So basically", "context": "Summary"},
    ],
    "farewells": [
        {"input": "See you later", "context": "Ending"},
        {"input": "Take care everyone", "context": "Closing"},
        {"input": "Peace out", "context": "Casual goodbye"},
        {"input": "Until next time", "context": "Outro"},
        {"input": "Thanks for joining", "context": "Gratitude"},
    ],
    "emotions": [
        {"input": "I'm so excited", "context": "Joy"},
        {"input": "This makes me happy", "context": "Happiness"},
        {"input": "I'm a bit worried", "context": "Concern"},
        {"input": "This is frustrating", "context": "Frustration"},
        {"input": "I appreciate you all", "context": "Gratitude"},
    ],
    "cannabis_context": [
        {"input": "Look at this plant", "context": "Showing grow"},
        {"input": "The leaves are healthy", "context": "Plant update"},
        {"input": "Time to water", "context": "Cultivation"},
        {"input": "Check out these trichomes", "context": "Harvest talk"},
    ],
    "mon_token": [
        {"input": "Check out the MON token", "context": "Crypto"},
        {"input": "MON is looking good", "context": "Market"},
        {"input": "The community is growing", "context": "Token community"},
    ],
}

# =============================================================================
# State Management
# =============================================================================

@dataclass
class LoopState:
    iteration: int = 0
    scores: Dict = field(default_factory=dict)
    best_scores: Dict = field(default_factory=dict)
    best_prompt: str = ""
    current_prompt: str = ""
    history: List = field(default_factory=list)
    changes_made: List = field(default_factory=list)
    research_done: List = field(default_factory=list)
    no_progress_count: int = 0
    total_improvements: int = 0
    exit_signal: bool = False
    started_at: str = ""
    last_updated: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


def load_state() -> LoopState:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        return LoopState(**data)
    return LoopState()


def save_state(state: LoopState):
    state.last_updated = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(asdict(state), indent=2))


def log_learning(message: str, level: str = "INFO"):
    """Append to markdown learnings file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not LEARNINGS_FILE.exists():
        LEARNINGS_FILE.write_text("# Ralph Loop Learnings\n\nTracking what works and what doesn't.\n\n---\n\n")

    with open(LEARNINGS_FILE, "a") as f:
        f.write(f"### [{timestamp}] {level}\n{message}\n\n")


# =============================================================================
# Rate Limiting (per Huntley best practices)
# =============================================================================

def check_rate_limit() -> Tuple[bool, int]:
    """Check if we're within rate limits. Returns (allowed, calls_this_hour)"""
    now = datetime.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    if CALL_LOG_FILE.exists():
        calls = json.loads(CALL_LOG_FILE.read_text())
    else:
        calls = []

    # Filter to calls in current hour
    calls_this_hour = [c for c in calls if datetime.fromisoformat(c) >= hour_start]

    return len(calls_this_hour) < MAX_CALLS_PER_HOUR, len(calls_this_hour)


def log_api_call():
    """Log an API call for rate limiting"""
    now = datetime.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    if CALL_LOG_FILE.exists():
        calls = json.loads(CALL_LOG_FILE.read_text())
    else:
        calls = []

    # Keep only calls from current hour
    calls = [c for c in calls if datetime.fromisoformat(c) >= hour_start]
    calls.append(now.isoformat())

    CALL_LOG_FILE.write_text(json.dumps(calls))


# =============================================================================
# Session Management (per frankbria best practices)
# =============================================================================

def get_or_create_session() -> str:
    """Get current session ID or create new one"""
    import uuid

    if SESSION_FILE.exists():
        session_data = json.loads(SESSION_FILE.read_text())
        expires = datetime.fromisoformat(session_data["expires"])
        if datetime.now() < expires:
            return session_data["session_id"]

    # Create new session
    session_id = str(uuid.uuid4())[:8]
    expires = datetime.now() + timedelta(hours=SESSION_TIMEOUT_HOURS)
    SESSION_FILE.write_text(json.dumps({
        "session_id": session_id,
        "created": datetime.now().isoformat(),
        "expires": expires.isoformat()
    }))
    return session_id


def reset_session():
    """Reset session (called on circuit breaker or completion)"""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


# =============================================================================
# Dual-Gate Completion Detection (per Huntley/frankbria best practices)
# =============================================================================

def count_completion_indicators(text: str) -> int:
    """Count how many completion patterns match in text"""
    count = 0
    text_lower = text.lower()
    for pattern in COMPLETION_PATTERNS:
        if re.search(pattern, text_lower):
            count += 1
    return count


def check_dual_gate_completion(scores: Dict, evaluation_text: str) -> Tuple[bool, str]:
    """
    Dual-gate completion check per Huntley best practices:
    - Gate 1: All score thresholds met
    - Gate 2: At least MIN_COMPLETION_INDICATORS heuristic matches

    Returns (is_complete, reason)
    """
    # Gate 1: Score thresholds
    score_failures = []
    for criterion, threshold in THRESHOLDS.items():
        score = scores.get(criterion, 0)
        if score < threshold:
            score_failures.append(f"{criterion}: {score}/{threshold}")

    gate1_passed = len(score_failures) == 0

    # Gate 2: Completion indicators
    indicators = count_completion_indicators(evaluation_text)
    gate2_passed = indicators >= MIN_COMPLETION_INDICATORS

    if gate1_passed and gate2_passed:
        return True, f"DUAL-GATE COMPLETE: scores passed + {indicators} indicators"

    if gate1_passed and not gate2_passed:
        return False, f"Scores passed but only {indicators} indicators (need {MIN_COMPLETION_INDICATORS})"

    if not gate1_passed and gate2_passed:
        return False, f"Indicators OK but scores failing: {score_failures}"

    return False, f"Both gates failing: scores={score_failures}, indicators={indicators}"


# =============================================================================
# Prompt Management - Actually Read/Write the Prompt
# =============================================================================

def get_current_prompt() -> str:
    """Extract IRIE_PROMPT from rasta_live.py"""
    content = PROMPT_FILE.read_text(encoding='utf-8')
    start = content.find('IRIE_PROMPT = """')
    if start == -1:
        raise ValueError("Could not find IRIE_PROMPT in rasta_live.py")
    start += len('IRIE_PROMPT = """')
    end = content.find('"""', start)
    return content[start:end]


def update_prompt(new_prompt: str) -> bool:
    """Actually update the prompt in rasta_live.py"""
    content = PROMPT_FILE.read_text(encoding='utf-8')
    start = content.find('IRIE_PROMPT = """')
    if start == -1:
        return False
    start += len('IRIE_PROMPT = """')
    end = content.find('"""', start)

    new_content = content[:start] + new_prompt + content[end:]
    PROMPT_FILE.write_text(new_content, encoding='utf-8')
    return True


# =============================================================================
# Generator - Run Tests Through Current Prompt
# =============================================================================

def generate_output(text: str, prompt: str, groq: Groq) -> str:
    """Transform single input using current prompt"""
    word_count = len(text.split())
    max_tokens = 30 if word_count <= 5 else 50 if word_count <= 12 else 80

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.6,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def run_test_batch(prompt: str, groq: Groq, sample_size: int = 3) -> List[Dict]:
    """Run randomized test batch"""
    results = []
    for category, scenarios in TEST_SCENARIOS.items():
        selected = random.sample(scenarios, min(sample_size, len(scenarios)))
        for scenario in selected:
            try:
                output = generate_output(scenario["input"], prompt, groq)
                results.append({
                    "category": category,
                    "input": scenario["input"],
                    "context": scenario["context"],
                    "output": output,
                })
            except Exception as e:
                results.append({
                    "category": category,
                    "input": scenario["input"],
                    "context": scenario["context"],
                    "output": f"ERROR: {e}",
                })
    return results


# =============================================================================
# Evaluator - Critical Analysis with Specific Feedback
# =============================================================================

EVALUATOR_PROMPT = """You are evaluating a Jamaican Rasta voice transformer for live Twitter Spaces.

PRIORITY ORDER: Funny > Not Boring > Not Repetitive > Warm > Everything Else
Stereotypical patois is FINE as long as it's entertaining!

KEY PRINCIPLE: Response length should be FLEXIBLE and guided by input:
- Short inputs ("Hello") = short outputs are fine
- Longer/complex inputs = can have longer, more elaborate responses
- Variety in response LENGTH is good too!

SCORE EACH CRITERION 1-10:

1. HUMOR (MOST IMPORTANT): Does it make you SMILE?
   - FAIL: Boring, dry, no personality, just translating words
   - FAIL: Same joke structure every time
   - PASS: Cheeky, playful, makes you grin
   - BONUS: Unexpected twists, wordplay, personality shines through

2. VARIETY: Is each response DIFFERENT and UNPREDICTABLE?
   - FAIL: Same phrases repeating ("Seen", "Jah bless" in every response)
   - FAIL: Same sentence pattern every time
   - FAIL: You can predict what's coming next
   - PASS: Fresh expressions, varied structure, keeps you guessing

3. ENTERTAINMENT: Would you want to KEEP LISTENING?
   - FAIL: Boring, monotonous, feels like a chore
   - FAIL: Too much, exhausting, trying too hard
   - PASS: Fun to listen to, has energy, engaging
   - BONUS: You'd tune in to hear more

4. WARMTH: Does it feel FRIENDLY and welcoming?
   - FAIL: Cold, distant, preachy, lecturing
   - PASS: Like talking to a fun friend at a party

5. FLOW: Easy to say out loud in live conversation?
   - FAIL: Too long, breaks rhythm
   - FAIL: Awkward phrasing
   - PASS: Natural conversational length, rolls off the tongue

6. NATURALNESS: Sounds like a person (not AI)?
   - FAIL: "I'd be happy to", "Here's", "Sure!", robotic phrases
   - PASS: Could be someone actually talking

7. AUTHENTICITY: Reasonably Jamaican? (can be a bit stereotypical!)
   - FAIL: Completely wrong, no patois at all
   - PASS: Has the vibe, uses patois, sounds Caribbean
   - NOTE: Tourist-level patois is OK if it's funny and entertaining!

MAIN ANTI-PATTERNS (what makes it BORING):
- REPETITIVE: Same words/phrases every response - THE WORST SIN
- PREDICTABLE: You know exactly what's coming
- BORING: No personality, just mechanical translation
- EXHAUSTING: Every single response is "too much"

THE REAL TEST: Would listeners:
a) Laugh or smile? (HUMOR)
b) Be surprised by what comes next? (VARIETY)
c) Want to keep listening? (ENTERTAINMENT)
d) Feel like they're with a friend? (WARMTH)

For low scores, give SPECIFIC examples and CONCRETE prompt fixes.

OUTPUT AS JSON:
{
    "scores": {"humor": N, "variety": N, "entertainment": N, "warmth": N, "flow": N, "naturalness": N, "authenticity": N},
    "average": N.N,
    "worst_category": "name",
    "anti_patterns_detected": ["REPETITIVE", "PREDICTABLE", "BORING", etc],
    "specific_failures": [
        {"input": "...", "output": "...", "problem": "...", "suggestion": "..."}
    ],
    "prompt_changes": [
        {"action": "add|remove|modify", "target": "what to change", "new_text": "replacement", "reason": "why"}
    ]
}"""


def evaluate_outputs(results: List[Dict], groq: Groq) -> Dict:
    """Get detailed evaluation with specific improvement suggestions"""
    results_text = "\n\n".join([
        f"[{r['category']}] {r['context']}\nIN: \"{r['input']}\"\nOUT: \"{r['output']}\""
        for r in results
    ])

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": EVALUATOR_PROMPT},
            {"role": "user", "content": f"Evaluate:\n\n{results_text}"}
        ],
        temperature=0.2,
        max_tokens=2500,
    )

    content = response.choices[0].message.content
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
    except:
        pass

    return {
        "scores": {k: 5 for k in THRESHOLDS.keys()},
        "average": 5,
        "worst_category": "humor",  # Start by fixing humor first
        "anti_patterns_detected": [],
        "specific_failures": [],
        "prompt_changes": []
    }


# =============================================================================
# Deep Analysis - Sequential Thinking for Hard Problems
# =============================================================================

DEEP_ANALYSIS_PROMPT = """You are analyzing why a Jamaican Rasta voice transformer is failing on specific criteria.

CURRENT PROBLEM: {problem}
CURRENT SCORE: {score}/10 (need {threshold})

FAILING EXAMPLES:
{examples}

CURRENT PROMPT EXCERPT (relevant section):
{prompt_section}

Think step by step:
1. What EXACTLY is wrong with the outputs?
2. What in the prompt is CAUSING this?
3. What SPECIFIC change would fix it?
4. How can we make this change WITHOUT breaking other things?

Be SPECIFIC. Give exact text to add/remove/change."""


def deep_analyze(problem: str, score: int, threshold: int,
                 examples: List[Dict], prompt: str, groq: Groq) -> Dict:
    """Deep sequential analysis of a specific problem"""

    # Extract relevant prompt section
    prompt_lower = problem.lower()
    if "natural" in prompt_lower or "ai" in prompt_lower:
        section = "OUTPUT ONLY" in prompt and prompt[prompt.find("OUTPUT"):prompt.find("OUTPUT")+500]
    elif "warm" in prompt_lower or "friendly" in prompt_lower:
        section = "PERSONALITY" in prompt and prompt[prompt.find("PERSONALITY"):prompt.find("PERSONALITY")+500]
    elif "authentic" in prompt_lower or "patois" in prompt_lower:
        section = "PATOIS" in prompt and prompt[prompt.find("PATOIS"):prompt.find("PATOIS")+500]
    else:
        section = prompt[:1000]

    examples_text = "\n".join([
        f"IN: \"{e.get('input', '')}\"\nOUT: \"{e.get('output', '')}\"\nPROBLEM: {e.get('problem', '')}"
        for e in examples[:5]
    ])

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a prompt engineering expert. Be specific and actionable."},
            {"role": "user", "content": DEEP_ANALYSIS_PROMPT.format(
                problem=problem,
                score=score,
                threshold=threshold,
                examples=examples_text,
                prompt_section=section or prompt[:800]
            )}
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    return {
        "analysis": response.choices[0].message.content,
        "problem": problem,
        "score": score
    }


# =============================================================================
# Expression Bank - Rich Vocabulary Store for Variety
# =============================================================================

def load_expression_bank() -> dict:
    """Load or initialize the expression bank"""
    if EXPRESSION_BANK_FILE.exists():
        return json.loads(EXPRESSION_BANK_FILE.read_text())
    return {
        "greetings": [],
        "reactions_positive": [],
        "reactions_negative": [],
        "reactions_surprise": [],
        "reactions_agreement": [],
        "reactions_disagreement": [],
        "transitions": [],
        "farewells": [],
        "filler_phrases": [],
        "exclamations": [],
        "thinking_phrases": [],
        "emphasis_words": [],
        "sentence_starters": [],
        "sentence_enders": [],
        "mood_markers": [],  # [laughs], [sighs], etc.
        "persona_quirks": [],  # Unique personality traits
        "proverbs": [],
        "slang_modern": [],
        "slang_classic": [],
    }


def save_expression_bank(bank: dict):
    """Save expression bank to file"""
    EXPRESSION_BANK_FILE.write_text(json.dumps(bank, indent=2))


def build_expression_bank(groq: Groq) -> dict:
    """Build a rich expression bank through targeted research"""
    print("\n[RESEARCH] Building expression bank for variety...")

    bank = load_expression_bank()

    # Research topics for rich vocabulary
    research_queries = [
        ("greetings", "20 different Jamaican greetings - formal, casual, energetic, chill - with variety"),
        ("reactions_positive", "20 ways Jamaicans express excitement, joy, approval - varied intensity"),
        ("reactions_negative", "15 ways Jamaicans express disappointment, concern, mild frustration - not too negative"),
        ("reactions_surprise", "15 Jamaican expressions of surprise, shock, disbelief"),
        ("reactions_agreement", "15 ways to say 'yes', 'I agree', 'that's right' in Jamaican patois"),
        ("reactions_disagreement", "10 polite ways to disagree or express doubt in Jamaican"),
        ("transitions", "15 Jamaican transition phrases - 'anyway', 'so', 'moving on', 'but yeah'"),
        ("farewells", "15 Jamaican ways to say goodbye - casual, warm, until-next-time"),
        ("filler_phrases", "20 Jamaican filler/thinking phrases - 'you know', 'like', 'well'"),
        ("exclamations", "25 Jamaican exclamations - mild to strong, expressive"),
        ("sentence_starters", "20 ways to start sentences in patois - varied"),
        ("sentence_enders", "15 ways to end sentences - 'ya know', 'seen', 'mon'"),
        ("emphasis_words", "15 Jamaican emphasis/intensifier words"),
        ("proverbs", "10 Jamaican proverbs and wise sayings - short ones"),
        ("slang_modern", "15 modern Jamaican slang terms used by younger people"),
        ("persona_quirks", "10 personality quirks for a wise, funny, laid-back Rasta character"),
    ]

    for category, query in research_queries:
        if len(bank.get(category, [])) < 5:  # Only research if we need more
            print(f"      Researching: {category}")
            try:
                response = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a Jamaican language expert. Output ONLY a JSON array of strings. No explanation."},
                        {"role": "user", "content": f"Give me {query}. Output as JSON array: [\"phrase1\", \"phrase2\", ...]"}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                )
                content = response.choices[0].message.content
                # Parse JSON array
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end > start:
                    phrases = json.loads(content[start:end])
                    bank[category] = list(set(bank.get(category, []) + phrases))
                    print(f"        -> {len(phrases)} expressions")
            except Exception as e:
                print(f"        Error: {e}")
            time.sleep(0.3)  # Rate limit

    save_expression_bank(bank)
    total = sum(len(v) for v in bank.values())
    print(f"[RESEARCH] Expression bank: {total} total expressions")
    return bank


def research_persona_patterns(groq: Groq) -> str:
    """Research advanced persona context patterns to avoid repetition"""

    PERSONA_RESEARCH = """You are an expert in LLM prompt engineering and character design.

Research task: How to maintain VARIETY in a voice transformer persona without repetition.

The persona is a Jamaican Rasta character for live streaming. The problem is:
- LLMs tend to fall into repetitive patterns
- Same catch phrases over and over ("Seen", "Jah bless", "mon")
- Same sentence structures
- Predictable responses

I need ADVANCED TECHNIQUES for:

1. VOCABULARY ROTATION SYSTEMS
   - How to structure prompts to encourage variety
   - Anti-repetition instructions that work
   - Dynamic expression selection

2. CONTEXT INJECTION PATTERNS
   - How to give the LLM a "mood" that changes
   - Techniques for varied sentence structure
   - Ways to prevent formula responses

3. PERSONA DEPTH TECHNIQUES
   - Backstory elements that create natural variety
   - Situational personality shifts
   - Character quirks that add unpredictability

4. PROMPT ENGINEERING TRICKS
   - Negative examples (what NOT to do)
   - Explicit variety instructions
   - Temperature and sampling considerations

Output specific, actionable techniques with example prompt snippets."""

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a prompt engineering expert specializing in character personas."},
            {"role": "user", "content": PERSONA_RESEARCH}
        ],
        temperature=0.5,
        max_tokens=2500,
    )

    return response.choices[0].message.content


def research_variety_techniques(groq: Groq) -> str:
    """DEDICATED research on variety techniques for this exact situation"""

    VARIETY_RESEARCH = """You are an expert in LLM prompt engineering. I have a SPECIFIC problem:

SITUATION: Voice transformer for live Twitter Spaces
- Takes English input, outputs Jamaican Patois
- Response length is FLEXIBLE - guided by input length/complexity
- Short input = short output, longer input = can be longer output
- Used for LIVE conversation (needs to feel natural)
- Persona: Wise, funny, warm Rastafari elder

THE PROBLEM: REPETITION. The outputs fall into patterns:
- Same greeting every time ("Wah gwaan!")
- Same filler phrases ("mon", "seen", "Jah bless")
- Same sentence structure (greeting + phrase + ending)
- Predictable endings ("ya know", "seen")
- Same response LENGTH every time (too uniform)

I need SPECIFIC, ACTIONABLE techniques for THIS situation:

1. GREETING VARIETY SYSTEM
   - How to ensure 10+ different greeting styles rotate
   - Not just synonym swapping - different ENERGY and STRUCTURE
   - Some short ("Yo!"), some medium ("Bless up, fam!"), some longer

2. FILLER PHRASE ROTATION
   - How to NOT overuse "mon", "seen", "Jah bless"
   - Techniques to inject variety: word position, frequency limits
   - Explicit "AVOID using X more than once per 5 responses"

3. SENTENCE STRUCTURE VARIETY
   - Sometimes SHORT ("Irie!")
   - Sometimes QUESTION ("Yuh feel mi?")
   - Sometimes STATEMENT with flair
   - Sometimes start with the emotion, sometimes end with it

4. ENERGY/MOOD VARIETY
   - Not every response should be "hype"
   - Mix: chill, excited, thoughtful, playful, wise
   - How to instruct the LLM to vary energy WITHOUT explicit mood injection

5. ANTI-FORMULA INSTRUCTIONS
   - Exact wording to prevent "greeting + content + catchphrase" formula
   - How to say "NEVER use the same pattern twice in a row"
   - Specific negative examples with alternatives

6. DYNAMIC SELECTION TECHNIQUES
   - How to give the LLM a "bag" of options to pick from
   - Weighted randomization through prompt engineering
   - "Rotate between these" vs "Choose randomly from"

7. RESPONSE LENGTH FLEXIBILITY
   - How to instruct the LLM to vary response length based on INPUT
   - Short inputs ("Hello") = short output ("Wah gwaan!")
   - Medium inputs = medium outputs with personality
   - Longer/complex inputs = can be longer, more elaborate responses
   - Avoid uniform length - vary based on what the input deserves

OUTPUT FORMAT:
For each technique, give me:
- The exact prompt snippet to add
- Why it works
- Example outputs showing variety"""

    response = groq_chat_with_retry(
        groq,
        messages=[
            {"role": "system", "content": "You are a prompt engineering expert. Focus on PRACTICAL, SPECIFIC techniques."},
            {"role": "user", "content": VARIETY_RESEARCH}
        ],
        max_tokens=3000,
        temperature=0.6
    )

    return response


def research_anti_repetition_patterns(groq: Groq) -> str:
    """Research specific anti-repetition patterns that work for voice transformers"""

    ANTI_REP_RESEARCH = """Give me 10 SPECIFIC prompt engineering patterns to prevent repetition in LLM outputs.

CONTEXT: Voice transformer responses (FLEXIBLE length - guided by input complexity), Jamaican patois persona

For each pattern, provide:
1. The exact text to add to the prompt
2. Why it works psychologically/mechanically
3. Before/After example

FOCUS ON:
- Vocabulary lists with "rotate between" instructions
- Explicit "NEVER X" statements that actually work
- Structural variety instructions
- Energy/mood variation cues
- Memory-less approaches (each call is independent)

Example pattern format:
---
PATTERN: [Name]
ADD TO PROMPT: "[exact text]"
WHY: [explanation]
BEFORE: "Wah gwaan, mon! Dat nice, seen."
AFTER: "Bless up! [chuckles] Now dat a suppm, ya hear?"
---"""

    response = groq_chat_with_retry(
        groq,
        messages=[
            {"role": "system", "content": "Output exactly in the requested format. Be specific."},
            {"role": "user", "content": ANTI_REP_RESEARCH}
        ],
        max_tokens=2500,
        temperature=0.5
    )

    return response


# =============================================================================
# Research - Targeted Vocabulary Expansion
# =============================================================================

def do_research(topic: str, groq: Groq) -> str:
    """Research expressions for a specific need"""

    RESEARCH_PROMPT = f"""You are an expert in Jamaican Patois.

I need VARIED expressions for: {topic}

THE GOAL IS VARIETY - give me options that are DIFFERENT from each other.

Provide:
1. 10-15 expressions/phrases - each one DIFFERENT in structure and tone
2. Mix of: casual, energetic, chill, thoughtful moods
3. Some short (1-3 words), some medium (4-6 words)
4. Include modern slang AND classic patois

AVOID:
- Giving variations of the same phrase
- Over-relying on "mon", "Jah", "irie"
- Same sentence pattern repeated

Format as a simple list, one per line."""

    response = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a Jamaican language expert focused on VARIETY."},
            {"role": "user", "content": RESEARCH_PROMPT}
        ],
        temperature=0.7,  # Higher for more variety
        max_tokens=1000,
    )

    return response.choices[0].message.content


# =============================================================================
# Improver - Actually Modify the Prompt
# =============================================================================

IMPROVE_PROMPT = """You are a prompt engineer improving a Jamaican Rasta voice transformer for MAXIMUM VARIETY.

CURRENT PROMPT:
```
{current_prompt}
```

EVALUATION: Average {average}/10, Worst: {worst} ({worst_score}/10, need {threshold})
VARIETY IS #1 PRIORITY - must reach 9/10

SPECIFIC FAILURES:
{failures}

SUGGESTED CHANGES:
{suggestions}

RESEARCH:
{research}

EXPRESSION BANK:
{expression_bank_summary}

VARIETY RESEARCH:
{variety_research}

=== THE VARIETY-FIRST PROMPT STRUCTURE THAT WORKS ===

Your improved prompt MUST follow this structure:
1. START with "=== VARIETY IS YOUR #1 PRIORITY ===" at the very top
2. Include FORBIDDEN PATTERNS section (what NOT to do) BEFORE any options
3. Use TIERED GREETINGS (A/B/C/D tiers) with explicit "never same tier twice"
4. Include DICE ROLL or RANDOMIZATION instructions (mentally pick 1-20)
5. List RESPONSE OPENERS beyond greetings (reactions, questions, direct jumps)
6. Keep character brief, then tools for variety
7. End with THE GOAL statement about unpredictability

KEY FORBIDDEN PATTERNS TO INCLUDE:
- NEVER start with "Pure niceness" more than once
- NEVER start consecutive responses the same way
- NEVER use "seen" or "mon" in every response
- AVOID formula: greeting + content + catchphrase

VARIETY TECHNIQUES:
- Multiple opener types (not just greetings)
- Energy dice roll (1-5 chill, 6-10 medium, 11-15 hype, 16-20 thoughtful)
- Tiered vocabulary (pick from different tiers)
- Mix response lengths

KEEP PROMPT UNDER 2500 CHARACTERS - shorter prompts with clear structure beat long verbose ones.

OUTPUT THE COMPLETE NEW PROMPT. Start with "===" on line 1."""


def generate_improved_prompt(state: LoopState, evaluation: Dict,
                            research: str, groq: Groq) -> str:
    """Generate an improved version of the prompt"""

    failures_text = "\n".join([
        f"- {f.get('input', 'N/A')} -> {f.get('output', 'N/A')}: {f.get('problem', 'N/A')}"
        for f in evaluation.get("specific_failures", [])[:5]
    ])

    suggestions_text = "\n".join([
        f"- {c.get('action', 'N/A')} '{c.get('target', 'N/A')}': {c.get('reason', 'N/A')}"
        for c in evaluation.get("prompt_changes", [])[:5]
    ])

    worst = evaluation.get("worst_category", "unknown")
    scores = evaluation.get("scores", {})

    # Load expression bank for variety suggestions
    expression_bank = load_expression_bank()
    bank_summary_parts = []
    for category, phrases in expression_bank.items():
        if phrases:
            # Show a sample of phrases from each category
            sample = random.sample(phrases, min(5, len(phrases)))
            bank_summary_parts.append(f"{category}: {', '.join(sample)}")
    expression_bank_summary = "\n".join(bank_summary_parts[:10]) if bank_summary_parts else "Not yet built"

    # Load variety research from learnings file if available
    variety_research = ""
    if LEARNINGS_FILE.exists():
        learnings_content = LEARNINGS_FILE.read_text()
        # Extract variety techniques section
        if "Variety Techniques Research" in learnings_content:
            start = learnings_content.find("Variety Techniques Research")
            end = learnings_content.find("###", start + 50)  # Find next section
            if end == -1:
                end = min(start + 3000, len(learnings_content))
            variety_research = learnings_content[start:end][:1500]  # Limit to 1500 chars

    response = groq_chat_with_retry(
        groq,
        messages=[
            {"role": "system", "content": "You are an expert prompt engineer. Output ONLY the improved prompt."},
            {"role": "user", "content": IMPROVE_PROMPT.format(
                current_prompt=state.current_prompt,
                scores=json.dumps(scores),
                average=evaluation.get("average", 5),
                worst=worst,
                worst_score=scores.get(worst, 5),
                threshold=THRESHOLDS.get(worst, 8),
                failures=failures_text or "None specified",
                suggestions=suggestions_text or "None specified",
                research=research or "None",
                expression_bank_summary=expression_bank_summary,
                variety_research=variety_research or "Research variety techniques during Phase 0"
            )}
        ],
        max_tokens=3500,
        temperature=0.5
    )

    return response


# =============================================================================
# Completion Check
# =============================================================================

def check_completion(scores: Dict) -> Tuple[bool, List[str]]:
    """Check if all criteria meet thresholds, return failures"""
    failures = []
    for criterion, threshold in THRESHOLDS.items():
        score = scores.get(criterion, 0)
        if score < threshold:
            failures.append(f"{criterion}: {score}/{threshold}")
    return len(failures) == 0, failures


def calculate_progress(current: Dict, previous: Dict) -> float:
    """Calculate improvement from previous iteration"""
    if not previous:
        return 1.0
    current_avg = sum(current.values()) / len(current) if current else 0
    previous_avg = sum(previous.values()) / len(previous) if previous else 0
    return current_avg - previous_avg


# =============================================================================
# Main Loop
# =============================================================================

def run_ralph_loop(max_iterations: int = 1000, continue_session: bool = False):
    """Execute the intelligent Ralph Loop"""

    print("=" * 70)
    print("RASTA VOICE RALPH LOOP - Intelligent Iteration")
    print("=" * 70)
    print(f"Thresholds: {THRESHOLDS}")
    print(f"Max iterations: {max_iterations} (exits early on completion)")
    print()

    # Session management (per Huntley best practices)
    session_id = get_or_create_session()
    print(f"[SESSION] ID: {session_id}")

    # Rate limit check
    allowed, calls_this_hour = check_rate_limit()
    print(f"[RATE LIMIT] {calls_this_hour}/{MAX_CALLS_PER_HOUR} calls this hour")
    if not allowed:
        print("[RATE LIMIT] EXCEEDED - waiting until next hour")
        log_learning("Rate limit exceeded - pausing", "WARNING")
        return None

    LOGS_DIR.mkdir(exist_ok=True)

    if continue_session and STATE_FILE.exists():
        state = load_state()
        print(f"[RESUME] Iteration {state.iteration}, avg score: {sum(state.scores.values())/max(len(state.scores),1):.1f}")
    else:
        state = LoopState()
        state.current_prompt = get_current_prompt()
        state.best_prompt = state.current_prompt
        print("[START] Fresh loop")

    groq = Groq(api_key=GROQ_KEY)

    # =========================================================================
    # PHASE 0: Build expression bank and research VARIETY techniques (first run)
    # =========================================================================
    if state.iteration == 0:
        print("\n" + "=" * 70)
        print("PHASE 0: Building Rich Context for VARIETY (#1 Priority)")
        print("=" * 70)

        # Build expression bank
        expression_bank = build_expression_bank(groq)

        # Research advanced persona patterns
        print("\n[RESEARCH] Researching persona context patterns...")
        persona_patterns = research_persona_patterns(groq)
        log_learning(f"# Persona Pattern Research\n\n{persona_patterns}", "RESEARCH")
        print(f"[RESEARCH] Saved {len(persona_patterns)} chars of persona research")

        # NEW: Research VARIETY-SPECIFIC techniques (this is the key addition)
        print("\n[RESEARCH] Researching VARIETY techniques for this exact situation...")
        variety_techniques = research_variety_techniques(groq)
        log_learning(f"# Variety Techniques Research (CRITICAL)\n\n{variety_techniques}", "RESEARCH")
        print(f"[RESEARCH] Saved {len(variety_techniques)} chars of variety techniques")

        # NEW: Research anti-repetition patterns
        print("\n[RESEARCH] Researching anti-repetition patterns...")
        anti_rep_patterns = research_anti_repetition_patterns(groq)
        log_learning(f"# Anti-Repetition Patterns\n\n{anti_rep_patterns}", "RESEARCH")
        print(f"[RESEARCH] Saved {len(anti_rep_patterns)} chars of anti-repetition patterns")

        # Inject expression bank summary into state for improver
        state.research_done.append({
            "iteration": 0,
            "topic": "expression_bank",
            "categories": list(expression_bank.keys()),
            "total_expressions": sum(len(v) for v in expression_bank.values())
        })
        state.research_done.append({
            "iteration": 0,
            "topic": "persona_patterns",
            "length": len(persona_patterns)
        })
        state.research_done.append({
            "iteration": 0,
            "topic": "variety_techniques",
            "length": len(variety_techniques)
        })
        state.research_done.append({
            "iteration": 0,
            "topic": "anti_repetition_patterns",
            "length": len(anti_rep_patterns)
        })

    log_learning(f"# Loop Started\nMax iterations: {max_iterations}\nThresholds: {THRESHOLDS}", "START")

    while state.iteration < max_iterations:
        state.iteration += 1
        iteration_start = time.time()

        print(f"\n{'='*70}")
        print(f"ITERATION {state.iteration}")
        print("=" * 70)

        # =====================================================================
        # STEP 1: Generate test outputs with current prompt
        # =====================================================================
        print("\n[1/5] GENERATING outputs...")
        state.current_prompt = get_current_prompt()  # Re-read in case modified
        results = run_test_batch(state.current_prompt, groq, sample_size=2)
        print(f"      {len(results)} test cases")

        # Show examples
        for r in random.sample(results, min(3, len(results))):
            print(f"      \"{r['input'][:25]}\" -> \"{r['output'][:40]}...\"")

        # =====================================================================
        # STEP 2: Evaluate critically
        # =====================================================================
        print("\n[2/5] EVALUATING...")
        evaluation = evaluate_outputs(results, groq)
        state.scores = evaluation.get("scores", {})
        avg = evaluation.get("average", 5)

        print(f"      Average: {avg:.1f}/10")
        for k, v in state.scores.items():
            thresh = THRESHOLDS.get(k, 8)
            status = "OK" if v >= thresh else "FAIL"
            print(f"      {k:12}: {v}/10 ({status}, need {thresh})")

        # Update best scores
        for k, v in state.scores.items():
            if v > state.best_scores.get(k, 0):
                state.best_scores[k] = v
                if avg > sum(state.best_scores.values()) / max(len(state.best_scores), 1) - 0.5:
                    state.best_prompt = state.current_prompt

        # =====================================================================
        # STEP 3: Check completion (DUAL-GATE per Huntley best practices)
        # =====================================================================
        print("\n[3/5] CHECKING completion (dual-gate)...")

        # Get evaluation text for completion indicator detection
        eval_text = json.dumps(evaluation) if evaluation else ""
        complete, gate_reason = check_dual_gate_completion(state.scores, eval_text)

        print(f"      {gate_reason}")

        if complete:
            state.exit_signal = True
            save_state(state)
            reset_session()  # Clean session on completion

            print("\n" + "=" * 70)
            print("DUAL-GATE COMPLETION ACHIEVED!")
            print("=" * 70)
            print(f"Final scores: {state.scores}")
            print(f"Iterations: {state.iteration}")
            print(f"Total improvements: {state.total_improvements}")
            print(f"Completion: {gate_reason}")

            log_learning(f"# DUAL-GATE COMPLETE!\n{gate_reason}\nFinal scores: {state.scores}\nIterations: {state.iteration}", "SUCCESS")
            return state

        # Get failures for display
        _, failures = check_completion(state.scores)
        print(f"      Remaining thresholds: {failures}")

        # Check progress
        prev_scores = state.history[-1]["scores"] if state.history else {}
        progress = calculate_progress(state.scores, prev_scores)

        if progress < MIN_PROGRESS_THRESHOLD:
            state.no_progress_count += 1
            print(f"      WARNING: Low progress ({progress:.2f}), streak: {state.no_progress_count}")
        else:
            state.no_progress_count = 0
            print(f"      Progress: +{progress:.2f}")

        if state.no_progress_count >= MAX_NO_PROGRESS_LOOPS:
            print("\n[CIRCUIT BREAK] No progress for too long")
            print("Reverting to best prompt and trying different approach...")
            state.current_prompt = state.best_prompt
            update_prompt(state.best_prompt)
            state.no_progress_count = 0
            reset_session()  # Fresh session after circuit break (per Huntley)
            log_learning("Circuit break triggered - reverted to best prompt, session reset", "WARNING")

        # Log API calls for rate limiting (after each major step)
        log_api_call()

        # Re-check rate limit mid-iteration
        allowed, calls = check_rate_limit()
        if not allowed:
            print(f"\n[RATE LIMIT] Hit {calls}/{MAX_CALLS_PER_HOUR} calls - pausing iteration")
            save_state(state)
            return state

        # =====================================================================
        # STEP 4: Deep analysis & research for worst problems
        # =====================================================================
        print("\n[4/5] ANALYZING problems...")

        worst = evaluation.get("worst_category", "naturalness")
        worst_score = state.scores.get(worst, 5)

        # Do research if variety/humor is low - need fresh material
        research = ""
        if worst in ["variety", "humor", "entertainment"] and worst_score < 7:
            print(f"      Researching fresh expressions for: {worst}")
            research = do_research(f"funny and varied Jamaican expressions, slang, and reactions for {worst} - need unpredictable options", groq)
            state.research_done.append({"iteration": state.iteration, "topic": worst})
            print(f"      Got {len(research)} chars of research")

        # Deep analysis of worst problem
        if evaluation.get("specific_failures"):
            print(f"      Deep analyzing: {worst} ({worst_score}/10)")
            analysis = deep_analyze(
                worst, worst_score, THRESHOLDS.get(worst, 8),
                evaluation.get("specific_failures", []),
                state.current_prompt, groq
            )
            print(f"      Analysis: {analysis['analysis'][:100]}...")
        else:
            analysis = None

        # =====================================================================
        # STEP 5: Generate and apply improved prompt
        # =====================================================================
        print("\n[5/5] IMPROVING prompt...")

        new_prompt = generate_improved_prompt(state, evaluation, research, groq)

        if new_prompt and len(new_prompt) > 100 and len(new_prompt) < 5500:
            # Validate it's actually different
            if new_prompt != state.current_prompt:
                update_prompt(new_prompt)
                state.total_improvements += 1

                change_summary = f"Iteration {state.iteration}: Focused on {worst} ({worst_score}->{THRESHOLDS.get(worst, 8)})"
                state.changes_made.append({
                    "iteration": state.iteration,
                    "target": worst,
                    "before_score": worst_score,
                    "prompt_length": len(new_prompt)
                })
                print(f"      Applied new prompt ({len(new_prompt)} chars)")
                log_learning(f"**Applied change:** {change_summary}\n\nTargeted: {worst}", "CHANGE")
            else:
                print("      No significant changes generated")
        else:
            print(f"      Invalid prompt generated ({len(new_prompt) if new_prompt else 0} chars)")

        # Record history
        state.history.append({
            "iteration": state.iteration,
            "scores": state.scores.copy(),
            "average": avg,
            "worst": worst,
            "progress": progress
        })

        # Save state
        save_state(state)

        # Save iteration log
        log_file = LOGS_DIR / f"iter_{state.iteration:04d}.json"
        log_file.write_text(json.dumps({
            "iteration": state.iteration,
            "scores": state.scores,
            "evaluation": evaluation,
            "results_sample": results[:5],
            "research": research[:500] if research else None,
            "analysis": analysis
        }, indent=2))

        elapsed = time.time() - iteration_start
        print(f"\n[TIME] {elapsed:.1f}s | Best avg: {sum(state.best_scores.values())/max(len(state.best_scores),1):.1f}")

        # Brief pause
        time.sleep(0.5)

    print("\n" + "=" * 70)
    print("MAX ITERATIONS REACHED")
    print("=" * 70)
    print(f"Best scores: {state.best_scores}")
    print(f"Run with --continue to keep going")

    return state


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rasta Voice Ralph Loop")
    parser.add_argument("--max-iterations", type=int, default=1000,
                        help="Max iterations (default: 1000, exits on completion)")
    parser.add_argument("--continue", dest="continue_session", action="store_true",
                        help="Continue from previous state")
    parser.add_argument("--reset", action="store_true",
                        help="Reset state and start fresh")
    parser.add_argument("--status", action="store_true",
                        help="Show current state")
    args = parser.parse_args()

    if args.reset:
        for f in [STATE_FILE, LEARNINGS_FILE]:
            if f.exists():
                f.unlink()
        if LOGS_DIR.exists():
            for log in LOGS_DIR.glob("*.json"):
                log.unlink()
        print("State reset.")
        sys.exit(0)

    if args.status:
        if STATE_FILE.exists():
            state = load_state()
            print(f"Iteration: {state.iteration}")
            print(f"Current scores: {state.scores}")
            print(f"Best scores: {state.best_scores}")
            print(f"Total improvements: {state.total_improvements}")
            print(f"No-progress streak: {state.no_progress_count}")

            complete, failures = check_completion(state.scores)
            if complete:
                print("STATUS: COMPLETE!")
            else:
                print(f"STATUS: In progress, failing: {failures}")
        else:
            print("No state file. Run without --status to start.")
        sys.exit(0)

    if not GROQ_KEY:
        print("[ERROR] GROQ_API_KEY not set")
        sys.exit(1)

    try:
        run_ralph_loop(
            max_iterations=args.max_iterations,
            continue_session=args.continue_session
        )
    except DailyLimitExceeded as e:
        print(f"\n{'='*70}")
        print("[DAILY LIMIT] Groq API daily token limit exceeded")
        print("='*70")
        print(f"{e.message}")
        wait_mins = e.wait_seconds // 60
        print(f"\nState saved. Run with --continue in ~{wait_mins} minutes to resume.")
        log_learning(f"Daily limit hit. Wait {wait_mins}m to continue.", "RATE_LIMIT")
        sys.exit(2)  # Exit code 2 = rate limit
    except RateLimitError as e:
        print(f"\n{'='*70}")
        print("[RATE LIMIT] Groq API rate limit exceeded")
        print("='*70")
        print(f"{e}")
        print("\nState saved. Run with --continue after the wait period.")
        log_learning(f"Rate limit error: {e}", "RATE_LIMIT")
        sys.exit(2)
