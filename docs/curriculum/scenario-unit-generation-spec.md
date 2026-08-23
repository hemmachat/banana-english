# Scenario Unit Generation Spec

A repeatable pipeline for producing all 141 scenario units at the quality of the flagship medical unit.

**This spec is implemented in `backend/generate_unit.py` — run that, don't do it by hand.** It reads the
registry entry, generates, validates, and writes `content/<locale>/<id>.json`. Measured cost **$0.30/unit**
(~$45 for the whole catalogue). Section 4b lists the rules device testing added; they are enforced in code.

The benchmark file (`flagship-unit-medical-centre.md`) is the **gold reference** — the generator's output for any scenario must be judged against it, not against a blank page.

---

## 1. How the pipeline works

```
scenario_registry.yaml   →  [generation prompt + this spec]  →  unit JSON  →  QA gate  →  Postgres
  (one line per scenario)      (run in Claude Code)              (validated)    (auto)      (content tables)
```

1. Maintain a flat **scenario registry** — the curriculum backbone, one entry per scenario.
2. For each entry, run the **generation prompt** (Section 4) with the entry's fields injected.
3. The model returns **one JSON object** conforming to the **output schema** (Section 3).
4. Run the **QA checklist** (Section 5) as an automated + spot-check gate before it reaches learners.
5. Insert into your content tables; the `sound_targets` and `roleplay_rubric` objects feed the pronunciation scorer and the AI roleplay engine respectively.

---

## 2. Scenario registry (input format)

One YAML entry drives one generation run. Author these by hand — this is the curriculum design, and it's small.

```yaml
- scenario_id: asking_directions
  title_en: Asking for Directions
  title_th: การถามทาง
  tier: 1
  cefr_range: [A1, B1]
  prerequisites: [greetings_small_talk]
  recycles: [numbers, excuse_me, please_thank_you]
  sound_targets: [r_l, clusters_str, final_consonants]
  register: neutral_polite
  killer_contrast: "left vs right (/l/ vs /r/) — wrong = you go the wrong way"
  sub_steps:
    - get someone's attention politely
    - ask the way to a place
    - understand a multi-step answer
    - confirm / ask them to repeat or slow down
  local_context: [BTS/MRT stations, sois, 7-Eleven as landmark, motorbike taxi]
```

**Registry-level rules the author enforces (not the model):**
- Every scenario spans **at least two CEFR levels**; the A1/A2 version is the scripted transaction, the B1 version is the same scenario gone off-script.
- `sound_targets` must be **motivated by the scenario** — pick the Thai L1 errors this situation actually stresses (see the sound→scenario map in Section 6), not a generic list.
- `recycles` must reference earlier scenarios so language spirals; a scenario that recycles nothing is a design smell.

---

## 3. Output schema (what the model must return)

One JSON object per unit. Field names map to content tables.

