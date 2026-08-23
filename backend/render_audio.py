#!/usr/bin/env python3
"""Pre-render model audio for every unit, once, at content-build time.

The learner must hear a word or line before shadowing it. Content is fixed, so synthesizing at
runtime would pay Azure repeatedly for identical audio - render once, serve as static files.
Whole catalogue costs a few dollars at ~$16/1M chars, and Azure's free tier is 0.5M chars/month.

    .venv/bin/python render_audio.py        # writes static/audio/<locale>/*.mp3, updates content JSON
"""
import glob, json, os, re
from xml.sax.saxutils import escape
import azure.cognitiveservices.speech as speechsdk

# A tester said the default rate sounds unrealistic - real Australians speak faster, and shadowing
# a slowed-down model teaches a target that doesn't exist. Raise it here and the whole catalogue
# re-renders at the new rate.
SPEECH_RATE = os.environ.get("SPEECH_RATE", "+18%")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Tina chosen by ear over Natasha, Freya and William Multilingual (voice_test.py).
VOICE = {"en-AU": "en-AU-TinaNeural", "global": "en-AU-TinaNeural"}

for _l in open(os.path.join(HERE, ".env")) if os.path.exists(os.path.join(HERE, ".env")) else []:
    if "=" in _l and not _l.strip().startswith("#"):
        k, v = _l.strip().split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "clip"


def render(text, voice, out_path):
    if os.path.exists(out_path):
        return False                                    # idempotent: never re-pay for the same clip
    cfg = speechsdk.SpeechConfig(subscription=os.environ["AZURE_SPEECH_KEY"],
                                 region=os.environ["AZURE_SPEECH_REGION"])
    cfg.speech_synthesis_voice_name = voice
    cfg.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3)
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-AU">'
            f'<voice name="{voice}"><prosody rate="{SPEECH_RATE}">{escape(text)}</prosody>'
            f'</voice></speak>')
    synth = speechsdk.SpeechSynthesizer(
        speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=out_path))
    r = synth.speak_ssml_async(ssml).get()
    del synth, cfg                                      # release the file handle (see calibrate.py)
    if r.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        os.path.exists(out_path) and os.remove(out_path)
        raise RuntimeError(f"{voice} / {text!r}: {r.reason}")
    return True


total_new = total_chars = 0
for path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
    unit = json.load(open(path))
    locale = unit.get("locale", "global")
    voice = VOICE.get(locale, "en-AU-NatashaNeural")
    outdir = os.path.join(HERE, "static", "audio", locale)
    os.makedirs(outdir, exist_ok=True)

    # everything a learner needs to hear before speaking
    items = [(v, "en") for v in unit.get("vocabulary", [])]
    for d in unit.get("model_dialogues", []):
        items += [(l, "text") for l in d.get("shadow_focus_lines", [])]
        items += [(l, "text") for l in d.get("lines", [])]

    for obj, field in items:
        text = obj[field]
        name = f"{slug(text)}.mp3"
        made = render(text, voice, os.path.join(outdir, name))
        obj["audio"] = f"/static/audio/{locale}/{name}"
        total_new += made
        total_chars += len(text) if made else 0
        if made:
            print(f"  {locale}/{name}")

    json.dump(unit, open(path, "w"), indent=2, ensure_ascii=False)

print(f"\n{total_new} new clip(s), {total_chars} characters "
      f"(~${total_chars / 1_000_000 * 16:.4f} at $16/1M; free tier is 500k chars/month)")
