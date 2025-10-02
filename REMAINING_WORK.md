# QAsmith - Remaining Work Summary

## 🎯 Project Status Overview

### Test Type 1: Smoke Testing
**Status:** ⚠️ WORKING BUT BROKEN
- Infrastructure: ✅ Complete
- Test Quality: ❌ Poor (bad selectors, timeouts)

### Test Type 2: Logic/API Testing  
**Status:** 🔧 BACKEND COMPLETE, NO FRONTEND
- Backend: ✅ 100% Complete
- Frontend: ❌ 0% Complete

### Test Type 3: Load Testing
**Status:** 🔧 BACKEND COMPLETE, NEEDS K6 + FRONTEND
- Backend: ✅ 100% Complete
- K6 Installation: ❌ Not installed
- Frontend: ❌ 0% Complete

---

## 📋 Detailed Breakdown

### PRIORITY 1: Fix Smoke Testing (Critical)

#### Problem 1: Bad Selectors ⚠️
**Issue:** AI generates selectors that match multiple elements
```typescript
// Current (BROKEN):
await page.locator('a:text("Sign in")').click();
// Error: Found 2 elements!

// Needed (FIXED):
await page.locator('header a:text("Sign in")').first().click();
// Or: Use more specific selector from crawl data
```

**Root Cause:** 
- AI prompt doesn't emphasize uniqueness
- Selectors not tested for strict mode compliance
- No fallback to `.first()` for common elements

**Fix Needed:**
1. Update AI prompt to require unique selectors
2. Add selector validation (count elements before use)
3. Auto-append `.first()` for known duplicates (Sign in, Logo, etc.)
4. Use more specific selectors from crawl (IDs, data attributes)

#### Problem 2: Test Timeouts ⏰
**Issue:** Tests exceed 30s timeout on slow pages
```
Test timeout of 30000ms exceeded
```

**Fix Needed:**
1. Increase default timeout to 45-60s for navigation tests
2. Add `waitUntil: 'networkidle'` for slow pages
3. Implement retry logic for flaky tests
4. Add custom timeout per test type

#### Problem 3: Generic Selectors 🎯
**Issue:** Selectors like `form` are too generic
```typescript
// Current (BROKEN):
await expect(page.locator('form')).toBeVisible();
// Error: No form found (or too many forms)

// Needed (FIXED):
await expect(page.locator('form[action="/signup"]')).toBeVisible();
```

**Fix Needed:**
1. Crawler must capture form attributes (action, id, name)
2. AI must use specific form selectors
3. Fallback: Use form position/context (first form, form in main, etc.)

---

### PRIORITY 2: Complete Logic/API Testing

#### Backend: ✅ Done
- [x] Form validation test generator
- [x] Workflow test generator
- [x] API test compiler
- [x] API endpoints created

#### Frontend: ❌ To Build
**Need to create:**

1. **Logic Testing Tab** (`frontend/src/pages/LogicTestsPage.tsx`)
```tsx
- Checkbox: "Form Validation Tests"
- Checkbox: "User Workflow Tests"  
- Checkbox: "API Tests" (future)
- Button: "Generate Logic Tests"
- Results display with pass/fail
```

2. **Test Type Selection UI**
```tsx
function LogicTestPanel({ crawlId }) {
  const [testTypes, setTestTypes] = useState(['form_validation']);
  
  const generateTests = async () => {
    const response = await fetch('/tests/logic/generate', {
      method: 'POST',
      body: JSON.stringify({ crawl_id: crawlId, test_types: testTypes })
    });
    // Handle results
  };
  
  return (
    <div>
      <h2>Logic Testing</h2>
      <Checkbox 
        label="Form Validation" 
        checked={testTypes.includes('form_validation')}
        onChange={() => toggleType('form_validation')}
      />
      <Checkbox 
        label="User Workflows" 
        checked={testTypes.includes('workflows')}
        onChange={() => toggleType('workflows')}
      />
      <button onClick={generateTests}>Generate Tests</button>
    </div>
  );
}
```

3. **Logic Test Results Display**
- Show form validation results (empty, invalid, valid)
- Show workflow test results (multi-step pass/fail)
- Display specific failure points

#### Backend Enhancements Needed:
1. **Better Form Detection**
```python
# Current: Basic form detection
# Needed: Full form analysis with validation rules

async def analyze_form(page, form_element):
    return {
        'action': await form.get_attribute('action'),
        'method': await form.get_attribute('method'),
        'fields': [
            {
                'name': field.name,
                'type': field.type,
                'required': field.required,
                'pattern': field.pattern,  # Regex validation
                'min': field.min,
                'max': field.max,
                'minLength': field.minLength,
                'maxLength': field.maxLength,
                'placeholder': field.placeholder
            }
            for field in form.elements
        ]
    }
```

2. **API Endpoint Discovery**
```python
# Monitor network requests during crawl
page.on('request', lambda req: log_api_call(req))
page.on('response', lambda res: log_api_response(res))

# Extract API patterns
discovered_apis = [
    {
        'method': 'POST',
        'path': '/api/users',
        'content_type': 'application/json',
        'sample_body': {...}
    }
]
```

---

### PRIORITY 3: Complete Load Testing

#### Backend: ✅ Done
- [x] K6 script generator
- [x] K6 runner
- [x] Results parser
- [x] API endpoint created

#### System: ❌ K6 Not Installed
**Action Required:**
```bash
# macOS
brew install k6

# Verify
k6 version

# Expected: v0.x.x
```

#### Frontend: ❌ To Build
**Need to create:**

