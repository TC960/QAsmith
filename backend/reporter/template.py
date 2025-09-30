"""HTML template for test reports."""

HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {run_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #fafafa;
            border-bottom: 1px solid #eee;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat.passed .stat-value {{ color: #10b981; }}
        .stat.failed .stat-value {{ color: #ef4444; }}
        .stat.skipped .stat-value {{ color: #f59e0b; }}

        .results {{
            padding: 30px;
        }}

        .results h2 {{
            margin-bottom: 20px;
            font-size: 22px;
            color: #333;
        }}

        .test-result {{
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            margin-bottom: 15px;
            overflow: hidden;
        }}

        .result-header {{
            display: flex;
            align-items: center;
            padding: 15px;
            background: #fff;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .result-header:hover {{
            background: #f9fafb;
        }}

        .status-icon {{
            font-size: 20px;
            margin-right: 12px;
            width: 24px;
            text-align: center;
        }}

        .test-name {{
            flex: 1;
            font-weight: 500;
        }}

        .duration {{
            color: #6b7280;
            font-size: 14px;
        }}

        .test-result.passed .result-header {{
            border-left: 4px solid #10b981;
        }}

        .test-result.failed .result-header {{
            border-left: 4px solid #ef4444;
        }}

        .test-result.skipped .result-header {{
            border-left: 4px solid #f59e0b;
        }}

        .error-details {{
            padding: 15px;
            background: #fef2f2;
            border-top: 1px solid #fee2e2;
        }}

        .error-details h4 {{
            color: #991b1b;
            margin-bottom: 8px;
            font-size: 14px;
        }}

        .error-details p {{
            color: #7f1d1d;
            margin-bottom: 15px;
            line-height: 1.5;
        }}

        .error-details pre {{
            background: white;
            border: 1px solid #fecaca;
            border-radius: 4px;
            padding: 12px;
            overflow-x: auto;
            font-size: 13px;
            color: #991b1b;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Report</h1>
            <div class="meta">
                <div>Run ID: {run_id}</div>
                <div>Generated: {timestamp}</div>
            </div>
        </div>

        <div class="summary">
            <div class="stat">
                <div class="stat-value">{total}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat passed">
                <div class="stat-value">{passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat failed">
                <div class="stat-value">{failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat skipped">
                <div class="stat-value">{skipped}</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat">
                <div class="stat-value">{pass_rate}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
            <div class="stat">
                <div class="stat-value">{duration}ms</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>

        <div class="results">
            <h2>Test Results</h2>
            {results_html}
        </div>

        <div class="footer">
            Generated by QAsmith - AI-Powered E2E Testing
        </div>
    </div>
</body>
</html>"""