#!/usr/bin/env node
/**
 * Classify the ARCA import matches from scan_arca_import_demand into intent categories:
 *
 * A. ARCA_PULL     — User wants to pull/download data FROM ARCA into Colppy (the feature request)
 * B. MIGRATE_OTHER — User wants to migrate from another system (Tango, old system, etc.)
 * C. IMPORT_PAIN   — User struggling with existing CSV import process (indirect signal)
 * D. ARCA_ISSUE    — User has ARCA connectivity/config issues (NOT about import)
 * E. GENERIC       — Generic mention of import + AFIP/ARCA, not about mass import
 */

import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load scan results
const scanFile = process.argv[2] || join(__dirname, 'arca_import_scan_onboarding_2026-03-03.json');
const data = JSON.parse(fs.readFileSync(scanFile, 'utf8'));

// Classification rules (applied in order - first match wins)
const rules = [
  {
    category: 'A_ARCA_PULL',
    label: 'Wants to pull/download data from ARCA',
    patterns: [
      /bajar\s+(de|desde)\s+arca/i,
      /traer\s+(de|desde)\s+arca/i,
      /descargar\s+(de|desde)\s+arca/i,
      /importar\s+(de|desde|directamente\s+desde)\s+arca/i,
      /importar.*arca/i,  // Less specific but still intent
      /arca.*importar/i,
      /trae.*automátic.*arca/i,
      /trae.*de\s+forma\s+automática.*arca/i,
      /todas?\s+las?\s+facturas?\s+(de|desde)\s+arca/i,
      /comprobantes?\s+(de|desde)\s+arca/i,
      /factura.*arca.*import/i,
      /arca.*factura.*import/i,
      /cuit.*importar/i,
      /cuit.*descargar/i,
      /cuit.*traer/i,
      /un\s+click.*arca/i,
      /automáticamente.*arca/i,
    ]
  },
  {
    category: 'B_MIGRATE_OTHER',
    label: 'Wants to migrate from another system',
    patterns: [
      /migrar.*sistema\s+anterior/i,
      /sistema\s+anterior.*migrar/i,
      /migrar.*(tango|xubio|alegra|quickbooks|bejerman|contasoft|fortia)/i,
      /migración.*sistema/i,
      /(tango|xubio|alegra).*migrar/i,
      /migrar.*cuentas?\s+corrientes?/i,
      /sistema\s+anterior/i,
      /sistema\s+viejo/i,
    ]
  },
  {
    category: 'C_IMPORT_PAIN',
    label: 'Struggling with existing CSV import (indirect signal)',
    patterns: [
      /archivo\s+modelo.*no\s+(me\s+)?permit/i,
      /error.*importa(r|ción|cion)/i,
      /importa(r|ción|cion).*error/i,
      /no\s+logr[oó].*importa/i,
      /no\s+pud[eio].*importa/i,
      /renegando.*importa/i,
      /problemas.*importa(r|ción)/i,
      /importa(r|ción).*problemas/i,
      /mucho\s+tiempo.*importa/i,
      /demora.*importa/i,
      /carga\s+masiva/i,
      /subir.*comprobantes/i,
      /subida\s+completa/i,
      /importar\s+todo\s+el\s+listado/i,
      /importa(r|ción).*facturas.*todo\s+el\s+ejercicio/i,
      /csv.*error/i,
      /error.*csv/i,
      /archivo.*no\s+respeta/i,
    ]
  },
  {
    category: 'D_ARCA_ISSUE',
    label: 'ARCA connectivity/config issues (not about import)',
    patterns: [
      /error.*conect.*arca/i,
      /arca.*error/i,
      /no.*figura.*arca/i,
      /código.*actividad.*arca/i,
      /registrado.*arca/i,
      /vinculaci[oó]n.*factura\s+electr[oó]nica/i,
      /factura\s+electr[oó]nica.*vinculaci/i,
      /punto\s+de\s+venta.*arca/i,
      /arca.*punto\s+de\s+venta/i,
      /delegación.*factura\s+electr/i,
    ]
  },
];

// Classify each match
const classified = { A_ARCA_PULL: [], B_MIGRATE_OTHER: [], C_IMPORT_PAIN: [], D_ARCA_ISSUE: [], E_GENERIC: [] };

