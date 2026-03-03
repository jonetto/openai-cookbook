#!/usr/bin/env node

/**
 * Convert llm_classify output into labeled CSVs for Feature Upvote items.
 *
 * Input:
 *  - cache JSON created by feature_upvote_prepare_llm_input.mjs
 *  - classified JSON created by llm_classify.mjs (non --all mode recommended)
 *
 * Output:
 *  - real ideas CSV
 *  - support complaints CSV
 *  - markdown summary
 */

import fs from 'fs';
import { join } from 'path';

const PLUGIN_ROOT = new URL('..', import.meta.url).pathname;

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    cache: null,
    classified: null,
    realOut: null,
    complaintsOut: null,
    summaryOut: null,
  };

  for (let i = 0; i < args.length; i += 1) {
    const a = args[i];
    if (a === '--cache' && args[i + 1]) opts.cache = args[++i];
    else if (a === '--classified' && args[i + 1]) opts.classified = args[++i];
    else if (a === '--real-out' && args[i + 1]) opts.realOut = args[++i];
    else if (a === '--complaints-out' && args[i + 1]) opts.complaintsOut = args[++i];
    else if (a === '--summary-out' && args[i + 1]) opts.summaryOut = args[++i];
  }

  if (!opts.cache || !opts.classified || !opts.realOut || !opts.complaintsOut || !opts.summaryOut) {
    console.error('Usage: node scripts/feature_upvote_apply_llm_labels.mjs --cache <cache.json> --classified <classified.json> --real-out <real.csv> --complaints-out <complaints.csv> --summary-out <summary.md>');
    process.exit(1);
  }

  return opts;
}

function resolvePath(p) {
  if (p.startsWith('/')) return p;
  return join(PLUGIN_ROOT, p);
}

function ensureDir(path) {
  const dir = path.split('/').slice(0, -1).join('/');
  if (dir && !fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function csvEscape(v) {
  const s = String(v ?? '');
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function writeCsv(path, rows, headers) {
  const lines = [headers.join(',')];
  for (const row of rows) {
    lines.push(headers.map((h) => csvEscape(row[h])).join(','));
  }
  fs.writeFileSync(path, lines.join('\n') + '\n', 'utf8');
}

function monthOf(d) {
  return String(d || '').slice(0, 7);
}

function main() {
  const opts = parseArgs();
  const cachePath = resolvePath(opts.cache);
  const classifiedPath = resolvePath(opts.classified);
  const realOut = resolvePath(opts.realOut);
  const complaintsOut = resolvePath(opts.complaintsOut);
  const summaryOut = resolvePath(opts.summaryOut);

  if (!fs.existsSync(cachePath)) {
    console.error(`Cache not found: ${cachePath}`);
    process.exit(1);
  }
  if (!fs.existsSync(classifiedPath)) {
    console.error(`Classified file not found: ${classifiedPath}`);
    process.exit(1);
  }

  const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
  const classified = JSON.parse(fs.readFileSync(classifiedPath, 'utf8'));

  const allConversations = cache.conversations || [];
  const byId = new Map(allConversations.map((c) => [String(c.conversation_id), c]));

  const classifiedRows = (classified.classified || []).map((r) => ({
    id: String(r.conversation_id),
    is_match: Boolean(r.llm?.is_match),
    confidence: Number(r.llm?.confidence || 0),
    category: String(r.llm?.category || ''),
    reasoning: String(r.llm?.reasoning || ''),
  }));

  const matchIds = new Set(classifiedRows.filter((x) => x.is_match).map((x) => x.id));
  const llmById = new Map(classifiedRows.map((x) => [x.id, x]));

  const labeled = allConversations.map((c) => {
    const id = String(c.conversation_id);
    const llm = llmById.get(id) || {
      id,
      is_match: false,
      confidence: 0,
      category: 'not_classified',
      reasoning: 'No LLM classification found for this item.',
    };

    return {
      suggestion_id: id,
      title: c.source_title || '',
      description: c.source_description || '',
      name: c.source_name || '',
      email: c.source_email || '',
      votes: c.source_votes ?? 0,
      comments: c.source_comments ?? 0,
      date_created: c.source_date_created || c.created_at || '',
      status: c.source_status || c.state || '',
      tags: Array.isArray(c.source_tags) ? c.source_tags.join(', ') : (Array.isArray(c.tags) ? c.tags.join(', ') : ''),
      llm_category: llm.category,
      llm_confidence: llm.confidence,
      llm_reasoning: llm.reasoning,
      classification: matchIds.has(id) ? 'real_idea' : 'support_complaint',
    };
  });

  const realIdeas = labeled.filter((x) => x.classification === 'real_idea');
  const complaints = labeled.filter((x) => x.classification === 'support_complaint');

  const headers = [
    'suggestion_id',
    'title',
    'description',
    'name',
    'email',
    'votes',
    'comments',
    'date_created',
    'status',
    'tags',
    'llm_category',
    'llm_confidence',
    'llm_reasoning',
    'classification',
  ];

  ensureDir(realOut);
  ensureDir(complaintsOut);
  ensureDir(summaryOut);

  writeCsv(realOut, realIdeas, headers);
  writeCsv(complaintsOut, complaints, headers);

  const monthly = new Map();
  for (const row of labeled) {
    const m = monthOf(row.date_created);
    if (!monthly.has(m)) {
      monthly.set(m, { total: 0, real_ideas: 0, support_complaints: 0 });
    }
    const agg = monthly.get(m);
    agg.total += 1;
    if (row.classification === 'real_idea') agg.real_ideas += 1;
    else agg.support_complaints += 1;
  }

  const summaryLines = [];
  summaryLines.push('# Feature Upvote LLM Triage Summary');
  summaryLines.push('');
  summaryLines.push(`- Total items: ${labeled.length}`);
  summaryLines.push(`- Real ideas: ${realIdeas.length}`);
  summaryLines.push(`- Support complaints: ${complaints.length}`);
  summaryLines.push('');
  summaryLines.push('## By month');
  summaryLines.push('');

  for (const month of [...monthly.keys()].sort().reverse()) {
    const s = monthly.get(month);
    summaryLines.push(`- ${month}: total=${s.total}, real_ideas=${s.real_ideas}, support_complaints=${s.support_complaints}`);
  }

  summaryLines.push('');
  summaryLines.push('## Latest real ideas');
  summaryLines.push('');
  const latestReal = [...realIdeas].sort((a, b) => String(b.date_created).localeCompare(String(a.date_created))).slice(0, 40);
  for (const r of latestReal) {
    summaryLines.push(`- ${r.date_created} | ${r.suggestion_id} | ${r.title} | ${r.llm_category}`);
  }

  fs.writeFileSync(summaryOut, summaryLines.join('\n') + '\n', 'utf8');

  console.log(JSON.stringify({
    total: labeled.length,
    real_ideas: realIdeas.length,
    support_complaints: complaints.length,
    real_out: realOut,
    complaints_out: complaintsOut,
    summary_out: summaryOut,
  }, null, 2));
}

main();
