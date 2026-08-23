#!/usr/bin/env python3
"""Step 0 spike: does Azure Pronunciation Assessment actually detect Thai L1 errors?

Usage:
    pip install azure-cognitiveservices-speech
    export AZURE_SPEECH_KEY=... AZURE_SPEECH_REGION=australiaeast
    python3 assess.py recordings/

Filename convention:  <speaker>__<test_id>__<correct|wrong>.wav
Example:              nok__card__wrong.wav
"""
import json, os, sys, collections


def _load_env(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Read KEY=value lines from spike/.env so the credentials don't have to live in the shell."""
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

# en-AU returns phoneme SCORES but empty phoneme LABELS, so we target by position instead:
# target = (word_index, phoneme_index), negative index counts from the end of the word.
# The reference text is fixed, so the phoneme sequence is deterministic and position is enough.
TESTS = {
    "card":       ("card",              (0, -1), "drop the final /d/ -> 'car'"),
    "bulk":       ("bulk billed",       (1, -1), "drop the clusters -> 'buk bin'"),
    "referral":   ("referral",          (0,  0), "r -> l, 'refellal'"),
    "three":      ("three times a day", (0,  0), "th -> t, 'tree times a day'"),
    "left":       ("turn left",         (1, -1), "l -> r and drop final t, 'turn reff'"),
    "script":     ("the script",        (1, -1), "'de scrip' - voiced th + str cluster + final t"),
    "thirteen":   ("thirteen",          (0, -1), "say 'thirty' instead"),
    "garbage":    ("bulk billed",       None,    "say something unrelated - guards against a scorer that rewards anything"),
}
LOCALE = os.environ.get("PAPAYA_LOCALE", "en-AU")


def assess(wav_path, reference_text):
    """Return Azure's raw JSON result for one utterance."""
    import azure.cognitiveservices.speech as speechsdk
    cfg = speechsdk.SpeechConfig(subscription=os.environ["AZURE_SPEECH_KEY"],
                                 region=os.environ["AZURE_SPEECH_REGION"])
    # without Detailed, the response has no per-word / per-phoneme breakdown at all
    cfg.output_format = speechsdk.OutputFormat.Detailed
    pron = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)          # so a dropped word shows as Omission, not silence
    pron.phoneme_alphabet = "IPA"
    # ponytail: prosody is en-US only, so word_stress/intonation targets can't be scored in en-AU.
    if LOCALE == "en-US":
        pron.enable_prosody_assessment()
    rec = speechsdk.SpeechRecognizer(speech_config=cfg, language=LOCALE,
                                     audio_config=speechsdk.audio.AudioConfig(filename=wav_path))
    pron.apply_to(rec)
    result = rec.recognize_once()
    raw = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
    if not raw:
        d = getattr(result, "cancellation_details", None)
        raise RuntimeError(f"{wav_path}: no result ({result.reason})\n"
                           f"  reason : {getattr(d, 'reason', '?')}\n"
                           f"  details: {getattr(d, 'error_details', '(none)')}\n"
                           f"  (if the audio was fine, check the WAV is 16kHz mono PCM)")
    return json.loads(raw)


def _ph_score(ph):
    return ph.get("PronunciationAssessment", {}).get("AccuracyScore")


def summarise(doc, target):
    """Pull the numbers that decide the spike out of Azure's JSON."""
    best = doc["NBest"][0]
    pa = best.get("PronunciationAssessment", {})
    words, all_ph, target_score = [], [], None
    for wi, w in enumerate(best.get("Words", [])):
        wpa = w.get("PronunciationAssessment", {})
        words.append((w["Word"], wpa.get("AccuracyScore"), wpa.get("ErrorType")))
        phonemes = w.get("Phonemes", [])
        all_ph.extend(_ph_score(p) for p in phonemes)
        if target and target[0] == wi and phonemes:
            try:
                target_score = _ph_score(phonemes[target[1]])
            except IndexError:          # the wrong take may have fewer phonemes - that IS the signal
                target_score = None
    return {
        "heard": best.get("Display", doc.get("DisplayText", "")),
        # AccuracyScore, NOT PronScore: on short drills PronScore is dominated by Fluency and
        # Completeness, which collapse to 0 on a clipped 0.5s clip and say nothing about pronunciation.
        "pron": pa.get("AccuracyScore"),
        "pronscore": pa.get("PronScore"),
        "fluency": pa.get("FluencyScore"),
        "completeness": pa.get("CompletenessScore"),
        "flagged": any(e and e != "None" for _, _, e in
                       [(w["Word"], None, w.get("PronunciationAssessment", {}).get("ErrorType"))
                        for w in best.get("Words", [])]),
        "words": words,
        "target": target_score,
        "worst_ph": min([s for s in all_ph if s is not None], default=None),
        "n_ph": len(all_ph),
    }


