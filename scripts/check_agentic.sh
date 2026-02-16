#!/bin/bash
# Check agentic features status
LOG=/tmp/gm_big.txt
journalctl --user -u grokmon -n 5000 --no-pager -o cat > $LOG 2>&1
echo "=== LOG LINES: $(wc -l < $LOG) ==="
echo ""

echo "=== SERVICE STATUS ==="
systemctl --user is-active grokmon

echo ""
echo "=== STARTUP MESSAGES ==="
grep -i "Starting reactive\|Orchestrator started\|Reactive decisions\|sensor_loop\|ai_loop\|sensor polling\|AI decisions" $LOG | tail -10

echo ""
echo "=== AI DECISION CYCLES ==="
grep "Grok Decision\|AI.*Trigger\|\[AI\]" $LOG | tail -10

echo ""
echo "=== REACTIVE TRIGGERS ==="
grep -i "REACTIVE\|anomaly" $LOG | tail -10

echo ""
echo "=== SENSOR LOOP ==="
grep "Sensor poll\|sensor_loop\|reading.*temp\|Safety alert" $LOG | tail -5

echo ""
echo "=== CRITICAL ERRORS (non-learning) ==="
grep -i "ERROR\|Traceback\|FAIL" $LOG | grep -vi "learning\|orchestrator.*LEARN\|repo scan" | tail -10

echo ""
echo "=== LAST 3 LINES ==="
tail -3 $LOG
