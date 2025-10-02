# QAsmith - 3 Testing Types Implementation Plan

## Current Status
✅ **Smoke Testing** - Implemented and working
- Crawls website
- Generates basic navigation tests
- Verifies pages load and links work
- Fast execution (5-10s for 10 pages)

## Type 1: ✅ Smoke Testing (DONE)

**Purpose:** Quick validation that site structure isn't broken

**Features:**
- 1 test per crawled page
- Validates page loads
- Checks basic navigation
- Verifies critical elements exist

**Current Implementation:**
- Generator: `backend/generator/`
- Compiler: `backend/compiler/`
- Runner: `backend/runner/`

---

## Type 2: 🧪 Logic/API Testing (TO BUILD)

**Purpose:** Test business logic, forms, APIs, edge cases

### Frontend Logic Testing

**What to Test:**
- Form validations (empty, invalid, valid inputs)
- User workflows (signup → login → action)
- Error states (404, 500, network failures)
- State persistence (localStorage, cookies, sessions)
- Business logic (calculations, filters, sorting)

**Architecture Changes Needed:**

1. **New Test Generator Mode**
```python
# backend/generator/logic_generator.py
class LogicTestGenerator:
    def generate_form_tests(self, form_data):
        """Generate validation tests for forms"""
        tests = []
        
        for field in form_data['fields']:
            # Test 1: Empty field
            tests.append({
                'name': f'{field["name"]} - Empty validation',
                'steps': [
                    {'action': 'goto', 'url': form_data['url']},
                    {'action': 'click', 'selector': 'button[type="submit"]'},
                    {'action': 'expect', 'selector': f'.error-{field["name"]}', 'assertion': 'toBeVisible'}
                ]
            })
            
            # Test 2: Invalid input
            if field['type'] == 'email':
                tests.append({
                    'name': f'{field["name"]} - Invalid email',
                    'steps': [
                        {'action': 'fill', 'selector': field['selector'], 'value': 'invalid-email'},
                        {'action': 'click', 'selector': 'button[type="submit"]'},
                        {'action': 'expect', 'selector': '.error', 'assertion': 'toContainText', 'value': 'Invalid'}
                    ]
                })
        
        return tests
    
    def generate_workflow_tests(self, pages):
        """Generate multi-page workflow tests"""
        # E.g., Signup → Login → Use feature → Logout
        pass
```

2. **Enhanced Crawler**
```python
# Detect forms with more detail
forms = await page.evaluate('''
() => {
    return Array.from(document.forms).map(form => ({
        action: form.action,
        method: form.method,
        fields: Array.from(form.elements).map(el => ({
            name: el.name,
            type: el.type,
            required: el.required,
            pattern: el.pattern,
            min: el.min,
            max: el.max,
            minLength: el.minLength,
            maxLength: el.maxLength
        }))
    }))
}
''')
```

3. **New Test Templates**
```typescript
// backend/compiler/templates.py - Add form validation templates
FORM_VALIDATION_TEMPLATE = """
  test('{test_name}', async ({{ page }}) => {{
    await page.goto('{form_url}');
    
    // Test invalid state
    await page.fill('{field_selector}', '{invalid_value}');
    await page.click('button[type="submit"]');
    await expect(page.locator('{error_selector}')).toBeVisible();
    
    // Test valid state
    await page.fill('{field_selector}', '{valid_value}');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/{success_url}/);
  }});
"""
```

### API Testing

**What to Test:**
- Endpoint responses (200, 400, 500)
- Request/response data validation
- Authentication flows
- Rate limiting
- Error handling

**Implementation:**

1. **API Test Runner**
```python
# backend/runner/api_runner.py
import requests
from typing import List, Dict
from backend.shared.types import APITestCase, APITestResult

class APITestRunner:
    def run_api_tests(self, base_url: str, tests: List[APITestCase]) -> List[APITestResult]:
        results = []
        
        for test in tests:
            try:
                response = requests.request(
                    method=test.method,
                    url=f"{base_url}{test.endpoint}",
                    headers=test.headers,
                    json=test.body,
                    timeout=test.timeout
                )
                
                # Validate response
                passed = True
                errors = []
                
                if test.expected_status != response.status_code:
                    passed = False
                    errors.append(f"Expected {test.expected_status}, got {response.status_code}")
                
                if test.expected_body:
                    if test.expected_body not in response.json():
                        passed = False
                        errors.append("Response body mismatch")
                
                results.append(APITestResult(
                    test_id=test.test_id,
                    passed=passed,
                    status_code=response.status_code,
                    response_time_ms=int(response.elapsed.total_seconds() * 1000),
                    errors=errors
                ))
            except Exception as e:
                results.append(APITestResult(
                    test_id=test.test_id,
                    passed=False,
                    errors=[str(e)]
                ))
        
        return results
```

2. **API Test Discovery**
```python
# Detect API endpoints from network traffic during crawl
async def discover_apis(page):
    api_calls = []
    
    page.on('request', lambda request: 
        api_calls.append({
            'url': request.url,
            'method': request.method,
            'headers': request.headers
        }) if '/api/' in request.url else None
    )
    
    await page.goto(url)
    return api_calls
```

