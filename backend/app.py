"""Banana English backend. One file on purpose - see PLAN.md Step 1.

    python3 -m venv .venv && .venv/bin/pip install flask psycopg[binary]
    cp .env.example .env
    .venv/bin/python app.py
"""
import datetime, json, os, random, string, urllib.request, uuid
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, jsonify, g

for _line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")) \
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")) else []:
    _line = _line.strip()
    if _line and not _line.startswith("#") and "=" in _line:
        k, v = _line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

DSN = os.environ.get("DATABASE_URL", "postgresql:///banana")
app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = psycopg.connect(DSN, row_factory=dict_row, autocommit=True)
    return g.db


@app.teardown_appcontext
def _close(_exc):
    conn = g.pop("db", None)
    if conn:
        conn.close()


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/speech-token")
def speech_token():
    """Short-lived Azure token for the browser SDK. The subscription key never leaves the server."""
    region = os.environ["AZURE_SPEECH_REGION"]
    req = urllib.request.Request(
        f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        method="POST", data=b"",
        headers={"Ocp-Apim-Subscription-Key": os.environ["AZURE_SPEECH_KEY"]})
    with urllib.request.urlopen(req, timeout=10) as r:
        return {"token": r.read().decode(), "region": region}   # valid ~10 min


@app.get("/health")
def health():
    db().execute("select 1")
    return {"ok": True}


@app.get("/scenarios")
def list_scenarios():
    """Core content plus the user's locale pack; the pack wins on a shared scenario_id."""
    locale = request.args.get("locale", "en-AU")
    rows = db().execute("""
        select distinct on (u.scenario_id)
               u.scenario_id, u.locale,
               u.data->>'title_en' as title_en, u.data->>'title_th' as title_th,
               (u.data->>'tier')::int as tier, u.data->'cefr_range' as cefr_range
          from units u
         where u.locale in ('global', %s)
           -- a locale pack can drop core scenarios that don't exist in that country
           and not exists (select 1 from locale_drops d
                            where d.locale = %s and d.scenario_id = u.scenario_id
                              and u.locale = 'global')
         order by u.scenario_id, (u.locale = 'global')   -- false sorts first, so the pack wins
    """, (locale, locale)).fetchall()
    return jsonify(rows)


@app.get("/scenarios/<scenario_id>")
def get_scenario(scenario_id):
    locale = request.args.get("locale", "en-AU")
    row = db().execute("""
        select u.data from units u
         where u.scenario_id = %s and u.locale in ('global', %s)
           and not exists (select 1 from locale_drops d
                            where d.locale = %s and d.scenario_id = u.scenario_id
                              and u.locale = 'global')
         order by (u.locale = 'global') limit 1
    """, (scenario_id, locale, locale)).fetchone()
    if not row:
        return {"error": "not found"}, 404
    return jsonify(row["data"])


@app.post("/users")
def create_user():
    """Device-generated identity. No auth until someone wants to pay."""
    body = request.get_json(silent=True) or {}
    uid = body.get("id") or str(uuid.uuid4())
    try:
        uuid.UUID(uid)
    except ValueError:
        return {"error": "id must be a uuid"}, 400
    for _ in range(5):          # 32^8 keyspace, but a collision must not hard-fail a signup
        try:
            db().execute("""insert into users (id, locale, tz, restore_code) values (%s,%s,%s,%s)
                            on conflict (id) do nothing""",
                         (uid, body.get("locale", "en-AU"), body.get("tz", "Australia/Sydney"),
                          _new_restore_code()))
            break
        except psycopg.errors.UniqueViolation:
            continue
    else:
        return {"error": "could not allocate a restore code"}, 503
    row = db().execute("""select id, display_name, goal, restore_code from users where id = %s""",
                       (uid,)).fetchone()
    return row, 201


