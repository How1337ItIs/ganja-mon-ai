#!/bin/bash
# Test the unified brain with money/alpha awareness
curl -s --max-time 120 -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What alpha opportunities do you see right now? How is the portfolio doing? Is Mon healthy? Give me your money_thesis."}' \
  > /tmp/money_test.json

# Extract key fields
python3 << 'EOF'
import json
d = json.load(open("/tmp/money_test.json"))

print("=== MONEY BRAIN TEST ===")
print(f"SUCCESS: {d.get('success')}")
print(f"ROUNDS: {d.get('tool_rounds')}")
print(f"TOKENS: {d.get('tokens_used')}")
print(f"ACTIONS: {len(d.get('actions_taken', []))}")

text = d.get("output", "")
# Check for key money terms
money_terms = ["money_thesis", "alpha", "portfolio", "revenue", "buyback", "arbitrage", "profit"]
found = [t for t in money_terms if t.lower() in text.lower()]
print(f"\nMONEY TERMS FOUND: {found}")

soul_terms = ["soul", "sacred", "jah", "healing", "one love"]
found_soul = [t for t in soul_terms if t.lower() in text.lower()]
print(f"SOUL TERMS FOUND: {found_soul}")

# Print first 800 chars
print(f"\nOUTPUT (first 800 chars):")
print(text[:800])
EOF
