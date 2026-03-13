#!/usr/bin/env python3
"""Enhanced D1000 tagging with expanded keywords + color + pattern matching."""

import json
import re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "data" / "d1000_knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "pinterest_index.json"
TAGGED_FILE = KNOWLEDGE_DIR / "pinterest_tagged.json"

# Complete 50 principle keyword mapping
P = {
    1:  ("4개의점", ["grid", "thirds", "intersection", "four points", "rule of thirds", "divided", "quadrant", "grid system", "alignment"]),
    2:  ("찌르기권법", ["bold text", "large text", "impact", "punch", "bold typography", "oversized", "statement", "dramatic text", "headline", "big font", "large font", "dominant text", "powerful", "huge text", "impactful"]),
    3:  ("비워내기의미학", ["minimalist", "minimal", "white space", "negative space", "empty", "clean design", "simple", "sparse", "breathing room", "zen", "less is more"]),
    4:  ("아래절반만", ["bottom half", "lower half", "half composition", "bottom aligned", "lower portion", "half page", "bottom heavy"]),
    5:  ("군중속에서튀기", ["stand out", "contrast", "highlight", "pop", "accent", "focal point", "eye catching", "distinct", "different color", "one element"]),
    6:  ("S자무적조형", ["s curve", "curved", "flowing", "wave", "serpentine", "organic flow", "sinuous", "wavy", "dynamic curve", "flowing line"]),
    7:  ("열쇠구멍디자인", ["keyhole", "cutout", "peek through", "circular frame", "shape cutout", "clipping mask", "mask shape", "peephole"]),
    8:  ("중력으로쌓기", ["stacked", "stacking", "layered", "piled", "vertical stack", "gravity", "accumulated", "overlapping layers", "layers"]),
    9:  ("중대소의법칙", ["size hierarchy", "scale variation", "big medium small", "size contrast", "varied sizes", "different sizes", "scaling", "hierarchy"]),
    10: ("빼꼼레이아웃", ["peek", "peeking", "partial", "cropped", "partially hidden", "emerging", "half visible", "coming out", "revealing"]),
    11: ("수평선레이아웃", ["horizon", "horizontal line", "horizontal layout", "landscape line", "horizontal divide", "panoramic", "wide format"]),
    12: ("위아래로만넣기", ["top bottom", "header footer", "top and bottom", "upper lower", "two sections", "split horizontal", "top text bottom text"]),
    13: ("쿵더러러구조", ["rhythm", "repetition", "pattern", "sequential", "beat", "recurring", "modular", "repeated elements", "series", "sequence"]),
    14: ("무작정막아버리기", ["blocking", "block", "covering", "bar across", "stripe across", "band", "overlay bar", "crossing element", "barrier", "stripe"]),
    15: ("무적의631비율", ["ratio", "proportion", "color ratio", "dominant secondary accent", "color balance", "balanced composition", "color scheme"]),
    16: ("테두리로몰아넣기", ["border", "frame", "framing", "bordered", "outline", "enclosed", "contained", "box frame", "decorative border", "margin"]),
    17: ("화면속의화면", ["screen within", "nested", "frame within", "picture in picture", "inset", "mockup", "device screen", "phone screen", "monitor"]),
    18: ("스티커붙이기", ["sticker", "badge", "label", "tag", "stamp", "seal", "emblem", "decal", "patch", "floating element", "placed on"]),
    19: ("아치넣기", ["arch", "arc", "curved top", "arched", "dome shape", "semicircle", "rainbow shape", "archway"]),
    20: ("거울효과", ["mirror", "reflection", "symmetry", "symmetric", "reflected", "mirrored", "flip", "bilateral"]),
    21: ("동트는색상", ["gradient", "dawn", "sunrise", "warm tones", "color transition", "ombre", "fading color", "pastel gradient", "soft colors"]),
    22: ("옛날사진만들기", ["vintage", "retro", "old photo", "aged", "nostalgic", "antique", "sepia", "faded photo", "old fashioned", "classic"]),
    23: ("종이를찢어버리기", ["torn", "tear", "ripped", "paper tear", "jagged edge", "torn effect", "collage", "cut paper", "ripped paper"]),
    24: ("스포트라이트비추기", ["spotlight", "light beam", "illuminated", "focused light", "dramatic lighting", "glow", "radiant", "lit up"]),
    25: ("꿀렁꿀렁물결치기", ["wave", "ripple", "undulating", "wavy pattern", "water wave", "oscillating", "wave pattern", "fluid wave"]),
    26: ("끄트머리접어주기", ["fold", "corner fold", "folded", "bent corner", "page curl", "dog ear", "turned corner", "paper fold"]),
    27: ("스프레이뿌리기", ["spray", "splatter", "paint splash", "sprayed", "mist", "speckle", "scattered", "dots scattered", "spray paint"]),
    28: ("금속질감넣기", ["metallic", "metal", "chrome", "silver", "gold foil", "shiny", "glossy", "reflective", "foil", "holographic", "iridescent"]),
    29: ("입체감더하기", ["3d", "three dimensional", "depth", "perspective", "isometric", "dimensional", "3d effect", "embossed", "raised", "beveled"]),
    30: ("기본도형일러스트", ["geometric", "shapes", "circle", "triangle", "rectangle", "basic shapes", "abstract shapes", "polygon", "square", "hexagon"]),
    31: ("텍스트와이미지겹치기", ["text overlay", "text on image", "overlapping text", "text over photo", "typography overlay", "words on image", "superimposed", "text image"]),
    32: ("픽셀얼룩넣기", ["pixel", "pixelated", "glitch", "digital artifact", "distortion", "corrupted", "data moshing", "8 bit", "digital noise"]),
    33: ("네온사인만들기", ["neon", "neon sign", "glowing text", "neon light", "luminous", "neon color", "electric glow", "neon tube"]),
    34: ("포장되기전효과", ["unwrapped", "packaging", "package", "unwrap", "before packaging", "raw material", "unboxed", "product layout"]),
    35: ("두꺼운선으로감싸기", ["thick line", "bold outline", "heavy stroke", "thick border", "contour", "bold line", "outlined", "thick stroke"]),
    36: ("매쉬그래디언트", ["mesh gradient", "gradient mesh", "smooth gradient", "aurora", "fluid gradient", "organic gradient", "blurred colors", "gradient blob"]),
    37: ("디자인툴을그리기", ["hand drawn", "sketch", "illustration", "drawing", "handwritten", "doodle", "pencil", "brush stroke", "artistic", "freehand", "illustrated"]),
    38: ("별넣어버리기", ["star", "stars", "sparkle", "twinkle", "asterisk", "starburst", "celestial", "star decoration", "glitter", "shine"]),
    39: ("갑자기블러하기", ["blur", "blurred", "blurry", "out of focus", "defocused", "gaussian", "motion blur", "bokeh", "soft focus"]),
    40: ("물감번지기", ["watercolor", "ink blot", "paint bleed", "bleeding", "smudge", "ink wash", "water stain", "spreading ink", "blot"]),
    41: ("대충그려버리기", ["rough", "scribble", "messy", "raw", "unfinished", "casual drawing", "loose sketch", "imperfect", "crude", "scratchy"]),
    42: ("줄긋기효과", ["line drawing", "strikethrough", "underline", "line across", "ruled", "lined", "striped", "cross out", "line effect"]),
    43: ("화살표로다이어버리기", ["arrow", "arrows", "direction", "pointer", "pointing", "directional", "arrow graphic"]),
    44: ("빛줄기넣기", ["light ray", "sun ray", "beam of light", "light streak", "ray", "sunbeam", "lens flare", "light burst", "radial light"]),
    45: ("그림자활용하기", ["shadow", "drop shadow", "shadow effect", "silhouette", "cast shadow", "long shadow", "shadow play"]),
    46: ("그냥스크린샷찍기", ["screenshot", "screen capture", "ui screenshot", "app screen", "interface", "browser window", "screen grab", "website"]),
    47: ("희멀겋게만들기", ["faded", "hazy", "washed out", "muted", "desaturated", "pale", "ethereal", "dreamy", "foggy", "pastel", "low contrast"]),
    48: ("노이즈끼얹기", ["noise", "grain", "grainy", "film grain", "noisy", "textured", "gritty", "distressed texture"]),
    49: ("물방울효과", ["water", "droplet", "water drop", "liquid", "wet", "rain", "splash", "bubble", "dew", "aqua", "fluid"]),
    50: ("도면공개하기", ["blueprint", "wireframe", "schematic", "technical drawing", "floor plan", "architectural", "diagram", "layout plan", "technical"]),
}

