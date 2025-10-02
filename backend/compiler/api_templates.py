"""Templates for Playwright API testing (backend logic tests)."""

# API Test File Template (no browser needed)
API_TEST_FILE_TEMPLATE = """import {{ test, expect }} from '@playwright/test';

test.describe('API Tests - {base_url}', () => {{

{test_cases}

}});
"""

# Individual API test template
API_TEST_CASE_TEMPLATE = """  test('{test_name}', async ({{ request }}) => {{
    // {test_description}
    
    const response = await request.{method}('{endpoint}', {{
{request_body}
{request_headers}
    }});
    
{assertions}
  }});"""

# Common API assertions
API_ASSERTIONS = {
    'status_200': "    expect(response.ok()).toBeTruthy();\n    expect(response.status()).toBe(200);",
    'status_201': "    expect(response.status()).toBe(201);",
    'status_400': "    expect(response.status()).toBe(400);",
    'status_401': "    expect(response.status()).toBe(401);",
    'status_404': "    expect(response.status()).toBe(404);",
    'status_500': "    expect(response.status()).toBe(500);",
    'response_time': "    expect(response.headers()['x-response-time']).toBeDefined();",
    'json_schema': """    const body = await response.json();
    expect(body).toHaveProperty('{property}');""",
    'array_length': """    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
    expect(body.length).toBeGreaterThan(0);""",
}

# Request body templates
REQUEST_BODY_TEMPLATES = {
    'json': """      data: {body}""",
    'form': """      form: {body}""",
    'multipart': """      multipart: {body}""",
}

# Header templates
HEADER_TEMPLATE = """      headers: {{
        'Content-Type': '{content_type}',
{additional_headers}
      }}"""

