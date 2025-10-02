"""API endpoints for Logic and Load testing."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

from backend.generator.logic_generator import LogicTestGenerator
from backend.compiler.api_compiler import APITestCompiler
from backend.runner.load_runner import K6LoadRunner, LoadTestConfig, LoadTestResult
from backend.shared.config import get_config

router = APIRouter(prefix="/tests", tags=["Advanced Testing"])
config = get_config()


# ===== REQUEST/RESPONSE MODELS =====

class GenerateLogicTestsRequest(BaseModel):
    crawl_id: str
    test_types: List[str]  # ['form_validation', 'workflows', 'api']


class GenerateLogicTestsResponse(BaseModel):
    suite_id: str
    form_tests_count: int
    workflow_tests_count: int
    api_tests_count: int
    total_tests: int
    success: bool


class RunLoadTestRequest(BaseModel):
    base_url: str
    pages: List[str]
    max_users: int = 100
    ramp_up_duration: int = 30
    steady_duration: int = 60
    ramp_down_duration: int = 30
    think_time: int = 1


class RunLoadTestResponse(BaseModel):
    test_id: str
    total_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    passed_thresholds: bool
    errors: List[Dict[str, Any]]


# ===== ENDPOINTS =====

@router.post("/logic/generate", response_model=GenerateLogicTestsResponse)
async def generate_logic_tests(request: GenerateLogicTestsRequest):
    """Generate logic/functional tests (form validation, workflows, API tests)."""
    print(f"🧪 Generating logic tests for crawl {request.crawl_id}")
    
    try:
        import json
        from backend.shared.types import AppMap
        
        # Load crawl data
        crawl_file = Path(config.storage.app_maps_path) / f"{request.crawl_id}.json"
        if not crawl_file.exists():
            raise HTTPException(status_code=404, detail=f"Crawl {request.crawl_id} not found")
        
        with open(crawl_file, 'r') as f:
            crawl_data = json.load(f)
        
        app_map = AppMap(**crawl_data)
        
        # Initialize generator
        logic_gen = LogicTestGenerator()
        
        form_tests = []
        workflow_tests = []
        api_tests = []
        
        # Generate requested test types
        if 'form_validation' in request.test_types:
            form_tests = logic_gen.generate_form_tests(app_map)
            print(f"✅ Generated {len(form_tests)} form validation tests")
        
        if 'workflows' in request.test_types:
            workflow_tests = logic_gen.generate_workflow_tests(app_map)
            print(f"✅ Generated {len(workflow_tests)} workflow tests")
        
        # TODO: API discovery during crawl
        # if 'api' in request.test_types:
        #     api_tests = logic_gen.generate_api_tests(discovered_apis)
        
        # Save logic test suite
        from backend.shared.utils import generate_id, save_json
        suite_id = generate_id("logic_suite_")
        
        all_tests = form_tests + workflow_tests
        
        suite_data = {
            'suite_id': suite_id,
            'crawl_id': request.crawl_id,
            'test_count': len(all_tests),
            'test_types': request.test_types,
            'tests': [test.model_dump() for test in all_tests]
        }
        
        suite_file = Path(config.storage.test_specs_path) / f"{suite_id}.json"
        save_json(suite_data, suite_file)
        
        return GenerateLogicTestsResponse(
            suite_id=suite_id,
            form_tests_count=len(form_tests),
            workflow_tests_count=len(workflow_tests),
            api_tests_count=len(api_tests),
            total_tests=len(all_tests),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Logic test generation failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/run", response_model=RunLoadTestResponse)
async def run_load_test(request: RunLoadTestRequest):
    """Execute K6 load test with specified configuration."""
    print(f"🔥 Starting load test: {request.max_users} users on {request.base_url}")
    
    try:
        # Create load test config
        load_config = LoadTestConfig(
            pages=request.pages,
            max_users=request.max_users,
            ramp_up_duration=request.ramp_up_duration,
            steady_duration=request.steady_duration,
            ramp_down_duration=request.ramp_down_duration,
            think_time=request.think_time
        )
        
        # Run load test
        runner = K6LoadRunner()
        result = runner.run_load_test(load_config, request.base_url)
        
        # Save results
        from backend.shared.utils import save_json
        results_file = Path(config.storage.reports_path) / f"{result.test_id}_load_test.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        save_json(result.model_dump(), results_file)
        
        return RunLoadTestResponse(
            test_id=result.test_id,
            total_requests=result.total_requests,
            failed_requests=result.failed_requests,
            requests_per_second=result.requests_per_second,
            avg_response_time_ms=result.avg_response_time_ms,
            p95_response_time_ms=result.p95_response_time_ms,
            p99_response_time_ms=result.p99_response_time_ms,
            passed_thresholds=result.passed_thresholds,
            errors=result.errors
        )
        
    except FileNotFoundError as e:
        if 'k6' in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail="K6 not installed. Install with: brew install k6 (macOS) or npm install -g k6"
            )
        raise
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/compile")
async def compile_api_tests(suite_id: str):
    """Compile API tests from logic test suite."""
    print(f"🔧 Compiling API tests for suite {suite_id}")
    
    try:
        import json
        
        # Load suite
        suite_file = Path(config.storage.test_specs_path) / f"{suite_id}.json"
        if not suite_file.exists():
            raise HTTPException(status_code=404, detail=f"Suite {suite_id} not found")
        
        with open(suite_file, 'r') as f:
            suite_data = json.load(f)
        
        # Extract API tests (if any)
        api_tests = [t for t in suite_data.get('tests', []) if 'api' in t.get('tags', [])]
        
        if not api_tests:
            raise HTTPException(status_code=400, detail="No API tests found in suite")
        
        # Compile
        compiler = APITestCompiler()
        spec_path = compiler.compile_api_tests(
            api_tests,
            suite_data.get('base_url', 'http://localhost'),
            suite_id
        )
        
        return {
            'suite_id': suite_id,
            'spec_file_path': str(spec_path),
            'api_tests_count': len(api_tests),
            'success': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API test compilation failed: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

