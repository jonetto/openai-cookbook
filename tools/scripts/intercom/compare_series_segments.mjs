#!/usr/bin/env node
/**
 * Download Content Data Export zip, list all CSVs, parse every segment-like file,
 * and compare counts for NPS series (448114) with our receipt-based metrics.
 * Usage: node compare_series_segments.mjs [from_date] [to_date]
 */
import axios from 'axios';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import AdmZip from 'adm-zip';

import {
  createContentDataExport,
  getContentDataExportStatus,
  downloadContentDataExport,
  aggregateSeriesFromReceiptsCsv,
  toUnixBoundary,
} from './intercom-api-helpers.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, '../../../.env') });

const from_date = process.argv[2] || '2026-03-01';
const to_date = process.argv[3] || '2026-03-10';
const NPS_SERIES_ID = '448114';

/** Export window: start N days before report from_date so receipt CSV includes receipts referenced by segment events in period (Intercom may limit range length) */
const EXPORT_LOOKBACK_DAYS = 3;
function exportFromDate(reportFrom) {
  const d = new Date(reportFrom + 'T12:00:00Z');
  d.setUTCDate(d.getUTCDate() - EXPORT_LOOKBACK_DAYS);
  return d.toISOString().slice(0, 10);
}

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

function parseCsvLine(line) {
  const out = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if (!inQuotes && c === ',') {
      out.push(cur);
      cur = '';
      continue;
    }
    cur += c;
  }
  out.push(cur);
  return out;
}

function parseTimestamp(val) {
  if (val == null || String(val).trim() === '') return null;
  const v = String(val).trim();
  const num = Number(v);
  if (!Number.isNaN(num) && num > 0) {
    return num > 1e12 ? Math.floor(num / 1000) : Math.floor(num);
  }
  const ms = Date.parse(v);
  return Number.isNaN(ms) ? null : Math.floor(ms / 1000);
}

/** Normalize header for flexible matching: lowercase, trim, collapse spaces */
function norm(h) {
  return (h || '').toString().trim().toLowerCase().replace(/\s+/g, ' ');
}

/** Find column index by possible names (case-insensitive) or regex */
function columnIndex(header, patterns) {
  for (let i = 0; i < header.length; i++) {
    const n = norm(header[i]);
    for (const p of patterns) {
      if (typeof p === 'string' && norm(p) === n) return i;
      if (p instanceof RegExp && p.test(header[i])) return i;
    }
  }
  return -1;
}

/** Date column patterns per segment file type (order = preference) */
const DATE_PATTERNS = {
  series_completion: [/completed_at|completion_at|completed|completion_timestamp/i, /created_at|timestamp|at/i],
  series_disengagement: [/disengaged_at|disengagement_at|disengaged|disengagement_timestamp/i, /created_at|timestamp|at/i],
  series_exit: [/exited_at|exit_at|exited|exit_timestamp/i, /created_at|timestamp|at/i],
  goal_success: [/goal_hit_at|success_at|goal_at|goal_success|success_timestamp/i, /created_at|timestamp|at/i],
};

/**
 * Build map receipt_id -> { series_id, user_id } from receipt CSV.
 * Segment CSVs only have receipt_id; we join to get series and user.
 */
function buildReceiptMap(receiptCsvText) {
  const lines = receiptCsvText.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return new Map();
  const header = parseCsvLine(lines[0]);
  const receiptIdIdx = columnIndex(header, ['receipt_id', 'receipt id', /receipt.*id/i]);
  const seriesIdIdx = columnIndex(header, ['series_id', 'series id', /series.*id|id.*series/i]);
  const userIdIdx = columnIndex(header, ['user_id', 'user id', 'email', 'contact_id']);
  if (receiptIdIdx < 0 || seriesIdIdx < 0 || userIdIdx < 0) return new Map();
  const map = new Map();
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    const receiptId = (row[receiptIdIdx] || '').toString().trim().replace(/^"|"$/g, '');
    const seriesId = (row[seriesIdIdx] || '').toString().trim().replace(/^"|"$/g, '');
    const userId = (row[userIdIdx] || '').toString().trim().replace(/^"|"$/g, '');
    if (!receiptId || seriesId === '-1') continue;
    map.set(receiptId, { series_id: seriesId, user_id: userId });
  }
  return map;
}