# Broader design concept -> principle associations
CONCEPT_MAP = {
    # Typography patterns
    "typography": [2, 31, 42],
    "typographic": [2, 31],
    "lettering": [2, 31, 37],
    "font": [2, 31],
    "text": [2, 31],
    "type design": [2, 31],
    # Layout patterns
    "poster": [2, 5, 13, 9],
    "layout": [1, 11, 12],
    "composition": [1, 9, 15],
    "editorial": [1, 9, 13],
    "magazine": [1, 13, 31],
    # Color patterns
    "color": [15, 21],
    "colorful": [15, 21, 36],
    "monochrome": [3, 47],
    "black and white": [3, 47],
    "dark": [24, 33],
    "bright": [5, 21, 33],
    # Texture/Effect patterns
    "texture": [28, 48],
    "grunge": [41, 48],
    "distressed": [23, 41, 48],
    # Style patterns
    "modern": [3, 36, 30],
    "vintage": [22, 47],
    "retro": [22, 32],
    "abstract": [6, 30, 36],
    "organic": [6, 25, 40],
    # Object patterns
    "branding": [5, 16, 18],
    "logo": [5, 16, 30],
    "business card": [16, 3],
    "book cover": [31, 2, 16],
    "book": [31, 16],
    "album": [31, 17],
    "packaging": [34, 16],
    "product": [34, 17],
    "advertisement": [2, 5, 31],
    "ad ": [2, 5, 31],
    "banner": [2, 14, 31],
    "infographic": [30, 43, 50],
    "chart": [30, 42, 50],
    "graph": [30, 42, 50],
    "diagram": [50, 43, 30],
    "architecture": [50, 29, 1],
    "building": [29, 50],
    "photography": [39, 24, 47],
    "photo": [31, 39, 47],
    "portrait": [7, 10, 24],
    "face": [7, 10],
    "fashion": [5, 47, 22],
    "luxury": [28, 3],
    "premium": [28, 3],
    "event": [2, 33, 5],
    "exhibition": [3, 2, 50],
    "invitation": [16, 3, 21],
    "card": [16, 3],
    "social media": [17, 31, 2],
    "instagram": [17, 31],
    "web": [46, 17, 1],
    "mobile": [17, 46],
    "app": [17, 46],
}

