const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('http://localhost:8085');
  await page.waitForTimeout(2000); // Wait for page to fully load
  await page.screenshot({ path: 'C:/Users/natha/sol-cannabis/rasta-voice/dashboard_final.png', fullPage: false });
  console.log('Screenshot saved!');
  await browser.close();
})();
