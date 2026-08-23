# Build Plan — Papaya

Read `CLAUDE.md` first, then `docs/feasibility-assessment.md` for the verified costs and market numbers
this plan assumes. Ordered by **risk retired per day of work**, not by architectural layer.
**[HUMAN]** = Claude Code cannot finish it; do the surrounding work, then stop and flag it.

---

## Where it stands — 2026-08-23

| Step | State |
|---|---|
| 0 · Speech spike | **Technical verdict GO.** Human half outstanding: lower-proficiency speakers, the AMEP question |
| 1 · Backend | **Done.** Flask + Postgres, three tables, `backend/test_api.py` green |
| 2 · Web slice | **Done and validated on a real iPhone.** No technical risks left |
| 3 · Real users | Blocked on the two Step 0 human items and the Thai review |
| 4 · Generator | Not started — and now better informed by what Step 2 revealed |
| 5 · Scale | Not started. Gamification already done early |

**The three things actually blocking progress**, none of which are code:

1. **[HUMAN]** Review the drafted Thai and set `th_status: "reviewed"` — only the founder can.
2. **[HUMAN]** Sit with 2–3 lower-proficiency Thai Australians: will they speak, and why not AMEP?
3. **[HUMAN]** Fact-check the AU claims (Medicare, bulk billing, referral validity, pathology walk-in).

**Step 2 has no technical risks left** — validated end to end on a real iPhone, mic included.

**What testing changed** (details in `spike/README.md` §6b–6e — read before touching scoring):
`/θ/` needs minimal pairs, not phoneme scoring · every phoneme has its own ceiling and it isn't 100 ·
`AccuracyScore` not `PronScore` · numeric scores compress at low proficiency but error flags don't ·
fast input is right, hurried output is not.

---

## Step 0 — Kill-or-continue speech spike — **TECHNICAL VERDICT: GO. Human half outstanding.**

Azure detects Thai L1 final-consonant errors *inside* the intended word (`card` said as "car" →
`card:Mispronunciation`, PronScore 80→10, still recognised as "card"). Clusters, `/r/–/l/`, and numbers
all discriminate cleanly. `/θ/` does not and needs word-level minimal-pair scoring instead. Full results:
`spike/README.md` §6b–6c — validated on genuine Thai L1 speech (n=1, high proficiency).
**Still outstanding: lower-proficiency Thai speakers (does it still discriminate when the baseline is 55,
not 85?), and the AMEP question.**

**→ Runnable: `spike/README.md` has the exact phrase list, recording instructions, and Azure setup;
`spike/assess.py` scores the recordings and prints a pass/fail delta per phrase.**

Everything downstream assumes pronunciation scoring works on Thai-accented English at a viable
price. Test that before building anything to hold it.

- [ ] **[HUMAN, BLOCKING STEP 3]** Sit with 3 Thai Australians — specifically **lower-proficiency** ones, the acute-need
      segment. Have them shadow a flagship line out loud off your laptop — no app, no scoring. Will they
      speak at all, in a room, in front of you? Face/shyness is the biggest untested assumption in the
      product and this costs an afternoon. Record them too: the open scoring question is whether the
      scorer still discriminates when a speaker's *correct* take scores ~55 rather than ~85.
- [ ] **[HUMAN, BLOCKING STEP 3]** Ask each of them: **"the government offers free unlimited English classes (AMEP) —
      why would you pay for this instead?"** If they can't answer, the positioning is wrong and no
      amount of engineering fixes it. This is the cheapest kill-test in the plan.
- [x] Native-speaker control: **no native speaker required** — `spike/make_controls.py` synthesizes the
      baseline with the en-AU neural voice (the same voice the product will shadow against).
- [~] Record 5 Thai speakers — **2 of 5 done** (`hemm` high-proficiency, `aon` lower-proficiency).
      `aon`'s data is the important one: their *best effort* scored 58 where `hemm`'s scored 67, which
      is what proved numeric scores compress and error flags don't. Three more would firm it up.
      Original instruction:
      *"bulk billed"*, *"referral"*, *"three times a day"*, *"turn left"*, *"the script"*.
