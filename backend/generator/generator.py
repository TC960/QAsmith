"""Generate test cases from app map using Claude."""

import json
from pathlib import Path
from anthropic import Anthropic
from backend.shared.types import AppMap, TestSuite, TestCase
from backend.shared.config import get_config
from backend.shared.utils import generate_id, save_json
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class TestGenerator:
    """Generate test cases from application map using Claude LLM."""

    def __init__(self):
        self.config = get_config()
        self.client = Anthropic(api_key=self.config.llm.api_key)

    def generate_tests(self, app_map: AppMap) -> TestSuite:
        """Generate test suite from app map."""
        print("Generating test cases with Claude...")

        # Prepare app map summary for the LLM
        app_map_summary = self._create_app_map_summary(app_map)

        # Call Claude
        response = self.client.messages.create(
            model=self.config.llm.model,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        base_url=app_map.base_url,
                        app_map_summary=app_map_summary,
                    ),
                }
            ],
        )

        # Parse response
        test_cases = self._parse_response(response.content[0].text)

        # Create test suite
        suite_id = generate_id("suite_")
        test_suite = TestSuite(
            suite_id=suite_id,
            name=f"Test Suite for {app_map.base_url}",
            base_url=app_map.base_url,
            test_cases=test_cases,
        )

        # Save test suite
        self._save_test_suite(test_suite)

        print(f"Generated {len(test_cases)} test cases")
        return test_suite

    def _create_app_map_summary(self, app_map: AppMap) -> str:
        """Create a concise summary of the app map for the LLM."""
        summary_parts = []

        for i, page in enumerate(app_map.pages, 1):
            page_summary = f"\nPage {i}: {page.url}\n"
            page_summary += f"Title: {page.title}\n"

            if page.forms:
                page_summary += "Forms:\n"
                for i, form in enumerate(page.forms, 1):
                    fields = ", ".join([f["name"] for f in form["fields"]])
                    # Include form selector if available for specificity
                    form_id = form.get("id", "")
                    form_selector = f"#{form_id}" if form_id else form.get("selector", "form")
                    page_summary += f"  - Form {i} (selector: {form_selector}): {form['method']} with fields: {fields}\n"

            if page.actions:
                page_summary += f"Actions ({len(page.actions)}):\n"
                # Limit to first 10 actions to avoid token limits
                for action in page.actions[:10]:
                    selector_info = f" (selector: {action.element.selector}, strategy: {action.element.selector_strategy.value})" if action.element.selector else ""
                    page_summary += f"  - {action.description}{selector_info}\n"

            summary_parts.append(page_summary)

        return "\n".join(summary_parts)

    def _parse_response(self, response_text: str) -> list[TestCase]:
        """Parse Claude's response into TestCase objects."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            # Parse JSON
            test_cases_data = json.loads(json_str)

            # Convert to TestCase objects
            test_cases = []
            if isinstance(test_cases_data, dict) and "test_cases" in test_cases_data:
                test_cases_data = test_cases_data["test_cases"]

            for tc_data in test_cases_data:
                test_cases.append(TestCase(**tc_data))

            return test_cases

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response: {response_text}")
            return []

    def _save_test_suite(self, test_suite: TestSuite) -> None:
        """Save test suite to file."""
        output_path = Path(self.config.storage.test_specs_path) / f"{test_suite.suite_id}.json"
        save_json(test_suite.model_dump(), output_path)
        print(f"Test suite saved to: {output_path}")