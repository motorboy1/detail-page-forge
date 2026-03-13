"""D1000 Design Principles Module for detail-page-forge.

50 design principles from "디자인 천재인 척 하는 법" (D1000),
categorized and mapped to e-commerce detail page sections.

Includes detailed knowledge from the D1000 PDF textbook (170 pages).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ─── Categorized Design Principles ───────────────────────────────

PRINCIPLES = {
    # ═══ LAYOUT (레이아웃) ═══
    "layout": [
        {"id": 1, "name": "4개의 점", "rule": "화면을 9등분하여 교차점 4개에 핵심 요소 배치 (삼분법)"},
        {"id": 4, "name": "큰 요소+아래 몰기", "rule": "큰 이미지 하나를 상단에 두고 텍스트는 아래로 몰아넣기"},
        {"id": 9, "name": "중대소 법칙", "rule": "대중소가 아닌 중-대-소 순서로 배치하면 부자연스러우면서 매력적"},
        {"id": 12, "name": "위아래 붙이기", "rule": "요소 배치가 막막하면 화면 상단 또는 하단에 밀착 배치"},
        {"id": 22, "name": "망치 타이틀", "rule": "타이틀을 상단에 꽉 채워 띠처럼 연출하면 힙함"},
    ],
    # ═══ COMPOSITION (구도/조형) ═══
    "composition": [
        {"id": 2, "name": "물체 찌르기", "rule": "여러 요소가 있을 때 서로 겹치거나 침범하게 배치하면 역동적"},
        {"id": 5, "name": "대중 속 튀는 놈", "rule": "반복 패턴 속에 하나만 다르게 (각도, 색, 크기) 두면 시선 집중"},
        {"id": 6, "name": "S라인 조형", "rule": "곡선(S라인)을 넣으면 움직이는 느낌, 역동성 부여"},
        {"id": 8, "name": "무너진 탑", "rule": "정렬된 요소를 고의로 무너뜨리면 신선하고 실험적"},
        {"id": 13, "name": "큰놈+반복", "rule": "큰 요소 옆에 작은 반복 요소를 붙이면 리듬감과 밀도감 생성"},
    ],
    # ═══ VISUAL TRICK (시각 심리) ═══
    "visual_trick": [
        {"id": 3, "name": "미니멀 강인상", "rule": "아무것도 넣지 않는 여백이 오히려 가장 강한 인상"},
        {"id": 7, "name": "열쇠구멍 효과", "rule": "디자인에 구멍/틈을 만들면 안을 보고 싶은 호기심 유발"},
        {"id": 10, "name": "빼꼼 효과", "rule": "요소를 화면 가장자리에서 살짝만 보이게 하면 궁금증 유발"},
        {"id": 11, "name": "수평선 시선끌기", "rule": "강제 수평선을 그으면 본능적으로 시선이 따라감"},
        {"id": 14, "name": "막기 효과", "rule": "이미지를 가리면 열어보고 싶은 심리 자극"},
        {"id": 20, "name": "거울 효과", "rule": "요소를 반사/대칭시키면 프리미엄 느낌 상승"},
        {"id": 24, "name": "스포트라이트", "rule": "원형 하이라이트로 특정 요소를 강조하면 트래킹 효과"},
    ],
    # ═══ COLOR (색상) ═══
    "color": [
        {"id": 15, "name": "6:3:1 공식", "rule": "주색60% + 보조색30% + 강조색10% = 황금비율 색상 배분"},
        {"id": 21, "name": "동트는 색깔", "rule": "검정+흰색+포인트색의 3색 그래디언트, 어떤 배경에서든 존재감"},
        {"id": 36, "name": "블러 배경", "rule": "원들을 크게 블러하면 매쉬 그래디언트 = 트렌디한 배경"},
        {"id": 44, "name": "마침표 색깔", "rule": "마침표 하나에 포인트 색을 넣으면 조형성 20% 상승"},
        {"id": 47, "name": "빛바랜 색감", "rule": "저대비 색감으로 빈티지/아트 느낌 연출"},
    ],
    # ═══ TYPOGRAPHY (타이포그래피) ═══
    "typography": [
        {"id": 16, "name": "텍스트 채우기", "rule": "이미지 없으면 텍스트로 면을 꽉 채워서 밀도감 연출"},
        {"id": 17, "name": "낱말찾기 그리드", "rule": "텍스트를 그리드 형태로 배치하면 한 줄로도 충분한 디자인"},
        {"id": 25, "name": "텍스트 뿌리기", "rule": "텍스트를 후추처럼 여기저기 뿌리면 감각적"},
        {"id": 29, "name": "폰트 믹싱", "rule": "서로 다른 폰트(고딕+손글씨, 세리프+픽셀)를 섞으면 힙함"},
        {"id": 31, "name": "텍스트-이미지 겹침", "rule": "텍스트는 반드시 이미지와 겹쳐야 레이어감+프로 느낌"},
        {"id": 33, "name": "텍스트 테두리", "rule": "텍스트에 테두리(stroke)를 넣으면 레트로 감성"},
        {"id": 34, "name": "텍스트 속 이미지", "rule": "텍스트 배경을 이미지로 설정하면 독특한 비주얼"},
        {"id": 40, "name": "텍스트 모양 만들기", "rule": "작은 텍스트를 대량으로 모아 큰 형태를 만들면 창의적"},
    ],
    # ═══ DECORATION (장식 요소) ═══
    "decoration": [
        {"id": 18, "name": "스티커 채우기", "rule": "요소가 많으면 정리하지 말고 스티커처럼 덕지덕지 붙이기"},
        {"id": 23, "name": "종이 찢기", "rule": "찢어진 종이 효과로 레이어감과 재미 추가"},
        {"id": 26, "name": "모서리 접기", "rule": "끝부분을 접어서 입체감과 재미있는 디테일 추가"},
        {"id": 30, "name": "도형 일러스트", "rule": "기본 도형(원, 사각, 삼각)을 조합하면 간단한 일러스트 완성"},
        {"id": 35, "name": "괄호 남발", "rule": "괄호를 무작정 넣으면 선처럼 작용하여 디자인 밀도 상승"},
        {"id": 38, "name": "별 첨가", "rule": "별은 의미 중립적+예쁨, 어디에 넣어도 트렌디함 상승"},
        {"id": 41, "name": "낙서", "rule": "막 그린 손그림을 얹으면 캐주얼하고 인간적인 느낌"},
        {"id": 42, "name": "저작권 기호", "rule": "©™® 기호를 넣으면 조형적이고 힙한 느낌"},
        {"id": 43, "name": "화살표 연결", "rule": "단어들을 화살표로 이으면 시선 유도+스토리텔링"},
    ],
    # ═══ TEXTURE & EFFECT (질감/효과) ═══
    "texture": [
        {"id": 19, "name": "텍스트빵+이미지건포도", "rule": "텍스트 덩어리 사이에 이미지를 건포도처럼 끼워넣기"},
        {"id": 27, "name": "자연풍경 배경", "rule": "배경에 자연풍경을 넣으면 무조건 분위기 상승"},
        {"id": 28, "name": "금속 질감", "rule": "검정-회색-검정 그래디언트 = 금속 느낌 = 시크+프리미엄"},
        {"id": 32, "name": "픽셀 효과", "rule": "갑자기 픽셀을 넣으면 디지털/레트로 무드"},
        {"id": 37, "name": "툴 속의 툴", "rule": "디자인 툴 UI 요소(핸들, 바운딩박스)를 보여주면 메타적 재미"},
        {"id": 39, "name": "예측 못한 블러", "rule": "일부만 블러하면 초점+깊이감, 배경용으로도 활용"},
        {"id": 45, "name": "그림자 의미", "rule": "실루엣/그림자로 숨겨진 의미를 담으면 스토리텔링"},
        {"id": 46, "name": "스크린샷", "rule": "휴대폰/PC 화면 캡처 스타일로 구성하면 현대적+친숙"},
        {"id": 48, "name": "동그라미 꾸미기", "rule": "글자 속 O를 이미지로 대체해도 가독성 유지+독특함"},
        {"id": 49, "name": "물방울 연결", "rule": "요소를 물방울처럼 이어붙이면 유기적 흐름"},
        {"id": 50, "name": "도면 공개", "rule": "설계도/도면 스타일은 호기심 유발+전문적 느낌"},
    ],
}

# ─── Section-Principle Mapping for Detail Pages ──────────────────

SECTION_PRINCIPLE_MAP = {
    "hero": {
        "description": "히어로 섹션 - 첫인상, 시선 집중",
        "primary": [1, 4, 3],
        "accent": [11, 24, 27],
        "color": [15, 21],
    },
    "features": {
        "description": "특장점 섹션 - 정보 전달, 비교",
        "primary": [13, 5, 9],
        "accent": [35, 43, 42],
        "color": [15, 44],
    },
    "benefits": {
        "description": "혜택 섹션 - 감성 어필",
        "primary": [6, 31, 2],
        "accent": [38, 49, 36],
        "color": [21, 36],
    },
    "testimonials": {
        "description": "후기 섹션 - 신뢰 구축",
        "primary": [18, 25, 46],
        "accent": [41, 35, 44],
        "color": [47, 15],
    },
    "specs": {
        "description": "스펙 섹션 - 정밀 정보",
        "primary": [50, 17, 16],
        "accent": [28, 37, 43],
        "color": [28, 21],
    },
    "cta": {
        "description": "CTA 섹션 - 행동 유도",
        "primary": [22, 3, 14],
        "accent": [38, 20, 48],
        "color": [21, 44],
    },
    "guarantee": {
        "description": "보증 섹션 - 안심 제공",
        "primary": [24, 12, 20],
        "accent": [42, 30, 45],
        "color": [15, 28],
    },
    "social_proof": {
        "description": "소셜프루프 섹션 - 사회적 증거",
        "primary": [13, 18, 46],
        "accent": [38, 42, 35],
        "color": [47, 15],
    },
}

# ─── Category-Specific Principle Profiles ────────────────────────

CATEGORY_PROFILES = {
    "food": {
        "name": "식품",
        "hero": [27, 24, 4],
        "color_mood": "따뜻한 톤, 자연 컬러, 식욕 자극 레드/오렌지",
        "key_principles": [27, 24, 21, 39, 15],
    },
    "electronics": {
        "name": "가전/전자",
        "hero": [28, 3, 50],
        "color_mood": "차가운 톤, 금속 그래디언트, 테크 블루/실버",
        "key_principles": [28, 3, 50, 37, 20],
    },
    "fashion": {
        "name": "패션",
        "hero": [7, 10, 29],
        "color_mood": "모노톤+포인트, 빛바랜 색감, 트렌디",
        "key_principles": [7, 10, 29, 47, 33],
    },
    "beauty": {
        "name": "뷰티",
        "hero": [36, 6, 21],
        "color_mood": "파스텔+그래디언트, 매쉬, 부드러운 곡선",
        "key_principles": [36, 6, 21, 48, 49],
    },
    "health": {
        "name": "건강/헬스",
        "hero": [27, 11, 24],
        "color_mood": "그린+화이트, 클린, 자연 톤",
        "key_principles": [27, 11, 24, 3, 15],
    },
    "lifestyle": {
        "name": "라이프스타일",
        "hero": [18, 41, 29],
        "color_mood": "캐주얼 톤, 다채로운 컬러, 플레이풀",
        "key_principles": [18, 41, 29, 38, 32],
    },
}


# ─── Style Keyword Mapping (Mode 1: AI Auto-select) ──────────────

STYLE_KEYWORDS = {
    # Mood
    "고급": [3, 28, 20, 15, 24],
    "프리미엄": [28, 20, 3, 15, 50],
    "럭셔리": [28, 20, 24, 15, 45],
    "미니멀": [3, 11, 1, 15, 12],
    "깔끔": [3, 11, 15, 1, 12],
    "심플": [3, 11, 15, 1, 12],
    "따뜻한": [27, 21, 6, 49, 39],
    "포근한": [27, 21, 6, 49, 18],
    "자연스러운": [27, 6, 49, 39, 21],
    "역동적": [2, 8, 5, 6, 10],
    "활기찬": [2, 8, 5, 18, 38],
    "에너지": [2, 5, 22, 4, 16],
    "레트로": [33, 32, 47, 29, 42],
    "빈티지": [47, 33, 32, 29, 42],
    "복고": [33, 47, 32, 29, 26],
    "트렌디": [36, 29, 38, 42, 32],
    "힙한": [29, 42, 22, 33, 36],
    "모던": [3, 36, 28, 11, 22],
    "귀여운": [18, 41, 38, 30, 48],
    "캐주얼": [18, 41, 25, 29, 38],
    "재미있는": [23, 41, 18, 7, 10],
    "전문적": [50, 17, 28, 11, 15],
    "신뢰감": [50, 20, 24, 15, 28],
    "감성적": [39, 36, 6, 45, 47],
    "부드러운": [6, 36, 39, 49, 21],
    "강렬한": [4, 22, 16, 5, 24],
    "임팩트": [4, 22, 3, 14, 24],
    "실험적": [8, 32, 37, 25, 40],
    "클래식": [1, 15, 20, 11, 9],
}


# ─── D1000 Quick Guide Table (50 Principles) ─────────────────────

D1000_GUIDE = [
    # Layout
    {"id": 1,  "cat": "레이아웃", "name": "4개의 점",       "tip": "9등분 교차점에 핵심 배치 (삼분법)", "prompt": "삼분법 구도로 핵심 요소를 교차점에 배치"},
    {"id": 4,  "cat": "레이아웃", "name": "큰 요소+아래 몰기", "tip": "큰 이미지 상단, 텍스트 하단 몰기", "prompt": "히어로 이미지를 크게 상단에, 설명은 아래로"},
    {"id": 9,  "cat": "레이아웃", "name": "중대소 법칙",     "tip": "중-대-소 순서로 의외성 부여", "prompt": "요소 크기를 중-대-소 순서로 의외성 있게"},
    {"id": 12, "cat": "레이아웃", "name": "위아래 붙이기",    "tip": "막막하면 상단/하단에 밀착 배치", "prompt": "텍스트를 화면 상단 또는 하단 끝에 밀착"},
    {"id": 22, "cat": "레이아웃", "name": "망치 타이틀",     "tip": "타이틀 꽉 채워 띠처럼 연출", "prompt": "제목을 화면 전체 폭으로 띠처럼 크게"},
    # Composition
    {"id": 2,  "cat": "구도",    "name": "물체 찌르기",     "tip": "요소끼리 겹치게 배치 = 역동적", "prompt": "이미지와 텍스트가 서로 겹치게 역동적으로"},
    {"id": 5,  "cat": "구도",    "name": "대중 속 튀는 놈",  "tip": "반복 중 하나만 다르게 = 시선 집중", "prompt": "반복 패턴에서 하나만 색/크기/각도 다르게"},
    {"id": 6,  "cat": "구도",    "name": "S라인 조형",      "tip": "곡선으로 움직이는 역동성", "prompt": "S자 곡선 흐름으로 시선이 자연스럽게 흐르게"},
    {"id": 8,  "cat": "구도",    "name": "무너진 탑",       "tip": "정렬을 고의로 무너뜨리기 = 신선함", "prompt": "정렬을 일부러 깨서 신선하고 실험적으로"},
    {"id": 13, "cat": "구도",    "name": "큰놈+반복",       "tip": "큰 요소 옆에 작은 요소 반복", "prompt": "큰 메인 요소 옆에 작은 아이콘을 반복 배치"},
    # Visual Trick
    {"id": 3,  "cat": "시각심리", "name": "미니멀 강인상",    "tip": "여백이 가장 강한 인상", "prompt": "넓은 여백을 남겨 미니멀하지만 강렬하게"},
    {"id": 7,  "cat": "시각심리", "name": "열쇠구멍 효과",    "tip": "구멍/틈으로 호기심 유발", "prompt": "일부만 보이는 구멍 효과로 궁금증 유발"},
    {"id": 10, "cat": "시각심리", "name": "빼꼼 효과",       "tip": "가장자리에서 살짝만 보이기", "prompt": "이미지를 화면 가장자리에서 살짝만 보이게"},
    {"id": 11, "cat": "시각심리", "name": "수평선 시선끌기",   "tip": "수평선으로 시선 유도", "prompt": "강한 수평선으로 시선을 자연스럽게 유도"},
    {"id": 14, "cat": "시각심리", "name": "막기 효과",       "tip": "가리면 더 보고 싶은 심리", "prompt": "이미지 일부를 가려서 더 보고 싶게"},
    {"id": 20, "cat": "시각심리", "name": "거울 효과",       "tip": "반사/대칭 = 프리미엄 느낌", "prompt": "거울처럼 대칭 반사 효과로 고급스럽게"},
    {"id": 24, "cat": "시각심리", "name": "스포트라이트",     "tip": "원형 하이라이트로 강조", "prompt": "원형 스포트라이트로 핵심 제품을 강조"},
    # Color
    {"id": 15, "cat": "색상",    "name": "6:3:1 공식",     "tip": "주색60% + 보조30% + 강조10%", "prompt": "6:3:1 비율로 주색, 보조색, 강조색 배분"},
    {"id": 21, "cat": "색상",    "name": "동트는 색깔",     "tip": "검정+흰+포인트 = 만능 조합", "prompt": "검정-흰색-포인트 3색 조합으로 모던하게"},
    {"id": 36, "cat": "색상",    "name": "블러 배경",       "tip": "원 블러 = 매쉬 그래디언트", "prompt": "큰 원들을 블러 처리한 매쉬 그래디언트 배경"},
    {"id": 44, "cat": "색상",    "name": "마침표 색깔",     "tip": "마침표 하나에 포인트색 = 조형성 UP", "prompt": "제목 끝 마침표에만 포인트 색상을 넣어"},
    {"id": 47, "cat": "색상",    "name": "빛바랜 색감",     "tip": "저대비 = 빈티지/아트 느낌", "prompt": "채도를 낮추고 빛바랜 빈티지 색감으로"},
    # Typography
    {"id": 16, "cat": "타이포",  "name": "텍스트 채우기",    "tip": "이미지 없으면 텍스트로 면 채우기", "prompt": "텍스트만으로 화면을 꽉 채워 밀도감을"},
    {"id": 17, "cat": "타이포",  "name": "낱말찾기 그리드",   "tip": "텍스트를 그리드 형태로 배치", "prompt": "핵심 단어를 그리드 형태로 배열"},
    {"id": 25, "cat": "타이포",  "name": "텍스트 뿌리기",    "tip": "후추처럼 여기저기 뿌리기", "prompt": "키워드를 화면 곳곳에 흩뿌려 감각적으로"},
    {"id": 29, "cat": "타이포",  "name": "폰트 믹싱",       "tip": "다른 폰트 섞기 = 힙함", "prompt": "고딕+손글씨 등 서로 다른 폰트를 믹스"},
    {"id": 31, "cat": "타이포",  "name": "텍스트-이미지 겹침", "tip": "텍스트는 반드시 이미지 위에", "prompt": "텍스트를 이미지 위에 겹쳐 레이어감을"},
    {"id": 33, "cat": "타이포",  "name": "텍스트 테두리",    "tip": "테두리(stroke) = 레트로 감성", "prompt": "글자에 테두리를 넣어 레트로 감성"},
    {"id": 34, "cat": "타이포",  "name": "텍스트 속 이미지",  "tip": "글자 배경을 이미지로", "prompt": "큰 글자 안에 이미지가 보이게 클리핑"},
    {"id": 40, "cat": "타이포",  "name": "텍스트 모양 만들기", "tip": "작은 텍스트로 큰 형태 만들기", "prompt": "작은 글자를 대량으로 모아 큰 모양을"},
    # Decoration
    {"id": 18, "cat": "장식",    "name": "스티커 채우기",    "tip": "덕지덕지 붙이기 = 풍부함", "prompt": "스티커처럼 다양한 요소를 빽빽하게 붙여서"},
    {"id": 23, "cat": "장식",    "name": "종이 찢기",       "tip": "찢어진 효과 = 재미+레이어", "prompt": "종이를 찢은 듯한 테두리 효과로 재미있게"},
    {"id": 26, "cat": "장식",    "name": "모서리 접기",     "tip": "끝부분 접어 입체감 추가", "prompt": "모서리를 접은 것 같은 입체 효과를"},
    {"id": 30, "cat": "장식",    "name": "도형 일러스트",    "tip": "기본 도형 조합 = 간단 일러스트", "prompt": "원, 사각, 삼각을 조합해 간단한 일러스트를"},
    {"id": 35, "cat": "장식",    "name": "괄호 남발",       "tip": "괄호 = 선 효과+밀도 상승", "prompt": "괄호()를 장식으로 활용해 밀도감을"},
    {"id": 38, "cat": "장식",    "name": "별 첨가",        "tip": "별은 어디든 트렌디함 상승", "prompt": "별 장식을 곳곳에 넣어 트렌디하게"},
    {"id": 41, "cat": "장식",    "name": "낙서",           "tip": "손그림 = 캐주얼+인간적 느낌", "prompt": "손으로 그린 듯한 낙서 일러스트를 추가"},
    {"id": 42, "cat": "장식",    "name": "저작권 기호",     "tip": "CTR 기호 = 조형적 힙함", "prompt": "CTR 기호를 장식 요소로 활용"},
    {"id": 43, "cat": "장식",    "name": "화살표 연결",     "tip": "화살표로 시선 유도+스토리텔링", "prompt": "단어를 화살표로 이어 시선 유도"},
    # Texture
    {"id": 19, "cat": "질감",    "name": "텍스트빵+이미지건포도", "tip": "텍스트 사이에 이미지 끼워넣기", "prompt": "텍스트 사이사이에 작은 이미지를 끼워넣어"},
    {"id": 27, "cat": "질감",    "name": "자연풍경 배경",    "tip": "자연 사진 = 무조건 분위기 UP", "prompt": "배경에 자연풍경 사진을 넣어 분위기를"},
    {"id": 28, "cat": "질감",    "name": "금속 질감",       "tip": "검-회-검 그래디언트 = 프리미엄", "prompt": "금속 그래디언트로 프리미엄하게"},
    {"id": 32, "cat": "질감",    "name": "픽셀 효과",       "tip": "갑자기 픽셀 = 디지털/레트로", "prompt": "일부 요소를 픽셀화해서 디지털 레트로 무드"},
    {"id": 37, "cat": "질감",    "name": "툴 속의 툴",      "tip": "디자인 툴 UI 보여주기 = 메타", "prompt": "디자인 툴의 핸들/바운딩박스 메타 효과"},
    {"id": 39, "cat": "질감",    "name": "예측 못한 블러",   "tip": "일부만 블러 = 초점+깊이감", "prompt": "일부만 블러 처리해서 초점과 깊이감을"},
    {"id": 45, "cat": "질감",    "name": "그림자 의미",     "tip": "실루엣으로 숨겨진 의미 전달", "prompt": "그림자/실루엣으로 숨겨진 의미를 표현"},
    {"id": 46, "cat": "질감",    "name": "스크린샷",       "tip": "화면 캡처 스타일 = 현대적+친숙", "prompt": "스마트폰/PC 화면 속에 제품을 담아"},
    {"id": 48, "cat": "질감",    "name": "동그라미 꾸미기",  "tip": "글자 속 O를 이미지로 대체", "prompt": "글자 속 O를 제품 이미지로 대체해서"},
    {"id": 49, "cat": "질감",    "name": "물방울 연결",     "tip": "유기적 흐름으로 연결", "prompt": "요소를 물방울처럼 유기적으로 이어붙여"},
    {"id": 50, "cat": "질감",    "name": "도면 공개",       "tip": "설계도 스타일 = 전문적 호기심", "prompt": "설계도/도면 스타일로 전문적 호기심 유발"},
]

# Category labels for UI grouping
CATEGORY_LABELS = {
    "레이아웃": {"icon": "📐", "ids": [1, 4, 9, 12, 22]},
    "구도":    {"icon": "🔀", "ids": [2, 5, 6, 8, 13]},
    "시각심리": {"icon": "👁", "ids": [3, 7, 10, 11, 14, 20, 24]},
    "색상":    {"icon": "🎨", "ids": [15, 21, 36, 44, 47]},
    "타이포":  {"icon": "🔤", "ids": [16, 17, 25, 29, 31, 33, 34, 40]},
    "장식":    {"icon": "✨", "ids": [18, 23, 26, 30, 35, 38, 41, 42, 43]},
    "질감":    {"icon": "🧱", "ids": [19, 27, 28, 32, 37, 39, 45, 46, 48, 49, 50]},
}

# Style presets for quick selection
STYLE_PRESETS = {
    "고급 미니멀": [3, 28, 20, 15, 11, 1],
    "따뜻한 자연": [27, 21, 6, 49, 39, 15],
    "트렌디 힙": [36, 29, 38, 42, 33, 22],
    "활기찬 역동": [2, 8, 5, 18, 38, 4],
    "레트로 빈티지": [33, 32, 47, 29, 42, 26],
    "전문 신뢰": [50, 17, 28, 11, 15, 20],
}


def get_principle(principle_id: int) -> dict | None:
    """Get a single principle by ID."""
    for category in PRINCIPLES.values():
        for p in category:
            if p["id"] == principle_id:
                return p
    return None


def get_section_prompt(section_type: str, category: str = "general") -> str:
    """Generate design guidance prompt for a specific section and product category."""
    section = SECTION_PRINCIPLE_MAP.get(section_type)
    if not section:
        return ""

    profile = CATEGORY_PROFILES.get(category)

    lines = [f"[디자인 원리 가이드 - {section['description']}]"]

    lines.append("적용할 핵심 원리:")
    for pid in section["primary"]:
        p = get_principle(pid)
        if p:
            lines.append(f"  - {p['name']}: {p['rule']}")

    lines.append("장식/강조 원리:")
    for pid in section["accent"][:2]:
        p = get_principle(pid)
        if p:
            lines.append(f"  - {p['name']}: {p['rule']}")

    lines.append("색상 원리:")
    for pid in section["color"]:
        p = get_principle(pid)
        if p:
            lines.append(f"  - {p['name']}: {p['rule']}")

    if profile:
        lines.append(f"카테고리 무드 ({profile['name']}): {profile['color_mood']}")

    return "\n".join(lines)


def get_system_prompt_compact() -> str:
    """Get a compact version of all principles for system prompt injection."""
    return """[D1000 디자인 원리 - 상세페이지 최적화]

