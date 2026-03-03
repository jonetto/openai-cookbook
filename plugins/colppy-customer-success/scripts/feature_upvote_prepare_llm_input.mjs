#!/usr/bin/env node

/**
 * Prepare Feature Upvote CSV export data for scripts/llm_classify.mjs.
 *
 * Produces two JSON files:
 * 1) cache JSON (Intercom-like conversation cache shape)
 * 2) scan results JSON (all entries pre-selected for classification)
 *
 * Example:
 *   node scripts/feature_upvote_prepare_llm_input.mjs \
 *     --csv docs/feature_upvote_export_all_2026-03-02.csv \
 *     --from 2025-12-01 \
 *     --to 2026-02-28 \
 *     --cache-out docs/feature_upvote_cache_dec2025_feb2026.json \
 *     --results-out docs/feature_upvote_scan_dec2025_feb2026.json
 */

import fs from 'fs';
import { join } from 'path';

const PLUGIN_ROOT = new URL('..', import.meta.url).pathname;

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    csv: null,
    from: null,
    to: null,
    cacheOut: null,
    resultsOut: null,
  };

  for (let i = 0; i < args.length; i += 1) {
    const a = args[i];
    if (a === '--csv' && args[i + 1]) opts.csv = args[++i];
    else if (a === '--from' && args[i + 1]) opts.from = args[++i];
    else if (a === '--to' && args[i + 1]) opts.to = args[++i];
    else if (a === '--cache-out' && args[i + 1]) opts.cacheOut = args[++i];
    else if (a === '--results-out' && args[i + 1]) opts.resultsOut = args[++i];
  }

  if (!opts.csv || !opts.from || !opts.to || !opts.cacheOut || !opts.resultsOut) {
    console.error('Usage: node scripts/feature_upvote_prepare_llm_input.mjs --csv <csv> --from YYYY-MM-DD --to YYYY-MM-DD --cache-out <json> --results-out <json>');
    process.exit(1);
  }

  return opts;
}

function resolvePath(p) {
  if (p.startsWith('/')) return p;
  return join(PLUGIN_ROOT, p);
}

function normalizeText(v) {
  return String(v || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function splitCsv(value) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < value.length; i += 1) {
    const ch = value[i];
    const next = value[i + 1];

    if (ch === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (ch === ',' && !inQuotes) {
      row.push(field);
      field = '';
      continue;
    }

    if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && next === '\n') i += 1;
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
      continue;
    }

    field += ch;
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return rows;
}

function parseCsvRecords(csvText) {
  const rawRows = splitCsv(String(csvText || ''));
  if (rawRows.length === 0) return [];

  const headers = rawRows[0].map((h, idx) => {
    const text = idx === 0 ? String(h || '').replace(/^\uFEFF/, '') : String(h || '');
    return normalizeText(text);
  });

  const records = [];
  for (let i = 1; i < rawRows.length; i += 1) {
    const row = rawRows[i];
    if (!row || row.every((x) => String(x || '').trim() === '')) continue;
    const obj = {};
    for (let j = 0; j < headers.length; j += 1) {
      obj[headers[j]] = row[j] ?? '';
    }
    records.push(obj);
  }
  return records;
}

function parseDateTime(raw) {
  const text = String(raw || '').trim();
  if (!text) return null;
  const iso = text.replace(' ', 'T') + 'Z';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d;
}

function inRange(d, from, to) {
  if (!d) return false;
  return d >= from && d <= to;
}

function toIsoNoMs(d) {
  if (!d) return null;
  return d.toISOString().replace(/\.\d{3}Z$/, '.000Z');
}

function splitTags(raw) {
  return String(raw || '')
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean);
}

function buildConversationText(record) {
  const parts = [
    `Title: ${record['title'] || ''}`,
    `Description: ${record['description'] || ''}`,
    `Status: ${record['status'] || ''}`,
    `Status code: ${record['status code'] || ''}`,
    `Votes: ${record['votes'] || '0'}`,
    `Comments: ${record['comments'] || '0'}`,
    `Tags: ${record['tags'] || ''}`,
    `Submitted by: ${record['name'] || ''} <${record['email'] || ''}>`,
  ];
  return parts.join('\n');
}

