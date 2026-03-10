/**
 * Shared Intercom API helpers used by the MCP server and other tools.
 * Provides: retry logic, conversation fetching, text extraction, CSV conversion.
 */

export function toUnixBoundary(dateStr, endOfDay = false) {
  if (!dateStr) return null;
  const iso = `${dateStr}${endOfDay ? 'T23:59:59Z' : 'T00:00:00Z'}`;
  const ms = Date.parse(iso);
  if (Number.isNaN(ms)) {
    throw new Error(`Invalid date: ${dateStr}`);
  }
  return Math.floor(ms / 1000);
}

/**
 * Retry wrapper with exponential backoff and 429 rate-limit handling.
 * @param {Function} fn - async function to execute
 * @param {number} maxRetries - max retry attempts (default 3)
 * @param {number} delay - base delay in ms (default 750)
 */
export async function retryableRequest(fn, maxRetries = 3, delay = 750) {
  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt < maxRetries) {
        if (error.response && error.response.status === 429) {
          const retryAfter = parseInt(error.response.headers['retry-after'] || '5', 10);
          const waitTime = retryAfter * 1000 || Math.min(delay * Math.pow(2, attempt), 30000);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        } else {
          const waitTime = delay * Math.pow(1.5, attempt - 1);
          await new Promise(resolve => setTimeout(resolve, waitTime));
        }
      }
    }
  }
  throw lastError;
}

/**
 * Fetch conversation IDs for a date range using the Intercom Search API.
 * @param {object} intercomApi - axios instance configured for Intercom
 * @param {string} fromDate - YYYY-MM-DD
 * @param {string} toDate - YYYY-MM-DD
 * @param {number|null} limit - max IDs to return (null = all)
 * @param {string|null} state - optional: 'open', 'closed', 'snoozed'
 * @param {string|null} teamAssigneeId - optional: team inbox ID (e.g. 2334166 for "Primeros 90 días")
 */
export async function fetchConversationIds(intercomApi, fromDate, toDate, limit = null, state = null, teamAssigneeId = null) {
  const fromTimestamp = toUnixBoundary(fromDate, false);
  const toTimestamp = toUnixBoundary(toDate, true);
  const queryValues = [
    { field: 'created_at', operator: '>=', value: fromTimestamp },
    { field: 'created_at', operator: '<=', value: toTimestamp },
  ];
  if (state) queryValues.push({ field: 'state', operator: '=', value: state });
  if (teamAssigneeId) queryValues.push({ field: 'team_assignee_id', operator: '=', value: String(teamAssigneeId) });

  const allIds = [];
  let hasMore = true;
  const maxPerPage = 150;
  let startingAfter = null;

  while (hasMore && (limit === null || allIds.length < limit)) {
    const searchQuery = {
      query: {
        operator: 'AND',
        value: queryValues,
      },
      pagination: {
        per_page: Math.min(maxPerPage, limit ? limit - allIds.length : maxPerPage),
      },
    };
    if (startingAfter) searchQuery.pagination.starting_after = startingAfter;

    const response = await retryableRequest(async () => {
      return await intercomApi.post('/conversations/search', searchQuery);
    });
    const conversations = response.data.conversations || [];
    if (conversations.length === 0) break;

    allIds.push(...conversations.map(c => c.id));

    const next = response.data.pages?.next?.starting_after;
    if (!next) break;
    startingAfter = next;
    if (limit && allIds.length >= limit) break;
  }
  return allIds.slice(0, limit || allIds.length);
}

/**
 * Fetch full conversation details by ID.
 * @param {object} intercomApi - axios instance
 * @param {string} conversationId
 */
export async function getConversationDetails(intercomApi, conversationId) {
  return await retryableRequest(async () => {
    const response = await intercomApi.get(`/conversations/${conversationId}`);
    return response.data;
  });
}

/**
 * Fetch contact details by ID. Returns custom_attributes (e.g. es_contador from HubSpot sync).
 * Intercom user/contact level is synced with HubSpot contact level.
 * @param {object} intercomApi - axios instance
 * @param {string} contactId - Intercom contact/lead ID
 */
