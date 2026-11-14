/* Run: PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/google-chrome node x8/scripts/print-pdfs.cjs */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '../..');
const htmlDir = path.join(root, 'x8/html');
const manifestPath = path.join(__dirname, 'pdf-export.json');
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const papers = [];
  try {
    const browserVersion = await browser.version();
    for (let i = 1; i <= 8; i++) {
      const num = String(i).padStart(2, '0');
      const htmlPath = path.join(htmlDir, `x8-${num}.html`);
      const pdfPath = path.join(htmlDir, `x8-${num}.pdf`);
      const before = hash(htmlPath);
      const errors = [];
      const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
      page.on('pageerror', err => errors.push(String(err)));
      await page.goto(pathToFileURL(htmlPath).href);
      await page.waitForFunction(() => document.body.dataset.ready === 'true');
      if (await page.locator('article').count() !== 38) {
        throw new Error(`x8-${num}: expected 38 questions`);
      }
      await page.emulateMedia({ media: 'print' });
      await page.pdf({
        path: pdfPath,
        preferCSSPageSize: true,
        printBackground: true,
        displayHeaderFooter: false,
        scale: 1,
      });
      if (errors.length || before !== hash(htmlPath)) {
        throw new Error(`x8-${num}: page error or HTML modified`);
      }
      papers.push({
        paper: i,
        html: `x8/html/x8-${num}.html`,
        html_sha256: before,
        pdf: `x8/html/x8-${num}.pdf`,
        pdf_sha256: hash(pdfPath),
        pdf_bytes: fs.statSync(pdfPath).size,
      });
      console.log(`x8-${num}: printed (${fs.statSync(pdfPath).size} bytes)`);
      await page.close();
    }
    fs.writeFileSync(
      manifestPath,
      JSON.stringify(
        {
          generator: 'x8/scripts/print-pdfs.cjs',
          browser: browserVersion,
          settings: { preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false, scale: 1 },
          papers,
        },
        null,
        2,
      ) + '\n',
    );
  } finally {
    await browser.close();
  }
})().catch(err => {
  console.error(err);
  process.exitCode = 1;
});
