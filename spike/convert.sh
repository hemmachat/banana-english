#!/bin/bash
# Convert exported Voice Memos (raw/*.m4a) to the 16kHz mono PCM WAV that Azure needs.
# Handles spaces in filenames. Skips anything already converted.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p recordings
shopt -s nullglob nocaseglob
found=0
for f in raw/*.m4a raw/*.mp3 raw/*.wav raw/*.aiff raw/*.caf; do
  found=1
  base=$(basename "${f%.*}")
  # accept single-underscore names (speaker_test_version) and normalise to the __ convention
  if [[ "$base" != *"__"* ]]; then
    base="${base//_/__}"
  fi
  out="recordings/${base}.wav"
  [ -f "$out" ] && { echo "skip  $base"; continue; }
  ffmpeg -loglevel error -i "$f" -ar 16000 -ac 1 -c:a pcm_s16le "$out"
  echo "ok    $base"
  # warn early about names assess.py can't parse
  [[ "$base" == *"__"*"__"* ]] || echo "      ^ WARNING: expected <speaker>__<test_id>__<correct|wrong>"
done
[ "$found" = 0 ] && echo "Nothing in raw/ - drag your exported recordings there first."
exit 0
