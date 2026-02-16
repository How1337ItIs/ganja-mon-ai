import os
import time
from playwright.sync_api import sync_playwright

TARGETS = [
    {"name": "claudeandsol_home", "url": "https://claudeandsol.com"},
    {"name": "autoncorp_biodome", "url": "https://autoncorp.com/biodome"},
    {"name": "dexscreener_soltomato", "url": "https://dexscreener.com/solana/cvatvr6zxgjj9tlzv5khzgwrmwdq3eemgat38gt6zbxe"},
]

OUTPUT_DIR = ".playwright-mcp"

def capture_branding():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        for target in TARGETS:
            print(f"Navigating to {target['url']}...")
            page = context.new_page()
            try:
                page.goto(target['url'], timeout=60000, wait_until="domcontentloaded")
                # Wait a bit for dynamic content
                time.sleep(5) 
                
                output_path = os.path.join(OUTPUT_DIR, f"{target['name']}.png")
                page.screenshot(path=output_path, full_page=True)
                print(f"Captured {output_path}")
            except Exception as e:
                print(f"Failed to capture {target['url']}: {e}")
            finally:
                page.close()

        browser.close()
        print("Done.")

if __name__ == "__main__":
    capture_branding()
