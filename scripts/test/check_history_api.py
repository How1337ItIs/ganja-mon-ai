import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

async def check_history():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            # Monitor network requests
            api_responses = []
            
            async def handle_response(response):
                if 'api' in response.url or 'history' in response.url:
                    try:
                        body = await response.text()
                        api_responses.append({
                            'url': response.url,
                            'status': response.status,
                            'body': body[:500]
                        })
                    except:
                        api_responses.append({
                            'url': response.url,
                            'status': response.status,
                            'body': 'Could not read body'
                        })
            
            page.on('response', handle_response)
            
            print('Navigating to http://chromebook.lan:8000...')
            await page.goto('http://chromebook.lan:8000', timeout=30000)
            await page.wait_for_timeout(5000)  # Wait longer for API calls
            
            print('\n=== API RESPONSES CAPTURED ===')
            for resp in api_responses:
                print(f'\nURL: {resp["url"]}')
                print(f'Status: {resp["status"]}')
                print(f'Body: {resp["body"][:300]}...')
            
            # Check console errors
            console_messages = []
            page.on('console', lambda msg: console_messages.append(f'{msg.type}: {msg.text}'))
            
            # Check if history section has loaded
            print('\n=== CHECKING HISTORY SECTION STATE ===')
            history_content = await page.query_selector('.history-content')
            if history_content:
                html = await history_content.inner_html()
                print(f'History content HTML:\n{html[:1000]}')
            
            # Try clicking the history section to expand it if needed
            history_header = await page.query_selector('.history-header')
            if history_header:
                print('\nClicking history header to expand...')
                await history_header.click()
                await page.wait_for_timeout(2000)
                
                # Check content again
                history_content = await page.query_selector('.history-content')
                if history_content:
                    html = await history_content.inner_html()
                    print(f'History content after click:\n{html[:1000]}')
            
            # Take screenshot of the page state
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_after_wait.png', full_page=True)
            print('\nFull page screenshot saved after waiting for API calls')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(check_history())
