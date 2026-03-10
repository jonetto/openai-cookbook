#!/usr/bin/env node

/**
 * Download a Google Slides presentation as PDF.
 *
 * Usage: node download-slides.js <url-or-id>
 *
 * Works with any presentation shared via link. No API keys or auth needed.
 * Output: cache/<presentation-id>.pdf
 */

import fs from 'fs/promises';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CACHE_DIR = join(__dirname, 'cache');

const input = process.argv[2];
if (!input) {
  console.error('Usage: node download-slides.js <google-slides-url-or-id>');
  process.exit(1);
}

const match = input.match(/\/presentation\/d\/([a-zA-Z0-9_-]+)/);
const id = match ? match[1] : input;
const pdfUrl = `https://docs.google.com/presentation/d/${id}/export/pdf`;

await fs.mkdir(CACHE_DIR, { recursive: true });

console.log(`Downloading ${id}...`);
const res = await fetch(pdfUrl, { redirect: 'follow' });

if (!res.ok) {
  console.error(`Failed: HTTP ${res.status}. Is the presentation shared via link?`);
  process.exit(1);
}

const buf = Buffer.from(await res.arrayBuffer());
const outPath = join(CACHE_DIR, `${id}.pdf`);
await fs.writeFile(outPath, buf);
console.log(`Saved: ${outPath} (${(buf.length / 1024 / 1024).toFixed(1)} MB)`);
