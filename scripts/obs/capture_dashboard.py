import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

async def capture_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            print('Navigating to http://chromebook.lan:8000...')
            await page.goto('http://chromebook.lan:8000', timeout=30000)
            await page.wait_for_timeout(2000)
            
            title = await page.title()
            print(f'Page title: {title}')
            
            print('Taking screenshot of top section...')
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_top.png')
            
            # Get all headings
            headings = await page.evaluate('''() => {
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                return headings.map(h => ({ tag: h.tagName, text: h.textContent.trim().replace(/[^\x00-\x7F]/g, '') }));
            }''')
            print('Headings found on page:')
            for h in headings:
                print(f'  {h["tag"]}: {h["text"]}')
            
            # Look for Growth Log or Plant Progress section
            growth_log = await page.query_selector('text=Growth Log')
            plant_progress = await page.query_selector('text=Plant Progress')
            timeline = await page.query_selector('text=Timeline')
            history = await page.query_selector('text=History')
            log_section = await page.query_selector('text=Log')
            
            target = growth_log or plant_progress or timeline or history or log_section
            
            if target:
                print('Found growth/progress section, scrolling to it...')
                await target.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_growth_log.png')
                print('Screenshot of Growth Log section saved!')
            else:
                print('Growth Log section not found by text. Scrolling down...')
            
            # Scroll down to bottom of page in increments
            page_height = await page.evaluate('() => document.body.scrollHeight')
            print(f'Page height: {page_height}px')
            
            for i in range(1, 6):
                scroll_pos = i * 600
                await page.evaluate(f'window.scrollTo(0, {scroll_pos})')
                await page.wait_for_timeout(300)
                print(f'Scrolled to {scroll_pos}px')
            
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_scrolled.png')
            print('Screenshot of scrolled page saved!')
            
            # Take full page screenshot
            print('Taking full page screenshot...')
            await page.screenshot(path='C:/Users/natha/sol-cannabis/screenshot_full.png', full_page=True)
            
            # Get page sections/divs that might contain progress info
            sections = await page.evaluate('''() => {
                const divs = Array.from(document.querySelectorAll('section, div[class*="log"], div[class*="progress"], div[class*="history"], div[class*="timeline"]'));
                return divs.map(d => d.className).filter(c => c);
            }''')
            print('Relevant sections/divs:')
            for s in sections[:20]:
                print(f'  {s}')
            
            print('\nScreenshots saved to C:/Users/natha/sol-cannabis/')
            print('Files: screenshot_top.png, screenshot_scrolled.png, screenshot_full.png')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

asyncio.run(capture_dashboard())