# Color-based principle matching (hex dominant_color -> principle IDs)
def color_principles(hex_color):
    """Match dominant color to design principles."""
    if not hex_color or not hex_color.startswith("#"):
        return []
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except (ValueError, IndexError):
        return []
    
    results = []
    brightness = (r + g + b) / 3
    saturation = max(r, g, b) - min(r, g, b)
    
    # Very dark -> shadow/spotlight/neon principles
    if brightness < 40:
        results.extend([(24, 0.3), (33, 0.3), (45, 0.3)])
    # Very bright/white -> minimalist/empty
    elif brightness > 230:
        results.extend([(3, 0.4), (47, 0.3)])
    # Pastel/soft -> gradient/hazy
    elif brightness > 180 and saturation < 80:
        results.extend([(21, 0.3), (47, 0.3)])
    # Highly saturated -> color principles
    if saturation > 150:
        results.extend([(5, 0.3), (15, 0.2)])
    # Metallic range (grays with slight warm tint)
    if 100 < brightness < 200 and saturation < 30:
        results.extend([(28, 0.2)])
    
    return results


def score_pin(pin):
    """Score a pin against all D1000 principles."""
    text_parts = []
    if pin.get("alt_text"):
        text_parts.append(pin["alt_text"].lower())
    if pin.get("title"):
        text_parts.append(pin["title"].lower())
    if pin.get("description"):
        text_parts.append(pin["description"].lower())
    
    full_text = " ".join(text_parts)
    scores = {}
    
    # 1. Direct keyword matching
    for pid, (name, keywords) in P.items():
        for kw in keywords:
            if kw.lower() in full_text:
                bonus = len(kw.split()) * 0.5
                score = 1.0 + bonus
                if pid not in scores:
                    scores[pid] = {"score": 0, "keywords": []}
                scores[pid]["score"] += score
                scores[pid]["keywords"].append(kw)
    
    # 2. Concept mapping (broader associations)
    for concept, pids in CONCEPT_MAP.items():
        if concept in full_text:
            for i, pid in enumerate(pids):
                weight = 0.5 - (i * 0.1)  # First principle gets more weight
                if weight < 0.1:
                    weight = 0.1
                if pid not in scores:
                    scores[pid] = {"score": 0, "keywords": []}
                scores[pid]["score"] += weight
                scores[pid]["keywords"].append(f"concept:{concept}")
    
    # 3. Color-based matching
    color_matches = color_principles(pin.get("dominant_color", ""))
    for pid, weight in color_matches:
        if pid not in scores:
            scores[pid] = {"score": 0, "keywords": []}
        scores[pid]["score"] += weight
        scores[pid]["keywords"].append(f"color:{pin.get('dominant_color', '')}")
    
    # Sort and return top 3
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    results = []
    for pid, data in sorted_scores[:3]:
        if data["score"] >= 0.5:
            confidence = "high" if data["score"] >= 2.0 else "medium" if data["score"] >= 1.0 else "low"
            results.append({
                "principle_id": pid,
                "score": round(data["score"], 2),
                "confidence": confidence,
                "matched_keywords": list(set(data["keywords"]))[:5],
            })
    return results


