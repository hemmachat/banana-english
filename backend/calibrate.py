#!/usr/bin/env python3
"""Measure the native ceiling for every shadow line, at content-build time.

Step 0 established that a perfect native take does NOT score 100 - it scores whatever that
particular sound sequence scores (final /d/ -> 100, but /th/ -> ~72-87 depending on voice). So
before any learner sees a number, we synthesize each shadow line with several en-AU neural voices,
assess them, and store the mean as that line's ceiling.

    .venv/bin/python calibrate.py            # updates content/<locale>/*.json in place
"""
import glob, json, os, statistics, tempfile
import azure.cognitiveservices.speech as speechsdk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICES = ["en-AU-NatashaNeural", "en-AU-WilliamNeural", "en-AU-AnnetteNeural", "en-AU-DarrenNeural"]

for _l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")) \
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")) else []:
    if "=" in _l and not _l.strip().startswith("#"):
        k, v = _l.strip().split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

KEY, REGION = os.environ["AZURE_SPEECH_KEY"], os.environ["AZURE_SPEECH_REGION"]


def _cfg():
    return speechsdk.SpeechConfig(subscription=KEY, region=REGION)


def native_accuracy(text, voice, locale):
    """Synthesize one line in one voice, score it against itself, return AccuracyScore."""
    wav = os.path.join(tempfile.gettempdir(), f"banana_cal_{abs(hash((text, voice)))}.wav")
    tts = _cfg()
    tts.speech_synthesis_voice_name = voice
    tts.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    synth = speechsdk.SpeechSynthesizer(
        speech_config=tts, audio_config=speechsdk.audio.AudioOutputConfig(filename=wav))
    r = synth.speak_text_async(text).get()
    # the synthesizer holds the file open; reopening it for recognition before release segfaults
    del synth, tts
    if r.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        return None

    stt = _cfg()
    stt.output_format = speechsdk.OutputFormat.Detailed
    pron = speechsdk.PronunciationAssessmentConfig(
        reference_text=text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True)
    rec = speechsdk.SpeechRecognizer(speech_config=stt, language=locale,
                                     audio_config=speechsdk.audio.AudioConfig(filename=wav))
    pron.apply_to(rec)
    raw = rec.recognize_once().properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
    del rec, stt
    os.path.exists(wav) and os.remove(wav)
    if not raw:
        return None
    return json.loads(raw)["NBest"][0].get("PronunciationAssessment", {}).get("AccuracyScore")


for path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
    unit = json.load(open(path))
    locale = unit.get("locale", "en-AU")
    changed = False
    learner_role = unit.get("guided_roleplay", {}).get("learner_role", "patient")
    for dialogue in unit.get("model_dialogues", []):
        # the learner speaks their own role's lines, so those need ceilings too
        practiseable = dialogue.get("shadow_focus_lines", []) + \
            [l for l in dialogue.get("lines", []) if l.get("speaker") == learner_role]
        for line in practiseable:
            scores = [s for s in (native_accuracy(line["text"], v, locale) for v in VOICES) if s is not None]
            if not scores:
                print(f"  !! no ceiling for {line['text']!r}")
                continue
            line["ceiling"] = round(statistics.mean(scores), 1)
            line["ceiling_spread"] = [min(scores), max(scores)]
            line["ceiling_voices"] = len(scores)
            changed = True
            flag = "  <-- WIDE SPREAD, treat this line's score with suspicion" \
                if max(scores) - min(scores) > 15 else ""
            print(f"  {line['text']!r:34} ceiling {line['ceiling']:5.1f}  spread {min(scores):.0f}-{max(scores):.0f}{flag}")
    if changed:
        json.dump(unit, open(path, "w"), indent=2, ensure_ascii=False)
        print(f"updated {os.path.relpath(path, ROOT)}\n")
