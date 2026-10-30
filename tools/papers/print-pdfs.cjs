/* Run: node tools/papers/print-pdfs.cjs [first-year] [last-year]
 * Requires playwright and installed Chinese serif/sans fonts.
 * Optional: PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH for an existing Chromium.
 * This prints the checked-in HTML directly and never rebuilds or edits it.
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');
const {execFileSync} = require('node:child_process');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'papers/pdf');
const manifestPath = path.join(__dirname, 'pdf-manifest.json');
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
(async () => {
  const first = Number(process.argv[2] || 2012), last = Number(process.argv[3] || 2026);
  if (!(first >= 2012 && last <= 2026 && first <= last)) throw Error('Years must be within 2012..2026');
  fs.mkdirSync(output, {recursive:true});
  const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : {papers:[]};
  manifest.html_revision = execFileSync('git', ['rev-parse', 'HEAD'], {cwd:root, encoding:'utf8'}).trim();
  manifest.settings = {preferCSSPageSize:true, printBackground:true, displayHeaderFooter:false, scale:1, answerSpace:false};
  const browser = await chromium.launch({headless:true, executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined, args:['--no-sandbox','--disable-gpu']});
  try {
    manifest.browser = await browser.version();
    for (let year=first; year<=last; year++) {
      const html = path.join(root, `papers/${year}.html`), pdf = path.join(output, `${year}.pdf`);
      const before = hash(html), errors=[];
      const page = await browser.newPage({viewport:{width:1280,height:900}});
      page.on('pageerror', error => errors.push(String(error)));
      await page.goto(pathToFileURL(html).href);
      await page.waitForFunction(() => document.body.dataset.ready === 'true');
      if (await page.locator('article').count() !== 38) throw Error(`${year}: expected 38 questions`);
      await page.emulateMedia({media:'print'});
      await page.pdf({path:pdf, preferCSSPageSize:true, printBackground:true, displayHeaderFooter:false, scale:1});
      if (errors.length || before !== hash(html)) throw Error(`${year}: page error or HTML changed`);
      manifest.papers = manifest.papers.filter(item => item.year !== year);
      manifest.papers.push({year,html:`papers/${year}.html`,html_sha256:before,pdf:`papers/pdf/${year}.pdf`,pdf_sha256:hash(pdf),pdf_bytes:fs.statSync(pdf).size});
      manifest.papers.sort((a,b)=>a.year-b.year);
      fs.writeFileSync(manifestPath, JSON.stringify(manifest,null,2)+'\n');
      console.log(`${year}: printed, HTML unchanged`);
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode=1;});
