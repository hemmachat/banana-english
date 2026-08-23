#!/usr/bin/env python3
"""Generate native-speaker control recordings with Azure TTS.

No native speaker needed: the en-AU neural voice IS the reference pronunciation, and it's the same
voice the product will use for model dialogue — so "how does my take score against the voice I'm
shadowing" is literally the comparison the app makes.

    export AZURE_SPEECH_KEY=... AZURE_SPEECH_REGION=australiaeast
    python3 make_controls.py recordings/

Writes recordings/ttsF__<test_id>__correct.wav and ttsM__<test_id>__correct.wav, which flow straight
into assess.py alongside the human takes.
"""
import os, sys
import azure.cognitiveservices.speech as speechsdk
from assess import TESTS  # noqa: F401  (also loads spike/.env)

# More reference voices = a more stable ceiling. The two-voice ceiling for /th/ varied by 8 points,
# and /th/ is a core Thai target, so the average matters. Costs nothing (TTS free tier).
VOICES = {
    "ttsF":  "en-AU-NatashaNeural",
    "ttsM":  "en-AU-WilliamNeural",
    "ttsF2": "en-AU-AnnetteNeural",
    "ttsF3": "en-AU-CarlyNeural",
    "ttsM2": "en-AU-DarrenNeural",
    "ttsM3": "en-AU-DuncanNeural",
}


def synth(text, voice, out_path):
    cfg = speechsdk.SpeechConfig(subscription=os.environ["AZURE_SPEECH_KEY"],
                                 region=os.environ["AZURE_SPEECH_REGION"])
    cfg.speech_synthesis_voice_name = voice
    # same format assess.py expects: 16kHz 16-bit mono PCM
    cfg.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm)
    s = speechsdk.SpeechSynthesizer(
        speech_config=cfg, audio_config=speechsdk.audio.AudioOutputConfig(filename=out_path))
    r = s.speak_text_async(text).get()
    if r.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        d = getattr(r, "cancellation_details", None)
        raise RuntimeError(f"{voice} / {text!r}: {r.reason}\n"
                           f"  reason : {getattr(d, 'reason', '?')}\n"
                           f"  details: {getattr(d, 'error_details', '(none)')}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "recordings"
    os.makedirs(out, exist_ok=True)
    for speaker, voice in VOICES.items():
        for test_id, (ref, _, _) in TESTS.items():
            if test_id == "garbage":
                continue                      # a control for "say something unrelated" is meaningless
            path = os.path.join(out, f"{speaker}__{test_id}__correct.wav")
            try:
                synth(ref, voice, path)
            except RuntimeError as e:       # a retired/renamed voice shouldn't kill the whole run
                print(f"SKIP {voice}: {str(e).splitlines()[-1]}")
                if os.path.exists(path):
                    os.remove(path)
                break
            print(f"{path}  <- {voice}  {ref!r}")
    print("\nDone. Now run: python3 assess.py", out)