```json
{
  "scenario_id": "string",
  "title_en": "string",
  "title_th": "string",
  "tier": 1,
  "cefr_range": ["A2", "B1"],
  "sound_target_box": {
    "note_th": "why this scenario is phonetically hard, in Thai",
    "targets": [
      {
        "sound": "th",
        "scoring_method": "minimal_pair",
        "words_in_context": ["throat", "three", "teeth"],
        "minimal_pairs": [["three", "tree"], ["teeth", "teet"]],
        "why_it_matters_here": "string"
      }
    ]
  },
  "vocabulary": [
    { "en": "prescription", "th": "ใบสั่งยา", "group": "things", "audio_needed": true }
  ],
  "model_dialogues": [
    {
      "cefr": "A2",
      "lines": [
        { "speaker": "doctor", "text": "What brings you in today?" },
        { "speaker": "patient", "text": "I have a fever and a cough." }
      ],
      "shadow_focus_lines": [
        { "text": "twice a day for five days", "targets": ["numbers", "final_consonants"] }
      ]
    }
  ],
  "chunk_drills": [
    {
      "label": "Symptom formula",
      "pattern": "I have (a) ___ / My ___ hurts",
      "examples": ["I have a fever", "My back hurts"],
      "spiralled_grammar": "present perfect for duration: I've had this for two days"
    }
  ],
  "listening_items": [
    {
      "audio_text": "Take one pill three times a day for seven days.",
      "channel": "in_person",
      "question": "How many pills per day?",
      "answer": "3",
      "distractor_focus": "thirteen/thirty number discrimination"
    }
  ],
  "guided_roleplay": {
    "learner_role": "patient",
    "flow": ["book", "check in", "describe symptoms", "answer follow-ups", "ask about medicine"],
    "sentence_frames": ["I have a ___", "It's about a ___ out of ten"],
    "hints_available": true
  },
  "free_roleplay": {
    "ai_persona": "a busy but kind clinic doctor",
    "a2_behavior": "stays on the standard script",
    "b1_curveballs": ["asks about allergies", "refers to a specialist", "pharmacy is closed"],
    "roleplay_rubric": [
      { "criterion": "completed all sub-steps", "type": "required" },
      { "criterion": "used symptom formula correctly", "type": "required" },
      { "criterion": "understood dosage (verified by a comprehension turn)", "type": "required" },
      { "criterion": "asked a clarification question when needed", "type": "required" },
      { "criterion": "th / final consonants / numbers intelligible", "type": "pronunciation" },
      { "criterion": "register stayed polite", "type": "required" },
      { "criterion": "recovered from an off-script curveball", "type": "stretch_b1" }
    ]
  },
  "register_culture_note": {
    "en": "string",
    "th": "string",
    "do_dont": [
      { "avoid": "Give me strong medicine", "prefer": "What treatment do you recommend?" }
    ],
    "thai_cultural_note": "string"
  },
  "can_do_checkpoints": [
    { "cefr": "A2", "statement": "I can make an appointment and check in." }
  ],
  "gamification": {
    "xp_per_substep": true,
    "unlocks": ["pharmacy"],
    "sound_meters": ["th", "final_consonants"]
  }
}
```

---

## 4. The generation prompt

Run this in Claude Code with the registry entry and the flagship file both in context.

> **System / instruction:**
>
> You are an English-education content designer building situational speaking lessons for **Thai adult learners** (CEFR A1–B2). You produce one scenario unit as a single JSON object conforming exactly to the provided schema.
>
> **Non-negotiables:**
> 1. **Match the benchmark.** The attached `flagship-unit-medical-centre.md` is the quality bar for depth, realism, and Thai-specific targeting. Do not produce anything thinner.
> 2. **Function over grammar.** Every element serves a real can-do goal. Grammar (e.g. present perfect for duration) is introduced only where the function needs it, never taught abstractly.
> 3. **Thai L1 targeting is mandatory and scenario-motivated.** Use only the `sound_targets` in the registry entry, and drill each one *inside* dialogue and roleplay where getting it wrong has a real cost. Populate `why_it_matters_here` with a concrete consequence.
> 4. **Span the levels.** Provide an A1/A2 scripted version and a B1 off-script version of the roleplay. The A2→B1 line is: A2 stays in short scripted exchanges; B1 enters unprepared and copes with the unexpected.
> 5. **Spiral.** Explicitly reuse language from the `recycles` list; note it in `chunk_drills.spiralled_grammar` or dialogue.
> 6. **Localise to Thailand.** Use the `local_context` items (BTS/MRT, 7-Eleven, Grab, sois, immigration offices, hospital vs clinic) so scenarios feel real, not imported from a US textbook.
> 7. **Register + culture.** Always include a `do_dont` grounded in real intelligibility/politeness failures, and a `thai_cultural_note` that flags a genuine cultural difference (e.g. proactive symptom reporting, direct questions being acceptable).
> 8. **Natural language only.** Dialogues must sound like real speech, not textbook sentences. Keep learner-produced lines short and repeatable ("rehearse out loud until automatic").
>
> **Input:** `{{registry_entry}}`
> **Output:** one JSON object per the schema. No prose outside the JSON.

---

## 4b. Rules added by device testing (2026-08-23) — these are enforced in code

`backend/generate_unit.py` implements this spec. Everything below came out of Step 0 and Step 2
testing and is **enforced by `validate()`**, which fails loudly and never auto-fixes. Full evidence
in `spike/README.md` §6b–6e.

