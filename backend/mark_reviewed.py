#!/usr/bin/env python3
"""Mark a unit's Thai as reviewed by a native speaker. Only a human runs this.

    .venv/bin/python mark_reviewed.py au_gp_appointment      # clear one unit
    .venv/bin/python mark_reviewed.py --status               # what's left to review

Sets th_status="reviewed" on every Thai string in the unit, which permanently protects it from
translate.py (even under --retranslate) and clears the DRAFT badge in the UI.
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strings(unit):
    """Every object in a unit that carries a Thai string."""
    out = list(unit.get("vocabulary", []))
    for d in unit.get("model_dialogues", []):
        out += d.get("lines", [])
    return [o for o in out if o.get("th")]


if "--status" in sys.argv:
    todo = done = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
        unit = json.load(open(path))
        objs = strings(unit)
        n_ok = sum(1 for o in objs if o.get("th_status") == "reviewed")
        todo += len(objs) - n_ok
        done += n_ok
        mark = "reviewed" if objs and n_ok == len(objs) else f"{n_ok}/{len(objs)}"
        print(f"  {unit['scenario_id']:30} {mark}")
    print(f"\n{done} reviewed, {todo} still draft across {len(glob.glob(os.path.join(ROOT,'content','*','*.json')))} units")
    sys.exit(0)

if len(sys.argv) < 2:
    sys.exit(__doc__)

for sid in sys.argv[1:]:
    hits = glob.glob(os.path.join(ROOT, "content", "*", f"{sid}.json"))
    if not hits:
        print(f"  {sid}: not found"); continue
    unit = json.load(open(hits[0]))
    objs = strings(unit)
    for o in objs:
        o["th_status"] = "reviewed"
    unit.setdefault("_review_status", {})["thai_strings"] = "REVIEWED by a native speaker"
    json.dump(unit, open(hits[0], "w"), indent=2, ensure_ascii=False)
    print(f"  {sid}: {len(objs)} strings marked reviewed")
print("\nRun seed.py to publish.")