■ 레이아웃
- 9등분 교차점 4개에 핵심 배치 (삼분법)
- 큰 이미지 상단 + 텍스트 하단 몰기
- 중-대-소 순서 배치 (의외성 = 매력)
- 타이틀을 상단 꽉 채워 띠로 연출

■ 시선 유도
- 반복 속 하나만 다르게 → 시선 집중
- 수평선 = 본능적 시선 끌기
- 스포트라이트(원형 하이라이트) = 강조
- 빼꼼(일부만 보이기) = 궁금증 유발
- 화살표로 단어 연결 = 스토리텔링

■ 색상
- 6:3:1 (주60% + 보조30% + 강조10%)
- 동트는 3색 (검정+흰색+포인트) = 만능
- 매쉬 그래디언트 (원 블러) = 트렌디 배경
- 금속 질감 (검-회-검 그래디언트) = 프리미엄
- 마침표 하나에 색 = 조형성 +20%

■ 타이포
- 텍스트로 면 채우기 = 이미지 없어도 밀도감
- 폰트 믹싱 (고딕+손글씨) = 힙함
- 텍스트는 반드시 이미지와 겹칠 것
- 텍스트 테두리(stroke) = 레트로 감성

■ 장식
- 별(★) = 어디든 트렌디함 상승
- 괄호 () = 선처럼 작용, 밀도 상승
- ©™® 기호 = 조형적 힙함
- 스티커처럼 덕지덕지 = 풍부함
- 손낙서 = 캐주얼+인간적