def _new_restore_code():
    """Short, speakable, no ambiguous characters. Written down, not typed often."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # no I/O/0/1
    return "-".join("".join(random.choices(alphabet, k=4)) for _ in range(2))


@app.get("/users/<user_id>")
def get_profile(user_id):
    row = db().execute("""select id, display_name, email, goal, locale, tz, restore_code, created_at
                            from users where id = %s""", (user_id,)).fetchone()
    return (row, 200) if row else ({"error": "not found"}, 404)


@app.patch("/users/<user_id>")
def update_profile(user_id):
    b = request.get_json(silent=True) or {}
    fields = {k: v for k, v in b.items() if k in ("display_name", "email", "goal", "tz", "locale")}
    if not fields:
        return {"error": "nothing to update"}, 400
    sets = ", ".join(f"{k} = %s" for k in fields)
    try:
        row = db().execute(f"""update users set {sets} where id = %s
                               returning id, display_name, email, goal, locale, tz, restore_code""",
                           (*fields.values(), user_id)).fetchone()
    except psycopg.errors.UniqueViolation:
        return {"error": "that email is already linked to another account"}, 409
    return (row, 200) if row else ({"error": "not found"}, 404)


@app.post("/restore")
def restore():
    """Recover an account on a new device. No password - the code IS the credential."""
    code = (request.get_json(silent=True) or {}).get("restore_code", "").strip().upper()
    row = db().execute("select id from users where restore_code = %s", (code,)).fetchone()
    return (row, 200) if row else ({"error": "no account with that code"}, 404)


@app.post("/attempts")
def log_attempt():
    """Log one scored attempt. Score is stored RELATIVE to the phoneme's ceiling.

    Step 0 found a perfect native take scores 100 on final /d/ but only ~72-80 on /th/, so raw
    vendor scores are not comparable across sounds and must never reach a learner.
    """
    b = request.get_json(silent=True) or {}
    for field in ("user_id", "scenario_id", "stage"):
        if not b.get(field):
            return {"error": f"{field} is required"}, 400

    # a failed recognition is not a practice attempt - logging it would poison the meters
    if b.get("recognition_failed"):
        return {"skipped": "recognition failed, not logged"}, 200

    raw_score, ceiling = b.get("raw_score"), b.get("ceiling")
    score = None
    if raw_score is not None:
        score = max(0.0, min(100.0, raw_score / ceiling * 100)) if ceiling else float(raw_score)

    row = db().execute("""
        insert into attempts (user_id, scenario_id, stage, sound_target, scoring_method,
                              raw_score, ceiling, score, seconds_spoken, raw, line_ref)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id, score
    """, (b["user_id"], b["scenario_id"], b["stage"], b.get("sound_target"),
          b.get("scoring_method"), raw_score, ceiling, score,
          b.get("seconds_spoken", 0), json.dumps(b.get("raw")) if b.get("raw") else None,
          b.get("line_ref"))).fetchone()
    return row, 201


# --- Free roleplay -----------------------------------------------------------------------------
# Model default is claude-opus-5. Sonnet 5 costs ~40% less and Haiku 4.5 ~80% less per session
# (docs/feasibility-assessment.md 5b) - switch with ROLEPLAY_MODEL once you've judged quality on
# real transcripts. Cost control here is turn caps, a trimmed system prompt, low effort and small
# max_tokens, not a cheaper model chosen blindly.
ROLEPLAY_MODEL = os.environ.get("ROLEPLAY_MODEL", "claude-opus-5")
MAX_TURNS = int(os.environ.get("ROLEPLAY_MAX_TURNS", "20"))


def _roleplay_system(unit, level):
    """Built from free_roleplay only (~600 tokens), never the whole unit JSON."""
    fr = unit.get("free_roleplay", {})
    gr = unit.get("guided_roleplay", {})
    curve = fr.get("b1_curveballs", [])
    return [{
        "type": "text",
        "text": f"""You are roleplaying with a Thai adult learning English. Stay in character.

YOUR CHARACTER: {fr.get('ai_persona', 'a friendly local')}
SITUATION: {unit.get('title_en')} in Australia. The learner is the {gr.get('learner_role', 'customer')}.
THEY MUST GET THROUGH: {' -> '.join(gr.get('flow', []))}

