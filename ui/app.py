"""Detail Forge — Streamlit UI v2 (Phase 2 Synthesis Engine)."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the import path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


import streamlit as st
from ui.theme import inject_theme

st.set_page_config(
    page_title="Detail Forge — 상세페이지 AI 생성기",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

# ──────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────

def _init_session_state():
    defaults = {
        # Navigation
        "current_phase": 1,
        # Phase 1: Product info
        "product_name": "프리미엄 세라믹 뚝배기",
        "product_features": [
            "뛰어난 보온성으로 음식을 오랫동안 따뜻하게 유지",
            "균일한 열전도율로 재료가 골고루 익음",
            "인체에 무해한 친환경 세라믹 소재",
            "모던하고 심플한 디자인",
        ],
        "product_target": "20~40대 요리에 관심 있는 분",
        "product_price": "29,900원",
        "product_photos": [],
        # Phase 2: Template gallery
        "selected_template_ids": [],
        "filter_section_type": None,
        "filter_category": None,
        "filter_d1000": [],
        # Phase 3: Design studio
        "selected_recipe": "classic_trust",
        "custom_principle_ids": [],
        "copy_sections": [],
        "generation_result": None,
        "preview_device": "desktop",
        # Phase 4: Export
        "quality_scores": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session_state()

# ──────────────────────────────────────────────────────────────────
# Imports from the synthesis engine (lazy, inside functions)
# ──────────────────────────────────────────────────────────────────

def _load_core():
    from detail_forge.asset_pipeline.lecture_knowledge import LectureKnowledge
    from detail_forge.copywriter.generator import ProductInfo, SectionCopy
    from detail_forge.designer.d1000_principles import (
        CATEGORY_PROFILES,
        STYLE_KEYWORDS,
        STYLE_PRESETS,
    )
    from detail_forge.designer.design_tokens import DesignTokenSet
    from detail_forge.designer.theme_generator import ThemeGenerator
    from detail_forge.output.export_manager import ExportManager
    from detail_forge.output.naver_renderer import NaverRenderer
    from detail_forge.output.quality_gate import QualityGate
    from detail_forge.output.web_renderer import WebRenderer
    from detail_forge.synthesis.one_click_generator import OneClickGenerator
    from detail_forge.templates.search import TemplateSearcher
    from detail_forge.templates.store import TemplateStore
    store = TemplateStore()
    lecture_kb = LectureKnowledge()
    return {
        "store": store,
        "searcher": TemplateSearcher(store),
        "generator": OneClickGenerator(template_store=store),
        "theme_gen": ThemeGenerator(),
        "web_renderer": WebRenderer(),
        "naver_renderer": NaverRenderer(),
        "quality_gate": QualityGate(),
        "export_manager": ExportManager(),
        "ProductInfo": ProductInfo,
        "SectionCopy": SectionCopy,
        "DesignTokenSet": DesignTokenSet,
        "STYLE_PRESETS": STYLE_PRESETS,
        "CATEGORY_PROFILES": CATEGORY_PROFILES,
        "STYLE_KEYWORDS": STYLE_KEYWORDS,
        "lecture_kb": lecture_kb,
    }


@st.cache_resource
def _get_core():
    return _load_core()


# ──────────────────────────────────────────────────────────────────
# Sidebar navigation
# ──────────────────────────────────────────────────────────────────

def _render_sidebar():
    with st.sidebar:
        st.markdown(
            '<span class="pf-nav-logo">Detail Forge</span>'
            '<span class="pf-nav-subtitle">AI 상세페이지 자동 생성기 v2.0</span>',
            unsafe_allow_html=True,
        )
        st.divider()

        phases = [
            ("1. 상품 정보", 1, "📦"),
            ("2. 템플릿 갤러리", 2, "🖼"),
            ("3. 디자인 스튜디오", 3, "🎨"),
            ("4. 내보내기", 4, "📤"),
        ]
        for label, num, icon in phases:
            current = st.session_state.current_phase == num
            btn_type = "primary" if current else "secondary"
            if st.button(f"{icon} {label}", key=f"nav_{num}", use_container_width=True, type=btn_type):
                st.session_state.current_phase = num
                st.rerun()

        st.divider()

        # Quick status summary
        if st.session_state.product_name:
            st.caption(f"상품: {st.session_state.product_name[:20]}")
        tpl_count = len(st.session_state.selected_template_ids)
        if tpl_count:
            st.caption(f"선택된 템플릿: {tpl_count}개")
        if st.session_state.generation_result:
            st.caption("생성 완료")

        st.divider()
        st.caption("D1000 원리 기반 엔진")
        st.caption("Claude Sonnet 3.5")

        # ── Lecture Knowledge Browser ──────────────────
        st.divider()
        with st.expander("🎓 강의 인사이트 브라우저", expanded=False):
            try:
                c = _get_core()
                lecture_kb = c.get("lecture_kb")
                if lecture_kb:
                    all_insights = lecture_kb.load_index()
                    st.caption(f"{len(all_insights)}개 강의 인사이트 로드됨")
                    if all_insights:
                        # Group by principle
                        by_principle = {}
                        for ins in all_insights:
                            by_principle.setdefault(ins.principle_id, []).append(ins)
                        for pid in sorted(by_principle.keys()):
                            items = by_principle[pid]
                            st.markdown(f"**#{pid}** ({len(items)}개 강의)")
                            for ins in items:
                                st.caption(f"└ {ins.source_lecture}: {ins.insight_text[:60]}...")
                    else:
                        st.caption("전사 데이터 없음")
            except Exception:
                st.caption("강의 데이터 로드 실패")


# ──────────────────────────────────────────────────────────────────
# Progress indicator
# ──────────────────────────────────────────────────────────────────

def _render_progress():
    phase = st.session_state.current_phase
    steps = [
        ("01", "상품 정보"),
        ("02", "템플릿 선택"),
        ("03", "디자인 스튜디오"),
        ("04", "내보내기"),
    ]
    step_items = []
    for i, (num, label) in enumerate(steps, 1):
        if i < phase:
            cls = "pf-step pf-step--done"
            dot_inner = "&#10003;"
        elif i == phase:
            cls = "pf-step pf-step--active"
            dot_inner = num
        else:
            cls = "pf-step"
            dot_inner = num
        step_items.append(
            f'<div class="{cls}">'
            f'<div class="pf-step-dot">{dot_inner}</div>'
            f'<div class="pf-step-label">{label}</div>'
            f'</div>'
        )
    steps_html = f'<div class="pf-step-bar">{"".join(step_items)}</div>'
    st.markdown(steps_html, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# Phase 1: Product Info
# ──────────────────────────────────────────────────────────────────

def render_phase1():
    st.header("📦 Phase 1: 상품 정보 입력")
    st.caption("판매할 상품의 기본 정보를 입력하세요. 이 정보를 바탕으로 카피라이팅과 디자인이 생성됩니다.")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("기본 정보")
        st.session_state.product_name = st.text_input(
            "상품명 *",
            value=st.session_state.product_name,
            placeholder="예: 프리미엄 세라믹 뚝배기 세트",
        )

        features_text = st.text_area(
            "핵심 특징 (줄 단위로 입력) *",
            value="\n".join(st.session_state.product_features),
            height=180,
            placeholder="뛰어난 보온성\n친환경 소재\n직화 가능\n...",
        )
        st.session_state.product_features = [
            f.strip() for f in features_text.strip().split("\n") if f.strip()
        ]

        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.product_target = st.text_input(
                "타겟 고객",
                value=st.session_state.product_target,
                placeholder="예: 20~40대 요리 애호가",
            )
        with col_b:
            st.session_state.product_price = st.text_input(
                "가격대",
                value=st.session_state.product_price,
                placeholder="예: 29,900원",
            )

    with col_right:
        st.subheader("제품 사진 (선택)")
        uploaded = st.file_uploader(
            "사진 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            help="없어도 진행 가능합니다. 플레이스홀더 이미지가 사용됩니다.",
        )
        if uploaded:
            st.session_state.product_photos = [f.read() for f in uploaded]
            img_cols = st.columns(min(len(uploaded), 3))
            for idx, f in enumerate(uploaded[:3]):
                f.seek(0)
                with img_cols[idx]:
                    st.image(f, use_container_width=True)
            if len(uploaded) > 3:
                st.caption(f"+{len(uploaded) - 3}장 더")
        elif st.session_state.product_photos:
            st.caption(f"업로드된 사진: {len(st.session_state.product_photos)}장")

        st.subheader("상품 카테고리")
        try:
            c = _get_core()
            categories = list(c["CATEGORY_PROFILES"].keys())
            cat_labels = {k: v["name"] for k, v in c["CATEGORY_PROFILES"].items()}
            selected_cat = st.selectbox(
                "카테고리 선택",
                ["(선택 안 함)"] + categories,
                format_func=lambda x: cat_labels.get(x, x),
            )
            if selected_cat != "(선택 안 함)":
                st.session_state.filter_category = selected_cat
                profile = c["CATEGORY_PROFILES"][selected_cat]
                st.caption(f"색감: {profile['color_mood']}")
            else:
                st.session_state.filter_category = None
        except Exception:
            pass

    st.divider()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("다음: 템플릿 선택 →", type="primary", use_container_width=True):
            if not st.session_state.product_name.strip():
                st.error("상품명을 입력하세요.")
            elif not st.session_state.product_features:
                st.error("핵심 특징을 최소 1개 이상 입력하세요.")
            else:
                st.session_state.current_phase = 2
                st.rerun()
    with col_btn2:
        if st.button("기본값으로 빠른 시작", use_container_width=True):
            st.session_state.current_phase = 2
            st.rerun()


# ──────────────────────────────────────────────────────────────────
# Phase 2: Template Gallery
# ──────────────────────────────────────────────────────────────────


def _render_lecture_insights(lecture_kb, principle_ids: list[int], context: str = "panel"):
    """Render lecture insights for given D1000 principle IDs."""
    if not principle_ids:
        return
    insights = lecture_kb.get_insights_for_principles(principle_ids)
    if not insights:
        return

    if context == "panel":
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;'
            'text-transform:uppercase;color:var(--pf-text-muted);margin-bottom:0.5rem;">'
            '강의 노하우</div>',
            unsafe_allow_html=True,
        )
        for ins in insights[:5]:
            card_html = (
                f'<div class="pf-insight-card">'
                f'<div style="margin-bottom:4px;">'
                f'<span class="pf-insight-badge">#{ins.principle_id}</span>'
                f'<span style="font-size:0.78rem;color:var(--pf-text-muted);">{ins.source_lecture}</span>'
                f'</div>'
                f'<div style="font-size:0.83rem;color:var(--pf-text);margin-bottom:4px;">{ins.insight_text}</div>'
                f'<div style="font-size:0.75rem;color:var(--pf-text-muted);">'
                f'AI 팁: {ins.reasoning_prompt[:120]}...'
                f'</div></div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
    elif context == "compact":
        for ins in insights[:3]:
            card_html = (
                f'<div class="pf-insight-card" style="padding:0.5rem 0.75rem;margin-bottom:0.35rem;">'
                f'<span class="pf-insight-badge">#{ins.principle_id}</span>'
                f'<span style="font-size:0.78rem;color:var(--pf-text-muted);">{ins.insight_text[:80]}...</span>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)


def render_phase2():
    st.header("🖼 Phase 2: 템플릿 갤러리")
    st.caption("사용할 템플릿을 선택하세요. D1000 원리 기반으로 필터링할 수 있습니다.")

    try:
        c = _get_core()
        searcher = c["searcher"]
        STYLE_PRESETS = c["STYLE_PRESETS"]

        # ── Filter bar ────────────────────────────────────
        with st.expander("필터 옵션", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                section_types = [
                    "(전체)", "hero", "features", "benefits",
                    "testimonials", "specs", "cta", "guarantee",
                    "social_proof", "full_page",
                ]
                chosen_type = st.selectbox("섹션 타입", section_types)
                filter_type = None if chosen_type == "(전체)" else chosen_type
                st.session_state.filter_section_type = filter_type

            with f_col2:
                preset_names = list(STYLE_PRESETS.keys())
                chosen_preset = st.selectbox("스타일 프리셋", ["(선택 안 함)"] + preset_names)
                if chosen_preset != "(선택 안 함)":
                    st.session_state.filter_d1000 = STYLE_PRESETS[chosen_preset]
                else:
                    if not st.session_state.get("filter_d1000"):
                        st.session_state.filter_d1000 = []

            with f_col3:
                st.caption("선택된 D1000 원리")
                st.caption(f"{st.session_state.filter_d1000}")

        # Show lecture insights for filtered principles
        if st.session_state.filter_d1000:
            _render_lecture_insights(c.get("lecture_kb"), st.session_state.filter_d1000, context="compact")

        # ── Template search ───────────────────────────────
        templates = searcher.search(
            section_type=st.session_state.filter_section_type,
            d1000_principles=st.session_state.filter_d1000 or None,
            category=st.session_state.filter_category,
            limit=24,
        )

        selected_ids = set(st.session_state.selected_template_ids)

        if not templates:
            st.info("조건에 맞는 템플릿이 없습니다. 필터를 조정하거나 기본 설정을 사용하세요.")
            _render_placeholder_gallery(selected_ids)
        else:
            st.caption(f"{len(templates)}개 템플릿 검색됨")
            _render_template_grid(templates, selected_ids)

    except Exception as e:
        st.warning(f"템플릿 라이브러리 로드 오류: {e}")
        st.info("기본 템플릿 세트를 사용합니다.")
        selected_ids = set(st.session_state.selected_template_ids)
        _render_placeholder_gallery(selected_ids)

    st.divider()

    # Selected summary
    selected_ids = set(st.session_state.selected_template_ids)
    if selected_ids:
        st.success(f"선택된 템플릿: {len(selected_ids)}개 — {', '.join(list(selected_ids)[:5])}")
    else:
        st.info("템플릿을 선택하거나 아래 버튼으로 기본 세트를 사용하세요.")

    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        if st.button("← 상품 정보", use_container_width=True):
            st.session_state.current_phase = 1
            st.rerun()
    with col_nav2:
        if st.button("기본 템플릿 세트 사용", use_container_width=True):
            # Use available template IDs from the store
            try:
                c = _get_core()
                all_tpls = c["store"].list_templates()
                if all_tpls:
                    st.session_state.selected_template_ids = [t.id for t in all_tpls[:6]]
                else:
                    st.session_state.selected_template_ids = []
            except Exception:
                st.session_state.selected_template_ids = []
            st.rerun()
    with col_nav3:
        if st.button("다음: 디자인 스튜디오 →", type="primary", use_container_width=True):
            st.session_state.current_phase = 3
            st.rerun()


def _render_template_grid(templates, selected_ids: set):
    """Render templates as a clickable card grid."""
    from detail_forge.designer.d1000_principles import D1000_GUIDE

    PRINCIPLE_MAP = {e["id"]: e["name"] for e in D1000_GUIDE}

    cols_per_row = 3
    rows = [templates[i:i + cols_per_row] for i in range(0, len(templates), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, tmpl in zip(cols, row):
            with col:
                is_selected = tmpl.id in selected_ids
                border_color = "#0068c9" if is_selected else "#ddd"
                badge_color = "#0068c9" if is_selected else "#888"

                # Card HTML
                principle_badges = "".join(
                    f'<span style="background:{badge_color};color:white;'
                    f'padding:2px 6px;border-radius:10px;font-size:10px;margin:2px;display:inline-block;">'
                    f'#{pid} {PRINCIPLE_MAP.get(pid, "")[:4]}</span>'
                    for pid in tmpl.d1000_principles[:3]
                )
                category_badge = (
                    f'<span style="background:#f0f0f0;color:#555;padding:2px 6px;'
                    f'border-radius:10px;font-size:10px;">{tmpl.category}</span>'
                )
                section_badge = (
                    f'<span style="background:#e8f4fd;color:#0068c9;padding:2px 6px;'
                    f'border-radius:10px;font-size:10px;">{tmpl.section_type}</span>'
                )
                selected_indicator = "✓ 선택됨" if is_selected else ""
                selected_style = "background:#e8f4fd;" if is_selected else ""

                card_html = f"""
                <div style="border:2px solid {border_color};border-radius:8px;
                     padding:12px;margin-bottom:4px;{selected_style}
                     transition:all 0.2s;">
                  <div style="background:#f5f5f5;height:100px;border-radius:4px;
                       display:flex;align-items:center;justify-content:center;
                       font-size:24px;margin-bottom:8px;">
                    🖼
                  </div>
                  <div style="font-weight:600;font-size:13px;margin-bottom:4px;
                       overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                    {tmpl.name[:28]}
                  </div>
                  <div style="margin-bottom:4px;">
                    {section_badge} {category_badge}
                  </div>
                  <div style="margin-bottom:4px;">{principle_badges}</div>
                  <div style="color:#0068c9;font-size:11px;font-weight:600;">
                    {selected_indicator}
                  </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

                btn_label = "선택 해제" if is_selected else "선택"
                btn_type = "secondary" if is_selected else "primary"
                if st.button(btn_label, key=f"tmpl_btn_{tmpl.id}", use_container_width=True, type=btn_type):
                    ids = list(st.session_state.selected_template_ids)
                    if is_selected:
                        ids = [x for x in ids if x != tmpl.id]
                    else:
                        ids.append(tmpl.id)
                    st.session_state.selected_template_ids = ids
                    st.rerun()


