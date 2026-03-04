/**
 * RNS CUIT Enrichment API — Cloudflare Worker + D1
 *
 * Two endpoints:
 *   GET /enrich?cuit=30712461221  → company details by CUIT
 *   GET /search?q=colppy&limit=10 → company name search (multi-token, LIKE)
 *
 * Data: 1.24M unique Argentine companies from RNS (datos.jus.gob.ar)
 */

interface Env {
  DB: D1Database;
}

interface CompanyRow {
  cuit: string;
  razon_social: string;
  razon_social_norm: string;
  fecha_contrato_social: string | null;
  tipo_societario: string | null;
  provincia: string | null;
  actividad_descripcion: string | null;
}

// --- Text normalization (mirrors Python rns_name_search.py) ---

function stripAccents(text: string): string {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function normalizeQuery(raw: string): string {
  return stripAccents(raw.toUpperCase().trim()).replace(/\s+/g, " ");
}

// --- Handlers ---

async function handleEnrich(cuit: string, db: D1Database): Promise<Response> {
  // Strip dashes, validate 11 digits
  const clean = cuit.replace(/-/g, "").trim();
  if (!/^\d{11}$/.test(clean)) {
    return json({ error: `Invalid CUIT: must be 11 digits, got '${cuit}'` }, 400);
  }

  const row = await db
    .prepare("SELECT * FROM companies WHERE cuit = ?")
    .bind(clean)
    .first<CompanyRow>();

  if (!row) {
    return json({ cuit: clean, found: false });
  }

  return json({
    cuit: clean,
    found: true,
    razon_social: row.razon_social,
    fecha_contrato_social: row.fecha_contrato_social || null,
    tipo_societario: row.tipo_societario || null,
    provincia: row.provincia || null,
    actividad_descripcion: row.actividad_descripcion || null,
  });
}

async function handleSearch(
  query: string,
  limit: number,
  provincia: string | null,
  db: D1Database
): Promise<Response> {
  if (!query || query.length < 2) {
    return json({ error: "Query must be at least 2 characters" }, 400);
  }

  const norm = normalizeQuery(query);
  const tokens = norm.split(" ").filter((t) => t.length > 0);

  // Build WHERE clause: each token must appear in razon_social_norm
  const conditions: string[] = [];
  const params: string[] = [];

  for (const token of tokens) {
    conditions.push("razon_social_norm LIKE ?");
    params.push(`%${token}%`);
  }

  if (provincia) {
    conditions.push("UPPER(provincia) LIKE ?");
    params.push(`%${stripAccents(provincia.toUpperCase())}%`);
  }

  const where = conditions.join(" AND ");
  const sql = `SELECT cuit, razon_social, fecha_contrato_social, tipo_societario, provincia, actividad_descripcion
               FROM companies WHERE ${where} LIMIT ?`;
  params.push(String(Math.min(limit, 50)));

  const { results } = await db
    .prepare(sql)
    .bind(...params)
    .all<CompanyRow>();

  return json({
    query,
    count: results.length,
    results: results.map((r) => ({
      cuit: r.cuit,
      razon_social: r.razon_social,
      fecha_contrato_social: r.fecha_contrato_social || null,
      tipo_societario: r.tipo_societario || null,
      provincia: r.provincia || null,
      actividad_descripcion: r.actividad_descripcion || null,
    })),
  });
}

// --- Router ---

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (path === "/enrich") {
      const cuit = url.searchParams.get("cuit");
      if (!cuit) return json({ error: "Missing ?cuit= parameter" }, 400);
      return handleEnrich(cuit, env.DB);
    }

    if (path === "/search") {
      const q = url.searchParams.get("q");
      if (!q) return json({ error: "Missing ?q= parameter" }, 400);
      const limit = parseInt(url.searchParams.get("limit") || "10", 10);
      const provincia = url.searchParams.get("provincia") || null;
      return handleSearch(q, limit, provincia, env.DB);
    }

    // Health / info
    if (path === "/" || path === "/health") {
      const { results } = await env.DB
        .prepare("SELECT COUNT(*) as count FROM companies")
        .all();
      return json({
        service: "RNS CUIT Enrichment API",
        source: "datos.jus.gob.ar — Registro Nacional de Sociedades",
        companies: results[0]?.count ?? 0,
        endpoints: {
          enrich: "GET /enrich?cuit=30712461221",
          search: "GET /search?q=colppy&limit=10&provincia=Buenos+Aires",
          health: "GET /health",
        },
      });
    }

    return json({ error: "Not found. Try /enrich?cuit=... or /search?q=..." }, 404);
  },
} satisfies ExportedHandler<Env>;
