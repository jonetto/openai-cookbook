#!/usr/bin/env node

/**
 * Feature Upvote Playwright MCP Server (Colppy Customer Success plugin)
 *
 * Browser-automation implementation for Feature Upvote using Playwright.
 *
 * Pattern mirrors bank-feed style:
 * - cache-first reads
 * - force_refresh bypass
 * - live Playwright fetch/update cache
 * - structured fallback errors
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';

import { chromium } from 'playwright';
import { existsSync } from 'fs';
import fs from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import dotenv from 'dotenv';

import { FEATURE_UPVOTE_PLAYWRIGHT_TOOL_DEFINITIONS } from './feature-upvote-playwright-tool-definitions.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CACHE_DIR = join(__dirname, '.cache', 'feature-upvote');
const DEFAULT_SIGNIN_URL = 'https://app.featureupvote.com/signin';
const DEFAULT_BOARD_URL = 'https://ideas.colppy.com';
const DEFAULT_DASHBOARD_HOME = 'https://app.featureupvote.com/dashboard/';
const DEFAULT_USER_AGENT =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36';
const DEFAULT_STORAGE_STATE_PATH = join(CACHE_DIR, 'feature-upvote-storage-state.json');

const STATUS_SLUGS = [
  'awaiting_moderation',
  'under_review',
  'planned',
  'not_planned',
  'done',
  'deleted',
  'spam',
  'all',
];

for (const envPath of [
  join(__dirname, '../../../.env'),
  join(__dirname, '../../.env'),
  join(process.cwd(), '.env'),
]) {
  dotenv.config({ path: envPath });
}

function nowIso() {
  return new Date().toISOString();
}

function toBool(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return String(value).toLowerCase() === 'true';
}

function parseCount(raw) {
  const digits = String(raw || '').replace(/[^\d]/g, '');
  return digits ? Number.parseInt(digits, 10) : 0;
}

function normalizeText(raw) {
  return String(raw || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function slugFromStatusLabel(label) {
  const v = normalizeText(label);
  if (v.includes('esperando moderacion')) return 'awaiting_moderation';
  if (v.includes('en consideracion')) return 'under_review';
  if (v.includes('planeado')) return 'planned';
  if (v.includes('no planeado')) return 'not_planned';
  if (v.includes('hecho')) return 'done';
  if (v.includes('eliminado')) return 'deleted';
  if (v.includes('spam')) return 'spam';
  if (v.startsWith('all') || v.startsWith('todos')) return 'all';
  return 'unknown';
}

function slugFromStatusCode(code) {
  const v = normalizeText(code);
  if (v === 'awaitingapproval') return 'awaiting_moderation';
  if (v === 'underreview') return 'under_review';
  if (v === 'planned') return 'planned';
  if (v === 'notplanned') return 'not_planned';
  if (v === 'done') return 'done';
  if (v === 'deleted') return 'deleted';
  if (v === 'spam') return 'spam';
  return 'unknown';
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
    if (!row || row.every((v) => String(v || '').trim() === '')) continue;
    const obj = {};
    for (let j = 0; j < headers.length; j += 1) {
      obj[headers[j]] = row[j] ?? '';
    }
    records.push(obj);
  }
  return records;
}

function cacheFileName(key) {
  return `${Buffer.from(key).toString('base64url')}.json`;
}

async function ensureCacheDir() {
  if (!existsSync(CACHE_DIR)) {
    await fs.mkdir(CACHE_DIR, { recursive: true });
  }
}

async function readCache(key) {
  try {
    await ensureCacheDir();
    const path = join(CACHE_DIR, cacheFileName(key));
    const raw = await fs.readFile(path, 'utf8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function writeCache(key, payload) {
  await ensureCacheDir();
  const path = join(CACHE_DIR, cacheFileName(key));
  await fs.writeFile(path, JSON.stringify(payload, null, 2), 'utf8');
}

function isCacheFresh(cached, ttlMinutes) {
  if (!cached?.fetched_at) return false;
  const ageMs = Date.now() - new Date(cached.fetched_at).getTime();
  return ageMs <= ttlMinutes * 60 * 1000;
}

function buildMeta(source, count, extra = {}) {
  return {
    source,
    count,
    fetched_at: nowIso(),
    ...extra,
  };
}

class FeatureUpvotePlaywrightMCPServer {
  constructor() {
    this.server = new Server(
      { name: 'feature-upvote-playwright-server', version: '1.0.0' },
      { capabilities: { tools: {} } },
    );
    this.setupErrorHandling();
    this.setupToolHandlers();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => console.error('[Feature Upvote Playwright MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  _env(name, fallback = '') {
    return process.env[name] || fallback;
  }

  _cacheTtlMinutes() {
    const raw = this._env('FEATURE_UPVOTE_CACHE_TTL_MINUTES', '30');
    const value = Number.parseInt(raw, 10);
    return Number.isNaN(value) ? 30 : Math.max(1, value);
  }

  _credentials() {
    const email = this._env('FEATURE_UPVOTE_EMAIL') || this._env('FEATURE_UPVOTE_USER');
    const password = this._env('FEATURE_UPVOTE_PASSWORD') || this._env('FEATURE_UPVOTE_PASS');
    if (!email || !password) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Missing Feature Upvote credentials. Set FEATURE_UPVOTE_EMAIL and FEATURE_UPVOTE_PASSWORD.',
      );
    }
    return { email, password };
  }

  _signinUrl() {
    return this._env('FEATURE_UPVOTE_SIGNIN_URL', DEFAULT_SIGNIN_URL);
  }

  _dashboardHomeUrl() {
    return this._env('FEATURE_UPVOTE_DASHBOARD_URL', DEFAULT_DASHBOARD_HOME);
  }

  _defaultBoardUrl() {
    return this._env('FEATURE_UPVOTE_BOARD_URL', DEFAULT_BOARD_URL);
  }

  _storageStatePath() {
    return this._env('FEATURE_UPVOTE_STORAGE_STATE_PATH', DEFAULT_STORAGE_STATE_PATH);
  }

  _launchOptions() {
    const headless = toBool(this._env('FEATURE_UPVOTE_HEADLESS', 'true'), true);
    return {
      headless,
      args: headless
        ? ['--disable-blink-features=AutomationControlled']
        : [],
    };
  }

  _contextOptions() {
    const options = {
      viewport: { width: 1440, height: 900 },
      userAgent: this._env('FEATURE_UPVOTE_USER_AGENT', DEFAULT_USER_AGENT),
      locale: this._env('FEATURE_UPVOTE_LOCALE', 'en-US'),
      timezoneId: this._env('FEATURE_UPVOTE_TIMEZONE', 'America/Argentina/Buenos_Aires'),
    };
    const storageStatePath = this._storageStatePath();
    if (existsSync(storageStatePath)) {
      options.storageState = storageStatePath;
    }
    return options;
  }

  async _persistStorageState(context) {
    await ensureCacheDir();
    await context.storageState({ path: this._storageStatePath() });
  }

  async _waitForCloudflareClear(page, maxWaitMs = 25000) {
    const started = Date.now();
    while (Date.now() - started < maxWaitMs) {
      const title = await page.title();
      if (!/just a moment/i.test(title)) return true;
      await page.waitForTimeout(1000);
    }
    return false;
  }

  async _gotoRobust(page, url, timeoutMs = 60000, retries = 2) {
    let lastError = null;
    for (let attempt = 1; attempt <= retries; attempt += 1) {
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: timeoutMs });
        await this._waitForCloudflareClear(page, 30000);
        return;
      } catch (error) {
        lastError = error;
        if (attempt < retries) {
          await page.waitForTimeout(1200);
          continue;
        }
      }
    }
    throw lastError;
  }

  async _withBrowser(task) {
    const browser = await chromium.launch(this._launchOptions());
    const context = await browser.newContext(this._contextOptions());
    const page = await context.newPage();
    page.setDefaultTimeout(45000);
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });
    try {
      const result = await task({ browser, context, page });
      if (toBool(this._env('FEATURE_UPVOTE_PERSIST_STORAGE_STATE', 'true'), true)) {
        await this._persistStorageState(context);
      }
      return result;
    } finally {
      await browser.close();
    }
  }

  async _firstAvailableLocator(candidates) {
    for (const locator of candidates) {
      try {
        if ((await locator.count()) > 0) {
          const first = locator.first();
          if (await first.isVisible({ timeout: 500 })) {
            return first;
          }
        }
      } catch {
        // Ignore invalid/unsupported selectors and keep trying.
      }
    }
    return null;
  }

  async _waitForSignInForm(page, maxWaitMs = 25000) {
    const start = Date.now();
    while (Date.now() - start < maxWaitMs) {
      const emailCount = await page.locator('input[type="email"], input[name*="email" i], input[id*="email" i]').count();
      const passwordCount = await page.locator('input[type="password"], input[name*="password" i], input[id*="password" i]').count();
      if (emailCount > 0 && passwordCount > 0) return true;
      await this._waitForCloudflareClear(page, 2000);
      await page.waitForTimeout(400);
    }
    return false;
  }

  async _login(page) {
    const { email, password } = this._credentials();
    await this._gotoRobust(page, this._dashboardHomeUrl(), 60000, 2);

    if (/\/dashboard\/?/.test(page.url()) && !/\/signin/.test(page.url())) {
      return;
    }

    await this._gotoRobust(page, this._signinUrl(), 60000, 2);
    const cloudflareCleared = await this._waitForCloudflareClear(page, 30000);
    if (!cloudflareCleared) {
      throw new Error(
        'Feature Upvote returned persistent Cloudflare challenge. Run one bootstrap with FEATURE_UPVOTE_HEADLESS=false, then retry headless.',
      );
    }
    const signInFormReady = await this._waitForSignInForm(page, 30000);
    if (!signInFormReady) {
      throw new Error('Sign-in form not available after challenge checks.');
    }

    const emailInput = await this._firstAvailableLocator([
      page.locator('input[type="email"]'),
      page.locator('input[name*="email" i]'),
      page.locator('input[id*="email" i]'),
      page.locator('input[autocomplete="email"]'),
      page.getByLabel(/email/i),
      page.getByPlaceholder(/email/i),
      page.getByRole('textbox').filter({ hasText: /email/i }),
    ]);

    const passwordInput = await this._firstAvailableLocator([
      page.locator('input[type="password"]'),
      page.locator('input[name*="password" i]'),
      page.locator('input[id*="password" i]'),
      page.locator('input[autocomplete="current-password"]'),
      page.getByLabel(/password/i),
      page.getByPlaceholder(/password/i),
    ]);

    if (!emailInput || !passwordInput) {
      throw new Error('Unable to locate sign-in inputs for Feature Upvote.');
    }

    const submitButton = await this._firstAvailableLocator([
      page.getByRole('button', { name: /sign in|log in|dashboard|ingresar|iniciar/i }),
      page.locator('button[type="submit"]'),
      page.locator('input[type="submit"]'),
    ]);

    if (!submitButton) {
      throw new Error('Unable to locate sign-in submit button for Feature Upvote.');
    }

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      await emailInput.fill(email);
      await passwordInput.fill(password);
      await submitButton.click();

      try {
        await page.waitForURL(/\/dashboard\/?/, { timeout: 30000 });
        return;
      } catch {
        await this._waitForCloudflareClear(page, 12000);
      }
    }

    throw new Error('Sign-in failed after retries (still not on dashboard).');
  }

  async _extractBoardSummary(page) {
    await this._gotoRobust(page, this._dashboardHomeUrl(), 60000, 2);
    return await page.evaluate(() => {
      const parseCountLocal = (raw) => {
        const digits = String(raw || '').replace(/[^\d]/g, '');
        return digits ? Number.parseInt(digits, 10) : 0;
      };

      const rows = Array.from(document.querySelectorAll('table tbody tr')).filter((tr) =>
        tr.querySelector('a[href*="/dashboard/boards/"]'),
      );

      const boards = rows.map((row) => {
        const cells = row.querySelectorAll('td');
        const name = (cells[0]?.innerText || '').trim();
        const suggestionsText = (cells[1]?.innerText || '').trim();
        const commentsText = (cells[2]?.innerText || '').trim();
        const upvotesText = (cells[3]?.innerText || '').trim();
        const moderateLink = row.querySelector('a[href*="/dashboard/boards/"][href*="/suggestions"]');
        const settingsLink = row.querySelector('a[href*="/dashboard/boards/"][href*="/appearance"]');
        const liveLink = row.querySelector('a[href*="/viewlive/"]');

        const moderateHref = moderateLink ? new URL(moderateLink.getAttribute('href'), location.origin).toString() : null;
        const boardRefMatch = moderateHref?.match(/\/boards\/([^/]+)\//);
        const boardRef = boardRefMatch?.[1] || null;

        return {
          name,
          board_ref: boardRef,
          suggestions_total: parseCountLocal(suggestionsText),
          comments_total: parseCountLocal(commentsText),
          upvotes_total: parseCountLocal(upvotesText),
          suggestions_approval_pending: parseCountLocal(
            row.querySelector('a[href*="/dashboard/boards/"][href*="/suggestions"]')?.innerText || '',
          ),
          comments_approval_pending: parseCountLocal(
            row.querySelector('a[href*="/dashboard/boards/"][href*="/comments"]')?.innerText || '',
          ),
          moderate_url: moderateHref,
          settings_url: settingsLink ? new URL(settingsLink.getAttribute('href'), location.origin).toString() : null,
          live_url: liveLink ? new URL(liveLink.getAttribute('href'), location.origin).toString() : null,
        };
      });

      return {
        boards,
        dashboard_url: location.href,
      };
    });
  }

  async _resolveBoardRef(page, requestedBoardRef = null) {
    const summary = await this._extractBoardSummary(page);
    if (!summary.boards?.length) {
      throw new Error('No Feature Upvote boards found in dashboard.');
    }
    if (requestedBoardRef) {
      const matched = summary.boards.find((b) => b.board_ref === requestedBoardRef);
      if (!matched) {
        throw new Error(`Board ref not found in dashboard: ${requestedBoardRef}`);
      }
      return { boardRef: requestedBoardRef, boardSummary: matched, allBoards: summary.boards };
    }
    return {
      boardRef: summary.boards[0].board_ref,
      boardSummary: summary.boards[0],
      allBoards: summary.boards,
    };
  }

  async _readStatusOptions(page) {
    return await page.evaluate(() => {
      const statusSelect = Array.from(document.querySelectorAll('select')).find((select) =>
        Array.from(select.options || []).some((opt) => /esperando moderaci/i.test(opt.textContent || '')),
      );

      if (!statusSelect) return { options: [], selected: null };

      const options = Array.from(statusSelect.options).map((opt) => {
        const label = (opt.textContent || '').trim();
        const v = label
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase()
          .trim();
        let slug = 'unknown';
        if (v.includes('esperando moderacion')) slug = 'awaiting_moderation';
        else if (v.includes('en consideracion')) slug = 'under_review';
        else if (v.includes('planeado')) slug = 'planned';
        else if (v.includes('no planeado')) slug = 'not_planned';
        else if (v.includes('hecho')) slug = 'done';
        else if (v.includes('eliminado')) slug = 'deleted';
        else if (v.includes('spam')) slug = 'spam';
        else if (v.startsWith('all') || v.startsWith('todos')) slug = 'all';

        return {
          value: opt.value,
          label,
          slug,
          selected: opt.selected,
        };
      });

      return {
        options,
        selected: options.find((x) => x.selected)?.slug || null,
      };
    });
  }

  async _extractModerationRowsAndNext(page) {
    return await page.evaluate(() => {
      const rows = [];
      const tableRows = Array.from(document.querySelectorAll('table tbody tr')).filter(
        (tr) => tr.querySelectorAll('td').length >= 7,
      );

      const clean = (v) => String(v || '').replace(/\s+/g, ' ').trim();
      const parseIntLoose = (v) => {
        const digits = String(v || '').replace(/[^\d]/g, '');
        return digits ? Number.parseInt(digits, 10) : 0;
      };

      for (const row of tableRows) {
        const cells = row.querySelectorAll('td');
        const titleCell = cells[1];
        const statusCell = cells[2];
        const votesCell = cells[3];
        const commentsCell = cells[4];
        const tagsCell = cells[5];
        const dateCell = cells[6];

        const titleLink = titleCell?.querySelector('a[href*="/suggestions/"]');
        const rawHref = titleLink ? titleLink.getAttribute('href') : null;
        const url = rawHref ? new URL(rawHref, location.origin).toString() : null;
        const suggestionMatch = decodeURIComponent(url || '').match(/\/suggestions\/(\d+)/);
        const suggestionId = suggestionMatch?.[1] || null;

        const title = clean(titleLink?.textContent || '');
        const cloned = titleCell?.cloneNode(true);
        if (cloned) {
          cloned.querySelectorAll('a,button,img,input,svg').forEach((el) => el.remove());
        }
        const textWithoutControls = clean(cloned?.textContent || '');
        const description = title && textWithoutControls.startsWith(title)
          ? clean(textWithoutControls.slice(title.length))
          : textWithoutControls;

        const tags = Array.from(tagsCell?.querySelectorAll('a') || [])
          .map((a) => clean(a.textContent).replace(/^#\s*/, ''))
          .filter(Boolean);

        const dateLines = clean(dateCell?.innerText || '')
          .split('\n')
          .map((x) => clean(x))
          .filter(Boolean);

        rows.push({
          suggestion_id: suggestionId ? Number.parseInt(suggestionId, 10) : null,
          title,
          description,
          status: clean(statusCell?.innerText || ''),
          status_slug: (() => {
            const v = clean(statusCell?.innerText || '')
              .normalize('NFD')
              .replace(/[\u0300-\u036f]/g, '')
              .toLowerCase();
            if (v.includes('esperando moderacion')) return 'awaiting_moderation';
            if (v.includes('en consideracion')) return 'under_review';
            if (v.includes('planeado')) return 'planned';
            if (v.includes('no planeado')) return 'not_planned';
            if (v.includes('hecho')) return 'done';
            if (v.includes('eliminado')) return 'deleted';
            if (v.includes('spam')) return 'spam';
            return 'unknown';
          })(),
          votes: parseIntLoose(votesCell?.innerText || ''),
          comments: parseIntLoose(commentsCell?.innerText || ''),
          tags,
          date: dateLines[0] || null,
          submitter_name: dateLines[1] || null,
          submitter_email: dateLines[2] || null,
          moderation_url: url,
        });
      }

      const currentPage = Number.parseInt(new URL(location.href).searchParams.get('page') || '1', 10);
      const pageLinks = Array.from(document.querySelectorAll('a[href*="page="]'))
        .map((a) => {
          const href = a.getAttribute('href');
          if (!href) return null;
          const abs = new URL(href, location.href).toString();
          const nextPage = Number.parseInt(new URL(abs).searchParams.get('page') || '1', 10);
          return { abs, nextPage };
        })
        .filter(Boolean)
        .filter((x) => x.nextPage > currentPage)
        .sort((a, b) => a.nextPage - b.nextPage);

      const nextUrl = pageLinks.length > 0 ? pageLinks[0].abs : null;
      const totalHint = clean(document.body.innerText).match(/(\d+-\d+\s+of\s+\d+)/i)?.[1] || null;

      return { rows, nextUrl, totalHint };
    });
  }

  async _downloadExportCsvFromPage(page) {
    const exportHref = await page.evaluate(() => {
      const link = Array.from(document.querySelectorAll('a[href]')).find((a) =>
        (a.getAttribute('href') || '').includes('suggestions_export'),
      );
      return link ? link.getAttribute('href') : null;
    });

    if (!exportHref) {
      throw new Error('Export CSV link not found on moderation page.');
    }

    const exportUrl = new URL(exportHref, page.url()).toString();
    const downloadPromise = page.waitForEvent('download', { timeout: 30000 });
    try {
      await page.goto(exportUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    } catch (error) {
      if (!String(error?.message || '').toLowerCase().includes('download is starting')) {
        throw error;
      }
    }

    const download = await downloadPromise;
    await ensureCacheDir();
    const tempPath = join(CACHE_DIR, `feature-upvote-export-${Date.now()}-${Math.random().toString(36).slice(2)}.csv`);
    await download.saveAs(tempPath);
    const csvText = await fs.readFile(tempPath, 'utf8');
    await fs.unlink(tempPath).catch(() => {});

    return { exportUrl, csvText };
  }

  _buildRequestsFromCsv({ csvText, limit, boardRef }) {
    const records = parseCsvRecords(csvText);

    const mapped = records.map((record) => {
      const suggestionIdRaw = record['suggestion id'] || '';
      const suggestionId = suggestionIdRaw ? Number.parseInt(String(suggestionIdRaw), 10) : null;
      const title = String(record['title'] || '').trim();
      const description = String(record['description'] || '').trim();
      const status = String(record['status'] || '').trim();
      const statusCode = String(record['status code'] || '').trim();
      const dateCreated = String(record['date created'] || '').trim();
      const tagsRaw = String(record['tags'] || '').trim();
      const tags = tagsRaw
        ? tagsRaw.split(',').map((x) => x.trim()).filter(Boolean)
        : [];

      return {
        suggestion_id: Number.isFinite(suggestionId) ? suggestionId : null,
        title,
        description,
        status,
        status_slug: slugFromStatusCode(statusCode) !== 'unknown'
          ? slugFromStatusCode(statusCode)
          : slugFromStatusLabel(status),
        votes: parseCount(record['votes'] || ''),
        comments: parseCount(record['comments'] || ''),
        tags,
        date: dateCreated ? dateCreated.slice(0, 10) : null,
        submitter_name: String(record['name'] || '').trim() || null,
        submitter_email: String(record['email'] || '').trim() || null,
        moderation_url: Number.isFinite(suggestionId)
          ? `https://app.featureupvote.com/viewlive/${boardRef}?redir=/suggestions/${suggestionId}`
          : null,
      };
    });

    return {
      totalRows: mapped.length,
      featureRequests: mapped.slice(0, limit),
    };
  }

  async _liveBoardSummary(args) {
    return this._withBrowser(async ({ page }) => {
      await this._login(page);
      const summary = await this._extractBoardSummary(page);
      const selected = args.board_ref
        ? summary.boards.find((b) => b.board_ref === args.board_ref)
        : summary.boards[0];
      if (!selected) {
        throw new Error(`Board ref not found: ${args.board_ref}`);
      }
      return {
        board: selected,
        boards: summary.boards,
        dashboard_url: summary.dashboard_url,
      };
    });
  }

  _buildModerationQueryUrl(base, statusId, query, tag) {
    const u = new URL(base);
    if (statusId) u.searchParams.set('status_id', statusId);
    if (query) u.searchParams.set('q', query);
    if (tag) u.searchParams.set('tag', tag);
    if (!u.searchParams.has('order')) u.searchParams.set('order', 'newest');
    if (!u.searchParams.has('minVotes')) u.searchParams.set('minVotes', '-1');
    if (!u.searchParams.has('maxVotes')) u.searchParams.set('maxVotes', '-1');
    return u.toString();
  }

  async _liveFeatureRequests(args) {
    return this._withBrowser(async ({ page }) => {
      await this._login(page);

      const { boardRef, boardSummary } = await this._resolveBoardRef(page, args.board_ref || null);
      const moderationUrl = `https://app.featureupvote.com/dashboard/boards/${boardRef}/suggestions`;
      await this._gotoRobust(page, moderationUrl, 60000, 2);

      const statusOptionsData = await this._readStatusOptions(page);
      const requestedStatus = STATUS_SLUGS.includes(args.status || '') ? (args.status || 'awaiting_moderation') : 'awaiting_moderation';
      const matchedStatusOption = statusOptionsData.options.find((opt) => opt.slug === requestedStatus);
      const statusValue = matchedStatusOption?.value || null;

      let pageUrl = this._buildModerationQueryUrl(page.url(), statusValue, args.query || '', args.tag || '');
      const useExportCsv = args.use_export_csv !== false;
      const maxPages = Number.isFinite(args.max_pages) ? Math.max(1, Math.min(30, args.max_pages)) : 5;
      const limit = Number.isFinite(args.limit) ? Math.max(1, Math.min(2000, args.limit)) : 200;

      if (useExportCsv) {
        try {
          await this._gotoRobust(page, pageUrl, 60000, 2);
          const { exportUrl, csvText } = await this._downloadExportCsvFromPage(page);
          const fromCsv = this._buildRequestsFromCsv({ csvText, limit, boardRef });

          return {
            board_ref: boardRef,
            board_name: boardSummary?.name || null,
            status_requested: requestedStatus,
            status_selected: matchedStatusOption?.slug || statusOptionsData.selected || null,
            status_options: statusOptionsData.options,
            query: args.query || '',
            tag: args.tag || '',
            total_returned: fromCsv.featureRequests.length,
            total_available: fromCsv.totalRows,
            max_pages: 0,
            limit,
            pages_crawled: [],
            export_csv: {
              used: true,
              url: exportUrl,
            },
            feature_requests: fromCsv.featureRequests,
          };
        } catch (error) {
          // Fall back to DOM pagination when CSV export is blocked/challenged.
        }
      }

      const allRows = [];
      const seenIds = new Set();
      const seenUrls = new Set();
      const pageSources = [];

      for (let pageCount = 0; pageCount < maxPages && pageUrl; pageCount += 1) {
        await this._gotoRobust(page, pageUrl, 60000, 2);
        const extracted = await this._extractModerationRowsAndNext(page);
        pageSources.push({ page: pageCount + 1, url: page.url(), total_hint: extracted.totalHint });

        for (const row of extracted.rows) {
          const key = row.suggestion_id ? `id:${row.suggestion_id}` : `url:${row.moderation_url || ''}`;
          if (seenIds.has(key) || seenUrls.has(row.moderation_url || '')) continue;
          seenIds.add(key);
          if (row.moderation_url) seenUrls.add(row.moderation_url);
          allRows.push(row);
          if (allRows.length >= limit) break;
        }

        if (allRows.length >= limit) break;
        pageUrl = extracted.nextUrl;
      }

      return {
        board_ref: boardRef,
        board_name: boardSummary?.name || null,
        status_requested: requestedStatus,
        status_selected: matchedStatusOption?.slug || statusOptionsData.selected || null,
        status_options: statusOptionsData.options,
        query: args.query || '',
        tag: args.tag || '',
        total_returned: allRows.length,
        max_pages: maxPages,
        limit,
        pages_crawled: pageSources,
        export_csv: { used: false },
        feature_requests: allRows,
      };
    });
  }

  async _liveCreateFeatureRequest(args) {
    const boardUrl = args.board_url || this._defaultBoardUrl();
    const contributorName = args.name || this._env('FEATURE_UPVOTE_DEFAULT_NAME') || this._env('FEATURE_UPVOTE_EMAIL');
    const contributorEmail = args.email || this._env('FEATURE_UPVOTE_DEFAULT_EMAIL') || this._env('FEATURE_UPVOTE_EMAIL');
    const consent = args.consent !== false;
    const dryRun = args.dry_run === true;

    return this._withBrowser(async ({ page }) => {
      const addUrl = new URL('/suggestions/add', boardUrl).toString();
      await this._gotoRobust(page, addUrl, 60000, 2);

      await page.getByRole('textbox', { name: 'Título' }).fill(args.title);
      if (args.description) {
        await page.getByRole('textbox', { name: 'Descripción' }).fill(args.description);
      }
      if (contributorName) {
        await page.getByRole('textbox', { name: 'Nombre' }).fill(contributorName);
      }
      if (contributorEmail) {
        await page.getByRole('textbox', { name: 'Email' }).fill(contributorEmail);
      }

      const consentCheckbox = page.getByRole('checkbox');
      if (consent) {
        const isChecked = await consentCheckbox.isChecked();
        if (!isChecked) await consentCheckbox.check();
      }

      if (dryRun) {
        return {
          dry_run: true,
          ready_to_submit: true,
          board_url: boardUrl,
          add_url: addUrl,
          title: args.title,
          description: args.description || '',
          name: contributorName || null,
          email: contributorEmail || null,
        };
      }

      await page.getByRole('button', { name: 'Publicar sugerencia' }).click();
      await page.waitForTimeout(2000);

      return {
        dry_run: false,
        board_url: boardUrl,
        submitted: true,
        final_url: page.url(),
      };
    });
  }

  _json(data) {
    return {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    };
  }

  async _cachedOrLive({ cacheKey, forceRefresh, liveFetcher }) {
    const ttl = this._cacheTtlMinutes();
    const cached = await readCache(cacheKey);
    if (!forceRefresh && cached && isCacheFresh(cached, ttl)) {
      return {
        ...cached.data,
        _meta: {
          ...cached.data?._meta,
          source: 'cache',
          cache_ttl_minutes: ttl,
          cache_fetched_at: cached.fetched_at,
        },
      };
    }

    const liveData = await liveFetcher();
    const payload = { fetched_at: nowIso(), data: liveData };
    await writeCache(cacheKey, payload);
    return {
      ...liveData,
      _meta: {
        ...liveData?._meta,
        source: 'live',
        cache_ttl_minutes: ttl,
      },
    };
  }

  async getBoardSummary(args = {}) {
    const cacheKey = `board_summary:${args.board_ref || 'first'}`;
    const forceRefresh = args.force_refresh === true;
    const data = await this._cachedOrLive({
      cacheKey,
      forceRefresh,
      liveFetcher: async () => {
        const result = await this._liveBoardSummary(args);
        return {
          success: true,
          board: result.board,
          boards: result.boards,
          dashboard_url: result.dashboard_url,
          _meta: buildMeta('live', result.boards.length, {
            board_ref: result.board?.board_ref || null,
          }),
        };
      },
    });
    return this._json(data);
  }

  async listFeatureRequests(args = {}) {
    const status = STATUS_SLUGS.includes(args.status) ? args.status : 'awaiting_moderation';
    const maxPages = Number.isFinite(args.max_pages) ? Math.max(1, Math.min(30, args.max_pages)) : 5;
    const limit = Number.isFinite(args.limit) ? Math.max(1, Math.min(2000, args.limit)) : 200;
    const forceRefresh = args.force_refresh === true;

    const cacheKey = [
      'feature_requests',
      args.board_ref || 'first',
      status,
      args.tag || '',
      args.query || '',
      maxPages,
      limit,
    ].join(':');

    const data = await this._cachedOrLive({
      cacheKey,
      forceRefresh,
      liveFetcher: async () => {
        const result = await this._liveFeatureRequests({
          ...args,
          status,
          max_pages: maxPages,
          limit,
        });
        return {
          success: true,
          ...result,
          _meta: buildMeta('live', result.total_returned, {
            board_ref: result.board_ref,
            status: result.status_selected,
          }),
        };
      },
    });
    return this._json(data);
  }

  async createFeatureRequest(args = {}) {
    const result = await this._liveCreateFeatureRequest(args);
    return this._json({
      success: true,
      ...result,
      _meta: buildMeta('live', 1),
    });
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: FEATURE_UPVOTE_PLAYWRIGHT_TOOL_DEFINITIONS,
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      try {
        switch (name) {
          case 'get_feature_upvote_board_summary':
            return await this.getBoardSummary(args || {});
          case 'list_feature_requests':
            return await this.listFeatureRequests(args || {});
          case 'create_feature_request':
            return await this.createFeatureRequest(args || {});
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        if (error instanceof McpError) throw error;
        throw new McpError(ErrorCode.InternalError, `Feature Upvote Playwright failed: ${error.message}`);
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Feature Upvote Playwright MCP server running on stdio');
  }
}

export { FeatureUpvotePlaywrightMCPServer };

const isDirectRun =
  process.argv[1] && fileURLToPath(import.meta.url).endsWith(process.argv[1].replace(/^.*[\\/]/, ''));

if (isDirectRun) {
  const server = new FeatureUpvotePlaywrightMCPServer();
  server.run().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
