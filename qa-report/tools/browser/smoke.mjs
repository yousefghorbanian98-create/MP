import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import {login} from './login.mjs';
import fs from 'fs';
const OUT = '/home/user/MP/qa-report/screenshots';
const PAGES = [['داشبورد','dashboard'],['اعضا','members'],['برنامه‌ها','programs'],['تغذیه','nutrition'],['ارزیابی','assessment'],['چت','chat'],['حضور','checkin'],['مالی','finance'],['هزینه‌ها','expenses'],['تحلیل‌ها','analytics'],['فروشگاه','shop']];
const tokens = await login('09120000001');
const b = await puppeteer.launch({executablePath: await chromium.executablePath(), args: [...chromium.args, '--no-sandbox'], headless: true, defaultViewport: {width:1440,height:900}, env: {...process.env, LD_LIBRARY_PATH:'/tmp/al/lib'}});
const p = await b.newPage();
const consoleErr = [], bad = [], pageErr = [];
p.on('console', m => { if (m.type()==='error') consoleErr.push(m.text().slice(0,200)); });
p.on('pageerror', e => pageErr.push(String(e.message).slice(0,200)));
p.on('response', r => { if (r.status()>=400 && r.url().includes('/api/')) bad.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`); });
await p.goto('http://127.0.0.1:5173/', {waitUntil:'domcontentloaded'});
await p.evaluate((t) => { localStorage.setItem('mp_token', t.access_token); localStorage.setItem('mp_refresh', t.refresh_token); }, tokens);
await p.goto('http://127.0.0.1:5173/', {waitUntil:'networkidle2', timeout: 60000});
const results = [];
for (const [label, key] of PAGES) {
  const clicked = await p.evaluate((label) => {
    const btn = [...document.querySelectorAll('button')].find(b => { const t = b.textContent.trim(); return t === label || (t.endsWith(label) && t.length <= label.length + 3); });
    if (btn) { btn.click(); return true; } return false;
  }, label);
  await new Promise(r => setTimeout(r, 2500));
  const info = await p.evaluate(() => ({
    h1: document.querySelector('main h1')?.textContent?.trim() ?? null,
    overflow: document.documentElement.scrollWidth > window.innerWidth,
    alert: document.querySelector('[role=alert]')?.textContent?.trim()?.slice(0,80) ?? null,
  }));
  await p.screenshot({path: `${OUT}/${key}.png`, fullPage: false});
  results.push({key, clicked, ...info});
}
await b.close();
fs.writeFileSync('/tmp/chr/smoke-result.json', JSON.stringify({results, consoleErr, bad, pageErr}, null, 1));
console.log(JSON.stringify(results, null, 0));
console.log('console errors', consoleErr.length, 'api>=400', bad.length, 'page errors', pageErr.length);
console.log(bad.slice(0,10).join('\n'), consoleErr.slice(0,5).join('\n'), pageErr.slice(0,5).join('\n'));
