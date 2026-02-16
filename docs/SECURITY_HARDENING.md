# Security Hardening Changelog

This document tracks all security changes made to the sol-cannabis project.
Each change is documented with before/after states for regression testing.

## Date: 2026-01-19

### Audit Summary

**CRITICAL vulnerabilities found and fixed:**

1. **Exposed credentials in .env files** - Real API keys committed to repo
2. **Blockchain private key exposed** - In launch-tools/custom/.env
3. **SSH credentials in documentation** - Password visible in CLAUDE.md
4. **Unauthenticated sensitive endpoints** - /api/grow/reset had no auth
5. **No rate limiting** - Login endpoint vulnerable to brute force
6. **Hardcoded default passwords** - In auth.py and docker-compose.yml
7. **WebSocket token in URL** - Exposed in access logs
8. **EMQX anonymous connections** - Allowed by default
9. **Hardcoded viewer password** - "viewonly" in auth.py

---

## Changes Made

### 1. Authentication Hardening (src/api/auth.py)

**Before:**
```python
_default_secret = "grok-and-mon-dev-secret-INSECURE"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CHANGE_ME_IN_ENV")
"viewer": {
    "hashed_password": pwd_context.hash("viewonly"),
}
```

**After:**
- Removed insecure default secrets
- Added rate limiting (5 attempts per minute)
- Removed hardcoded viewer password
- Added failed login tracking
- Production mode requires all secrets to be set via environment

**Regression test:**
```bash
# Test rate limiting (should block after 5 attempts)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/token \
    -d "username=admin&password=wrong" 2>/dev/null | jq -r '.detail'
done
# Expected: Last attempt returns "Too many login attempts"

# Test that auth still works with correct credentials
curl -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=$ADMIN_PASSWORD" | jq
```

---

### 2. Unauthenticated Endpoint Fix (src/api/app.py)

**Before:**
```python
@app.post("/api/grow/reset")
async def reset_grow_session():
    # No authentication!
```

**After:**
```python
@app.post("/api/grow/reset")
async def reset_grow_session(current_user: User = Depends(get_current_admin)):
    # Requires admin authentication
```

**Regression test:**
```bash
# Without auth - should fail with 401
curl -X POST http://localhost:8000/api/grow/reset
# Expected: {"detail":"Not authenticated"}

# With admin auth - should work
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -d "username=admin&password=$ADMIN_PASSWORD" | jq -r '.access_token')
curl -X POST http://localhost:8000/api/grow/reset \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### 3. Lead Capture Input Validation (src/api/app.py)

**Before:**
- Accepted arbitrary data without validation
- No XSS sanitization

**After:**
- Added Pydantic model with field validation
- HTML tag stripping
- Phone number validation
- Length limits on all fields

**Regression test:**
```bash
# Test XSS prevention
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","company":"<script>alert(1)</script>"}'
# Expected: company field should be sanitized

# Test invalid email
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email"}'
# Expected: {"detail":"Valid email required"}
```

---

### 4. Environment File Sanitization

**Files sanitized:**
- `/.env` - Replaced real keys with placeholders
- `/rasta-voice/.env` - Replaced real keys with placeholders
- `/launch-tools/custom/.env` - Replaced private key with placeholder

**IMPORTANT:** After applying these changes, you MUST:
1. Generate new API keys for all services
2. Generate a new blockchain wallet if the key was compromised
3. Update .env files with new credentials locally

**Regression test:**
```bash
# Verify no real API keys in committed files
grep -r "xai-" --include="*.env" . 2>/dev/null
grep -r "sk_" --include="*.env" . 2>/dev/null
grep -r "0x[a-f0-9]{64}" --include="*.env" . 2>/dev/null
# Expected: Should only find placeholder patterns
```

---

### 5. Documentation Credential Removal (CLAUDE.md)

**Before:**
```markdown
| SSH/sudo | natha | claude |
| API Admin | admin | `$ADMIN_PASSWORD` |
```

**After:**
- SSH password replaced with `<SET_SECURE_PASSWORD>`
- Admin password replaced with `<SET_VIA_ENV>`
- Added warning about credential management

**Regression test:**
```bash
# Verify no plaintext passwords in docs
grep -i "password.*=" CLAUDE.md | grep -v "SET_"
# Expected: No results
```

---

### 6. Docker Compose Hardening (docker-compose.yml)

**Before:**
```yaml
- EMQX_DASHBOARD__DEFAULT_PASSWORD=grokmon123
- EMQX_ALLOW_ANONYMOUS=true
- DOCKER_INFLUXDB_INIT_PASSWORD=grokmon123
- GF_SECURITY_ADMIN_PASSWORD=grokmon123
```

**After:**
- All passwords use environment variable references
- Anonymous MQTT connections disabled
- Added security comments

**Regression test:**
```bash
# Verify no hardcoded passwords
grep -E "PASSWORD=[^$]" docker-compose.yml
# Expected: No results (all should use ${VAR} syntax)
```

---

### 7. Gitignore Enhancement (.gitignore)

**Added patterns:**
```
# All environment files
**/.env
**/.env.*
!**/.env.example