export async function getContactDetails(intercomApi, contactId) {
  if (!contactId) return null;
  try {
    const response = await retryableRequest(async () => {
      return await intercomApi.get(`/contacts/${contactId}`);
    });
    return response.data;
  } catch (e) {
    return null;
  }
}

/**
 * Remove HTML tags and decode entities from a string.
 */
export function stripHtml(html) {
  if (!html || typeof html !== 'string') return '';
  let text = html.replace(/<[^>]+>/g, ' ');
  text = text.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
  text = text.replace(/&quot;/g, '"').replace(/&#039;/g, "'").replace(/&nbsp;/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

/**
 * Extract tag names from a conversation object.
 * @param {object} conversation - Intercom conversation
 * @returns {string[]} tag names
 */
export function extractTags(conversation) {
  const t = conversation.tags;
  let tagList = [];
  if (t && typeof t === 'object' && !Array.isArray(t)) {
    tagList = t.tags || [];
  } else if (Array.isArray(t)) {
    tagList = t;
  }
  return tagList
    .map(tag => (typeof tag === 'object' ? tag.name : String(tag)))
    .filter(Boolean)
    .map(n => n.trim());
}

/**
 * Build a plain-text representation of the full conversation (source + parts).
 * Returns { fullText, parts } where parts is an array of { author_type, body, created_at }.
 */
export function buildConversationText(conversation) {
  const parts = [];
  if (conversation.source) {
    const body = stripHtml(conversation.source.body || '');
    const authorType = conversation.source.author?.type || 'unknown';
    parts.push({ author_type: authorType, body, created_at: conversation.created_at });
  }
  const cpList = conversation.conversation_parts?.conversation_parts || [];
  for (const p of cpList) {
    const body = stripHtml(p.body || '');
    if (!body) continue;
    const authorType = p.author?.type || 'unknown';
    parts.push({ author_type: authorType, body, created_at: p.created_at });
  }
  const fullText = parts.map(p => p.body).join(' ');
  return { fullText, parts };
}

/**
 * Process a conversation into structured row data (for CSV export).
 */
export function processConversation(conversation, includeContent = true) {
  if (!conversation) return [];
  const conversationId = conversation.id;
  const createdAt = conversation.created_at ? new Date(conversation.created_at * 1000).toISOString() : '';
  const updatedAt = conversation.updated_at ? new Date(conversation.updated_at * 1000).toISOString() : '';
  const state = conversation.state || '';
  const read = conversation.read !== undefined ? conversation.read.toString() : '';

  let ownerName = '';
  if (conversation.admin_assignee_id && conversation.teammates?.admins) {
    const admin = conversation.teammates.admins.find(a => a.id === conversation.admin_assignee_id.toString());
    if (admin?.name) ownerName = admin.name;
  }

  let userId = '';
  let companyId = '';
  if (conversation.contacts?.contacts?.length > 0) {
    const contact = conversation.contacts.contacts[0];
    userId = contact.id || '';
    if (contact.companies?.length > 0) companyId = contact.companies[0].id;
  }

  const rows = [];
  if (conversation.source) {
    rows.push({
      conversation_id: conversationId, created_at: createdAt, updated_at: updatedAt,
      message_id: conversation.source.id || '',
      message_body: includeContent ? (conversation.source.body || '') : '[CONTENT_HIDDEN]',
      part_type: 'conversation',
      author_type: conversation.source.author?.type || '',
      author_id: conversation.source.author?.id || '',
      author_name: conversation.source.author?.name || '',
      owner_name: ownerName, user_id: userId, company_id: companyId, state, read,
    });
  }
  const cpList = conversation.conversation_parts?.conversation_parts || [];
  for (const part of cpList) {
    rows.push({
      conversation_id: conversationId,
      created_at: part.created_at ? new Date(part.created_at * 1000).toISOString() : '',
      updated_at: part.updated_at ? new Date(part.updated_at * 1000).toISOString() : '',
      message_id: part.id || '',
      message_body: includeContent ? (part.body || '') : '[CONTENT_HIDDEN]',
      part_type: part.part_type || 'comment',
      author_type: part.author?.type || '',
      author_id: part.author?.id || '',
      author_name: part.author?.name || '',
      owner_name: ownerName, user_id: userId, company_id: companyId, state, read,
    });
  }
  return rows;
}

/** Convert array of row objects to CSV string. */
export function convertToCSV(rows) {
  if (rows.length === 0) return '';
  const headers = Object.keys(rows[0]);
  const csvRows = [
    headers.map(h => `"${h}"`).join(','),
    ...rows.map(row =>
      headers.map(h => `"${String(row[h] || '').replace(/"/g, '""')}"`).join(',')
    ),
  ];
  return csvRows.join('\n');
}

/** Group array items by a property, returning { key: count }. */
export function groupBy(array, property) {
  return array.reduce((groups, item) => {
    const key = item[property];
    groups[key] = (groups[key] || 0) + 1;
    return groups;
  }, {});
}

/**
 * Build the Intercom Search API query body for date range + state + team filters.
 * @param {object} opts - { from_date, to_date, state, team_assignee_id, per_page }
 */
export function buildSearchQuery({ from_date, to_date, state, team_assignee_id, per_page = 150 }) {
  const q = { query: { operator: 'AND', value: [] }, pagination: { per_page } };
  if (from_date) {
    q.query.value.push({ field: 'created_at', operator: '>=', value: toUnixBoundary(from_date, false) });
  }
  if (to_date) {
    q.query.value.push({ field: 'created_at', operator: '<=', value: toUnixBoundary(to_date, true) });
  }
  if (state) {
    q.query.value.push({ field: 'state', operator: '=', value: state });
  }
  if (team_assignee_id) {
    q.query.value.push({ field: 'team_assignee_id', operator: '=', value: String(team_assignee_id) });
  }
  if (q.query.value.length === 0 && to_date) {
    q.query.value.push({ field: 'created_at', operator: '<=', value: toUnixBoundary(to_date, true) });
  }
  return q;
}

// ── Content data export (for Series metrics) ─────────────────────────────

/**
 * Create a content data export job. Only one job per workspace can be pending.
 * @param {object} intercomApi - axios instance
 * @param {string} fromDate - YYYY-MM-DD
 * @param {string} toDate - YYYY-MM-DD
 * @returns {Promise<{ job_identifier: string, status: string }>}
 */
export async function createContentDataExport(intercomApi, fromDate, toDate) {
  const created_at_after = toUnixBoundary(fromDate, false);
  const created_at_before = toUnixBoundary(toDate, true);
  const response = await retryableRequest(() =>
    intercomApi.post('/export/content/data', { created_at_after, created_at_before })
  );
  const body = response.data;
  const job_identifier = body.job_identifier ?? body.job_identfier;
  return { job_identifier, status: body.status ?? 'pending', download_url: body.download_url };
}

/**
 * Get content data export job status.
 * @param {object} intercomApi - axios instance
 * @param {string} jobIdentifier
 * @returns {Promise<{ status: string, download_url?: string }>}
 */
export async function getContentDataExportStatus(intercomApi, jobIdentifier) {
  const response = await retryableRequest(() =>
    intercomApi.get(`/export/content/data/${jobIdentifier}`)
  );
  const body = response.data;
  return {
    status: body.status ?? 'pending',
    download_url: body.download_url,
    download_expires_at: body.download_expires_at,
  };
}

/**
 * Download content data export (gzipped). Use full URL so auth is applied to same origin.
 * Returns raw buffer (gzipped). Caller must gunzip and extract or parse receipts CSV.
 * @param {object} axiosInstance - axios with same defaults (baseURL, auth); will GET fullUrl
 * @param {string} fullDownloadUrl - e.g. https://api.intercom.io/download/content/data/{job_identifier}
 * @returns {Promise<Buffer>}
 */
export async function downloadContentDataExport(axiosInstance, fullDownloadUrl) {
  const response = await retryableRequest(() =>
    axiosInstance.get(fullDownloadUrl, {
      responseType: 'arraybuffer',
      headers: { Accept: 'application/octet-stream' },
      maxContentLength: 200 * 1024 * 1024,
      timeout: 120000,
    })
  );
  return Buffer.from(response.data);
}

/**
 * Parse timestamp from CSV (Unix seconds or ISO string) to Unix seconds. Returns null if invalid or empty.
 */
function parseTimestamp(val) {
  if (val == null || String(val).trim() === '') return null;
  const v = String(val).trim();
  const num = Number(v);
  if (!Number.isNaN(num) && num > 0) {
    const asSec = num > 1e12 ? Math.floor(num / 1000) : Math.floor(num);
    return asSec;
  }
  const ms = Date.parse(v);
  return Number.isNaN(ms) ? null : Math.floor(ms / 1000);
}

/**
 * Parse a receipts CSV string (from Intercom content export) and aggregate Series metrics.
 * When fromDate/toDate are provided, counts only events (finished, disengaged, exited, goal) whose timestamp falls in range, to align with Intercom UI "performance in period".
 * @param {string} csvText - Full CSV text (header + rows)
 * @param {{ fromDate?: string, toDate?: string }} options - optional YYYY-MM-DD range for in-period counts
 * @returns {{ series: Array<{ series_id, series_title, started, finished, disengaged, exited, goal }> }}
 */
export function aggregateSeriesFromReceiptsCsv(csvText, options = {}) {
  const { fromDate, toDate } = options;
  const fromTs = fromDate ? toUnixBoundary(fromDate, false) : null;
  const toTs = toDate ? toUnixBoundary(toDate, true) : null;
  const inPeriod = (ts) => ts != null && (!fromTs || ts >= fromTs) && (!toTs || ts <= toTs);

  const lines = csvText.split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return { series: [] };

  const header = parseCsvLine(lines[0]);
  const idx = (name) => {
    const i = header.indexOf(name);
    return i >= 0 ? i : header.indexOf(name.replace(/_/g, ''));
  };
  const userIdx = header.findIndex((h) => h === 'user_id' || h === 'email');
  const seriesIdIdx = idx('series_id');
  const seriesTitleIdx = idx('series_title');
  const firstCompletionIdx = idx('first_series_completion');
  const firstDisengageIdx = idx('first_series_disengagement');
  const firstExitIdx = idx('first_series_exit');
  const firstGoalIdx = idx('first_goal_success');

  if (userIdx < 0 || seriesIdIdx < 0) return { series: [] };

  const bySeries = new Map();

  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    const userId = (row[userIdx] || '').toString().trim();
    const seriesId = (row[seriesIdIdx] ?? '').toString().trim();
    const seriesTitle = (seriesTitleIdx >= 0 ? row[seriesTitleIdx] : '').toString().trim();
    if (!userId || !seriesId || seriesId === '-1') continue;

    const key = seriesId;
    if (!bySeries.has(key)) {
      bySeries.set(key, {
        series_id: seriesId,
        series_title: seriesTitle || seriesId,
        started: new Set(),
        finished: new Set(),
        disengaged: new Set(),
        exited: new Set(),
        goal: new Set(),
      });
    }
    const s = bySeries.get(key);
    s.started.add(userId);

    const completionTs = firstCompletionIdx >= 0 ? parseTimestamp(row[firstCompletionIdx]) : null;
    const disengageTs = firstDisengageIdx >= 0 ? parseTimestamp(row[firstDisengageIdx]) : null;
    const exitTs = firstExitIdx >= 0 ? parseTimestamp(row[firstExitIdx]) : null;
    const goalTs = firstGoalIdx >= 0 ? parseTimestamp(row[firstGoalIdx]) : null;

    if (completionTs != null && (!fromTs || inPeriod(completionTs))) s.finished.add(userId);
    if (disengageTs != null && (!fromTs || inPeriod(disengageTs))) s.disengaged.add(userId);
    if (exitTs != null && (!fromTs || inPeriod(exitTs))) s.exited.add(userId);
    if (goalTs != null && (!fromTs || inPeriod(goalTs))) s.goal.add(userId);
  }

  const series = Array.from(bySeries.values()).map((s) => ({
    series_id: s.series_id,
    series_title: s.series_title,
    started: s.started.size,
    finished: s.finished.size,
    disengaged: s.disengaged.size,
    exited: s.exited.size,
    goal: s.goal.size,
  }));

  return { series };
}

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
    if (inQuotes && c === '"' && line[i + 1] === '"') {
      cur += '"';
      i++;
      continue;
    }
    cur += c;
  }
  out.push(cur);
  return out;
}
