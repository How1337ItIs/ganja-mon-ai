#!/bin/bash
# Test unified agentic brain
curl -s --max-time 120 -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Full status report across grow trading social blockchain"}' \
  > /tmp/ut.json 2>&1

echo "HTTP_DONE"

python3 << 'PYEOF'
import json
try:
    d = json.load(open("/tmp/ut.json"))
    print("SUCCESS:", d.get("success"))
    print("ROUNDS:", d.get("tool_rounds", 0))
    print("TOKENS:", d.get("tokens_used", 0))
    print("ACTIONS:", len(d.get("actions_taken", [])))
    print()
    print("OUTPUT (first 600 chars):")
    print(d.get("output_text", "?")[:600])
except Exception as e:
    print("PARSE ERROR:", e)
    import os
    sz = os.path.getsize("/tmp/ut.json") if os.path.exists("/tmp/ut.json") else 0
    print("File size:", sz)
    if sz < 500:
        print(open("/tmp/ut.json").read())
PYEOF
