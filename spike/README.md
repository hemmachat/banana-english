# Step 0 spike — is Azure Pronunciation Assessment good enough?

One question: **when a Thai speaker drops a final consonant, does Azure report a pronunciation error
on the right word and phoneme — or does it just recognise a different word and move on?**

Everything in Banana English's retention engine (per-sound accuracy meters, adaptive drilling) needs the first
answer. If it's the second, the product needs rethinking. Budget: one afternoon, about $0.

---

## 1. Set up Azure (15 min)

1. portal.azure.com → **Create a resource** → search **Speech** → Create.
2. Region: **Australia East**. Pricing tier: **F0 (free)** — 5 audio-hours/month, plenty for this.
3. Once deployed, **click into the Speech resource itself** (e.g. `banana-speech`) — not the resource
   group that contains it. The resource group page has no keys; its left menu shows Deployments/Policies/
   Locks. Inside the resource, left nav → **Resource Management → Keys and Endpoint** → copy Key 1.

   Or skip the portal entirely:
   ```bash
   az cognitiveservices account keys list -n banana-speech -g Banana English --query key1 -o tsv
   ```

```bash
cd spike
python3 -m venv .venv                              # Homebrew Python blocks global pip installs (PEP 668)
.venv/bin/pip install azure-cognitiveservices-speech
export AZURE_SPEECH_KEY=<your key>
export AZURE_SPEECH_REGION=australiaeast           # matches "Australia East"
```

Verified working on macOS arm64 / Python 3.14 with SDK 1.51.2. Run everything below with
`.venv/bin/python`, or `source .venv/bin/activate` once and then just `python`.

---

## 2. What to record

**8 phrases × 2 versions each = 16 short takes per person.** About 10 minutes per speaker.

For each phrase, record it **twice**: once trying to say it correctly ("correct"), once deliberately
making the listed Thai-L1 error ("wrong"). The whole test is whether Azure scores the second one
meaningfully lower.

| # | test_id | Say this | The "wrong" version | What it proves |
|---|---|---|---|---|
| 1 | `card` | **card** | drop the final /d/ — say "car" | **The critical one.** Final-consonant deletion is the single most common Thai L1 error. |
| 2 | `bulk` | **bulk billed** | "buk bin" | Consonant clusters + finals stacked — and it's the real phrase from the AU flagship unit. |
| 3 | `referral` | **referral** | "refellal" (r → l) | /r/–/l/, the killer word in the GP scenario. |
| 4 | `three` | **three times a day** | "tree times a day" | `th` → `t`. Getting dosage wrong has a real cost. |
| 5 | `left` | **turn left** | "turn reff" (l → r, drop final t) | The directions killer contrast. |
| 6 | `script` | **the script** | "de scrip" | Voiced `th` + `str` cluster + final /t/. |
| 7 | `thirteen` | **thirteen** | say "thirty" instead | Number discrimination — 13/30. |
| 8 | `garbage` | **bulk billed** | say something completely unrelated | Guards against a scorer that gives everything a decent score. |

**Who to record:**
- **3–5 Thai speakers.** Ideally real Thai Australians. If you can't get them today, imitate the errors
  yourself — it's a weaker signal but it unblocks the test.
- **No native speaker needed for the control** — generate it (below).

### The native control, without a native speaker

```bash
python3 make_controls.py recordings/
```

This synthesizes every phrase with the **en-AU neural voices** (Natasha and William) straight into
`recordings/`, correctly formatted, named so `assess.py` picks them up as two extra speakers.

Why this is a legitimate control — arguably a better one:
- A neural TTS voice *is* reference native pronunciation. That's what it was trained to be.
- It's the **same voice the product will use** for model dialogue, so "how does my take score against
  the voice I'm shadowing" is exactly the comparison the app makes.
- Free (0.5M characters/month), same Azure key, ~10 seconds to run.

**The one honest caveat:** TTS audio is *too* clean — no room noise, no mic colouring, no breath. It
gives you the **ceiling**, which is what a control is for, but it won't tell you how a real native
sounds through a phone mic. If you want that too, play the TTS out of a laptop speaker and re-record it
on the phone alongside the human takes — 2 minutes, and it isolates how much your recording setup costs
you in score.

