"""Batch conversion script for Figma template PNGs.

Processes all PNGs in data/d1000_knowledge/figma_templates/,
converts each to HTML/CSS using PngConverter + Claude Vision,
and writes results to data/templates/.

Usage:
    uv run python scripts/convert_figma_templates.py [--input DIR] [--output DIR]

For testing with a mock provider, call batch_convert() directly.

T-1.3.10 Pilot note:
    Run this script against 10 PNGs from figma_templates/ to evaluate conversion
    quality. Expected: 7+ of 10 score >= 7. Failures are logged to curation_queue/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project src is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ---------------------------------------------------------------------------
# Report data structure (plain class, avoids importlib @dataclass __module__ issue)
# ---------------------------------------------------------------------------


class ConversionReport:
    """Summary of a batch conversion run."""

    def __init__(self) -> None:
        self.total: int = 0
        self.success: int = 0
        self.failed: int = 0
        self.curation_queue: list[dict] = []
        self.scores: list[float] = []

    @property
    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(self.scores) / len(self.scores), 2)


def generate_report(report: ConversionReport) -> str:
    """Format a ConversionReport as a human-readable string.

    Args:
        report: ConversionReport instance from batch_convert().

    Returns:
        Multi-line report string.

    Example output::

        === Figma Template Conversion Report ===
        Total:    10
        Success:  8
        Failed:   2
        Avg Score: 7.45

        Curation Queue (score < 7):
          - template_3.png (score: 5.2)
          - template_8.png (score: 6.1)
    """
    lines = [
        "=== Figma Template Conversion Report ===",
        f"Total:    {report.total}",
        f"Success:  {report.success}",
        f"Failed:   {report.failed}",
        f"Avg Score: {report.average_score}",
    ]
    if report.curation_queue:
        lines.append("")
        lines.append("Curation Queue (score < 7):")
        for item in report.curation_queue:
            lines.append(f"  - {item['path']} (score: {item['score']})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core batch conversion
# ---------------------------------------------------------------------------


async def batch_convert(
    *,
    input_dir: Path,
    output_dir: Path,
    provider: Any,
    score_threshold: float = 7.0,
) -> ConversionReport:
    """Convert all PNG files in input_dir to HTML/CSS.

    Args:
        input_dir: Directory containing PNG files.
        output_dir: Directory to write converted templates.
        provider: AIProviderBase implementation (injected, can be mock).
        score_threshold: Minimum quality score for auto-registration.

    Returns:
        ConversionReport with total, success, failed, average_score.
    """
    from detail_forge.asset_pipeline import PngConverter

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    png_files = sorted(input_dir.glob("*.png"))
    report = ConversionReport()
    report.total = len(png_files)
    converter = PngConverter(provider=provider)

    for png_path in png_files:
        try:
            result = await converter.convert(png_path)

            out_name = png_path.stem
            out_dir = output_dir / out_name
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "template.html").write_text(result.html, encoding="utf-8")
            (out_dir / "styles.css").write_text(result.css, encoding="utf-8")
            (out_dir / "slot_mapping.json").write_text(
                json.dumps(result.slot_mapping.to_dict(), ensure_ascii=False, indent=2)
            )

            report.scores.append(result.quality_score)

            if result.needs_curation:
                report.curation_queue.append(
                    {"path": str(png_path.name), "score": result.quality_score}
                )
                report.failed += 1
            else:
                report.success += 1

        except Exception as exc:  # noqa: BLE001
            report.failed += 1
            report.curation_queue.append(
                {"path": str(png_path.name), "score": 0, "error": str(exc)}
            )

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for CLI usage.

    T-1.3.10 Pilot:
        Run against 10 sample PNGs from figma_templates/ to validate the
        end-to-end pipeline before full batch execution.

        Expected outcome:
            - 7+ of 10 conversions score >= 7.0
            - Score < 7 files are written to data/curation_queue/
            - Conversion report printed to stdout
    """
    parser = argparse.ArgumentParser(description="Batch convert Figma template PNGs")
    project_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--input",
        default=str(project_root / "data" / "d1000_knowledge" / "figma_templates"),
        help="Directory containing PNG files",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "data" / "templates"),
        help="Output directory for converted templates",
    )
    args = parser.parse_args()

    from detail_forge.providers.claude import ClaudeProvider
    provider = ClaudeProvider()

    report = asyncio.run(
        batch_convert(
            input_dir=Path(args.input),
            output_dir=Path(args.output),
            provider=provider,
        )
    )
    print(generate_report(report))


if __name__ == "__main__":
    main()
