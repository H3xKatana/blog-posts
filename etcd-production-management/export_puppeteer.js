const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  const url = 'https://excalidraw.com/#json=LtMT9BdvSJDHVPslHbC-G,5OWDE7-VpkTEiTsVuV60rA';
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

  // Wait for canvas to appear and scene to load
  await page.waitForSelector('canvas', { timeout: 15000 });
  
  // Wait for scene to render (the URL hash loads the JSON)
  await new Promise(r => setTimeout(r, 5000));

  // Get the canvas element and take a screenshot of just it
  const canvas = await page.$('canvas');
  if (!canvas) {
    console.error('Canvas not found');
    await browser.close();
    process.exit(1);
  }

  const outputPath = path.resolve('/opt/data/blog-posts/etcd-production-management/cluster-architecture-exported.png');
  await canvas.screenshot({ path: outputPath, type: 'png' });
  
  console.log('Exported to: ' + outputPath);
  await browser.close();
})();
