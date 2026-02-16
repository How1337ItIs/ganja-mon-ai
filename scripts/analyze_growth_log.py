import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

async def analyze_growth_log():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            print('Navigating to http://chromebook.lan:8000...')
            await page.goto('http://chromebook.lan:8000', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Find and analyze the growth-timeline section
            print('\n=== GROWTH TIMELINE SECTION ===')
            timeline = await page.query_selector('.growth-timeline')
            if timeline:
                timeline_text = await timeline.inner_text()
                print('Timeline content:')
                print(timeline_text.replace('\n\n', '\n')[:1500])
                
                # Screenshot just the timeline
                await timeline.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_timeline_only.png')
                print('\nTimeline screenshot saved!')
            else:
                print('No .growth-timeline element found')
            
            # Find and analyze the grok-history section  
            print('\n=== GROK HISTORY SECTION ===')
            history = await page.query_selector('.grok-history')
            if history:
                history_text = await history.inner_text()
                print('History content:')
                print(history_text.replace('\n\n', '\n')[:2000])
                
                # Screenshot just the history
                await history.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)
                await history.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_history_only.png')
                print('\nHistory screenshot saved!')
            else:
                print('No .grok-history element found')
            
            # Check for any timeline stages
            print('\n=== TIMELINE STAGES ===')
            stages = await page.query_selector_all('.timeline-stages > *')
            if stages:
                print(f'Found {len(stages)} stage elements')
                for i, stage in enumerate(stages):
                    stage_text = await stage.inner_text()
                    stage_class = await stage.get_attribute('class')
                    print(f'  Stage {i+1}: {stage_text[:50]} (class: {stage_class})')
            
            # Check for history items
            print('\n=== HISTORY ITEMS ===')
            history_items = await page.query_selector_all('.history-content > *')
            if history_items:
                print(f'Found {len(history_items)} history items')
                for i, item in enumerate(history_items[:10]):
                    item_text = await item.inner_text()
                    print(f'  Item {i+1}: {item_text[:100].replace(chr(10), " ")}...')
            else:
                print('No history items found')
            
            print('\n=== ANALYSIS COMPLETE ===')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(analyze_growth_log())