- [x] curl Azure Pronunciation Assessment with each. Compare against 2 native recordings.
- [x] **The card/car contrast** (the make-or-break check): say "card" with the final /d/ dropped.
      Does the API report a *final-consonant error on `card`*, or does it just recognise the word "car"?
      The per-sound meters — the whole retention engine — only work if it does the former.
- [~] Latency: shadow scoring is fast enough locally, but **roleplay turns take ~3.6s** — too slow for
      real conversation. Fix by streaming the reply and speaking it as it arrives. Still unmeasured on
      mobile data. Original instruction:
      Test with the Azure **JS SDK streaming** path, since that's what Step 2 now uses.
- [ ] **Decide the prosody problem.** Azure returns `ProsodyScore` for **en-US only** — so the registry's
      `word_stress` and `intonation` sound targets have no scorer in en-AU, the launch locale. Either run
      those specific drills against en-US, or drop the two targets from the AU launch. This changes
      `scenario-registry.yaml`, not just code.
- [x] **`th` scoring method decided** (done 2026-08-23): phoneme scoring for `/θ/` is unusable (61–100
      across six perfect native takes). Score `th` via word-level minimal-pair recognition instead —
      `minimal_pairs` is already in the generation schema, so no content rework. Every other Thai target
      scores reliably by phoneme.
