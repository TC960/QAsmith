"""Templates for generating Playwright TypeScript code."""

from backend.shared.types import ActionType, SelectorStrategy

# Main test file template
TEST_FILE_TEMPLATE = """import {{ test, expect }} from '@playwright/test';

test.describe('Generated E2E Tests', () => {{
  test.beforeEach(async ({{ page }}) => {{
    await page.goto('{base_url}');
  }});

{test_cases}
}});
"""

# Individual test case template
TEST_CASE_TEMPLATE = """  test('{test_name}', async ({{ page }}) => {{
    // {test_description}

{steps}

{assertions}
  }});"""

# Selector generation templates
SELECTOR_TEMPLATES = {
    SelectorStrategy.TEST_ID: "page.getByTestId('{selector}')",
    SelectorStrategy.ARIA_LABEL: "page.getByLabel('{selector}')",
    SelectorStrategy.TEXT: "page.getByText('{selector}')",
    SelectorStrategy.CSS: "page.locator('{selector}')",
    SelectorStrategy.XPATH: "page.locator('{selector}')",
}

# Action templates
TEST_STEP_TEMPLATES = {
    ActionType.NAVIGATE: "    await page.goto('{value}');",

    ActionType.GOTO: "    await page.goto('{url}');",

    ActionType.CLICK: "    await {selector}.click();",

    ActionType.FILL: "    await {selector}.fill('{value}');",

    ActionType.SELECT: "    await {selector}.selectOption('{value}');",

    ActionType.SUBMIT: "    await {selector}.click(); // Submit form",

    ActionType.HOVER: "    await {selector}.hover();",

    ActionType.CHECK: "    await {selector}.check();",

    ActionType.UNCHECK: "    await {selector}.uncheck();",

    ActionType.EXPECT: "    await expect({selector}).{assertion}({value});",

    ActionType.GO_BACK: "    await page.goBack();",

    ActionType.RELOAD: "    await page.reload();",

    ActionType.WAIT: "    await page.waitForTimeout({value}); // Wait {value}ms for dynamic content",
}


def generate_assertion(assertion_text: str) -> str:
    """Generate assertion code from assertion text."""
    # Simple heuristics for common assertions
    if "visible" in assertion_text.lower():
        return "    await expect(page.locator('selector')).toBeVisible();"
    elif "text" in assertion_text.lower() or "contains" in assertion_text.lower():
        return "    await expect(page).toContainText('expected text');"
    elif "url" in assertion_text.lower():
        return "    await expect(page).toHaveURL(/expected-url/);"
    else:
        return f"    // TODO: Implement assertion: {assertion_text}"