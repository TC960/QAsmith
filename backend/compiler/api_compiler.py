"""Compile API test cases into Playwright API tests."""

import json
from pathlib import Path
from typing import List, Dict, Any
from backend.shared.config import get_config
from .api_templates import (
    API_TEST_FILE_TEMPLATE,
    API_TEST_CASE_TEMPLATE,
    API_ASSERTIONS,
    REQUEST_BODY_TEMPLATES,
    HEADER_TEMPLATE
)


class APITestCompiler:
    """Compiles API test cases into Playwright API test specs."""

    def __init__(self):
        self.config = get_config()

    def compile_api_tests(self, api_tests: List[Dict[str, Any]], base_url: str, suite_id: str) -> Path:
        """Compile API tests into Playwright spec file."""
        print(f"Compiling {len(api_tests)} API tests...")

        test_cases_code = []
        for test in api_tests:
            test_code = self._compile_api_test(test)
            test_cases_code.append(test_code)

        # Generate complete file
        file_content = API_TEST_FILE_TEMPLATE.format(
            base_url=base_url,
            test_cases="\n\n".join(test_cases_code)
        )

        # Save to file
        output_path = self._save_spec_file(suite_id, file_content)
        print(f"Compiled API spec saved to: {output_path}")

        return output_path

    def _compile_api_test(self, test: Dict[str, Any]) -> str:
        """Compile a single API test case."""
        method = test.get('method', 'get').lower()
        endpoint = test.get('endpoint', '/')
        expected_status = test.get('expected_status', 200)
        
        # Build request body
        request_body = ""
        if test.get('body'):
            body_type = test.get('body_type', 'json')
            template = REQUEST_BODY_TEMPLATES.get(body_type, REQUEST_BODY_TEMPLATES['json'])
            request_body = template.format(body=json.dumps(test['body'], indent=8))
        
        # Build headers
        request_headers = ""
        if test.get('headers'):
            content_type = test.get('headers', {}).get('Content-Type', 'application/json')
            additional = "\n".join([
                f"        '{k}': '{v}'," 
                for k, v in test.get('headers', {}).items() 
                if k != 'Content-Type'
            ])
            request_headers = HEADER_TEMPLATE.format(
                content_type=content_type,
                additional_headers=additional
            )
        
        # Build assertions
        assertions = []
        
        # Status assertion
        if expected_status == 200:
            assertions.append(API_ASSERTIONS['status_200'])
        elif expected_status == 201:
            assertions.append(API_ASSERTIONS['status_201'])
        elif expected_status == 400:
            assertions.append(API_ASSERTIONS['status_400'])
        elif expected_status == 401:
            assertions.append(API_ASSERTIONS['status_401'])
        elif expected_status == 404:
            assertions.append(API_ASSERTIONS['status_404'])
        else:
            assertions.append(f"    expect(response.status()).toBe({expected_status});")
        
        # Response body assertions
        if test.get('expected_body'):
            if isinstance(test['expected_body'], dict):
                for key in test['expected_body'].keys():
                    assertions.append(API_ASSERTIONS['json_schema'].format(property=key))
            elif test['expected_body'] == 'array':
                assertions.append(API_ASSERTIONS['array_length'])
        
        # Response time assertion (if specified)
        if test.get('max_response_time_ms'):
            assertions.append(f"    // Response time should be under {test['max_response_time_ms']}ms")
        
        return API_TEST_CASE_TEMPLATE.format(
            test_name=test.get('name', f'{method.upper()} {endpoint}'),
            test_description=test.get('description', f'Tests {method.upper()} {endpoint}'),
            method=method,
            endpoint=endpoint,
            request_body=request_body,
            request_headers=request_headers,
            assertions="\n".join(assertions)
        )

    def _save_spec_file(self, suite_id: str, content: str) -> Path:
        """Save the compiled API spec to a file."""
        output_dir = Path(self.config.storage.test_specs_path) / "compiled"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{suite_id}_api.spec.ts"
        output_path.write_text(content)

        return output_path

