"""API request/response schemas."""

from pydantic import BaseModel, HttpUrl


class CrawlRequest(BaseModel):
    """Request to crawl a website."""
    url: HttpUrl


class GenerateTestsRequest(BaseModel):
    """Request to generate tests from app map."""
    app_map_file: str


class RunTestsRequest(BaseModel):
    """Request to run tests."""
    suite_id: str