■ 질감
- 자연풍경 배경 = 무조건 분위기 상승
- 일부 블러 = 초점+깊이감
- 스크린샷 스타일 = 현대적+친숙
- 도면/설계도 스타일 = 전문적 호기심"""


# ─── Mode 1: AI Auto-select from Description ─────────────────────

def match_principles_from_description(text: str) -> list[int]:
    """Match D1000 principle IDs from natural language style description."""
    matched = set()
    for keyword, principle_ids in STYLE_KEYWORDS.items():
        if keyword in text:
            matched.update(principle_ids)

    if not matched:
        # Default: universally useful principles
        matched = {1, 15, 3, 11, 4}

    return sorted(matched)


# ─── Mode 2/Hybrid: Custom Prompt from Selected Principles ───────

def get_custom_prompt(principle_ids: list[int]) -> str:
    """Generate AI design prompt from user-selected principle IDs."""
    if not principle_ids:
        return get_system_prompt_compact()

    lines = [f"[D1000 선택 디자인 원리 — {len(principle_ids)}개 적용]"]
    lines.append("")

    current_cat = ""
    for entry in D1000_GUIDE:
        if entry["id"] in principle_ids:
            if entry["cat"] != current_cat:
                current_cat = entry["cat"]
                lines.append(f"■ {current_cat}")
            lines.append(f"- #{entry['id']:02d} {entry['name']}: {entry['tip']}")

    lines.append("")
    lines.append("위 원리들을 카피와 디자인에 적극 반영하세요.")
    lines.append("각 섹션의 design_note에 적용한 원리 번호를 명시하세요.")

    return "\n".join(lines)


def get_guide_for_display() -> list[dict]:
    """Return guide data formatted for Streamlit table display."""
    return [
        {
            "번호": f"#{g['id']:02d}",
            "카테고리": g["cat"],
            "원리명": g["name"],
            "설명": g["tip"],
            "AI 프롬프트": g["prompt"],
        }
        for g in D1000_GUIDE
    ]

# ─── D1000 Detailed Knowledge (from PDF textbook) ────────────────

_KNOWLEDGE_CACHE: dict[int, str] | None = None

# Clean title mapping: raw PDF titles → clean principle names
_TITLE_CLEAN = {
    0: "서문 — 만들어질 디자인들 미리보기",
    1: "4개의 점을 기억할 것",
    2: "여러개 물체는 서로 찔러라",
    3: "강한 인상을 주려면 아무것도 넣지 마라",
    4: "큰 요소 하나가 들어가면 아래로 몰아넣어라",
    5: "대중 속에 튀는 놈을 넣으면 더 튄다",
    6: "S라인은 무적의 조형이다",
    7: "우리는 열쇠구멍을 궁금해한다",
    8: "무너진 탑처럼 디자인하면 신선하다",
    9: "대중소 말고 중대소를 활용하라",
    10: "빼꼼하면 궁금증이 생긴다",
    11: "우리는 수평선을 좋아한다",
    12: "모르겠으면 위나 아래에 붙여버려라",
    13: "큰놈 옆에는 반복되는 놈을 붙여라",
    14: "막아버리면 더 들어가보고 싶은 법",
    15: "6:3:1의 무적 공식",
    16: "텍스트밖에 없으면 그냥 채워버려라",
    17: "낱말찾기를 쓰면 텍스트 한줄로 충분하다",
    18: "스티커처럼 붙여라",
    19: "텍스트는 빵 이미지는 건포도",
    20: "거울은 신비롭다",
    21: "동트는 색깔을 활용하라",
    22: "망치로 두드리듯 타이틀을 치라",
    23: "종이를 찢어라",
    24: "스포트라이트를 비춰라",
    25: "텍스트를 후추처럼 뿌려라",
    26: "모서리를 접어라",
    27: "자연풍경을 깔아라",
    28: "금속 질감을 입혀라",
    29: "폰트를 섞어라",
    30: "도형으로 일러스트를 만들어라",
    31: "텍스트는 이미지와 겹쳐라",
    32: "픽셀을 넣어라",
    33: "텍스트에 테두리를 넣어라",
    34: "텍스트 속에 이미지를 넣어라",
    35: "괄호를 남발하라",
    36: "블러로 배경을 만들어라",
    37: "툴 속의 툴을 보여줘라",
    38: "별을 넣어라",
    39: "예측 못한 블러를 넣어라",
    40: "텍스트로 모양을 만들어라",
    41: "낙서를 더해라",
    42: "저작권 기호를 넣어라",
    43: "화살표로 연결하라",
    44: "마침표에 색깔을 넣어라",
    45: "그림자에 의미를 담아라",
    46: "스크린샷 스타일을 쓰라",
    47: "빛바랜 색감을 쓰라",
    48: "동그라미를 꾸며라",
    49: "물방울처럼 연결하라",
    50: "도면을 공개하라",
}


def _load_knowledge() -> dict[int, str]:
    """Load detailed knowledge from raw_extraction.json (lazy, cached)."""
    global _KNOWLEDGE_CACHE
    if _KNOWLEDGE_CACHE is not None:
        return _KNOWLEDGE_CACHE

    json_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "d1000_knowledge" / "raw_extraction.json"
    if not json_path.exists():
        _KNOWLEDGE_CACHE = {}
        return _KNOWLEDGE_CACHE

    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    knowledge: dict[int, str] = {}
    for key, entry in raw.items():
        pid = int(key)
        if pid == 0:
            continue  # Skip intro
        text = entry.get("text", "")
        # Clean up: remove repeated title fragments, normalize whitespace
        clean = re.sub(r"[A-Z]\s[A-Z]\s[A-Z]", "", text)  # Remove spaced-out English
        clean = re.sub(r"\*\d{3}", "", clean)  # Remove *001, *002 references
        knowledge[pid] = clean.strip()

    _KNOWLEDGE_CACHE = knowledge
    return _KNOWLEDGE_CACHE


def get_detailed_knowledge(principle_id: int) -> str | None:
    """Get detailed knowledge text for a principle from the PDF textbook.

    Returns the full explanation (1200-2200 chars) or None if not available.
    """
    knowledge = _load_knowledge()
    return knowledge.get(principle_id)


def get_knowledge_summary(principle_id: int, max_chars: int = 300) -> str | None:
    """Get a truncated summary of the detailed knowledge.

    Useful for tooltips and brief explanations.
    """
    full = get_detailed_knowledge(principle_id)
    if not full:
        return None
    # Find a clean sentence break near max_chars
    if len(full) <= max_chars:
        return full
    cut = full[:max_chars]
    last_period = cut.rfind(".")
    if last_period > max_chars // 2:
        return cut[:last_period + 1]
    return cut + "..."


def get_principle_title(principle_id: int) -> str | None:
    """Get the clean Korean title for a principle."""
    return _TITLE_CLEAN.get(principle_id)


def get_enriched_prompt(principle_ids: list[int], detail_level: str = "medium") -> str:
    """Generate AI design prompt enriched with detailed PDF knowledge.

    Args:
        principle_ids: List of principle IDs to include.
        detail_level: "brief" (tip only), "medium" (tip + 300 char summary),
                      "full" (tip + complete knowledge).
    """
    if not principle_ids:
        return get_system_prompt_compact()

    lines = [f"[D1000 디자인 원리 — {len(principle_ids)}개 적용 (상세 지식 포함)]"]
    lines.append("")

    current_cat = ""
    for entry in D1000_GUIDE:
        if entry["id"] not in principle_ids:
            continue

        if entry["cat"] != current_cat:
            current_cat = entry["cat"]
            lines.append(f"■ {current_cat}")

        title = get_principle_title(entry["id"]) or entry["name"]
        lines.append(f"### #{entry['id']:02d} {title}")
        lines.append(f"핵심: {entry['tip']}")
        lines.append(f"적용 지시: {entry['prompt']}")

        if detail_level == "medium":
            summary = get_knowledge_summary(entry["id"], 300)
            if summary:
                lines.append(f"상세: {summary}")
        elif detail_level == "full":
            full = get_detailed_knowledge(entry["id"])
            if full:
                lines.append(f"상세 설명:\n{full}")

        lines.append("")

    lines.append("위 원리들을 카피와 디자인에 적극 반영하세요.")
    lines.append("각 섹션의 design_note에 적용한 원리 번호와 키워드를 명시하세요.")

    return "\n".join(lines)


def search_knowledge(query: str, top_n: int = 5) -> list[dict]:
    """Search detailed knowledge for principles matching a query.

    Returns list of {id, name, title, relevance, snippet} dicts.
    """
    knowledge = _load_knowledge()
    results = []

    for pid, text in knowledge.items():
        if query in text:
            # Count occurrences as simple relevance
            count = text.count(query)
            # Extract snippet around first match
            idx = text.find(query)
            start = max(0, idx - 50)
            end = min(len(text), idx + len(query) + 100)
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            principle = get_principle(pid)
            results.append({
                "id": pid,
                "name": principle["name"] if principle else f"#{pid}",
                "title": get_principle_title(pid) or "",
                "relevance": count,
                "snippet": snippet,
            })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:top_n]

