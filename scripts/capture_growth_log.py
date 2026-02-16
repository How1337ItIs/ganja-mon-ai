import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

async def capture_growth_log():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            print('Navigating to http://chromebook.lan:8000...')
            await page.goto('http://chromebook.lan:8000', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Find the GROWTH LOG section by its header text
            print('\n=== FINDING GROWTH LOG SECTION ===')
            growth_log = await page.query_selector('text=GROWTH LOG')
            
            if growth_log:
                print('Found GROWTH LOG header!')
                # Get the parent section-card
                section = await growth_log.evaluate_handle('el => el.closest(".section-card")')
                if section:
                    # Scroll to make it visible
                    await section.as_element().scroll_into_view_if_needed()
                    await page.wait_for_timeout(1000)
                    
                    # Get the full content
                    content = await section.as_element().inner_text()
                    print('\nGROWTH LOG Content:')
                    print('='*50)
                    print(content[:3000])
                    print('='*50)
                    
                    # Take screenshot of just this section
                    await section.as_element().screenshot(path='C:/Users/natha/sol-cannabis/screenshot_growth_log_section.png')
                    print('\nGrowth Log section screenshot saved!')
                    
                    # Also take viewport screenshot
                    await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_growth_log_viewport.png')
            else:
                print('GROWTH LOG header not found, trying alternative selectors...')
                # Try finding by update count
                updates_header = await page.query_selector('text=UPDATES')
                if updates_header:
                    print('Found by UPDATES text')
            
            print('\n=== DONE ===')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(capture_growth_log())
