# Papaya backend

```bash
brew services start postgresql@18
createdb papaya
psql -d papaya -f schema.sql

python3 -m venv .venv && .venv/bin/pip install flask "psycopg[binary]"
cp .env.example .env
.venv/bin/python ../backend/seed.py     # loads content/<locale>/*.json
.venv/bin/python app.py                 # :5001
.venv/bin/python test_api.py            # end-to-end check, needs the server running
```

## Why it looks like this

- **Three tables** (`units`, `users`, `attempts`). A unit is a document read whole → `jsonb`, not seven
  normalised tables. Streaks, XP and per-sound meters are `GROUP BY` over `attempts` → no progress/
  streak/xp tables.
- **`attempts.ceiling` is not optional.** Step 0 measured that a *perfect native take* scores 100 on a
  final `/d/` but only ~79.8 on `/θ/`. Raw vendor scores are not comparable across sounds, so `score`
  is stored as `raw_score / ceiling * 100` and **only `score` may ever reach a learner**.
- **`users.tz`** because streak day-boundaries break the first time someone flies to Thailand, which
  this user base does constantly.
- **No auth.** Device-generated uuid until someone wants to pay.
- **No ORM, no migrations, no blueprints, no app factory.** Three tables and five endpoints.

## Endpoints

| | |
|---|---|
| `GET /health` | |
| `GET /scenarios?locale=en-AU` | core ∪ locale pack, pack wins on shared `scenario_id` |
| `GET /scenarios/<id>?locale=en-AU` | the full unit JSON |
| `POST /users` | `{id?, locale?, tz?}` → device identity |
| `POST /attempts` | `{user_id, scenario_id, stage, sound_target?, scoring_method?, raw_score?, ceiling?, seconds_spoken?}` |
| `GET /users/<id>/progress` | streak (minutes spoken), xp, per-sound meters |
