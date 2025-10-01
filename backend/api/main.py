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
from backend.crawler.crawler import Crawler
from backend.generator.generator import TestGenerator
from backend.compiler.compiler import TestCompiler
from backend.runner.runner import TestRunner
from backend.reporter.reporter import Reporter
from .schemas import (
    CrawlRequest, CrawlResponse, GenerateTestsRequest, RunTestsRequest,
    GraphVisualizationResponse, CrawlSummaryResponse, PageInfo,
    PathFindingRequest, PathFindingResponse, TestGenerationResponse,
    CrawlerConfigRequest
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
        pages = graph_db.get_crawl_pages(crawl_id)
        graph_db.close()
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get crawl pages: {str(e)}")


@app.get("/graph/{crawl_id}/visualize", response_model=GraphVisualizationResponse)
async def visualize_graph(crawl_id: str):
    """Export graph data for visualization."""
    try:
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        graph_data = graph_db.export_graph_for_visualization(crawl_id)
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
    """Generate tests for a path between two pages."""
    print(f"🚀 API: Received test generation request for path from {request.start_url} to {request.end_url}")
    
    try:
        # Initialize GraphDB connection
        print("📊 API: Connecting to Neo4j...")
        graph_db = GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)
        print("✅ API: Neo4j connection established")
        
        # Find shortest path between pages
        print(f"🔍 API: Finding path from {request.start_url} to {request.end_url}...")
        path = graph_db.find_shortest_path(request.start_url, request.end_url)
        
        if not path or not path.get("path_found"):
            raise HTTPException(status_code=404, detail=f"No path found between {request.start_url} and {request.end_url}")
        
        print(f"✅ API: Found path with {path.get('path_length')} hops")
        
        # Export path to AppMap
        print("🗺️  API: Exporting path to AppMap...")
        app_map = graph_db.export_path_to_appmap(path)
        print(f"✅ API: Exported AppMap with {len(app_map.pages)} pages")
        
        # Generate tests using TestGenerator
        print("🧠 API: Generating tests...")
        generator = TestGenerator(config.llm.api_key)
        test_suite = generator.generate(app_map)
        print(f"✅ API: Generated {len(test_suite.tests)} tests")
        
        # Close GraphDB connection
        graph_db.close()
        print("🔒 API: Neo4j connection closed")
        
        response = TestGenerationResponse(
            crawl_id=request.crawl_id,
            test_suite_id=test_suite.id,
            test_count=len(test_suite.tests),
            tests=test_suite.tests
        )
        print(f"🎉 API: Returning response with {len(test_suite.tests)} tests")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API: Test generation failed with error: {e}")
        import traceback
        print(f"🔍 API: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@app.post("/run-tests")
async def run_tests(request: RunTestsRequest):
    """Run tests for a test suite."""
    print(f"🚀 API: Received test run request for test suite {request.test_suite_id}")
    
    try:
        # Compile tests
        print("🔧 API: Compiling tests...")
        compiler = TestCompiler()
        compiled_tests = compiler.compile(request.tests)
        print(f"✅ API: Compiled {len(compiled_tests)} tests")
        
        # Run tests
        print("🏃 API: Running tests...")
        runner = TestRunner(config.runner.browser, config.runner.headless)
        test_results = await runner.run(compiled_tests)
        print(f"✅ API: Ran {len(test_results)} tests")
        
        # Generate report
        print("📊 API: Generating report...")
        reporter = Reporter()
        report = reporter.generate(test_results)
        print(f"✅ API: Generated report")
        
        return {
            "test_suite_id": request.test_suite_id,
            "test_run_id": report.id,
            "results": test_results
        }
        
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