def _render_placeholder_gallery(selected_ids: set):
    """Render placeholder cards when no templates exist yet."""
    st.info("아직 라이브러리에 템플릿이 없습니다. 기본 섹션 구성으로 생성을 진행할 수 있습니다.")
    placeholder_sections = [
        ("hero", "히어로 배너"),
        ("features", "핵심 특징"),
        ("benefits", "사용 혜택"),
        ("specs", "상세 스펙"),
        ("testimonials", "고객 후기"),
        ("cta", "구매 유도"),
    ]
    cols = st.columns(3)
    for i, (stype, sname) in enumerate(placeholder_sections):
        with cols[i % 3]:
            is_selected = stype in selected_ids
            border = "#0068c9" if is_selected else "#ddd"
            card = f"""
            <div style="border:2px solid {border};border-radius:8px;padding:12px;margin-bottom:4px;">
              <div style="font-size:28px;text-align:center;margin-bottom:8px;">
                {'✓' if is_selected else '□'}
              </div>
              <div style="font-weight:600;text-align:center;">{sname}</div>
              <div style="color:#888;font-size:11px;text-align:center;">{stype}</div>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)
            label = "선택 해제" if is_selected else "선택"
            if st.button(label, key=f"ph_btn_{stype}", use_container_width=True):
                ids = list(st.session_state.selected_template_ids)
                if is_selected:
                    ids = [x for x in ids if x != stype]
                else:
                    ids.append(stype)
                st.session_state.selected_template_ids = ids
                st.rerun()


# ──────────────────────────────────────────────────────────────────
# Phase 3: Design Studio
# ──────────────────────────────────────────────────────────────────

def render_phase3():
    st.header("🎨 Phase 3: 디자인 스튜디오")
    st.caption("스타일을 선택하고, 카피를 편집하고, 실시간으로 미리보기를 확인하세요.")

    try:
        c = _get_core()
        theme_gen = c["theme_gen"]
    except Exception as e:
        st.error(f"엔진 로드 실패: {e}")
        return

    left_col, right_col = st.columns([1, 2])

    with left_col:
        # ── Style preset selector ──────────────────────
        st.subheader("스타일 프리셋")

        recipes = theme_gen.list_recipes()

        RECIPE_KR = {
            "premium_minimal": "고급 미니멀",
            "warm_nature": "따뜻한 자연",
            "trendy_hip": "트렌디 힙",
            "dark_luxury": "다크 럭셔리",
            "classic_trust": "클래식 신뢰",
            "organic_flow": "유기적 흐름",
        }
        MOOD_COLORS = {
            "elegant": "#9c27b0",
            "warm": "#ff7043",
            "bold": "#e91e63",
            "cool": "#1565c0",
            "neutral": "#455a64",
        }

        for recipe_name in recipes:
            rname = recipe_name["name"]
            kr_name = RECIPE_KR.get(rname, rname)
            mood = recipe_name.get("mood", "neutral")
            mood_color = MOOD_COLORS.get(mood, "#888")
            desc = recipe_name.get("description", "")
            is_selected = st.session_state.selected_recipe == rname

            swatch = f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
              <div style="width:14px;height:14px;border-radius:50%;
                   background:{mood_color};flex-shrink:0;"></div>
              <div>
                <div style="font-size:13px;font-weight:{'700' if is_selected else '400'};">
                  {kr_name}
                </div>
                <div style="font-size:11px;color:#888;">{desc}</div>
              </div>
            </div>
            """
            st.markdown(swatch, unsafe_allow_html=True)
            btn_type = "primary" if is_selected else "secondary"
            if st.button("적용", key=f"recipe_{rname}", type=btn_type, use_container_width=True):
                st.session_state.selected_recipe = rname
                st.session_state.generation_result = None
                st.rerun()

        # Show insights for selected recipe's principles
        if st.session_state.selected_recipe and st.session_state.selected_recipe != "__custom__":
            try:
                recipe_data = theme_gen.get_recipe(st.session_state.selected_recipe)
                if recipe_data and hasattr(recipe_data, "principle_ids"):
                    _render_lecture_insights(c.get("lecture_kb"), recipe_data.principle_ids, context="panel")
            except (ValueError, AttributeError):
                pass

        # Custom principles expander
        with st.expander("D1000 원리 직접 선택", expanded=False):
            from detail_forge.designer.d1000_principles import D1000_GUIDE
            selected_pids = list(st.session_state.custom_principle_ids)
            for entry in D1000_GUIDE:
                pid = entry["id"]
                checked = st.checkbox(
                    f"#{pid} {entry['name']}",
                    value=pid in selected_pids,
                    key=f"pid_cb_{pid}",
                    help=entry.get("rule", ""),
                )
                if checked and pid not in selected_pids:
                    selected_pids.append(pid)
                elif not checked and pid in selected_pids:
                    selected_pids.remove(pid)
            st.session_state.custom_principle_ids = selected_pids
            if selected_pids:
                _render_lecture_insights(c.get("lecture_kb"), selected_pids, context="panel")
                if st.button("커스텀 테마 적용", type="primary", use_container_width=True):
                    st.session_state.selected_recipe = "__custom__"
                    st.session_state.generation_result = None
                    st.rerun()

        st.divider()

        # ── Copy editor ───────────────────────────────
        st.subheader("카피 편집")
        _render_copy_editor()

        st.divider()

        # ── Generate button ───────────────────────────
        if st.button("페이지 생성", type="primary", use_container_width=True):
            _run_generation(c)

    with right_col:
        st.subheader("미리보기")

        # Device switcher
        device_col1, device_col2 = st.columns(2)
        with device_col1:
            if st.button("데스크탑", use_container_width=True,
                         type="primary" if st.session_state.preview_device == "desktop" else "secondary"):
                st.session_state.preview_device = "desktop"
                st.rerun()
        with device_col2:
            if st.button("모바일", use_container_width=True,
                         type="primary" if st.session_state.preview_device == "mobile" else "secondary"):
                st.session_state.preview_device = "mobile"
                st.rerun()

        result = st.session_state.generation_result
        if result is None:
            st.info("왼쪽에서 스타일을 선택하고 '페이지 생성' 버튼을 누르세요.")
        else:
            _render_live_preview(result)

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← 템플릿 선택", use_container_width=True):
            st.session_state.current_phase = 2
            st.rerun()
    with col_next:
        if st.button("다음: 내보내기 →", type="primary", use_container_width=True):
            if st.session_state.generation_result is None:
                st.warning("먼저 페이지를 생성하세요.")
            else:
                st.session_state.current_phase = 4
                st.rerun()


