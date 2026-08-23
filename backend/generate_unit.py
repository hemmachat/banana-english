#!/usr/bin/env python3
"""Generate a scenario unit from a registry entry. Step 4 of PLAN.md.

    .venv/bin/python generate_unit.py asking_directions
    .venv/bin/python generate_unit.py au_gp_appointment --locale en-AU
    .venv/bin/python generate_unit.py --batch tier1 --locale global
    .venv/bin/python generate_unit.py --validate-only content/en-AU/au_gp_appointment.json

Writes content/<locale>/<id>.json. Then run, in order:
    render_audio.py -> calibrate.py -> translate.py -> seed.py

The prompt below encodes what Step 0 and Step 2 testing established. Those findings are not
optional polish - they are why the AU flagship scores correctly. See spike/README.md 6b-6e.
"""
import argparse, glob, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _l in open(os.path.join(HERE, ".env")) if os.path.exists(os.path.join(HERE, ".env")) else []:
    if "=" in _l and not _l.strip().startswith("#"):
        k, v = _l.strip().split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

REGISTRY = os.path.join(ROOT, "docs/curriculum/scenario-registry.yaml")
LOCALE_PACKS = {"en-AU": os.path.join(ROOT, "docs/curriculum/locale-pack-australia.yaml")}
FLAGSHIP = os.path.join(ROOT, "docs/curriculum/au-flagship-unit-gp-appointment.md")

# /th/ cannot be scored by phoneme - 61-100 across six perfect native takes (spike/README.md 6b)
MINIMAL_PAIR_SOUNDS = {"th"}
# Azure returns ProsodyScore for en-US ONLY, so these are taught and drilled but never metered.
# Marking them explicitly beats pretending a phoneme score means something for them.
UNSCORED_SOUNDS = {"word_stress", "intonation", "weak_forms"}


def scoring_method_for(sound):
    if sound in UNSCORED_SOUNDS:
        return "unscored"
    return "minimal_pair" if sound in MINIMAL_PAIR_SOUNDS else "phoneme"

BASE_RULES = """You are an English-education content designer building situational speaking lessons
for Thai adult learners (CEFR A1-B2). Return ONE JSON object, no prose outside it.

NON-NEGOTIABLES
1. Match the benchmark unit's depth. Do not produce anything thinner.
2. Function over grammar. Every element serves a real can-do goal.
3. Thai L1 targeting is mandatory and scenario-motivated. Use ONLY the registry's sound_targets, and
   drill each inside dialogue and roleplay where getting it wrong has a real cost. Populate
   why_it_matters_here with a concrete consequence.
4. Span the levels: an A2 scripted dialogue AND a B1 off-script dialogue of the same situation.
5. Spiral: explicitly reuse language from the `recycles` list.
6. Register and culture: a do_dont grounded in real intelligibility failures, and a thai_cultural_note
   flagging a genuine cultural difference, never a stereotype.
7. Natural speech only. Dialogue must sound like a real person, not a textbook.

WHAT DEVICE TESTING PROVED - these are requirements, not suggestions:

8. scoring_method on every sound target - use exactly the values supplied in the request.
   "th" is "minimal_pair": phoneme scoring for it is unusable (61-100 across six flawless native
   takes). Prosodic targets (word_stress, intonation, weak_forms) are "unscored": the vendor
   returns no prosody data for en-AU, so they are taught and drilled but never metered. Everything
   else is "phoneme". Every target still needs minimal_pairs of REAL WORDS - word-level
   recognition is the fallback whenever a number is untrustworthy.

9. Dialogue length. The A2 dialogue is 7-10 lines. The B1 dialogue is 15-20 lines - it must be
   visibly harder and longer, with the learner handling something unexpected. A short B1 dialogue
   is the most common failure; testers said short conversations felt unreal.

10. shadow_focus_lines: 4 per dialogue, each 3-6 words. They are billed per second of audio and
    drilled to automaticity, so they must be short and repeatable. Give each one `targets`
    naming which sound_targets it stresses.

11. The learner's own lines must be short and sayable by someone who is nervous. Long learner
    lines are an authoring smell.

12. Never write a learner line that only a fluent speaker would produce. This unit is for someone
    whose best effort currently scores around 58 out of 100.

OUTPUT SCHEMA - every field required:
{"scenario_id","locale","title_en","title_th":null,"tier","cefr_range":["A2","B1"],
 "prerequisites":[],"recycles":[],"register",
 "sound_target_box":{"note_th":null,"targets":[{"sound","scoring_method","words_in_context":[],
   "minimal_pairs":[["a","b"]],"why_it_matters_here"}]},
 "vocabulary":[{"en","th":null,"group","audio_needed":true}],
 "model_dialogues":[{"cefr":"A2","label","lines":[{"speaker","text"}],
   "shadow_focus_lines":[{"text","targets":[]}]}],
 "chunk_drills":[{"label","pattern","examples":[],"spiralled_grammar"}],
 "listening_items":[{"audio_text","channel","question","answer","distractor_focus"}],
 "guided_roleplay":{"learner_role","flow":[],"sentence_frames":[],"hints_available":true},
 "free_roleplay":{"ai_persona","a2_behavior","b1_curveballs":[],
   "roleplay_rubric":[{"criterion","type"}]},
 "register_culture_note":{"en","th":null,"do_dont":[{"avoid","prefer"}],"thai_cultural_note"},
 "can_do_checkpoints":[{"cefr","statement"}],
 "gamification":{"xp_per_substep":true,"unlocks":[],"sound_meters":[]}}

Copy title_th verbatim from the registry entry's `th`. Leave every OTHER Thai field null - a native
speaker drafts and reviews those separately (translate.py). Inventing Thai here produces text nobody
can verify, which CLAUDE.md forbids shipping.

roleplay_rubric needs 4+ criteria of type "required", one "pronunciation", one "stretch_b1"."""