/**
 * Count distinct users in a segment CSV for the given series_id and date range.
 * Segment files have receipt_id (not series_id); pass receiptMap from receipt CSV to join.
 */
function countSegmentCsvWithReceiptJoin(csvText, fromDate, toDate, seriesId, fileType, receiptMap) {
  const fromTs = toUnixBoundary(fromDate, false);
  const toTs = toUnixBoundary(toDate, true);
  const inPeriod = (ts) => ts != null && ts >= fromTs && ts <= toTs;
  const lines = csvText.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return { count: 0, headers: parseCsvLine(lines[0]) };
  const header = parseCsvLine(lines[0]);
  const receiptIdIdx = columnIndex(header, ['receipt_id', 'receipt id', /receipt.*id/i]);
  const datePatterns = DATE_PATTERNS[fileType] || [/created_at|timestamp|at|date/i];
  let dateIdx = -1;
  for (const pat of datePatterns) {
    dateIdx = header.findIndex((h) => pat.test(String(h)));
    if (dateIdx >= 0) break;
  }
  if (dateIdx < 0) dateIdx = header.findIndex((h) => /at|date|timestamp/i.test(String(h)));
  if (receiptIdIdx < 0 || dateIdx < 0 || !receiptMap || receiptMap.size === 0) {
    return { count: 0, headers: header };
  }
  const users = new Set();
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    const receiptId = (row[receiptIdIdx] || '').toString().trim().replace(/^"|"$/g, '');
    const info = receiptMap.get(receiptId);
    if (!info || (info.series_id !== seriesId && info.series_id !== String(seriesId))) continue;
    const ts = parseTimestamp(row[dateIdx]);
    if (ts == null || !inPeriod(ts)) continue;
    if (info.user_id) users.add(info.user_id);
  }
  return { count: users.size, headers: header };
}

/** Count distinct users with at least one receipt in the report period (received_at in range). Use when export window is wider than report. */
function startedInReportPeriodFromReceiptCsv(receiptCsvText, fromDate, toDate, seriesId) {
  const fromTs = toUnixBoundary(fromDate, false);
  const toTs = toUnixBoundary(toDate, true);
  const inPeriod = (ts) => ts != null && ts >= fromTs && ts <= toTs;
  const lines = receiptCsvText.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return 0;
  const header = parseCsvLine(lines[0]);
  const seriesIdIdx = columnIndex(header, ['series_id', 'series id', /series.*id|id.*series/i]);
  const userIdIdx = columnIndex(header, ['user_id', 'user id', 'email', 'contact_id']);
  const receivedIdx = columnIndex(header, ['received_at', 'received at', /received|sent_at|created_at/i]);
  if (seriesIdIdx < 0 || userIdIdx < 0 || receivedIdx < 0) return 0;
  const users = new Set();
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    const rowSeriesId = (row[seriesIdIdx] || '').toString().trim().replace(/^"|"$/g, '');
    if (rowSeriesId !== seriesId && rowSeriesId !== String(seriesId)) continue;
    const ts = parseTimestamp(row[receivedIdx]);
    if (!inPeriod(ts)) continue;
    const uid = (row[userIdIdx] || '').toString().trim();
    if (uid) users.add(uid);
  }
  return users.size;
}

