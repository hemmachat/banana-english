# Flagship Scenario Unit — "At the Medical Centre"

**This is the quality benchmark.** Every generated unit must match the depth, structure, and Thai-specific targeting shown here. Medical was chosen deliberately: it is high-stakes, register-sensitive, phonetically demanding for Thai speakers, and has a clean predictable sub-structure — if the generator can produce this well, it can produce the easier scenarios.

---

## 1. Unit metadata

| Field | Value |
|---|---|
| `scenario_id` | `medical_centre` |
| `title_en` | At the Medical Centre |
| `title_th` | ที่คลินิก / ที่โรงพยาบาล |
| `tier` | 2 — Higher-stakes life admin |
| `cefr_range` | A2 → B1 (with an A1 on-ramp) |
| `prerequisites` | `greetings_small_talk`, `phone_calls_basics` (spiralled in) |
| `recycles_language_from` | numbers, time/dates, "How much?", "Excuse me…" |
| `sound_targets` | `th` (θ/ð), final consonants, `/r/–/l/`, number clarity |
| `register` | Formal / polite |
| `estimated_minutes` | 18–22 per level pass |

---

## 2. Scenario decomposition (the fixed sub-steps)

A medical visit is a predictable sequence. Each sub-step is its own mini-goal so the learner always knows where they are:

1. **Book the appointment** (often by phone — hardest, no body language)
2. **Check in** at reception
3. **Describe symptoms** to the doctor
4. **Understand the doctor** (questions, diagnosis, instructions)
5. **Ask about the medicine / next steps** (dosage, pharmacy, follow-up)

The unit walks all five. The roleplay stage stitches them into one continuous encounter.

---

## 3. Thai L1 sound target box (drilled *inside* this scenario)

> This scenario is unusually loaded with the English sounds Thai speakers struggle with. Getting these wrong here isn't just an accent issue — a dropped final consonant on a number can change a dose.

- **`th` (/θ/ and /ð/):** throat, teeth, mouth, breathe, three, month, "this," "the." Thai speakers tend to say `t/d/s` instead. → **Minimal pairs:** *three / tree*, *teeth / teet*, *mouth / mout*, *breathe / breeze*.
- **Final consonants:** cough, chest, back, rash, cold, sick, hurt, sharp, eight, five. Thai final consonants are unreleased, so these vanish. → **Drill:** *bag / back*, *sick / sic*, *hurt / her*.
- **`/r/ vs /l/`:** allergic, prescription, pill, relief, refer, throat is clear but *"allergic to penicillin"* stacks both. → **Minimal pairs:** *right / light*, *fry / fly*.
- **Number clarity (final + stress):** thirteen vs thirty, fifteen vs fifty — critical for dosage and pain scale. → **Drill:** "three **times** a day," "for **eight** days," "**twice** a day."

Each appears again in the shadowing and roleplay scoring below — the sound isn't a separate lesson, it's judged where it matters.

---

## 4. Stage-by-stage content

### Stage 1 — Warm-up & vocabulary preview
Taught with audio + image, grouped for memory.

**Symptoms:** fever, cough, sore throat, headache, stomachache, rash, dizzy, tired/run-down, short of breath.
**Body parts:** throat, chest, back, stomach, head, ear, tooth/teeth.
**Places & people:** clinic, hospital, pharmacy, reception, doctor, nurse, appointment.
**Actions/things:** prescription, medicine/pills, blood test, X-ray, injection, dosage.

*Micro-check:* tap the image that matches the audio word (final-consonant words like "cough/cold/chest" grouped to force the contrast).

### Stage 2 — Model dialogue (hear → shadow, scored on sound targets)

> **A2 model — the standard flu visit**
> **Doctor:** Good morning. What brings you in today?
> **Patient:** I have a fever and a cough. My throat is sore.
> **Doctor:** How long have you had these symptoms?
> **Patient:** For three days.
> **Doctor:** Let me listen to your chest. … You have the flu. Take this medicine twice a day for five days, and rest.
> **Patient:** Thank you, doctor. Where is the pharmacy?

*Shadowing focus lines* (scored): "My **th**roat is sore," "For **three** days," "**twice** a day for **five** days." These pack `th`, number clarity, and final consonants into three short lines.

### Stage 3 — Chunk drills (the reusable phrase patterns)

The high-leverage formulas, drilled to automaticity:

