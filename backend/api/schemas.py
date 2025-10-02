"""API schema definitions."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, HttpUrl


class CrawlRequest(BaseModel):
    """Request schema for /crawl endpoint."""
    url: str


class CrawlResponse(BaseModel):
    """Response schema for /crawl endpoint."""
    crawl_id: str
    base_url: str
    status: str
    total_pages: int
    total_elements: int
    total_links: int


class CrawlSummaryResponse(BaseModel):
    """Response schema for /crawl/{crawl_id}/summary endpoint."""
    crawl_id: str
    base_url: str
    domain: str
    status: str
    page_count: int
    element_count: int
    link_count: int


class PageInfo(BaseModel):
    """Page information schema."""
    url: str
    title: str
    depth: int
    elements: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]


class PathFindingRequest(BaseModel):
    """Request schema for /graph/find-path endpoint."""
    start_url: str
    end_url: str


class PathFindingResponse(BaseModel):
    """Response schema for /graph/find-path endpoint."""
    path_found: bool
    path_length: int
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    total_distance: int


class GenerateTestsRequest(BaseModel):
    """Request schema for /generate-tests endpoint."""
    crawl_id: str
    page_urls: List[str]  # List of page URLs to generate tests for


class TestGenerationResponse(BaseModel):
    """Response schema for /generate-tests endpoint."""
    crawl_id: str
    test_suite_id: str
    test_count: int
    tests: List[Dict[str, Any]]


class CompileTestsRequest(BaseModel):
    """Request schema for /compile-tests endpoint."""
    suite_id: str


class CompileTestsResponse(BaseModel):
    """Response schema for /compile-tests endpoint."""
    suite_id: str
    spec_file_path: str
    success: bool


class RunTestsRequest(BaseModel):
    """Request schema for /run-tests endpoint."""
    suite_id: str


class RunTestsResponse(BaseModel):
    """Response schema for /run-tests endpoint."""
    suite_id: str
    run_id: str
    total_tests: int
    passed: int
    failed: int
    report_path: Optional[str] = None
    ai_summary: Optional[str] = None
    test_results: Optional[List[Dict[str, Any]]] = None


class GraphVisualizationResponse(BaseModel):
    """Response schema for /graph/{crawl_id}/visualize endpoint."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class CrawlerConfigRequest(BaseModel):
    """Request schema for /config/crawler endpoint."""
    max_depth: int
    max_pages: int
    timeout: int
    screenshot: bool
    page_delay_ms: int
    skip_embeddings: bool