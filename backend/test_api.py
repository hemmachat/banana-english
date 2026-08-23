#!/usr/bin/env python3
"""End-to-end check of the scoring + progress logic. Needs the server running on :5001.

    .venv/bin/python test_api.py
"""
import json, urllib.request

BASE = "http://localhost:5001"


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(req))


assert call("GET", "/health")["ok"]

uid = call("POST", "/users", {"tz": "Australia/Sydney"})["id"]

# real Step 0 numbers: same-ish raw score, very different meaning once calibrated
cases = [
    ("final_consonants", "phoneme",     67, 100.0, 4),   # dropped /d/ in "card"
    ("th",               "minimal_pair", 74, 79.8,  5),   # /th/ ceiling is 79.8, not 100
    ("clusters",         "phoneme",       9, 100.0, 3),   # "bulk billed" collapsed
    ("r_l",              "phoneme",      78, 98.2,  4),   # "referral"
]
for sound, method, raw, ceiling, secs in cases:
    call("POST", "/attempts", {"user_id": uid, "scenario_id": "au_gp_appointment",
                               "stage": "shadow", "sound_target": sound,
                               "scoring_method": method, "raw_score": raw,
                               "ceiling": ceiling, "seconds_spoken": secs})

p = call("GET", f"/users/{uid}/progress")
meters = {m["sound_target"]: float(m["avg_score"]) for m in p["sound_meters"]}

# the whole point of the ceiling column: raw 74 on /th/ beats raw 67 on a final consonant
assert meters["th"] == 92.7, meters
assert meters["final_consonants"] == 67.0, meters
assert meters["th"] > meters["final_consonants"], "ceiling calibration is not being applied"
assert meters["clusters"] == 9.0, meters
assert round(meters["r_l"]) == 79, meters          # 78/98.2

assert p["xp"] == 4, p
assert p["total_minutes_spoken"] == round(16 / 60.0, 1), p
assert p["streak_days"] == 1, p                     # all today, in the user's tz

unit = call("GET", "/scenarios/au_gp_appointment?locale=en-AU")
assert unit["title_en"] == "Seeing a GP (Medicare)"
assert len(unit["model_dialogues"][0]["shadow_focus_lines"]) == 4
# /th/ must never be scored by phoneme - Step 0 showed 61-100 on perfect native takes
th = next(t for t in unit["sound_target_box"]["targets"] if t["sound"] == "th")
assert th["scoring_method"] == "minimal_pair", th

listing = call("GET", "/scenarios?locale=en-AU")
ids = {s["scenario_id"] for s in listing}
assert "au_gp_appointment" in ids, "the AU flagship should resolve for an en-AU learner"
# the AU pack drops Thailand-resident scenarios; without this an Australian learner is offered
# lessons on the Bangkok Skytrain
assert "bts_mrt_skytrain" not in ids, "locale drops are not being applied"
assert "bts_mrt_skytrain" in {s["scenario_id"] for s in call("GET", "/scenarios?locale=global")}, \
    "a Thailand learner should still get the Skytrain unit"

print(f"all checks passed  ({len(listing)} units resolve for en-AU)")
print(f"  sound meters: {meters}")
print(f"  xp={p['xp']} minutes={p['total_minutes_spoken']} streak={p['streak_days']}d")
