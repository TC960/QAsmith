"""Neo4j graph database abstraction layer for QAsmith."""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from backend.shared.types import AppMap, Page, PageElement, PageAction, SelectorStrategy, ActionType
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
                 screenshot_path: Optional[str] = None) -> str:
        """
        Add a page node to the graph.

        Args:
            crawl_id: Crawl this page belongs to
            url: Page URL
            title: Page title
            depth: Crawl depth level
            screenshot_path: Optional path to screenshot

        Returns:
            page_id: Unique identifier for this page
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                CREATE (p:Page {
                    page_id: randomUUID(),
                    crawl_id: $crawl_id,
                    url: $url,
                    title: $title,
                    depth: $depth,
                    screenshot_path: $screenshot_path,
                    created_at: datetime()
                })
                CREATE (c)-[:HAS_PAGE]->(p)
                RETURN p.page_id as page_id
            """, crawl_id=crawl_id, url=url, title=title, depth=depth,
               screenshot_path=screenshot_path)
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
            result = session.run("""
                MATCH (c:Crawl {crawl_id: $crawl_id})
                MATCH (p:Page)
                WHERE p.page_id IN $page_ids
                OPTIONAL MATCH (p)-[:HAS_ELEMENT]->(e:Element)
                OPTIONAL MATCH (e)-[:CAN_PERFORM]->(a:Action)
                RETURN
                    c.base_url as base_url,
                    c.domain as domain,
                    collect(DISTINCT {
                        url: p.url,
                        title: p.title,
                        screenshot_path: p.screenshot_path,
                        elements: collect(DISTINCT {
                            selector: e.selector,
                            selector_strategy: e.selector_strategy,
                            element_type: e.element_type,
                            text: e.text,
                            attributes: e.attributes,
                            actions: collect(DISTINCT {
                                action_type: a.action_type,
                                target_url: a.target_url,
                                value: a.value
                            })
                        })
                    }) as pages
            """, crawl_id=crawl_id, page_ids=page_ids)

            record = result.single()
            if not record:
                raise ValueError(f"No data found for crawl {crawl_id}")

            # Convert to AppMap structure
            pages = []
            for page_data in record["pages"]:
                elements = []
                for elem in page_data["elements"]:
                    if elem["selector"]:  # Skip null elements
                        actions = []
                        for action in elem["actions"]:
                            if action["action_type"]:  # Skip null actions
                                actions.append(PageAction(
                                    action_type=ActionType(action["action_type"]),
                                    element=PageElement(
                                        selector=elem["selector"],
                                        selector_strategy=SelectorStrategy(elem["selector_strategy"]),
                                        element_type=elem["element_type"],
                                        text=elem["text"],
                                        attributes=json.loads(elem["attributes"]) if elem["attributes"] else {}
                                    ),
                                    description=f"{action['action_type']} on {elem['element_type']}"
                                ))
                        elements.append(PageElement(
                            selector=elem["selector"],
                            selector_strategy=SelectorStrategy(elem["selector_strategy"]),
                            element_type=elem["element_type"],
                            text=elem["text"],
                            attributes=json.loads(elem["attributes"]) if elem["attributes"] else {}
                        ))

                pages.append(Page(
                    url=page_data["url"],
                    title=page_data["title"],
                    screenshot_path=page_data["screenshot_path"],
                    elements=elements,
                    actions=[]  # Actions are derived from elements in this model
                ))

            return AppMap(
                base_url=record["base_url"],
                domain=record["domain"],
                pages=pages,
                crawl_depth=len(pages),  # Path length
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