LOCALE_RULES = """
LOCALISATION - locale is {locale}:
9L. Use the host country's systems and terms exactly, from the locale context below.
10L. Host spelling and accent throughout ({locale}: -ise/-our/-re, "enrolment", "recognise").
11L. Host register - casual but respectful, first names, direct.
12L. Keep the invariant core invariant: Thai sound targets, CEFR banding, do_dont safety guidance
     and the structure DO NOT change by locale. Only the system layer localises.
13L. The culture note must reflect a genuine host-country difference plus the Thai-learner bridge.

NEVER let another country's terms leak in. For en-AU that means no: 911, ER, ZIP code, NHS, copay,
Social Security, pharmacy(US sense), or US spellings (-ize, color, enrollment).

LOCALE CONTEXT:
{context}"""

LEAKAGE = {"en-AU": [r"\b911\b", r"\bER\b", r"ZIP code", r"\bNHS\b", r"\bcopay", r"Social Security",
                     r"\w+ize\b", r"\bcolor\b", r"enrollment", r"\bgotten\b", r"\bsidewalk\b"]}
REQUIRED_TERMS = {("en-AU", "health"): ["Medicare", "bulk bill"]}


def load_registry(scenario_id, locale):
    """Find the entry in the core registry or the locale pack."""
    entries = list(yaml.safe_load(open(REGISTRY)) or [])
    if locale in LOCALE_PACKS:
        entries += yaml.safe_load(open(LOCALE_PACKS[locale])).get("scenarios", [])
    for e in entries or []:
        if isinstance(e, dict) and e.get("id") == scenario_id:
            return e
    raise SystemExit(f"'{scenario_id}' not found in the registry or the {locale} pack")


def locale_context(locale):
    if locale not in LOCALE_PACKS:
        return ""
    cfg = yaml.safe_load(open(LOCALE_PACKS[locale])).get("config", {})
    return json.dumps(cfg, ensure_ascii=False, indent=1)