# Wallet and key files
*.pem
*.key
wallets/
*.enc

# Sensitive config
**/secrets.yaml
**/credentials.json
```

**Regression test:**
```bash
# Verify .env files would be ignored
git check-ignore .env rasta-voice/.env launch-tools/custom/.env
# Expected: All three files should be listed
```

---

### 8. WebSocket Authentication Improvement (src/api/app.py)

**Before:**
- Token passed as URL query parameter (visible in logs)

**After:**
- Added support for token in first WebSocket message
- Deprecated query parameter method with warning
- Token no longer logged

**Regression test:**
```javascript
// Connect with token in message (new method)
const ws = new WebSocket('ws://localhost:8000/ws/sensors');
ws.onopen = () => ws.send(JSON.stringify({type: 'auth', token: 'your-jwt'}));
```

---

## Post-Hardening Checklist

After applying these changes, complete these steps:

### If You Plan to Push to a Public Repo

- [ ] **Rotate all API keys (they're in git history):**
  - [ ] XAI API key (create new at x.ai)
  - [ ] Govee API key (regenerate in Govee app)
  - [ ] Deepgram API key
  - [ ] AssemblyAI API key
  - [ ] Groq API key
  - [ ] Cartesia API key
  - [ ] ElevenLabs API key

- [ ] **Blockchain security:**
  - [ ] If private key was used for real funds, transfer immediately
  - [ ] Generate new wallet for production use

### For Local Use (No Public Repo)

Your existing API keys are safe to keep using. However:

- [ ] **Server credentials:**
  - [ ] Change SSH password for 'natha' user (was in CLAUDE.md)
  - [ ] Verify ADMIN_PASSWORD is set in .env
  - [ ] Verify JWT_SECRET_KEY is set in .env

- [ ] **Run regression tests:**
  - [ ] All endpoints still functional
  - [ ] Rate limiting working
  - [ ] Auth required on protected endpoints

## Deploy to Chromebook

After hardening, deploy the updated files:

```bash
# Copy hardened files to Chromebook
scp /mnt/c/Users/natha/sol-cannabis/src/api/auth.py chromebook.lan:/home/natha/projects/sol-cannabis/src/api/auth.py
scp /mnt/c/Users/natha/sol-cannabis/src/api/app.py chromebook.lan:/home/natha/projects/sol-cannabis/src/api/app.py

# Restart the service
ssh chromebook.lan "systemctl --user restart grokmon"

# Verify it's running
ssh chromebook.lan "systemctl --user status grokmon --no-pager"

# Test the API
ssh chromebook.lan "curl -s http://localhost:8000/api/health | jq"
```

---

## Security Best Practices Going Forward

1. **Never commit .env files** - Use .env.example templates only
2. **Use secrets manager** for production (AWS Secrets Manager, Vault, etc.)
3. **Rotate credentials regularly** - At least quarterly
4. **Monitor for leaked credentials** - Use GitHub secret scanning
5. **Principle of least privilege** - Only grant necessary permissions
6. **Audit logs** - Log all authentication attempts and sensitive operations

---

## Rollback Instructions

If any change breaks functionality:

1. Each section above shows before/after code
2. Git history preserves original implementations
3. Environment variables can be reverted to defaults for dev only

```bash
# Revert specific file
git checkout HEAD~1 -- path/to/file

# Revert all security changes
git revert <commit-hash>
```