def _render_copy_editor():
    """Editable copy fields for each section type."""
    copy_sections = st.session_state.copy_sections or []
    section_types = ["hero", "features", "benefits", "specs", "testimonials", "cta"]
    copy_map = {c["section_type"]: c for c in copy_sections} if copy_sections else {}

    updated_copies = []
    for stype in section_types:
        existing = copy_map.get(stype, {})
        with st.expander(f"섹션: {stype}", expanded=(stype == "hero")):
            headline = st.text_input(
                "헤드라인",
                value=existing.get("headline", ""),
                key=f"cp_head_{stype}",
                placeholder=f"{stype} 섹션 헤드라인",
            )
            sub = st.text_input(
                "서브헤드라인",
                value=existing.get("subheadline", ""),
                key=f"cp_sub_{stype}",
            )
            body = st.text_area(
                "본문",
                value=existing.get("body", ""),
                key=f"cp_body_{stype}",
                height=80,
            )
            cta = st.text_input(
                "CTA 텍스트",
                value=existing.get("cta_text", ""),
                key=f"cp_cta_{stype}",
                placeholder="지금 구매하기",
            )
            updated_copies.append({
                "section_type": stype,
                "section_index": section_types.index(stype),
                "headline": headline,
                "subheadline": sub,
                "body": body,
                "cta_text": cta,
            })
    st.session_state.copy_sections = updated_copies


