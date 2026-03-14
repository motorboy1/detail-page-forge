"""Detail Forge dark theme injection for Streamlit.

Usage:
    from ui.theme import inject_theme
    inject_theme()
"""
from __future__ import annotations

import streamlit as st


_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Design tokens ───────────────────────────────────────────── */
:root {
  --pf-bg:          oklch(0.13 0.015 260);
  --pf-surface:     oklch(0.17 0.018 260);
  --pf-surface-2:   oklch(0.20 0.018 260);
  --pf-border:      oklch(0.28 0.02  260);
  --pf-text:        oklch(0.93 0.005 260);
  --pf-text-muted:  oklch(0.65 0.02  260);
  --pf-primary:     oklch(0.72 0.17  195);
  --pf-secondary:   oklch(0.65 0.2   160);
  --pf-tertiary:    oklch(0.7  0.15  280);
  --pf-accent-warm: oklch(0.75 0.12   80);
  --pf-danger:      oklch(0.65 0.22   25);
  --pf-warning:     oklch(0.78 0.15   80);
  --pf-success:     oklch(0.65 0.2   160);

  --pf-radius:  0.75rem;
  --pf-radius-sm: 0.5rem;
}

/* ── Base app shell ──────────────────────────────────────────── */
.stApp {
  background-color: var(--pf-bg) !important;
  background-image:
    linear-gradient(oklch(0.72 0.17 195 / 0.03) 1px, transparent 1px),
    linear-gradient(90deg, oklch(0.72 0.17 195 / 0.03) 1px, transparent 1px) !important;
  background-size: 40px 40px !important;
  font-family: "Inter", system-ui, sans-serif !important;
  color: var(--pf-text) !important;
}

/* ── Main content area ───────────────────────────────────────── */
[data-testid="stAppViewContainer"] > .main,
section.main > div.block-container {
  background: transparent !important;
  padding-top: 1.5rem !important;
}

/* ── Header ──────────────────────────────────────────────────── */
[data-testid="stHeader"] {
  background: oklch(0.13 0.015 260 / 0.8) !important;
  backdrop-filter: blur(12px) !important;
  border-bottom: 1px solid var(--pf-border) !important;
}
[data-testid="stDecoration"] {
  background: linear-gradient(90deg, var(--pf-primary), var(--pf-secondary)) !important;
  height: 2px !important;
}

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"],
.stSidebar {
  background-color: var(--pf-surface) !important;
  border-right: 1px solid var(--pf-border) !important;
}
[data-testid="stSidebar"] * {
  color: var(--pf-text) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
  color: var(--pf-text-muted) !important;
}
[data-testid="stSidebarNav"] {
  background: transparent !important;
}

/* ── Typography ──────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: "Inter", system-ui, sans-serif !important;
  color: var(--pf-text) !important;
  letter-spacing: -0.02em !important;
}

/* Gradient headers */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {
  background: linear-gradient(90deg, var(--pf-primary), var(--pf-secondary)) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

.stHeader,
[data-testid="stHeading"] {
  color: var(--pf-text) !important;
}

p, span, li, label,
.stMarkdown, .stCaption, small {
  color: var(--pf-text) !important;
  font-family: "Inter", system-ui, sans-serif !important;
}
.stCaption, small, .element-container small {
  color: var(--pf-text-muted) !important;
}

/* ── Divider ─────────────────────────────────────────────────── */
hr, [data-testid="stDivider"] hr {
  border-color: var(--pf-border) !important;
  opacity: 1 !important;
}

/* ── Cards / Containers / Expanders ─────────────────────────── */
.stExpander,
[data-testid="stExpander"] {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius) !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  background: var(--pf-surface) !important;
  color: var(--pf-text) !important;
  padding: 0.75rem 1rem !important;
  border-bottom: 1px solid var(--pf-border) !important;
  display: flex !important;
  align-items: center !important;
  gap: 0.5rem !important;
  min-height: 2.5rem !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
[data-testid="stExpander"] summary span {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  flex: 1 !important;
  min-width: 0 !important;
}
[data-testid="stExpander"] summary:hover {
  background: oklch(0.72 0.17 195 / 0.08) !important;
}
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
  background: var(--pf-surface) !important;
  padding: 1rem !important;
}
[data-testid="stExpander"] svg {
  fill: var(--pf-text-muted) !important;
}