**While they're there, ask the other Step 0 question** (see `PLAN.md`): *"the government gives free
unlimited English classes — why would you pay for this instead?"* That answer matters as much as the scores.

---

## 3. How to record

Phone voice memo app is fine. One file per take. Quiet room, phone ~20cm away, normal speaking volume.

Name each file **`<speaker>__<test_id>__<correct|wrong>.wav`**, e.g. `nok__card__wrong.wav`.
Two underscores between parts — the script splits on them.

Voice memos give you `.m4a`, and Azure needs 16 kHz mono PCM WAV. Convert the lot:

```bash
brew install ffmpeg          # if you don't have it
mkdir -p recordings
for f in raw/*.m4a; do
  ffmpeg -i "$f" -ar 16000 -ac 1 -c:a pcm_s16le "recordings/$(basename "${f%.m4a}").wav"
done
```

---

## 4. Run it

```bash
.venv/bin/python assess.py --selftest        # parser check — no Azure calls, no key needed
.venv/bin/python make_controls.py recordings/   # native-speaker baseline via en-AU TTS
.venv/bin/python assess.py recordings/
```

Output, one line per take plus a delta line per pair:

```
speaker    test       ver      PronScore target ph  heard / word errors
----------------------------------------------------------------------------------------------------
nok        card       correct       92.0      95.0  'Card.' -
nok        card       wrong         61.0      12.0  'Car.' card:Mispronunciation
           card       delta         31        PASS
```

---

## 5. How to read the result

**The card/car test — look at three things on the `wrong` row:**

| What you see | Meaning |
|---|---|
| `word errors` says **`card:Mispronunciation`** and the **target ph** score is low (<40) | ✅ **This is the answer you want.** Azure located the dropped /d/ inside the intended word. Per-sound meters will work. |
| `word errors` says **`card:Omission`** and `heard` is `'Car.'` | ⚠️ It gave up on the word rather than scoring the phoneme. Meters still possible but coarser — you'd be counting omissions, not phoneme accuracy. Workable, weaker. |
| PronScore barely moves (delta < 15, printed as `*** TOO CLOSE ***`) | ❌ The scorer doesn't discriminate the error you built the product around. Stop and evaluate Speechace, or rethink the sound-meter feature. |

**Also check:**
- **`garbage` must score low.** If unrelated speech still scores 70+, the number is decorative and you
  can't show it to learners as feedback.
- **The TTS control takes should score high** (85+). If they don't, something is wrong with the setup
  or the reference text — fix that before drawing any conclusion about the human takes.
- **The gap between the TTS control and a human "correct" take** tells you how much of a score drop is
  just microphone and room, not pronunciation. That's the noise floor you have to design the learner's
  score display around — don't show a learner 78/100 when 78 is what a good take through a phone mic
  scores.
- **Consistency across speakers.** One speaker's odd result is noise; the same pattern in 3+ is signal.

---

## 6. Two things to check while you're in there

- **Latency.** Time one `assess()` call end to end. Over ~1.5s and live shadowing will feel dead —
  which pushes Step 2 toward the browser streaming SDK. (Note this is file-based, so it's a floor,
  not the real number.)
- **Prosody is `en-US` only.** Azure does not return `ProsodyScore` for `en-AU`. The registry's
  `word_stress` and `intonation` sound targets therefore have **no scorer** in the launch locale.
  Options: score those drills against `en-US` while everything else runs `en-AU`, or drop those two
  targets from the AU launch. Decide it now — it affects the registry, not just the code.
  (`BANANA_LOCALE=en-US .venv/bin/python assess.py recordings/` to compare.)

---

## 6b. Confirmed on first run (2026-08-23), before any human recordings

Running the TTS controls through the assessor established three things:

1. **The pipeline works.** Azure segments phonemes correctly (`card` = 3, `three times a day` = 10) and
   returns per-phoneme accuracy scores.
2. **`en-AU` returns phoneme scores but empty phoneme *labels*** (`"Phoneme": ""`), and empty syllable
   labels too. Scores and offsets are there; names are not. Hence positional targeting `(word_index,
   phoneme_index)` in `assess.py`. To tell a learner *"your /d/ was weak"* you need the phoneme sequence
   for each reference line — generate it at content-build time (CMUdict) and store it with the unit.
