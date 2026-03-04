-- RNS CUIT Enrichment — D1 schema
-- 1.24M unique Argentine companies from datos.jus.gob.ar

CREATE TABLE IF NOT EXISTS companies (
    cuit TEXT PRIMARY KEY,
    razon_social TEXT NOT NULL,
    razon_social_norm TEXT NOT NULL,
    fecha_contrato_social TEXT,
    tipo_societario TEXT,
    provincia TEXT,
    actividad_descripcion TEXT
);

CREATE INDEX IF NOT EXISTS idx_razon_social_norm ON companies(razon_social_norm);
