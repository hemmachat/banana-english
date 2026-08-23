#!/usr/bin/env python3
"""Load content/<locale>/*.json into units. Idempotent - re-run after editing content."""
import json, os, sys, glob
import psycopg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DSN = os.environ.get("DATABASE_URL", "postgresql:///papaya")

with psycopg.connect(DSN, autocommit=True) as conn:
    n = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
        unit = json.load(open(path))
        locale = unit.get("locale", "global")
        conn.execute("""insert into units (scenario_id, locale, data) values (%s,%s,%s)
                        on conflict (scenario_id, locale)
                        do update set data = excluded.data, updated_at = now()""",
                     (unit["scenario_id"], locale, json.dumps(unit)))
        print(f"  {unit['scenario_id']:24} {locale:8} <- {os.path.relpath(path, ROOT)}")
        n += 1
    print(f"{n} unit(s) loaded")
