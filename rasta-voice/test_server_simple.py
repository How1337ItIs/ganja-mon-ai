#!/usr/bin/env python3
"""Minimal test server to verify FastAPI/uvicorn works."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def test():
    return HTMLResponse("<h1>Test Server Works!</h1><p>If you see this, FastAPI is working.</p>")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("Starting test server on http://127.0.0.1:8087")
    uvicorn.run(app, host="127.0.0.1", port=8087)
