#!/usr/bin/env python3
"""Draft Thai for vocabulary and dialogue lines. DRAFTS ONLY - a native speaker must review.

Every string written here is tagged th_status="draft_unverified". CLAUDE.md is explicit that no
unverified Thai ships; the UI shows a draft badge until a human clears it.

    .venv/bin/python translate.py                 # fill missing th, skip anything already reviewed
    .venv/bin/python translate.py --retranslate   # redo drafts (never touches reviewed strings)
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _l in open(os.path.join(HERE, ".env")) if os.path.exists(os.path.join(HERE, ".env")) else []:
    if "=" in _l and not _l.strip().startswith("#"):
        k, v = _l.strip().split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import anthropic

SYSTEM = """You write Thai for a Thai adult learning English in Australia.

Rules:
1. Natural spoken Thai, the way a Thai friend would explain it. Not textbook, not literal.
2. Australian system terms (Medicare, bulk billed, script, pathology, gap fee, GP) have NO Thai
   equivalent. Do NOT invent one. Keep the English term and add a short Thai explanation of what
   it actually means in practice. e.g. bulk billed -> keep "bulk billed", explain it means
   Medicare pays and you pay nothing.
3. For dialogue lines, convey what the speaker MEANS, including tone. A casual Australian line
   should read casual in Thai, not formal.
4. Use ครับ/ค่ะ sparingly - these are explanations, not dialogue with the learner.
5. Keep it short. This appears under the English on a phone screen.

Return JSON only: {"items":[{"i":0,"th":"..."}]}"""


def draft(items, kind):
    """items: list of English strings. Returns list of Thai strings."""
    client = anthropic.Anthropic()
    listing = "\n".join(f"{i}. {t}" for i, t in enumerate(items))
    r = client.messages.create(
        model=os.environ.get("TRANSLATE_MODEL", "claude-opus-5"),
        max_tokens=8000,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"These are {kind} from a unit about seeing a GP "
                                              f"in Australia.\n\n{listing}"}],
    )
    text = "".join(c.text for c in r.content if c.type == "text")
    parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
    out = [None] * len(items)
    for x in parsed.get("items", []):
        if 0 <= x.get("i", -1) < len(items):
            out[x["i"]] = x.get("th")
    return out


redo = "--retranslate" in sys.argv

for path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
    unit = json.load(open(path))

    def needs(obj):
        if obj.get("th_status") == "reviewed":
            return False                       # never overwrite a human's work
        return redo or not obj.get("th")

    targets = [v for v in unit.get("vocabulary", []) if needs(v)]
    if targets:
        for obj, th in zip(targets, draft([v["en"] for v in targets], "vocabulary items")):
            obj["th"], obj["th_status"] = th, "draft_unverified"
        print(f"  {len(targets)} vocabulary drafted")

    lines = [l for d in unit.get("model_dialogues", []) for l in d.get("lines", []) if needs(l)]
    if lines:
        for obj, th in zip(lines, draft([l["text"] for l in lines], "dialogue lines")):
            obj["th"], obj["th_status"] = th, "draft_unverified"
        print(f"  {len(lines)} dialogue lines drafted")

    unit["_review_status"]["thai_strings"] = (
        "DRAFT - machine-generated, tagged th_status=draft_unverified. A native Thai speaker must "
        "review every string and set th_status='reviewed'.")
    json.dump(unit, open(path, "w"), indent=2, ensure_ascii=False)
    print(f"updated {os.path.relpath(path, ROOT)}")
