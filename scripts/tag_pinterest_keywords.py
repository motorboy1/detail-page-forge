#!/usr/bin/env python3
"""Tag Pinterest images with D1000 principle IDs using keyword matching.

No API needed. Maps D1000 principles to English design keywords,
then matches against Pinterest alt_text/title/description.
"""

import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "d1000_knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "pinterest_index.json"
TAGGED_FILE = KNOWLEDGE_DIR / "pinterest_tagged.json"

# D1000 principle -> English design keyword mapping
# Each principle mapped to visual/design characteristics
PRINCIPLE_KEYWORDS = {
    1: {  # 4개의점 (4 points / rule of thirds)
        "name": "4개의점",
        "keywords": ["grid", "thirds", "intersection", "four points", "rule of thirds",
                     "grid layout", "composition grid", "divided", "quadrant"],
        "weight": 1.0,
    },
    2: {  # 찌르기권법 (piercing punch)
        "name": "찌르기권법",
        "keywords": ["bold text", "large text", "impact", "punch", "bold typography",
                     "oversized", "statement", "dramatic text", "headline", "big font",
                     "large font", "dominant text", "powerful"],
        "weight": 1.0,
    },
    3: {  # 비워내기의미학 (aesthetics of emptying)
        "name": "비워내기의미학",
        "keywords": ["minimalist", "minimal", "white space", "negative space", "empty",
                     "clean", "simple", "sparse", "breathing room", "whitespace",
                     "less is more", "zen", "void"],
        "weight": 1.0,
    },
    4: {  # 아래절반만 (bottom half only)
        "name": "아래절반만",
        "keywords": ["bottom half", "lower half", "half composition", "bottom aligned",
                     "bottom section", "lower portion", "half page", "split horizontal"],
        "weight": 1.0,
    },
    5: {  # 군중속에서튀기 (stand out in crowd)
        "name": "군중속에서튀기",
        "keywords": ["stand out", "contrast", "highlight", "pop", "accent",
                     "focal point", "attention", "eye catching", "distinct",
                     "different color", "one element", "spotlight"],
        "weight": 1.0,
    },
    6: {  # S자무적조형 (S-curve composition)
        "name": "S자무적조형",
        "keywords": ["s curve", "curved", "flowing", "wave", "serpentine",
                     "organic flow", "sinuous", "undulating", "wavy line",
                     "curved line", "flow", "dynamic curve"],
        "weight": 1.0,
    },
    7: {  # 열쇠구멍디자인 (keyhole design)
        "name": "열쇠구멍디자인",
        "keywords": ["keyhole", "cutout", "peek", "window", "peeping",
                     "circular frame", "hole", "opening", "shape cutout",
                     "mask", "clipping mask", "through hole"],
        "weight": 1.0,
    },
    8: {  # 중력으로쌓기 (stacking with gravity)
        "name": "중력으로쌓기",
        "keywords": ["stacked", "stacking", "layered", "piled", "vertical stack",
                     "gravity", "accumulated", "built up", "tower",
                     "overlapping layers", "heap"],
        "weight": 1.0,
    },
    9: {  # 중대소의법칙 (big-medium-small rule)
        "name": "중대소의법칙",
        "keywords": ["size hierarchy", "scale variation", "big medium small",
                     "size contrast", "varied sizes", "hierarchy", "proportion",
                     "large medium small", "different sizes", "scaling"],
        "weight": 1.0,
    },
    10: {  # 빼꼼레이아웃 (peek layout)
        "name": "빼꼼레이아웃",
        "keywords": ["peek", "peeking", "partial", "cropped", "partially hidden",
                     "emerging", "coming out", "revealing", "half visible",
                     "behind", "overlapping edge"],
        "weight": 1.0,
    },
    11: {  # 수평선레이아웃 (horizon layout)
        "name": "수평선레이아웃",
        "keywords": ["horizon", "horizontal line", "horizontal layout", "landscape",
                     "horizontal divide", "horizon line", "panoramic",
                     "wide format", "horizontal split"],
        "weight": 1.0,
    },
    12: {  # 위아래로만넣기 (top and bottom only)
        "name": "위아래로만넣기",
        "keywords": ["top bottom", "header footer", "top and bottom", "vertical split",
                     "upper lower", "two sections", "divided vertical",
                     "top section bottom section"],
        "weight": 1.0,
    },
    13: {  # 쿵더러러구조 (boom structure / rhythm)
        "name": "쿵더러러구조",
        "keywords": ["rhythm", "repetition", "pattern", "sequential", "beat",
                     "cadence", "recurring", "modular", "repeated elements",
                     "systematic", "series"],
        "weight": 1.0,
    },
    14: {  # 무작정막아버리기 (blocking)
        "name": "무작정막아버리기",
        "keywords": ["blocking", "block", "covering", "overlapping", "obstruct",
                     "bar across", "stripe", "band", "overlay bar",
                     "crossing element", "barrier"],
        "weight": 1.0,
    },
    15: {  # 무적의631비율 (6:3:1 ratio)
        "name": "무적의631비율",
        "keywords": ["ratio", "proportion", "6 3 1", "color ratio", "dominant",
                     "secondary", "accent color", "color proportion",
                     "balanced composition", "color balance"],
        "weight": 1.0,
    },
    16: {  # 테두리로몰아넣기 (border framing)
        "name": "테두리로몰아넣기",
        "keywords": ["border", "frame", "framing", "bordered", "outline",
                     "surrounded", "enclosed", "contained", "box frame",
                     "decorative border", "margin"],
        "weight": 1.0,
    },
    17: {  # 화면속의화면 (screen within screen)
        "name": "화면속의화면",
        "keywords": ["screen within", "nested", "frame within", "picture in picture",
                     "inset", "window within", "mockup", "device screen",
                     "phone screen", "monitor display", "screen in screen"],
        "weight": 1.0,
    },
    18: {  # 스티커붙이기 (sticker placement)
        "name": "스티커붙이기",
        "keywords": ["sticker", "badge", "label", "tag", "stamp", "seal",
                     "emblem", "decal", "patch", "placed on top", "floating element"],
        "weight": 1.0,
    },
    20: {  # 거울효과 (mirror effect)
        "name": "거울효과",
        "keywords": ["mirror", "reflection", "symmetry", "symmetric", "reflected",
                     "mirrored", "flip", "bilateral", "mirror image"],
        "weight": 1.0,
    },
    21: {  # 동트는색상 (dawn colors / gradient)
        "name": "동트는색상",
        "keywords": ["gradient", "dawn", "sunrise", "warm tones", "color transition",
                     "ombre", "fading color", "pastel gradient", "soft colors",
                     "blending colors", "color fade"],
        "weight": 1.0,
    },
    23: {  # 종이를찢어버리기 (paper tear)
        "name": "종이를찢어버리기",
        "keywords": ["torn", "tear", "ripped", "paper tear", "torn paper",
                     "ripped edge", "jagged edge", "torn effect", "paper rip",
                     "collage", "cut paper"],
        "weight": 1.0,
    },
    24: {  # 스포트라이트비추기 (spotlight)
        "name": "스포트라이트비추기",
        "keywords": ["spotlight", "light beam", "illuminated", "lit up",
                     "focused light", "dramatic lighting", "highlight beam",
                     "light effect", "glow", "radiant"],
        "weight": 1.0,
    },
    26: {  # 끄트머리접어주기 (corner fold)
        "name": "끄트머리접어주기",
        "keywords": ["fold", "corner fold", "folded", "bent corner", "page curl",
                     "dog ear", "turned corner", "paper fold", "crease"],
        "weight": 1.0,
    },
    28: {  # 금속질감넣기 (metallic texture)
        "name": "금속질감넣기",
        "keywords": ["metallic", "metal", "chrome", "silver", "gold foil",
                     "shiny", "glossy", "reflective surface", "brushed metal",
                     "foil", "holographic", "iridescent"],
        "weight": 1.0,
    },
    30: {  # 기본도형일러스트 (basic shape illustration)
        "name": "기본도형일러스트",
        "keywords": ["geometric", "shapes", "circle", "triangle", "rectangle",
                     "basic shapes", "abstract shapes", "geometric illustration",
                     "simple shapes", "polygon", "square"],
        "weight": 1.0,
    },
    31: {  # 텍스트와이미지겹치기 (text-image overlap)
        "name": "텍스트와이미지겹치기",
        "keywords": ["text overlay", "text on image", "overlapping text",
                     "text over photo", "typography overlay", "words on image",
                     "lettering over", "text image blend", "superimposed text"],
        "weight": 1.0,
    },
    32: {  # 픽셀얼룩넣기 (pixel smudge)
        "name": "픽셀얼룩넣기",
        "keywords": ["pixel", "pixelated", "glitch", "digital artifact",
                     "distortion", "corrupted", "data moshing", "pixel art",
                     "digital noise", "8 bit"],
        "weight": 1.0,
    },
    36: {  # 매쉬그래디언트 (mesh gradient)
        "name": "매쉬그래디언트",
        "keywords": ["mesh gradient", "gradient mesh", "smooth gradient",
                     "multi color gradient", "aurora", "fluid gradient",
                     "organic gradient", "blurred colors", "gradient blob"],
        "weight": 1.0,
    },
    37: {  # 디자인툴을그리기 (drawing design tools)
        "name": "디자인툴을그리기",
        "keywords": ["hand drawn", "sketch", "illustration", "drawing",
                     "handwritten", "doodle", "pencil", "brush stroke",
                     "artistic", "freehand", "illustrated"],
        "weight": 1.0,
    },
    38: {  # 별넣어버리기 (adding stars)
        "name": "별넣어버리기",
        "keywords": ["star", "stars", "sparkle", "twinkle", "asterisk",
                     "star shape", "starburst", "celestial", "star decoration",
                     "glitter", "shine"],
        "weight": 1.0,
    },
    39: {  # 갑자기블러하기 (sudden blur)
        "name": "갑자기블러하기",
        "keywords": ["blur", "blurred", "blurry", "out of focus", "defocused",
                     "gaussian blur", "motion blur", "depth of field",
                     "bokeh", "soft focus"],
        "weight": 1.0,
    },
    41: {  # 대충그려버리기 (rough drawing)
        "name": "대충그려버리기",
        "keywords": ["rough", "scribble", "messy", "raw", "unfinished",
                     "casual drawing", "loose sketch", "imperfect",
                     "hand scrawled", "crude"],
        "weight": 1.0,
    },
    43: {  # 화살표로다이어버리기 (arrows everywhere)
        "name": "화살표로다이어버리기",
        "keywords": ["arrow", "arrows", "direction", "pointer", "pointing",
                     "directional", "arrow graphic", "navigation arrow"],
        "weight": 1.0,
    },
    45: {  # 그림자활용하기 (shadow utilization)
        "name": "그림자활용하기",
        "keywords": ["shadow", "drop shadow", "shadow effect", "silhouette",
                     "cast shadow", "long shadow", "shadow play", "dark shadow"],
        "weight": 1.0,
    },
    46: {  # 그냥스크린샷찍기 (just take a screenshot)
        "name": "그냥스크린샷찍기",
        "keywords": ["screenshot", "screen capture", "ui screenshot", "app screen",
                     "interface", "website screenshot", "browser window",
                     "screen grab", "desktop capture"],
        "weight": 1.0,
    },
    47: {  # 희멀겋게만들기 (making it hazy/faded)
        "name": "희멀겋게만들기",
        "keywords": ["faded", "hazy", "washed out", "muted", "desaturated",
                     "pale", "soft", "ethereal", "dreamy", "foggy",
                     "pastel", "light tones", "low contrast"],
        "weight": 1.0,
    },
    49: {  # 물방울효과 (water drop effect)
        "name": "물방울효과",
        "keywords": ["water", "droplet", "water drop", "liquid", "wet",
                     "rain", "splash", "bubble", "dew", "aqua",
                     "fluid", "water effect"],
        "weight": 1.0,
    },
    50: {  # 도면공개하기 (revealing blueprints)
        "name": "도면공개하기",
        "keywords": ["blueprint", "wireframe", "schematic", "technical drawing",
                     "floor plan", "architectural", "diagram", "layout plan",
                     "construction", "draft", "technical"],
        "weight": 1.0,
    },
}