function countRowsInPeriod(csvText, fromDate, toDate, options = {}) {
  const fromTs = toUnixBoundary(fromDate, false);
  const toTs = toUnixBoundary(toDate, true);
  const inPeriod = (ts) => ts != null && ts >= fromTs && ts <= toTs;
  const lines = csvText.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return { bySeries: {}, total: 0 };
  const header = parseCsvLine(lines[0]);
  const seriesIdIdx = columnIndex(header, ['series_id', 'series id', /series.*id|id.*series/i]);
  const userIdIdx = columnIndex(header, ['user_id', 'user id', 'email', 'contact_id']);
  const dateCol = options.dateColumn || header.find((h) => /at|date|timestamp/i.test(h));
  const dateIdx = dateCol ? header.indexOf(dateCol) : -1;
  const bySeries = new Map();
  let total = 0;
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    const seriesId = seriesIdIdx >= 0 ? (row[seriesIdIdx] || '').toString().trim().replace(/^"|"$/g, '') : '';
    if (seriesId === '-1' || (seriesIdIdx >= 0 && !seriesId)) continue;
    const ts = dateIdx >= 0 ? parseTimestamp(row[dateIdx]) : null;
    if (dateIdx >= 0 && ts != null && !inPeriod(ts)) continue;
    const key = seriesId || '_all';
    if (!bySeries.has(key)) bySeries.set(key, new Set());
    const userKey = userIdIdx >= 0 ? row[userIdIdx] : i;
    bySeries.get(key).add(String(userKey));
    total++;
  }
  const bySeriesObj = {};
  bySeries.forEach((set, key) => { bySeriesObj[key] = set.size; });
  return { bySeries: bySeriesObj, total };
}

