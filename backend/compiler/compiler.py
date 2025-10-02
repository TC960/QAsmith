"""Compile JSON test cases into Playwright TypeScript specs."""

from pathlib import Path
from typing import List
from backend.shared.types import TestSuite, TestCase, TestStep, ActionType, SelectorStrategy
from backend.shared.config import get_config
from .templates import (
    TEST_FILE_TEMPLATE,
    TEST_CASE_TEMPLATE,
    TEST_STEP_TEMPLATES,
    SELECTOR_TEMPLATES,
)


class TestCompiler:
    """Compiles JSON test cases into executable Playwright TypeScript specs."""

    def __init__(self):
        self.config = get_config()

    def compile(self, test_suite: TestSuite) -> Path:
        """Compile a test suite into a Playwright spec file."""
        print(f"Compiling test suite: {test_suite.name}")

        # Generate test cases code
        test_cases_code = []
        for test_case in test_suite.test_cases:
            test_code = self._compile_test_case(test_case)
            test_cases_code.append(test_code)

        # Generate complete file
        file_content = TEST_FILE_TEMPLATE.format(
            base_url=test_suite.base_url,
            test_cases="\n\n".join(test_cases_code),
        )

        # Save to file
        output_path = self._save_spec_file(test_suite.suite_id, file_content)
        print(f"Compiled spec saved to: {output_path}")

        return output_path

    def _compile_test_case(self, test_case: TestCase) -> str:
        """Compile a single test case."""
        # Generate steps code
        steps_code = []
        for i, step in enumerate(test_case.steps, 1):
            step_code = self._compile_step(step, i)
            steps_code.append(step_code)

        # Generate assertions
        assertions_code = []
        for assertion in test_case.assertions:
            # Simple assertions (can be enhanced)
            assertions_code.append(f"    // Assert: {assertion}")

        return TEST_CASE_TEMPLATE.format(
            test_name=test_case.name,
            test_description=test_case.description,
            steps="\n".join(steps_code),
            assertions="\n".join(assertions_code) if assertions_code else "    // No explicit assertions",
        )

    def _compile_step(self, step: TestStep, step_number: int) -> str:
        """Compile a single test step."""
        # Get action template
        action_template = TEST_STEP_TEMPLATES.get(step.action)
        if not action_template:
            return f"    // Unsupported action: {step.action}"

        # Handle different action types
        if step.action == ActionType.GOTO:
            action_code = action_template.format(url=step.url or step.value or "")
        elif step.action == ActionType.WAIT:
            # Wait action needs a timeout value
            timeout_value = step.value or "1000"  # Default to 1 second
            action_code = action_template.format(value=timeout_value)
        elif step.action in [ActionType.GO_BACK, ActionType.RELOAD]:
            # Actions that don't need selectors or values
            action_code = action_template
        elif step.action == ActionType.EXPECT:
            # Special handling for title assertions
            if step.selector and step.selector.lower() == 'title':
                # Use page.toHaveTitle() for title assertions
                if step.value:
                    escaped_value = step.value.replace("'", "\\'")
                    # Use regex pattern for flexible matching
                    action_code = f"    await expect(page).toHaveTitle(/{escaped_value}/);"
                else:
                    action_code = "    // SKIPPED: Title assertion requires a value"
            else:
                # Format selector - use _generate_selector for :visible + .first() support
                if step.selector:
                    escaped_selector = step.selector.replace("'", "\\'")
                    selector_code = self._generate_selector(escaped_selector, step.selector_strategy)
                else:
                    selector_code = "page"

                # Assertions that don't need values
                no_value_assertions = [
                    'toBeVisible', 'toBeHidden', 'toBeEnabled', 'toBeDisabled',
                    'toBeChecked', 'toBeEditable', 'toBeEmpty', 'toBeFocused',
                    'toBeAttached', 'toBeInViewport'
                ]

                assertion = step.assertion or "toBeVisible"

                # Handle timeout if provided
                timeout_option = ""
                if hasattr(step, 'timeout') and step.timeout:
                    timeout_option = f"{{ timeout: {step.timeout} }}"

                # Check if this assertion needs a value
                if assertion in no_value_assertions:
                    # No value needed - generate without parentheses content
                    if timeout_option:
                        action_code = f"    await expect({selector_code}).{assertion}({timeout_option});"
                    else:
                        action_code = f"    await expect({selector_code}).{assertion}();"
                elif step.value:
                    # Has a value - use it
                    escaped_value = step.value.replace("'", "\\'")
                    value_str = f"'{escaped_value}'"
                    if timeout_option:
                        action_code = f"    await expect({selector_code}).{assertion}({value_str}, {timeout_option});"
                    else:
                        action_code = f"    await expect({selector_code}).{assertion}({value_str});"
                else:
                    # Assertion requires value but none provided - skip or use default
                    action_code = f"    // SKIPPED: {assertion} requires a value but none was provided"
        else:
            # Regular actions with selectors - escape quotes
            if step.selector:
                escaped_selector = step.selector.replace("'", "\\'")
                selector_code = self._generate_selector(escaped_selector, step.selector_strategy)
            else:
                selector_code = "page"

            action_code = action_template.format(
                selector=selector_code,
                value=step.value or "",
                description=step.description,
            )

        return f"    // Step {step_number}: {step.description or step.action}\n{action_code}"

    def _generate_selector(self, selector: str, strategy: SelectorStrategy) -> str:
        """Generate Playwright selector code based on strategy."""
        # Detect and convert legacy/invalid selector formats
        selector = self._normalize_selector(selector)

        if not strategy:
            # Try to infer strategy from selector format
            strategy = self._infer_selector_strategy(selector)

        template = SELECTOR_TEMPLATES.get(strategy)
        if not template:
            # Default to CSS selector with .first()
            return f"page.locator('{selector}').first()"

        # Generate base selector
        base_selector = template.format(selector=selector)

        # Add .first() for potentially ambiguous selectors
        # Don't add for getByTestId (should be unique) or xpath with specific paths
        if strategy in [SelectorStrategy.TEXT, SelectorStrategy.CSS]:
            # These strategies often match multiple elements
            return f"{base_selector}.first()"

        return base_selector

    def _normalize_selector(self, selector: str) -> str:
        """Normalize legacy or invalid selector formats to valid Playwright syntax."""
        import re

        # Convert a:text('...') to proper getByRole format
        # Pattern: a:text('...') or a:text("...")
        text_link_match = re.match(r"a:text\(['\"](.+?)['\"]\)", selector)
        if text_link_match:
            # Return the text content - will be used with getByRole later
            return text_link_match.group(1)

        # Convert text=... to just the text (will use getByText)
        if selector.startswith('text='):
            return selector[5:]  # Remove 'text=' prefix

        return selector

    def _infer_selector_strategy(self, selector: str) -> SelectorStrategy:
        """Infer the best selector strategy based on selector format."""
        import re

        # Check for common patterns
        if selector.startswith('[data-testid'):
            return SelectorStrategy.TEST_ID
        elif selector.startswith('[aria-label'):
            return SelectorStrategy.ARIA_LABEL
        elif selector.startswith('//'):
            return SelectorStrategy.XPATH
        elif re.match(r'^[a-zA-Z\s]+$', selector) and not selector.startswith('.') and not selector.startswith('#'):
            # Plain text without CSS indicators
            return SelectorStrategy.TEXT
        else:
            # Default to CSS
            return SelectorStrategy.CSS

    def _save_spec_file(self, suite_id: str, content: str) -> Path:
        """Save the compiled spec to a file."""
        output_dir = Path(self.config.storage.test_specs_path) / "compiled"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{suite_id}.spec.ts"
        output_path.write_text(content)

        return output_path