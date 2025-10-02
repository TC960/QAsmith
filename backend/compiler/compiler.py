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
        elif step.action == ActionType.EXPECT:
            # Format selector - escape single quotes
            escaped_selector = step.selector.replace("'", "\\'") if step.selector else ""
            selector_code = f"page.locator('{escaped_selector}')" if step.selector else "page"
            # Format assertion value
            escaped_value = step.value.replace("'", "\\'") if step.value else ""
            value_str = f"'{escaped_value}'" if step.value else ""
            if not value_str and step.assertion in ['toBeVisible', 'toBeHidden', 'toBeEnabled', 'toBeDisabled']:
                value_str = ""  # No value needed for these assertions
            action_code = action_template.format(
                selector=selector_code,
                assertion=step.assertion or "toBeVisible",
                value=value_str
            )
        else:
            # Regular actions with selectors - escape quotes
            if step.selector:
                escaped_selector = step.selector.replace("'", "\\'")
                if step.selector_strategy:
                    selector_code = self._generate_selector(escaped_selector, step.selector_strategy)
                else:
                    selector_code = f"page.locator('{escaped_selector}')"
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
        if not strategy:
            return f"page.locator('{selector}')"  # Default to CSS selector

        template = SELECTOR_TEMPLATES.get(strategy)
        if not template:
            return f"page.locator('{selector}')"  # Default to CSS selector

        return template.format(selector=selector)

    def _save_spec_file(self, suite_id: str, content: str) -> Path:
        """Save the compiled spec to a file."""
        output_dir = Path(self.config.storage.test_specs_path) / "compiled"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{suite_id}.spec.ts"
        output_path.write_text(content)

        return output_path