1. **Load Testing Tab** (`frontend/src/pages/LoadTestsPage.tsx`)
```tsx
function LoadTestPanel() {
  return (
    <div>
      <h2>Load Testing (K6)</h2>
      
      <FormGroup>
        <Label>Max Concurrent Users</Label>
        <Input type="number" min="1" max="10000" value={maxUsers} />
      </FormGroup>
      
      <FormGroup>
        <Label>Ramp-Up Duration (seconds)</Label>
        <Input type="number" value={rampUpDuration} />
      </FormGroup>
      
      <FormGroup>
        <Label>Steady State Duration (seconds)</Label>
        <Input type="number" value={steadyDuration} />
      </FormGroup>
      
      <FormGroup>
        <Label>Test Pages</Label>
        <MultiSelect options={crawledPages} selected={selectedPages} />
      </FormGroup>
      
      <Button onClick={runLoadTest}>Start Load Test</Button>
    </div>
  );
}
```

2. **Load Test Results Dashboard**
```tsx
function LoadTestResults({ results }) {
  return (
    <div>
      <MetricCard 
        title="Requests/Second" 
        value={results.requests_per_second} 
        unit="req/s"
      />
      <MetricCard 
        title="Avg Response Time" 
        value={results.avg_response_time_ms} 
        unit="ms"
      />
      <MetricCard 
        title="P95 Response Time" 
        value={results.p95_response_time_ms} 
        unit="ms"
      />
      <MetricCard 
        title="Error Rate" 
        value={(results.failed_requests / results.total_requests * 100).toFixed(2)} 
        unit="%"
      />
      
      {/* Timeline Graph (Future) */}
      <LineChart 
        data={results.timeline}
        xAxis="time"
        yAxis="response_time_ms"
      />
    </div>
  );
}
```

3. **Real-time Progress Updates**
- WebSocket connection for live K6 output
- Progress bar showing test phase (ramp-up, steady, ramp-down)
- Live metrics update every second

---

## 🚀 Implementation Order

### Phase 1: Fix Smoke Tests (1-2 days)
**Critical for basic functionality**
1. ✅ Fix title assertions (DONE)
2. ✅ Fix JSON parser (DONE)
3. ⏳ Fix selector generation
   - Update AI prompt for unique selectors
   - Add `.first()` fallback for duplicates
   - Use more specific crawl data
4. ⏳ Fix timeouts
   - Increase to 45-60s
   - Add networkidle wait
   - Implement retry logic

### Phase 2: Frontend for Logic Testing (2-3 days)
**Unlock form validation & workflow testing**
1. Create LogicTestsPage.tsx
2. Add test type selection UI
3. Integrate with /tests/logic/generate endpoint
4. Display logic test results
5. Add compile & run buttons (reuse existing flow)

### Phase 3: Frontend for Load Testing (2-3 days)
**Unlock performance testing**
1. Install K6 (`brew install k6`)
2. Create LoadTestsPage.tsx
3. Build configuration form
4. Integrate with /tests/load/run endpoint
5. Display metrics dashboard
6. Add timeline graphs (optional)

### Phase 4: Enhancements (1-2 weeks)
**Polish and extend**
1. Better form detection in crawler
2. API endpoint discovery
3. Advanced load test scenarios
4. Performance graphs/charts
5. Test history & comparison
6. CI/CD integration

---

## 📊 Effort Estimation

| Task | Effort | Priority |
|------|--------|----------|
| Fix smoke test selectors | 4-6 hours | 🔴 Critical |
| Fix timeouts | 2-3 hours | 🔴 Critical |
| Logic testing frontend | 8-12 hours | 🟡 High |
| Load testing frontend | 8-12 hours | 🟡 High |
| Install K6 | 5 minutes | 🟡 High |
| Enhanced form detection | 4-6 hours | 🟢 Medium |
| API discovery | 6-8 hours | 🟢 Medium |
| Graphs/charts | 6-8 hours | 🟢 Medium |
| **Total** | **40-60 hours** | |

---

## 🎯 Quick Win Checklist

**Can be done in next 30 minutes:**
- [ ] Install K6: `brew install k6`
- [ ] Test load API manually: `curl -X POST ...`
- [ ] Fix one selector issue as example

**Can be done today:**
- [ ] Fix all smoke test selector issues
- [ ] Fix timeout issues
- [ ] Create basic Logic Testing tab UI

**Can be done this week:**
- [ ] Complete Logic Testing frontend
- [ ] Complete Load Testing frontend
- [ ] Test all 3 test types end-to-end

---

## 📝 Notes

**Current Working Directory:**
```
/Users/mohak/Desktop/QAsmith
```

**Key Files:**
- Smoke test generator: `backend/generator/generator.py`
- Logic test generator: `backend/generator/logic_generator.py`
- Load test runner: `backend/runner/load_runner.py`
- API endpoints: `backend/api/test_type_endpoints.py`
- Frontend: `frontend/src/pages/` (need to create LogicTestsPage, LoadTestsPage)

**Documentation:**
- `IMPLEMENTATION_GUIDE.md` - Full setup guide
- `TESTING_TYPES_ROADMAP.md` - Architecture plan
- `COMPLETE_FIX_GUIDE.md` - All fixes applied
- `TEST_EXECUTION_FIX.md` - Test execution issues

---

## 🆘 Need Help With

**Frontend:**
- Creating new pages for Logic/Load testing
- Integrating with new API endpoints
- Building metrics dashboard

**Backend:**
- Form field detection enhancement
- API endpoint discovery during crawl
- Advanced K6 scenarios

**DevOps:**
- K6 installation on different platforms
- CI/CD integration for automated testing

