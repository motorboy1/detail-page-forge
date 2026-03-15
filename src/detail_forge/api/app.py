"""FastAPI application for detail_forge."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from detail_forge.api.error_handlers import (
    detail_forge_exception_handler,
    generic_exception_handler,
    pydantic_validation_exception_handler,
)
from detail_forge.exceptions import (
    DetailForgeError,
)

app = FastAPI(
    title="Detail Forge API",
    description="E-commerce product detail page generation API",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(DetailForgeError, detail_forge_exception_handler)
app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Pydantic models for requests/responses
class ProductRequest(BaseModel):
    product_name: str
    product_features: list[str]
    template_ids: list[str] = []
    theme_name: str = "classic_trust"
    include_naver: bool = True
    # Technique Engine parameters
    use_technique_engine: bool = False
    category: str | None = None
    style_keywords: list[str] = []
    workflow_id: str | None = None


class TechniqueResultSummary(BaseModel):
    workflow_name: str
    workflow_name_en: str
    total_atoms: int
    section_count: int
    mood_profile: list[str]
    sections: list[dict]
    conflicts_resolved: list[str] = []


class TemplateMatchSummary(BaseModel):
    template_ids: list[str]
    matched_count: int
    unmatched_sections: list[int]
    matches: list[dict]


class GenerationResponse(BaseModel):
    web_html: str
    naver_html: str | None = None
    quality_score: float
    generation_time_ms: int
    warnings: list[str] = []
    technique_result: TechniqueResultSummary | None = None
    template_match: TemplateMatchSummary | None = None


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.3.0")


@app.post("/api/v1/generate", response_model=GenerationResponse)
async def generate_page(request: ProductRequest) -> GenerationResponse:
    """Generate a product detail page."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    try:
        from detail_forge.copywriter.generator import ProductInfo, SectionCopy
        from detail_forge.synthesis.one_click_generator import OneClickGenerator
        from detail_forge.templates.store import TemplateStore

        store = TemplateStore()
        gen = OneClickGenerator(template_store=store)

        product = ProductInfo(
            name=request.product_name,
            features=request.product_features,
        )

        num_sections = len(request.template_ids) or 1
        copy_sections = [
            SectionCopy(
                section_index=i,
                section_type="hero" if i == 0 else "features",
            )
            for i in range(num_sections)
        ]

        result = gen.generate(
            product=product,
            copy_sections=copy_sections,
            template_ids=request.template_ids,
            include_naver=request.include_naver,
            use_technique_engine=request.use_technique_engine,
            category=request.category,
            style_keywords=request.style_keywords or None,
            workflow_id=request.workflow_id,
        )

        # Build technique result summary if available
        technique_summary = None
        if result.technique_result:
            tr = result.technique_result
            technique_summary = TechniqueResultSummary(
                workflow_name=tr.workflow.name,
                workflow_name_en=tr.workflow.name_en,
                total_atoms=len(tr.all_atoms),
                section_count=len(tr.section_techniques),
                mood_profile=tr.mood_profile,
                sections=[
                    {
                        "order": s.section_order,
                        "type": s.section_type,
                        "compound": s.compound.name,
                        "atoms": [a.name for a in s.atoms],
                    }
                    for s in tr.section_techniques
                ],
                conflicts_resolved=tr.conflicts_resolved,
            )

        # Build template match summary if available
        match_summary = None
        if result.template_match:
            tm = result.template_match
            match_summary = TemplateMatchSummary(
                template_ids=tm.template_ids,
                matched_count=len(tm.matched),
                unmatched_sections=tm.unmatched_sections,
                matches=[
                    {
                        "template_id": m.template.id,
                        "section_order": m.section_order,
                        "section_type": m.section_type,
                        "score": round(m.score, 2),
                        "reasons": m.match_reasons,
                    }
                    for m in tm.matched
                ],
            )

        return GenerationResponse(
            web_html=result.web_html.html,
            naver_html=result.naver_html.html if result.naver_html else None,
            quality_score=result.quality.total_score,
            generation_time_ms=result.generation_time_ms,
            warnings=result.warnings,
            technique_result=technique_summary,
            template_match=match_summary,
        )
    except DetailForgeError:
        raise
    except Exception as e:
        raise e


@app.get("/api/v1/themes")
async def list_themes() -> dict:
    """List available theme recipes."""
    from detail_forge.designer.theme_generator import ThemeGenerator

    gen = ThemeGenerator()
    return {"themes": gen.list_recipes()}


@app.get("/api/v1/workflows")
async def list_workflows() -> dict:
    """List available technique engine workflows."""
    from detail_forge.technique_engine.engine import TechniqueEngine

    engine = TechniqueEngine()
    workflows = engine.list_workflows()
    return {
        "workflows": [
            {
                "id": wf.id,
                "name": wf.name,
                "name_en": wf.name_en,
                "description": wf.description,
                "target_categories": wf.target_categories,
                "section_count": len(wf.page_structure),
                "scroll_depth": wf.estimated_scroll_depth,
            }
            for wf in workflows
        ]
    }


@app.get("/api/v1/templates")
async def list_templates() -> dict:
    """List available templates."""
    from detail_forge.templates.store import TemplateStore

    store = TemplateStore()
    templates = store.list_templates()
    return {
        "templates": [
            {"id": t.id, "section_type": t.section_type, "category": t.category}
            for t in templates
        ]
    }
