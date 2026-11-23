#!/usr/bin/env node
// Render a Graphviz DOT file to SVG and high-resolution PNG.
// This is repository documentation tooling only; it is not imported by the app.
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, extname } from 'node:path';
import { instance } from '@viz-js/viz';
import sharp from 'sharp';

const [inputArg, outputArg, widthArg = '4800'] = process.argv.slice(2);
if (!inputArg || !outputArg) {
  console.error('Usage: npm run render -- <input.dot> <output.png> [width_px]');
  process.exit(2);
}
const input = resolve(inputArg);
const output = resolve(outputArg);
const width = Number(widthArg);
if (!Number.isInteger(width) || width < 1200 || width > 12000) {
  throw new Error('width_px must be an integer between 1200 and 12000');
}
const dot = await readFile(input, 'utf8');
const viz = await instance();
const svg = viz.renderString(dot, { engine: 'dot', format: 'svg' });
const stem = output.slice(0, output.length - extname(output).length);
const svgPath = `${stem}.svg`;
await writeFile(svgPath, svg, 'utf8');
const rendered = await sharp(Buffer.from(svg), { density: 72 })
  .resize({ width, withoutEnlargement: false })
  .png({ compressionLevel: 9, adaptiveFiltering: true })
  .toFile(output);
console.log(`DOT: ${input}`);
console.log(`SVG: ${svgPath}`);
console.log(`PNG: ${output} (${rendered.width}x${rendered.height}, ${rendered.size} bytes)`);