/* ── Metric cards ────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius) !important;
  padding: 1rem !important;
}
[data-testid="stMetricValue"] {
  color: var(--pf-primary) !important;
  font-family: "JetBrains Mono", monospace !important;
}
[data-testid="stMetricLabel"] {
  color: var(--pf-text-muted) !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
  background: var(--pf-surface-2) !important;
  color: var(--pf-text) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius-sm) !important;
  font-family: "Inter", system-ui, sans-serif !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}
.stButton > button:hover {
  background: oklch(0.72 0.17 195 / 0.12) !important;
  border-color: var(--pf-primary) !important;
  color: var(--pf-primary) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, var(--pf-primary), oklch(0.65 0.2 160)) !important;
  color: oklch(0.13 0.015 260) !important;
  border: none !important;
  font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
  opacity: 0.88 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px oklch(0.72 0.17 195 / 0.35) !important;
  color: oklch(0.13 0.015 260) !important;
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  color: var(--pf-text) !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
  border-color: var(--pf-primary) !important;
  color: var(--pf-primary) !important;
}

/* ── Download buttons ────────────────────────────────────────── */
.stDownloadButton > button {
  background: linear-gradient(135deg, var(--pf-secondary), var(--pf-primary)) !important;
  color: oklch(0.13 0.015 260) !important;
  border: none !important;
  border-radius: var(--pf-radius-sm) !important;
  font-weight: 600 !important;
}
.stDownloadButton > button:hover {
  opacity: 0.85 !important;
  transform: translateY(-1px) !important;
}

/* ── Text inputs ─────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
  background: var(--pf-surface-2) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius-sm) !important;
  color: var(--pf-text) !important;
  font-family: "Inter", system-ui, sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--pf-primary) !important;
  box-shadow: 0 0 0 2px oklch(0.72 0.17 195 / 0.2) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
  color: var(--pf-text-muted) !important;
}

/* ── Labels / form helpers ───────────────────────────────────── */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stNumberInput label,
.stSlider label,
.stFileUploader label,
.stCheckbox label,
.stRadio label {
  color: var(--pf-text-muted) !important;
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* ── Selectboxes ─────────────────────────────────────────────── */
.stSelectbox > div > div,
[data-testid="stSelectbox"] > div > div {
  background: var(--pf-surface-2) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius-sm) !important;
  color: var(--pf-text) !important;
}
[data-testid="stSelectbox"] > div > div:focus-within {
  border-color: var(--pf-primary) !important;
  box-shadow: 0 0 0 2px oklch(0.72 0.17 195 / 0.2) !important;
}
[data-baseweb="select"] > div {
  background: var(--pf-surface-2) !important;
  border-color: var(--pf-border) !important;
  color: var(--pf-text) !important;
}
[data-baseweb="popover"] {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius-sm) !important;
}
[data-baseweb="menu"] li {
  background: var(--pf-surface) !important;
  color: var(--pf-text) !important;
}
[data-baseweb="menu"] li:hover {
  background: oklch(0.72 0.17 195 / 0.12) !important;
}

/* ── Checkboxes ──────────────────────────────────────────────── */
.stCheckbox input[type="checkbox"] + label::before {
  background: var(--pf-surface-2) !important;
  border-color: var(--pf-border) !important;
}
.stCheckbox input[type="checkbox"]:checked + label::before {
  background: var(--pf-primary) !important;
  border-color: var(--pf-primary) !important;
}

