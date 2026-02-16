#!/bin/bash
# Advance grow day counter
# Run this daily at midnight via cron

curl -X POST http://localhost:8000/api/grow/advance-day \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  >> /tmp/day_advance.log 2>&1

# Or if admin token not set, you can manually call:
# curl -X POST https://grokandmon.com/api/grow/advance-day \
#   -H "Authorization: Bearer YOUR_JWT_TOKEN"