def generate(entry, locale):
    import anthropic
    sounds = entry.get("sounds", [])
    methods = {s: scoring_method_for(s) for s in sounds}
    system = BASE_RULES
    if locale != "global":
        system += LOCALE_RULES.format(locale=locale, context=locale_context(locale))

    # a full unit is a large generation; the SDK requires streaming above 10 minutes
    with anthropic.Anthropic().messages.stream(
        model=os.environ.get("GENERATE_MODEL", "claude-opus-5"),
        max_tokens=32000,
        system=system,
        messages=[{"role": "user", "content":
                   f"BENCHMARK (match this depth):\n{open(FLAGSHIP).read()[:9000]}\n\n"
                   f"REGISTRY ENTRY:\n{json.dumps(entry, ensure_ascii=False, indent=1)}\n\n"
                   f"locale = {locale}\n"
                   f"scoring_method per sound (use exactly these): {json.dumps(methods)}\n\n"
                   f"Generate the unit JSON."}],
    ) as stream:
        r = stream.get_final_message()
    text = "".join(c.text for c in r.content if c.type == "text")
    unit = json.loads(text[text.index("{"):text.rindex("}") + 1])
    unit["locale"] = locale
    unit.setdefault("_review_status", {})
    unit["_review_status"].update({
        "thai_strings": "NOT AUTHORED - run translate.py, then a native speaker reviews",
        "facts": f"UNVERIFIED - generated content, needs a local fact-check before shipping",
        "generated_by": os.environ.get("GENERATE_MODEL", "claude-opus-5"),
    })
    return unit, r.usage


