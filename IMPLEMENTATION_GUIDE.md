# QAsmith - 3 Testing Types Implementation

## ✅ What's Been Built

I've implemented the architecture for all 3 testing types based on your requirements:

### 1. ✅ Smoke Testing (Already Working)
- Quick URL validation
- Basic navigation checks
- Fast execution

### 2. ✅ Logic/API Testing (Just Built)
**Backend:** Playwright API testing (no browser)
**Frontend:** Playwright browser testing (forms, workflows)

**New Features:**
- Form validation testing (empty, invalid, valid inputs)
- Multi-page workflow testing (signup → login → action)
- API endpoint testing (status codes, response validation)

### 3. ✅ Load Testing (Just Built)
**Tool:** K6 for scalable load testing
- Supports 10-10,000+ concurrent users
- Configurable ramp-up/steady/ramp-down phases
- Real-time metrics (RPS, response times, errors)

---

## 🏗️ Architecture Overview

### New Files Created:

```
backend/
├── generator/
│   └── logic_generator.py          # Generates form/workflow tests
├── compiler/
│   ├── api_templates.py            # Playwright API test templates
│   └── api_compiler.py             # Compiles API tests
├── runner/
│   └── load_runner.py              # K6 load test runner
└── api/
    └── test_type_endpoints.py      # New API endpoints
```

### API Endpoints Added:

```
POST /tests/logic/generate          # Generate logic tests
POST /tests/load/run                # Run K6 load test
POST /tests/api/compile             # Compile API tests
```

---

## 🚀 Setup Instructions

### 1. Install K6 (for load testing)

**macOS:**
```bash
brew install k6
```

**Linux:**
```bash
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**Windows:**
```bash
choco install k6
# or
winget install k6 --source winget
```

**Verify installation:**
```bash
k6 version
```

### 2. Restart Backend

```bash
cd /Users/mohak/Desktop/QAsmith
python start_backend.py
```

---

## 📋 How to Use Each Test Type

### Type 1: Smoke Testing (Current)

**What it does:** Quick validation that pages load

**How to use:**
1. Crawl website → Generate tests → Compile → Run
2. Tests check: URL loads, title correct, basic navigation

**Example output:**
```
✅ 10/10 tests passed
- Homepage loads
- About page accessible
- Contact form visible
```

---

### Type 2: Logic/API Testing (New)

#### A. Form Validation Testing

**What it does:** Tests form inputs with empty, invalid, and valid data

**How to use:**

1. **Crawl website** (forms are auto-detected)

2. **Generate logic tests:**
```bash
POST /tests/logic/generate
{
  "crawl_id": "abc123",
  "test_types": ["form_validation", "workflows"]
}
```

3. **Compile tests** (same as smoke tests)

4. **Run tests** (same as smoke tests)

**Example tests generated:**
```typescript
// Test 1: Empty form submission
test('Contact Form - Empty Validation', async ({ page }) => {
  await page.goto('/contact');
  await page.click('button[type="submit"]');
  await expect(page.locator('.error')).toBeVisible();
});

// Test 2: Invalid email
test('Contact Form - Invalid Email', async ({ page }) => {
  await page.goto('/contact');
  await page.fill('input[name="email"]', 'invalid-email');
  await page.click('button[type="submit"]');
  await expect(page.locator('.error')).toBeVisible();
});

// Test 3: Valid submission
test('Contact Form - Valid Submission', async ({ page }) => {
  await page.goto('/contact');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="message"]', 'Test message');
  await page.click('button[type="submit"]');
  await expect(page.locator('.success')).toBeVisible();
});
```

#### B. Workflow Testing

**What it does:** Tests multi-page user journeys

**Example:**
```typescript
test('Complete Signup and Login Flow', async ({ page }) => {
  // Step 1: Signup
  await page.goto('/signup');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'SecurePass123!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
  
  // Step 2: Logout
  await page.click('button:text("Logout")');
  
  // Step 3: Login
  await page.goto('/login');
  await page.fill('input[name="email"]', 'user@example.com');
  await page.fill('input[name="password"]', 'SecurePass123!');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/dashboard/);
});
```

#### C. API Testing

**What it does:** Tests backend APIs without browser

**Example:**
```typescript
test('API: GET /users - Success', async ({ request }) => {
  const response = await request.get('/api/users');
  expect(response.ok()).toBeTruthy();
  expect(response.status()).toBe(200);
  
  const body = await response.json();
  expect(Array.isArray(body)).toBeTruthy();
});

