#!/usr/bin/env python3
"""
Convert RNS CSV dataset to SQLite for Cloudflare D1 deployment.

Reads the 833MB CSV (3M+ rows), deduplicates by CUIT (→ 1.24M rows),
keeps only the columns needed for enrichment/search, and exports a
compact SQLite database (~125MB).

Usage:
    python rns_to_sqlite.py
    python rns_to_sqlite.py --csv path/to/custom.csv --output rns.db
"""

import argparse
import sqlite3
import time
import unicodedata
import re
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Text normalization (mirrors rns_name_search.py for search compatibility)
# ---------------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


_LEGAL_SUFFIXES = re.compile(
    r"\b(S\.?A\.?U?\.?|S\.?A\.?S?\.?|S\.?R\.?L\.?|S\.?C\.?|S\.?H\.?|S\.?E\.?|"
    r"SOCIEDAD ANONIMA UNIPERSONAL|SOCIEDAD ANONIMA|"
    r"SOCIEDAD DE RESPONSABILIDAD LIMITADA|"
    r"SOCIEDAD POR ACCIONES SIMPLIFICADA)\s*$",
    re.IGNORECASE,
)


def normalize_name(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    text = raw.upper().strip()
    text = _strip_accents(text)
    text = _LEGAL_SUFFIXES.sub("", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert(csv_path: str, output_path: str) -> None:
    t0 = time.time()

    print(f"Reading CSV: {csv_path}")
    df = pd.read_csv(
        csv_path,
        encoding="utf-8",
        low_memory=False,
        on_bad_lines="skip",
        usecols=[
            "cuit",
            "razon_social",
            "fecha_hora_contrato_social",
            "tipo_societario",
            "dom_fiscal_provincia",
            "actividad_descripcion",
        ],
        dtype={
            "cuit": str,
            "razon_social": str,
            "fecha_hora_contrato_social": str,
            "tipo_societario": str,
            "dom_fiscal_provincia": str,
            "actividad_descripcion": str,
        },
    )
    print(f"  Loaded {len(df):,} rows in {time.time() - t0:.1f}s")

    # Drop rows without CUIT or name
    df = df.dropna(subset=["cuit", "razon_social"])
    print(f"  After dropping nulls: {len(df):,} rows")

    # Normalize CUIT: strip dashes, keep only digits
    df["cuit"] = df["cuit"].str.replace("-", "", regex=False).str.strip()
    df = df[df["cuit"].str.len() == 11]
    print(f"  After CUIT validation (11 digits): {len(df):,} rows")

    # Deduplicate by CUIT — keep first occurrence
    df = df.drop_duplicates(subset=["cuit"], keep="first")
    print(f"  After dedup: {len(df):,} unique CUITs")

    # Rename columns for cleaner schema
    df = df.rename(columns={
        "fecha_hora_contrato_social": "fecha_contrato_social",
        "dom_fiscal_provincia": "provincia",
    })

    # Add normalized name column for search
    df["razon_social_norm"] = df["razon_social"].apply(normalize_name)

    # Extract just the date part from fecha_contrato_social (may have time component)
    df["fecha_contrato_social"] = df["fecha_contrato_social"].str[:10]

    # Fill NaN with empty string for text columns
    for col in ["tipo_societario", "provincia", "actividad_descripcion", "fecha_contrato_social"]:
        df[col] = df[col].fillna("")

    # Write to SQLite
    print(f"\nWriting SQLite: {output_path}")
    db_path = Path(output_path)
    db_path.unlink(missing_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE companies (
            cuit TEXT PRIMARY KEY,
            razon_social TEXT NOT NULL,
            razon_social_norm TEXT NOT NULL,
            fecha_contrato_social TEXT,
            tipo_societario TEXT,
            provincia TEXT,
            actividad_descripcion TEXT
        )
    """)

    # Insert data
    cols = ["cuit", "razon_social", "razon_social_norm", "fecha_contrato_social",
            "tipo_societario", "provincia", "actividad_descripcion"]
    rows = df[cols].values.tolist()

    cursor.executemany(
        "INSERT INTO companies VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    print(f"  Inserted {len(rows):,} rows")

    # Create indexes
    print("  Creating indexes...")
    cursor.execute("CREATE INDEX idx_razon_social_norm ON companies(razon_social_norm)")
    conn.commit()

    # Stats
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]

    conn.close()

    size_mb = db_path.stat().st_size / (1024 * 1024)
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  Rows: {count:,}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Path: {db_path.absolute()}")


def main():
    datasets_dir = Path(__file__).resolve().parent / "rns_datasets"
    default_csv = sorted(datasets_dir.glob("registro-nacional-sociedades-*.csv"))
    default_csv = str(default_csv[-1]) if default_csv else None

    parser = argparse.ArgumentParser(description="Convert RNS CSV to SQLite for D1")
    parser.add_argument("--csv", default=default_csv, help="Path to RNS CSV file")
    parser.add_argument("--output", default=str(datasets_dir / "rns.sqlite"),
                        help="Output SQLite path")
    args = parser.parse_args()

    if not args.csv:
        parser.error("No CSV found. Provide --csv path.")

    convert(args.csv, args.output)


if __name__ == "__main__":
    main()
