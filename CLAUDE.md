# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QAsmith is an AI-powered E2E test generation tool that automatically creates Playwright tests for websites. It's a monorepo with a Python backend and React frontend, using **Neo4j graph database** for scalable website crawl storage.

**Core Pipeline:**
1. **Crawler** → BFS crawl builds Neo4j graph (pages, elements, actions, links)
2. **Generator** → Finds path in graph, exports to JSON, Claude LLM converts to `TestSuite`
3. **Compiler** → Converts `TestSuite` to Playwright TypeScript specs
4. **Runner** → Executes specs, collects artifacts (JUnit XML, traces, videos)
5. **Reporter** → Generates HTML reports with AI failure summaries

**Key Architectural Decision:** Using Neo4j instead of JSON files for app maps allows infinite crawl depth, shortest-path algorithms for test generation, and visual graph exploration in the frontend.

## Setup & Configuration

**First-time setup:**
```bash
# Backend (Python 3.12 required, 3.13 has compatibility issues)
cd backend
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install

# Frontend
cd frontend
npm install

# Neo4j (choose one method)
# Option A: Docker (recommended for development)
docker run --name neo4j -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/testpassword neo4j:latest

# Option B: Neo4j Aura (free cloud tier)
# Sign up at https://neo4j.com/cloud/aura/

# Config
cp config/config.example.json config/config.json
# Edit config/config.json with:
#   - Anthropic API key
#   - Neo4j connection details (uri, user, password)
```

