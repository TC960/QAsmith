"""K6 Load Testing Runner - Generate and execute K6 load tests."""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.shared.config import get_config
from backend.shared.utils import generate_id, get_timestamp


class LoadTestConfig(BaseModel):
    """Configuration for a load test."""
    pages: List[str]  # URLs to test
    max_users: int = 100  # Peak concurrent virtual users
    ramp_up_duration: int = 30  # Seconds to ramp up to max users
    steady_duration: int = 60  # Seconds to maintain max users
    ramp_down_duration: int = 30  # Seconds to ramp down
    think_time: int = 1  # Seconds between user actions
    thresholds: Dict[str, str] = {
        'http_req_duration': 'p(95)<500',  # 95% of requests under 500ms
        'http_req_failed': 'rate<0.01'     # Less than 1% failures
    }


class LoadTestResult(BaseModel):
    """Results from a load test execution."""
    test_id: str
    timestamp: str
    total_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    errors: List[Dict[str, Any]]
    passed_thresholds: bool
    duration_seconds: int


class K6LoadRunner:
    """Generates and executes K6 load tests."""

    def __init__(self):
        self.config = get_config()

    def run_load_test(self, config: LoadTestConfig, base_url: str) -> LoadTestResult:
        """Generate K6 script and execute load test."""
        print(f"🔥 Starting load test: {config.max_users} users on {base_url}")

        # Generate K6 script
        test_id = generate_id("load_")
        k6_script = self._generate_k6_script(config, base_url)
        
        # Save script
        script_path = Path(self.config.storage.test_specs_path) / "load_tests" / f"{test_id}.js"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(k6_script)
        
        # Results path
        results_path = script_path.parent / f"{test_id}_results.json"
        
        # Execute K6
        print(f"📊 Running K6 load test...")
        result = self._execute_k6(script_path, results_path)
        
        # Parse results
        load_result = self._parse_k6_results(results_path, test_id)
        
        print(f"✅ Load test complete: {load_result.requests_per_second:.2f} req/s, "
              f"p95: {load_result.p95_response_time_ms:.2f}ms")
        
        return load_result

    def _generate_k6_script(self, config: LoadTestConfig, base_url: str) -> str:
        """Generate K6 JavaScript test script."""
        
        # Build user journey from pages
        user_journey = self._generate_user_journey(config.pages, base_url)
        
        # Build thresholds
        thresholds_str = ",\n    ".join([
            f"'{k}': ['{v}']" for k, v in config.thresholds.items()
        ])
        
        script = f"""import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate }} from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {{
  stages: [
    {{ duration: '{config.ramp_up_duration}s', target: {config.max_users} }}, // Ramp up
    {{ duration: '{config.steady_duration}s', target: {config.max_users} }}, // Steady state
    {{ duration: '{config.ramp_down_duration}s', target: 0 }},               // Ramp down
  ],
  thresholds: {{
    {thresholds_str}
  }},
}};

export default function() {{
  // Simulate user journey
{user_journey}
  
  // Think time between iterations
  sleep({config.think_time});
}}

export function handleSummary(data) {{
  return {{
    'stdout': JSON.stringify(data, null, 2),
  }};
}}
"""
        return script

    def _generate_user_journey(self, pages: List[str], base_url: str) -> str:
        """Generate user journey code for K6."""
        journey_steps = []
        
        for idx, page in enumerate(pages):
            # Build full URL
            if page.startswith('http'):
                url = page
            else:
                url = f"{base_url.rstrip('/')}/{page.lstrip('/')}"
            
            var_name = f"res{idx}"
            
            step = f"""  // Step {idx + 1}: Visit {page}
  const {var_name} = http.get('{url}');
  check({var_name}, {{
    'status is 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 2000,
  }}) || errorRate.add(1);
  
  sleep(0.5); // Brief pause between pages
"""
            journey_steps.append(step)
        
        return "\n".join(journey_steps)

    def _execute_k6(self, script_path: Path, results_path: Path) -> subprocess.CompletedProcess:
        """Execute K6 load test."""
        cmd = [
            'k6',
            'run',
            '--out', f'json={results_path}',
            '--summary-export', f'{results_path.parent}/{results_path.stem}_summary.json',
            str(script_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                print(f"⚠️ K6 exited with code {result.returncode}")
                print(f"stderr: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            print("⚠️ K6 test timed out after 10 minutes")
            raise
        except FileNotFoundError:
            print("❌ K6 not found. Install with: brew install k6 (macOS) or npm install -g k6")
            raise

    def _parse_k6_results(self, results_path: Path, test_id: str) -> LoadTestResult:
        """Parse K6 JSON results."""
        
        # K6 writes results to summary file
        summary_path = results_path.parent / f"{results_path.stem}_summary.json"
        
        if not summary_path.exists():
            print(f"⚠️ K6 summary not found at {summary_path}")
            return LoadTestResult(
                test_id=test_id,
                timestamp=get_timestamp(),
                total_requests=0,
                failed_requests=0,
                requests_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                max_response_time_ms=0,
                errors=[],
                passed_thresholds=False,
                duration_seconds=0
            )
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        # Extract metrics
        metrics = summary.get('metrics', {})
        
        http_reqs = metrics.get('http_reqs', {}).get('values', {})
        http_req_duration = metrics.get('http_req_duration', {}).get('values', {})
        http_req_failed = metrics.get('http_req_failed', {}).get('values', {})
        
        total_requests = int(http_reqs.get('count', 0))
        failed_rate = http_req_failed.get('rate', 0)
        failed_requests = int(total_requests * failed_rate)
        
        # Response times (K6 reports in milliseconds)
        avg_response = http_req_duration.get('avg', 0)
        p95_response = http_req_duration.get('p(95)', 0)
        p99_response = http_req_duration.get('p(99)', 0)
        max_response = http_req_duration.get('max', 0)
        
        # Calculate RPS
        duration = summary.get('state', {}).get('testRunDurationMs', 1000) / 1000
        rps = total_requests / duration if duration > 0 else 0
        
        # Check if thresholds passed
        passed_thresholds = all(
            metric.get('thresholds', {}).get(thresh, {}).get('ok', True)
            for metric in metrics.values()
            for thresh in metric.get('thresholds', {})
        )
        
        # Extract errors
        errors = []
        if failed_requests > 0:
            errors.append({
                'type': 'http_failures',
                'count': failed_requests,
                'rate': f"{failed_rate * 100:.2f}%"
            })
        
        return LoadTestResult(
            test_id=test_id,
            timestamp=get_timestamp(),
            total_requests=total_requests,
            failed_requests=failed_requests,
            requests_per_second=rps,
            avg_response_time_ms=avg_response,
            p95_response_time_ms=p95_response,
            p99_response_time_ms=p99_response,
            max_response_time_ms=max_response,
            errors=errors,
            passed_thresholds=passed_thresholds,
            duration_seconds=int(duration)
        )

    def generate_load_test_from_smoke_tests(self, smoke_test_urls: List[str]) -> LoadTestConfig:
        """Auto-generate load test config from smoke test URLs."""
        return LoadTestConfig(
            pages=smoke_test_urls,
            max_users=50,  # Default moderate load
            ramp_up_duration=30,
            steady_duration=60,
            ramp_down_duration=30,
            think_time=1
        )