def _run_generation(c: dict):
    """Run the OneClickGenerator pipeline."""
    from detail_forge.copywriter.generator import ProductInfo, SectionCopy
    from detail_forge.designer.theme_generator import ThemeGenerator

    product = ProductInfo(
        name=st.session_state.product_name,
        features=st.session_state.product_features,
        target_audience=st.session_state.product_target,
        price_range=st.session_state.product_price,
    )

    copy_sections = [
        SectionCopy(
            section_index=cs["section_index"],
            section_type=cs["section_type"],
            headline=cs["headline"],
            subheadline=cs["subheadline"],
            body=cs["body"],
            cta_text=cs["cta_text"],
        )
        for cs in (st.session_state.copy_sections or [])
    ]

    # Resolve theme
    recipe = st.session_state.selected_recipe
    theme = None
    if recipe == "__custom__" and st.session_state.custom_principle_ids:
        theme_gen = ThemeGenerator()
        theme = theme_gen.generate_custom(principle_ids=st.session_state.custom_principle_ids)
    elif recipe != "__custom__":
        try:
            theme_gen = ThemeGenerator()
            theme = theme_gen.generate(recipe)
        except ValueError:
            theme = None

    # Template IDs
    template_ids = st.session_state.selected_template_ids or []

    generator = c["generator"]

    with st.spinner("페이지 생성 중..."):
        try:
            result = generator.generate(
                product=product,
                copy_sections=copy_sections,
                template_ids=template_ids,
                theme=theme,
                include_naver=True,
            )
            st.session_state.generation_result = result
            if result.warnings:
                for w in result.warnings:
                    st.warning(w)
            st.success(f"생성 완료 ({result.generation_time_ms}ms)")
        except Exception as e:
            st.error(f"생성 오류: {e}")
            # Fallback: generate a simple placeholder HTML
            _generate_placeholder_html(product, theme)