- [x] Answer three questions in writing: (1) does the phoneme score actually separate a dropped
      final consonant / `r`→`l` / missing `th` from a clean take? (2) does it return word offsets
      good enough for shadowing timing (if yes, **it is also the STT — don't buy a second vendor**)?
      (3) **[HUMAN]** confirm $1.32/audio-hour still holds for your region and tier.

**Exit**: a go/no-go on Azure. No-go → evaluate alternatives now, while nothing depends on it.

---

## Step 1 — Thinnest backend that serves one unit — **DONE 2026-08-23**

Running: local Homebrew Postgres 18 (no Docker needed), `backend/app.py` on :5001, one unit seeded.
`backend/test_api.py` asserts the whole loop end to end. Outstanding: `phoneme_sequence` per shadow
line (CMUdict) and the second flagship unit - neither blocks Step 2.


- [x] `backend/app.py` — single-file Flask, app factory only if config actually diverges.
      `.env.example`: `DATABASE_URL`, `ANTHROPIC_API_KEY`, `AZURE_SPEECH_KEY`.
- [x] Postgres — **local Homebrew 18, no Docker needed**. **Three tables:**
      - `units(scenario_id, locale, data jsonb, primary key (scenario_id, locale))`
        — a unit is a document, read whole. Do not shred it into 7 tables.
      - `attempts(id, user_id, scenario_id, stage, sound_target, score, seconds_spoken, raw jsonb, created_at)`
        — the product's brain. Streaks (minutes spoken), XP, and per-sound accuracy meters are all
        `GROUP BY` over this. No separate progress/streak/xp tables.
        **Store the score relative to the phoneme's calibrated ceiling, not the raw Azure number**, and
        record *which method* scored it — confirmed in Step 0 (`spike/README.md` §6b): final consonants,
        clusters and `/r/` score a stable 100 across six native voices, but `/θ/` ranges 61–100 on
        flawless input. `th` must be scored by **word-level minimal-pair recognition**, everything else
        by phoneme. Never drive a meter from utterance-level `PronScore`.
      - `users(id uuid, locale, tz, created_at)` — device-generated uuid, no auth until there's money.
        `tz` is not optional: streak day-boundaries break the first time someone flies to Thailand,
        which this user base does constantly.
- [x] Endpoints: `GET /scenarios?locale=`, `GET /scenarios/<id>` (resolve `global ∪ locale`, pack wins),
      `POST /attempts`, `GET /me/progress`.
- [x] Seed content — **`au_gp_appointment` only**; the generic `medical_centre` flagship is not converted
      and can wait for the Step 4 generator rather than being hand-done twice.
- [ ] **STILL OPEN** — store, per shadow line: the **phoneme sequence** (CMUdict, computed at build time — `en-AU` returns
      phoneme scores with empty labels, so position is the only way to map a score to a sound) and the
      **TTS ceiling** per target phoneme (from `spike/make_controls.py`). Both are content-build outputs,
      not runtime lookups.
- [~] **[HUMAN]** Thai now **drafted** for all vocabulary and both dialogues (`backend/translate.py`,
      tagged `th_status: draft_unverified`, shown in the UI behind a DRAFT badge). Needs the founder to
      correct and mark `reviewed`. Original instruction: (2 files,
      ~1 hour of their time). This has to happen *here*, not at Step 3: the flagships are the few-shot
      benchmark the generator imitates, so bad Thai in them propagates into all ~130 generated units.

**Exit**: `curl` returns the AU flagship unit merged for an `en-AU` user; an attempt logs and appears
in a per-sound accuracy query.

---

## Step 2 — Vertical slice as a **web app** — **DONE 2026-08-23**

Running at `http://localhost:5001`. Vocab + shadow stages work end to end: hear the model audio →
browser mic → Azure JS SDK → word-level feedback + calibrated score → `POST /attempts` → sound meters.

Content build steps, both idempotent and run before seeding:
- `backend/render_audio.py` — pre-renders vocab + dialogue + shadow audio (en-AU neural). Whole unit: $0.01.
- `backend/calibrate.py` — measures each shadow line's native ceiling across four AU voices.

All five stages run at `http://localhost:5001`:

| Stage | What works |
|---|---|
| Warm-up vocabulary | 17 terms, tap to hear in en-AU, Thai explanation under each |
| The whole conversation | A2 (7 lines) and B1 (17 lines) model dialogues, play-all with line highlighting, practise your own lines inline, Thai under every line |
| Drill the tricky bits | Shadow lines with calibrated ceilings, word-level error feedback |
| Free roleplay | Mic → Azure STT → Claude → spoken en-AU reply. A2/B1, 20-turn cap, never autostarts |
| Rewards & profile | Streak (minutes spoken), XP, sound meters, 8 derived achievements, restore code, end-of-session summary |

Content build steps, all idempotent, run before seeding:
- `backend/render_audio.py` — en-AU audio at `+18%` rate. Whole unit: $0.03.
- `backend/calibrate.py` — native ceiling per practisable line, across four AU voices.
- `backend/translate.py` — draft Thai, tagged `draft_unverified`. Never overwrites `reviewed`.

Measured costs: roleplay **$0.004/turn** (~$0.03–0.05 per full conversation), audio **$0.03/unit**.

**Remaining: the iPhone Safari validation** (ngrok tunnel gives the HTTPS a real device needs).


One scenario (`au_gp_appointment`), **three of the seven stages**: vocab → shadow one line → free roleplay.
The middle stages are content plumbing; they prove nothing new.

**Web first, native later.** A mobile-web page opened in iPhone Safari tests everything Steps 0–3 need
(will they speak, does scoring work, do they come back) and skips Expo, app review, and TestFlight.
Two risks from the original plan disappear with it: the Azure Speech **JavaScript SDK** streams mic audio
straight from the browser, so there is no m4a-vs-webm conversion and no upload round-trip.

- [x] **iPhone Safari validated 2026-08-23** — mic, scoring, roleplay and voice all work on a real
      device. Two iOS-specific bugs found and fixed (see §"iOS Safari rules" below). Original task:
      load the app on a real iPhone in Safari over the ngrok HTTPS URL
      and confirm mic permission + streaming assessment actually work. There are documented iOS Safari
      quirks (permission prompt timing, events stalling after grant). If it fails, fall back to
      `MediaRecorder` + server-side upload — which reinstates the audio-format work, so find out now.
- [x] Plain HTML/JS page served by the same Flask app — no framework, no build step, no SPA.
- [x] Azure Speech JS SDK in the browser for mic capture + streaming pronunciation assessment.
      **Never ship the Azure key to the browser**: add `GET /speech-token` to Flask that issues Azure's
      short-lived (~10 min) auth token from the key held server-side.
- [x] Client POSTs the resulting scores (not the audio) to `POST /attempts`.
- [ ] **STILL OPEN — biggest remaining cost lever.** Trim leading/trailing silence with an RMS gate
      before sending (~20 lines of JS). Not done because the browser SDK streams directly. Azure bills
      per second of audio sent; a 4s recording of a 3-word phrase is ~1.5–2s of actual speech. Cheapest
      35–50% saving in the whole product.
- [x] Keep shadow-focus lines to **3–5 word chunks**. Halves billed audio, and the flagship already
      calls for short repeatable lines — free saving.
- [x] HTTPS for device testing — **ngrok tunnel** (`ngrok http 5001`). Caddy on the droplet when deployed.
- [x] Roleplay endpoint: Anthropic API, system prompt built from the unit's `free_roleplay`
      (`ai_persona`, `b1_curveballs`, `roleplay_rubric`) — **that object only, ~600 tokens, not the whole
      unit JSON**. Adapt MockPatient's persona+rubric prompt; don't rebuild it.
- [x] Cost config on the roleplay call. **Note: `max_tokens` is NOT a length control** — adaptive
      thinking consumes it and returns an empty reply. Raised to 400; length comes from the prompt. (output
      is 5× input price and a reply is one or two sentences), **no extended thinking** on dialogue turns,
      prompt caching on the system prompt, and **Haiku 4.5 for turns with the rubric scored once at
      session end** rather than every turn.
- [x] TTS: pre-render dialogue lines to mp3 **at content-build time**, AU voice, serve as static files.
      Runtime TTS pays repeatedly for fixed content.
- [x] Roleplay capped at **20 turns**. Audio deletion is moot — **audio is never stored**; the
      browser streams straight to Azure. Original: cap at ~12 turns/session, delete uploaded audio after 7 days
      (keep the scores). Uncapped turns are unbounded COGS; kept audio is storage plus privacy exposure
      you get nothing for.
- [x] Account recovery — **restore codes** (`UWLX-A7RA`), no email server needed. Original rationale: device-uuid-only means a reinstall
      wipes their streak and progress, which is user-visible data loss in a retention product.

### iOS Safari rules — apply to every screen from here on

Both found on the first real-device test; neither shows up on a laptop.

1. **Claim the microphone synchronously inside the tap handler.** iOS only grants `getUserMedia`
   when it is reached without an intervening `await`. Fetching the speech token first broke the
   gesture chain and iOS refused the mic *silently*, with no error. Keep a warm token; claim the
   mic as the first statement in the handler; reuse the granted stream for the session.
2. **44px minimum touch targets.** Buttons with `padding: 3px 0` were unclickable by thumb while
   looking perfect under a mouse pointer. Also set `touch-action: manipulation` to drop Safari's
   300ms double-tap-zoom delay.

### Surfaced by testing, not yet done

- [ ] **Separate roleplay pronunciation from shadow pronunciation in the meters.** A tester rushed to
      match the GP's pace and mispronounced "bulk billed" — that logs as a `clusters` failure but
      measures conversational anxiety, not articulation. `attempts.stage` already distinguishes them;
      the meter query does not.
- [ ] **Stream the roleplay reply** and speak it as it arrives. 3.6s of silence per turn is the
      biggest thing making the conversation feel unreal.
- [ ] Second flagship (`medical_centre`, generic) — or skip it and let the Step 4 generator produce it.

**Exit**: you open a URL on your phone, speak, and get a pronunciation score and an in-scenario roleplay
reply. This is the moment the product is real or isn't.

Native (Expo) waits until Step 3 proves people come back — that's when push notifications and a
home-screen icon start earning their build cost. What web *can't* test: notification-driven habit and
app-store discovery. Neither matters at n=10.

---

## Step 3 — Get it in front of Thai Australians (~1 week, mostly not coding)

- [ ] **[HUMAN]** Native Thai speaker (the founder) reviews the drafted `th:` fields and sets
      `th_status: "reviewed"`. Drafts exist for all vocabulary and both dialogues.
- [ ] **[HUMAN]** Fact-check the AU flagship's Medicare/bulk-billing claims against current sources.
- [ ] **[HUMAN]** 5–10 Thai Australians use the slice. Watch them. The question is "did they come back
      tomorrow", not "did they like it".
- [ ] Fake paywall on day 3 of the trial: **"$11.99/month"** (ELSA's price — the anchor your users will
      compare against) — tap to join the waitlist. Willingness to pay is the reason this market was
      chosen over Thailand-domestic and it is currently untested. Their median income is $657/week, so
      this is a real decision for them, not a rounding error. One hour of work, real signal.
- [ ] **[HUMAN]** Ask every tester the AMEP question again, after they've used it. The answer changes
      once someone has actually rehearsed a GP conversation twenty times.
- [ ] **[HUMAN]** "Papaya" trademark clearance before any public-facing name use (`docs/brand/brand-guide.md`).
      Hold off on domains and store listings until it clears — renaming later is cheap, wasted spend isn't.

**Exit**: evidence the loop is worth scaling — or a redesign that costs one week, not three months.
Read n=10 as directional only; friends of the founder are polite and the sample proves nothing statistically.

---

## Step 4 — Content generator, calibrated (~2 days)

Only now, because the prompt should be tuned against something users actually reacted to.

- [ ] `backend/scripts/generate_unit.py` — one file: read registry entry (+ `locale_context`), call the
      API with the Section 4 prompt, run `validate(unit)`, write `content/<locale>/<id>.json`.
- [ ] `validate()` = plain checks from spec §5 + addendum §4 (required fields non-empty, ≥2 CEFR levels,
      every registry `sound_target` present in the box *and* a shadow line/curveball, all `required`
      rubric criteria, Thai fields actually Thai (codepoint range), no cross-country term leakage,
      en-AU spelling). Raise with the specific reason. Never auto-fix.
- [ ] Calibration: regenerate `medical_centre` and `au_gp_appointment`, diff against the hand-authored
      flagships. Drift → fix the prompt, not the output. **This diff is structural, not qualitative** —
      it cannot tell you the dialogue sounds like a textbook. Only a human read of the first 5 can, and
      "structurally valid but pedagogically mediocre" is how the content moat quietly dies.
- [ ] Ingest = `psql`-able loop dumping each JSON into `units.data`.

**Exit**: generating a known unit reproduces flagship depth.

---

## Step 5 — Scale content, price it, finish the loop

- [ ] Generate Tier 1 core (5 first, **[HUMAN]** review, then the rest ~28), then the AU pack (25), then Tier 2.
- [ ] Fill in the remaining 4 unit stages in the client once one full unit is worth completing.
- [x] Gamification UI — **done early in Step 2**: streak (minutes spoken), XP, sound meters, 8 derived
      achievements, end-of-session summary. All read from `attempts`; no extra tables, and the
      achievement rules can change without a migration.
- [ ] Native app (Expo) — only now, and only if Step 3 showed people coming back.
- [ ] **Offer annual billing (~$99/yr)** alongside monthly — one Stripe fee instead of twelve (~$4.60/user/yr),
      cash up front, better retention.
- [ ] **Billing: hard paywall + short free trial, sold on the web via Stripe.** Not freemium — hard
      paywalls convert ~5× better (10.7% vs 2.1%), and at this market size a 2.6% freemium conversion
      doesn't produce enough subscribers to fund the free users' per-minute costs. Web billing also
      keeps the 15–30% app-store cut, which is comparable to total COGS per subscriber.
- [ ] **The tier line follows the cost line.** Free/trial: vocab, chunk drills, listening, culture note
      (~zero marginal cost, can be generous). Paid: shadowing, guided roleplay, free roleplay — metered,
      turn-capped, never unlimited. Duolingo can afford unlimited because their core loop is
      client-graded static content at 140.6M MAU; ours costs money every minute. Metering is not a
      growth lever to add later — it is irreversible once users have unlimited access.
- [ ] **[HUMAN]** Full Thai review + full AU fact-check across everything generated.

---

## Cost model

Rates marked ⚠️ are estimates to confirm in Step 0 — they move, and two of them decide the business.

| Item | Rate | Alpha (20 users) | 1,000 paying users |
|---|---|---|---|
| Pronunciation scoring (Azure, ⚠️ ~$1/audio-hour) | $0.017/min scored | ~$10/mo | **$1.20–5.00/user/mo** |
| Roleplay (Claude Opus 5, $5/$25 per MTok, cached system prompt) | ~$0.10/session | ~$15/mo | **$6.00/user/mo** at 2 sessions/day |
| TTS (⚠️ ~$16/1M chars) — pre-rendered once, not per request | ~$5 for all 130 units | ~$0 | ~$0 |
| Content generation (~130 units, cached prefix + Batch) | ~$0.09/unit | <$100 **total, ever** | — |
| Hosting (DO droplet + nightly `pg_dump` to Spaces) | $12–17/mo | $17/mo | ~$100/mo (managed PG by then) |
| Apple $99/yr + Google $25 once | — | ~$10/mo | ~$10/mo |
| **Total** | | **~$50–75/mo** | **COGS $3–11/user vs $12 price** |

**With the cost levers in `docs/feasibility-assessment.md` §5b applied** (silence trimming, short shadow
lines, adaptive sampling, trimmed system prompt, capped `max_tokens`, split model tiers, web billing),
COGS lands near **$0.50/user/month — a 96% margin**, and alpha runs on one $12 droplet. Do not optimise
content generation, TTS, or hosting: they total under $50 and free tiers absorb them.

**The two numbers that decide whether this is a business:**

1. **Minutes of audio you send to the scorer.** At $1/audio-hour, 10 min/day/user is ~$5/user/month —
   against a ~$12 subscription. Scoring *only the shadow-focus lines* (~20 utterances × 4s = 80s/day)
   drops it to ~$1.20. **Score selectively by default; never score a whole roleplay turn.** An
   unlimited free tier is not affordable at any granularity — cap free minutes from day one.
2. **Roleplay turns.** Opus 5 at 2 sessions/day is ~$6/user/month, the single largest line item.
   Cache the unit JSON in the system prompt (reads at ~0.1×), cap turns per session, and treat the
   model choice as a live decision — Sonnet 5 halves it, Haiku 4.5 cuts it ~5×. Measure quality on
   real roleplay before assuming the cheaper tier is worse.

Content generation is so cheap it should not be optimised at all — regenerating every unit five times
over costs less than one month of hosting.

## Deliberately not doing

- UK/US packs — not until AU is validated with real users. **But they are the business, not optional
  extras**: AU alone caps around $130k/yr, and the ~500k Thai diaspora across English-speaking countries
  is what makes this a $650k–1.3M business. Sequenced late, weighted heavily.
- Payments, accounts, password reset — device uuid until someone wants to pay.
- Separate STT vendor — Azure's assessment response carries the words and offsets.
- Normalised content schema, progress/streak/xp tables, human-review UI, admin panel, CI/CD, staging env.
- Non-Thai audience or non-English-speaking country — deliberate scope call (`CLAUDE.md` §1, §6).
