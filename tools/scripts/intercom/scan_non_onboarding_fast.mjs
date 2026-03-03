#!/usr/bin/env node
/**
 * Fast scan of NON-onboarding conversations for ARCA import demand.
 *
 * Strategy:
 * 1. Fetch all conversation IDs (no team filter) in the date range
 * 2. Quick pre-filter on source body (first message) for keywords
 * 3. Full-text scan ONLY the pre-filtered matches
 * 4. Exclude conversations already found in onboarding scan
 */

import axios from 'axios';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, '../../../.env') });

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

const fromDate = '2025-09-01';
const toDate = '2026-03-03';

// Load onboarding scan to get already-found IDs
const onboardingScan = JSON.parse(fs.readFileSync(join(__dirname, 'arca_import_scan_onboarding_2026-03-03.json'), 'utf8'));
const onboardingIds = new Set(onboardingScan.matches.map(m => m.conversation_id));
console.log(`Loaded ${onboardingIds.size} onboarding conversation IDs to exclude`);

// Keywords (same as before)
const KEYWORDS = [
  'arca', 'importar', 'importación', 'importacion', 'migrar', 'migración', 'migracion',
  'carga masiva', 'datos masivos', 'traer facturas', 'descargar facturas', 'bajar facturas',
  'sistema anterior', 'sistema viejo', 'factura electrónica', 'factura electronica', 'afip',
];

// ARCA-specific import keywords (for the combo filter)
const importKw = ['importar', 'importación', 'importacion', 'migrar', 'migración', 'migracion',
  'carga masiva', 'datos masivos', 'traer facturas', 'descargar facturas', 'bajar facturas',
  'sistema anterior', 'sistema viejo'];
const sourceKw = ['arca', 'afip', 'factura electrónica', 'factura electronica'];

