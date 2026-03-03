#!/usr/bin/env node
/**
 * Scan Intercom conversations for ARCA mass-import / data-migration demand.
 *
 * Phase 1: Onboarding inbox (team_assignee_id: 2334166 = "Primeros 90 días")
 * Phase 2: All conversations (no team filter)
 *
 * Usage:
 *   node scan_arca_import_demand.mjs [--phase onboarding|all] [--from YYYY-MM-DD] [--to YYYY-MM-DD]
 */

import axios from 'axios';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load env
dotenv.config({ path: join(__dirname, '../../../.env') });
dotenv.config({ path: join(__dirname, '../../.env') });

const TOKEN = process.env.INTERCOM_ACCESS_TOKEN;
if (!TOKEN) { console.error('INTERCOM_ACCESS_TOKEN not set'); process.exit(1); }

const api = axios.create({
  baseURL: 'https://api.intercom.io',
  headers: {
    'Authorization': `Bearer ${TOKEN}`,
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Intercom-Version': '2.13',
  },
  timeout: 30000,
});

// ── CLI args ──
const args = process.argv.slice(2);
const getArg = (name, def) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : def; };
const phase = getArg('--phase', 'onboarding'); // 'onboarding' or 'all'
const fromDate = getArg('--from', '2025-09-01');
const toDate = getArg('--to', '2026-03-03');

const ONBOARDING_TEAM_ID = '2334166'; // "Primeros 90 días"

// ── Keywords ──
// Broad keywords to catch any mention of ARCA, import, migration, mass load
const KEYWORDS = [
  'arca',
  'importar',
  'importación',
  'importacion',
  'migrar',
  'migración',
  'migracion',
  'carga masiva',
  'datos masivos',
  'traer facturas',
  'descargar facturas',
  'bajar facturas',
  'sistema anterior',
  'sistema viejo',
  'factura electrónica',
  'factura electronica',
  'afip',
];

// ── Helpers ──
function toUnix(dateStr, endOfDay = false) {
  const iso = `${dateStr}${endOfDay ? 'T23:59:59Z' : 'T00:00:00Z'}`;
  return Math.floor(Date.parse(iso) / 1000);
}

