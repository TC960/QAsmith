"""Neo4j graph database abstraction layer for QAsmith."""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from .types import AppMap, PageInfo, PageElement, PageAction, SelectorStrategy, ActionType
from .utils import get_timestamp
import json


class GraphDB:
    """Manages Neo4j graph database operations for website crawl data."""

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j driver connection."""
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._create_constraints()

    def _create_constraints(self):
        """Create unique constraints and indexes for optimal performance."""
        with self.driver.session() as session:
            # Unique constraint on Page URL within a crawl
            session.run("""
                CREATE CONSTRAINT page_url_crawl IF NOT EXISTS
                FOR (p:Page) REQUIRE (p.crawl_id, p.url) IS UNIQUE
            """)

            # Index on crawl_id for fast filtering
            session.run("""
                CREATE INDEX crawl_id_idx IF NOT EXISTS
                FOR (p:Page) ON (p.crawl_id)
            """)

            # Index on element selectors
            session.run("""
                CREATE INDEX element_selector_idx IF NOT EXISTS
                FOR (e:Element) ON (e.selector)
            """)

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

    def create_crawl(self, base_url: str, domain: str) -> str:
        """
        Create a new crawl node and return crawl_id.

        Args:
            base_url: Starting URL of the crawl
            domain: Domain name extracted from URL

        Returns:
            crawl_id: Unique identifier for this crawl
        """
        with self.driver.session() as session:
            result = session.run("""
                CREATE (c:Crawl {
                    crawl_id: randomUUID(),
                    base_url: $base_url,
                    domain: $domain,
                    created_at: datetime(),
                    status: 'in_progress'
                })
                RETURN c.crawl_id as crawl_id
            """, base_url=base_url, domain=domain)
            return result.single()["crawl_id"]

    def add_page(self, crawl_id: str, url: str, title: str, depth: int,
                 screenshot_path: Optional[str] = None,
                 content_data: Optional[Dict[str, Any]] = None,
                 embedding: Optional[List[float]] = None) -> str:
        """
        Add a page node to the graph with rich content data.

        Args:
            crawl_id: Crawl this page belongs to
            url: Page URL
            title: Page title
            depth: Crawl depth level
            screenshot_path: Optional path to screenshot
            content_data: Optional dict with meta_description, content_text, headers, etc.
            embedding: Optional embedding vector for semantic search

        Returns:
            page_id: Unique identifier for this page
        """
        with self.driver.session() as session:
            # Prepare content fields
            meta_description = ""
            content_text = ""
            content_length = 0
            link_count = 0
            image_count = 0
            headers_json = "{}"
            
            if content_data:
                meta_description = content_data.get("meta_description", "")
                content_text = content_data.get("content_text", "")[:10000]  # Limit
                content_length = content_data.get("content_length", 0)
                link_count = content_data.get("link_count", 0)
                image_count = content_data.get("image_count", 0)
                headers_json = json.dumps(content_data.get("headers", {}))
            
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                CREATE (p:Page {
                    page_id: randomUUID(),
                    crawl_id: $crawl_id,
                    url: $url,
                    title: $title,
                    depth: $depth,
                    screenshot_path: $screenshot_path,
                    meta_description: $meta_description,
                    content_text: $content_text,
                    content_length: $content_length,
                    link_count: $link_count,
                    image_count: $image_count,
                    headers: $headers_json,
                    embedding: $embedding,
                    created_at: datetime()
                })
                CREATE (c)-[:HAS_PAGE]->(p)
                RETURN p.page_id as page_id
            """, crawl_id=crawl_id, url=url, title=title, depth=depth,
               screenshot_path=screenshot_path, meta_description=meta_description,
               content_text=content_text, content_length=content_length,
               link_count=link_count, image_count=image_count,
               headers_json=headers_json, embedding=embedding or [])
            return result.single()["page_id"]

    def add_element(self, page_id: str, selector: str, selector_strategy: str,
                    element_type: str, text: Optional[str] = None,
                    attributes: Dict[str, Any] = None) -> str:
        """
        Add an interactive element to a page.

        Args:
            page_id: Page this element belongs to
            selector: Element selector string
            selector_strategy: Strategy used (test-id, aria-label, text, css)
            element_type: Type of element (button, input, link, etc.)
            text: Optional visible text
            attributes: Optional element attributes

        Returns:
            element_id: Unique identifier for this element
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Page {page_id: $page_id})
                CREATE (e:Element {
                    element_id: randomUUID(),
                    selector: $selector,
                    selector_strategy: $selector_strategy,
                    element_type: $element_type,
                    text: $text,
                    attributes: $attributes
                })
                CREATE (p)-[:HAS_ELEMENT]->(e)
                RETURN e.element_id as element_id
            """, page_id=page_id, selector=selector, selector_strategy=selector_strategy,
               element_type=element_type, text=text, attributes=json.dumps(attributes or {}))
            return result.single()["element_id"]

    def add_action(self, element_id: str, action_type: str,
                   target_url: Optional[str] = None, value: Optional[str] = None):
        """
        Add an action that can be performed on an element.

        Args:
            element_id: Element this action belongs to
            action_type: Type of action (click, fill, submit, etc.)
            target_url: Optional URL this action navigates to
            value: Optional value for fill actions
        """
        with self.driver.session() as session:
            session.run("""
                MATCH (e:Element {element_id: $element_id})
                CREATE (a:Action {
                    action_id: randomUUID(),
                    action_type: $action_type,
                    target_url: $target_url,
                    value: $value
                })
                CREATE (e)-[:CAN_PERFORM]->(a)
            """, element_id=element_id, action_type=action_type,
               target_url=target_url, value=value)

    def link_pages(self, from_page_id: str, to_page_id: str, link_text: Optional[str] = None):
        """
        Create a navigation link between two pages.

        Args:
            from_page_id: Source page
            to_page_id: Target page
            link_text: Optional text of the link
        """
        with self.driver.session() as session:
            session.run("""
                MATCH (from:Page {page_id: $from_page_id})
                MATCH (to:Page {page_id: $to_page_id})
                MERGE (from)-[l:LINKS_TO]->(to)
                ON CREATE SET l.link_text = $link_text, l.created_at = datetime()
            """, from_page_id=from_page_id, to_page_id=to_page_id, link_text=link_text)

    def mark_crawl_complete(self, crawl_id: str):
        """Mark a crawl as completed."""
        with self.driver.session() as session:
            session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                SET c.status = 'completed', c.completed_at = datetime()
            """, crawl_id=crawl_id)

    def get_crawl_summary(self, crawl_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a crawl.

        Args:
            crawl_id: Crawl to summarize

        Returns:
            Dictionary with page count, element count, etc.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                OPTIONAL MATCH (c)-[:HAS_PAGE]->(p:Page)
                OPTIONAL MATCH (p)-[:HAS_ELEMENT]->(e:Element)
                OPTIONAL MATCH (p)-[:LINKS_TO]->(linked:Page)
                RETURN
                    c.base_url as base_url,
                    c.domain as domain,
                    c.status as status,
                    count(DISTINCT p) as page_count,
                    count(DISTINCT e) as element_count,
                    count(DISTINCT linked) as link_count
            """, crawl_id=crawl_id)
            record = result.single()
            return dict(record) if record else {}

    def get_all_pages(self, crawl_id: str) -> List[Dict[str, Any]]:
        """
        Get all pages for a crawl.

        Args:
            crawl_id: Crawl to query

        Returns:
            List of page dictionaries
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})-[:HAS_PAGE]->(p:Page)
                RETURN p.page_id as page_id, p.url as url, p.title as title,
                       p.depth as depth, p.screenshot_path as screenshot_path
                ORDER BY p.depth, p.url
            """, crawl_id=crawl_id)
            return [dict(record) for record in result]

    def find_shortest_path(self, crawl_id: str, start_url: str, end_url: str) -> List[Dict[str, Any]]:
        """
        Find shortest navigation path between two pages using Neo4j's shortestPath algorithm.

        Args:
            crawl_id: Crawl to search within
            start_url: Starting page URL
            end_url: Ending page URL

        Returns:
            List of pages in the shortest path, or empty list if no path exists
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (start:Page {crawl_id: $crawl_id, url: $start_url})
                MATCH (end:Page {crawl_id: $crawl_id, url: $end_url})
                MATCH path = shortestPath((start)-[:LINKS_TO*]->(end))
                RETURN [node in nodes(path) | {
                    page_id: node.page_id,
                    url: node.url,
                    title: node.title
                }] as pages
            """, crawl_id=crawl_id, start_url=start_url, end_url=end_url)

            record = result.single()
            return record["pages"] if record else []

    def export_path_to_appmap(self, crawl_id: str, page_ids: List[str]) -> AppMap:
        """
        Export a specific path (list of pages) to AppMap format for LLM consumption.

        Args:
            crawl_id: Crawl to export from
            page_ids: List of page IDs to include in export

        Returns:
            AppMap object compatible with test generator
        """
        with self.driver.session() as session:
            # First, get crawl metadata
            crawl_result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                RETURN c.base_url as base_url, c.domain as domain
            """, crawl_id=crawl_id)
            crawl_record = crawl_result.single()
            if not crawl_record:
                raise ValueError(f"No crawl found with ID {crawl_id}")

            # Then get all page data with elements and actions
            result = session.run("""
                MATCH (p:Page)
                WHERE p.page_id IN $page_ids AND p.crawl_id = $crawl_id
                OPTIONAL MATCH (p)-[:HAS_ELEMENT]->(e:Element)
                OPTIONAL MATCH (e)-[:CAN_PERFORM]->(a:Action)
                RETURN
                    p.page_id as page_id,
                    p.url as url,
                    p.title as title,
                    p.screenshot_path as screenshot_path,
                    e.element_id as element_id,
                    e.selector as selector,
                    e.selector_strategy as selector_strategy,
                    e.element_type as element_type,
                    e.text as text,
                    e.attributes as attributes,
                    a.action_type as action_type,
                    a.target_url as target_url,
                    a.value as value
                ORDER BY p.page_id, e.element_id, a.action_id
            """, crawl_id=crawl_id, page_ids=page_ids)

            # Group results by page and element
            pages_dict = {}
            for record in result:
                page_id = record["page_id"]

                # Initialize page if not seen
                if page_id not in pages_dict:
                    pages_dict[page_id] = {
                        "url": record["url"],
                        "title": record["title"],
                        "screenshot_path": record["screenshot_path"],
                        "elements": {}
                    }

                # Add element if present
                element_id = record["element_id"]
                if element_id:
                    if element_id not in pages_dict[page_id]["elements"]:
                        pages_dict[page_id]["elements"][element_id] = {
                            "selector": record["selector"],
                            "selector_strategy": record["selector_strategy"],
                            "element_type": record["element_type"],
                            "text": record["text"],
                            "attributes": record["attributes"],
                            "actions": []
                        }

                    # Add action if present
                    if record["action_type"]:
                        pages_dict[page_id]["elements"][element_id]["actions"].append({
                            "action_type": record["action_type"],
                            "target_url": record["target_url"],
                            "value": record["value"]
                        })

            if not pages_dict:
                raise ValueError(f"No pages found for provided page IDs")

            # Convert to AppMap structure
            pages = []
            for page_id, page_data in pages_dict.items():
                elements = []
                actions = []

                # Process elements
                for element_id, elem in page_data["elements"].items():
                    elements.append(PageElement(
                        selector=elem["selector"],
                        selector_strategy=SelectorStrategy(elem["selector_strategy"].lower()),
                        element_type=elem["element_type"],
                        text=elem["text"],
                        attributes=json.loads(elem["attributes"]) if elem["attributes"] else {}
                    ))

                    # Create PageAction for each action
                    for action in elem["actions"]:
                        actions.append(PageAction(
                            action_type=ActionType(action["action_type"].lower()),
                            element=PageElement(
                                selector=elem["selector"],
                                selector_strategy=SelectorStrategy(elem["selector_strategy"].lower()),
                                element_type=elem["element_type"],
                                text=elem["text"],
                                attributes=json.loads(elem["attributes"]) if elem["attributes"] else {}
                            ),
                            description=f"{action['action_type']} on {elem['element_type']}"
                        ))

                pages.append(PageInfo(
                    url=page_data["url"],
                    title=page_data["title"],
                    elements=elements,
                    actions=actions,
                    screenshot_path=page_data["screenshot_path"]
                ))

            return AppMap(
                base_url=crawl_record["base_url"],
                pages=pages,
                crawl_timestamp=get_timestamp(),
                total_pages=len(pages)
            )

    def get_graph_visualization_data(self, crawl_id: str) -> Dict[str, Any]:
        """
        Export graph data in format suitable for frontend visualization (e.g., D3.js, vis.js).

        Args:
            crawl_id: Crawl to visualize

        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})-[:HAS_PAGE]->(p:Page)
                OPTIONAL MATCH (p)-[l:LINKS_TO]->(target:Page)
                RETURN
                    collect(DISTINCT {
                        id: p.page_id,
                        label: p.title,
                        url: p.url,
                        depth: p.depth
                    }) as nodes,
                    collect(DISTINCT {
                        source: p.page_id,
                        target: target.page_id,
                        label: l.link_text
                    }) as edges
            """, crawl_id=crawl_id)

            record = result.single()
            return {
                "nodes": record["nodes"] if record else [],
                "edges": [e for e in (record["edges"] if record else []) if e["target"]]
            }

    def list_all_crawls(self) -> List[Dict[str, Any]]:
        """
        List all crawls in the database.

        Returns:
            List of crawl summaries
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Crawl)
                OPTIONAL MATCH (c)-[:HAS_PAGE]->(p:Page)
                RETURN
                    c.crawl_id as crawl_id,
                    c.base_url as base_url,
                    c.domain as domain,
                    c.status as status,
                    c.created_at as created_at,
                    count(p) as page_count
                ORDER BY c.created_at DESC
            """)
            return [dict(record) for record in result]
