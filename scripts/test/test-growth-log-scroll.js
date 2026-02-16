const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
    
    console.log('Navigating to http://chromebook.lan:8000...');
    await page.goto('http://chromebook.lan:8000', { waitUntil: 'networkidle', timeout: 30000 });
    
    console.log('Page loaded. Taking initial screenshot...');
    await page.screenshot({ path: 'screenshot-1-initial.png', fullPage: false });
    
    // Scroll down to find Growth Log section
    console.log('Scrolling down to find Growth Log section...');
    await page.evaluate(() => window.scrollBy(0, 800));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshot-2-scrolled-down.png', fullPage: false });
    
    // Look for Growth Log section
    const growthLogSection = await page.$('text=Growth Log');
    if (growthLogSection) {
        console.log('Found Growth Log section!');
        await growthLogSection.scrollIntoViewIfNeeded();
        await page.waitForTimeout(300);
        await page.screenshot({ path: 'screenshot-3-growth-log-visible.png', fullPage: false });
    } else {
        console.log('Growth Log text not found, continuing to scroll...');
        await page.evaluate(() => window.scrollBy(0, 500));
        await page.waitForTimeout(500);
        await page.screenshot({ path: 'screenshot-3-more-scroll.png', fullPage: false });
    }
    
    // Find the horizontally scrollable container for growth log
    // It's likely a container with overflow-x: auto or scroll
    console.log('Looking for scrollable growth log container...');
    
    // Try to find the growth log container and scroll it horizontally
    const scrollResult = await page.evaluate(() => {
        // Look for elements that might be the growth log container
        const candidates = document.querySelectorAll('[class*="growth"], [class*="log"], [class*="scroll"], [id*="growth"], [id*="log"]');
        console.log('Found candidates:', candidates.length);
        
        // Also look for any horizontally scrollable element
        const allElements = document.querySelectorAll('*');
        let scrollableElement = null;
        
        for (const el of allElements) {
            const style = window.getComputedStyle(el);
            const overflowX = style.overflowX;
            if ((overflowX === 'auto' || overflowX === 'scroll') && el.scrollWidth > el.clientWidth) {
                // Found a horizontally scrollable element
                scrollableElement = el;
                console.log('Found scrollable element:', el.tagName, el.className);
            }
        }
        
        if (scrollableElement) {
            // Scroll to the right (to show older entries)
            const initialScroll = scrollableElement.scrollLeft;
            scrollableElement.scrollLeft = scrollableElement.scrollWidth;
            const finalScroll = scrollableElement.scrollLeft;
            return { found: true, initialScroll, finalScroll, scrollWidth: scrollableElement.scrollWidth };
        }
        
        return { found: false };
    });
    
    console.log('Scroll result:', JSON.stringify(scrollResult));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshot-4-after-scroll-right.png', fullPage: false });
    
    // Now scroll back to the left (most recent should be on left)
    console.log('Scrolling growth log back to the left (most recent entries)...');
    const scrollLeftResult = await page.evaluate(() => {
        const allElements = document.querySelectorAll('*');
        for (const el of allElements) {
            const style = window.getComputedStyle(el);
            const overflowX = style.overflowX;
            if ((overflowX === 'auto' || overflowX === 'scroll') && el.scrollWidth > el.clientWidth) {
                el.scrollLeft = 0;
                return { scrolled: true, scrollLeft: el.scrollLeft };
            }
        }
        return { scrolled: false };
    });
    
    console.log('Scroll left result:', JSON.stringify(scrollLeftResult));
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'screenshot-5-scrolled-left-recent.png', fullPage: false });
    
    console.log('Done! Screenshots saved.');
    await browser.close();
})();