function stripHtml(html) {
  if (!html || typeof html !== 'string') return '';
  let text = html.replace(/<[^>]+>/g, ' ');
  text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  text = text.replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&nbsp;/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

async function retryable(fn, retries = 3) {
  for (let i = 1; i <= retries; i++) {
    try { return await fn(); }
    catch (e) {
      if (i === retries) throw e;
      const wait = e.response?.status === 429
        ? (parseInt(e.response.headers['retry-after'] || '5') * 1000)
        : 1000 * i;
      await new Promise(r => setTimeout(r, wait));
    }
  }
}

// ── Fetch all conversation IDs in range ──
async function fetchAllIds(teamId) {
  const queryValues = [
    { field: 'created_at', operator: '>=', value: toUnix(fromDate) },
    { field: 'created_at', operator: '<=', value: toUnix(toDate, true) },
  ];
  if (teamId) queryValues.push({ field: 'team_assignee_id', operator: '=', value: teamId });

  const allIds = [];
  let startingAfter = null;
  while (true) {
    const body = {
      query: { operator: 'AND', value: queryValues },
      pagination: { per_page: 150 },
    };
    if (startingAfter) body.pagination.starting_after = startingAfter;
    const resp = await retryable(() => api.post('/conversations/search', body));
    const convs = resp.data.conversations || [];
    if (convs.length === 0) break;
    allIds.push(...convs.map(c => ({ id: c.id, created_at: c.created_at, source_body: stripHtml(c.source?.body || '') })));
    const next = resp.data.pages?.next?.starting_after;
    if (!next) break;
    startingAfter = next;
  }
  return allIds;
}

// ── Fetch full conversation and scan ──
async function scanConversation(convId) {
  const resp = await retryable(() => api.get(`/conversations/${convId}`));
  const conv = resp.data;

  // Build full text from all parts
  const parts = [];
  if (conv.source) {
    parts.push({ author_type: conv.source.author?.type || 'unknown', body: stripHtml(conv.source.body || ''), created_at: conv.created_at });
  }
  for (const p of (conv.conversation_parts?.conversation_parts || [])) {
    const body = stripHtml(p.body || '');
    if (!body) continue;
    parts.push({ author_type: p.author?.type || 'unknown', body, created_at: p.created_at });
  }

  // Check keywords
  const matchedParts = [];
  for (const p of parts) {
    const lower = p.body.toLowerCase();
    const hits = KEYWORDS.filter(kw => lower.includes(kw));
    if (hits.length > 0) {
      matchedParts.push({
        author_type: p.author_type,
        keywords: hits,
        excerpt: p.body.substring(0, 300),
        created_at: p.created_at ? new Date(p.created_at * 1000).toISOString() : null,
      });
    }
  }

  // Get tags
  const tags = [];
  const t = conv.tags;
  if (t && typeof t === 'object' && !Array.isArray(t)) {
    for (const tag of (t.tags || [])) tags.push(typeof tag === 'object' ? tag.name : String(tag));
  }

  // Get contact info
  let contactName = '';
  let contactEmail = '';
  if (conv.contacts?.contacts?.length > 0) {
    const c = conv.contacts.contacts[0];
    contactName = c.name || '';
    contactEmail = c.email || '';
  }

  return {
    conversation_id: convId,
    created_at: conv.created_at ? new Date(conv.created_at * 1000).toISOString() : '',
    state: conv.state,
    tags,
    contact_name: contactName,
    contact_email: contactEmail,
    total_parts: parts.length,
    matched_parts: matchedParts,
    all_keywords_found: [...new Set(matchedParts.flatMap(p => p.keywords))],
  };
}

// ── Main ──
async function main() {
  const teamId = phase === 'onboarding' ? ONBOARDING_TEAM_ID : null;
  const label = phase === 'onboarding' ? 'Onboarding (Primeros 90 días)' : 'All conversations';

  console.log(`\n═══ ARCA Import Demand Scan ═══`);
  console.log(`Phase: ${label}`);
  console.log(`Date range: ${fromDate} → ${toDate}`);
  console.log(`Keywords: ${KEYWORDS.join(', ')}`);
  console.log(`───────────────────────────────────\n`);

  // Step 1: Get all conversation IDs
  console.log('Fetching conversation IDs...');
  const allConvs = await fetchAllIds(teamId);
  console.log(`Total conversations in range: ${allConvs.length}`);

  // Step 2: Quick pre-filter on source body (first message) to reduce API calls
  const preFiltered = allConvs.filter(c => {
    const lower = c.source_body.toLowerCase();
    return KEYWORDS.some(kw => lower.includes(kw));
  });
  console.log(`Pre-filtered (source body keyword match): ${preFiltered.length}`);

  // Step 3: Full-text scan all conversations (not just pre-filtered)
  // We do full scan because keywords may appear in agent replies or user follow-ups
  console.log(`\nStarting full-text scan of ${allConvs.length} conversations (batches of 5)...\n`);

  const matches = [];
  const BATCH = 5;
  for (let i = 0; i < allConvs.length; i += BATCH) {
    const batch = allConvs.slice(i, i + BATCH);
    const results = await Promise.all(batch.map(async (c) => {
      try { return await scanConversation(c.id); }
      catch (e) { console.error(`  Error scanning ${c.id}: ${e.message}`); return null; }
    }));
    for (const r of results) {
      if (r && r.matched_parts.length > 0) matches.push(r);
    }
    if ((i + BATCH) % 50 === 0 || i + BATCH >= allConvs.length) {
      console.log(`  Scanned ${Math.min(i + BATCH, allConvs.length)}/${allConvs.length} — matches so far: ${matches.length}`);
    }
  }

  // Step 4: Filter for ARCA-import-specific matches (not just generic "arca" or "afip")
  // A conversation is "import-relevant" if it mentions arca/afip AND import/migration/mass-load keywords
  const importKeywords = ['importar', 'importación', 'importacion', 'migrar', 'migración', 'migracion',
    'carga masiva', 'datos masivos', 'traer facturas', 'descargar facturas', 'bajar facturas',
    'sistema anterior', 'sistema viejo'];
  const sourceKeywords = ['arca', 'afip', 'factura electrónica', 'factura electronica'];

  const arcaImportMatches = matches.filter(m => {
    const allKw = m.all_keywords_found;
    const hasSource = allKw.some(kw => sourceKeywords.includes(kw));
    const hasImport = allKw.some(kw => importKeywords.includes(kw));
    return hasSource && hasImport;
  });

  // Step 5: Report
  console.log(`\n═══ RESULTS ═══`);
  console.log(`Total conversations scanned: ${allConvs.length}`);
  console.log(`Conversations with ANY keyword match: ${matches.length}`);
  console.log(`Conversations with ARCA+import combo: ${arcaImportMatches.length}`);

  console.log(`\n── All keyword matches (${matches.length}) ──\n`);
  for (const m of matches) {
    console.log(`  [${m.conversation_id}] ${m.created_at} | ${m.state} | tags: ${m.tags.join(', ') || '(none)'}`);
    console.log(`    Contact: ${m.contact_name} <${m.contact_email}>`);
    console.log(`    Keywords: ${m.all_keywords_found.join(', ')}`);
    for (const p of m.matched_parts) {
      console.log(`    [${p.author_type}] ${p.excerpt.substring(0, 150)}...`);
    }
    console.log('');
  }

  if (arcaImportMatches.length > 0) {
    console.log(`\n── ARCA + Import intent matches (${arcaImportMatches.length}) ──\n`);
    for (const m of arcaImportMatches) {
      console.log(`  [${m.conversation_id}] ${m.created_at} | ${m.state}`);
      console.log(`    Contact: ${m.contact_name} <${m.contact_email}>`);
      console.log(`    Keywords: ${m.all_keywords_found.join(', ')}`);
      for (const p of m.matched_parts) {
        console.log(`    [${p.author_type}] ${p.excerpt.substring(0, 200)}`);
      }
      console.log('');
    }
  }

  // Save full results to JSON
  const outputPath = join(__dirname, `arca_import_scan_${phase}_${new Date().toISOString().split('T')[0]}.json`);
  fs.writeFileSync(outputPath, JSON.stringify({
    scan_config: { phase, label, fromDate, toDate, keywords: KEYWORDS },
    summary: {
      total_conversations: allConvs.length,
      keyword_matches: matches.length,
      arca_import_matches: arcaImportMatches.length,
    },
    matches,
    arca_import_matches: arcaImportMatches,
  }, null, 2));
  console.log(`\nFull results saved to: ${outputPath}`);
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
