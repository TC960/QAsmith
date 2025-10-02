"""Analyze page structure to extract elements, actions, and forms."""

from typing import List, Dict, Any, Optional
from playwright.async_api import Page
from backend.shared.types import PageElement, PageAction, ActionType, SelectorStrategy
import re


class PageAnalyzer:
    """Analyzes page structure to extract testable elements and actions."""

    async def extract_elements(self, page: Page) -> List[PageElement]:
        """Extract interactive elements from the page."""
        elements = []

        # Extract buttons
        buttons = await page.query_selector_all("button, input[type='button'], input[type='submit']")
        for btn in buttons:
            element = await self._create_element(btn, "button")
            if element:
                elements.append(element)

        # Extract links
        links = await page.query_selector_all("a[href]")
        for link in links:
            element = await self._create_element(link, "link")
            if element:
                elements.append(element)

        # Extract inputs
        inputs = await page.query_selector_all("input:not([type='button']):not([type='submit'])")
        for inp in inputs:
            element = await self._create_element(inp, "input")
            if element:
                elements.append(element)

        # Extract textareas
        textareas = await page.query_selector_all("textarea")
        for textarea in textareas:
            element = await self._create_element(textarea, "textarea")
            if element:
                elements.append(element)

        # Extract selects
        selects = await page.query_selector_all("select")
        for select in selects:
            element = await self._create_element(select, "select")
            if element:
                elements.append(element)

        return elements

    async def _create_element(self, locator, element_type: str) -> PageElement:
        """Create a PageElement from a Playwright locator."""
        try:
            # Try different selector strategies in order of preference
            test_id = await locator.get_attribute("data-testid")
            if test_id:
                return PageElement(
                    selector=f"[data-testid='{test_id}']",
                    selector_strategy=SelectorStrategy.TEST_ID,
                    element_type=element_type,
                    text=await locator.text_content(),
                    attributes=await self._get_attributes(locator),
                )

            aria_label = await locator.get_attribute("aria-label")
            if aria_label:
                return PageElement(
                    selector=aria_label,
                    selector_strategy=SelectorStrategy.ARIA_LABEL,
                    element_type=element_type,
                    text=await locator.text_content(),
                    attributes=await self._get_attributes(locator),
                )

            text = await locator.text_content()
            if text and text.strip():
                return PageElement(
                    selector=text.strip(),
                    selector_strategy=SelectorStrategy.TEXT,
                    element_type=element_type,
                    text=text.strip(),
                    attributes=await self._get_attributes(locator),
                )

            # Fall back to generating a CSS selector
            element_id = await locator.get_attribute("id")
            if element_id:
                selector = f"#{element_id}"
            else:
                class_name = await locator.get_attribute("class")
                if class_name:
                    selector = f".{class_name.split()[0]}"
                else:
                    name = await locator.get_attribute("name")
                    selector = f"[name='{name}']" if name else element_type

            return PageElement(
                selector=selector,
                selector_strategy=SelectorStrategy.CSS,
                element_type=element_type,
                text=await locator.text_content(),
                attributes=await self._get_attributes(locator),
            )
        except Exception as e:
            print(f"Error creating element: {e}")
            return None

    async def _get_attributes(self, locator) -> Dict[str, Any]:
        """Extract detailed attributes from an element (inspired by graph_redo)."""
        attrs = {}
        
        # Standard attributes
        standard_attrs = ["id", "name", "class", "type", "placeholder", "value", "href", 
                         "title", "alt", "rel", "target", "tabindex", "role"]
        
        for attr in standard_attrs:
            try:
                value = await locator.get_attribute(attr)
                if value:
                    attrs[attr] = value
            except:
                pass
        
        # Aria attributes for accessibility
        aria_attrs = ["aria-label", "aria-describedby", "aria-required", "aria-hidden", 
                     "aria-expanded", "aria-controls", "aria-checked"]
        
        for attr in aria_attrs:
            try:
                value = await locator.get_attribute(attr)
                if value:
                    attrs[attr] = value
            except:
                pass
        
        # JavaScript event handlers
        js_events = ["onclick", "onsubmit", "onchange", "onmousedown", "onmouseup", "ondblclick"]
        js_events_found = {}
        for event in js_events:
            try:
                value = await locator.get_attribute(event)
                if value:
                    js_events_found[event] = value[:200]  # Limit length
            except:
                pass
        
        if js_events_found:
            attrs["js_events"] = str(js_events_found)
        
        # Data attributes (custom data-* attributes)
        try:
            # Get all attributes using evaluate
            all_attrs = await locator.evaluate("""
                el => {
                    const dataAttrs = {};
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-')) {
                            dataAttrs[attr.name] = attr.value;
                        }
                    }
                    return dataAttrs;
                }
            """)
            if all_attrs:
                attrs["data_attributes"] = str(all_attrs)
        except:
            pass
        
        # Disabled state
        try:
            disabled = await locator.is_disabled()
            if disabled:
                attrs["disabled"] = "true"
        except:
            pass
        
        # Visible state
        try:
            visible = await locator.is_visible()
            attrs["visible"] = str(visible)
        except:
            pass
        
        return attrs

    async def extract_actions(self, page: Page) -> List[PageAction]:
        """Extract possible actions from the page."""
        actions = []

        # Click actions for buttons and links
        clickable = await page.query_selector_all("button, a[href], input[type='button'], input[type='submit']")
        for elem in clickable:
            element = await self._create_element(elem, "clickable")
            if element:
                text = element.text or element.attributes.get("value", "")
                actions.append(
                    PageAction(
                        action_type=ActionType.CLICK,
                        element=element,
                        description=f"Click {text or element.selector}",
                    )
                )

        # Fill actions for inputs and textareas
        fillable = await page.query_selector_all("input:not([type='button']):not([type='submit']), textarea")
        for elem in fillable:
            element = await self._create_element(elem, "input")
            if element:
                placeholder = element.attributes.get("placeholder", "")
                name = element.attributes.get("name", "")
                actions.append(
                    PageAction(
                        action_type=ActionType.FILL,
                        element=element,
                        description=f"Fill {name or placeholder or element.selector}",
                    )
                )

        return actions

    async def extract_forms(self, page: Page) -> List[Dict[str, Any]]:
        """Extract form structures from the page."""
        forms = []

        form_elements = await page.query_selector_all("form")
        for form_elem in form_elements:
            try:
                form_data = {
                    "action": await form_elem.get_attribute("action"),
                    "method": await form_elem.get_attribute("method") or "GET",
                    "fields": [],
                }

                # Extract form fields
                fields = await form_elem.query_selector_all("input, textarea, select")
                for field in fields:
                    field_type = await field.get_attribute("type") or "text"
                    field_name = await field.get_attribute("name")
                    if field_name:
                        form_data["fields"].append({
                            "name": field_name,
                            "type": field_type,
                            "required": await field.get_attribute("required") is not None,
                        })

                if form_data["fields"]:
                    forms.append(form_data)
            except Exception as e:
                print(f"Error extracting form: {e}")
                continue

        return forms
    
    async def extract_page_content(self, page: Page) -> Dict[str, Any]:
        """Extract FAST, lightweight page content for AI embeddings."""
        try:
            content_data = {}

            # Extract everything in ONE evaluate call for speed
            extracted = await page.evaluate("""
                () => {
                    // Title
                    const title = document.title || '';

                    // Meta description
                    const metaDesc = document.querySelector('meta[name="description"]')?.content || '';

                    // H1 tags only (most important)
                    const h1s = Array.from(document.querySelectorAll('h1'))
                        .map(h => h.textContent?.trim())
                        .filter(t => t);

                    // First 500 chars of visible text (MUCH faster than full body)
                    const mainContent = document.querySelector('main, article, [role="main"], body');
                    let text = mainContent?.textContent || '';
                    text = text.replace(/\\s+/g, ' ').trim().substring(0, 500);

                    return {
                        title,
                        meta_description: metaDesc,
                        h1_tags: h1s,
                        content_snippet: text
                    };
                }
            """)

            content_data = {
                "title": extracted.get("title", ""),
                "meta_description": extracted.get("meta_description", ""),
                "headers": {"h1": extracted.get("h1_tags", [])},
                "content_text": extracted.get("content_snippet", ""),
                "content_length": len(extracted.get("content_snippet", ""))
            }

            # Create embedding text (lightweight - just title, description, h1s, snippet)
            embedding_text_parts = [
                content_data.get("title", ""),
                content_data.get("meta_description", "")
            ]

            # Add h1 headers
            embedding_text_parts.extend(content_data["headers"].get("h1", []))

            # Add content snippet
            embedding_text_parts.append(content_data.get("content_text", ""))

            # Combine and clean
            embedding_text = " ".join([p for p in embedding_text_parts if p])
            embedding_text = re.sub(r'\s+', ' ', embedding_text).strip()

            content_data["embedding_text"] = embedding_text[:2000]  # Limit to 2000 chars (much faster)

            return content_data
            
        except Exception as e:
            print(f"❌ Error extracting page content: {e}")
            return {
                "title": "",
                "meta_description": "",
                "content_text": "",
                "headers": {},
                "content_length": 0,
                "embedding_text": ""
            }