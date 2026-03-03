import fs from 'fs';
const data = JSON.parse(fs.readFileSync('arca_import_scan_onboarding_2026-03-03.json', 'utf8'));

const highlight_ids = [
  '215471494688991',
  '215472595432533',
  '215472860096218',
  '215471368664361',
  '215472925738091',
  '215471661403306',
  '215471207812860',
  '215470873896927',
  '215470857389277',
  '215470617626072',
  '215472997033503',
  '215471174225201',
  '215470751278948',
];

for (const m of data.matches) {
  if (!highlight_ids.includes(m.conversation_id)) continue;
  console.log('===', m.conversation_id, '===');
  console.log('Date:', m.created_at, '| State:', m.state);
  console.log('Tags:', m.tags.join(', '));
  console.log('Keywords:', m.all_keywords_found.join(', '));
  console.log('');
  for (const p of m.matched_parts) {
    console.log('[' + p.author_type + ']', p.excerpt);
    console.log('');
  }
  console.log('---\n');
}
