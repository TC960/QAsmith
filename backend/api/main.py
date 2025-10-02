"""FastAPI main application."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from fastapi.responses import FileResponse
from pathlib import Path
from backend.shared.config import get_config, update_config
from backend.shared.graph_db import GraphDB
from backend.shared.types import TestSuite, TestRunResult
from backend.shared.utils import get_timestamp
from backend.crawler.crawler import Crawler
from backend.generator.generator import TestGenerator
from backend.compiler.compiler import TestCompiler
from backend.runner.runner import TestRunner
from backend.reporter.reporter import Reporter
from .schemas import (
    CrawlRequest, CrawlResponse, GenerateTestsRequest, RunTestsRequest,
    GraphVisualizationResponse, CrawlSummaryResponse, PageInfo,
    PathFindingRequest, PathFindingResponse, TestGenerationResponse,
    CrawlerConfigRequest, CompileTestsRequest, CompileTestsResponse, RunTestsResponse
)

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

# Include advanced testing routers
from backend.api.test_type_endpoints import router as test_types_router
app.include_router(test_types_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "QAsmith API"}


async def _send_heartbeats(websocket: WebSocket):
    """Send periodic heartbeats to keep WebSocket connection alive."""
    try:
        while True:
            await asyncio.sleep(15)  # Send heartbeat every 15 seconds
            await websocket.send_json({"type": "heartbeat", "timestamp": time.time()})
    except Exception:
        # Silently fail if connection is closed
        pass

@app.websocket("/ws/crawl/{crawl_session_id}")
async def websocket_crawl(websocket: WebSocket, crawl_session_id: str):
    """WebSocket endpoint for real-time crawl progress updates."""
    await websocket.accept()
    print(f"🔌 WEBSOCKET: Client connected for session {crawl_session_id}")
    
    try:
        # Receive crawl URL from client
        data = await websocket.receive_json()
        url = data.get("url")
        
        # Get custom crawler settings if provided
        crawler_settings = data.get("settings")
        
        if not url:
            await websocket.send_json({"type": "error", "message": "URL is required"})
            await websocket.close()
            return
        
        print(f"🚀 WEBSOCKET: Starting crawl for {url}")
        await websocket.send_json({"type": "crawl_start", "url": url})
        
        # Initialize GraphDB and embeddings
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        
        try:
            from backend.shared.embeddings import get_embedding_generator
            embedding_gen = get_embedding_generator()
            print("✅ WEBSOCKET: Embedding generator initialized")
        except Exception as e:
            print(f"⚠️  WEBSOCKET: Embeddings disabled: {e}")
            embedding_gen = None
        
        # Create crawler with progress callback
        crawler = Crawler(graph_db, embedding_gen)
        
        # Apply custom settings if provided
        if crawler_settings:
            print(f"⚙️ WEBSOCKET: Using custom crawler settings: {crawler_settings}")
            # Temporarily update config for this crawl
            config.crawler.max_depth = crawler_settings.get("max_depth", config.crawler.max_depth)
            config.crawler.max_pages = crawler_settings.get("max_pages", config.crawler.max_pages)
            config.crawler.timeout = crawler_settings.get("timeout", config.crawler.timeout)
            config.crawler.screenshot = crawler_settings.get("screenshot", config.crawler.screenshot)
            config.crawler.page_delay_ms = crawler_settings.get("page_delay_ms", getattr(config.crawler, "page_delay_ms", 300))
            config.crawler.skip_embeddings = crawler_settings.get("skip_embeddings", getattr(config.crawler, "skip_embeddings", True))
        
        # Set progress callback to send updates via WebSocket
        async def progress_callback(update: dict):
            await websocket.send_json(update)
            print(f"📡 WEBSOCKET: Sent update: {update.get('type')}")
        
        crawler.progress_callback = progress_callback
        
        # Start crawling with timeout handling
        try:
            # Send periodic heartbeat to keep connection alive
            heartbeat_task = asyncio.create_task(_send_heartbeats(websocket))
            
            # Start crawling with timeout handling
            crawl_id = await asyncio.wait_for(
                crawler.crawl(url),
                timeout=300  # 5 minutes timeout (much higher than browser WebSocket timeout)
            )
            
            # Cancel heartbeat task
            heartbeat_task.cancel()
            
            # Get final summary
            summary = graph_db.get_crawl_summary(crawl_id)
            
            # Send completion message
            await websocket.send_json({
                "type": "crawl_complete",
                "crawl_id": crawl_id,
                "summary": summary
            })
        except asyncio.TimeoutError:
            await websocket.send_json({
                "type": "error",
                "message": "Crawl operation timed out after 5 minutes. Try with a smaller depth/max_pages."
            })
            print(f"⏱️ WEBSOCKET: Crawl timed out for {url}")
            return
        
        print(f"✅ WEBSOCKET: Crawl {crawl_id} completed")
        graph_db.close()
        
    except WebSocketDisconnect:
        print(f"🔌 WEBSOCKET: Client disconnected for session {crawl_session_id}")
    except Exception as e:
        print(f"❌ WEBSOCKET: Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest):
    """Crawl a website and store in Neo4j graph (synchronous endpoint)."""
    print(f"🚀 API: Received crawl request for {request.url}")
    
    try:
        # Initialize GraphDB connection
        print("📊 API: Connecting to Neo4j...")
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        print("✅ API: Neo4j connection established")
        
        # Initialize embeddings
        try:
            from backend.shared.embeddings import get_embedding_generator
            embedding_gen = get_embedding_generator()
            print("✅ API: Embedding generator initialized")
        except Exception as e:
            print(f"⚠️  API: Embeddings disabled: {e}")
            embedding_gen = None
        
        # Create crawler and start crawling
        print("🕷️  API: Initializing crawler...")
        crawler = Crawler(graph_db, embedding_gen)
        print("🚀 API: Starting crawl...")
        crawl_id = await crawler.crawl(str(request.url))
        print(f"✅ API: Crawl completed with ID: {crawl_id}")
        
        # Get crawl summary
        print("📊 API: Getting crawl summary...")
        summary = graph_db.get_crawl_summary(crawl_id)
        print(f"📊 API: Summary: {summary}")
        
        # Close GraphDB connection
        graph_db.close()
        print("🔒 API: Neo4j connection closed")
        
        response = CrawlResponse(
            crawl_id=crawl_id,
            base_url=str(request.url),
            status="completed",
            total_pages=summary.get("page_count", 0),
            total_elements=summary.get("element_count", 0),
            total_links=summary.get("link_count", 0)
        )
        print(f"🎉 API: Returning response: {response}")
        return response
        
    except Exception as e:
        print(f"❌ API: Crawl failed with error: {e}")
        import traceback
        print(f"🔍 API: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@app.get("/crawls")
async def list_crawls():
    """List all crawls in the database."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        crawls = graph_db.list_all_crawls()
        graph_db.close()
        return crawls
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list crawls: {str(e)}")


