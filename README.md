# Detail Forge

AI-powered e-commerce product detail page generator using Python, Streamlit, and FastAPI.

## Overview

Detail Forge automatically generates professional e-commerce product detail pages by combining multiple AI providers (Claude, OpenAI, Gemini) with a comprehensive D1000 design system (50 design principles mapped to CSS tokens).

## Features

- **D1000 Design System**: 50 design principles, 6 theme recipes (Classic Trust, Modern Bold, Luxury Elite, etc.)
- **Multi-Provider AI**: ProviderRouter with Claude → OpenAI → Gemini fallback
- **One-Click Generation**: Single endpoint transforms product data into complete pages
- **Multi-Format Export**: Web (responsive HTML), Naver (inline CSS), Coupang (860px Playwright)
- **Quality Gates**: 5-dimension scoring (design, UX, performance, SEO, brand)
- **Streamlit UI**: 4-phase workflow (Product Info → Template Gallery → Design Studio → Export)
- **FastAPI Backend**: REST API with SQLAlchemy DB backend

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run Streamlit UI
streamlit run ui/app.py

# Run FastAPI server
uvicorn src.detail_forge.api.app:app --port 8000 --reload
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/generate | Generate product page |
| GET | /api/v1/templates | List templates |
| GET | /api/v1/themes | List theme recipes |

## Architecture

```
Streamlit UI (port 8501) ─── 4-Phase Workflow
        │
FastAPI Backend (port 8000) ─── REST API + SQLAlchemy
        │
Core Engine:
  designer/      D1000 principles, design tokens, themes
  copywriter/    AI-powered section copy generation
  templates/     Template store, search, importer
  synthesis/     SectionCompositor, CoherenceEngine, PageAssembler
  output/        WebRenderer, NaverRenderer, CoupangRenderer, QualityGate
  providers/     ProviderRouter (Claude/OpenAI/Gemini fallback)
  db/            SQLAlchemy models (Template, Generation, User)
```

## Development

```bash
# Run tests (723 tests, 78% coverage)
pytest

# Run with coverage
pytest --cov=src/detail_forge --cov-report=html

# Lint
ruff check src/ tests/
```

## Configuration

```bash
export ANTHROPIC_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."
```

## Stack

- Python 3.12+, Streamlit, FastAPI, SQLAlchemy
- Anthropic Claude, OpenAI, Google Gemini
- Playwright, Pillow, BeautifulSoup4, Pydantic
- pytest, ruff

## License

Apache-2.0
