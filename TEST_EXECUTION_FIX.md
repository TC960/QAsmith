# Test Execution Issue - Root Cause & Solution

## Problem Summary
Tests were failing with 0% pass rate because AI-generated tests used fictional selectors that didn't exist on actual websites.

## Root Cause Analysis

### Issue 1: Missing Playwright Browsers (RESOLVED)
- **Error**: `browserType.launch: Executable doesn't exist`
- **Cause**: Playwright browser binaries not installed
- **Status**: ✅ Fixed - Chromium browser now installed

### Issue 2: Invalid Test Selectors (MAIN ISSUE - NOW FIXED)
- **Error**: `Expected: visible, Received: <element(s) not found>`
- **Cause**: Test generator was creating tests with guessed/made-up selectors

#### Example from CVS Website Test:
**Generated Test Used:**
- `.clinic-locator` ❌
- `#location-search` ❌
- `#search-button` ❌

**Actual Page Has:**
- `textbox "ZIP code, or city and state"` ✅
- `button "search"` ✅

#### Why This Happened:
The test generator (`backend/generator/generator.py`) was only sending action **descriptions** to the AI:
```
Actions:
  - Click on search button
  - Fill location search field
```

It did NOT include the actual **selectors**:
```
Actions:
  - Click on search button (selector: button[aria-label='search'], strategy: css)
  - Fill location search field (selector: input[name='location'], strategy: css)
```

So the AI had no choice but to guess selectors like `#search-button`, which don't exist.

## The Fix

### 1. Updated `backend/generator/generator.py` (Line 79)
Now includes actual selectors in the app map summary sent to AI:

```python
# BEFORE:
page_summary += f"  - {action.description}\n"

# AFTER:
selector_info = f" (selector: {action.element.selector}, strategy: {action.element.selector_strategy.value})" if action.element.selector else ""
page_summary += f"  - {action.description}{selector_info}\n"
```

### 2. Updated `backend/generator/prompts.py` (Line 19)
Added critical instruction to use only provided selectors:

```
REQUIREMENTS:
- **CRITICAL**: Use ONLY the selectors provided in the application map - do NOT make up or guess selectors
- When a selector is provided in the action description, use it exactly as shown
- Use the selector_strategy that matches the provided selector (if specified)
```

## Testing the Fix

To verify the fix works:

1. **Re-crawl a website**
   - Go to your app at http://localhost:3000
   - Enter a website URL and crawl it
   - The crawler will capture actual selectors

2. **Generate new tests**
   - Click "Generate Tests"
   - The AI will now receive actual selectors
   - Tests should use real selectors from the page

3. **Run the tests**
   - Tests should now find elements successfully
   - Pass rate should improve dramatically

## Expected Outcome

✅ Tests will use real selectors from crawled data
✅ Elements will be found on the page
✅ Tests will execute properly instead of timing out
✅ Pass rate should reflect actual functionality, not selector issues

## Example: Correct Test Generation

**Before Fix (Fictional Selectors):**
```typescript
await page.locator('#search-button').click(); // Element doesn't exist!
```

**After Fix (Real Selectors):**
```typescript
await page.locator('button[aria-label="search"]').click(); // Actual element from crawl
```

---

**Status**: ✅ FIXED - Ready to test with new crawl and test generation

