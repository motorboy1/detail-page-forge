# Changelog

All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] - 2026-03-14

### Phase 3: Polish

#### M-3.3: FastAPI + SQLAlchemy DB
- FastAPI REST API: /health, /api/v1/generate, /api/v1/themes, /api/v1/templates
- SQLAlchemy ORM models: Template, Generation, User
- Pydantic request/response validation
- CORS middleware

#### M-3.2: Asset Integration + Provider Router
- ProviderRouter: Claude → OpenAI → Gemini fallback routing
- ReferenceLibrary: Pinterest image index with D1000 mapping
- LectureKnowledge: 85 lecture transcript insights

#### M-3.1: UI/UX Rewrite
- Streamlit 4-phase workflow (Product Info → Template Gallery → Design Studio → Export)
- Template gallery with D1000 filters, card selection
- Design studio: 6 style presets, live preview
- Export dashboard: 3-format preview, quality scores, ZIP download

## [0.2.1] - 2026-03-14

### Bug Fixes
- NaverRenderer: var(--df-*) → actual value resolution (was empty string)
- CoherenceEngine: raw color/spacing inconsistency detection
- PageAssembler: added noscript fallback for JS-disabled users
- OneClickGenerator: added warnings field for skipped templates

## [0.2.0] - 2026-03-14

### Phase 2: Engine

#### M-2.1: Synthesis Engine Core
- SectionCompositor: slot filling with copy + template
- CoherenceEngine: cross-section consistency validation
- PageAssembler: full HTML document assembly

#### M-2.2: Output Pipeline
- WebRenderer: responsive HTML
- NaverRenderer: inline CSS, safe fonts
- CoupangRenderer: 860px fixed-width (Playwright)
- QualityGate: 5-dimension scoring
- ExportManager: ZIP packaging

#### M-2.3: OneClick + Theme Generator
- OneClickGenerator: full pipeline orchestration
- ThemeGenerator: 6 theme recipes

## [0.1.0] - 2026-03-14

### Phase 1: Foundation

#### M-1.1: Design Token System
- D1000 principles (50 design principles → CSS tokens)
- DesignTokenSet with category/style presets

#### M-1.2: Test Infrastructure
- pytest with conftest fixtures
- 100+ initial tests

#### M-1.3: Asset Pipeline
- PngConverter: HTML quality conversion
- SlotTagger: section content area identification
- Batch conversion CLI script