@app.get("/crawl/{crawl_id}/summary", response_model=CrawlSummaryResponse)
async def get_crawl_summary(crawl_id: str):
    """Get summary statistics for a crawl."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        summary = graph_db.get_crawl_summary(crawl_id)
        graph_db.close()
        
        if not summary:
            raise HTTPException(status_code=404, detail=f"Crawl {crawl_id} not found")
        
        return CrawlSummaryResponse(
            crawl_id=crawl_id,
            base_url=summary.get("base_url", ""),
            domain=summary.get("domain", ""),
            status=summary.get("status", "unknown"),
            page_count=summary.get("page_count", 0),
            element_count=summary.get("element_count", 0),
            link_count=summary.get("link_count", 0)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawl summary: {str(e)}")


@app.get("/crawl/{crawl_id}/pages")
async def get_crawl_pages(crawl_id: str):
    """Get all pages for a crawl."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        pages = graph_db.get_all_pages(crawl_id)
        graph_db.close()
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawl pages: {str(e)}")


@app.get("/graph/{crawl_id}/visualize", response_model=GraphVisualizationResponse)
async def visualize_graph(crawl_id: str):
    """Export graph data for visualization."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        graph_data = graph_db.get_graph_visualization_data(crawl_id)
        graph_db.close()
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export graph: {str(e)}")


@app.post("/graph/find-path", response_model=PathFindingResponse)
async def find_path(request: PathFindingRequest):
    """Find the shortest path between two pages."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        path = graph_db.find_shortest_path(request.start_url, request.end_url)
        graph_db.close()
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find path: {str(e)}")