---

## Type 3: 🔥 Load Testing (TO BUILD)

**Purpose:** Test performance under load (10-10,000 concurrent users)

### Recommended Tool: K6 (Best for web load testing)

**Why K6:**
- JavaScript-based (easy to integrate)
- Supports 1K-10K+ virtual users
- Built-in metrics (response times, throughput, errors)
- Can reuse Playwright test scenarios
- Cloud-ready (k6 Cloud for distributed testing)

**Architecture:**

1. **K6 Integration**
```python
# backend/runner/load_runner.py
import subprocess
import json
from pathlib import Path

class LoadTestRunner:
    def run_load_test(self, test_config: LoadTestConfig) -> LoadTestResult:
        # Generate K6 script from test config
        k6_script = self._generate_k6_script(test_config)
        
        # Write to temp file
        script_path = Path('/tmp/load-test.js')
        script_path.write_text(k6_script)
        
        # Run K6
        result = subprocess.run(
            ['k6', 'run', '--out', 'json=results.json', str(script_path)],
            capture_output=True,
            text=True
        )
        
        # Parse results
        return self._parse_k6_results('results.json')
    
    def _generate_k6_script(self, config: LoadTestConfig) -> str:
        return f"""
import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export const options = {{
  stages: [
    {{ duration: '30s', target: {config.ramp_up_users} }},
    {{ duration: '{config.duration}s', target: {config.max_users} }},
    {{ duration: '30s', target: 0 }},
  ],
  thresholds: {{
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% failures
  }},
}};

export default function() {{
  // User journey from crawled data
  {self._generate_user_journey(config.pages)}
  
  sleep(1);
}}
"""
    
    def _generate_user_journey(self, pages: List[str]) -> str:
        journey = []
        for page in pages:
            journey.append(f"""
  const res_{hash(page)} = http.get('{page}');
  check(res_{hash(page)}, {{
    'status is 200': (r) => r.status === 200,
    'response time OK': (r) => r.timings.duration < 1000,
  }});
""")
        return "\n".join(journey)
```

2. **Load Test Config**
```python
# backend/shared/types.py
class LoadTestConfig(BaseModel):
    pages: List[str]  # URLs to test
    max_users: int    # Peak concurrent users
    ramp_up_users: int  # Initial users
    duration: int     # Test duration in seconds
    ramp_up_duration: int  # Seconds to reach max users
    think_time: int   # Seconds between requests (simulate real users)

class LoadTestResult(BaseModel):
    total_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    errors: List[Dict[str, Any]]
```

3. **Frontend UI for Load Testing**
```tsx
// Load Test Configuration UI
function LoadTestConfig() {
  return (
    <div>
      <h2>Load Testing</h2>
      <input 
        type="number" 
        placeholder="Max Concurrent Users" 
        min="1" 
        max="10000"
      />
      <input 
        type="number" 
        placeholder="Test Duration (seconds)" 
      />
      <input 
        type="number" 
        placeholder="Ramp-up Time (seconds)" 
      />
      <select>
        <option value="smoke">Smoke Test Scenario</option>
        <option value="custom">Custom Scenario</option>
      </select>
      <button onClick={runLoadTest}>Start Load Test</button>
    </div>
  );
}
```

### Alternative: Artillery (YAML-based, simpler)

```yaml
# load-test.yml (auto-generated from crawl)
config:
  target: 'https://example.com'
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 120
      arrivalRate: 100

scenarios:
  - name: "User browsing flow"
    flow:
      - get:
          url: "/products"
      - think: 2
      - get:
          url: "/products/123"
      - think: 3
      - post:
          url: "/cart/add"
          json:
            product_id: 123
```

---

## Implementation Priority

### Phase 1: Logic/API Testing (2-3 weeks)
1. Week 1: Enhanced form detection in crawler
2. Week 1-2: Logic test generator (form validation, workflows)
3. Week 2: API test discovery and runner
4. Week 3: Integration and testing

### Phase 2: Load Testing (1-2 weeks)
1. Week 1: K6 integration and script generation
2. Week 1-2: Results parsing and visualization
3. Week 2: Frontend UI for load test config

---

## Tech Stack Additions

**For Logic/API Testing:**
- ✅ Playwright (already have)
- Add: `requests` (Python HTTP library)
- Add: Schema validation (`pydantic`, `jsonschema`)

**For Load Testing:**
- Add: `k6` (install via `brew install k6` or download)
- Alternative: `artillery` (install via `npm install -g artillery`)
- Add: Metrics storage (TimescaleDB or InfluxDB for time-series data)

---

## Next Steps

1. **Choose API Testing Approach:**
   - Playwright API testing (integrated with browser tests)
   - Standalone API testing (faster, no browser)
   - Both (comprehensive)

2. **Choose Load Testing Tool:**
   - K6 (recommended, powerful, scalable)
   - Artillery (simpler, YAML-based)
   - Playwright workers (limited to ~100 users)

3. **Database for Results:**
   - Current: JSON files
   - Upgrade to: PostgreSQL + TimescaleDB for time-series metrics

Let me know which approaches you want to start with!