/* ── File uploader ───────────────────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--pf-surface) !important;
  border: 1px dashed var(--pf-border) !important;
  border-radius: var(--pf-radius) !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--pf-primary) !important;
  background: oklch(0.72 0.17 195 / 0.04) !important;
}

/* ── Sliders ─────────────────────────────────────────────────── */
[data-testid="stSlider"] > div > div {
  background: var(--pf-border) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div:nth-child(3) > div {
  background: var(--pf-primary) !important;
}

/* ── Progress bars ───────────────────────────────────────────── */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--pf-primary), var(--pf-secondary)) !important;
  border-radius: 99px !important;
}
.stProgress > div > div > div {
  background: var(--pf-border) !important;
  border-radius: 99px !important;
}

/* ── Alert / Status boxes ────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--pf-radius-sm) !important;
  border: 1px solid !important;
  font-family: "Inter", system-ui, sans-serif !important;
}
.stSuccess,
[data-testid="stAlert"][data-baseweb="notification"][kind="positive"] {
  background: oklch(0.65 0.2 160 / 0.12) !important;
  border-color: oklch(0.65 0.2 160 / 0.4) !important;
  color: var(--pf-text) !important;
}
.stInfo,
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
  background: oklch(0.72 0.17 195 / 0.10) !important;
  border-color: oklch(0.72 0.17 195 / 0.35) !important;
  color: var(--pf-text) !important;
}
.stWarning,
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
  background: oklch(0.75 0.12 80 / 0.12) !important;
  border-color: oklch(0.75 0.12 80 / 0.4) !important;
  color: var(--pf-text) !important;
}
.stError,
[data-testid="stAlert"][data-baseweb="notification"][kind="negative"] {
  background: oklch(0.65 0.22 25 / 0.12) !important;
  border-color: oklch(0.65 0.22 25 / 0.4) !important;
  color: var(--pf-text) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--pf-surface) !important;
  border-bottom: 1px solid var(--pf-border) !important;
  gap: 0 !important;
  border-radius: var(--pf-radius) var(--pf-radius) 0 0 !important;
  overflow: hidden !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--pf-text-muted) !important;
  border-bottom: 2px solid transparent !important;
  font-family: "Inter", system-ui, sans-serif !important;
  font-weight: 500 !important;
  padding: 0.75rem 1.25rem !important;
  transition: all 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--pf-text) !important;
  background: oklch(0.72 0.17 195 / 0.06) !important;
}
.stTabs [aria-selected="true"] {
  color: var(--pf-primary) !important;
  border-bottom-color: var(--pf-primary) !important;
  background: oklch(0.72 0.17 195 / 0.08) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--pf-radius) var(--pf-radius) !important;
  padding: 1rem !important;
}

/* ── Spinner / Loading ───────────────────────────────────────── */
[data-testid="stSpinner"] > div {
  border-top-color: var(--pf-primary) !important;
}

/* ── Columns ─────────────────────────────────────────────────── */
[data-testid="column"] {
  background: transparent !important;
}

/* ── Code blocks ─────────────────────────────────────────────── */
code, pre {
  background: var(--pf-surface) !important;
  border: 1px solid var(--pf-border) !important;
  border-radius: var(--pf-radius-sm) !important;
  color: var(--pf-primary) !important;
  font-family: "JetBrains Mono", monospace !important;
}

/* ── Scrollbars ──────────────────────────────────────────────── */
* {
  scrollbar-width: thin !important;
  scrollbar-color: var(--pf-border) transparent !important;
}
*::-webkit-scrollbar {
  width: 6px !important;
  height: 6px !important;
}
*::-webkit-scrollbar-track {
  background: transparent !important;
}
*::-webkit-scrollbar-thumb {
  background-color: var(--pf-border) !important;
  border-radius: 99px !important;
}
*::-webkit-scrollbar-thumb:hover {
  background-color: var(--pf-text-muted) !important;
}

