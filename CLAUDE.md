# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QAsmith is an AI-powered E2E test generation tool that automatically creates Playwright tests for websites. It's a monorepo with a Python backend and React frontend.

**Core Pipeline:**
1. **Crawler** → BFS crawl creates `AppMap` (pages, forms, actions, screenshots)
2. **Generator** → Claude LLM converts `AppMap` to `TestSuite` (JSON test cases)
3. **Compiler** → Converts `TestSuite` to Playwright TypeScript specs
4. **Runner** → Executes specs, collects artifacts (JUnit XML, traces, videos)
5. **Reporter** → Generates HTML reports with AI failure summaries

## Setup & Configuration

**First-time setup:**
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install

# Frontend
cd frontend
npm install

# Config
cp config/config.example.json config/config.json
# Edit config/config.json with your Anthropic API key
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

All data models are defined in `backend/shared/types.py` using Pydantic. The entire pipeline follows this type flow:

```
URL → AppMap → TestSuite → Playwright .spec.ts → TestRunResult → HTML Report
```

**Critical types:**
- `AppMap`: Complete website structure from crawler
- `TestSuite`: Collection of JSON `TestCase` objects
- `TestCase`: Contains `TestStep` objects with actions and selectors
- `TestRunResult`: Execution results with `TestResult` for each test

### Module Boundaries

Each backend module is **strictly isolated**:

- **crawler/**: Playwright automation, NO business logic about test generation
- **generator/**: LLM calls only, uses `prompts.py` for prompt engineering
- **compiler/**: Template-based code generation using `templates.py`
- **runner/**: Playwright subprocess execution, artifact collection
- **reporter/**: HTML generation + LLM summarization of failures
- **api/**: Orchestrates modules, handles REST endpoints

**Important:** Modules communicate ONLY through Pydantic types. No direct cross-module function calls except through `api/main.py`.

### Configuration System

`backend/shared/config.py` provides centralized configuration:
- Uses `get_config()` singleton pattern
- Loads from `config/config.json`
- Automatically creates storage directories on startup
- Storage paths are configurable for cloud deployment readiness

### Selector Strategy System

The crawler uses `SelectorStrategy` enum (test-id → aria-label → text → CSS) to generate **stable selectors**. The compiler translates these to Playwright locators:

```python
SelectorStrategy.TEST_ID → page.getByTestId('...')
SelectorStrategy.ARIA_LABEL → page.getByLabel('...')
SelectorStrategy.TEXT → page.getByText('...')
```

This is critical for test stability.

## API Endpoints

FastAPI endpoints in `backend/api/main.py`:

- `POST /crawl` - Start BFS crawl, returns `AppMap`
- `POST /generate-tests` - Generate tests from app map file
- `POST /compile-tests` - Compile suite to Playwright spec
- `POST /run-tests` - Execute tests, returns `TestRunResult`
- `GET /report/{run_id}` - Serve HTML report
- `GET /app-maps` - List all crawled app maps
- `GET /test-suites` - List all test suites
- `GET /test-runs` - List all test runs

## Frontend Architecture

React app uses:
- **React Router** for navigation
- **TanStack Query** for API calls and caching
- **Vite** as build tool
- Proxy configured: `/api/*` → `http://localhost:8000`

Pages map to pipeline stages:
- `/crawl` - Initiate website crawling
- `/tests` - Manage test generation & compilation
- `/results` - View test results & reports

## Working with LLM Integration

**Generator** (`backend/generator/generator.py`):
- Uses Anthropic SDK with Claude model
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

## Storage Layout

All paths configurable in `config/config.json`:

```
backend/
  app_maps/           # {domain}_app_map.json
  test_specs/         # {suite_id}.json
    compiled/         # {suite_id}.spec.ts
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

## Important Implementation Notes

1. **Import paths**: Backend uses absolute imports like `from backend.shared.types import AppMap`. Run from repo root.

2. **Async patterns**: Crawler and Runner use `async/await`. API endpoints must be `async def`.

3. **Error handling**: Each API endpoint wraps operations in try/except and raises `HTTPException` with proper status codes.

4. **BFS crawl**: Crawler maintains `visited_urls` set and depth tracking to respect `max_depth` and `max_pages` config.

5. **Playwright subprocess**: Runner executes Playwright via subprocess, not as a library, to isolate test execution environment.

6. **File naming**: Use `sanitize_filename()` from `backend/shared/utils.py` for any user-provided data in filenames.

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
# 1. Start backend
cd backend && uvicorn api.main:app --reload

# 2. Crawl a site (use API or frontend)
curl -X POST http://localhost:8000/crawl -H "Content-Type: application/json" -d '{"url":"https://example.com"}'

# 3. Check app maps
curl http://localhost:8000/app-maps

# 4. Generate tests
curl -X POST http://localhost:8000/generate-tests -H "Content-Type: application/json" -d '{"app_map_file":"example.com_app_map.json"}'

# 5. Compile and run tests using returned suite_id
```