3. **Most target phonemes are rock stable at 100 — `/θ/` is not scorable at all.**
   Six en-AU neural voices, identical perfect input, target phoneme score:

   | Target | Six-voice spread | Usable? |
   |---|---|---|
   | final `/d/` — "card" | 100, 100, 100, 100, 100, 100 | ✅ |
   | final `/t/` — "turn left" | 100 ×6 | ✅ |
   | `/k/` cluster — "bulk billed" | 100 ×6 | ✅ |
   | final `/n/` — "thirteen" | 100 ×6 | ✅ |
   | final `/t/` — "the script" | 99–100 | ✅ |
   | `/r/` — "referral" | 91–100 | ✅ |
   | **`/θ/` — "three"** | **80, 100, 61, 73, 87, 78** | ❌ |

   Azure even returned `three:Mispronunciation` **on one of its own neural voices**. A 39-point spread on
   flawless input means no `th` meter can be built from the phoneme score.

   **The workaround costs nothing:** `three`/`tree` and `teeth`/`teet` are minimal pairs of *real words*,
   so a Thai speaker saying "tree" gets transcribed as "tree" and caught by word-level miscue detection —
   far more robust than a phoneme score. The generation spec already emits `minimal_pairs` for every
   sound target. **Score `th` by word recognition; score everything else by phoneme.**

4. **Drive meters from the targeted phoneme, never from `PronScore`.** One voice (Carly) scored low on
   every utterance — card 82, referral 79.6, thirteen 81.4 — while its *target phonemes* still read 100.
   Utterance-level score tracks voice and speaking style; the targeted phoneme does not.

5. **Re-run `make_controls.py` whenever content is generated** and store the resulting ceilings. It is a
   permanent calibration fixture, not spike scaffolding.

---

## 6c. First human run (2026-08-23, n=1 — native Thai speaker, high English proficiency)

**Result: PASS on the question that matters.**

| Test | correct → wrong (PronScore) | target phoneme | Word flag | Verdict |
|---|---|---|---|---|
| **card** (final /d/) | 80.2 → **9.8** | 100 → 67 | `card:Mispronunciation`, still heard as "Card." | ✅ **the decisive one** |
| bulk billed (clusters) | 97.2 → 50.6 | 100 → **9** | `billed:Mispronunciation` | ✅ |
| referral (/r/–/l/) | 87.4 → 10.8 | 94 → 78 | `referral:Mispronunciation` | ✅ |
| thirteen (numbers) | 79.6 → 11.6 | 100 → 64 | `thirteen:Mispronunciation` | ✅ |
| garbage guard | unrelated speech → **0.0**, `Omission` | — | — | ✅ score is meaningful |
| turn left | 89.8 → 97.0 (*wrong scored higher*) | 100 → 84 | none | ⚠️ phoneme caught it, PronScore didn't |
| the script | 98.8 → 98.8 (identical) | 100 → 100 | none | ⚠️ likely no error in the take |
| three (`/θ/`) | 94.6 → 94.6 (identical) | 72 → 74 | none | ❌ as predicted — `th` unscorable |

**Azure recognised "card" as *card* while scoring the dropped /d/ as an error.** It did not silently
substitute "car". This is what makes per-sound accuracy meters possible, and it is the finding that
unblocks Step 1.

**These are genuine Thai L1 articulations**, not an imitation by a non-Thai speaker — so the errors carry
real Thai articulatory habits (unreleased final stops, cluster reduction, `/r/`–`/l/` substitution) and
the discrimination result holds for the actual target population's sound system.

**What this run also gives us: the proficient-Thai-speaker band.** Correct takes scored 79.6–98.8 against
a TTS ceiling of 100 — that is what *good* Thai-accented English scores. Useful for setting expectations,
and it means a learner-facing "you scored 85" must be read against ~80–98, not against 100.

