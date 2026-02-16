#!/usr/bin/env python3
"""Quick test to verify Playwright browser automation works."""
import asyncio
from playwright.async_api import async_playwright

async def test():
    print("Starting Playwright...")
    p = await async_playwright().start()
    print("Launching Chromium...")
    b = await p.chromium.launch(headless=True)
    print("Opening new page...")
    page = await b.new_page()
    print("Navigating to Google...")
    await page.goto('https://google.com')
    title = await page.title()
    print(f'Page Title: {title}')
    await b.close()
    await p.stop()
    print("SUCCESS - Browser testing works!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test())
    print(f"\nResult: {'PASS' if result else 'FAIL'}")