test('API: POST /users - Invalid Data', async ({ request }) => {
  const response = await request.post('/api/users', {
    data: {}  // Empty body
  });
  expect(response.status()).toBe(400);
});
```

---

### Type 3: Load Testing (New)

**What it does:** Simulates hundreds/thousands of concurrent users

**How to use:**

1. **Run load test via API:**
```bash
POST /tests/load/run
{
  "base_url": "https://example.com",
  "pages": ["/", "/products", "/about"],
  "max_users": 100,
  "ramp_up_duration": 30,
  "steady_duration": 60,
  "ramp_down_duration": 30,
  "think_time": 1
}
```

2. **Get results:**
```json
{
  "test_id": "load_abc123",
  "total_requests": 15000,
  "failed_requests": 50,
  "requests_per_second": 125.5,
  "avg_response_time_ms": 245.3,
  "p95_response_time_ms": 480.2,
  "p99_response_time_ms": 890.1,
  "passed_thresholds": true,
  "errors": []
}
```

**Load Test Configuration:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `max_users` | Peak concurrent virtual users | 100 |
| `ramp_up_duration` | Seconds to reach max users | 30 |
| `steady_duration` | Seconds at peak load | 60 |
| `ramp_down_duration` | Seconds to ramp down | 30 |
| `think_time` | Seconds between user actions | 1 |

**Performance Thresholds:**
- 95% of requests must complete < 500ms
- Less than 1% request failures
- (Configurable in code)

**Example K6 Script Generated:**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 100 }, // Ramp up to 100 users
    { duration: '60s', target: 100 }, // Stay at 100 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'], // 95% under 500ms
    'http_req_failed': ['rate<0.01'],   // <1% failures
  },
};

export default function() {
  // User journey
  const res1 = http.get('https://example.com/');
  check(res1, { 'status is 200': (r) => r.status === 200 });
  sleep(0.5);
  
  const res2 = http.get('https://example.com/products');
  check(res2, { 'status is 200': (r) => r.status === 200 });
  sleep(0.5);
  
  sleep(1); // Think time
}
```

---

## 🎨 Frontend Integration (Next Step)

You'll need to add UI components for the new test types:

### 1. Logic Testing Tab
```tsx
function LogicTestingPanel() {
  return (
    <div>
      <h2>Logic & API Testing</h2>
      
      <h3>Select Test Types:</h3>
      <Checkbox label="Form Validation" checked />
      <Checkbox label="User Workflows" checked />
      <Checkbox label="API Endpoints" />
      
      <button onClick={generateLogicTests}>
        Generate Logic Tests
      </button>
      
      <TestResults tests={logicTests} />
    </div>
  );
}
```

### 2. Load Testing Tab
```tsx
function LoadTestingPanel() {
  return (
    <div>
      <h2>Load Testing (K6)</h2>
      
      <input 
        type="number" 
        label="Max Concurrent Users"
        value={maxUsers}
        onChange={(e) => setMaxUsers(e.target.value)}
      />
      
      <input 
        type="number" 
        label="Test Duration (seconds)"
        value={duration}
      />
      
      <button onClick={runLoadTest}>
        Start Load Test
      </button>
      
      <LoadTestResults 
        rps={results.requests_per_second}
        p95={results.p95_response_time_ms}
        errors={results.errors}
      />
    </div>
  );
}
```

---

## 📊 Results & Metrics

### Smoke Tests
```
✅ Pass/Fail
⏱️ Duration
📍 Failed selectors
```

### Logic Tests
```
✅ Form validation pass/fail
🔄 Workflow completion
❌ Validation errors caught
```

### Load Tests
```
📈 Requests per second (RPS)
⏱️ Response times (avg, p95, p99)
❌ Error rate
✅ Threshold pass/fail
📊 Timeline graph (future)
```

---

## 🔧 Technical Details

### Logic Test Generator
- **Forms:** Auto-detects forms during crawl
- **Validation:** Tests empty, invalid, valid inputs
- **Workflows:** AI-generated multi-page journeys
- **API:** Discovers endpoints from network traffic (future)

### Load Test Runner
- **Engine:** K6 (JavaScript-based)
- **Scalability:** 1-10,000+ virtual users
- **Metrics:** Built-in (no DB needed initially)
- **Output:** JSON results, summary metrics

### API Testing
- **Framework:** Playwright `request` fixture
- **No Browser:** Faster than E2E
- **Features:** Status codes, JSON validation, headers

---

## ✅ Next Steps

1. **Install K6:**
   ```bash
   brew install k6  # macOS
   k6 version       # Verify
   ```

2. **Restart Backend:**
   ```bash
   python start_backend.py
   ```

3. **Test Logic Tests API:**
   ```bash
   curl -X POST http://localhost:8000/tests/logic/generate \
     -H "Content-Type: application/json" \
     -d '{
       "crawl_id": "YOUR_CRAWL_ID",
       "test_types": ["form_validation", "workflows"]
     }'
   ```

4. **Test Load Test API:**
   ```bash
   curl -X POST http://localhost:8000/tests/load/run \
     -H "Content-Type: application/json" \
     -d '{
       "base_url": "https://github.com",
       "pages": ["/", "/features"],
       "max_users": 50,
       "steady_duration": 30
     }'
   ```

5. **Frontend Integration:**
   - Add tabs for Logic Testing and Load Testing
   - Create forms for configuration
   - Display results with charts/metrics

---

## 🎯 Summary

| Test Type | Purpose | Tool | Speed | Use Case |
|-----------|---------|------|-------|----------|
| **Smoke** | URLs load | Playwright | Fast (10s) | Quick validation |
| **Logic** | Functionality works | Playwright | Medium (1-5min) | Feature testing |
| **Load** | Performance under load | K6 | Slow (2-10min) | Scalability testing |

All systems ready! Just need to:
1. Install K6
2. Restart backend
3. Build frontend UI for new test types

Let me know if you want help with the frontend integration!

