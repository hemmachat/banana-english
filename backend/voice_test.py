#!/usr/bin/env python3
"""Render one line across candidate voices and rates so a human can pick by ear.

    .venv/bin/python voice_test.py
    open http://localhost:5001/static/voicetest/

Naturalness is not measurable from a spec sheet. Costs a few hundred characters against the
500k/month free tier.
"""
import os
from xml.sax.saxutils import escape
import azure.cognitiveservices.speech as speechsdk

HERE = os.path.dirname(os.path.abspath(__file__))
for _l in open(os.path.join(HERE, ".env")):
    if "=" in _l and not _l.strip().startswith("#"):
        k, v = _l.strip().split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# a real line from the AU flagship: conversational, and carries the phrase testers struggle on
LINE = "There is, yeah - we don't bulk bill. It's forty dollars after the Medicare rebate."

CANDIDATES = [
    ("1-current-natasha-18",  "en-AU-NatashaNeural",                        "+18%"),
    ("2-natasha-normal",      "en-AU-NatashaNeural",                        "+0%"),
    ("3-natasha-10",          "en-AU-NatashaNeural",                        "+10%"),
    ("4-william-multiling",   "en-AU-WilliamMultilingualNeural",            "+18%"),
    ("5-freya",               "en-AU-FreyaNeural",                          "+18%"),
    ("6-tina",                "en-AU-TinaNeural",                           "+18%"),
    ("7-hd-cyanspark",        "en-au-cyanspark:DragonHDOmniLatestNeural",   "+18%"),
    ("8-hd-siennatopaz",      "en-au-siennatopaz:DragonHDOmniLatestNeural", "+18%"),
]

out = os.path.join(HERE, "static", "voicetest")
os.makedirs(out, exist_ok=True)
made = []
for name, voice, rate in CANDIDATES:
    cfg = speechsdk.SpeechConfig(subscription=os.environ["AZURE_SPEECH_KEY"],
                                 region=os.environ["AZURE_SPEECH_REGION"])
    cfg.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3)
    path = os.path.join(out, f"{name}.mp3")
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-AU">'
            f'<voice name="{voice}"><prosody rate="{rate}">{escape(LINE)}</prosody></voice></speak>')
    synth = speechsdk.SpeechSynthesizer(
        speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=path))
    r = synth.speak_ssml_async(ssml).get()
    del synth, cfg
    if r.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        made.append((name, voice, rate)); print(f"  ok   {name:22} {voice}")
    else:
        d = getattr(r, "cancellation_details", None)
        print(f"  FAIL {name:22} {voice}  {getattr(d, 'error_details', r.reason)}"[:150])
        os.path.exists(path) and os.remove(path)

cards = "".join(
    f'<div class=row><button data-src="{n}.mp3">&#9654; Play</button>'
    f'<div><b>{n}</b><br><small>{v} &middot; rate {rt}</small></div></div>'
    for n, v, rt in made)

page = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Voice comparison</title>
<style>
body{font:16px/1.5 -apple-system,BlinkMacSystemFont,sans-serif;padding:18px;max-width:620px;
margin:auto;background:#FFE9CE;color:#2E2A2B}
.row{display:flex;gap:13px;align-items:center;background:#fff;border-radius:12px;
padding:12px 14px;margin-bottom:9px}
button{font:inherit;font-weight:700;background:#FF8A3D;color:#fff;border:0;border-radius:10px;
padding:0 18px;min-height:48px;min-width:104px;cursor:pointer;flex:0 0 auto}
button.on{background:#F4603E}
small{color:#8a7f7a}
</style>
<h2>Which sounds least robotic?</h2>
<p>&ldquo;__LINE__&rdquo;</p>
__CARDS__
<p><small>1&ndash;3 test whether the <b>speed</b> is the problem, not the voice.
7&ndash;8 are DragonHD &mdash; verify pricing before shipping those.</small></p>
<script>
var a = new Audio();
document.querySelectorAll('button').forEach(function (b) {
  b.onclick = function () {
    var wasPlaying = (a.dataset.cur === b.dataset.src && !a.paused);
    document.querySelectorAll('button').forEach(function (x) {
      x.classList.remove('on'); x.innerHTML = '&#9654; Play';
    });
    a.pause();
    if (wasPlaying) return;
    a.src = b.dataset.src; a.dataset.cur = b.dataset.src;
    a.play();
    b.classList.add('on'); b.innerHTML = '&#9632; Stop';
    a.onended = function () { b.classList.remove('on'); b.innerHTML = '&#9654; Play'; };
  };
});
</script>"""
open(os.path.join(out, "index.html"), "w").write(
    page.replace("__LINE__", LINE).replace("__CARDS__", cards))
print(f"\n{len(made)} samples -> http://localhost:5001/static/voicetest/index.html")