**Caveats that remain:**
- n=1, and a **high-proficiency** speaker. The acute-need segment (the 16.7% who speak English "not well
  or not at all") differs in a way that matters: their *correct* takes will score far lower, compressing
  the gap between a good attempt and a poor one. **The open question is no longer "can it detect a Thai
  error" — it's "does it still discriminate when the speaker's baseline is 55, not 85?"** That needs
  lower-proficiency speakers specifically, not just more speakers.
- `script` and `three` returned identical scores for both takes — most likely those "wrong" recordings
  didn't contain the intended error. Re-record those two.
- `turn left` is the clearest evidence yet for the rule in §6b item 4: **PronScore moved the wrong way
  while the target phoneme moved the right way.** Never drive a meter from PronScore.

---

## 6d. Second speaker (2026-08-23) — the low-proficiency case

A second native Thai speaker (`aon`, lower English proficiency), *correct* takes only. This answers the
question left open in §6c.

**Finding 1 — `PronScore` is unusable on short drills. Use `AccuracyScore`.**

| | Accuracy | Fluency | Completeness | PronScore |
|---|---|---|---|---|
| hemm "card" (0.89s) | 67 | 100 | 100 | **80.2** |
| aon "card" (0.53s) | 58 | **0** | **0** | **11.6** |

The real pronunciation gap is 9 points; PronScore differs by 69. Fluency and Completeness collapse on a
short or tightly-trimmed clip and have nothing to do with pronunciation. **Show `AccuracyScore`; treat
`Fluency`/`Completeness` of 0 as "recording too short", not as a bad attempt.** The client must also
guard against clipping — capture a moment of lead-in and lead-out.

**Finding 2 — numeric scores compress at low proficiency, but the error flag does not.**
A proficient speaker's good "card" scores 67; a lower-proficiency speaker's *best effort* scores 58.
Nine points is not enough to build a meter on. But `aon` was flagged `card:Mispronunciation` and
`turn:Mispronunciation` on natural speech while `hemm` was not.

> **Build sound meters on error-flag rate (what fraction of attempts flag `Mispronunciation` on the
> target word), not on average score.** Binary, robust, and immune to the compression. This is the same
> conclusion the `/θ/` result forced: word-level detection beats numeric scoring.

**Re-scored on `AccuracyScore`, the numeric deltas are far weaker than `PronScore` implied** (the §6c
table was reading inflated PronScore values — corrected here):

| test | correct → wrong (Accuracy) | delta |
|---|---|---|
| bulk billed | 96 → 39 | ✅ 57 |
| referral | 79 → 54 | ✅ 25 |
| card | 67 → 49 | ⚠️ 18 (PronScore claimed 70) |
| thirteen | 66 → 58 | ❌ 8 |
| turn left | 83 → **95** | ❌ wrong scored *higher* |
| the script / three | no change | ❌ |

**Error flags over the same 21 takes:**

| | flags |
|---|---|
| hemm, 7 correct takes (proficient) | **0** — no false positives |
| hemm, wrong takes | 4 of the 5 that actually contained an error |
| aon, 7 correct takes (lower proficiency) | 2 — `card`, `turn`, both genuine Thai L1 errors |

Zero false positives on good speech; fires on real errors at natural severity for both speakers. The
flag is the signal. The number is decoration.

**Finding 3 — the scorer finds real Thai L1 errors in natural speech.** `aon`'s flags landed exactly
where Thai L1 predicts: final consonant in "card", `/r/` in "turn". No performance required.

**Finding 4 — never show the raw number to this user.** `aon`'s best attempt at "card" would display as
**11.6/100**. For an audience whose documented barrier is fear of losing face, that number would do real
damage. The score shown must be calibrated, artifact-guarded, and framed as progress — see
`docs/brand/brand-guide.md`.

---

## 6e. From app testing (2026-08-23) — speed, and what it costs

A tester using the built app rushed to match the GP's speaking pace and **mispronounced "bulk billed"**
as a result. Two separate lessons:

1. **Model audio at default rate was called "unrealistic"** — real Australians speak faster, so the
   catalogue now renders at `+18%` via SSML prosody.
2. **But faster input created imagined time pressure on output**, and the pronunciation broke exactly
   on the phrase the unit exists to teach. The fix is not slower audio — it is removing the deadline:
   a patient persona, a long mic cutoff, and telling the learner explicitly they can take their time.

This matters for scoring too: a rushed take measures anxiety, not pronunciation. Any future analysis
that compares takes should note whether the learner was under conversational pressure at the time.

---

## 7. What "pass" means

Ship-forward if: the `card` delta is ≥15 with a low target-phoneme score, `garbage` scores low, and
natives score high. Then Step 1 in `PLAN.md` starts.

Anything else is a finding worth more than a week of building — write down what you saw and bring it back.