def main():
    pins = json.loads(INDEX_FILE.read_text())
    print(f"Loaded {len(pins)} pins")
    
    tag_dist = Counter()
    conf_dist = Counter()
    tagged = 0
    
    for pin in pins:
        tags = score_pin(pin)
        if tags:
            pin["d1000_tags"] = [t["principle_id"] for t in tags]
            pin["d1000_tag_details"] = tags
            pin["tag_confidence"] = tags[0]["confidence"]
            tagged += 1
            for t in tags:
                tag_dist[t["principle_id"]] += 1
                conf_dist[t["confidence"]] += 1
        else:
            pin["d1000_tags"] = []
            pin["d1000_tag_details"] = []
            pin["tag_confidence"] = "untagged"
    
    TAGGED_FILE.write_text(json.dumps(pins, indent=2, ensure_ascii=False))
    
    untagged = len(pins) - tagged
    print(f"\nTagged: {tagged}/{len(pins)} ({tagged*100//len(pins)}%)")
    print(f"Untagged: {untagged}")
    
    print(f"\nConfidence: {dict(conf_dist.most_common())}")
    
    print(f"\nTop 20 principles:")
    for pid, cnt in tag_dist.most_common(20):
        name = P.get(pid, ("?",))[0]
        print(f"  #{pid:2d} {name}: {cnt}")
    
    covered = set(tag_dist.keys())
    missing = set(P.keys()) - covered
    print(f"\nPrinciples covered: {len(covered)}/50")
    if missing:
        print(f"Uncovered: {sorted(missing)}")
    
    print(f"\nSaved: {TAGGED_FILE}")


if __name__ == "__main__":
    main()
