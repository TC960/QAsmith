"""Generate logic/functional test cases for forms, APIs, and workflows."""

import json
from typing import List, Dict, Any
from anthropic import Anthropic
from backend.shared.types import AppMap, TestSuite, TestCase, TestStep, ActionType
from backend.shared.config import get_config
from backend.shared.utils import generate_id


class LogicTestGenerator:
    """Generate comprehensive logic tests for forms, APIs, and user workflows."""

    def __init__(self):
        self.config = get_config()
        self.client = Anthropic(api_key=self.config.llm.api_key)

    def generate_form_tests(self, app_map: AppMap) -> List[TestCase]:
        """Generate form validation tests (empty, invalid, valid inputs)."""
        test_cases = []
        
        for page in app_map.pages:
            if not page.forms:
                continue
            
            for form_idx, form in enumerate(page.forms):
                # Generate test for each form
                form_tests = self._generate_single_form_tests(page.url, form, form_idx)
                test_cases.extend(form_tests)
        
        return test_cases

    def _generate_single_form_tests(self, page_url: str, form: Dict[str, Any], form_idx: int) -> List[TestCase]:
        """Generate validation tests for a single form."""
        test_cases = []
        form_name = form.get('id', f'form_{form_idx}')
        
        # Test 1: Empty form submission
        empty_test_steps = [
            TestStep(
                action=ActionType.GOTO,
                url=str(page_url),
                description=f"Navigate to {page_url}"
            ),
            TestStep(
                action=ActionType.CLICK,
                selector=f"form#{form_name} button[type='submit']" if form.get('id') else "button[type='submit']",
                description="Submit empty form"
            ),
            TestStep(
                action=ActionType.EXPECT,
                selector=".error, .validation-error, [role='alert']",
                assertion="toBeVisible",
                description="Verify validation error appears"
            )
        ]
        
        test_cases.append(TestCase(
            test_id=generate_id("test_"),
            name=f"{form_name} - Empty Form Validation",
            description=f"Validates that {form_name} shows errors when submitted empty",
            tags=["logic", "validation", "negative"],
            steps=empty_test_steps,
            assertions=["Form validation errors are displayed"]
        ))
        
        # Test 2: Invalid input for each field
        for field in form.get('fields', []):
            if field.get('type') == 'email':
                invalid_test_steps = [
                    TestStep(
                        action=ActionType.GOTO,
                        url=str(page_url),
                        description=f"Navigate to {page_url}"
                    ),
                    TestStep(
                        action=ActionType.FILL,
                        selector=f"input[name='{field['name']}']",
                        value="invalid-email-format",
                        description=f"Enter invalid email in {field['name']}"
                    ),
                    TestStep(
                        action=ActionType.CLICK,
                        selector="button[type='submit']",
                        description="Submit form"
                    ),
                    TestStep(
                        action=ActionType.EXPECT,
                        selector=f".error, [data-field='{field['name']}'] .error",
                        assertion="toBeVisible",
                        description="Verify email validation error"
                    )
                ]
                
                test_cases.append(TestCase(
                    test_id=generate_id("test_"),
                    name=f"{form_name} - Invalid Email Validation",
                    description=f"Validates email field in {form_name} rejects invalid format",
                    tags=["logic", "validation", "email"],
                    steps=invalid_test_steps,
                    assertions=["Invalid email error is displayed"]
                ))
        
        # Test 3: Valid form submission
        valid_test_steps = [
            TestStep(
                action=ActionType.GOTO,
                url=str(page_url),
                description=f"Navigate to {page_url}"
            )
        ]
        
        # Fill each field with valid data
        for field in form.get('fields', []):
            field_type = field.get('type', 'text')
            
            # Generate valid test data based on field type
            test_value = self._generate_valid_test_data(field_type, field.get('name', ''))
            
            valid_test_steps.append(TestStep(
                action=ActionType.FILL,
                selector=f"input[name='{field['name']}']",
                value=test_value,
                description=f"Enter valid {field_type} in {field['name']}"
            ))
        
        valid_test_steps.append(TestStep(
            action=ActionType.CLICK,
            selector="button[type='submit']",
            description="Submit form with valid data"
        ))
        
        # Expect success (page change or success message)
        valid_test_steps.append(TestStep(
            action=ActionType.EXPECT,
            selector=".success, .confirmation, [role='status']",
            assertion="toBeVisible",
            description="Verify success message or redirect"
        ))
        
        test_cases.append(TestCase(
            test_id=generate_id("test_"),
            name=f"{form_name} - Valid Submission",
            description=f"Validates {form_name} accepts valid input and submits successfully",
            tags=["logic", "validation", "positive"],
            steps=valid_test_steps,
            assertions=["Form submits successfully", "Success feedback is displayed"]
        ))
        
        return test_cases

    def _generate_valid_test_data(self, field_type: str, field_name: str) -> str:
        """Generate realistic valid test data based on field type and name."""
        field_name_lower = field_name.lower()
        
        if field_type == 'email' or 'email' in field_name_lower:
            return "test.user@example.com"
        elif field_type == 'password' or 'password' in field_name_lower:
            return "SecurePass123!"
        elif field_type == 'tel' or 'phone' in field_name_lower:
            return "+1-555-123-4567"
        elif field_type == 'url' or 'website' in field_name_lower:
            return "https://example.com"
        elif field_type == 'number' or 'age' in field_name_lower:
            return "25"
        elif 'name' in field_name_lower:
            if 'first' in field_name_lower:
                return "John"
            elif 'last' in field_name_lower:
                return "Doe"
            else:
                return "John Doe"
        elif 'address' in field_name_lower:
            return "123 Main Street"
        elif 'city' in field_name_lower:
            return "New York"
        elif 'zip' in field_name_lower or 'postal' in field_name_lower:
            return "10001"
        else:
            return "Valid Test Input"

    def generate_workflow_tests(self, app_map: AppMap) -> List[TestCase]:
        """Generate multi-step workflow tests using AI."""
        workflow_prompt = f"""Analyze this website and generate realistic user workflow tests.

Website: {app_map.base_url}

Pages Available:
{self._format_pages_for_prompt(app_map.pages)}

Generate 3-5 realistic user workflow tests that span multiple pages. Examples:
- Signup → Login → Use feature → Logout
- Browse products → Add to cart → Checkout
- Search → Filter results → View details → Contact

For each workflow, provide:
1. Clear user journey name
2. Step-by-step actions with specific selectors
3. Validation at each step

Return ONLY valid JSON in this format:
{{
  "workflows": [
    {{
      "name": "User Signup and Login Flow",
      "description": "Tests complete user registration and authentication",
      "steps": [
        {{"action": "goto", "url": "/signup", "description": "Navigate to signup"}},
        {{"action": "fill", "selector": "input[name='email']", "value": "test@example.com"}},
        {{"action": "click", "selector": "button[type='submit']"}},
        {{"action": "expect", "selector": ".success", "assertion": "toBeVisible"}}
      ]
    }}
  ]
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.config.llm.model,
                max_tokens=self.config.llm.max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": workflow_prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            data = json.loads(json_str)
            workflows = data.get('workflows', [])
            
            # Convert to TestCase objects
            test_cases = []
            for workflow in workflows:
                steps = [
                    TestStep(
                        action=ActionType(step['action']),
                        selector=step.get('selector', ''),
                        value=step.get('value'),
                        url=step.get('url'),
                        assertion=step.get('assertion'),
                        description=step.get('description', '')
                    )
                    for step in workflow['steps']
                ]
                
                test_cases.append(TestCase(
                    test_id=generate_id("test_"),
                    name=workflow['name'],
                    description=workflow['description'],
                    tags=["workflow", "integration", "e2e"],
                    steps=steps,
                    assertions=[]
                ))
            
            return test_cases
            
        except Exception as e:
            print(f"Error generating workflow tests: {e}")
            return []

    def _format_pages_for_prompt(self, pages) -> str:
        """Format pages for AI prompt."""
        formatted = []
        for page in pages:
            page_info = f"- {page.url}: {page.title}"
            if page.forms:
                page_info += f" (has {len(page.forms)} form(s))"
            formatted.append(page_info)
        return "\n".join(formatted)

    def generate_api_tests(self, discovered_apis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate API tests from discovered endpoints."""
        api_tests = []
        
        for api in discovered_apis:
            # Test 1: Basic endpoint validation
            api_tests.append({
                'name': f"API {api['method']} {api['path']} - Success",
                'endpoint': api['path'],
                'method': api['method'],
                'expected_status': 200,
                'description': f"Validates {api['path']} returns success"
            })
            
            # Test 2: Error handling
            if api['method'] == 'POST':
                api_tests.append({
                    'name': f"API {api['method']} {api['path']} - Invalid Data",
                    'endpoint': api['path'],
                    'method': api['method'],
                    'body': {},  # Empty body
                    'expected_status': 400,
                    'description': f"Validates {api['path']} handles invalid input"
                })
        
        return api_tests

