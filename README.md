# QAsmith

Auto-generate end-to-end tests for any website using AI.

## Architecture

QAsmith is a monorepo with the following structure:

```
.
├── backend/          # Python backend services
│   ├── crawler/      # Playwright BFS crawler → app_map.json
│   ├── generator/    # LLM integration → JSON test cases
│   ├── compiler/     # JSON → Playwright specs
│   ├── runner/       # Execute specs, collect artifacts
│   ├── reporter/     # HTML report generation with AI summaries
│   ├── api/          # FastAPI backend
│   └── shared/       # Shared Python utilities
├── frontend/         # React frontend
└── config/           # Configuration files and examples

```

## Features

1. **Crawler**: BFS traversal of target website to map pages, forms, and actions
2. **Test Generator**: Claude AI converts app map into structured JSON test cases
3. **Compiler**: Transforms JSON test cases into executable Playwright TypeScript specs
4. **Runner**: Executes test suite with artifact collection (JUnit XML, traces, screenshots, videos)
5. **Reporter**: Rich HTML reports with AI-generated failure summaries
6. **Frontend**: React UI to configure runs, select pages, and view results

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Configuration

Copy `config/config.example.json` to `config/config.json` and add your Claude API key.

## Development

### Start Backend
```bash
cd backend
uvicorn api.main:app --reload
```

### Start Frontend
```bash
cd frontend
npm run dev
```

## Project Status

🚧 In Development