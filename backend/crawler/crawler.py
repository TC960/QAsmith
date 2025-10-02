"""Main crawler implementation using Playwright BFS with Neo4j integration."""

import asyncio
from pathlib import Path
from typing import Set, List, Optional, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page, Browser
from backend.shared.types import PageElement, PageAction
from backend.shared.config import get_config
from backend.shared.graph_db import GraphDB
from backend.shared.utils import get_timestamp, sanitize_filename
from .page_analyzer import PageAnalyzer


class Crawler:
    """BFS web crawler using Playwright with Neo4j graph storage."""

    def __init__(self, graph_db: GraphDB, embedding_generator=None):
        self.config = get_config()
        self.graph_db = graph_db
        self.visited_urls: Set[str] = set()
        self.analyzer = PageAnalyzer()
        self.crawl_id: Optional[str] = None
        self.embedding_generator = embedding_generator
        self.progress_callback = None  # For WebSocket progress updates

    async def crawl(self, base_url: str) -> str:
        """Perform BFS crawl of the website and store in Neo4j graph."""
        print(f"🕷️  CRAWLER: Starting crawl for {base_url}")
        base_url = base_url.rstrip("/")
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        
        print(f"🔗 CRAWLER: Parsed domain: {domain}")
        
        try:
            # Create crawl in Neo4j
            print("📊 CRAWLER: Creating crawl record in Neo4j...")
            self.crawl_id = self.graph_db.create_crawl(base_url, domain)
            print(f"✅ CRAWLER: Created crawl {self.crawl_id} for {base_url}")
        except Exception as e:
            print(f"❌ CRAWLER: Failed to create crawl in Neo4j: {e}")
            raise
        
        try:
            print("🌐 CRAWLER: Launching Playwright browser...")
            async with async_playwright() as p:
                # Use Firefox for better macOS compatibility
                browser = await p.firefox.launch(headless=True)
                print("✅ CRAWLER: Browser launched successfully")
                
                page = await browser.new_page(
                    viewport={
                        "width": self.config.crawler.viewport["width"],
                        "height": self.config.crawler.viewport["height"],
                    }
                )
                print(f"📄 CRAWLER: Created new page with viewport {self.config.crawler.viewport}")

                queue = [base_url]
                page_id_map = {}  # URL -> page_id mapping for linking

                print(f"🎯 CRAWLER: Starting BFS crawl (max_depth: {self.config.crawler.max_depth}, max_pages: {self.config.crawler.max_pages})")

                while queue and len(self.visited_urls) < self.config.crawler.max_pages:
                    current_url = queue.pop(0)

                    # Calculate depth based on URL path segments (not BFS order)
                    current_depth = self._calculate_url_depth(current_url, base_url)

                    if current_url in self.visited_urls or current_depth > self.config.crawler.max_depth:
                        print(f"⏭️  CRAWLER: Skipping {current_url} (visited: {current_url in self.visited_urls}, depth: {current_depth})")
                        continue

                    print(f"🔍 CRAWLER: Crawling {current_url} (depth: {current_depth}, queue: {len(queue)}, visited: {len(self.visited_urls)})")

                    try:
                        page_id = await self._crawl_page(page, current_url, current_depth)
                        page_id_map[current_url] = page_id
                        self.visited_urls.add(current_url)
                        print(f"✅ CRAWLER: Successfully crawled {current_url} -> page_id: {page_id}")

                        # Extract links for BFS crawling
                        if current_depth < self.config.crawler.max_depth:
                            print(f"🔗 CRAWLER: Extracting links from {current_url}...")
                            links = await self._extract_links(page, base_url)
                            print(f"🔗 CRAWLER: Found {len(links)} internal links")

                            for link in links:
                                # Add to crawl queue if not visited
                                if link not in self.visited_urls and link not in queue:
                                    link_depth = self._calculate_url_depth(link, base_url)
                                    if link_depth <= self.config.crawler.max_depth:
                                        queue.append(link)
                                        print(f"➕ CRAWLER: Added to queue: {link} (depth: {link_depth})")
                        
                        # Add configurable delay between pages (to be respectful to servers)
                        page_delay_ms = getattr(self.config.crawler, 'page_delay_ms', 0)
                        if page_delay_ms > 0:
                            delay_sec = page_delay_ms / 1000
                            print(f"⏱️ CRAWLER: Waiting {delay_sec}s before next page...")
                            await asyncio.sleep(delay_sec)

                    except Exception as e:
                        print(f"❌ CRAWLER: Error crawling {current_url}: {e}")
                        import traceback
                        print(f"🔍 CRAWLER: Traceback: {traceback.format_exc()}")
                        continue

                # Create hierarchical parent-child relationships based on URL structure
                print(f"🔗 CRAWLER: Creating hierarchical parent-child relationships...")
                self._create_hierarchical_links(page_id_map, base_url)
                print(f"✅ CRAWLER: Hierarchical relationships created")

                await browser.close()
                print("🔒 CRAWLER: Browser closed")

        except Exception as e:
            print(f"❌ CRAWLER: Critical error during crawl: {e}")
            import traceback
            print(f"🔍 CRAWLER: Full traceback: {traceback.format_exc()}")
            raise

        # Mark crawl as complete
        try:
            print("📊 CRAWLER: Marking crawl as complete in Neo4j...")
            self.graph_db.mark_crawl_complete(self.crawl_id)
            print(f"🎉 CRAWLER: Crawl {self.crawl_id} completed successfully with {len(self.visited_urls)} pages")
        except Exception as e:
            print(f"❌ CRAWLER: Failed to mark crawl as complete: {e}")
            raise
        
        return self.crawl_id

    async def _crawl_page(self, page: Page, url: str, depth: int) -> str:
        """Crawl a single page and store in Neo4j graph."""
        print(f"📄 PAGE: Loading {url}...")
        
        # Send progress update
        if self.progress_callback:
            await self.progress_callback({
                "type": "page_loading",
                "url": url,
                "depth": depth,
                "visited": len(self.visited_urls)
            })
        
        try:
            await page.goto(url, timeout=self.config.crawler.timeout, wait_until="domcontentloaded")
            print(f"✅ PAGE: Successfully loaded {url}")
        except Exception as e:
            print(f"❌ PAGE: Failed to load {url}: {e}")
            if self.progress_callback:
                await self.progress_callback({
                    "type": "page_error",
                    "url": url,
                    "error": str(e)
                })
            raise

        # Get page title
        try:
            title = await page.title()
            print(f"📝 PAGE: Title: '{title}'")
        except Exception as e:
            print(f"❌ PAGE: Failed to get title: {e}")
            title = "Unknown Title"

        # Extract comprehensive page content (SKIP IF DISABLED FOR SPEED)
        content_data = None
        embedding = None

        skip_embeddings = getattr(self.config.crawler, 'skip_embeddings', True)  # Default to True (skip for speed)
        print(f"🔍 PAGE: skip_embeddings setting = {skip_embeddings}")

        if not skip_embeddings:
            try:
                print(f"📊 PAGE: Extracting page content...")
                content_data = await self.analyzer.extract_page_content(page)
                print(f"✅ PAGE: Extracted content ({content_data.get('content_length', 0)} chars)")
                
                # Generate embedding if generator is available
                if self.embedding_generator and content_data.get("embedding_text"):
                    print(f"🧠 PAGE: Generating AI embedding...")
                    embedding = self.embedding_generator.generate_embedding(content_data["embedding_text"])
                    print(f"✅ PAGE: Generated embedding with {len(embedding)} dimensions")
            except Exception as e:
                print(f"❌ PAGE: Failed to extract content: {e}")
        else:
            print(f"⏩ PAGE: Skipping embeddings for speed")

        # Take screenshot (viewport only for speed - not full page)
        screenshot_path = None
        if self.config.crawler.screenshot:
            try:
                screenshot_path = self._get_screenshot_path(url)
                await page.screenshot(path=screenshot_path, full_page=False)  # Changed to False for speed
                print(f"📸 PAGE: Screenshot saved to {screenshot_path}")
            except Exception as e:
                print(f"❌ PAGE: Failed to take screenshot: {e}")

        # Add page to Neo4j with rich content
        try:
            print(f"📊 PAGE: Adding page to Neo4j...")
            page_id = self.graph_db.add_page(
                crawl_id=self.crawl_id,
                url=url,
                title=title,
                depth=depth,
                screenshot_path=str(screenshot_path) if screenshot_path else None,
                content_data=content_data,
                embedding=embedding
            )
            print(f"✅ PAGE: Added to Neo4j with page_id: {page_id}")
            
            # Send progress update
            if self.progress_callback:
                await self.progress_callback({
                    "type": "page_complete",
                    "url": url,
                    "page_id": page_id,
                    "title": title,
                    "depth": depth,
                    "content_length": content_data.get("content_length", 0) if content_data else 0
                })
        except Exception as e:
            print(f"❌ PAGE: Failed to add page to Neo4j: {e}")
            raise

        # Analyze page elements and add to graph (SIMPLIFIED FOR SPEED)
        try:
            # Check if we should do full element extraction or simplified version
            skip_detailed_elements = getattr(self.config.crawler, 'skip_embeddings', True)  # Default to True (skip for speed)
            
            if skip_detailed_elements:
                # FAST MODE: Just extract links and basic elements in bulk
                print(f"⚡ PAGE: Fast element extraction mode...")
                
                # Extract links directly from page
                links = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => ({
                            url: a.href,
                            text: a.textContent?.trim() || '',
                            type: 'link'
                        }))
                        .filter(link => link.url && !link.url.startsWith('javascript:'))
                        .slice(0, 100)
                """)
                
                # Extract basic interactive elements
                buttons = await page.evaluate("""
                    () => Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'))
                        .map(el => ({
                            text: el.textContent?.trim() || el.value || '',
                            type: 'button'
                        }))
                        .slice(0, 50)
                """)
                
                # Add all elements in bulk
                element_count = len(links) + len(buttons)
                print(f"⚡ PAGE: Found {element_count} elements ({len(links)} links, {len(buttons)} buttons)")
                
                # Add a sample of elements to Neo4j (just for graph structure)
                sample_size = min(10, element_count)
                for i in range(sample_size):
                    if i < len(links):
                        element_data = links[i]
                        try:
                            self.graph_db.add_element(
                                page_id=page_id,
                                selector=element_data.get('text', '')[:30] or element_data.get('url', '')[:30],
                                selector_strategy="TEXT",
                                element_type="link",
                                text=element_data.get('text', '')[:50],
                                attributes={"href": element_data.get('url', '')}
                            )
                        except Exception as e:
                            print(f"⚠️ PAGE: Skipping element: {e}")
                
                print(f"⚡ PAGE: Added {sample_size} sample elements")
                
            else:
                # DETAILED MODE: Full element extraction (slower but more complete)
                print(f"🔍 PAGE: Analyzing page elements...")
                elements = await self.analyzer.extract_elements(page)
                print(f"🔍 PAGE: Found {len(elements)} interactive elements")
                
                # Process a reasonable number of elements (for performance)
                max_elements = 30  # Limit for performance
                for i, element in enumerate(elements[:max_elements]):
                    print(f"🔧 PAGE: Processing element {i+1}/{min(len(elements), max_elements)}: {element.element_type} - {element.selector}")
                    try:
                        element_id = self.graph_db.add_element(
                            page_id=page_id,
                            selector=element.selector,
                            selector_strategy=element.selector_strategy.value,
                            element_type=element.element_type,
                            text=element.text,
                            attributes=element.attributes
                        )
                        
                        # Add possible actions for this element
                        await self._add_element_actions(element, element_id)
                        
                    except Exception as e:
                        print(f"⚠️ PAGE: Skipping element: {e}")
                        continue
            
        except Exception as e:
            print(f"❌ PAGE: Failed to analyze elements: {e}")
            # Don't raise here, continue with page creation

        print(f"🎉 PAGE: Successfully processed {url}")
        return page_id

    def _create_hierarchical_links(self, page_id_map: dict, base_url: str):
        """Create parent-child links based on URL hierarchy.

        Examples:
            github.com/tc960 -> parent: github.com
            github.com/tc960/munch -> parent: github.com/tc960
            github.com/omega/lol -> parent: github.com (no tc960 in path)

        If a parent URL doesn't exist in the crawl, attach to the nearest ancestor
        that does exist (including the base URL).
        """
        clean_base = base_url.split("#")[0].split("?")[0].rstrip("/")

        for child_url, child_page_id in page_id_map.items():
            # Skip the base URL itself (it has no parent)
            clean_child = child_url.split("#")[0].split("?")[0].rstrip("/")
            if clean_child == clean_base:
                continue

            # Find the parent URL by removing the last path segment
            path_after_base = clean_child.replace(clean_base, "")
            segments = [s for s in path_after_base.split("/") if s]

            if not segments:
                continue

            # Try to find the most specific parent first, then work backwards
            parent_url = None
            for i in range(len(segments) - 1, 0, -1):
                potential_parent = clean_base + "/" + "/".join(segments[:i])
                if potential_parent in page_id_map:
                    parent_url = potential_parent
                    break

            # If no intermediate parent exists, link directly to base URL
            if not parent_url:
                parent_url = clean_base

            # Create the hierarchical link
            if parent_url in page_id_map:
                parent_page_id = page_id_map[parent_url]
                try:
                    # Extract link text (last segment of child URL)
                    link_text = segments[-1] if segments else ""
                    self.graph_db.link_pages(parent_page_id, child_page_id, link_text)
                    print(f"🔗 HIERARCHICAL LINK: {parent_url} -> {clean_child}")
                except Exception as e:
                    print(f"⚠️ CRAWLER: Failed to create hierarchical link {parent_url} -> {clean_child}: {e}")

    def _calculate_url_depth(self, url: str, base_url: str) -> int:
        """Calculate depth based on URL path segments.

        Examples:
            github.com -> depth 0
            github.com/tc960 -> depth 1
            github.com/tc960/munch -> depth 2
        """
        # Normalize URLs by removing trailing slashes, fragments, and query params
        clean_url = url.split("#")[0].split("?")[0].rstrip("/")
        clean_base = base_url.split("#")[0].split("?")[0].rstrip("/")

        # If it's the base URL itself, depth is 0
        if clean_url == clean_base:
            return 0

        # Get the path after the base URL
        if not clean_url.startswith(clean_base):
            return 0  # Not a child of base URL

        path = clean_url.replace(clean_base, "")

        # Count non-empty path segments
        segments = [s for s in path.split("/") if s]
        return len(segments)

    async def _extract_links(self, page: Page, base_url: str) -> List[str]:
        """Extract internal links, prioritizing top-level navigation."""
        links = await page.eval_on_selector_all(
            "a[href]",
            """elements => elements.map(el => el.href).filter(href => href)"""
        )

        # Filter to same-origin links only and categorize by depth
        top_level_links = []  # e.g., github.com/about
        deeper_links = []     # e.g., github.com/solutions/industry/manufacturing

        for link in links:
            if link.startswith(base_url) and link not in self.visited_urls:
                # Remove fragments and query params for deduplication
                clean_link = link.split("#")[0].split("?")[0].rstrip("/")

                # Skip if same as base URL
                if clean_link == base_url.rstrip("/"):
                    continue

                # Use the new depth calculation method
                depth = self._calculate_url_depth(clean_link, base_url)

                # Prioritize top-level links (depth 1-2)
                if depth <= 2:
                    top_level_links.append(clean_link)
                else:
                    deeper_links.append(clean_link)

        # Return top-level links first, then deeper ones
        all_links = list(set(top_level_links)) + list(set(deeper_links))
        print(f"🔗 LINK PRIORITY: {len(top_level_links)} top-level, {len(deeper_links)} deeper links")
        return all_links

    async def _add_element_actions(self, element: PageElement, element_id: str):
        """Add possible actions for an element to the graph."""
        # Determine possible actions based on element type
        if element.element_type in ["button", "input[type='button']", "input[type='submit']"]:
            self.graph_db.add_action(element_id, "click")
        elif element.element_type == "link":
            # For links, we'll add the target URL when we create page relationships
            self.graph_db.add_action(element_id, "click")
        elif element.element_type in ["input", "textarea"]:
            input_type = element.attributes.get("type", "text")
            if input_type in ["text", "email", "password", "search", "tel", "url"]:
                self.graph_db.add_action(element_id, "fill")
            elif input_type in ["checkbox", "radio"]:
                self.graph_db.add_action(element_id, "check")
        elif element.element_type == "select":
            self.graph_db.add_action(element_id, "select")

    async def _create_page_links(self, page: Page, page_id_map: dict, base_url: str):
        """Create LINKS_TO relationships between pages after crawling."""
        for from_url, from_page_id in page_id_map.items():
            try:
                await page.goto(from_url, timeout=self.config.crawler.timeout)
                
                # Get all links on this page
                link_elements = await page.query_selector_all("a[href]")
                for link_elem in link_elements:
                    try:
                        href = await link_elem.get_attribute("href")
                        if href and href.startswith(base_url):
                            clean_href = href.split("#")[0].split("?")[0]
                            if clean_href in page_id_map:
                                link_text = await link_elem.text_content()
                                self.graph_db.link_pages(
                                    from_page_id, 
                                    page_id_map[clean_href], 
                                    link_text
                                )
                    except Exception as e:
                        print(f"Error processing link: {e}")
                        continue
            except Exception as e:
                print(f"Error creating links for {from_url}: {e}")
                continue

    def _get_screenshot_path(self, url: str) -> Path:
        """Generate screenshot path for a URL."""
        parsed_url = urlparse(url)
        url_part = parsed_url.path.strip("/") or "home"
        filename = sanitize_filename(url_part)
        screenshots_dir = Path(self.config.storage.artifacts_path) / "screenshots" / self.crawl_id
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        return screenshots_dir / f"{filename}.png"