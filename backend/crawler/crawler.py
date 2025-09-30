"""Main crawler implementation using Playwright BFS."""

from pathlib import Path
from typing import Set, List
from playwright.async_api import async_playwright, Page, Browser
from backend.shared.types import AppMap, PageInfo
from backend.shared.config import get_config
from backend.shared.utils import get_timestamp, save_json
from .page_analyzer import PageAnalyzer


class Crawler:
    """BFS web crawler using Playwright."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.config = get_config()
        self.visited_urls: Set[str] = set()
        self.pages: List[PageInfo] = []
        self.analyzer = PageAnalyzer()

    async def crawl(self) -> AppMap:
        """Perform BFS crawl of the website."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.config.crawler.screenshot)
            page = await browser.new_page(
                viewport={
                    "width": self.config.crawler.viewport["width"],
                    "height": self.config.crawler.viewport["height"],
                }
            )

            queue = [self.base_url]
            depth_map = {self.base_url: 0}

            while queue and len(self.visited_urls) < self.config.crawler.max_pages:
                current_url = queue.pop(0)
                current_depth = depth_map[current_url]

                if current_url in self.visited_urls or current_depth > self.config.crawler.max_depth:
                    continue

                print(f"Crawling: {current_url} (depth: {current_depth})")

                try:
                    page_info = await self._crawl_page(page, current_url)
                    self.pages.append(page_info)
                    self.visited_urls.add(current_url)

                    # Extract links for BFS
                    if current_depth < self.config.crawler.max_depth:
                        links = await self._extract_links(page)
                        for link in links:
                            if link not in self.visited_urls and link not in queue:
                                queue.append(link)
                                depth_map[link] = current_depth + 1

                except Exception as e:
                    print(f"Error crawling {current_url}: {e}")
                    continue

            await browser.close()

        # Create app map
        app_map = AppMap(
            base_url=self.base_url,
            pages=self.pages,
            crawl_timestamp=get_timestamp(),
            total_pages=len(self.pages),
        )

        # Save app map
        self._save_app_map(app_map)

        return app_map

    async def _crawl_page(self, page: Page, url: str) -> PageInfo:
        """Crawl a single page and extract information."""
        await page.goto(url, timeout=self.config.crawler.timeout, wait_until="networkidle")

        # Get page title
        title = await page.title()

        # Analyze page elements and actions
        elements = await self.analyzer.extract_elements(page)
        actions = await self.analyzer.extract_actions(page)
        forms = await self.analyzer.extract_forms(page)

        # Take screenshot
        screenshot_path = None
        if self.config.crawler.screenshot:
            screenshot_path = self._get_screenshot_path(url)
            await page.screenshot(path=screenshot_path, full_page=True)

        return PageInfo(
            url=url,
            title=title,
            elements=elements,
            actions=actions,
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            forms=forms,
        )

    async def _extract_links(self, page: Page) -> List[str]:
        """Extract all internal links from the current page."""
        links = await page.eval_on_selector_all(
            "a[href]",
            """elements => elements.map(el => el.href).filter(href => href)"""
        )

        # Filter to same-origin links only
        internal_links = []
        for link in links:
            if link.startswith(self.base_url) and link not in self.visited_urls:
                # Remove fragments and query params for deduplication
                clean_link = link.split("#")[0].split("?")[0]
                internal_links.append(clean_link)

        return list(set(internal_links))

    def _get_screenshot_path(self, url: str) -> Path:
        """Generate screenshot path for a URL."""
        from backend.shared.utils import sanitize_filename

        url_part = url.replace(self.base_url, "").strip("/")
        filename = sanitize_filename(url_part) or "home"
        screenshots_dir = Path(self.config.storage.artifacts_path) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir / f"{filename}.png"

    def _save_app_map(self, app_map: AppMap) -> None:
        """Save the app map to file."""
        from backend.shared.utils import sanitize_filename

        domain = self.base_url.split("//")[1].split("/")[0]
        filename = f"{sanitize_filename(domain)}_app_map.json"
        output_path = Path(self.config.storage.app_maps_path) / filename

        save_json(app_map.model_dump(), output_path)
        print(f"App map saved to: {output_path}")