LEVEL {level}:
{"Stay on the standard script - be predictable and patient - but still work through every step. "
 + fr.get('a2_behavior', '')
 if level == 'A2' else
 "Go off-script once they are settled. Work in TWO of these across the encounter, not one, and "
 "space them out: " + "; ".join(curve)}

PACE - this is what makes it feel real:
- Work through EVERY step above, in order. Do not jump to the ending.
- Spend two or three exchanges on each step before moving on. A real GP asks follow-ups:
  how long, how bad out of ten, does it hurt to swallow, any allergies, taking anything else,
  has it happened before, does anyone else at home have it.
- Ask ONE question at a time and wait for the answer. Never stack two questions in one turn.
- Do not wrap up until they have handled the outcome (script, referral or test) AND know where
  to go next. If they try to leave early, do what a real GP does - stop them: "Before you go..."
- Only when everything is genuinely done, close warmly.

HOW TO SPEAK:
- One or two short sentences per turn. This is spoken aloud, not read.
- ONE turn only. Never write two exchanges in one reply, never skip ahead in time, never leave a
  blank line and continue. Stop after your one turn and wait - the learner needs the gap to speak.
- Natural Australian English. Contractions, "no worries", first names.
- Never break character to teach. If they are hard to understand, do what a real person does:
  "Sorry, say that again?" - that IS the feedback.
- If they are stuck twice on the same thing, help them the way a kind stranger would.
- Their short or broken answers are normal. Do not accept a one-word answer and move on -
  draw them out the way a real person would: "Sore how - scratchy, or hard to swallow?"

NEVER RUSH THEM. You speak at a natural Australian pace, but they do not have to match it.
- After you ask something, stop. Do not add a second sentence to fill the silence.
- If they rush, trail off, or a word comes out garbled, do not just move on and do not correct
  them. Slow yourself down and give the time back: "No rush, mate - take your time."
- If a key word was unclear, ask for it plainly the way a real person would: "Sorry, say that
  last bit again for me?" Give them the chance to say it properly rather than guessing.
- A learner who takes eight seconds to build a sentence is doing exactly what they should.
- Never write stage directions, asterisks, or emoji.

