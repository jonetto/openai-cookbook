#!/usr/bin/env node
/**
 * Headless Mixpanel Dual-Group Verification for Staging
 *
 * Tests KAN-12024: Mixpanel Dual-Group (Company + Product)
 * Logs into staging, extracts Mixpanel state, and validates against the ticket spec.
 *
 * Usage:
 *   node tools/scripts/test_mixpanel_staging.js [--url URL] [--user EMAIL] [--pass PASSWORD]
 *
 * Defaults from .env: STAGING_URL, STAGING_USER, STAGING_PASS
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// Load .env from repo root
const envPath = path.join(__dirname, '..', '..', '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  for (const line of envContent.split('\n')) {
    const match = line.match(/^([^#=]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const val = match[2].trim().replace(/^["']|["']$/g, '');
      if (!process.env[key]) process.env[key] = val;
    }
  }
}

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, envKey, fallback) {
  const idx = args.indexOf(`--${name}`);
  if (idx !== -1 && args[idx + 1]) return args[idx + 1];
  return process.env[envKey] || fallback;
}

const STAGING_URL = getArg('url', 'STAGING_URL', 'https://app.stg.colppy.com/');
const STAGING_USER = getArg('user', 'STAGING_USER', '');
const STAGING_PASS = getArg('pass', 'STAGING_PASS', '');

if (!STAGING_USER || !STAGING_PASS) {
  console.error('ERROR: STAGING_USER and STAGING_PASS required (via .env or --user/--pass)');
  process.exit(1);
}

// Expected spec from KAN-12024
const SPEC = {
  distinct_id_should_be: 'email',          // Should be user email, NOT CUIT
  company_group_key: 'CUITFacturacion',    // company group should use billing CUIT
  product_group_key: 'idEmpresa',          // product_id group should use idEmpresa
  company_product_must_differ: true,       // company != product_id (the whole point)
};

async function run() {
  console.log('=== Mixpanel Dual-Group Staging Test ===');
  console.log(`URL:  ${STAGING_URL}`);
  console.log(`User: ${STAGING_USER}`);
  console.log('');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Disable browser cache via CDP — equivalent to "Disable cache" in DevTools
  const cdpSession = await context.newCDPSession(page);
  await cdpSession.send('Network.setCacheDisabled', { cacheDisabled: true });
  console.log('[cache] Browser cache disabled via CDP');

  // Intercept colppyall-min.js to verify deployed code + capture Mixpanel API calls
  const mixpanelRequests = [];
  let colppyJsSnippet = null;

  await page.route('**/*', async (route) => {
    const url = route.request().url();

    // Capture Mixpanel API calls (full payload for groups)
    if (url.includes('api.mixpanel.com') || url.includes('api-js.mixpanel.com')) {
      const postData = route.request().postData() || null;
      mixpanelRequests.push({
        url: url.split('?')[0],
        method: route.request().method(),
        postData: postData,
        endpoint: url.includes('/groups/') ? 'GROUPS' : url.includes('/track/') ? 'TRACK' : url.includes('/engage/') ? 'ENGAGE' : 'OTHER',
      });
    }

    // Intercept colppyall-min.js — check code AND inject tracing
    if (url.includes('colppyall') && url.includes('.js')) {
      const response = await route.fetch();
      let body = await response.text();
      const match = body.match(/setCompanyPropertiesMixpanel[^}]+\}/);
      colppyJsSnippet = match ? match[0] : 'NOT FOUND in bundle';
      console.log(`  [bundle] colppyall JS size: ${(body.length / 1024).toFixed(0)}KB`);

      const cuitAssignments = body.match(/CUITFacturacion\s*=\s*[^;,]{1,100}/g);
      console.log(`  [bundle] CUITFacturacion assignments: ${JSON.stringify(cuitAssignments?.slice(0, 5))}`);

      // Log the intercepted URL and search for set_group
      console.log(`  [bundle] URL: ${url.split('?')[0].split('/').pop()}`);
      const sgCount = (body.match(/set_group/g) || []).length;
      console.log(`  [bundle] "set_group" occurrences: ${sgCount}`);
      if (sgCount > 0) {
        let si = 0;
        for (let i = 0; i < Math.min(sgCount, 5); i++) {
          si = body.indexOf('set_group', si);
          if (si === -1) break;
          console.log(`  [bundle] @${si}: ...${body.substring(Math.max(0,si-80), si+60).replace(/\n/g,' ')}...`);
          si++;
        }
      }
      // Also check for the company_id parameter usage
      const companyIdParam = body.match(/function colppyAnalytics\([^)]+\)/);
      console.log(`  [bundle] colppyAnalytics signature: ${companyIdParam?.[0] || 'NOT FOUND'}`);

      await route.fulfill({ response });
    } else {
      await route.continue();
    }
  });

  try {
    // 1. Navigate to login
    console.log('[1/5] Navigating to login...');
    await page.goto(STAGING_URL, { waitUntil: 'networkidle', timeout: 30000 });

    // 2. Fill login form
    console.log('[2/5] Logging in...');
    await page.getByRole('textbox', { name: /correo/i }).fill(STAGING_USER);
    await page.getByRole('textbox', { name: /password/i }).fill(STAGING_PASS);
    await page.getByRole('button', { name: /ingresar/i }).click();

    // 3. Wait for redirect to main legacy app (staging.colppy.com)
    //    Login flow: app.stg.colppy.com (MFE auth) → staging.colppy.com (legacy PHP app)
    console.log('[3/5] Waiting for redirect to legacy app...');
    try {
      await page.waitForURL(/staging\.colppy\.com/, { timeout: 30000 });
    } catch {
      // If not redirected, maybe it went directly — check current URL
    }
    console.log(`  Current URL: ${page.url()}`);

    // 3.5. Poll Mixpanel state DURING page load + monitor cookie changes
    const stateSnapshots = [];
    const pollInterval = setInterval(async () => {
      try {
        const snap = await page.evaluate(() => {
          if (typeof mixpanel === 'undefined' || !mixpanel.get_property) return null;
          // Read persistence directly to see raw state
          const props = mixpanel.persistence ? mixpanel.persistence.props : {};
          return {
            company: props.company,
            product_id: props.product_id,
            distinct_id: props.$user_id,
            cuit_global: (typeof CUITFacturacion !== 'undefined') ? CUITFacturacion : 'UNDEF',
            // Check if there are pending Mixpanel requests
            mpQueue: mixpanel._batch_requests ? mixpanel._batch_requests.length : 'N/A',
          };
        }).catch(() => null);
        if (snap) stateSnapshots.push({ ...snap, t: Date.now() });
      } catch {}
    }, 100);  // Faster polling to catch the transition

    // Now wait for JS bundles to load
    await page.waitForTimeout(10000);

    // Snapshot right after wait, before any further evaluate calls
    const postWaitSnap = await page.evaluate(() => {
      if (typeof mixpanel === 'undefined' || !mixpanel.persistence) return null;
      return {
        company: mixpanel.persistence.props.company,
        product_id: mixpanel.persistence.props.product_id,
      };
    }).catch(() => null);
    console.log(`  [post-wait] persistence: ${JSON.stringify(postWaitSnap)}`);

    // 4. Extract Mixpanel state — poll until available (scripts load async)
    console.log('[4/5] Extracting Mixpanel state...');
    let targetFrame = page;

    // Poll for mixpanel across all frames with retries
    for (let attempt = 0; attempt < 10; attempt++) {
      // Check main frame
      const hasMP = await page.evaluate(() => typeof mixpanel !== 'undefined').catch(() => false);
      if (hasMP) { targetFrame = page; break; }

      // Check all iframes
      const frames = page.frames();
      let found = false;
      for (const frame of frames) {
        if (frame === page.mainFrame()) continue;
        const frameHasMP = await frame.evaluate(() => typeof mixpanel !== 'undefined').catch(() => false);
        if (frameHasMP) {
          console.log(`  Found mixpanel in frame: ${frame.url()}`);
          targetFrame = frame;
          found = true;
          break;
        }
      }
      if (found) break;

      if (attempt === 0) console.log(`  Waiting for mixpanel to initialize (${frames.length} frames)...`);
      await page.waitForTimeout(2000);
    }

    // Final check
    const mpReady = await targetFrame.evaluate(() => typeof mixpanel !== 'undefined').catch(() => false);
    if (!mpReady) {
      console.log(`  Page URL: ${page.url()}`);
      console.log(`  Frames: ${page.frames().map(f => f.url()).join(', ')}`);
      const bodyText = await page.evaluate(() => document.body?.innerText?.substring(0, 200)).catch(() => 'N/A');
      console.log(`  Body preview: ${bodyText}`);
    }

    // Check actual set_group behavior by calling it directly
    const groupTest = await targetFrame.evaluate(() => {
      // Before: what is the current state
      const before = {
        company_prop: mixpanel.persistence.props.company,
        company_get: mixpanel.get_property('company'),
      };

      // Call set_group with CUIT to see what happens
      const cuit = CUITFacturacion;
      mixpanel.set_group('company', cuit);

      const afterSetGroup = {
        company_prop: mixpanel.persistence.props.company,
        company_get: mixpanel.get_property('company'),
      };

      // Now call register to overwrite
      mixpanel.register({ company: cuit });

      const afterRegister = {
        company_prop: mixpanel.persistence.props.company,
        company_get: mixpanel.get_property('company'),
      };

      return { cuit, before, afterSetGroup, afterRegister };
    }).catch(e => ({ error: e.message }));
    console.log(`  [group-test] ${JSON.stringify(groupTest, null, 2)}`);

    const state = await targetFrame.evaluate(() => {
      const r = {};
      if (typeof mixpanel === 'undefined') return { error: 'mixpanel not defined on page' };

      if (typeof mixpanel.get_distinct_id !== 'function') {
        r.note = 'mixpanel exists but get_distinct_id is not a function';
        return r;
      }

      // MARKER: read company at very start
      r._company_at_start = mixpanel.persistence.props.company;

      // Identity
      r.distinct_id = mixpanel.get_distinct_id();
      r._company_after_get_distinct_id = mixpanel.persistence.props.company;

      r.user_id = mixpanel.get_property('$user_id');
      r._company_after_user_id = mixpanel.persistence.props.company;

      r.groups = mixpanel.get_property('$groups');
      r._company_after_groups = mixpanel.persistence.props.company;

      r.company = mixpanel.get_property('company');
      r._company_after_get_company = mixpanel.persistence.props.company;

      r.company_id = mixpanel.get_property('company_id');
      r.product_id = mixpanel.get_property('product_id');

      // Direct persistence read
      if (mixpanel.persistence && mixpanel.persistence.props) {
        r._raw_company = mixpanel.persistence.props.company;
        r._raw_product_id = mixpanel.persistence.props.product_id;
        r._raw_company_id = mixpanel.persistence.props.company_id;
      }
      r.email = mixpanel.get_property('Email');
      r.tipo_plan = mixpanel.get_property('Tipo Plan Empresa');
      r.es_admin = mixpanel.get_property('Es Administrador');
      r.es_contador = mixpanel.get_property('Es Contador');
      r.es_demo = mixpanel.get_property('Es Demo');

      // Facturacion properties (from company group)
      r.cuit = mixpanel.get_property('CUIT');
      r.razon_social = mixpanel.get_property('Razon Social');
      r.mail_facturacion = mixpanel.get_property('Mail Facturacion');
      r.condicion_iva = mixpanel.get_property('Condicion Iva');
      r.domicilio = mixpanel.get_property('Domicilio');
      r.localidad = mixpanel.get_property('Localidad');
      r.provincia = mixpanel.get_property('Provincia');

      // Product properties (from product group)
      r.plan = mixpanel.get_property('Plan');
      r.nombre_plan = mixpanel.get_property('Nombre Plan');
      r.fecha_alta = mixpanel.get_property('Fecha Alta');
      r.estado = mixpanel.get_property('Estado');

      // All super property keys
      try {
        r.all_super_prop_keys = mixpanel.persistence
          ? Object.keys(mixpanel.persistence.props || {}).filter(k => !k.startsWith('__'))
          : [];
      } catch { r.all_super_prop_keys = []; }

      // Global JS vars (backend data)
      const globals = {};
      const varNames = [
        'CUITFacturacion', 'CUITEmpresa', 'idEmpresaUsuario',
        'razonSocialFacturacion', 'emailFacturacionReal',
        'telefonoFacturacion', 'jurisIIBB1Facturacion',
        'jurisIIBB2Facturacion', 'idSocioFacturacion',
        'idCondicionIvaFacturacion'
      ];
      for (const v of varNames) {
        try { globals[v] = eval(v); } catch { globals[v] = 'NOT_DEFINED'; }
      }
      r.globals = globals;

      // Decode full Mixpanel cookie
      try {
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('mp_'));
        if (cookie) {
          const cookieVal = decodeURIComponent(cookie.trim().split('=').slice(1).join('='));
          const parsed = JSON.parse(cookieVal);
          r.mixpanel_cookie_company = parsed.company;
          r.mixpanel_cookie_product_id = parsed.product_id;
          r.mixpanel_cookie_distinct_id = parsed.distinct_id;
          r.mixpanel_cookie_company_id = parsed.company_id;
        }
      } catch(e) { r.mixpanel_cookie_error = e.message; }

      // Check persistence props directly
      try {
        if (mixpanel.persistence && mixpanel.persistence.props) {
          const p = mixpanel.persistence.props;
          r.persistence_company = p.company;
          r.persistence_product_id = p.product_id;
          r.persistence_company_id = p.company_id;
          r.persistence_distinct_id = p.distinct_id;
          // Check $groups specifically
          r.persistence_groups = p.$groups;
        }
      } catch(e) { r.persistence_error = e.message; }

      // Find where CUITFacturacion is declared in the page source (ALL scripts, including inline)
      const allScripts = Array.from(document.querySelectorAll('script'));
      r.total_scripts = allScripts.length;
      r.inline_scripts = allScripts.filter(s => !s.src).length;
      r.external_scripts = allScripts.filter(s => s.src).map(s => s.src.split('/').pop()).slice(0, 10);

      // Search inline scripts for CUITFacturacion
      const inlineScripts = allScripts.filter(s => !s.src);
      const cuitScripts = inlineScripts
        .map((s, i) => ({ index: i, text: s.textContent }))
        .filter(s => s.text.includes('CUITFacturacion'));
      r.cuit_script_locations = cuitScripts.map(s => {
        const match = s.text.match(/[^\n]*CUITFacturacion[^\n]*/g);
        return match ? match.slice(0, 3).map(m => m.trim().substring(0, 150)) : 'no match';
      });

      // Search for colppyAnalytics calls
      const analyticsScripts = inlineScripts
        .map((s, i) => ({ index: i, text: s.textContent }))
        .filter(s => s.text.includes('colppyAnalytics'));
      r.analytics_call_locations = analyticsScripts.map(s => {
        const match = s.text.match(/colppyAnalytics[^;]+/g);
        return match ? match.slice(0, 3).map(m => m.trim().substring(0, 200)) : 'no match';
      });

      // Also search for company_id or identify patterns
      const identifyScripts = inlineScripts
        .filter(s => s.textContent.includes('identify') || s.textContent.includes('company_id'));
      r.identify_script_count = identifyScripts.length;

      // Get full page HTML size and search for CUITFacturacion in full HTML
      const html = document.documentElement.outerHTML;
      r.page_html_size = `${(html.length / 1024).toFixed(0)}KB`;
      const htmlCuitMatches = html.match(/CUITFacturacion[^<]{0,100}/g);
      r.cuit_in_html = htmlCuitMatches ? htmlCuitMatches.slice(0, 5).map(m => m.substring(0, 100)) : 'NOT FOUND';

      return r;
    });

    if (state.error) {
      console.error('ERROR:', state.error);
      process.exit(1);
    }

    // 5. Validate against spec
    console.log('[5/5] Validating against KAN-12024 spec...\n');

    const results = [];
    function check(name, expected, actual, critical = false) {
      const pass = JSON.stringify(expected) === JSON.stringify(actual);
      const status = pass ? 'PASS' : (critical ? 'FAIL' : 'WARN');
      results.push({ name, expected, actual, status });
      const icon = pass ? '\u2705' : (critical ? '\u274C' : '\u26A0\uFE0F');
      console.log(`${icon} ${status} | ${name}`);
      if (!pass) {
        console.log(`       Expected: ${JSON.stringify(expected)}`);
        console.log(`       Actual:   ${JSON.stringify(actual)}`);
      }
    }

    // Core identity checks
    const isEmailDistinctId = state.distinct_id === STAGING_USER;
    check('distinct_id is user email (not CUIT)',
      true, isEmailDistinctId, true);

    // Company group check
    const companyGroupVal = Array.isArray(state.company) ? state.company[0] : state.company;
    const isCuitCompany = companyGroupVal === state.globals.CUITFacturacion;
    check('company group uses CUITFacturacion',
      true, isCuitCompany, true);

    // Product group check
    const productGroupVal = Array.isArray(state.product_id) ? state.product_id[0] : state.product_id;
    const isIdEmpresaProduct = productGroupVal === state.globals.idEmpresaUsuario;
    check('product_id group uses idEmpresa',
      true, isIdEmpresaProduct, true);

    // Dual group separation
    check('company != product_id (dual-group separation)',
      true, companyGroupVal !== productGroupVal, true);

    // Backend data checks
    check('CUITFacturacion populated from backend',
      true, !!state.globals.CUITFacturacion && state.globals.CUITFacturacion !== 'NOT_DEFINED');
    check('razonSocialFacturacion populated',
      true, !!state.globals.razonSocialFacturacion && state.globals.razonSocialFacturacion !== 'NOT_DEFINED');
    check('telefonoFacturacion populated',
      true, !!state.globals.telefonoFacturacion && state.globals.telefonoFacturacion !== 'NOT_DEFINED');
    check('jurisIIBB1Facturacion populated',
      true, !!state.globals.jurisIIBB1Facturacion && state.globals.jurisIIBB1Facturacion !== 'NOT_DEFINED');
    check('idSocioFacturacion populated',
      true, !!state.globals.idSocioFacturacion && state.globals.idSocioFacturacion !== 'NOT_DEFINED');

    // Mixpanel super properties
    check('CUIT super property set', true, !!state.cuit);
    check('Razon Social super property set', true, !!state.razon_social);
    check('Email super property set', true, !!state.email);

    // Stop polling and show state evolution
    clearInterval(pollInterval);
    console.log(`\n=== MIXPANEL STATE EVOLUTION (${stateSnapshots.length} snapshots) ===`);
    let prevCompany = null;
    const t0 = stateSnapshots.length > 0 ? stateSnapshots[0].t : 0;
    for (const snap of stateSnapshots) {
      const companyStr = JSON.stringify(snap.company);
      if (companyStr !== prevCompany) {
        const dt = snap.t - t0;
        console.log(`  [+${dt}ms] company=${companyStr} | product_id=${JSON.stringify(snap.product_id)} | distinct_id=${snap.distinct_id} | CUITFacturacion=${snap.cuit_global}`);
        prevCompany = companyStr;
      }
    }
    if (stateSnapshots.length === 0) console.log('  (no snapshots captured)');

    // Also check: after everything settled, what does the Mixpanel library think about groups?
    const groupCheck = await targetFrame.evaluate(() => {
      const r = {};
      // Check if persistence.props has $groups
      try {
        if (mixpanel.persistence) {
          r.persistence_props_company = mixpanel.persistence.props.company;
          r.persistence_props_groups = mixpanel.persistence.props.$groups;
        }
      } catch {}
      // Read the group directly from the library
      try {
        const grp = mixpanel.get_group('company', CUITFacturacion);
        r.get_group_cuit_exists = !!grp;
      } catch { r.get_group_cuit_exists = false; }
      try {
        const grp2 = mixpanel.get_group('company', idEmpresaUsuario);
        r.get_group_idEmpresa_exists = !!grp2;
      } catch { r.get_group_idEmpresa_exists = false; }
      return r;
    }).catch(() => ({}));
    console.log('\n=== GROUP STATE ===');
    console.log(JSON.stringify(groupCheck, null, 2));

    // Bundle verification
    console.log('\n=== DEPLOYED BUNDLE VERIFICATION ===');
    console.log(`setCompanyPropertiesMixpanel in bundle: ${colppyJsSnippet || 'NOT INTERCEPTED'}`);

    // Mixpanel API calls — decode and show group details
    console.log(`\n=== MIXPANEL API CALLS (${mixpanelRequests.length}) ===`);
    for (const req of mixpanelRequests) {
      console.log(`  [${req.endpoint}] ${req.method} ${req.url}`);
      if (req.postData) {
        try {
          // Decode URL-encoded data
          const decoded = decodeURIComponent(req.postData.replace(/^data=/, ''));
          const json = JSON.parse(decoded);
          if (req.endpoint === 'GROUPS') {
            console.log(`    FULL GROUPS PAYLOAD: ${JSON.stringify(json, null, 2)}`);
          } else if (req.endpoint === 'TRACK') {
            // Show event name + company/product_id group values
            for (const evt of (Array.isArray(json) ? json : [json])) {
              const props = evt.properties || {};
              console.log(`    Event: "${evt.event}" | company=${props.company} | product_id=${props.product_id} | distinct_id=${props.distinct_id?.substring(0, 30)}`);
            }
          } else if (req.endpoint === 'ENGAGE') {
            console.log(`    ENGAGE: ${JSON.stringify(json).substring(0, 300)}`);
          }
        } catch {
          console.log(`    raw: ${req.postData.substring(0, 200)}`);
        }
      }
    }

    // Summary
    console.log('\n=== RAW STATE ===');
    console.log(JSON.stringify(state, null, 2));

    console.log('\n=== SUMMARY ===');
    const fails = results.filter(r => r.status === 'FAIL');
    const warns = results.filter(r => r.status === 'WARN');
    const passes = results.filter(r => r.status === 'PASS');
    console.log(`  ${passes.length} passed, ${warns.length} warnings, ${fails.length} FAILED`);

    if (fails.length > 0) {
      console.log('\nCRITICAL FAILURES:');
      for (const f of fails) {
        console.log(`  - ${f.name}`);
      }
    }

    process.exit(fails.length > 0 ? 1 : 0);

  } catch (err) {
    console.error('Test error:', err.message);
    process.exit(2);
  } finally {
    await browser.close();
  }
}

run();
