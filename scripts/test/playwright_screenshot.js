const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    console.log('Navigating to http://chromebook.lan:8000...');
    await page.goto('http://chromebook.lan:8000', { timeout: 30000 });
    
    console.log('Taking initial screenshot...');
    await page.screenshot({ path: 'screenshot_top.png', fullPage: false });
    
    console.log('Scrolling to find Growth Log section...');
    // Get the full page height
    const pageHeight = await page.evaluate(() => document.body.scrollHeight);
    console.log('Page height:', pageHeight);
    
    // Scroll down in increments and look for growth log
    let found = false;
    for (let i = 0; i < 5; i++) {
      await page.evaluate((scrollY) => window.scrollTo(0, scrollY), i * 500);
      await page.waitForTimeout(500);
      
      // Check for Growth Log or Plant Progress elements
      const growthLog = await page.$('text=Growth Log');
      const plantProgress = await page.$('text=Plant Progress');
      const timeline = await page.$('text=Timeline');
      
      if (growthLog || plantProgress || timeline) {
        console.log('Found growth/progress section!');
        found = true;
        break;
      }
    }
    
    // Take screenshot of current view
    console.log('Taking screenshot of scrolled view...');
    await page.screenshot({ path: 'screenshot_scrolled.png', fullPage: false });
    
    // Also take a full page screenshot
    console.log('Taking full page screenshot...');
    await page.screenshot({ path: 'screenshot_full.png', fullPage: true });
    
    // Get page title and content summary
    const title = await page.title();
    console.log('Page title:', title);
    
    // Look for specific sections
    const sections = await page.evaluate(() => {
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      return headings.map(h => h.textContent.trim());
    });
    console.log('Page sections found:', sections);
    
    console.log('Screenshots saved successfully!');
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
})();