/* ── Utility: gradient text ──────────────────────────────────── */
.pf-gradient-text {
  background: linear-gradient(90deg, var(--pf-primary), var(--pf-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  display: inline-block;
}

/* ── Utility: pf-card ────────────────────────────────────────── */
.pf-card {
  background: var(--pf-surface);
  border: 1px solid var(--pf-border);
  border-radius: var(--pf-radius);
  padding: 1rem;
  transition: border-color 0.2s, background 0.2s;
}
.pf-card:hover {
  border-color: oklch(0.72 0.17 195 / 0.5);
  background: oklch(0.72 0.17 195 / 0.04);
}
.pf-card.pf-card--selected {
  border-color: var(--pf-primary);
  background: oklch(0.72 0.17 195 / 0.08);
}

/* ── Step indicator ──────────────────────────────────────────── */
.pf-step-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0.5rem 0 1rem;
}
.pf-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
}
.pf-step:not(:last-child)::after {
  content: "";
  position: absolute;
  top: 14px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--pf-border);
  z-index: 0;
}
.pf-step.pf-step--done:not(:last-child)::after {
  background: var(--pf-secondary);
}
.pf-step.pf-step--active:not(:last-child)::after {
  background: linear-gradient(90deg, var(--pf-primary) 50%, var(--pf-border) 50%);
}
.pf-step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--pf-border);
  background: var(--pf-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  position: relative;
  z-index: 1;
  color: var(--pf-text-muted);
  transition: all 0.2s;
}
.pf-step.pf-step--done .pf-step-dot {
  background: var(--pf-secondary);
  border-color: var(--pf-secondary);
  color: oklch(0.13 0.015 260);
}
.pf-step.pf-step--active .pf-step-dot {
  background: var(--pf-primary);
  border-color: var(--pf-primary);
  color: oklch(0.13 0.015 260);
  box-shadow: 0 0 0 4px oklch(0.72 0.17 195 / 0.2);
}
.pf-step-label {
  font-size: 10px;
  font-weight: 500;
  color: var(--pf-text-muted);
  text-align: center;
  white-space: nowrap;
}
.pf-step.pf-step--active .pf-step-label {
  color: var(--pf-primary);
}
.pf-step.pf-step--done .pf-step-label {
  color: var(--pf-secondary);
}

/* ── Sidebar nav items ───────────────────────────────────────── */
.pf-nav-logo {
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(90deg, var(--pf-primary), var(--pf-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.25rem;
  display: block;
}
.pf-nav-subtitle {
  font-size: 0.7rem;
  color: var(--pf-text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ── Insight cards ───────────────────────────────────────────── */
.pf-insight-card {
  background: oklch(0.72 0.17 195 / 0.06);
  border: 1px solid oklch(0.72 0.17 195 / 0.2);
  border-left: 3px solid var(--pf-primary);
  border-radius: 0 var(--pf-radius-sm) var(--pf-radius-sm) 0;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.82rem;
}
.pf-insight-badge {
  display: inline-block;
  background: var(--pf-primary);
  color: oklch(0.13 0.015 260);
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 99px;
  margin-right: 6px;
  font-family: "JetBrains Mono", monospace;
}

/* ── Status badge ────────────────────────────────────────────── */
.pf-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
  letter-spacing: 0.04em;
}
.pf-badge--primary {
  background: oklch(0.72 0.17 195 / 0.15);
  color: var(--pf-primary);
  border: 1px solid oklch(0.72 0.17 195 / 0.3);
}
.pf-badge--success {
  background: oklch(0.65 0.2 160 / 0.15);
  color: var(--pf-secondary);
  border: 1px solid oklch(0.65 0.2 160 / 0.3);
}
.pf-badge--muted {
  background: oklch(0.65 0.02 260 / 0.1);
  color: var(--pf-text-muted);
  border: 1px solid var(--pf-border);
}
</style>
"""


def inject_theme() -> None:
    """Inject the Detail Forge dark theme into the current Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
