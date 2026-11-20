import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';
import {login} from './login.mjs';
import fs from 'fs';
const PAGES = [['داشبورد','dashboard'],['اعضا','members'],['برنامه‌ها','programs'],['تغذیه','nutrition'],['ارزیابی','assessment'],['چت','chat'],['حضور','checkin'],['مالی','finance'],['هزینه‌ها','expenses'],['تحلیل‌ها','analytics'],['فروشگاه','shop']];
const SKIP = /خروج|تغییر شماره|حذف|نهایی|پرداخت|ارسال|تأیید|رد /;
const MAX = 14;
const tokens = await login('09120000001');
const b = await puppeteer.launch({executablePath: await chromium.executablePath(), args: [...chromium.args,'--no-sandbox'], headless:true, defaultViewport:{width:1440,height:900}, env:{...process.env, LD_LIBRARY_PATH:'/tmp/al/lib'}});
const p = await b.newPage();
let errs=[], bad=[];
p.on('console', m => { if (m.type()==='error') errs.push(m.text().slice(0,160)); });
p.on('pageerror', e => errs.push('PAGEERR '+String(e.message).slice(0,160)));
p.on('response', r => { if (r.status()>=400 && r.url().includes('/api/')) bad.push(`${r.status()} ${new URL(r.url()).pathname}`); });
async function open(){
  await p.goto('http://127.0.0.1:5173/', {waitUntil:'domcontentloaded'});
  await p.evaluate((t) => { localStorage.setItem('mp_token', t.access_token); localStorage.setItem('mp_refresh', t.refresh_token); }, tokens);
  await p.goto('http://127.0.0.1:5173/', {waitUntil:'networkidle2', timeout:60000});
}
async function gotoPage(label){
  await p.evaluate((label) => { const btn=[...document.querySelectorAll('button')].find(b=>{const t=b.textContent.trim();return t===label||(t.endsWith(label)&&t.length<=label.length+3);}); btn?.click(); }, label);
  await new Promise(r=>setTimeout(r,1800));
}
const report=[];
await open();
for (const [label,key] of PAGES){
  await gotoPage(label);
  const names = await p.evaluate((skipSrc) => {
    const skip = new RegExp(skipSrc);
    const side = new Set([...document.querySelectorAll('aside button, nav button')]);
    return [...document.querySelectorAll('main button')].filter(b=>!b.disabled && b.offsetParent!==null && b.textContent.trim() && !skip.test(b.textContent.trim())).map(b=>b.textContent.trim().slice(0,40));
  }, SKIP.source);
  const uniq=[...new Set(names)].slice(0,MAX);
  for (const name of uniq){
    errs=[]; bad=[];
    await open(); await gotoPage(label);
    const clicked = await p.evaluate((name) => { const b=[...document.querySelectorAll('main button')].find(x=>x.textContent.trim().slice(0,40)===name && !x.disabled); if(!b) return false; b.click(); return true; }, name);
    await new Promise(r=>setTimeout(r,1200));
    const alert = await p.evaluate(()=>document.querySelector('[role=alert]')?.textContent?.trim().slice(0,90) ?? null);
    report.push({page:key, button:name, clicked, errors:errs.length, api4xx:bad, alert});
    console.log(key, '|', name, '| clicked', clicked, '| console', errs.length, '| api', bad.join(';')||'-', '| alert', alert ?? '-');
  }
}
await b.close();
fs.writeFileSync('/tmp/chr/buttons.json', JSON.stringify(report,null,1));
