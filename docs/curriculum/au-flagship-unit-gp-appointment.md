# Australian Flagship Unit — "Seeing a GP (Medicare)"

**The quality benchmark for locale content.** This is the Australian port of the generic medical flagship. It shows exactly how a Layer C locale scenario should look: the pedagogical spine and Thai L1 sound targets are identical to the generic unit, but the *system* — Medicare, bulk billing, GP referral gatekeeping, "scripts," pathology — is fully Australian. Any generated `en-AU` health unit must match this depth and this local accuracy.

---

## 1. Unit metadata

| Field | Value |
|---|---|
| `scenario_id` | `au_gp_appointment` |
| `locale` | `en-AU` |
| `title_en` | Seeing a GP (Medicare) |
| `title_th` | การพบแพทย์ทั่วไป (เมดิแคร์) |
| `model_accent` | Australian English (TTS + pronunciation targets) |
| `tier` | 2 — Higher-stakes life admin |
| `cefr_range` | A2 → B1 (A1 on-ramp) |
| `prerequisites` | `greetings_small_talk`, `phone_call_basics`, `au_enrol_medicare` |
| `recycles_language_from` | numbers, time/dates, "How much?", describing symptoms |
| `sound_targets` | `th`, final consonants (+ clusters), `/r/–/l/`, number clarity |
| `register` | Casual-polite (AU norm: first names, direct) |

---

## 2. Scenario decomposition (the AU-specific sequence)

An Australian GP visit has a predictable shape that differs from a generic clinic in three places (marked ★):

1. **Book the appointment** — by phone or online; "Do you have anything today?"
2. ★ **Check in at reception** — "Have you got your Medicare card?" / **"Is it bulk billed?"** (the money question — normal and expected)
3. **Describe symptoms** to the GP — same symptom formulas as the generic unit
4. ★ **Understand the GP** — the GP is a **gatekeeper**: diagnosis may end in a **referral** to a specialist, a **script** (prescription), or a **pathology** request (blood test)
5. ★ **Next steps** — take the script to **the chemist**; go to a **pathology** collection centre; book the specialist (needs the referral to claim Medicare)

The ★ items are what make this a locale unit rather than the generic one.

---

## 3. Thai L1 sound target box (drilled inside the AU context)

> Same Thai first-language errors as the generic medical unit — but note that several high-frequency *Australian* words are themselves brutal for Thai speakers. "Bulk billed" alone stacks two consonant clusters and two final consonants.

- **`th` (/θ/, /ð/):** throat, teeth, mouth, three times, months, "this / the." → *three/tree, teeth/teet, mouth/mout.*
- **Final consonants (+ clusters):** **bulk billed** (/lk/ + /ld/), script, card, test, cough, back, rash, script. Thai unreleased finals make these vanish. → *card/car, test/tes, script/scrip.*
- **`/r/ vs /l/`:** **referral** (r…r…l — the killer word), prescription, allergic, pathology, pharmacy. → *referral, allergic to penicillin.*
- **Number clarity (final + stress):** thirteen/thirty, dosage ("three times a day"), Medicare number, appointment times. → *"twice a day for five days."*

Each reappears in the shadowing and roleplay scoring below.

---

## 4. Stage-by-stage content

### Stage 1 — Warm-up & vocabulary (AU-flavoured, audio + image)

**People/places:** GP, reception, the clinic/surgery, the chemist, pathology.
**Medicare words:** Medicare card, bulk billed, gap fee / out-of-pocket, referral.
**Symptoms/body:** fever, cough, sore throat, rash, chest, back, tired/run-down.
**Outcomes:** script (prescription), blood test, referral, follow-up.

*Micro-check:* match the AU term to the meaning ("script" → prescription; "bulk billed" → no cost to you; "referral" → letter to see a specialist).

### Stage 2 — Model dialogue (hear in an AU accent → shadow, scored)

> **A2 model — a standard GP visit**
> **Reception:** Hi there! Have you got your Medicare card?
> **Patient:** Yes, here you go. Is it bulk billed?
> **Reception:** It is, no charge today. Take a seat, the doctor won't be long.
> *(later)*
> **GP:** G'day, what brings you in today?
> **Patient:** I've had a sore throat and a fever for three days.
> **GP:** Let's have a look. … It's a throat infection. I'll write you a script — take it twice a day for five days.
> **Patient:** Thanks. Where's the nearest chemist?

*Shadowing focus lines* (scored): "Is it **bulk billed**?", "for **three** days," "take it **twice** a day," "the nearest **chemist**." These pack clusters, `th`, final consonants, and numbers into short, repeatable lines.

### Stage 3 — Chunk drills (reusable patterns, AU-specific added)

Generic symptom formulas (recycled from the core medical unit):
- *I have (a) ___* → "I have a fever." / *My ___ hurts* → "My throat hurts."
- Location + type (sharp/dull) + severity (0–10) + timing ("for three days," "it comes and goes").
- Duration → present perfect: "I've had this cough **for** two days."

