import asyncio
import os
from playwright.async_api import async_playwright

# Use forward slashes for cross-platform compatibility
OUTPUT_DIR = "C:/Users/natha/sol-cannabis"

async def test_growth_log():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1400, 'height': 900})
        
        print('Navigating to http://192.168.125.128:8000...')
        await page.goto('http://192.168.125.128:8000', wait_until='domcontentloaded', timeout=60000)
        
        # Wait a bit for JS to render
        await page.wait_for_timeout(3000)
        
        print('Page loaded. Taking initial screenshot...')
        await page.screenshot(path=os.path.join(OUTPUT_DIR, 'growth-log-1-initial.png'))
        
        # Scroll down to find Growth Log section
        print('Scrolling down to find Growth Log section...')
        await page.evaluate('window.scrollBy(0, 800)')
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, 'growth-log-2-scrolled-down.png'))
        
        # Look for Growth Log section by heading
        growth_log_heading = await page.query_selector('h2:has-text("Growth Log"), h3:has-text("Growth Log"), [class*="growth"]')
        if growth_log_heading:
            print('Found Growth Log section!')
            await growth_log_heading.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)
        else:
            # Try scrolling more
            print('Looking for Growth Log, scrolling more...')
            await page.evaluate('window.scrollBy(0, 600)')
            await page.wait_for_timeout(500)
        
        await page.screenshot(path=os.path.join(OUTPUT_DIR, 'growth-log-3-section-visible.png'))
        
        # Find scrollable elements info
        scroll_result = await page.evaluate('''() => {
            const allElements = document.querySelectorAll('*');
            let scrollableElements = [];
            
            for (const el of allElements) {
                const style = window.getComputedStyle(el);
                const overflowX = style.overflowX;
                if ((overflowX === 'auto' || overflowX === 'scroll') && el.scrollWidth > el.clientWidth) {
                    scrollableElements.push({
                        tag: el.tagName,
                        className: el.className,
                        id: el.id,
                        scrollWidth: el.scrollWidth,
                        clientWidth: el.clientWidth
                    });
                }
            }
            
            return scrollableElements;
        }''')
        
        print(f'Found scrollable elements: {scroll_result}')
        
        # Scroll the progress-scroller to the right (older entries)
        print('Scrolling growth log to the right (older entries)...')
        scrolled = await page.evaluate('''() => {
            const scroller = document.getElementById('progress-scroller') || document.querySelector('.progress-scroller');
            if (scroller) {
                const before = scroller.scrollLeft;
                scroller.scrollLeft = scroller.scrollWidth;
                const after = scroller.scrollLeft;
                return {scrolled: true, before, after, scrollWidth: scroller.scrollWidth};
            }
            return {scrolled: false};
        }''')
        
        print(f'Scroll right result: {scrolled}')
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, 'growth-log-4-scrolled-right-older.png'))
        
        # Now scroll back to the left (most recent should be on left)
        print('Scrolling growth log back to the left (most recent entries)...')
        scroll_left_result = await page.evaluate('''() => {
            const scroller = document.getElementById('progress-scroller') || document.querySelector('.progress-scroller');
            if (scroller) {
                scroller.scrollLeft = 0;
                return {scrolled: true, scrollLeft: scroller.scrollLeft};
            }
            return {scrolled: false};
        }''')
        
        print(f'Scroll left result: {scroll_left_result}')
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUTPUT_DIR, 'growth-log-5-scrolled-left-recent.png'))
        
        print(f'Done! Screenshots saved to {OUTPUT_DIR}')
        await browser.close()

asyncio.run(test_growth_log())
