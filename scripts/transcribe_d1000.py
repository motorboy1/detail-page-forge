#!/usr/bin/env python3
"""D1000 Video Transcription Pipeline.

Extracts audio from D1000 lecture videos and transcribes using Whisper.
Results saved as JSON per lecture with timestamps and segments.
"""

import json
import os
import re
import subprocess
import time
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "d1000_knowledge"
AUDIO_DIR = KNOWLEDGE_DIR / "audio"
TRANSCRIPTS_DIR = KNOWLEDGE_DIR / "transcripts"
MAPPING_FILE = KNOWLEDGE_DIR / "video_mapping.json"
PROGRESS_FILE = KNOWLEDGE_DIR / "transcription_progress.json"
FFMPEG = Path.home() / ".local" / "bin" / "ffmpeg"
DOWNLOADS_DIR = Path("/mnt/c/Users/USER/Downloads")


def find_video_files():
    videos = []
    for f in os.listdir(DOWNLOADS_DIR):
        fn_nfc = unicodedata.normalize("NFC", f)
        match = re.match(r"(\d+)강[_\-](.+?)\(예제(\d+)\)(?:\s*\(\d+\))?\.mp4$", fn_nfc)
        if match:
            lecture_num = int(match.group(1))
            topic = match.group(2).strip("-").strip()
            example_num = int(match.group(3))
            raw_path = DOWNLOADS_DIR / f
            videos.append({
                "lecture": lecture_num,
                "topic": topic,
                "example": example_num,
                "filename": fn_nfc,
                "raw_path": str(raw_path),
            })
    videos.sort(key=lambda x: (x["lecture"], x["example"]))
    return videos


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"completed": [], "failed": []}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, ensure_ascii=False))


def extract_audio(video_path, audio_path):
    result = subprocess.run(
        [str(FFMPEG), "-y", "-i", video_path,
         "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
         str(audio_path)],
        capture_output=True, text=True, timeout=300
    )
    return result.returncode == 0


def transcribe_audio(model, audio_path):
    result = model.transcribe(
        str(audio_path),
        language="ko",
        fp16=False,
    )
    return result


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    mapping = {}
    if MAPPING_FILE.exists():
        raw_mapping = json.loads(MAPPING_FILE.read_text())
        for lec_str, info in raw_mapping.items():
            mapping[int(lec_str)] = info.get("d1000_id")

    videos = find_video_files()
    print(f"Found {len(videos)} video files")

    progress = load_progress()
    completed_keys = set(progress["completed"])

    print("Loading Whisper model (base)...")
    import whisper
    model = whisper.load_model("base")
    print("Model loaded.")

    total = len(videos)
    done = 0
    skipped = 0
    failed = 0

    for i, video in enumerate(videos):
        key = f"{video['lecture']:02d}_{video['example']}"
        audio_path = AUDIO_DIR / f"lecture_{key}.wav"
        transcript_path = TRANSCRIPTS_DIR / f"lecture_{key}.json"

        if key in completed_keys and transcript_path.exists():
            skipped += 1
            print(f"[{i+1}/{total}] SKIP {video['filename']} (already done)")
            continue

        print(f"\n[{i+1}/{total}] Processing: {video['filename']}")

        t0 = time.time()
        try:
            ok = extract_audio(video["raw_path"], audio_path)
            if not ok:
                print(f"  ERROR: ffmpeg failed for {video['filename']}")
                progress["failed"].append({"key": key, "error": "ffmpeg failed"})
                save_progress(progress)
                failed += 1
                continue
        except subprocess.TimeoutExpired:
            print(f"  ERROR: ffmpeg timeout for {video['filename']}")
            progress["failed"].append({"key": key, "error": "ffmpeg timeout"})
            save_progress(progress)
            failed += 1
            continue
        audio_time = time.time() - t0

        t0 = time.time()
        try:
            result = transcribe_audio(model, audio_path)
        except Exception as e:
            print(f"  ERROR: Whisper failed: {e}")
            progress["failed"].append({"key": key, "error": str(e)})
            save_progress(progress)
            failed += 1
            if audio_path.exists():
                audio_path.unlink()
            continue
        whisper_time = time.time() - t0

        d1000_id = mapping.get(video["lecture"])
        transcript_data = {
            "lecture": video["lecture"],
            "example": video["example"],
            "topic": video["topic"],
            "d1000_principle_id": d1000_id,
            "filename": video["filename"],
            "text": result["text"],
            "text_length": len(result["text"]),
            "segments": [
                {
                    "id": seg["id"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                }
                for seg in result["segments"]
            ],
            "segment_count": len(result["segments"]),
            "processing": {
                "audio_extraction_seconds": round(audio_time, 1),
                "transcription_seconds": round(whisper_time, 1),
                "whisper_model": "base",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        }
        transcript_path.write_text(
            json.dumps(transcript_data, indent=2, ensure_ascii=False)
        )

        if audio_path.exists():
            audio_path.unlink()

        progress["completed"].append(key)
        completed_keys.add(key)
        save_progress(progress)
        done += 1

        print(f"  OK: {len(result['text'])} chars, {len(result['segments'])} segments")
        print(f"  Time: audio={audio_time:.1f}s, whisper={whisper_time:.1f}s")

    print(f"\n{'='*50}")
    print(f"COMPLETE: {done} transcribed, {skipped} skipped, {failed} failed")
    print(f"Total transcripts: {len(list(TRANSCRIPTS_DIR.glob('*.json')))}")

    test_wav = AUDIO_DIR / "test_01.wav"
    if test_wav.exists():
        test_wav.unlink()
        print("Cleaned up test audio file.")


if __name__ == "__main__":
    main()