**AU-specific chunks (the locale layer):**
- **"Is it bulk billed?"** / "Is there a gap fee?" / "How much is the appointment?"
- "Do I need a **referral**?" / "Can you refer me to a specialist?"
- "Can you write me a **script**?" / "Is there a generic?"
- "Do I need a **blood test**?" / "Where's the pathology?"
- Clarification (recycled everywhere): "Sorry, could you say that again?" / "Could you write it down?"

### Stage 4 — Comprehension / listening (AU accent; includes phone booking)

- Audio (reception, phone): "We've got nothing till this arvo — is 3:15 okay?" → **Q:** What time is offered?
- Audio (GP): "Take one tablet three times a day for seven days." → **Q:** How many per day? For how long?
- Audio (GP): "I'll refer you to a skin specialist — you'll need this letter to book in." → **Q:** What do you need to bring to the specialist?
- Number-discrimination items (thirty/thirteen, fifteen/fifty) — same contrast as the sound box.

### Stage 5 — Guided roleplay (scaffolded, all five sub-steps)

Learner plays the patient with on-screen frames and a hint button:
book by phone → check in and ask "is it bulk billed?" → describe symptoms with the formula → answer "how long?"/"how bad?" → understand the outcome (script / referral / test) → ask where to go next.

### Stage 6 — Free roleplay with AI (off-script; the differentiator)

Judgment-free voice conversation with an **Australian GP persona** (casual, warm, uses first names).

- **A2 pass:** GP stays on the standard script.
- **B1 pass (off-script curveballs):** the GP asks about allergies or current medication; refers the patient to a specialist and explains the referral/gap; orders a blood test; or the patient must handle "the clinic doesn't bulk bill — there's a $40 gap." Learner must ask for clarification, cope, and keep going.

**Roleplay scoring rubric** (reused by the AI engine):
- ✅ Completed all five sub-steps
- ✅ Asked the Medicare/bulk-billing question at reception
- ✅ Used the symptom formula correctly (location/type/severity/timing)
- ✅ Understood the outcome — script dosage OR the referral/test next-step (verified by a comprehension turn)
- ✅ Asked at least one clarification question when needed
- ✅ Pronunciation: `th`, final consonants (incl. "bulk billed"), "referral," numbers intelligible
- ✅ Register stayed appropriately casual-polite
- ⭐ Stretch (B1): coped with the off-script curveball (gap fee / referral / test) without breaking down

### Stage 7 — Register & culture note (Thai + English)

- **AU medical register is casual.** GPs often use first names and a relaxed tone ("G'day, what's up?"). Being warm and direct is normal; you don't need heavy formality.
- **The money question is expected.** Asking "Is it bulk billed?" or "Is there a gap?" is completely normal and not rude — clinics expect it.
- **The GP is the gatekeeper.** You generally can't self-refer to a specialist and claim Medicare — you need a GP referral first. Say "I'd like a referral to…" rather than trying to book the specialist directly.
- **Do / Don't** (intelligibility + safety, recycled from generic unit):
  - ✗ "Give me strong medicine." → ✓ "What treatment do you recommend?"
  - ✗ "I'm allergic to antibiotics." → ✓ "I'm allergic to penicillin." (name the drug + reaction)
- **Cultural note for Thai learners:** Australian GPs expect you to describe symptoms proactively and ask questions. Under-reporting to avoid being a bother can lead to worse care — being specific is helpful, not impolite.

---

## 5. Can-do checkpoints (unit exit criteria)

- ☐ **A2:** I can book a GP appointment and check in with my Medicare card.
- ☐ **A2:** I can ask whether the appointment is bulk billed.
- ☐ **A2:** I can describe common symptoms and understand a script's dosage.
- ☐ **B1:** I can describe pain by location, type, severity, and timing.
- ☐ **B1:** I can understand a referral or a blood-test request and ask what to do next.
- ☐ **Sound:** My `th`, final consonants ("bulk billed," "script"), "referral," and numbers are intelligible.

---

## 6. Gamification hooks

- XP per completed sub-step (booking, check-in, symptoms, outcome, next step).
- Per-sound accuracy meter (`th`, clusters) that visibly climbs.
- Streak credit = **minutes spoken**, not lessons tapped.
- Unlock: completing this unlocks `au_pharmacy_pbs` and `au_specialist_referral` (spirals the same script/referral language).

---

## 7. Notes for the locale-content author

- This unit reuses the generic medical unit's **symptom formulas, severity scale, and Do/Don't** verbatim — that's the invariant core showing through. Only the **system layer** (Medicare, bulk billing, referral, script, chemist, pathology) is new.
- When porting to **UK**: swap Medicare→NHS, bulk billed→"it's free on the NHS," chemist stays "chemist," script→"prescription," "book in with the surgery." When porting to **US**: swap to insurance/copay/in-network, "pharmacy," "prescription," and add the insurance-verification sub-step. The pedagogical spine and Thai sound targets **do not change**.
- ⚠️ AU facts written at author level — have a local (ideally a GP receptionist or recent migrant) sanity-check before shipping. ⚠️ Thai strings need native review.
