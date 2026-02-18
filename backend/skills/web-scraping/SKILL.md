---
name: web-scraping
description: Fast data extraction from web pages using crawl4ai for text, tables, structured content, and pricing information
license: MIT
compatibility: Requires internet access and crawl4ai library
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: scrape_url
---

# web-scraping

## Overview

This skill provides guidance for efficient web scraping using crawl4ai. Use this for pure data extraction from web pages without browser interaction - ideal for fetching text, tables, pricing, documentation, articles, and structured content.

## Core Principles

1. **Pure Extraction**: For data retrieval, NOT browser interaction
2. **Fast & Efficient**: No browser overhead, faster than automation
3. **Clean Output**: Convert HTML to structured Markdown
4. **Specific Targeting**: Use prompts to extract specific elements
5. **Source Attribution**: Always include source URL

## When to Use This Skill

### ✅ Use Web Scraping For:

- Extracting text content from pages
- Scraping product pricing tables
- Fetching documentation or articles
- Downloading structured data (lists, tables)
- Quick data retrieval without complex interactions

### ❌ Don't Use Web Scraping For:

- Clicking buttons or filling forms → Use browser-automation
- Multi-step workflows requiring interaction → Use browser-automation
- JavaScript-heavy dynamic content → Use browser-automation
- Authentication flows → Use browser-automation

---

## Instructions

### Step 1: Identify Target Data

Parse the user request to determine:

- **URL**: Web page to scrape
- **Data type**: What to extract (text, table, pricing, list)
- **Specificity**: General scrape or targeted extraction

**Examples**:

- "Extract pricing from openai.com/pricing" → Pricing table
- "Get article text from blog.com/post" → Article content
- "Scrape FAQ section from website.com" → Specific section

---

### Step 2: Choose Scraping Strategy

#### Strategy A: General Scrape (No Prompt)

For entire page content:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://example.com/page"
  }
}
```

**Returns**: Full page converted to clean Markdown

---

#### Strategy B: Targeted Scrape (With Prompt)

For specific elements:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://example.com/pricing",
    "prompt": "Extract the pricing table with plan names and prices"
  }
}
```

**Returns**: Only the requested data in structured format

---

### Step 3: Execute Scrape

Make the scraping request:

**Basic Scrape**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://docs.example.com/api"
  }
}
```

**Targeted Scrape**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://shop.example.com/products",
    "prompt": "Extract product names, prices, and availability status"
  }
}
```

---

### Step 4: Format Output

Present scraped data in clean, structured format:

#### Text Content

```markdown
# [Page Title]

[Main content in Markdown format]

Source: [URL]
Scraped: [timestamp]
```

#### Tables

```markdown
## Pricing Plans

| Plan | Price  | Features    |
| ---- | ------ | ----------- |
| Free | $0/mo  | 10 requests |
| Pro  | $20/mo | Unlimited   |

Source: https://example.com/pricing
```

#### Lists

```markdown
## Product Catalog

1. **Product A** - $99.99 (In Stock)
2. **Product B** - $149.99 (Out of Stock)
3. **Product C** - $79.99 (In Stock)

Source: https://example.com/products
```

---

### Step 5: Verify and Report

Check scraped output:

- ✅ Data successfully extracted?
- ✅ Format is clean and readable?
- ✅ Relevant information captured?
- ✅ Source URL included?

**If successful**: Present formatted data
**If failed**: Report error with suggestions

---

## Scraping Examples

### Example 1: Extract Pricing Table

**Request**: "Scrape pricing from openai.com/pricing"

**Execution**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://openai.com/pricing",
    "prompt": "Extract all pricing plans with names, prices, and key features"
  }
}
```

**Output**:

```markdown
## OpenAI Pricing Plans

### Free Tier

- **Price**: $0/month
- **Features**:
  - Limited API access
  - Community support
  - Basic models

### Plus Plan

- **Price**: $20/month
- **Features**:
  - Priority access
  - Faster response times
  - Advanced models

### Enterprise

- **Price**: Custom pricing
- **Features**:
  - Dedicated support
  - Custom solutions
  - Volume discounts

Source: https://openai.com/pricing
Scraped: 2026-02-13 23:00:00
```

---

### Example 2: Extract Article Content

**Request**: "Get the main article from blog.example.com/post-123"

**Execution**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://blog.example.com/post-123",
    "prompt": "Extract the article title and main content, exclude ads and sidebar"
  }
}
```

**Output**:

```markdown
# How to Build Web Scrapers in Python

Web scraping is the process of extracting data from websites programmatically. In this guide, we'll explore how to build efficient web scrapers using Python.

## Introduction

[Article content here...]

## Getting Started

[Article content here...]

## Best Practices

[Article content here...]

---

Source: https://blog.example.com/post-123
Author: John Doe
Published: 2026-01-15
```

---

### Example 3: Scrape Product Listings

**Request**: "Extract product names and prices from shop.com/electronics"

**Execution**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://shop.com/electronics",
    "prompt": "Extract product names, prices, and ratings"
  }
}
```

**Output**:

```markdown
## Electronics Products

1. **Wireless Headphones XL**
   - Price: $149.99
   - Rating: ⭐⭐⭐⭐⭐ (4.8/5)

2. **Smart Watch Pro**
   - Price: $299.99
   - Rating: ⭐⭐⭐⭐ (4.5/5)

