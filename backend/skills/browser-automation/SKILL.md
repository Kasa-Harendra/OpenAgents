---
name: browser-automation
description: Automated browser control for web navigation, interaction, form filling, and data extraction using Playwright
license: MIT
compatibility: Requires Playwright browser tools
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: navigate_browser, click_element, fill_form, get_elements, screenshot
---

# browser-automation

## Overview

This skill provides step-by-step guidance for precise browser automation tasks. Use this skill for web navigation, element interaction, form filling, data extraction, and visual documentation. The skill emphasizes task precision and stopping immediately after completing the exact requested action.

## Core Principles

1. **PRECISION**: Execute ONLY the exact actions requested
2. **STOP IMMEDIATELY**: When the requested task is complete
3. **NO EXPLORATION**: Never click extra links or explore beyond instructions
4. **8-STEP LIMIT**: Maximum 8 actions per task to prevent runaway loops

## Instructions

### Step 1: Understand the Task

Parse the user's request to identify:

- **Exact actions needed** (navigate, click, fill, extract)
- **Target elements** (URLs, selectors, form fields)
- **Stopping condition** (when the task is complete)
- **Expected output** (data, screenshot, confirmation)

**Self-check**: "What is the minimum set of actions to complete this task?"

---

### Step 2: Navigate to Target Page

Use `navigate_browser` to open the URL:

- Provide full URL including protocol (https://)
- Wait for page load completion
- Verify successful navigation

**Example**:

```json
{
  "tool": "navigate_browser",
  "params": {
    "url": "https://example.com"
  }
}
```

---

### Step 3: Execute Required Actions

Based on task type, use appropriate tools:

#### For Clicking Elements:

```json
{
  "tool": "click_element",
  "params": {
    "selector": "button.submit-btn",
    "description": "Submit button"
  }
}
```

#### For Filling Forms:

```json
{
  "tool": "fill_form",
  "params": {
    "selector": "input[name='email']",
    "text": "user@example.com"
  }
}
```

#### For Extracting Data:

```json
{
  "tool": "get_elements",
  "params": {
    "selector": "h1.title",
    "attributes": ["textContent"]
  }
}
```

#### For Visual Documentation:

```json
{
  "tool": "screenshot",
  "params": {
    "path": "screenshot.png"
  }
}
```

---

### Step 4: Validate Completion

After each action, check:

- ✅ Did the action succeed?
- ✅ Is the exact requested task now complete?
- ✅ Do I need to perform any more actions?

**If task is complete**: Proceed to Step 5
**If more actions needed**: Repeat Step 3 (max 8 total steps)

---

### Step 5: Stop and Report

Once the requested task is complete:

1. **STOP immediately** - do not perform additional actions
2. **Report clearly** what was accomplished
3. **Include relevant data** extracted or actions performed

**Report Format**:

```
Task complete. [Brief description of what was accomplished]

Actions performed:
1. Navigated to [URL]
2. [Action 2]
3. [Action 3]

Result: [Data extracted / Confirmation / Screenshot saved]
```

---

## Common Patterns

### Pattern 1: Simple Navigation

**Request**: "Open example.com"
**Actions**:

1. Navigate to https://example.com
2. STOP

### Pattern 2: Single Data Extraction

**Request**: "Get the title from example.com"
**Actions**:

1. Navigate to https://example.com
2. Extract h1 text using get_elements
3. STOP

### Pattern 3: Form Submission

**Request**: "Fill login form on example.com with email test@test.com"
**Actions**:

1. Navigate to https://example.com/login
2. Fill email field with test@test.com
3. STOP (do NOT click submit unless explicitly requested)

### Pattern 4: Multi-Step Workflow (Use with Caution)

**Request**: "Login to example.com with email and password"
**Actions**:

1. Navigate to https://example.com/login
2. Fill email field
3. Fill password field
4. Click submit button
5. Wait for redirect
6. STOP

---

## Anti-Patterns (What NOT to Do)

❌ **Over-Execution**:

- Request: "Open example.com"
- Bad: Navigate → Click links → Fill forms → Explore
- Good: Navigate → STOP

❌ **Assumption**:

- Request: "Fill email field"
- Bad: Fill email AND click submit
- Good: Fill email → STOP

❌ **Endless Loop**:

- Clicking through pagination endlessly
- Following every link on a page
- Solution: Use 8-step limit

---

## Error Handling

### Element Not Found

- Retry with different selector
- Check if page fully loaded
- Report to user if element doesn't exist

### Navigation Failed

- Verify URL format
- Check internet connection
- Try alternative URL

### Timeout

- Increase wait time for slow pages
- Report timeout to user
- Suggest manual verification

---

## Best Practices

1. **Use Specific Selectors**: Prefer IDs and unique classes over generic tags
2. **Wait for Elements**: Ensure page loads before interactions
3. **Verify Actions**: Check that clicks/fills succeeded
4. **Stay Focused**: Complete only the requested task
5. **Report Clearly**: Provide actionable feedback

---

## Examples

### Example 1: Extract Product Pricing

**Request**: "Get pricing from openai.com/pricing"

**Execution**:

```
Step 1: Navigate to https://openai.com/pricing
Step 2: Use get_elements with selector ".pricing-card"
Step 3: Extract price data
Step 4: STOP

Result:
- Free Plan: $0/month
- Plus Plan: $20/month
- Team Plan: $30/user/month
Source: openai.com/pricing
```

### Example 2: Simple Screenshot

**Request**: "Take screenshot of google.com"

**Execution**:

```
Step 1: Navigate to https://google.com
Step 2: Use screenshot tool
Step 3: STOP

Result: Screenshot saved to screenshot.png
```

### Example 3: Login Flow

**Request**: "Login to example.com with email: user@test.com, password: pass123"

**Execution**:

```
Step 1: Navigate to https://example.com/login
Step 2: Fill input[type='email'] with user@test.com
Step 3: Fill input[type='password'] with pass123
Step 4: Click button[type='submit']
Step 5: Wait for navigation
Step 6: STOP

Result: Successfully logged in to example.com
```

---

## Troubleshooting

**Q: Agent keeps clicking extra links**
**A**: Emphasize stopping condition in request. Use phrases like "ONLY navigate" or "extract data and STOP"

**Q: Timeout errors on slow pages**
**A**: Add explicit wait steps or increase timeout parameters

**Q: Can't find element**
**A**: Use browser dev tools to verify selector, try alternative selectors (ID, class, XPath)

**Q: Task taking too long**
**A**: Check if hitting 8-step limit, simplify task or break into smaller requests
