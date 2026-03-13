#!/usr/bin/env python3
"""Tag Pinterest images with D1000 principle IDs using Gemini Flash."""

import json
import os
import time
from pathlib import Path

# Setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "d1000_knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "pinterest_index.json"
TAGGED_FILE = KNOWLEDGE_DIR / "pinterest_tagged.json"
RAW_EXTRACTION = KNOWLEDGE_DIR / "raw_extraction.json"

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import google.genai as genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.0-flash"


def load_principles():
    """Load D1000 50 principles with summaries."""
    raw_data = json.loads(RAW_EXTRACTION.read_text())
    principles = {}
    for key, entry in raw_data.items():
        pid = int(key) if key.isdigit() else None
        if pid and 1 <= pid <= 50:
            title = entry.get("title", "")
            text = entry.get("text", "")[:300]  # First 300 chars as context
            principles[pid] = {"title": title, "summary": text}
    return principles


def build_principles_prompt(principles):
    """Build the principles reference for the prompt."""
    lines = []
    for pid in sorted(principles.keys()):
        p = principles[pid]
        lines.append(f"  ID {pid}: {p['title']} - {p['summary'][:100]}")
    return "\n".join(lines)


def tag_batch(pins_batch, principles_text):
    """Send a batch of pins to Gemini for tagging."""
    pins_desc = []
    for i, pin in enumerate(pins_batch):
        desc = f"Pin {i}: "
        parts = []
        if pin.get("alt_text"):
            parts.append(f"Visual: {pin['alt_text'][:150]}")
        if pin.get("title"):
            parts.append(f"Title: {pin['title'][:100]}")
        if pin.get("description"):
            parts.append(f"Desc: {pin['description'][:100]}")
        desc += " | ".join(parts) if parts else "(no description)"
        pins_desc.append(desc)

    prompt = f"""You are a design principle tagger. Given Pinterest design images described by their alt-text/title/description, tag each with the most relevant D1000 design principle IDs (1-50).

## D1000 Design Principles Reference:
{principles_text}

## Pinterest Pins to Tag:
{chr(10).join(pins_desc)}

## Instructions:
- For each Pin (0 to {len(pins_batch)-1}), output the most relevant principle IDs (1-3 max)
- If no principle matches well, output empty array
- These are Korean graphic design principles about layout, typography, color, effects, and composition
- Match based on the visual design TECHNIQUE shown, not the subject matter

## Output Format (JSON only, no markdown):
[
  {{"pin": 0, "tags": [1, 5], "confidence": "high"}},
  {{"pin": 1, "tags": [12], "confidence": "medium"}},
  {{"pin": 2, "tags": [], "confidence": "low"}}
]"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2000,
        ),
    )
    return response.text


def parse_tags(response_text):
    """Parse Gemini response to extract tags."""
    text = response_text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        elif "```" in text:
            text = text[:text.rindex("```")]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array in text
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return []


def main():
    print("Loading D1000 principles...")
    principles = load_principles()
    print(f"Loaded {len(principles)} principles")
    principles_text = build_principles_prompt(principles)

    print("Loading Pinterest index...")
    pins = json.loads(INDEX_FILE.read_text())
    print(f"Loaded {len(pins)} pins")

    # Load existing progress
    tagged = {}
    if TAGGED_FILE.exists():
        existing = json.loads(TAGGED_FILE.read_text())
        for p in existing:
            if p.get("d1000_tags"):
                tagged[p["id"]] = p["d1000_tags"]
        print(f"Existing tags: {len(tagged)} pins already tagged")

    BATCH_SIZE = 20
    batches = [pins[i:i+BATCH_SIZE] for i in range(0, len(pins), BATCH_SIZE)]
    print(f"Processing {len(batches)} batches of {BATCH_SIZE}")

    total_tagged = 0
    total_failed = 0

    for batch_idx, batch in enumerate(batches):
        # Skip if all pins in batch already tagged
        untagged = [p for p in batch if p["id"] not in tagged]
        if not untagged:
            print(f"[Batch {batch_idx+1}/{len(batches)}] All {len(batch)} pins already tagged, skipping")
            continue

        print(f"\n[Batch {batch_idx+1}/{len(batches)}] Tagging {len(untagged)} pins...")
        t0 = time.time()

        try:
            response_text = tag_batch(untagged, principles_text)
            results = parse_tags(response_text)

            for result in results:
                pin_idx = result.get("pin", -1)
                tags = result.get("tags", [])
                confidence = result.get("confidence", "unknown")
                if 0 <= pin_idx < len(untagged):
                    pin_id = untagged[pin_idx]["id"]
                    tagged[pin_id] = {
                        "principle_ids": tags,
                        "confidence": confidence,
                    }
                    total_tagged += 1

            elapsed = time.time() - t0
            print(f"  OK: {len(results)} tagged in {elapsed:.1f}s")

        except Exception as e:
            print(f"  ERROR: {e}")
            total_failed += len(untagged)

        # Rate limiting
        time.sleep(1)

    # Merge tags back into pins
    for pin in pins:
        tag_info = tagged.get(pin["id"], {})
        pin["d1000_tags"] = tag_info.get("principle_ids", [])
        pin["tag_confidence"] = tag_info.get("confidence", "untagged")

    # Save
    TAGGED_FILE.write_text(json.dumps(pins, indent=2, ensure_ascii=False))
    print(f"\n{'='*50}")
    print(f"COMPLETE: {total_tagged} newly tagged, {total_failed} failed")
    print(f"Saved to: {TAGGED_FILE}")

    # Stats
    from collections import Counter
    tag_counts = Counter()
    for pin in pins:
        for t in pin.get("d1000_tags", []):
            tag_counts[t] += 1

    tagged_count = sum(1 for p in pins if p.get("d1000_tags"))
    print(f"\nPins with tags: {tagged_count}/{len(pins)}")
    print(f"\nTop 10 principles by pin count:")
    for pid, cnt in tag_counts.most_common(10):
        p = principles.get(pid, {})
        print(f"  #{pid} {p.get('title', '?')}: {cnt} pins")


if __name__ == "__main__":
    main()