- **Symptom formula A:** *I have (a) ___* → "I have a fever," "I have a headache."
- **Symptom formula B:** *My ___ hurts / aches* → "My back hurts," "My head aches."
- **Location + type + severity + timing** (the doctor's mental checklist):
  - Location: "It hurts here / in my chest / on my left side."
  - Type: "It's a sharp / dull / aching pain."
  - Severity: "It's about a seven out of ten."
  - Timing: "It started three days ago / It comes and goes."
- **Duration → present perfect** (spiralled grammar, taught functionally): "I've had this cough **for** two days," "I've been feeling dizzy **since** yesterday."
- **Asking about medicine:** "How often do I take this?" / "How many times a day?" / "With food?" / "Any side effects?"
- **Clarification (recycled everywhere):** "Sorry, could you say that again?" / "Could you write it down?" / "What does ___ mean?"

### Stage 4 — Comprehension / listening (understand the other side)

Learner hears the doctor/receptionist and must extract the key fact. Includes the **phone-booking variant** (no visuals, faster speech) because it's the hardest channel.

*Sample items:*
- Audio: "Take one pill three times a day for seven days." → **Q:** How many pills per day? (3) How many days? (7)
- Audio (phone): "We can see you tomorrow at 10:30, or Thursday at 2." → **Q:** What's the earliest time?
- Audio: "You'll need a blood test before we prescribe anything." → **Q:** What happens first?

Number-discrimination items (thirty/thirteen, fifty/fifteen) are deliberately included — the same contrast trained in the sound box.

### Stage 5 — Guided roleplay (scaffolded)

Learner plays the patient through all five sub-steps with hints available. Sentence frames appear on screen; a "give me a hint" button offers the next chunk. Learner speaks; app scores pronunciation on the target sounds and checks the required chunk was used.

*Prompt flow:* Book by phone → check in ("I have a 10:30 appointment with Dr. …") → describe symptoms using the formula → answer "How long?" and "How severe?" → ask about the medicine.

### Stage 6 — Free roleplay with AI (the differentiator, off-script)

Judgment-free voice conversation with an AI doctor persona. **This is where levels diverge:**

- **A2 pass:** the doctor stays on the standard script; learner just has to produce, not adapt.
- **B1 pass:** the doctor goes off-script — asks an unexpected follow-up ("Any allergies? Are you on any other medication? Has this ever happened before?"), or the learner must handle a curveball (the pharmacy is closed; a referral to a specialist). Learner must ask for clarification, cope, and keep the conversation going.

**Roleplay scoring rubric** (this object is reused by the AI engine — see generation spec):
- ✅ Completed all five sub-steps
- ✅ Used symptom formula correctly (location/type/severity/timing)
- ✅ Understood dosage instructions (verified by a comprehension turn)
- ✅ Asked at least one clarification question when needed
- ✅ Pronunciation: `th`, final consonants, and numbers intelligible
- ✅ Register stayed polite/formal
- ⭐ Stretch (B1): recovered from the off-script curveball without breaking down

### Stage 7 — Register & culture note (shown in Thai + English)

- **Medical English is formal.** Use "Could you…?" and "I'd like to…," not bare commands.
- **Do / Don't** (real intelligibility + safety):
  - ✗ "Give me strong medicine." → ✓ "What treatment do you recommend?"
  - ✗ "I'm allergic to antibiotics." (a whole class) → ✓ "I'm allergic to penicillin." (name the specific drug + reaction: rash / swelling)
  - ✓ It's fine to say "That hurts," "Can I sit down?", "Could you speak more slowly?" — doctors expect patients to speak up.
- **Cultural note for Thai learners:** in many English-speaking healthcare settings you're expected to describe symptoms proactively and ask questions directly; waiting to be asked (or under-reporting to avoid being troublesome) can lead to worse care. Being specific is polite, not rude.

---

## 5. Can-do checkpoints (unit exit criteria)

The learner "passes" the unit when they can tick these — shown as a progress card:

- ☐ **A2:** I can make an appointment and check in.
- ☐ **A2:** I can describe common symptoms using "I have…" and "My ___ hurts."
- ☐ **A2:** I can understand simple dosage instructions.
- ☐ **B1:** I can describe pain by location, type, severity, and timing.
- ☐ **B1:** I can answer unexpected follow-up questions and ask for clarification.
- ☐ **Sound:** My `th`, final consonants, and numbers are intelligible in this context.

---

## 6. Gamification hooks for this unit

- XP per completed sub-step (so a long scenario still gives frequent wins).
- A per-sound accuracy meter that visibly climbs (`th`: 62% → 88%).
- "Streak" credit counts **minutes spoken**, not lessons tapped.
- Unlock: completing "Medical Centre" unlocks "Pharmacy" (spirals the same medicine/dosage language).
