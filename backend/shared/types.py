"""Shared type definitions used across all backend modules."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl


class ActionType(str, Enum):
    """Types of actions that can be performed on a page."""
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    NAVIGATE = "navigate"
    SUBMIT = "submit"
    HOVER = "hover"
    CHECK = "check"
    UNCHECK = "uncheck"


class SelectorStrategy(str, Enum):
    """Strategies for generating stable selectors."""
    TEST_ID = "test-id"
    ARIA_LABEL = "aria-label"
    TEXT = "text"
    CSS = "css"
    XPATH = "xpath"


class TestStatus(str, Enum):
    """Status of a test execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PageElement(BaseModel):
    """Represents an interactive element on a page."""
    selector: str
    selector_strategy: SelectorStrategy
    element_type: str  # button, input, link, etc.
    text: Optional[str] = None
    attributes: Dict[str, Any] = {}


class PageAction(BaseModel):
    """Represents an action that can be performed on a page."""
    action_type: ActionType
    element: PageElement
    value: Optional[str] = None  # For fill, select actions
    description: str


class PageInfo(BaseModel):
    """Information about a crawled page."""
    url: HttpUrl
    title: str
    elements: List[PageElement]
    actions: List[PageAction]
    screenshot_path: Optional[str] = None
    forms: List[Dict[str, Any]] = []


class AppMap(BaseModel):
    """Complete map of the application structure."""
    base_url: HttpUrl
    pages: List[PageInfo]
    crawl_timestamp: str
    total_pages: int


class TestStep(BaseModel):
    """A single step in a test case."""
    action: ActionType
    selector: str
    selector_strategy: SelectorStrategy
    value: Optional[str] = None
    description: str
    expected_outcome: Optional[str] = None


class TestCase(BaseModel):
    """A complete test case in JSON format."""
    test_id: str
    name: str
    description: str
    tags: List[str] = []
    preconditions: List[str] = []
    steps: List[TestStep]
    assertions: List[str] = []


class TestSuite(BaseModel):
    """Collection of test cases."""
    suite_id: str
    name: str
    base_url: HttpUrl
    test_cases: List[TestCase]


class TestResult(BaseModel):
    """Result of a single test execution."""
    test_id: str
    status: TestStatus
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    video_path: Optional[str] = None


class TestRunResult(BaseModel):
    """Complete result of a test run."""
    run_id: str
    suite_id: str
    timestamp: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    results: List[TestResult]
    junit_xml_path: Optional[str] = None
    html_report_path: Optional[str] = None