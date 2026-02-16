import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

async def final_check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            print('Navigating to http://chromebook.lan:8000...')
            await page.goto('http://chromebook.lan:8000', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Get the growth timeline section screenshot
            print('\n=== GROWTH TIMELINE ===')
            timeline = await page.query_selector('.growth-timeline')
            if timeline:
                box = await timeline.bounding_box()
                if box:
                    print(f'Timeline position: x={box["x"]}, y={box["y"]}, width={box["width"]}, height={box["height"]}')
                    # Scroll to make it visible and capture
                    await page.evaluate(f'window.scrollTo(0, {box["y"] - 100})')
                    await page.wait_for_timeout(500)
                    await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_timeline_section.png')
                    print('Timeline section screenshot saved!')
                
                # Get timeline stages details
                stages = await page.query_selector_all('.timeline-stages .stage')
                if stages:
                    print(f'\nTimeline has {len(stages)} stages:')
                    for i, stage in enumerate(stages):
                        stage_class = await stage.get_attribute('class')
                        stage_text = await stage.inner_text()
                        print(f'  Stage {i+1}: {stage_text.strip()} (class: {stage_class})')
            
            # Check for current stage indicator
            current_stage = await page.query_selector('.stage.current')
            if current_stage:
                text = await current_stage.inner_text()
                print(f'\nCurrent stage highlighted: {text}')
            
            # Look for progress bar or completion indicator
            progress = await page.query_selector('.timeline-progress')
            if progress:
                style = await progress.get_attribute('style')
                print(f'\nProgress bar style: {style}')
            
            # Check for day counter
            day_element = await page.query_selector('.timeline-title')
            if day_element:
                day_text = await day_element.inner_text()
                print(f'\nDay display: {day_text}')
            
            # Look for any plant progress section
            print('\n=== LOOKING FOR PLANT PROGRESS SECTIONS ===')
            all_sections = await page.query_selector_all('.section-card')
            for section in all_sections:
                header = await section.query_selector('h2, h3, .section-header')
                if header:
                    header_text = await header.inner_text()
                    header_text = header_text.replace('\n', ' ').strip()[:50]
                    print(f'  Section: {header_text}')
            
            # Take a viewport screenshot focused on the top content
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(500)
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_dashboard_top.png')
            
            # Scroll to middle of page and capture
            await page.evaluate('window.scrollTo(0, 1000)')
            await page.wait_for_timeout(500)
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_dashboard_middle.png')
            
            # Scroll to bottom and capture
            await page.evaluate('window.scrollTo(0, 3000)')
            await page.wait_for_timeout(500)
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_dashboard_bottom.png')
            
            print('\nAll screenshots saved!')
            print('\nScreenshot files:')
            print('  - screenshot_dashboard_top.png')
            print('  - screenshot_dashboard_middle.png')
            print('  - screenshot_dashboard_bottom.png')
            print('  - screenshot_timeline_section.png')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(final_check())