3. **Bluetooth Speaker Mini**
   - Price: $79.99
   - Rating: ⭐⭐⭐⭐⭐ (4.9/5)

Source: https://shop.com/electronics
Total products: 3
```

---

## Prompting Strategies

### Generic Prompts

```
"Extract all text content"
"Get the main article"
"Scrape the entire page"
```

### Specific Prompts

```
"Extract only the pricing table with plan names and monthly costs"
"Get product descriptions excluding reviews and ads"
"Scrape FAQ section questions and answers in Q&A format"
```

### Structured Prompts

```
"Extract in the following format:
- Product name
- Price
- Availability
- Customer rating"
```

---

## Data Type Patterns

### Pattern 1: Pricing Information

**URL**: Pricing pages, subscription plans
**Prompt**: "Extract plan names, prices, and key features"
**Output**: Table or structured list

### Pattern 2: Documentation

**URL**: API docs, technical guides
**Prompt**: "Extract endpoint descriptions and parameters"
**Output**: Markdown with code blocks

### Pattern 3: News/Articles

**URL**: Blog posts, news articles
**Prompt**: "Extract title, author, date, and main content"
**Output**: Clean article text

### Pattern 4: Product Catalogs

**URL**: E-commerce listings
**Prompt**: "Extract product names, prices, and availability"
**Output**: Structured product list

### Pattern 5: FAQs

**URL**: Help centers, support pages
**Prompt**: "Extract questions and answers in Q&A format"
**Output**: Q&A markdown list

---

## Error Handling

### Error 1: Page Not Accessible

**Response**:

```
❌ Unable to access page

URL: https://example.com/page
Error: HTTP 404 Not Found

Explanation:
The requested page doesn't exist or has been moved.

Suggested Fix:
- Verify the URL is correct
- Check if the page still exists
- Try alternative URL or archived version
```

---

### Error 2: Rate Limiting

**Response**:

```
❌ Rate limit exceeded

URL: https://api.example.com/data
Error: HTTP 429 Too Many Requests

Explanation:
The website is blocking requests due to rate limiting.

Suggested Fix:
- Wait before retrying (suggested: 60 seconds)
- Use API access if available
- Contact website for rate limit increase
```

---

### Error 3: JavaScript Content Not Loading

**Response**:

```
⚠️ Partial content retrieved

URL: https://dynamic.example.com
Note: Page uses heavy JavaScript for content rendering

Scraped Content:
[Limited static content here]

Suggestion:
This page requires JavaScript execution.
Consider using browser-automation skill instead for full content extraction.
```

---

## Best Practices

1. **Respect robots.txt**: Check website's scraping policy
2. **Rate limiting**: Don't overwhelm servers with requests
3. **Specific prompts**: Target exactly what you need
4. **Clean output**: Format in readable Markdown
5. **Source attribution**: Always include source URL
6. **Error handling**: Report clear errors with fixes
7. **Choose right tool**: Scraping for data, automation for interaction

---

## Web Scraping vs Browser Automation

| Aspect           | Web Scraping         | Browser Automation       |
| ---------------- | -------------------- | ------------------------ |
| **Speed**        | ⚡ Fast (no browser) | 🐌 Slower (full browser) |
| **Use Case**     | Data extraction      | Interaction & workflows  |
| **JavaScript**   | ❌ Limited support   | ✅ Full support          |
| **Forms/Clicks** | ❌ Not supported     | ✅ Supported             |
| **Best For**     | Static content, APIs | Dynamic SPAs, auth flows |

**Decision Rule**:

- Need to click/fill/interact? → **browser-automation**
- Just extracting data? → **web-scraping**

---

## Advanced Example: Multi-Section Extraction

**Request**: "Extract pricing, features, and FAQs from product page"

**Execution**:

```json
{
  "tool": "scrape_url",
  "params": {
    "url": "https://saas.example.com/product",
    "prompt": "Extract three sections: 1) Pricing plans with prices, 2) Key features list, 3) Common FAQs"
  }
}
```

**Output**:

```markdown
# Product Name Pro

## Pricing Plans

| Plan       | Price  | Best For      |
| ---------- | ------ | ------------- |
| Basic      | $29/mo | Individuals   |
| Pro        | $99/mo | Teams         |
| Enterprise | Custom | Organizations |

## Key Features

- ✅ Real-time collaboration
- ✅ Advanced analytics dashboard
- ✅ 24/7 customer support
- ✅ API access
- ✅ Custom integrations

## Frequently Asked Questions

**Q: Is there a free trial?**
A: Yes, all plans include a 14-day free trial.

**Q: Can I change plans later?**
A: Yes, you can upgrade or downgrade anytime.

**Q: What payment methods are accepted?**
A: We accept credit cards, PayPal, and bank transfers.

---

Source: https://saas.example.com/product
Sections extracted: 3 (Pricing, Features, FAQs)
```

---

## Troubleshooting

**Q: Getting empty or minimal content**
**A**: Page likely uses JavaScript. Switch to browser-automation skill

**Q: Scraping returns too much irrelevant content**
**A**: Use more specific prompt to target exact elements needed

**Q: Table formatting is messy**
**A**: Specify desired format in prompt: "Extract as markdown table"

**Q: Missing images or media**
**A**: Scraping extracts text only. For images, use browser screenshot tool