function toUnix(dateStr, endOfDay = false) {
  return Math.floor(Date.parse(`${dateStr}${endOfDay ? 'T23:59:59Z' : 'T00:00:00Z'}`) / 1000);
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

async function main() {
  console.log(`\n=== Non-Onboarding ARCA Import Demand Scan ===`);
  console.log(`Date range: ${fromDate} -> ${toDate}\n`);

  // Step 1: Fetch ALL conversations (no team filter) and pre-filter on source body
  const queryValues = [
    { field: 'created_at', operator: '>=', value: toUnix(fromDate) },
    { field: 'created_at', operator: '<=', value: toUnix(toDate, true) },
  ];

  let totalConvs = 0;
  const preFiltered = [];
  let startingAfter = null;

  console.log('Step 1: Fetching and pre-filtering ALL conversations on source body...');
  while (true) {
    const body = {
      query: { operator: 'AND', value: queryValues },
      pagination: { per_page: 150 },
    };
    if (startingAfter) body.pagination.starting_after = startingAfter;

    const resp = await retryable(() => api.post('/conversations/search', body));
    const convs = resp.data.conversations || [];
    if (convs.length === 0) break;

    totalConvs += convs.length;

    for (const c of convs) {
      // Skip if already in onboarding scan
      if (onboardingIds.has(c.id)) continue;

      const sourceBody = stripHtml(c.source?.body || '').toLowerCase();
      const matchedKw = KEYWORDS.filter(kw => sourceBody.includes(kw));
      if (matchedKw.length === 0) continue;

      // Check for ARCA+import combo in source body
      const hasSource = matchedKw.some(kw => sourceKw.includes(kw));
      const hasImport = matchedKw.some(kw => importKw.includes(kw));

      preFiltered.push({
        id: c.id,
        created_at: c.created_at,
        state: c.state,
        source_body: stripHtml(c.source?.body || ''),
        matched_keywords: matchedKw,
        is_arca_import_combo: hasSource && hasImport,
      });
    }

    const next = resp.data.pages?.next?.starting_after;
    if (!next) break;
    startingAfter = next;

    if (totalConvs % 300 === 0) {
      console.log(`  Fetched ${totalConvs} conversations, pre-filtered matches: ${preFiltered.length}`);
    }
  }

  console.log(`\nTotal ALL conversations: ${totalConvs}`);
  console.log(`Non-onboarding with keyword match (source body): ${preFiltered.length}`);
  console.log(`Non-onboarding with ARCA+import combo (source body): ${preFiltered.filter(p => p.is_arca_import_combo).length}`);

  // Step 2: Full-text scan the ARCA+import combo matches (max ~200)
  const toDeepScan = preFiltered.filter(p => p.is_arca_import_combo).slice(0, 200);
  console.log(`\nStep 2: Full-text scanning ${toDeepScan.length} ARCA+import conversations...`);

  const matches = [];
  const BATCH = 5;
  for (let i = 0; i < toDeepScan.length; i += BATCH) {
    const batch = toDeepScan.slice(i, i + BATCH);
    const results = await Promise.all(batch.map(async (c) => {
      try {
        const resp = await retryable(() => api.get(`/conversations/${c.id}`));
        const conv = resp.data;
        const parts = [];
        if (conv.source) parts.push({ author_type: conv.source.author?.type || 'unknown', body: stripHtml(conv.source.body || ''), created_at: conv.created_at });
        for (const p of (conv.conversation_parts?.conversation_parts || [])) {
          const body = stripHtml(p.body || '');
          if (!body) continue;
          parts.push({ author_type: p.author?.type || 'unknown', body, created_at: p.created_at });
        }

        const matchedParts = [];
        for (const p of parts) {
          const lower = p.body.toLowerCase();
          const hits = KEYWORDS.filter(kw => lower.includes(kw));
          if (hits.length > 0) matchedParts.push({ author_type: p.author_type, keywords: hits, excerpt: p.body.substring(0, 300), created_at: p.created_at ? new Date(p.created_at * 1000).toISOString() : null });
        }

        const tags = [];
        const t = conv.tags;
        if (t && typeof t === 'object' && !Array.isArray(t)) for (const tag of (t.tags || [])) tags.push(typeof tag === 'object' ? tag.name : String(tag));

        let contactName = '', contactEmail = '';
        if (conv.contacts?.contacts?.length > 0) { contactName = conv.contacts.contacts[0].name || ''; contactEmail = conv.contacts.contacts[0].email || ''; }

        return {
          conversation_id: c.id,
          created_at: conv.created_at ? new Date(conv.created_at * 1000).toISOString() : '',
          state: conv.state,
          tags,
          contact_name: contactName,
          contact_email: contactEmail,
          total_parts: parts.length,
          matched_parts: matchedParts,
          all_keywords_found: [...new Set(matchedParts.flatMap(p => p.keywords))],
        };
      } catch (e) { return null; }
    }));
    for (const r of results) { if (r && r.matched_parts.length > 0) matches.push(r); }
    if ((i + BATCH) % 20 === 0) console.log(`  Scanned ${Math.min(i + BATCH, toDeepScan.length)}/${toDeepScan.length}`);
  }

  // Apply same ARCA+import combo filter to full text results
  const arcaImportMatches = matches.filter(m => {
    const allKw = m.all_keywords_found;
    return allKw.some(kw => sourceKw.includes(kw)) && allKw.some(kw => importKw.includes(kw));
  });

  console.log(`\n=== RESULTS (Non-Onboarding) ===`);
  console.log(`Total conversations scanned: ${totalConvs}`);
  console.log(`Already in onboarding: ${onboardingIds.size}`);
  console.log(`Pre-filtered (source body keywords): ${preFiltered.length}`);
  console.log(`ARCA+import deep-scanned: ${toDeepScan.length}`);
  console.log(`Full-text ARCA+import matches: ${arcaImportMatches.length}`);

  // Print matches
  console.log(`\n--- ARCA + Import intent matches (${arcaImportMatches.length}) ---\n`);
  for (const m of arcaImportMatches) {
    console.log(`  [${m.conversation_id}] ${m.created_at} | ${m.state}`);
    console.log(`    Tags: ${m.tags.join(', ') || '(none)'}`);
    console.log(`    Keywords: ${m.all_keywords_found.join(', ')}`);
    const userParts = m.matched_parts.filter(p => p.author_type === 'user' || p.author_type === 'lead');
    if (userParts.length > 0) {
      for (const p of userParts) console.log(`    [user] ${p.excerpt.substring(0, 200)}`);
    }
    console.log('');
  }

  // Save
  const outPath = join(__dirname, `arca_import_scan_non_onboarding_${new Date().toISOString().split('T')[0]}.json`);
  fs.writeFileSync(outPath, JSON.stringify({
    scan_config: { fromDate, toDate, phase: 'non-onboarding' },
    summary: {
      total_all_conversations: totalConvs,
      onboarding_excluded: onboardingIds.size,
      pre_filtered_keyword_matches: preFiltered.length,
      arca_import_combo_source: preFiltered.filter(p => p.is_arca_import_combo).length,
      full_text_arca_import_matches: arcaImportMatches.length,
    },
    pre_filtered: preFiltered,
    arca_import_matches: arcaImportMatches,
  }, null, 2));
  console.log(`\nSaved to: ${outPath}`);
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