@app.post("/generate-tests", response_model=TestGenerationResponse)
async def generate_tests(request: GenerateTestsRequest):
    """Generate tests for selected pages using AI."""
    print(f"🚀 API: Received test generation request for {len(request.page_urls)} pages")

    try:
        # Initialize GraphDB connection
        print("📊 API: Connecting to Neo4j...")
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        print("✅ API: Neo4j connection established")

        # Get page IDs for selected URLs (with URL normalization)
        print(f"🔍 API: Fetching page data for selected URLs...")
        page_ids = []
        for url in request.page_urls:
            # Normalize URL by removing trailing slash
            normalized_url = url.rstrip('/')

            # Query to get page_id from URL (try both with and without trailing slash)
            with graph_db.driver.session() as session:
                result = session.run("""
                    MATCH (p:Page {crawl_id: $crawl_id})
                    WHERE p.url = $url OR p.url = $url_with_slash OR p.url = $url_without_slash
                    RETURN p.page_id as page_id
                    LIMIT 1
                """, crawl_id=request.crawl_id, url=url,
                     url_with_slash=normalized_url + '/',
                     url_without_slash=normalized_url)
                record = result.single()
                if record:
                    page_ids.append(record["page_id"])
                    print(f"✅ API: Found page_id for {url}")
                else:
                    print(f"⚠️ API: No page found for {url}")

        if not page_ids:
            raise HTTPException(status_code=404, detail="No pages found for selected URLs")

        print(f"✅ API: Found {len(page_ids)} pages")

        # Export selected pages to AppMap
        print("🗺️  API: Exporting pages to AppMap...")
        app_map = graph_db.export_path_to_appmap(request.crawl_id, page_ids)
        print(f"✅ API: Exported AppMap with {len(app_map.pages)} pages")

        # Generate tests using TestGenerator (uses proper prompts and selector strategies)
        print("🤖 API: Generating tests with TestGenerator...")
        generator = TestGenerator()
        test_suite = generator.generate_tests(app_map)
        print(f"✅ API: Generated {len(test_suite.test_cases)} test cases")

        # Convert TestSuite to the expected format
        tests = [
            {
                "test_id": tc.test_id,
                "name": tc.name,
                "description": tc.description,
                "page_url": str(app_map.pages[0].url) if app_map.pages else "",
                "steps": [
                    {
                        "action": step.action.value,
                        "selector": step.selector,
                        "selector_strategy": step.selector_strategy.value if step.selector_strategy else None,
                        "value": step.value,
                        "description": step.description,
                        "url": step.url,
                        "assertion": step.assertion
                    }
                    for step in tc.steps
                ]
            }
            for tc in test_suite.test_cases
        ]

        # Save tests using consistent format
        import json
        from pathlib import Path
        suite_id = test_suite.suite_id
        test_specs_dir = Path(config.storage.test_specs_path)
        test_specs_dir.mkdir(parents=True, exist_ok=True)

        suite_file = test_specs_dir / f"{suite_id}.json"
        with open(suite_file, 'w') as f:
            json.dump({
                "suite_id": suite_id,
                "crawl_id": request.crawl_id,
                "test_count": len(tests),
                "tests": tests
            }, f, indent=2)
        print(f"💾 API: Saved test suite to {suite_file}")

        # Close GraphDB connection
        graph_db.close()
        print("🔒 API: Neo4j connection closed")

        api_response = TestGenerationResponse(
            crawl_id=request.crawl_id,
            test_suite_id=suite_id,
            test_count=len(tests),
            tests=tests
        )
        print(f"🎉 API: Returning response with {len(tests)} tests")
        return api_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Test generation failed with error: {e}")
        import traceback
        print(f"🔍 API: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@app.post("/compile-tests", response_model=CompileTestsResponse)
async def compile_tests(request: CompileTestsRequest):
    """Compile test suite JSON to Playwright TypeScript spec."""
    print(f"🚀 API: Received compile request for suite {request.suite_id}")

    try:
        # Load test suite from disk
        import json
        from pathlib import Path
        from backend.shared.types import TestSuite, TestCase, TestStep

        suite_file = Path(config.storage.test_specs_path) / f"{request.suite_id}.json"
        if not suite_file.exists():
            raise HTTPException(status_code=404, detail=f"Test suite {request.suite_id} not found")

        with open(suite_file, 'r') as f:
            suite_data = json.load(f)

        # Convert to TestSuite object
        test_cases = []
        for i, test in enumerate(suite_data['tests']):
            steps = []
            for step in test['steps']:
                steps.append(TestStep(
                    action=step['action'],
                    selector=step.get('selector', ''),
                    value=step.get('value'),
                    assertion=step.get('assertion'),
                    description=step.get('description', ''),
                    url=step.get('url')
                ))
            test_cases.append(TestCase(
                test_id=f"{request.suite_id}_test_{i}",
                name=test['name'],
                description=test['description'],
                page_url=test.get('page_url', ''),
                steps=steps
            ))

        # Extract base_url from first test's page_url if not in suite_data
        base_url = suite_data.get('base_url', '')
        if not base_url and suite_data.get('tests') and len(suite_data['tests']) > 0:
            from urllib.parse import urlparse
            first_url = suite_data['tests'][0].get('page_url', '')
            if first_url:
                parsed = urlparse(first_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"

        test_suite = TestSuite(
            suite_id=request.suite_id,
            name=f"Test Suite {request.suite_id}",
            base_url=base_url or "https://example.com",  # Fallback
            test_cases=test_cases
        )

        # Compile to Playwright spec
        print("🔧 API: Compiling to Playwright TypeScript...")
        from backend.compiler.compiler import TestCompiler
        compiler = TestCompiler()
        spec_path = compiler.compile(test_suite)
        print(f"✅ API: Compiled to {spec_path}")

        return CompileTestsResponse(
            suite_id=request.suite_id,
            spec_file_path=str(spec_path),
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Compilation failed with error: {e}")
        import traceback
        print(f"🔍 API: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@app.post("/run-tests", response_model=RunTestsResponse)
async def run_tests(request: RunTestsRequest):
    """Run compiled Playwright tests with visible browser and generate AI summary."""
    print(f"🚀 API: Received test run request for suite {request.suite_id}")

    try:
        from pathlib import Path
        import subprocess
        import uuid
        import json
        import re

        # Load test suite for AI context
        suite_file = Path(config.storage.test_specs_path) / f"{request.suite_id}.json"
        if not suite_file.exists():
            raise HTTPException(status_code=404, detail=f"Test suite {request.suite_id} not found")

        with open(suite_file, 'r') as f:
            suite_data = json.load(f)

        # Check if spec file exists
        spec_file = Path(config.storage.test_specs_path) / "compiled" / f"{request.suite_id}.spec.ts"
        if not spec_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Compiled spec not found. Please compile tests first using /compile-tests"
            )

        run_id = f"run_{request.suite_id}_{uuid.uuid4().hex[:8]}"

        # Run Playwright tests with headed browser (visible) and JSON reporter
        print("🏃 API: Running Playwright tests with visible browser...")
        cmd = [
            "npx",
            "playwright",
            "test",
            str(spec_file),
            "--headed",  # Show the browser
            "--reporter=json",  # Get structured results
        ]

        # Run from backend directory where Playwright is installed
        backend_dir = Path(__file__).parent.parent
        result = subprocess.run(
            cmd,
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
        )

        print(f"📊 API: Playwright output:\n{result.stdout}")
        if result.stderr:
            print(f"⚠️ API: Playwright stderr:\n{result.stderr}")

        # Parse JSON results
        try:
            test_results_json = json.loads(result.stdout)
            
            # Navigate to the actual test specs (they're nested in suites[0].suites[0].specs)
            outer_suites = test_results_json.get('suites', [])
            if outer_suites and len(outer_suites) > 0:
                inner_suites = outer_suites[0].get('suites', [])
                if inner_suites and len(inner_suites) > 0:
                    specs = inner_suites[0].get('specs', [])
                else:
                    # Fallback: try direct specs if no nested suites
                    specs = outer_suites[0].get('specs', [])
            else:
                specs = []
            
            total_tests = len(specs)
            passed = sum(1 for spec in specs if spec.get('ok', False))
            failed = total_tests - passed

            # Extract individual test results
            test_results = []
            for spec in specs:
                test_results.append({
                    'name': spec.get('title', 'Unknown test'),
                    'status': 'passed' if spec.get('ok', False) else 'failed',
                    'error': spec.get('tests', [{}])[0].get('results', [{}])[0].get('error', {}).get('message') if not spec.get('ok', False) else None
                })
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Fallback to text parsing
            print(f"⚠️ API: Failed to parse JSON output: {e}, using text parsing")
            total_tests = result.stdout.count(' expected')
            passed = result.stdout.count(' passed')
            failed = result.stdout.count(' failed')
            test_results = []

        print(f"✅ API: Test run complete - {passed}/{total_tests} passed")

        # Generate AI summary using Anthropic with enhanced prompt
        print("🤖 API: Generating comprehensive AI test analysis...")
        ai_summary = None
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.llm.api_key)

            # Enhanced AI prompt for detailed, professional analysis
            summary_prompt = f"""You are a senior QA engineer analyzing E2E test results for a production web application. Provide a comprehensive, data-driven test execution report.

**Test Suite Configuration:**
Suite ID: {request.suite_id}
Total Test Cases: {len(suite_data.get('tests', []))}

**Test Specifications:**
{json.dumps(suite_data.get('tests', []), indent=2)}

**Execution Results:**
- Total Tests Executed: {total_tests}
- Passed: {passed} ({(passed/total_tests*100) if total_tests > 0 else 0:.1f}%)
- Failed: {failed} ({(failed/total_tests*100) if total_tests > 0 else 0:.1f}%)
- Exit Code: {result.returncode}

**Individual Test Outcomes:**
{json.dumps(test_results, indent=2)}

**Raw Playwright Output:**
{result.stdout[:1000]}

**TASK: Generate a professional QA test report with the following structure:**

1. **Executive Summary** (2-3 sentences)
   - Overall test execution status
   - Key findings and critical issues
   - Recommendation (ship/hold/re-test)

2. **Functionality Coverage Analysis** (bullet points)
   - List each tested user journey/feature
   - Specify expected vs actual behavior
   - Identify any gaps in test coverage

3. **Root Cause Analysis** (if failures exist)
   - Technical reasons for each failure
   - Whether failures are due to: test logic errors, application bugs, environmental issues, or data problems
   - Impact severity (critical/high/medium/low)

4. **Actionable Recommendations** (numbered list)
   - Specific steps to fix failures
   - Suggestions for test improvement
   - Areas requiring additional test coverage

**Style Guidelines:**
- Use precise, technical language appropriate for engineers
- Avoid unnecessary pleasantries or filler text
- Focus on facts, data, and logical conclusions
- Be direct and actionable
- Maximum length: 400 words

Begin your analysis now:"""

            response = client.messages.create(
                model=config.llm.model,
                max_tokens=1500,
                temperature=0.2,  # Lower temperature for more consistent, factual output
                messages=[{
                    "role": "user",
                    "content": summary_prompt
                }]
            )

            ai_summary = response.content[0].text
            print(f"✅ API: Generated AI analysis ({len(ai_summary)} chars)")

        except Exception as e:
            print(f"⚠️ API: Failed to generate AI summary: {e}")
            ai_summary = f"Test run completed with {passed}/{total_tests} tests passing. AI analysis unavailable."

        # Save comprehensive test report to test_run_output
        report_dir = Path("backend/test_run_output/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        report_data = {
            "run_id": run_id,
            "suite_id": request.suite_id,
            "timestamp": get_timestamp(),
            "execution_summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total_tests*100) if total_tests > 0 else 0:.1f}%",
                "exit_code": result.returncode
            },
            "test_specifications": suite_data.get('tests', []),
            "individual_results": test_results,
            "ai_analysis": ai_summary,
            "playwright_output": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "raw_json": result.stdout if '{' in result.stdout else None
            }
        }

        report_file = report_dir / f"{run_id}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"💾 API: Saved detailed report to {report_file}")

        return RunTestsResponse(
            suite_id=request.suite_id,
            run_id=run_id,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            report_path=str(report_file),
            ai_summary=ai_summary,
            test_results=test_results if test_results else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Test run failed with error: {e}")
        import traceback
        print(f"🔍 API: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test run failed: {str(e)}")


@app.get("/config/crawler")
async def get_crawler_config():
    """Get current crawler configuration."""
    try:
        return {
            "max_depth": config.crawler.max_depth,
            "max_pages": config.crawler.max_pages,
            "timeout": config.crawler.timeout,
            "screenshot": config.crawler.screenshot,
            "page_delay_ms": getattr(config.crawler, "page_delay_ms", 300),
            "skip_embeddings": getattr(config.crawler, "skip_embeddings", True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawler config: {str(e)}")


@app.post("/config/crawler")
async def update_crawler_config(request: CrawlerConfigRequest):
    """Update crawler configuration."""
    try:
        # Update in-memory config
        config.crawler.max_depth = request.max_depth
        config.crawler.max_pages = request.max_pages
        config.crawler.timeout = request.timeout
        config.crawler.screenshot = request.screenshot
        
        # Add new fields
        setattr(config.crawler, "page_delay_ms", request.page_delay_ms)
        setattr(config.crawler, "skip_embeddings", request.skip_embeddings)
        
        # Update config file
        update_config({
            "crawler": {
                "max_depth": request.max_depth,
                "max_pages": request.max_pages,
                "timeout": request.timeout,
                "screenshot": request.screenshot,
                "page_delay_ms": request.page_delay_ms,
                "skip_embeddings": request.skip_embeddings
            }
        })
        
        return {"status": "success", "message": "Crawler configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update crawler config: {str(e)}")