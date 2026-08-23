# Generation Spec — Locale Addendum

Extends `scenario-unit-generation-spec.md` so the **same pipeline** produces localized content (Australia first, then UK/US/other English-speaking countries). Nothing in the base spec is removed — this adds a locale dimension on top of it.

The benchmark for locale output is `au-flagship-unit-gp-appointment.md`. Generated `en-AU` units must match its depth **and** its local accuracy.

---

## 1. Two new inputs

Every generation run now takes two extra fields alongside the registry entry:

```yaml
locale: en-AU
locale_context: |
  Australian English. Model accent = Australian; spelling = en-AU
  (organise, colour, centre). Currency AUD, emergency number 000.
  Health = Medicare; GPs bulk bill or charge a gap; GP is the
  gatekeeper (referral needed for specialists); prescription = "script";
  pharmacy = "the chemist"; blood tests = "pathology". Welfare =
  Centrelink / Services Australia via myGov. Tax ID = TFN. Register is
  casual even with officials (first names, "no worries", direct).
```

`locale_context` is a **one-paragraph description of the relevant host-country systems** — the author writes it once per locale (it lives in the locale pack's `config` + a short system note) and it is injected into every run for that locale.

---

## 2. Output schema change

Add one field to the unit object from the base spec:

```json
{
  "locale": "en-AU",
  "...": "all other fields from the base schema"
}
```

Runtime resolution (see the architecture doc's data model): a unit with `locale: "global"` is core; a unit with `locale: "en-AU"` overrides/adds for Australian users, keyed by `scenario_id`.

---

## 3. Locale rules appended to the generation prompt

Add this block to the base generation prompt, after its existing non-negotiables:

> **Localization rules (when a `locale` is supplied):**
>
> 9. **Use the host country's systems and terms exactly.** Take every institution name, process, and colloquialism from `locale_context`. For `en-AU`: "GP," "bulk billed," "script," "the chemist," "pathology," "Medicare card," "referral," "Centrelink," "000." Never let another country's terms leak in — no "ER," "911," "pharmacy" (US), "insurance copay," or "NHS" in an `en-AU` unit.
> 10. **Model the host accent and spelling.** TTS voice = `model_accent`; all spelling follows the locale (`en-AU`: -ise/-our/-re, "enrolment," "recognise"). Dialogue should use natural host-country phrasing ("G'day, what brings you in today?", "have you got…").
> 11. **Apply the host register.** Use the `politeness_note` — for `en-AU`, casual-but-respectful, first names, direct symptom reporting encouraged.
> 12. **Keep the invariant core invariant.** The Thai L1 sound targets, the symptom/severity formulas, the CEFR banding, the Do/Don't safety guidance, and the 7-stage structure **do not change by locale.** Only the *system layer* (agencies, terms, processes) localizes. If you find yourself rewriting the pedagogy for a locale, stop — that's a signal you're changing the wrong layer.
> 13. **Localize the culture note.** The `register_culture_note` must reflect a genuine host-country difference (e.g. AU: asking "is it bulk billed?" is normal; the GP is a gatekeeper) plus the Thai-learner cultural bridge.

---

## 4. Locale QA checks (added to the base checklist)

Automated:
- ☐ `locale` field present and matches the run's target.
- ☐ **No cross-country leakage:** scan output for wrong-locale tokens. For `en-AU`, fail on: `911`, ` ER `, `ZIP code`, `NHS`, `copay`, `Social Security`, US spellings (`-ize`, `color`, `enrollment`).
- ☐ Spelling matches the locale variant throughout.
- ☐ Required host-system terms for the scenario's category appear (e.g. an `en-AU` health unit must contain "Medicare" and "bulk bill").
- ☐ Thai L1 sound targets still present and unchanged (localization must not have quietly dropped them).

Human spot-check (every locale unit, not a sample — locale facts are high-risk):
- ☐ Are the host-country facts actually correct? (Have a local or recent migrant verify.)
- ☐ Does the dialogue sound like a real person *in that country*, not a translated textbook?
- ☐ Is the culture note true, current, and non-stereotyping?
- ☐ Thai strings verified by a native speaker.

---

## 5. Per-locale generation workflow

For each new country:

1. Author the locale pack: `config` block + `locale_context` paragraph + ~22 Layer C scenario entries (use `locale-pack-australia.yaml` as the template).
2. Regenerate **only** the Layer C scenarios with `locale` + `locale_context` injected. (Core Layer A content is generated once as `global`; it does **not** get regenerated per locale — at most it gets an automated spelling pass and any config-driven swaps like transit-card names.)
3. Run locale QA; every locale unit gets a human fact-check.
4. Add one TTS voice for the new `model_accent`.
5. Ship.

**Cost note:** because only ~22 scenarios regenerate per country (not the whole catalogue), each new locale is a small, bounded batch. Australia is the exception — it's your first full run, so it also validates the core.

---

## 6. Order of operations for Australia (do this first)

1. Confirm `au-flagship-unit-gp-appointment.md` as the `en-AU` quality bar.
2. Generate the 5 Tier-1 core scenarios (as `global`) + `au_gp_appointment` (as `en-AU`) — your first testable, Australia-ready content set.
3. Review both against their respective flagships; tune the prompt where output drifts.
4. Batch the rest of the AU Layer C pack, then the remaining core.
5. Only then start the UK pack — it ports from AU with moderate edits (NHS, deposit-protection, British accent).
