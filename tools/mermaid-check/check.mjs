#!/usr/bin/env node
// Mermaid syntax gate: every ```mermaid block in tracked Markdown must really parse.
// Why: scripts/docs_gate.py only proves a diagram declaration exists, not that the
// diagram is valid Mermaid. This closes that gap with the official parser (MIT),
// headless (jsdom), no browser and no network at check time.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

// مستقل از cwd: ریشهٔ مخزن نسبت به محل همین فایل تعیین می‌شود.
const ROOT = fileURLToPath(new URL('../..', import.meta.url));

const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.Element = dom.window.Element;
globalThis.HTMLElement = dom.window.HTMLElement;

const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false });

function markdownFiles() {
  const out = execFileSync('git', ['-C', ROOT, 'ls-files', '*.md'], { encoding: 'utf8' });
  return out.split('\n').map((l) => l.trim()).filter(Boolean);
}

function blocks(path) {
  const lines = readFileSync(path, 'utf8').split('\n');
  const found = [];
  let start = -1;
  let body = [];
  for (let i = 0; i < lines.length; i += 1) {
    const fence = /^\s*```(\S*)\s*$/.exec(lines[i]);
    if (!fence) {
      if (start !== -1) body.push(lines[i]);
      continue;
    }
    if (start === -1) {
      if (fence[1].toLowerCase() === 'mermaid') {
        start = i + 1;
        body = [];
      }
      continue;
    }
    found.push({ line: start, text: body.join('\n').trim() });
    start = -1;
    body = [];
  }
  return found;
}

let checked = 0;
const failures = [];
for (const relative of markdownFiles()) {
  const path = `${ROOT}${relative}`;
  for (const block of blocks(path)) {
    if (!block.text) {
      failures.push(`${relative}:${block.line}: empty Mermaid block`);
      continue;
    }
    try {
      await mermaid.parse(block.text);
      checked += 1;
    } catch (error) {
      failures.push(`${relative}:${block.line}: ${String(error.message || error).split('\n')[0]}`);
    }
  }
}

if (failures.length) {
  console.error('Mermaid syntax gate FAILED:');
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}
console.log(`Mermaid syntax gate passed: ${checked} diagram(s) parsed by mermaid ${mermaid.mermaidAPI?.getConfig?.().version ?? ''}`.trim());
