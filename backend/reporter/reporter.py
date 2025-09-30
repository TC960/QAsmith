"""Generate HTML reports with AI-powered failure summaries."""

from pathlib import Path
from typing import List
from anthropic import Anthropic
from backend.shared.types import TestRunResult, TestResult, TestStatus
from backend.shared.config import get_config
from .template import HTML_REPORT_TEMPLATE


class Reporter:
    """Generates rich HTML reports with AI-generated failure summaries."""

    def __init__(self):
        self.config = get_config()
        self.client = Anthropic(api_key=self.config.llm.api_key)

    def generate_report(self, test_run: TestRunResult) -> Path:
        """Generate HTML report for test run."""
        print("Generating HTML report...")

        # Generate AI summaries for failures
        failure_summaries = self._generate_failure_summaries(test_run.results)

        # Generate report HTML
        html_content = self._generate_html(test_run, failure_summaries)

        # Save report
        report_path = self._save_report(test_run.run_id, html_content)

        print(f"Report generated: {report_path}")
        return report_path

    def _generate_failure_summaries(self, results: List[TestResult]) -> dict[str, str]:
        """Generate AI summaries for failed tests."""
        summaries = {}

        failed_tests = [r for r in results if r.status == TestStatus.FAILED]
        if not failed_tests:
            return summaries

        print(f"Generating AI summaries for {len(failed_tests)} failed tests...")

        for result in failed_tests:
            if not result.error_message:
                continue

            try:
                summary = self._generate_single_summary(result)
                summaries[result.test_id] = summary
            except Exception as e:
                print(f"Error generating summary for {result.test_id}: {e}")
                summaries[result.test_id] = "Failed to generate summary"

        return summaries

    def _generate_single_summary(self, result: TestResult) -> str:
        """Generate AI summary for a single failure."""
        prompt = f"""Analyze this test failure and provide a concise summary of:
1. What went wrong
2. Possible root cause
3. Suggested fix

Test ID: {result.test_id}
Error: {result.error_message}

Provide a brief, actionable summary (2-3 sentences)."""

        response = self.client.messages.create(
            model=self.config.llm.model,
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _generate_html(self, test_run: TestRunResult, failure_summaries: dict[str, str]) -> str:
        """Generate HTML content for report."""
        # Summary stats
        pass_rate = (test_run.passed / test_run.total * 100) if test_run.total > 0 else 0

        # Generate test results HTML
        results_html = []
        for result in test_run.results:
            status_class = result.status.value
            status_emoji = {
                TestStatus.PASSED: "✓",
                TestStatus.FAILED: "✗",
                TestStatus.SKIPPED: "⊘",
            }.get(result.status, "?")

            error_html = ""
            if result.status == TestStatus.FAILED:
                ai_summary = failure_summaries.get(result.test_id, "No summary available")
                error_html = f"""
                    <div class="error-details">
                        <h4>AI Analysis</h4>
                        <p>{ai_summary}</p>
                        <h4>Error Message</h4>
                        <pre>{result.error_message or 'No error message'}</pre>
                    </div>
                """

            result_html = f"""
                <div class="test-result {status_class}">
                    <div class="result-header">
                        <span class="status-icon">{status_emoji}</span>
                        <span class="test-name">{result.test_id}</span>
                        <span class="duration">{result.duration_ms}ms</span>
                    </div>
                    {error_html}
                </div>
            """
            results_html.append(result_html)

        # Render template
        html = HTML_REPORT_TEMPLATE.format(
            run_id=test_run.run_id,
            timestamp=test_run.timestamp,
            total=test_run.total,
            passed=test_run.passed,
            failed=test_run.failed,
            skipped=test_run.skipped,
            pass_rate=f"{pass_rate:.1f}",
            duration=test_run.duration_ms,
            results_html="\n".join(results_html),
        )

        return html

    def _save_report(self, run_id: str, html_content: str) -> Path:
        """Save HTML report to file."""
        report_dir = Path(self.config.storage.reports_path) / run_id
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / "report.html"
        report_path.write_text(html_content)

        return report_path