def validate(unit, entry, locale):
    """Spec section 5 + addendum section 4. Fails loudly with reasons; never auto-fixes."""
    errs = []
    def need(cond, msg):
        if not cond:
            errs.append(msg)

    need(unit.get("scenario_id") == entry["id"], "scenario_id does not match the registry")
    need(unit.get("locale") == locale, f"locale should be {locale}")
    need(len(unit.get("cefr_range", [])) >= 2, "cefr_range needs at least 2 levels")

    targets = unit.get("sound_target_box", {}).get("targets", [])
    got = {t.get("sound") for t in targets}
    for s in entry.get("sounds", []):
        need(s in got, f"registry sound_target '{s}' missing from sound_target_box")
    for t in targets:
        want = scoring_method_for(t.get("sound"))
        need(t.get("scoring_method") == want,
             f"sound '{t.get('sound')}' must use scoring_method '{want}' (spike/README.md 6b)")
        need(t.get("scoring_method") != "phoneme" or t.get("sound") not in UNSCORED_SOUNDS,
             f"prosodic sound '{t.get('sound')}' cannot be phoneme-scored - no en-AU prosody data")
        need(t.get("minimal_pairs"), f"sound '{t.get('sound')}' has no minimal_pairs")
        need(t.get("why_it_matters_here"), f"sound '{t.get('sound')}' has no why_it_matters_here")

    dialogues = {d.get("cefr"): d for d in unit.get("model_dialogues", [])}
    need("A2" in dialogues and "B1" in dialogues, "needs both an A2 and a B1 dialogue")
    for cefr, lo, hi in (("A2", 6, 12), ("B1", 14, 22)):
        d = dialogues.get(cefr)
        if not d:
            continue
        n = len(d.get("lines", []))
        need(lo <= n <= hi, f"{cefr} dialogue has {n} lines, expected {lo}-{hi}")
        shadows = d.get("shadow_focus_lines", [])
        need(len(shadows) >= 3, f"{cefr} needs at least 3 shadow_focus_lines, has {len(shadows)}")
        for sl in shadows:
            words = len(sl.get("text", "").split())
            need(words <= 8, f"shadow line '{sl.get('text')}' is {words} words, keep it under 8")
            need(sl.get("targets"), f"shadow line '{sl.get('text')}' has no targets")

    # every sound target must be stressed somewhere the learner speaks. Check the structured
    # `targets` field, not a substring match - prosodic targets have no literal word to find, and
    # words_in_context legitimately carries IPA annotations that never match plain line text.
    tagged = {tag for d in unit.get("model_dialogues", [])
              for sl in d.get("shadow_focus_lines", []) for tag in sl.get("targets", [])}
    spoken = " ".join(sl.get("text", "") for d in unit.get("model_dialogues", [])
                      for sl in d.get("shadow_focus_lines", [])).lower()
    curve = " ".join(unit.get("free_roleplay", {}).get("b1_curveballs", [])).lower()
    for t in targets:
        sound = t.get("sound")
        words = [re.sub(r"\s*\(.*", "", w).lower() for w in t.get("words_in_context", [])]
        need(sound in tagged or any(w and (w in spoken or w in curve) for w in words),
             f"sound '{sound}' is not named in any shadow line's targets")

    rubric = unit.get("free_roleplay", {}).get("roleplay_rubric", [])
    need(sum(1 for c in rubric if c.get("type") == "required") >= 4, "rubric needs 4+ required criteria")
    need(any(c.get("type") == "pronunciation" for c in rubric), "rubric needs a pronunciation criterion")
    need(unit.get("free_roleplay", {}).get("b1_curveballs"), "b1_curveballs is empty")

    for field in ("vocabulary", "chunk_drills", "listening_items", "can_do_checkpoints"):
        need(unit.get(field), f"{field} is empty")

    blob = json.dumps(unit, ensure_ascii=False)
    for pat in LEAKAGE.get(locale, []):
        hits = re.findall(pat, blob)
        need(not hits, f"cross-locale leakage: {pat} -> {hits[:3]}")
    for (loc, domain), terms in REQUIRED_TERMS.items():
        if loc == locale and domain in json.dumps(entry).lower():
            for term in terms:
                need(term.lower() in blob.lower(), f"en-AU {domain} unit must mention '{term}'")

    # title_th comes from the registry (author-written); everything else must be left for a
    # native speaker via translate.py. Inventing Thai here produces text nobody can verify.
    need(unit.get("title_th") in (None, entry.get("th")),
         "title_th must be null or exactly the registry's th value, not invented")
    invented = [k for k, v in (("sound_target_box.note_th",
                                unit.get("sound_target_box", {}).get("note_th")),
                               ("register_culture_note.th",
                                unit.get("register_culture_note", {}).get("th"))) if v]
    need(not invented, f"Thai must be left null for translate.py to draft: {invented}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario_id", nargs="?")
    ap.add_argument("--locale", default="global")
    ap.add_argument("--batch", help="tier number, or 'all'")
    ap.add_argument("--validate-only", metavar="PATH")
    args = ap.parse_args()

    if args.validate_only:
        unit = json.load(open(args.validate_only))
        entry = load_registry(unit["scenario_id"], unit.get("locale", "global"))
        errs = validate(unit, entry, unit.get("locale", "global"))
        print("\n".join("  FAIL " + e for e in errs) if errs else "  valid")
        sys.exit(1 if errs else 0)

    ids = []
    if args.batch:
        entries = list(yaml.safe_load(open(REGISTRY)) or [])
        if args.locale in LOCALE_PACKS:
            entries += yaml.safe_load(open(LOCALE_PACKS[args.locale])).get("scenarios", [])
        ids = [e["id"] for e in entries if isinstance(e, dict) and e.get("id")
               and (args.batch == "all" or str(e.get("tier")) == args.batch)]
    elif args.scenario_id:
        ids = [args.scenario_id]
    else:
        ap.error("give a scenario_id or --batch")

    outdir = os.path.join(ROOT, "content", args.locale)
    os.makedirs(outdir, exist_ok=True)
    ok = fail = 0
    for sid in ids:
        entry = load_registry(sid, args.locale)
        print(f"\n{sid} ({args.locale})")
        try:
            unit, usage = generate(entry, args.locale)
        except Exception as e:
            print(f"  ERROR {type(e).__name__}: {str(e)[:200]}"); fail += 1; continue
        errs = validate(unit, entry, args.locale)
        cost = usage.input_tokens / 1e6 * 5 + usage.output_tokens / 1e6 * 25
        if errs:
            path = os.path.join(outdir, f"{sid}.REJECTED.json")
            json.dump(unit, open(path, "w"), indent=2, ensure_ascii=False)
            print("\n".join(f"  FAIL {e}" for e in errs))
            print(f"  -> {os.path.relpath(path, ROOT)} (not published)  ${cost:.3f}")
            fail += 1
        else:
            path = os.path.join(outdir, f"{sid}.json")
            json.dump(unit, open(path, "w"), indent=2, ensure_ascii=False)
            print(f"  ok -> {os.path.relpath(path, ROOT)}  ${cost:.3f}")
            ok += 1
    print(f"\n{ok} passed, {fail} failed")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