def main(folder):
    rows = collections.defaultdict(dict)
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".wav"):
            continue
        speaker, test_id, version = fn[:-4].split("__")
        ref, target, _ = TESTS[test_id]
        rows[(speaker, test_id)][version] = summarise(assess(os.path.join(folder, fn), ref), target)

    # Each phoneme has its own ceiling (final /d/ hits 100, but /th/ tops out ~72-80 on a perfect
    # native take), so an absolute score means nothing on its own. Calibrate against the TTS controls.
    ceiling = {}
    for (speaker, test_id), versions in rows.items():
        if speaker.startswith("tts") and "correct" in versions:
            t = versions["correct"]["target"]
            if t is not None:
                ceiling.setdefault(test_id, []).append(t)
    ceiling = {k: sum(v) / len(v) for k, v in ceiling.items()}
    if ceiling:
        print("\nTTS ceiling per target phoneme (a perfect native take scores this, not 100):")
        for k, v in sorted(ceiling.items()):
            print(f"  {k:10} {v:5.1f}")

    print(f"\n{'speaker':10} {'test':10} {'ver':8} {'Accuracy':>9} {'target ph':>9} {'vs ceil':>8} "
          f"{'worst ph':>8} {'#ph':>4}  heard / word errors")
    print("-" * 120)
    for (speaker, test_id), versions in sorted(rows.items()):
        for version, r in sorted(versions.items()):
            errs = ",".join(f"{w}:{e}" for w, s, e in r["words"] if e and e != "None") or "-"
            c = ceiling.get(test_id)
            rel = f"{r['target'] - c:+.0f}" if (c and r["target"] is not None) else "-"
            warn = ""
            if r["completeness"] == 0 or r["fluency"] == 0:
                warn = "  [!] fluency/completeness 0 - clip likely trimmed too tight, ignore PronScore"
            print(f"{speaker:10} {test_id:10} {version:8} {str(r['pron']):>9} {str(r['target']):>9} {rel:>8} "
                  f"{str(r['worst_ph']):>8} {r['n_ph']:>4}  {r['heard'][:30]!r} {errs}{warn}")
        if test_id == "garbage":
            # not a pair: the pass condition is "unrelated speech scores low", either way round
            lo = min(v["pron"] or 0 for v in versions.values())
            print(f"{'':10} {'':10} guard    {lo:>9.0f}  "
                  f"{'PASS (unrelated speech scores low)' if lo < 30 else '*** FAILS - scores anything highly ***'}\n")
        elif "correct" in versions and "wrong" in versions:
            c, w = versions["correct"]["pron"] or 0, versions["wrong"]["pron"] or 0
            verdict = "PASS" if c - w >= 15 else "*** TOO CLOSE ***"
            print(f"{'':10} {'':10} delta    {c - w:>9.0f}  {verdict}\n")


def selftest():
    doc = {"DisplayText": "car.", "NBest": [{"Display": "car.",
        "PronunciationAssessment": {"PronScore": 62.0, "AccuracyScore": 60.0, "CompletenessScore": 100.0},
        "Words": [{"Word": "card", "PronunciationAssessment": {"AccuracyScore": 55.0, "ErrorType": "Mispronunciation"},
                   "Phonemes": [{"Phoneme": "k", "PronunciationAssessment": {"AccuracyScore": 98.0}},
                                {"Phoneme": "d", "PronunciationAssessment": {"AccuracyScore": 12.0}}]}]}]}
    s = summarise(doc, (0, -1))
    assert s["pron"] == 60.0, s                                  # AccuracyScore, not PronScore (62.0)
    assert s["pronscore"] == 62.0 and s["target"] == 12.0, s     # last phoneme of word 0
    assert s["flagged"] is True, s
    assert s["words"][0] == ("card", 55.0, "Mispronunciation"), s
    assert s["worst_ph"] == 12.0 and s["n_ph"] == 2, s
    assert summarise(doc, None)["target"] is None
    assert summarise(doc, (0, 0))["target"] == 98.0              # first phoneme
    assert summarise(doc, (9, 0))["target"] is None              # word index out of range
    print("selftest ok")


def dump(wav_path):
    """Print Azure's raw JSON for one file - use when the parsed table looks wrong."""
    speaker, test_id, version = os.path.basename(wav_path)[:-4].split("__")
    print(json.dumps(assess(wav_path, TESTS[test_id][0]), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    elif len(sys.argv) > 2 and sys.argv[1] == "--dump":
        dump(sys.argv[2])
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        sys.exit(__doc__)
