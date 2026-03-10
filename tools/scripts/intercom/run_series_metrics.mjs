#!/usr/bin/env node
/**
 * One-off runner for Intercom Series metrics (March 2026 or any date range).
 * Usage: node run_series_metrics.mjs [from_date] [to_date]
 * Default: 2026-03-01 to 2026-03-31
 */
import axios from 'axios';
import zlib from 'zlib';
import fs from 'fs';
import os from 'os';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import dotenv from 'dotenv';
import * as tar from 'tar';
import AdmZip from 'adm-zip';

import {
  retryableRequest,
  createContentDataExport,
  getContentDataExportStatus,
  downloadContentDataExport,
  aggregateSeriesFromReceiptsCsv,
} from './intercom-api-helpers.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, '../../../.env') });

const from_date = process.argv[2] || '2026-03-01';
const to_date = process.argv[3] || '2026-03-31';

const intercomApi = axios.create({
  baseURL: 'https://api.intercom.io',
  headers: {
    Authorization: `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}`,
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'Intercom-Version': '2.13',
  },
  timeout: 30000,
});

async function main() {
  if (!process.env.INTERCOM_ACCESS_TOKEN) {
    console.error('INTERCOM_ACCESS_TOKEN not set');
    process.exit(1);
  }

  console.error(`Creating content export for ${from_date} to ${to_date}...`);
  let jobId;
  try {
    const created = await createContentDataExport(intercomApi, from_date, to_date);
    jobId = created.job_identifier;
  } catch (e) {
    if (e.response?.status === 429) {
      console.error('Another export job is already running. Try again later.');
      process.exit(1);
    }
    throw e;
  }

  console.error(`Job ${jobId}; polling until complete...`);
  const pollIntervalMs = 30000;
  const deadline = Date.now() + 600000;
  let status = 'pending';
  let downloadUrl = null;

  while (Date.now() < deadline) {
    const res = await getContentDataExportStatus(intercomApi, jobId);
    status = res.status;
    downloadUrl = res.download_url || null;
    if (status === 'completed' && downloadUrl) break;
    if (status === 'no_data') {
      console.log(JSON.stringify({ success: true, date_range: { from: from_date, to: to_date }, series: [], message: 'No message data in range' }, null, 2));
      return;
    }
    if (status === 'failed' || status === 'canceled') {
      console.error(`Export ${status}`);
      process.exit(1);
    }
    await new Promise((r) => setTimeout(r, pollIntervalMs));
  }

  if (status !== 'completed' || !downloadUrl) {
    console.error('Export did not complete in time');
    process.exit(1);
  }

  const fullUrl = downloadUrl.startsWith('http') ? downloadUrl : `${intercomApi.defaults.baseURL}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
  console.error('Downloading export...');
  const rawBuffer = await downloadContentDataExport(intercomApi, fullUrl);
  let csvText;

  const isZip = rawBuffer.length >= 2 && rawBuffer[0] === 0x50 && rawBuffer[1] === 0x4b;
  const isGzip = rawBuffer.length >= 2 && rawBuffer[0] === 0x1f && rawBuffer[1] === 0x8b;

  if (isZip) {
    const zip = new AdmZip(rawBuffer);
    const entries = zip.getEntries();
    const receiptEntry = entries.find((e) => !e.isDirectory && e.entryName.match(/receipt.*\.csv$/i));
    if (!receiptEntry) {
      console.error('ZIP contains no receipt CSV. Entries:', entries.map((e) => e.entryName).slice(0, 10));
      process.exit(1);
    }
    csvText = receiptEntry.getData().toString('utf8');
  } else {
    let decompressed;
    if (isGzip) {
      try {
        decompressed = zlib.gunzipSync(rawBuffer);
      } catch (e) {
        console.error('Gunzip failed:', e.message);
        process.exit(1);
      }
    } else {
      decompressed = rawBuffer;
    }
    const asText = decompressed.toString('utf8');
    const head = decompressed.slice(0, 10000).toString('utf8');
    const looksLikeCsv = head.includes('series_id') || head.includes('user_id') || (head.includes('receipt') && head.includes(','));
    csvText = asText;
    if (!looksLikeCsv) {
      const tmpDir = join(os.tmpdir(), `intercom-export-${jobId}`);
      fs.mkdirSync(tmpDir, { recursive: true });
      const tarPath = join(tmpDir, 'export.tar');
      fs.writeFileSync(tarPath, decompressed);
      try {
        await tar.x({ file: tarPath, cwd: tmpDir });
        const files = fs.readdirSync(tmpDir).filter((f) => f.startsWith('receipts_') && f.endsWith('.csv'));
        if (files.length > 0) {
          csvText = fs.readFileSync(join(tmpDir, files[0]), 'utf8');
        }
      } catch (_) {}
      try { fs.rmSync(tmpDir, { recursive: true }); } catch (_) {}
    }
  }

  const { series } = aggregateSeriesFromReceiptsCsv(csvText, { fromDate: from_date, toDate: to_date });
  console.log(JSON.stringify({
    success: true,
    date_range: { from: from_date, to: to_date },
    series,
    note: 'Finished/Disengaged/Exited/Goal = users whose event timestamp is in the date range (aligns with UI). Started = distinct users with ≥1 message receipt in period (UI "Started" = users who entered the series in period; export has no enrollment date, so our started can be higher). See tools/docs/INTERCOM_SERIES_UI_VS_EXPORT.md.',
  }, null, 2));
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