function ensureDir(path) {
  const dir = path.split('/').slice(0, -1).join('/');
  if (dir && !fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function main() {
  const opts = parseArgs();
  const csvPath = resolvePath(opts.csv);
  const cacheOut = resolvePath(opts.cacheOut);
  const resultsOut = resolvePath(opts.resultsOut);

  if (!fs.existsSync(csvPath)) {
    console.error(`CSV not found: ${csvPath}`);
    process.exit(1);
  }

  const from = new Date(`${opts.from}T00:00:00.000Z`);
  const to = new Date(`${opts.to}T23:59:59.999Z`);
  if (Number.isNaN(from.getTime()) || Number.isNaN(to.getTime())) {
    console.error('Invalid --from/--to date');
    process.exit(1);
  }

  const csvText = fs.readFileSync(csvPath, 'utf8');
  const records = parseCsvRecords(csvText)
    .map((r) => ({ ...r, _dt: parseDateTime(r['date created']) }))
    .filter((r) => inRange(r._dt, from, to))
    .sort((a, b) => b._dt - a._dt);

  const conversations = records.map((r) => {
    const suggestionId = String(r['suggestion id'] || '').trim();
    const createdAt = toIsoNoMs(r._dt);
    const tags = splitTags(r['tags']);
    const conversationText = buildConversationText(r);

    return {
      conversation_id: suggestionId,
      created_at: createdAt,
      state: String(r['status code'] || '').trim() || 'unknown',
      contact_email: String(r['email'] || '').trim() || null,
      contact_es_contador: null,
      contact_rol_wizard: null,
      tags,
      parts: [
        {
          author_type: 'user',
          body: conversationText,
          created_at: createdAt,
        },
      ],
      source_type: 'feature_upvote_csv',
      source_status: String(r['status'] || '').trim() || null,
      source_votes: Number.parseInt(String(r['votes'] || '0').replace(/[^\d]/g, ''), 10) || 0,
      source_comments: Number.parseInt(String(r['comments'] || '0').replace(/[^\d]/g, ''), 10) || 0,
      source_name: String(r['name'] || '').trim() || null,
      source_email: String(r['email'] || '').trim() || null,
      source_title: String(r['title'] || '').trim() || '',
      source_description: String(r['description'] || '').trim() || '',
      source_tags: tags,
      source_date_created: String(r['date created'] || '').trim() || null,
    };
  });

  const cachePayload = {
    from_date: opts.from,
    to_date: opts.to,
    state: 'all',
    team_assignee_id: null,
    topic: 'Feature Upvote suggestions',
    saved_at: new Date().toISOString(),
    conversations,
  };

  const scanMatches = conversations.map((c) => ({
    conversation_id: c.conversation_id,
    created_at: c.created_at,
    state: c.state,
    tags: c.tags,
    match_reason: 'feature_upvote_entry',
    matched_in: [
      {
        author_type: 'user',
        matched_keywords: ['feature_upvote_entry'],
        excerpt: c.source_title || c.parts[0].body.slice(0, 160),
        created_at: c.created_at,
        full_body: c.parts[0].body,
      },
    ],
    admin_assignee_id: null,
    contact_count: 1,
    conversation_thread: [],
  }));

  const scanPayload = {
    success: true,
    source: 'feature_upvote_csv_prepared',
    research_topic: 'Feature Upvote ideas triage',
    search_criteria: {
      keywords: ['feature_upvote_entry'],
      from_date: opts.from,
      to_date: opts.to,
      state: 'all',
      exclude_if_only: [],
    },
    conversations_scanned: conversations.length,
    matches_found: scanMatches.length,
    matches: scanMatches,
  };

  ensureDir(cacheOut);
  ensureDir(resultsOut);
  fs.writeFileSync(cacheOut, JSON.stringify(cachePayload, null, 2), 'utf8');
  fs.writeFileSync(resultsOut, JSON.stringify(scanPayload, null, 2), 'utf8');

  console.log(JSON.stringify({
    csv: csvPath,
    from: opts.from,
    to: opts.to,
    conversations: conversations.length,
    cache_out: cacheOut,
    results_out: resultsOut,
  }, null, 2));
}

main();
