#!/usr/bin/env python3
"""Load content/<locale>/*.json into units. Idempotent - re-run after editing content."""
import json, os, sys, glob
import psycopg
import yaml

LOCALE_PACKS = {"en-AU": "docs/curriculum/locale-pack-australia.yaml"}

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

    # a locale pack can DROP core scenarios that make no sense in that country - without this an
    # Australian learner is offered lessons on the Bangkok Skytrain and songthaews
    for locale, rel in LOCALE_PACKS.items():
        pack = yaml.safe_load(open(os.path.join(ROOT, rel)))
        drops = pack.get("drops_from_core", []) or []
        conn.execute("delete from locale_drops where locale = %s", (locale,))
        for sid in drops:
            conn.execute("insert into locale_drops (locale, scenario_id) values (%s,%s)"
                         " on conflict do nothing", (locale, sid))
        print(f"{len(drops)} scenario(s) dropped for {locale}: {', '.join(drops)}")