| Rule | Why |
|---|---|
| **`scoring_method` on every sound target** | Not all sounds can be measured the same way |
| `th` → **`minimal_pair`** | Phoneme scoring for /θ/ returned **61–100 across six flawless native takes**. Unusable. Score by word recognition of real minimal pairs instead |
| `word_stress`, `intonation`, `weak_forms` → **`unscored`** | The vendor returns prosody data for **en-US only**. These are taught and drilled but never metered — better than a number that means nothing |
| everything else → `phoneme` | Final consonants, clusters and `/r/`–`/l/` scored a stable 100 across six native voices |
| **minimal_pairs of real words on every target** | Word-level detection is the fallback whenever a number is untrustworthy — which testing showed is often |
| **A2 dialogue 6–12 lines; B1 dialogue 14–22** | A tester said "the conversation is a bit too short". A thin B1 is the most common generation failure |
| **shadow_focus_lines: 4 per dialogue, under 8 words, each naming its `targets`** | Billed per second of audio and drilled to automaticity, so short and repeatable. `targets` is what the coverage check reads |
| **Learner lines sayable by a nervous beginner** | A lower-proficiency speaker's *best effort* scores ~58 where a proficient one scores 67. Write for 58 |
| **Thai left null except the registry's `title_th`** | Invented Thai is unverifiable. `translate.py` drafts, a native speaker reviews (`mark_reviewed.py`) |

**Two things the score does NOT measure**, both of which shape content design:

- **Numeric scores compress at low proficiency.** 67 (proficient) vs 58 (learner's best effort) is
  not enough spread to build a meter on. **Error flags** discriminated cleanly with zero false
  positives — so units are designed around detectable word-level errors, not score deltas.
- **A rushed take measures anxiety, not articulation.** A tester hurrying to match a fast persona
  mispronounced the hardest phrase in the unit. Personas must give time back, never fill silence,
  and ask for an unclear word again rather than guessing past it.

---

## 5. QA checklist (gate before publishing)

Automated checks (cheap, run on every unit):
- ☐ Valid JSON, all required schema fields present and non-empty.
- ☐ `cefr_range` has ≥ 2 levels; a B1 curveball list is non-empty.
- ☐ Every `sound_target` from the registry appears in `sound_target_box` **and** in at least one `shadow_focus_line` or roleplay curveball.
- ☐ `recycles` items are actually referenced somewhere.
- ☐ `roleplay_rubric` contains all four `required` criteria + the pronunciation one.
- ☐ Thai fields (`title_th`, `note_th`, culture note `th`) are present and actually in Thai.

Human spot-check (sample ~1 in 5, plus every Tier 2/3 unit):
- ☐ Do the dialogues sound like a real person would say them?
- ☐ Is the sound target genuinely stressed by this scenario, or bolted on?
- ☐ Is the cultural note true and useful, not a stereotype?
- ☐ Would a nervous Thai beginner actually be able to complete the A1/A2 pass?

---

## 6. Sound → scenario map (author's reference for filling `sound_targets`)

Pick targets from the scenario's real phonetic demands:

| Scenario | Primary sound targets | Killer example |
|---|---|---|
| Asking directions | `/r/–/l/`, `str-` cluster, final consonants | **left / right**, straight, turn |
| Transport / tickets | clusters, final consonants | platform, flight, ticket, next stop |
| Shopping / market | numbers (13/30), final consonants | price clarity, "fifteen/fifty baht" |
| Ordering food | final consonants, `th` | rice/lice, "with", "smoothie" |
| Medical centre | `th`, final consonants, `/r/–/l/`, numbers | throat, three times, allergic |
| Job interview | word stress, weak forms | "REcord" vs "reCORD", "manage**ment**" |
| Meetings | word stress, intonation (questions) | rising vs falling for yes/no vs wh- |
| Phone calls | everything, no visual support | spelling names, numbers, "could you repeat" |

---

## 7. Build order

1. Generate **Tier 1** first (5 scenarios) — this is your MVP content set.
2. Hand-review all five against the benchmark; fix the prompt where output drifts.
3. Only then batch **Tier 2–4**. The prompt is stable by then, so these go faster.
4. Feed `roleplay_rubric` + `ai_persona` + `b1_curveballs` straight into the AI roleplay engine (the same scenario-persona-rubric shape MockPatient already runs on — reuse that machinery rather than rebuilding it).
