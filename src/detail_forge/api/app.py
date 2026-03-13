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


class GenerationResponse(BaseModel):
    web_html: str
    naver_html: str | None = None
    quality_score: float
    generation_time_ms: int
    warnings: list[str] = []


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
        )

        return GenerationResponse(
            web_html=result.web_html.html,
            naver_html=result.naver_html.html if result.naver_html else None,
            quality_score=result.quality.total_score,
            generation_time_ms=result.generation_time_ms,
            warnings=result.warnings,
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
