#!/usr/bin/env python3
"""
Import RNS SQLite data into Cloudflare D1 in chunks.

Generates SQL files with batched INSERT statements and executes them
via wrangler CLI. D1 has limits on SQL file size, so we chunk into
~50K rows per file (~10-15MB each).

Usage:
    python import_to_d1.py
    python import_to_d1.py --sqlite ../tools/scripts/rns_datasets/rns.sqlite --batch-size 50000
"""

import argparse
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


def escape_sql(val: str | None) -> str:
    """Escape a value for SQL INSERT."""
    if val is None or val == "":
        return "NULL"
    return "'" + val.replace("'", "''") + "'"


def generate_chunk(rows: list, chunk_num: int, output_dir: Path) -> Path:
    """Generate a SQL file with INSERT statements for a chunk of rows."""
    path = output_dir / f"chunk_{chunk_num:03d}.sql"
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            vals = ", ".join(escape_sql(v) for v in row)
            f.write(f"INSERT OR IGNORE INTO companies VALUES ({vals});\n")
    return path


def main():
    parser = argparse.ArgumentParser(description="Import RNS data into D1")
    parser.add_argument(
        "--sqlite",
        default=str(Path(__file__).resolve().parents[1] / "tools" / "scripts" / "rns_datasets" / "rns.sqlite"),
        help="Path to RNS SQLite file",
    )
    parser.add_argument("--db-name", default="rns-cuit-enrichment", help="D1 database name")
    parser.add_argument("--batch-size", type=int, default=50000, help="Rows per chunk")
    parser.add_argument("--skip-schema", action="store_true", help="Skip schema creation")
    parser.add_argument("--start-chunk", type=int, default=0, help="Resume from chunk N")
    args = parser.parse_args()

    sqlite_path = args.sqlite
    db_name = args.db_name
    batch_size = args.batch_size

    # Temp directory for SQL chunks
    chunk_dir = Path(__file__).resolve().parent / "chunks"
    chunk_dir.mkdir(exist_ok=True)

    # Step 1: Create schema in D1
    if not args.skip_schema:
        print("Creating schema in D1...")
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        result = subprocess.run(
            ["wrangler", "d1", "execute", db_name, "--file", str(schema_path), "--remote", "-y"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Schema creation failed: {result.stderr}")
            sys.exit(1)
        print("  Schema created.")

    # Step 2: Read from local SQLite and chunk
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    total = cursor.fetchone()[0]
    print(f"\nTotal rows to import: {total:,}")

    cursor.execute(
        "SELECT cuit, razon_social, razon_social_norm, fecha_contrato_social, "
        "tipo_societario, provincia, actividad_descripcion FROM companies"
    )

    chunk_num = 0
    imported = 0
    t0 = time.time()

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        if chunk_num < args.start_chunk:
            chunk_num += 1
            imported += len(rows)
            continue

        chunk_path = generate_chunk(rows, chunk_num, chunk_dir)
        size_mb = chunk_path.stat().st_size / (1024 * 1024)
        imported += len(rows)

        print(f"  Chunk {chunk_num}: {len(rows):,} rows ({size_mb:.1f}MB) — importing... ", end="", flush=True)

        result = subprocess.run(
            ["wrangler", "d1", "execute", db_name, "--file", str(chunk_path), "--remote", "-y"],
            capture_output=True, text=True,
        )

        if result.returncode != 0:
            print(f"FAILED")
            print(f"  Error: {result.stderr[:500]}")
            print(f"  Resume with: --start-chunk {chunk_num} --skip-schema")
            conn.close()
            sys.exit(1)

        elapsed = time.time() - t0
        rate = imported / elapsed if elapsed > 0 else 0
        eta = (total - imported) / rate if rate > 0 else 0

        print(f"OK ({imported:,}/{total:,} — {rate:.0f} rows/s, ETA {eta:.0f}s)")

        # Clean up chunk file
        chunk_path.unlink()
        chunk_num += 1

    conn.close()

    # Clean up chunk dir
    if chunk_dir.exists() and not list(chunk_dir.iterdir()):
        chunk_dir.rmdir()

    elapsed = time.time() - t0
    print(f"\nDone! Imported {imported:,} rows in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