ANSWER THEIR QUESTIONS. If the learner asks something this scenario exists to teach - the cost,
the next step, what a word means - give them a real, concrete answer. Do not defer it ("we'll
sort that out later"), because the answer is the thing they came to practise hearing.

Open the conversation yourself if there are no messages yet.""",
        "cache_control": {"type": "ephemeral"},     # stable prefix, reused every turn at ~0.1x
    }]


def _client():
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")
    return anthropic.Anthropic()


@app.post("/roleplay")
def roleplay():
    b = request.get_json(silent=True) or {}
    messages = b.get("messages", [])
    if len(messages) > MAX_TURNS * 2:
        return {"error": "turn_limit", "message": "That's a full conversation - well done."}, 200

    row = db().execute("""select data from units where scenario_id = %s and locale in ('global', %s)
                          order by (locale = 'global') limit 1""",
                       (b.get("scenario_id", ""), b.get("locale", "en-AU"))).fetchone()
    if not row:
        return {"error": "unknown scenario"}, 404

    try:
        r = _client().messages.create(
            model=ROLEPLAY_MODEL,
            # thinking tokens count against max_tokens - at 150 a turn that thinks harder returns
            # an EMPTY reply. Replies stay short because the prompt says so, not because of this cap.
            max_tokens=400,
            system=_roleplay_system(row["data"], b.get("level", "A2")),
            output_config={"effort": "low"},                 # staying in character is not a reasoning task
            messages=messages or [{"role": "user", "content": "(the learner has just walked in)"}],
        )
    except RuntimeError as e:
        return {"error": "not_configured", "message": str(e)}, 503
    except Exception as e:
        return {"error": "upstream", "message": str(e)}, 502

    reply = "".join(c.text for c in r.content if c.type == "text").strip()
    if not reply:
        # never render an empty bubble; tell the client so it can prompt a retry
        return {"error": "empty_reply", "message": "Sorry, say that again?",
                "stop_reason": r.stop_reason}, 200
    return {"reply": reply, "turn": len(messages) // 2 + 1, "max_turns": MAX_TURNS,
            "usage": {"in": r.usage.input_tokens, "out": r.usage.output_tokens,
                      "cache_read": getattr(r.usage, "cache_read_input_tokens", 0)}}


@app.post("/roleplay/score")
def roleplay_score():
    """Score the rubric ONCE at the end, not per turn - see feasibility 5b."""
    b = request.get_json(silent=True) or {}
    row = db().execute("""select data from units where scenario_id = %s and locale in ('global', %s)
                          order by (locale = 'global') limit 1""",
                       (b.get("scenario_id", ""), b.get("locale", "en-AU"))).fetchone()
    if not row:
        return {"error": "unknown scenario"}, 404
    unit = row["data"]
    rubric = unit.get("free_roleplay", {}).get("roleplay_rubric", [])
    # feed the unit's OWN phrases in, so suggestions spiral with the curriculum instead of
    # being invented fresh each time
    frames = unit.get("guided_roleplay", {}).get("sentence_frames", [])
    for d in unit.get("chunk_drills", []):
        frames += d.get("examples", [])
    transcript = "\n".join(f"{'LEARNER' if m['role'] == 'user' else 'OTHER'}: {m['content']}"
                            for m in b.get("messages", []))
    if not transcript:
        return {"error": "no transcript"}, 400

    criteria = "\n".join(f"{i}. [{c['type']}] {c['criterion']}" for i, c in enumerate(rubric))
    try:
        r = _client().messages.create(
            model=os.environ.get("SCORING_MODEL", ROLEPLAY_MODEL),
            # thinking tokens count against max_tokens; 900 truncated the JSON mid-object
            max_tokens=2500,
            system="""You assess a Thai adult's English roleplay. Be generous about accent and
grammar - judge whether they ACHIEVED the goal, the way a real Australian would.

Two rules that matter more than the scoring:

1. WHEN THEY SUCCEEDED, quote their exact words back and say why it worked. "You said 'I have
   sore throat three days' - naming the symptom AND how long is exactly what a GP needs." People
   remember a phrase they can see themselves saying; they forget abstract praise. Never write
   "good job" without the words that earned it.

2. WHEN THEY MISSED SOMETHING, give them the sentence to say, not a description of it. Not "you
   should ask about severity" but "Next time say: 'It's about a seven out of ten.'" Prefer a
   phrase from the PHRASES list - those are the ones this unit teaches.

3. REWRITE EVERY CRITERION AS A PLAIN GOAL the learner would recognise. The criteria below are
   written for content authors, not for learners. "used the symptom formula correctly
   (location/type/severity/timing)" becomes "Describe your symptoms clearly". "coped with an
   off-script curveball" becomes "Handle a surprise". Five words or fewer, start with a verb,
   no jargon, no brackets.

Reply with JSON only.""",
            messages=[{"role": "user", "content": f"""TRANSCRIPT:
{transcript}

CRITERIA:
{criteria}

PHRASES this unit teaches (draw suggestions from these where they fit):
{chr(10).join('- ' + f for f in frames[:18])}

Return JSON:
{{"results":[
   {{"i":0,"goal":"Ask if it's bulk billed","met":true,"quote":"their exact words",
     "why":"why that worked, one sentence"}},
   {{"i":1,"goal":"Describe your symptoms","met":false,
     "say_this":"the exact sentence to use next time",
     "why":"what it gets you, one short sentence"}}],
 "headline":"one warm sentence naming the single best thing they actually said",
 "next_time":"the ONE thing to focus on next time, as a short instruction"}}"""}],
        )
        text = "".join(c.text for c in r.content if c.type == "text")
    except RuntimeError as e:
        return {"error": "not_configured", "message": str(e)}, 503
    except Exception as e:
        return {"error": "upstream", "message": f"{type(e).__name__}: {e}"}, 502

    try:
        parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        # truncation is the usual cause - say so instead of a bare 502
        return {"error": "unparseable",
                "message": f"scorer returned {len(text)} chars, stop_reason={r.stop_reason}",
                "text": text[-300:]}, 502

    results = [{**rubric[x["i"]], "goal": x.get("goal") or rubric[x["i"]]["criterion"],
                "met": x.get("met"), "quote": x.get("quote"),
                "say_this": x.get("say_this"), "why": x.get("why")}
               for x in parsed.get("results", []) if x.get("i", -1) < len(rubric)]
    required = [x for x in results if x.get("type") == "required"]
    passed = sum(1 for x in required if x.get("met"))
    pct = round(100 * passed / len(required)) if required else 0
    # bands, not raw percentages - a learner reading "50%" hears failure, and this audience's
    # documented barrier is fear of losing face (docs/brand/brand-guide.md)
    band = ("You did it" if pct >= 85 else "Nearly there" if pct >= 60
            else "Good start" if pct >= 30 else "Keep going")

    if b.get("user_id"):
        db().execute("""insert into attempts (user_id, scenario_id, stage, score, seconds_spoken, raw)
                        values (%s,%s,'free_roleplay',%s,%s,%s)""",
                     (b["user_id"], b["scenario_id"],
                      100.0 * passed / len(required) if required else None,
                      b.get("seconds_spoken", 0), json.dumps(parsed)))

    return {"headline": parsed.get("headline", ""), "results": results,
            "next_time": parsed.get("next_time", ""),
            "passed": passed, "of": len(required), "pct": pct, "band": band}


@app.get("/users/<user_id>/progress")
def progress(user_id):
    """Streak, XP and per-sound meters, all derived from attempts. No extra tables."""
    conn = db()
    meters = conn.execute("""
        select sound_target, scoring_method,
               round(avg(score)::numeric, 1) as avg_score,
               count(*) as attempts,
               round(avg(score) filter (where created_at > now() - interval '7 days')::numeric, 1) as last_7d
          from attempts
         where user_id = %s and sound_target is not null
         group by sound_target, scoring_method
         order by avg_score nulls last
    """, (user_id,)).fetchall()

    # streak currency is minutes spoken, counted in the user's own timezone
    days = conn.execute("""
        select (a.created_at at time zone u.tz)::date as day,
               round((sum(seconds_spoken) / 60.0)::numeric, 1) as minutes
          from attempts a join users u on u.id = a.user_id
         where a.user_id = %s
         group by day order by day desc
    """, (user_id,)).fetchall()

    streak, expected = 0, None
    for d in days:
        if float(d["minutes"]) <= 0:
            break
        if expected is None or d["day"] == expected:
            streak += 1
            expected = d["day"] - datetime.timedelta(days=1)
        else:
            break

    total = conn.execute("""select count(*) as n, coalesce(sum(seconds_spoken),0) as secs,
                                   count(*) filter (where score >= 80) as clean
                              from attempts where user_id = %s""", (user_id,)).fetchone()
    profile = conn.execute("""select display_name, goal, restore_code, email
                                from users where id = %s""", (user_id,)).fetchone() or {}

    # today, in the learner's own timezone - what the end-of-session summary is built from
    today = conn.execute("""
        select count(*) as takes,
               round((coalesce(sum(a.seconds_spoken),0) / 60.0)::numeric, 1) as minutes,
               count(*) filter (where a.stage = 'shadow') as shadow_takes,
               count(*) filter (where a.stage = 'free_roleplay') as roleplays,
               round(avg(a.score) filter (where a.stage = 'shadow')::numeric, 0) as avg_shadow
          from attempts a join users u on u.id = a.user_id
         where a.user_id = %s
           and (a.created_at at time zone u.tz)::date = (now() at time zone u.tz)::date
    """, (user_id,)).fetchone()

    # biggest gain on any sound today: first attempt vs last
    improved = conn.execute("""
        with t as (
          select a.sound_target, a.score,
                 row_number() over (partition by a.sound_target order by a.id)      as first_n,
                 row_number() over (partition by a.sound_target order by a.id desc) as last_n,
                 count(*)   over (partition by a.sound_target)                      as n
            from attempts a join users u on u.id = a.user_id
           where a.user_id = %s and a.sound_target is not null
             and (a.created_at at time zone u.tz)::date = (now() at time zone u.tz)::date)
        select sound_target,
               round(max(score) filter (where last_n = 1)::numeric, 0)
             - round(max(score) filter (where first_n = 1)::numeric, 0) as gain,
               round(max(score) filter (where last_n = 1)::numeric, 0)  as now
          from t where n > 1 group by sound_target order by gain desc limit 1
    """, (user_id,)).fetchone()
    minutes = round(total["secs"] / 60.0, 1)

    # Lines they've beaten, and the one to come back to. Adaptive resurfacing starts here.
    lines = conn.execute("""
        select line_ref, round(max(score)::numeric,0) as best,
               round(avg(score)::numeric,0) as avg, count(*) as tries
          from attempts where user_id = %s and line_ref is not null
         group by line_ref order by max(score)
    """, (user_id,)).fetchall()

    return {
        "user_id": user_id,
        "display_name": profile.get("display_name"),
        "goal": profile.get("goal"),
        "restore_code": profile.get("restore_code"),
        "has_email": bool(profile.get("email")),
        "streak_days": streak,
        "total_minutes_spoken": minutes,
        "xp": total["n"],                       # 1 XP per completed sub-step attempt
        "clean_takes": total["clean"],
        "sound_meters": meters,
        "lines": lines,
        "weakest_line": lines[0]["line_ref"] if lines else None,
        "achievements": achievements(minutes, streak, total["n"], total["clean"], meters),
        "today": dict(today or {}, improved=improved),
        "recent_days": days[:14],
    }


def achievements(minutes, streak, xp, clean, meters):
    """Derived, never stored - so the rules can change without a migration or backfill.

    Thresholds are deliberately low early on: this audience's barrier is fear of speaking, so the
    first rewards are for *showing up and making a sound*, not for being correct (brand-guide.md:
    the mascot cheers attempts, never scolds).
    """
    best = max((float(m["avg_score"]) for m in meters if m["avg_score"] is not None), default=0)
    defs = [
        ("first_words",  "First words",       "You spoke English out loud. That's the hard part.", xp >= 1,        1,   xp),
        ("five_takes",   "Warmed up",         "Five attempts recorded.",                           xp >= 5,        5,   xp),
        ("one_minute",   "A minute of speaking", "60 seconds of English out of your mouth.",       minutes >= 1,   1,   minutes),
        ("ten_minutes",  "Ten minutes",       "Ten minutes spoken. That's a real conversation.",   minutes >= 10,  10,  minutes),
        ("clean_take",   "Clear as a bell",   "A take with every word understood.",                clean >= 1,     1,   clean),
        ("streak_3",     "Three days",        "Three days in a row.",                              streak >= 3,    3,   streak),
        ("streak_7",     "A full week",       "Seven days in a row.",                              streak >= 7,    7,   streak),
        ("sound_80",     "Sound mastered",    "A sound meter above 80.",                           best >= 80,     80,  round(best)),
    ]
    return [{"key": k, "title": t, "blurb": b, "earned": bool(e),
             "target": tgt, "progress": min(prog, tgt)}
            for k, t, b, e, tgt, prog in defs]


if __name__ == "__main__":
    # 0.0.0.0 so a phone on the same wifi can reach it. NOTE: getUserMedia needs a secure
    # context, so the mic will NOT work over http://<lan-ip>. Use a tunnel for real device
    # testing - see backend/README.md.
    app.run(host="0.0.0.0", port=5001, debug=True)