def _generate_placeholder_html(product, theme):
    """Generate a simple placeholder page when no templates are available."""
    from detail_forge.designer.theme_generator import ThemeGenerator
    from detail_forge.output.naver_renderer import NaverRenderer
    from detail_forge.output.quality_gate import QualityGate
    from detail_forge.output.web_renderer import WebRenderer
    from detail_forge.synthesis.one_click_generator import GenerationResult
    from detail_forge.synthesis.page_assembler import AssembledPage

    if theme is None:
        theme_gen = ThemeGenerator()
        theme = theme_gen.generate("classic_trust")

    features_html = "".join(
        f"<li>{f}</li>" for f in (getattr(product, "features", []) or [])
    )
    simple_html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{product.name}</title>
      <style>
        body {{ font-family: 'Noto Sans KR', sans-serif; margin: 0; padding: 20px; }}
        .hero {{ background: #f5f5f5; padding: 60px 20px; text-align: center; }}
        .hero h1 {{ font-size: 2em; margin-bottom: 16px; }}
        .features {{ padding: 40px 20px; max-width: 800px; margin: 0 auto; }}
        .features ul {{ font-size: 1.1em; line-height: 2; }}
        .cta {{ background: #0068c9; color: white; padding: 40px; text-align: center; }}
        .cta button {{ background: white; color: #0068c9; border: none;
                       padding: 16px 32px; font-size: 1.1em; border-radius: 8px;
                       cursor: pointer; font-weight: bold; }}
      </style>
    </head>
    <body>
      <div class="hero">
        <h1>{product.name}</h1>
        <p>{getattr(product, 'target_audience', '')}</p>
        <p><strong>{getattr(product, 'price_range', '')}</strong></p>
      </div>
      <div class="features">
        <h2>핵심 특징</h2>
        <ul>{features_html}</ul>
      </div>
      <div class="cta">
        <h2>지금 바로 구매하세요</h2>
        <button>구매하기</button>
      </div>
    </body>
    </html>
    """

    web_renderer = WebRenderer()
    naver_renderer = NaverRenderer()
    quality_gate = QualityGate()

    web_html = web_renderer.render(html=simple_html, product_name=product.name)
    naver_html = naver_renderer.render(html=simple_html)
    quality = quality_gate.evaluate(html=web_html.html, platform="web")
    assembled = AssembledPage(html=simple_html, section_count=3, token_count=0, warnings=[])

    result = GenerationResult(
        assembled_page=assembled,
        theme=theme,
        web_html=web_html,
        naver_html=naver_html,
        quality=quality,
        generation_time_ms=0,
        warnings=["템플릿 없음: 플레이스홀더 페이지로 생성됨"],
    )
    st.session_state.generation_result = result
    st.info("템플릿이 없어 기본 레이아웃으로 생성되었습니다.")


def _render_live_preview(result):
    """Render the generated HTML in an iframe-like component."""
    html_content = result.web_html.html
    is_mobile = st.session_state.preview_device == "mobile"
    width = 390 if is_mobile else 900
    height = 700

    # Device frame wrapper
    frame_style = (
        f"border:1px solid #ddd;border-radius:12px;"
        f"box-shadow:0 4px 20px rgba(0,0,0,0.1);"
        f"overflow:hidden;max-width:{width}px;margin:0 auto;"
    )
    if is_mobile:
        # Add mobile notch styling
        st.markdown(
            f'<div style="{frame_style}">'
            '<div style="background:#000;height:24px;border-radius:12px 12px 0 0;'
            'display:flex;justify-content:center;align-items:center;">'
            '<div style="width:60px;height:6px;background:#333;border-radius:3px;"></div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

    st.components.v1.html(html_content, height=height, scrolling=True)

    # Quality summary below preview
    q = result.quality
    q_col1, q_col2, q_col3 = st.columns(3)
    with q_col1:
        score_color = "#4caf50" if q.total_score >= 7 else "#ff9800"
        st.markdown(
            f'<div style="text-align:center;padding:8px;background:{score_color}20;'
            f'border-radius:8px;"><div style="font-size:22px;font-weight:700;color:{score_color};">'
            f'{q.total_score:.1f}</div><div style="font-size:11px;color:#666;">종합 점수</div></div>',
            unsafe_allow_html=True,
        )
    with q_col2:
        status = "합격" if q.passed else "미흡"
        status_color = "#4caf50" if q.passed else "#f44336"
        st.markdown(
            f'<div style="text-align:center;padding:8px;background:{status_color}20;'
            f'border-radius:8px;"><div style="font-size:22px;font-weight:700;color:{status_color};">'
            f'{status}</div><div style="font-size:11px;color:#666;">품질 게이트</div></div>',
            unsafe_allow_html=True,
        )
    with q_col3:
        st.markdown(
            f'<div style="text-align:center;padding:8px;background:#e3f2fd;border-radius:8px;">'
            f'<div style="font-size:22px;font-weight:700;color:#1565c0;">'
            f'{result.generation_time_ms}ms</div>'
            f'<div style="font-size:11px;color:#666;">생성 시간</div></div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────
# Phase 4: Export Dashboard
# ──────────────────────────────────────────────────────────────────

def render_phase4():
    st.header("📤 Phase 4: 내보내기 대시보드")
    st.caption("3개 포맷의 미리보기와 품질 점수를 확인하고 다운로드하세요.")

    result = st.session_state.generation_result
    if result is None:
        st.warning("Phase 3에서 먼저 페이지를 생성하세요.")
        if st.button("← 디자인 스튜디오로 돌아가기"):
            st.session_state.current_phase = 3
            st.rerun()
        return

    # ── Quality gate detail ────────────────────────────
    st.subheader("품질 점수")
    q = result.quality
    dim_cols = st.columns(len(q.dimensions))
    for col, dim in zip(dim_cols, q.dimensions):
        with col:
            color = "#4caf50" if dim.score >= 7 else ("#ff9800" if dim.score >= 5 else "#f44336")
            st.markdown(
                f'<div style="text-align:center;padding:12px;background:{color}20;'
                f'border-radius:8px;border:1px solid {color}40;">'
                f'<div style="font-size:24px;font-weight:700;color:{color};">{dim.score:.1f}</div>'
                f'<div style="font-size:12px;color:#666;margin-top:4px;">{dim.name}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if dim.issues:
                with st.expander("이슈 보기"):
                    for issue in dim.issues:
                        st.caption(f"- {issue}")

    st.divider()

    # ── 3-format preview tabs ──────────────────────────
    st.subheader("포맷별 미리보기")
    tab_web, tab_naver, tab_info = st.tabs(["웹 (반응형)", "네이버 스마트스토어", "메타 정보"])

    with tab_web:
        st.caption("반응형 독립 HTML — 브라우저에서 직접 사용 가능")
        web_html = result.web_html.html
        st.components.v1.html(web_html, height=600, scrolling=True)
        st.download_button(
            "웹 HTML 다운로드",
            data=web_html.encode("utf-8"),
            file_name=f"{st.session_state.product_name[:20]}_web.html",
            mime="text/html",
            use_container_width=True,
        )

    with tab_naver:
        st.caption("네이버 스마트스토어 안전 HTML — 인라인 CSS, 안전 폰트")
        if result.naver_html:
            naver_html = result.naver_html.html
            st.components.v1.html(naver_html, height=600, scrolling=True)
            st.download_button(
                "네이버 HTML 다운로드",
                data=naver_html.encode("utf-8"),
                file_name=f"{st.session_state.product_name[:20]}_naver.html",
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.info("네이버 형식이 포함되지 않았습니다.")

    with tab_info:
        st.caption("생성 메타데이터")
        theme = result.theme
        info_data = {
            "상품명": st.session_state.product_name,
            "테마": f"{theme.name} ({theme.mood})",
            "D1000 원리": str(theme.principle_ids),
            "섹션 수": result.assembled_page.section_count,
            "생성 시간": f"{result.generation_time_ms}ms",
            "품질 점수": f"{result.quality.total_score:.1f} / 10",
            "품질 통과": "합격" if result.quality.passed else "미흡",
        }
        for k, v in info_data.items():
            col_k, col_v = st.columns([1, 2])
            with col_k:
                st.markdown(f"**{k}**")
            with col_v:
                st.markdown(str(v))

    st.divider()

    # ── ZIP export ─────────────────────────────────────
    st.subheader("전체 패키지 다운로드")

    try:
        c = _get_core()
        export_manager = c["export_manager"]

        if st.button("ZIP 패키지 생성", type="primary", use_container_width=True):
            with st.spinner("패키지 생성 중..."):
                metadata = {
                    "theme": result.theme.name,
                    "quality_score": result.quality.total_score,
                    "quality_passed": result.quality.passed,
                }
                package = export_manager.export(
                    product_name=st.session_state.product_name,
                    naver_html=result.naver_html.html if result.naver_html else None,
                    web_html=result.web_html.html,
                    metadata=metadata,
                )
                st.download_button(
                    label=f"ZIP 다운로드 ({package.total_size_bytes // 1024}KB, {package.file_count}개 파일)",
                    data=package.zip_bytes,
                    file_name=f"{st.session_state.product_name[:20]}_export.zip",
                    mime="application/zip",
                    use_container_width=True,
                )
                st.success(f"패키지 생성 완료: {package.file_count}개 파일, {package.total_size_bytes // 1024}KB")

                # Show manifest
                with st.expander("파일 목록"):
                    for path, desc in package.manifest.items():
                        st.caption(f"📄 {path} — {desc}")
    except Exception as e:
        st.error(f"내보내기 오류: {e}")

    st.divider()
    if st.button("← 디자인 스튜디오", use_container_width=True):
        st.session_state.current_phase = 3
        st.rerun()


# ──────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────

def main():
    _render_sidebar()
    _render_progress()

    phase = st.session_state.current_phase
    if phase == 1:
        render_phase1()
    elif phase == 2:
        render_phase2()
    elif phase == 3:
        render_phase3()
    elif phase == 4:
        render_phase4()


if __name__ == "__main__" or True:
    main()