# Additional general design keywords for broader matching
GENERAL_DESIGN_KEYWORDS = {
    "typography": [2, 31],
    "poster": [2, 5, 13],
    "layout": [1, 11, 12],
    "composition": [1, 9, 15],
    "color": [15, 21, 36],
    "texture": [28, 32],
    "illustration": [30, 37, 41],
    "photo": [31, 39, 47],
    "modern": [3, 36],
    "vintage": [23, 47],
    "abstract": [6, 30, 36],
    "branding": [5, 16, 18],
    "editorial": [1, 9, 13],
}


def score_pin(pin, principles):
    """Score a pin against all principles using keyword matching."""
    # Combine all text from the pin
    text_parts = []
    if pin.get("alt_text"):
        text_parts.append(pin["alt_text"].lower())
    if pin.get("title"):
        text_parts.append(pin["title"].lower())
    if pin.get("description"):
        text_parts.append(pin["description"].lower())

    full_text = " ".join(text_parts)
    if not full_text.strip():
        return []

    scores = {}

    # Score against principle keywords
    for pid, pdata in principles.items():
        score = 0
        matched_keywords = []
        for kw in pdata["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in full_text:
                # Longer keywords get higher scores
                bonus = len(kw.split()) * 0.5
                score += (1.0 + bonus) * pdata["weight"]
                matched_keywords.append(kw)
        if score > 0:
            scores[pid] = {"score": score, "keywords": matched_keywords}

    # Also check general keywords
    for gkw, pids in GENERAL_DESIGN_KEYWORDS.items():
        if gkw in full_text:
            for pid in pids:
                if pid in scores:
                    scores[pid]["score"] += 0.3
                elif pid in principles:
                    scores[pid] = {"score": 0.3, "keywords": [f"general:{gkw}"]}

    # Sort by score, return top 3
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    results = []
    for pid, data in sorted_scores[:3]:
        if data["score"] >= 0.8:  # Minimum threshold
            confidence = "high" if data["score"] >= 2.0 else "medium" if data["score"] >= 1.0 else "low"
            results.append({
                "principle_id": pid,
                "score": round(data["score"], 2),
                "confidence": confidence,
                "matched_keywords": data["keywords"][:5],
            })

    return results


def main():
    print("Loading Pinterest index...")
    pins = json.loads(INDEX_FILE.read_text())
    print(f"Loaded {len(pins)} pins")

    tagged_count = 0
    untagged_count = 0
    tag_distribution = Counter()
    confidence_dist = Counter()

    for pin in pins:
        tags = score_pin(pin, PRINCIPLE_KEYWORDS)

        if tags:
            pin["d1000_tags"] = [t["principle_id"] for t in tags]
            pin["d1000_tag_details"] = tags
            pin["tag_confidence"] = tags[0]["confidence"]
            tagged_count += 1
            for t in tags:
                tag_distribution[t["principle_id"]] += 1
                confidence_dist[t["confidence"]] += 1
        else:
            pin["d1000_tags"] = []
            pin["d1000_tag_details"] = []
            pin["tag_confidence"] = "untagged"
            untagged_count += 1

    # Save
    TAGGED_FILE.write_text(json.dumps(pins, indent=2, ensure_ascii=False))

    print(f"\n{'='*50}")
    print("RESULTS:")
    print(f"  Tagged: {tagged_count} pins ({tagged_count*100//len(pins)}%)")
    print(f"  Untagged: {untagged_count} pins")
    print("\nConfidence distribution:")
    for conf, cnt in confidence_dist.most_common():
        print(f"  {conf}: {cnt}")

    print("\nTop 15 principles by pin count:")
    for pid, cnt in tag_distribution.most_common(15):
        name = PRINCIPLE_KEYWORDS.get(pid, {}).get("name", f"#{pid}")
        print(f"  #{pid:2d} {name}: {cnt} pins")

    # Show untagged principles
    all_pids = set(PRINCIPLE_KEYWORDS.keys())
    tagged_pids = set(tag_distribution.keys())
    missing = all_pids - tagged_pids
    if missing:
        print(f"\nPrinciples with 0 pins: {sorted(missing)}")

    print(f"\nSaved to: {TAGGED_FILE}")


if __name__ == "__main__":
    main()
