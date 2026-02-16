#!/usr/bin/env python3
"""
Test script to verify the Chromebook web interface loads correctly
"""
import asyncio
from pathlib import Path
import json
from playwright.async_api import async_playwright

async def test_web_interface():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set up console message listener to capture any errors
        console_messages = []
        page_errors = []

        def on_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })

        def on_page_error(error):
            page_errors.append(str(error))

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        try:
            print("Navigating to http://192.168.125.128:8000/...")
            response = await page.goto("http://192.168.125.128:8000/", wait_until="networkidle", timeout=15000)
            print(f"Response status: {response.status}")

            # Wait a bit for any animations/effects to render
            await page.wait_for_timeout(2000)

            # Take screenshot
            screenshot_path = Path("C:/Users/natha/sol-cannabis/test-screenshot.png")
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Screenshot saved to {screenshot_path}")

            # Get page title
            title = await page.title()
            print(f"Page title: {title}")

            # Check for visual elements
            body_html = await page.content()

            # Look for key elements
            has_canvas = "canvas" in body_html.lower()
            has_smoke = "smoke" in body_html.lower()
            has_effects = "effects" in body_html.lower()
            has_settings = "settings" in body_html.lower()

            print(f"\nPage Analysis:")
            print(f"  - Canvas element found: {has_canvas}")
            print(f"  - 'smoke' text found in HTML: {has_smoke}")
            print(f"  - 'effects' text found in HTML: {has_effects}")
            print(f"  - 'settings' text found in HTML: {has_settings}")

            # Check console messages
            print(f"\nConsole Messages ({len(console_messages)} total):")
            for msg in console_messages:
                if msg['type'] in ['error', 'warning']:
                    print(f"  [{msg['type'].upper()}] {msg['text']}")

            if page_errors:
                print(f"\nPage Errors ({len(page_errors)} total):")
                for error in page_errors:
                    print(f"  - {error}")
            else:
                print("\nNo page errors detected!")

            # Save detailed report
            report = {
                'url': 'http://192.168.125.128:8000/',
                'status': response.status,
                'title': title,
                'elements_found': {
                    'canvas': has_canvas,
                    'smoke': has_smoke,
                    'effects': has_effects,
                    'settings': has_settings
                },
                'console_messages': console_messages,
                'page_errors': page_errors
            }

            report_path = Path("C:/Users/natha/sol-cannabis/test-report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nDetailed report saved to {report_path}")

        except Exception as e:
            print(f"ERROR: {e}")
            return False
        finally:
            await browser.close()

    return True

if __name__ == "__main__":
    success = asyncio.run(test_web_interface())
    exit(0 if success else 1)
