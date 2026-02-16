# Moltbook Integration - Lessons Learned

**Date:** February 5, 2026
**Status:** RESOLVED

## Issue: Empty Post Bodies

### Symptom
Posts on Moltbook showed title ("GanjaMon Update") but NO body content.

### Root Cause
The `moltbook_client.py` was sending the post body as `text` field, but Moltbook API expects `content` field (same as Clawk API).

**Incorrect:**
```python
payload = {
    "text": text,  # WRONG - Moltbook ignores this
    "title": title,
    ...
}
```

**Correct:**
```python
payload = {
    "content": text,  # CORRECT - Moltbook reads this
    "title": title,
    ...
}
```

### Fix Location
`cloned-repos/ganjamon-agent/src/publishing/moltbook_client.py:83-89`

### How We Found It
1. Viewed profile at https://moltbook.com/u/ganjamon
2. Clicked on a post - saw title but empty body
3. Checked code in `moltbook_client.py`
4. Compared with Clawk API docs (uses `content` field)
5. Fixed field name

---

## Issue: Profile "Not Found" Initially

### Symptom
Navigating to `/u/ganjamon` showed "Loading..." then nothing.

### Root Cause
Server-side rendering returns static HTML, actual agent data loads via client-side JavaScript. Need to wait for page hydration.

### Lesson
When checking Moltbook profiles via curl or static fetch:
- The HTML will show "Loading..."
- Must use browser automation (Playwright) or wait for JavaScript
- Or query the API directly: `GET /api/v1/agents/status`

---

## Key API Findings

### Moltbook API Endpoints (Undocumented)
Based on reverse engineering:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/agents/status` | Check claim status (requires Bearer token) |
| `POST /api/v1/posts` | Create post (title, content, submolt, tags) |

### Expected Payload Structure
```json
{
  "title": "Post Title",
  "content": "The actual body content goes here",
  "submolt": "general",
  "tags": ["tag1", "tag2"]
}
```

### Authentication
```
Authorization: Bearer moltbook_sk_...
```

---

## Registration Checklist (Updated)

- [x] Get API key (stored in `config/openclaw.json`)
- [x] Post verification tweet with code
- [x] Confirm claim status via API
- [x] Update IDENTITY.md with agent ID
- [x] Fix posting to use `content` field
- [ ] Test new post with content

---

## Related Files

| File | Purpose |
|------|---------|
| `config/openclaw.json` | API keys for Moltbook and Clawk |
| `openclaw-workspace/ganjamon/IDENTITY.md` | Agent identity and registration status |
| `cloned-repos/ganjamon-agent/src/publishing/moltbook_client.py` | Moltbook posting client |
| `cloned-repos/ganjamon-agent/src/publishing/social_broadcaster.py` | Orchestrates social posting |
| `docs/MOLTBOOK_HACKATHON_GUIDE.md` | Hackathon requirements |