async function main() {
  if (!process.env.INTERCOM_ACCESS_TOKEN) {
    console.error('INTERCOM_ACCESS_TOKEN not set');
    process.exit(1);
  }

  const export_from = exportFromDate(from_date);
  console.error(`Creating export ${export_from} → ${to_date} (report period ${from_date} → ${to_date})...`);
  let jobId;
  try {
    const created = await createContentDataExport(intercomApi, export_from, to_date);
    jobId = created.job_identifier;
  } catch (e) {
    if (e.response?.status === 429) {
      console.error('Another export job is already running.');
      process.exit(1);
    }
    throw e;
  }

  console.error(`Polling job ${jobId}...`);
  const deadline = Date.now() + 600000;
  let status = 'pending';
  let downloadUrl = null;
  while (Date.now() < deadline) {
    const res = await getContentDataExportStatus(intercomApi, jobId);
    status = res.status;
    downloadUrl = res.download_url || null;
    if (status === 'completed' && downloadUrl) break;
    if (status === 'no_data' || status === 'failed') {
      console.error(status);
      process.exit(1);
    }
    await new Promise((r) => setTimeout(r, 30000));
  }
  if (status !== 'completed' || !downloadUrl) {
    console.error('Export did not complete in time');
    process.exit(1);
  }

  const fullUrl = downloadUrl.startsWith('http') ? downloadUrl : `${intercomApi.defaults.baseURL}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
  console.error('Downloading zip...');
  const rawBuffer = await downloadContentDataExport(intercomApi, fullUrl);
  if (rawBuffer[0] !== 0x50 || rawBuffer[1] !== 0x4b) {
    console.error('Download is not a ZIP');
    process.exit(1);
  }

  const zip = new AdmZip(rawBuffer);
  const entries = zip.getEntries().filter((e) => !e.isDirectory && e.entryName.toLowerCase().endsWith('.csv'));
  console.error('\nAll CSV files in export zip:', entries.map((e) => e.entryName));

  const results = { from_receipt: null, from_other_files: {}, file_headers: {}, from_segment_files: null };
  let receiptCsvText = null;
  /** Map base type (e.g. series_completion) -> full CSV text for first matching file */
  const segmentCsvByType = {};

  for (const entry of entries) {
    const name = entry.entryName;
    const csvText = entry.getData().toString('utf8');
    const lines = csvText.split(/\r?\n/).filter((l) => l.trim());
    const header = lines[0] ? parseCsvLine(lines[0]) : [];
    results.file_headers[name] = header.slice(0, 20);

    if (/receipt.*\.csv$/i.test(name)) {
      receiptCsvText = csvText;
      const { series } = aggregateSeriesFromReceiptsCsv(csvText, { fromDate: from_date, toDate: to_date });
      const nps = series.find((s) => s.series_id === NPS_SERIES_ID);
      results.from_receipt = nps || null;
      continue;
    }

    if (/^series_completion_/.test(name) && !segmentCsvByType.series_completion) segmentCsvByType.series_completion = csvText;
    if (/^series_disengagement_/.test(name) && !segmentCsvByType.series_disengagement) segmentCsvByType.series_disengagement = csvText;
    if (/^series_exit_/.test(name) && !segmentCsvByType.series_exit) segmentCsvByType.series_exit = csvText;
    if (/^goal_success_/.test(name) && !segmentCsvByType.goal_success) segmentCsvByType.goal_success = csvText;

    const hasSeriesId = header.some((h) => /series_id|series\s*id/i.test(String(h)));
    const dateCol = header.find((h) => /at|date|timestamp|completed|disengag|exit|goal|success/i.test(String(h)));
    const { bySeries, total } = countRowsInPeriod(csvText, from_date, to_date, {
      dateColumn: dateCol,
    });
    if (hasSeriesId || total > 0) {
      results.from_other_files[name] = {
        total,
        series_448114: bySeries[NPS_SERIES_ID] ?? bySeries['448114'] ?? null,
        by_series_sample: Object.entries(bySeries).slice(0, 5),
      };
    }
  }

  if (receiptCsvText) {
    const { series } = aggregateSeriesFromReceiptsCsv(receiptCsvText, { fromDate: from_date, toDate: to_date });
    results.from_receipt = series.find((s) => s.series_id === NPS_SERIES_ID) || null;
  }

  // Build receipt_id -> { series_id, user_id } so we can join segment CSVs (they only have receipt_id)
  const receiptMap = receiptCsvText ? buildReceiptMap(receiptCsvText) : new Map();

  // UI-aligned metrics from segment CSVs joined with receipt (same source as Intercom UI)
  // When export window is wider than report, "started" = users with receipt in report period only
  const startedCount = export_from !== from_date
    ? startedInReportPeriodFromReceiptCsv(receiptCsvText, from_date, to_date, NPS_SERIES_ID)
    : results.from_receipt?.started ?? null;
  const segment = {
    started: startedCount,
    finished: null,
    disengaged: null,
    exited: null,
    goal: null,
    _segment_headers: {},
  };
  if (segmentCsvByType.series_completion) {
    const r = countSegmentCsvWithReceiptJoin(segmentCsvByType.series_completion, from_date, to_date, NPS_SERIES_ID, 'series_completion', receiptMap);
    segment.finished = r.count;
    segment._segment_headers.series_completion = r.headers;
  }
  if (segmentCsvByType.series_disengagement) {
    const r = countSegmentCsvWithReceiptJoin(segmentCsvByType.series_disengagement, from_date, to_date, NPS_SERIES_ID, 'series_disengagement', receiptMap);
    segment.disengaged = r.count;
    segment._segment_headers.series_disengagement = r.headers;
  }
  if (segmentCsvByType.series_exit) {
    const r = countSegmentCsvWithReceiptJoin(segmentCsvByType.series_exit, from_date, to_date, NPS_SERIES_ID, 'series_exit', receiptMap);
    segment.exited = r.count;
    segment._segment_headers.series_exit = r.headers;
  }
  if (segmentCsvByType.goal_success) {
    const r = countSegmentCsvWithReceiptJoin(segmentCsvByType.goal_success, from_date, to_date, NPS_SERIES_ID, 'goal_success', receiptMap);
    segment.goal = r.count;
    segment._segment_headers.goal_success = r.headers;
  }
  results.from_segment_files = segment;

  console.log('\n=== NPS series', NPS_SERIES_ID, from_date, '→', to_date, '===\n');
  console.log('Receipt-based (in-period):');
  console.log(JSON.stringify(results.from_receipt, null, 2));
  console.log('\nUI-aligned (from segment CSVs – use these to compare with Intercom UI):');
  console.log(JSON.stringify({
    started: segment.started,
    finished: segment.finished,
    disengaged: segment.disengaged,
    exited: segment.exited,
    goal: segment.goal,
  }, null, 2));
  console.log('\nSegment CSV column headers (for debugging):');
  Object.entries(segment._segment_headers).forEach(([k, h]) => {
    console.log('  ' + k + ':', (h || []).slice(0, 15).join(', '));
  });
  console.log('\nOther CSV files in zip (counts in period where applicable):');
  console.log(JSON.stringify(results.from_other_files, null, 2));
  console.log('\nZip contained:', entries.length, 'CSV files.');
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
