"""Execute Playwright tests and collect artifacts."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional
from backend.shared.types import TestRunResult, TestResult, TestStatus
from backend.shared.config import get_config
from backend.shared.utils import generate_id, get_timestamp, save_json


class TestRunner:
    """Executes Playwright test specs and collects artifacts."""

    def __init__(self):
        self.config = get_config()

    async def run_tests(self, spec_path: Path, suite_id: str) -> TestRunResult:
        """Run Playwright tests and collect results."""
        print(f"Running tests from: {spec_path}")

        run_id = generate_id("run_")
        artifacts_dir = Path(self.config.storage.artifacts_path) / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Prepare Playwright config
        playwright_config = self._create_playwright_config(artifacts_dir)
        config_path = artifacts_dir / "playwright.config.ts"
        config_path.write_text(playwright_config)

        # Run Playwright
        start_time = asyncio.get_event_loop().time()
        results = await self._execute_playwright(spec_path, config_path, artifacts_dir)
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

        # Parse results
        test_results = self._parse_results(artifacts_dir)

        # Create test run result
        test_run = TestRunResult(
            run_id=run_id,
            suite_id=suite_id,
            timestamp=get_timestamp(),
            total=len(test_results),
            passed=sum(1 for r in test_results if r.status == TestStatus.PASSED),
            failed=sum(1 for r in test_results if r.status == TestStatus.FAILED),
            skipped=sum(1 for r in test_results if r.status == TestStatus.SKIPPED),
            duration_ms=duration_ms,
            results=test_results,
            junit_xml_path=str(artifacts_dir / "results.xml"),
            html_report_path=str(artifacts_dir / "html-report" / "index.html"),
        )

        # Save results
        self._save_results(test_run, artifacts_dir)

        print(f"Test run complete: {test_run.passed} passed, {test_run.failed} failed")
        return test_run

    def _create_playwright_config(self, artifacts_dir: Path) -> str:
        """Generate Playwright configuration."""
        # Get timeout from config, default to 60000ms (60s)
        timeout = getattr(self.config.runner, 'timeout', 60000)

        config = f"""
import {{ defineConfig, devices }} from '@playwright/test';

export default defineConfig({{
  testDir: '.',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  timeout: {timeout},
  reporter: [
    ['html', {{ outputFolder: '{artifacts_dir}/html-report' }}],
    ['junit', {{ outputFile: '{artifacts_dir}/results.xml' }}],
    ['json', {{ outputFile: '{artifacts_dir}/results.json' }}],
  ],
  use: {{
    baseURL: 'http://localhost:3000',
    trace: '{self.config.runner.trace and "on" or "off"}',
    video: '{self.config.runner.video and "on" or "off"}',
    screenshot: '{self.config.runner.screenshot}',
    actionTimeout: {timeout // 2},
    navigationTimeout: {timeout // 2},
  }},
  projects: [
    {{
      name: '{self.config.runner.browser}',
      use: {{ ...devices['Desktop Chrome'] }},
    }},
  ],
}});
"""
        return config

    async def _execute_playwright(
        self, spec_path: Path, config_path: Path, artifacts_dir: Path
    ) -> subprocess.CompletedProcess:
        """Execute Playwright via subprocess."""
        cmd = [
            "npx",
            "playwright",
            "test",
            str(spec_path),
            "--config",
            str(config_path),
        ]

        if self.config.runner.headless:
            cmd.append("--headed=false")

        try:
            result = subprocess.run(
                cmd,
                cwd=artifacts_dir.parent,
                capture_output=True,
                text=True,
            )
            return result
        except Exception as e:
            print(f"Error executing Playwright: {e}")
            raise

    def _parse_results(self, artifacts_dir: Path) -> list[TestResult]:
        """Parse Playwright JSON results."""
        results_json = artifacts_dir / "results.json"

        if not results_json.exists():
            print("No results JSON found")
            return []

        try:
            with open(results_json, "r") as f:
                data = json.load(f)

            test_results = []
            for suite in data.get("suites", []):
                for spec in suite.get("specs", []):
                    for test in spec.get("tests", []):
                        result = test.get("results", [{}])[0]

                        status_map = {
                            "passed": TestStatus.PASSED,
                            "failed": TestStatus.FAILED,
                            "skipped": TestStatus.SKIPPED,
                        }

                        test_results.append(
                            TestResult(
                                test_id=test.get("testId", "unknown"),
                                status=status_map.get(result.get("status"), TestStatus.FAILED),
                                duration_ms=result.get("duration", 0),
                                error_message=result.get("error", {}).get("message"),
                                screenshot_path=None,  # TODO: Extract from attachments
                                trace_path=None,  # TODO: Extract from attachments
                                video_path=None,  # TODO: Extract from attachments
                            )
                        )

            return test_results
        except Exception as e:
            print(f"Error parsing results: {e}")
            return []

    def _save_results(self, test_run: TestRunResult, artifacts_dir: Path) -> None:
        """Save test run results."""
        results_path = artifacts_dir / "test_run.json"
        save_json(test_run.model_dump(), results_path)
        print(f"Results saved to: {results_path}")