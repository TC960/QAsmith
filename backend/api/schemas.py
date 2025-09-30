"""API request/response schemas."""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any


class CrawlRequest(BaseModel):
    """Request to crawl a website."""
    url: HttpUrl


class CrawlResponse(BaseModel):
    """Response from crawl operation."""
    crawl_id: str
    domain: str
    status: str
    message: str


class GraphVisualizationResponse(BaseModel):
    """Graph data for frontend visualization."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class GenerateTestsRequest(BaseModel):
    """Request to generate tests from a graph path."""
    crawl_id: str
    start_url: str
    end_url: str
    test_description: Optional[str] = None


class TestGenerationResponse(BaseModel):
    """Response from test generation."""
    suite_id: str
    test_count: int
    message: str


class RunTestsRequest(BaseModel):
    """Request to run tests."""
    suite_id: str


class PageInfo(BaseModel):
    """Information about a crawled page."""
    page_id: str
    url: str
    title: str
    depth: int
    screenshot_path: Optional[str] = None


class CrawlSummaryResponse(BaseModel):
    """Summary of a crawl."""
    crawl_id: str
    base_url: str
    domain: str
    status: str
    page_count: int
    element_count: int
    link_count: int


class PathFindingRequest(BaseModel):
    """Request to find shortest path between pages."""
    crawl_id: str
    start_url: str
    end_url: str


class PathFindingResponse(BaseModel):
    """Response with shortest path between pages."""
    path: List[Dict[str, str]]
    path_length: int