**Running the app:**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn api.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:3000`.

## Architecture & Key Concepts

### Data Flow & Type System

All data models are defined in `backend/shared/types.py` using Pydantic. The pipeline follows this flow:

```
URL → Neo4j Graph → Path Selection → AppMap (JSON) → TestSuite → .spec.ts → TestRunResult → HTML Report
```

**Critical types:**
- `AppMap`: Exported subgraph from Neo4j (specific path for test generation)
- `TestSuite`: Collection of JSON `TestCase` objects
- `TestCase`: Contains `TestStep` objects with actions and selectors
- `TestRunResult`: Execution results with `TestResult` for each test

### Neo4j Graph Database Layer

`backend/shared/graph_db.py` provides the `GraphDB` class for all Neo4j operations:

**Graph Structure:**
```cypher
(:Crawl)-[:HAS_PAGE]->(:Page)-[:LINKS_TO]->(:Page)
(:Page)-[:HAS_ELEMENT]->(:Element)-[:CAN_PERFORM]->(:Action)
```

**Key Methods:**
- `create_crawl(base_url, domain) -> crawl_id` - Initialize new crawl
- `add_page(crawl_id, url, title, depth)` - Add page node
- `add_element(page_id, selector, ...)` - Add interactive element
- `link_pages(from_page_id, to_page_id)` - Create navigation relationship
- `find_shortest_path(crawl_id, start_url, end_url)` - Neo4j shortestPath algorithm
- `export_path_to_appmap(crawl_id, page_ids)` - Convert graph path to AppMap JSON for LLM
- `get_graph_visualization_data(crawl_id)` - Export nodes/edges for frontend display

**Why this matters:** The generator doesn't receive the entire crawl—only the relevant path between start and end pages. This keeps LLM context focused and tokens low.

### Module Boundaries

Each backend module is **strictly isolated**:

- **crawler/**: Playwright automation, writes to Neo4j graph via `GraphDB`
- **generator/**: Queries Neo4j for path, exports to JSON, sends to Claude LLM
- **compiler/**: Template-based code generation using `templates.py`
- **runner/**: Playwright subprocess execution, artifact collection
- **reporter/**: HTML generation + LLM summarization of failures
- **api/**: Orchestrates modules, handles REST endpoints
- **shared/graph_db.py**: Neo4j abstraction layer used by crawler, generator, API

**Important:** Modules communicate through Pydantic types and Neo4j graph. The `GraphDB` class is the single point of interaction with Neo4j.

### Configuration System

`backend/shared/config.py` provides centralized configuration:
- Uses `get_config()` singleton pattern
- Loads from `config/config.json`
- Automatically creates storage directories on startup
- Storage paths are configurable for cloud deployment readiness
- Includes `Neo4jConfig` class with uri, user, password fields

### Selector Strategy System

The crawler uses `SelectorStrategy` enum (test-id → aria-label → text → CSS) to generate **stable selectors**. The compiler translates these to Playwright locators:

```python
SelectorStrategy.TEST_ID → page.getByTestId('...')
SelectorStrategy.ARIA_LABEL → page.getByLabel('...')
SelectorStrategy.TEXT → page.getByText('...')
```

This is critical for test stability.

## API Endpoints

FastAPI endpoints in `backend/api/main.py` (schemas defined in `backend/api/schemas.py`):

**Crawl Management:**
- `POST /crawl` - Start BFS crawl, stores in Neo4j, returns `CrawlResponse` with `crawl_id`
- `GET /crawls` - List all crawls with summaries
- `GET /crawl/{crawl_id}/summary` - Get crawl statistics (page_count, element_count, link_count)
- `GET /crawl/{crawl_id}/pages` - List all pages in a crawl

**Graph Operations:**
- `GET /graph/{crawl_id}/visualize` - Export graph data for frontend visualization (D3.js format)
- `POST /graph/find-path` - Find shortest path between two pages (uses Neo4j shortestPath)

**Test Generation:**
- `POST /generate-tests` - Takes `crawl_id`, `start_url`, `end_url`, generates tests for that path
- `POST /compile-tests` - Compile TestSuite to Playwright .spec.ts
- `GET /test-suites` - List all test suites

**Test Execution:**
- `POST /run-tests` - Execute tests, returns `TestRunResult`
- `GET /test-runs` - List all test runs
- `GET /report/{run_id}` - Serve HTML report

## Frontend Architecture

React app uses:
- **React Router** for navigation
- **TanStack Query** for API calls and caching
- **Vite** as build tool
- Proxy configured: `/api/*` → `http://localhost:8000`

Pages map to pipeline stages:
- `/` - Home page with feature overview
- `/crawl` - Initiate website crawling, view crawl progress
- `/tests` - View graph visualization, select start/end pages, generate tests
- `/results` - View test execution results & reports

## Working with LLM Integration

**Generator** (`backend/generator/generator.py`):
- Receives path from Neo4j (via `GraphDB.find_shortest_path()`)
- Exports path to `AppMap` JSON (via `GraphDB.export_path_to_appmap()`)
- Sends focused JSON to Claude (only relevant pages, not entire site)
- System prompt defines test generation rules
- Returns structured JSON parsed into `TestCase` objects

**Reporter** (`backend/reporter/reporter.py`):
- Generates AI summaries for failed tests only
- Uses lower temperature (0.3) for consistency
- Embeds summaries in HTML report

**When modifying prompts:**
- Edit `backend/generator/prompts.py`
- Test with various website structures
- Ensure JSON output is parseable
- Remember: LLM only sees the exported path, not the entire graph

## Storage Layout

**Neo4j Database:** Stores all crawl data (pages, elements, actions, relationships)

**File System:** (paths configurable in `config/config.json`)
```
backend/
  test_specs/         # {suite_id}.json (generated test suites)
    compiled/         # {suite_id}.spec.ts (compiled Playwright specs)
  artifacts/          # Per-run artifacts
    {run_id}/
      results.json
      results.xml
      html-report/
      traces/
      screenshots/
      videos/
  reports/            # AI-enhanced HTML reports
    {run_id}/
      report.html
```

**Note:** `app_maps/` directory is no longer used—crawl data lives in Neo4j instead of JSON files.

## Important Implementation Notes

1. **Import paths**: Backend uses absolute imports like `from backend.shared.types import AppMap`. Run commands from repo root.

2. **Neo4j connection management**:
   - Initialize `GraphDB` using config: `GraphDB(config.neo4j.uri, config.neo4j.user, config.neo4j.password)`
   - Always call `graph_db.close()` when done (use context managers in production)
   - Constraints and indexes are created automatically on first connection

3. **Async patterns**: Crawler and Runner use `async/await`. API endpoints must be `async def`.

4. **Error handling**: Each API endpoint wraps operations in try/except and raises `HTTPException` with proper status codes.

5. **BFS crawl**:
   - Crawler maintains `visited_urls` set and depth tracking to respect `max_depth` and `max_pages` config
   - As each page is discovered, immediately add to Neo4j graph
   - Create `LINKS_TO` relationships between pages for path finding

6. **Playwright subprocess**: Runner executes Playwright via subprocess, not as a library, to isolate test execution environment.

7. **File naming**: Use `sanitize_filename()` from `backend/shared/utils.py` for any user-provided data in filenames.

8. **Python version**: Use Python 3.12 (3.13 has dependency compatibility issues with greenlet/pydantic-core)

## Development Commands

```bash
# Run backend API server
cd backend && uvicorn api.main:app --reload

# Run frontend dev server
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Type check frontend
cd frontend && npx tsc --noEmit

# Install Playwright browsers
cd backend && playwright install
```

## Testing the Pipeline

Manual end-to-end test:
```bash
# 1. Ensure Neo4j is running
docker ps | grep neo4j

# 2. Start backend
cd backend && source venv/bin/activate && uvicorn api.main:app --reload

# 3. Crawl a site
curl -X POST http://localhost:8000/crawl -H "Content-Type: application/json" -d '{"url":"https://example.com"}'
# Returns: {"crawl_id": "abc-123", ...}

# 4. View graph visualization data
curl http://localhost:8000/graph/abc-123/visualize

# 5. Find path between pages
curl -X POST http://localhost:8000/graph/find-path -H "Content-Type: application/json" \
  -d '{"crawl_id":"abc-123","start_url":"https://example.com/","end_url":"https://example.com/contact"}'

# 6. Generate tests for a specific path
curl -X POST http://localhost:8000/generate-tests -H "Content-Type: application/json" \
  -d '{"crawl_id":"abc-123","start_url":"https://example.com/","end_url":"https://example.com/contact"}'
# Returns: {"suite_id": "suite-456", ...}

# 7. Compile and run tests using returned suite_id
curl -X POST http://localhost:8000/compile-tests -H "Content-Type: application/json" -d '{"suite_id":"suite-456"}'
curl -X POST http://localhost:8000/run-tests -H "Content-Type: application/json" -d '{"suite_id":"suite-456"}'
```

## Current Implementation Status

**✅ Completed:**
- Project structure and dependencies
- Neo4j graph database abstraction layer (`backend/shared/graph_db.py`)
- Configuration system with Neo4j support
- API schemas for graph-based workflow
- Frontend scaffolding (HomePage, CrawlPage shells)

**⏳ In Progress/Pending:**
- Crawler implementation (needs to write to Neo4j)
- API endpoint wiring (skeleton exists, needs implementation)
- Generator LLM integration
- Compiler template system
- Runner subprocess execution
- Reporter HTML generation
- Frontend graph visualization component (TestsPage)
- Frontend results display (ResultsPage)

**See PROJECT_STATUS.md for detailed implementation checklist.**