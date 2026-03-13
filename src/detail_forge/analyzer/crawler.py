"""Competitor detail page crawler using Playwright."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from playwright.async_api import async_playwright

from detail_forge.config import Platform, get_settings


@dataclass
class CompetitorPage:
    """Crawled competitor page data."""
    rank: int = 0
    title: str = ""
    url: str = ""
    platform: Platform = Platform.NAVER
    screenshots: list[bytes] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    full_html: str = ""
    review_count: int = 0
    price: str = ""


@dataclass
class AnalysisResult:
    """Complete competitor analysis result."""
    keyword: str = ""
    competitors: list[CompetitorPage] = field(default_factory=list)
    section_template: list[dict] = field(default_factory=list)  # Combined best structure


class CompetitorCrawler:
    """Crawl competitor product detail pages from Naver/Coupang."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def crawl(self, keyword: str, platforms: list[Platform] | None = None) -> AnalysisResult:
        """Crawl competitor pages for the given keyword."""
        platforms = platforms or [Platform.NAVER, Platform.COUPANG]
        result = AnalysisResult(keyword=keyword)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="ko-KR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )

            for platform in platforms:
                pages = await self._search_platform(context, keyword, platform)
                result.competitors.extend(pages)

            await browser.close()

        # Sort by rank, limit to max_competitors
        result.competitors.sort(key=lambda c: c.rank)
        result.competitors = result.competitors[: self.settings.max_competitors]

        return result

    async def _search_platform(
        self, context, keyword: str, platform: Platform
    ) -> list[CompetitorPage]:
        """Search a platform and get top product detail pages."""
        pages: list[CompetitorPage] = []

        if platform == Platform.NAVER:
            pages = await self._search_naver(context, keyword)
        elif platform == Platform.COUPANG:
            pages = await self._search_coupang(context, keyword)

        return pages

    async def _search_naver(self, context, keyword: str) -> list[CompetitorPage]:
        """Search Naver Smart Store for keyword."""
        page = await context.new_page()
        results: list[CompetitorPage] = []

        try:
            search_url = f"https://search.shopping.naver.com/search/all?query={keyword}"
            await page.goto(search_url, timeout=self.settings.crawl_timeout_seconds * 1000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Extract product links
            items = await page.query_selector_all(".product_item__MDtDF")
            for rank, item in enumerate(items[: self.settings.max_competitors], 1):
                link_el = await item.query_selector("a.product_link__TrAac")
                title_el = await item.query_selector(".product_title__Mmw2K")

                if link_el and title_el:
                    url = await link_el.get_attribute("href") or ""
                    title = await title_el.inner_text()
                    results.append(
                        CompetitorPage(
                            rank=rank,
                            title=title.strip(),
                            url=url,
                            platform=Platform.NAVER,
                        )
                    )
        except Exception as e:
            print(f"[Naver] Search error: {e}")
        finally:
            await page.close()

        # Crawl each detail page
        for comp in results:
            await self._crawl_detail_page(context, comp)

        return results

    async def _search_coupang(self, context, keyword: str) -> list[CompetitorPage]:
        """Search Coupang for keyword."""
        page = await context.new_page()
        results: list[CompetitorPage] = []

        try:
            search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
            await page.goto(search_url, timeout=self.settings.crawl_timeout_seconds * 1000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            items = await page.query_selector_all(".search-product")
            for rank, item in enumerate(items[: self.settings.max_competitors], 1):
                link_el = await item.query_selector("a.search-product-link")
                title_el = await item.query_selector(".name")

                if link_el and title_el:
                    href = await link_el.get_attribute("href") or ""
                    url = f"https://www.coupang.com{href}" if href.startswith("/") else href
                    title = await title_el.inner_text()
                    results.append(
                        CompetitorPage(
                            rank=rank,
                            title=title.strip(),
                            url=url,
                            platform=Platform.COUPANG,
                        )
                    )
        except Exception as e:
            print(f"[Coupang] Search error: {e}")
        finally:
            await page.close()

        for comp in results:
            await self._crawl_detail_page(context, comp)

        return results

    async def _crawl_detail_page(self, context, comp: CompetitorPage) -> None:
        """Crawl a single product detail page and capture screenshots."""
        if not comp.url:
            return

        page = await context.new_page()
        try:
            await page.goto(comp.url, timeout=self.settings.crawl_timeout_seconds * 1000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Scroll to load lazy content
            await self._scroll_page(page)

            # Full page screenshot
            screenshot = await page.screenshot(full_page=True)
            comp.screenshots.append(screenshot)

            # Get HTML
            comp.full_html = await page.content()

        except Exception as e:
            print(f"[Detail] Crawl error for {comp.title}: {e}")
        finally:
            await page.close()

    async def _scroll_page(self, page) -> None:
        """Scroll page to trigger lazy-loaded content."""
        await page.evaluate("""
            async () => {
                const delay = ms => new Promise(r => setTimeout(r, ms));
                const height = document.body.scrollHeight;
                for (let y = 0; y < height; y += 500) {
                    window.scrollTo(0, y);
                    await delay(200);
                }
                window.scrollTo(0, 0);
            }
        """)
        await asyncio.sleep(1)