for (const match of data.arca_import_matches) {
  // Build full text from matched parts (user messages only for intent)
  const userText = match.matched_parts
    .filter(p => p.author_type === 'user' || p.author_type === 'lead')
    .map(p => p.excerpt)
    .join(' ');
  const allText = match.matched_parts.map(p => p.excerpt).join(' ');
  const tags = (match.tags || []).join(' ');

  let category = 'E_GENERIC';
  let matchedPattern = null;

  for (const rule of rules) {
    for (const pattern of rule.patterns) {
      if (pattern.test(userText) || pattern.test(allText) || pattern.test(tags)) {
        category = rule.category;
        matchedPattern = pattern.toString();
        break;
      }
    }
    if (category !== 'E_GENERIC') break;
  }

  classified[category].push({
    ...match,
    classification: category,
    matched_rule: matchedPattern,
    user_text_preview: userText.substring(0, 200) || '(no user text captured)',
  });
}

// Report
console.log('═══ ARCA Import Demand Classification ═══');
console.log(`Date range: ${data.scan_config?.fromDate || '?'} → ${data.scan_config?.toDate || '?'}`);
console.log(`Total onboarding conversations: ${data.summary.total_conversations}`);
console.log(`Keyword matches: ${data.summary.keyword_matches}`);
console.log(`ARCA+import combos: ${data.summary.arca_import_matches}`);
console.log('');

const labels = {
  A_ARCA_PULL: 'A. ARCA PULL — Wants to pull data from ARCA into Colppy',
  B_MIGRATE_OTHER: 'B. MIGRATE — Wants to migrate from another system',
  C_IMPORT_PAIN: 'C. IMPORT PAIN — Struggling with existing import process',
  D_ARCA_ISSUE: 'D. ARCA ISSUE — ARCA connectivity/config issue',
  E_GENERIC: 'E. GENERIC — Generic import + AFIP/ARCA mention',
};

console.log('── Category Summary ──');
for (const [cat, items] of Object.entries(classified)) {
  const pct = ((items.length / data.summary.total_conversations) * 100).toFixed(1);
  console.log(`  ${labels[cat]}: ${items.length} (${pct}% of all onboarding)`);
}
console.log('');

// Feature demand = A + B + C (direct + indirect signals)
const directDemand = classified.A_ARCA_PULL.length;
const migrationDemand = classified.B_MIGRATE_OTHER.length;
const importPain = classified.C_IMPORT_PAIN.length;
const totalDemandSignal = directDemand + migrationDemand + importPain;

console.log('── Feature Demand Signal ──');
console.log(`  Direct "pull from ARCA" requests:    ${directDemand}`);
console.log(`  Migration from other systems:        ${migrationDemand}`);
console.log(`  Import process pain (indirect):      ${importPain}`);
console.log(`  TOTAL demand signal:                 ${totalDemandSignal} (${((totalDemandSignal / data.summary.total_conversations) * 100).toFixed(1)}% of onboarding)`);
console.log('');

// Print details for each category
for (const [cat, items] of Object.entries(classified)) {
  if (items.length === 0) continue;
  console.log(`\n── ${labels[cat]} (${items.length}) ──`);
  for (const m of items) {
    console.log(`  [${m.conversation_id}] ${m.created_at} | ${m.state}`);
    console.log(`    Tags: ${m.tags.join(', ') || '(none)'}`);
    console.log(`    Keywords: ${m.all_keywords_found.join(', ')}`);
    if (m.user_text_preview && m.user_text_preview !== '(no user text captured)') {
      console.log(`    User: ${m.user_text_preview.substring(0, 150)}`);
    }
    console.log('');
  }
}

// Save classified results
const outPath = join(__dirname, `arca_demand_classified_${new Date().toISOString().split('T')[0]}.json`);
fs.writeFileSync(outPath, JSON.stringify({
  scan_config: data.scan_config,
  summary: {
    ...data.summary,
    classification: Object.fromEntries(Object.entries(classified).map(([k, v]) => [k, v.length])),
    demand_signal: { direct: directDemand, migration: migrationDemand, import_pain: importPain, total: totalDemandSignal },
  },
  classified,
}, null, 2));
console.log(`\nClassified results saved to: ${outPath}`);
