"""FastAPI main application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from backend.shared.config import get_config
from backend.shared.types import AppMap, TestSuite, TestRunResult
from backend.crawler import Crawler
from backend.generator import TestGenerator
from backend.compiler import TestCompiler
from backend.runner import TestRunner
from backend.reporter import Reporter
from .schemas import CrawlRequest, GenerateTestsRequest, RunTestsRequest

# Initialize config
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="QAsmith API",
    description="Auto-generate E2E tests for websites",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "QAsmith API"}


@app.post("/crawl", response_model=AppMap)
async def crawl_website(request: CrawlRequest):
    """Crawl a website and generate app map."""
    try:
        crawler = Crawler(request.url)
        app_map = await crawler.crawl()
        return app_map
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@app.post("/generate-tests", response_model=TestSuite)
async def generate_tests(request: GenerateTestsRequest):
    """Generate test cases from app map."""
    try:
        # Load app map
        app_map_path = Path(config.storage.app_maps_path) / request.app_map_file
        if not app_map_path.exists():
            raise HTTPException(status_code=404, detail="App map not found")

        from backend.shared.utils import load_json
        app_map_data = load_json(app_map_path)
        app_map = AppMap(**app_map_data)

        # Generate tests
        generator = TestGenerator()
        test_suite = generator.generate_tests(app_map)

        return test_suite
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@app.post("/compile-tests")
async def compile_tests(suite_id: str):
    """Compile test suite to Playwright specs."""
    try:
        # Load test suite
        suite_path = Path(config.storage.test_specs_path) / f"{suite_id}.json"
        if not suite_path.exists():
            raise HTTPException(status_code=404, detail="Test suite not found")

        from backend.shared.utils import load_json
        suite_data = load_json(suite_path)
        test_suite = TestSuite(**suite_data)

        # Compile
        compiler = TestCompiler()
        spec_path = compiler.compile(test_suite)

        return {"spec_path": str(spec_path), "suite_id": suite_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@app.post("/run-tests", response_model=TestRunResult)
async def run_tests(request: RunTestsRequest):
    """Run compiled tests."""
    try:
        # Find spec file
        spec_path = Path(config.storage.test_specs_path) / "compiled" / f"{request.suite_id}.spec.ts"
        if not spec_path.exists():
            raise HTTPException(status_code=404, detail="Test spec not found")

        # Run tests
        runner = TestRunner()
        test_run = await runner.run_tests(spec_path, request.suite_id)

        # Generate report
        reporter = Reporter()
        report_path = reporter.generate_report(test_run)

        return test_run
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test run failed: {str(e)}")


@app.get("/report/{run_id}")
async def get_report(run_id: str):
    """Serve HTML report."""
    report_path = Path(config.storage.reports_path) / run_id / "report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(report_path)


@app.get("/app-maps")
async def list_app_maps():
    """List all app maps."""
    app_maps_dir = Path(config.storage.app_maps_path)
    files = list(app_maps_dir.glob("*.json"))
    return {"app_maps": [f.name for f in files]}


@app.get("/test-suites")
async def list_test_suites():
    """List all test suites."""
    suites_dir = Path(config.storage.test_specs_path)
    files = list(suites_dir.glob("*.json"))
    return {"test_suites": [f.stem for f in files]}


@app.get("/test-runs")
async def list_test_runs():
    """List all test runs."""
    artifacts_dir = Path(config.storage.artifacts_path)
    runs = [d.name for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    return {"test_runs": runs}