# Phase 6: Product Factory - Research

**Researched:** 2026-01-31
**Domain:** Digital Product Generation & Reddit Pain Point Mining
**Confidence:** MEDIUM (verified against official docs, some patterns from training)

## Summary

Phase 6 creates a Product Factory that mines Reddit for e-commerce pain points and generates high-value digital products ($1K+ perceived value) to solve specific problems. The system must support 6 product types: HTML tools, automations/workflows, Custom GPTs, Google Sheets templates, PDF frameworks, and prompt packs.

The existing `reddit_fetcher.py` using PRAW provides a solid foundation for pain point research - it already supports search queries and can be extended with different subreddits targeting complaints. For PDF generation, `fpdf2` is the clear standard - lightweight, pure Python, actively maintained with 1.5k stars. Google Sheets generation uses `gspread` with service account auth. HTML tools are best generated as single-file apps with embedded CSS/JS.

**Primary recommendation:** Extend existing reddit_fetcher for pain point mining, use fpdf2 for PDFs, gspread for Sheets, generate HTML tools as single-file standalone apps, and create templated generators for each product type.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| praw | 7.7+ | Reddit API access | Already in use, official Reddit wrapper |
| fpdf2 | 2.8+ | PDF generation | Lightweight, pure Python, actively maintained |
| gspread | 6.x | Google Sheets API | 7.4k stars, simple interface, service account auth |
| Jinja2 | 3.x | Template rendering | Standard for HTML/text templating |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-docx | 0.8+ | Word docs (optional) | If Word output needed |
| Pillow | 10+ | Image processing | For PDF images |
| json | stdlib | Config/data storage | Product definitions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fpdf2 | reportlab | More powerful but heavier, commercial license concerns |
| fpdf2 | weasyprint | HTML-to-PDF, but requires external dependencies |
| gspread | pygsheets | Simpler but less maintained |

**Installation:**
```bash
pip install fpdf2 gspread google-auth Jinja2
# praw already installed
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
├── generators/                # Product generators
│   ├── __init__.py
│   ├── base_generator.py      # Abstract base class
│   ├── html_tool.py           # Single-file HTML apps
│   ├── automation.py          # Python scripts/workflows
│   ├── gpt_config.py          # Custom GPT packages
│   ├── sheets.py              # Google Sheets templates
│   ├── pdf.py                 # PDF frameworks/guides
│   └── prompt_pack.py         # Curated prompt collections
├── pain_point_miner.py        # Reddit pain point search
├── product_packager.py        # Assembles final product
└── sales_copy_generator.py    # AI sales copy

data/
├── product_templates/         # Base templates per type
│   ├── html/                  # HTML tool templates
│   ├── sheets/                # Sheets formula templates
│   └── prompts/               # Prompt pack structures
└── pain_points/               # Cached pain point research

output/
└── products/                  # Generated products
    └── {product_id}/          # Each product gets folder
        ├── deliverable/       # The actual product files
        ├── sales_copy.md      # Generated sales copy
        └── manifest.json      # Product metadata
```

### Pattern 1: Generator Base Class
**What:** Abstract base with common interface
**When to use:** All product generators inherit from this
**Example:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductSpec:
    """Specification for a product to generate."""
    problem: str           # The pain point being solved
    solution_name: str     # Product name
    target_audience: str   # Who it's for
    key_benefits: list[str]
    product_type: str      # html_tool, automation, etc.

@dataclass
class GeneratedProduct:
    """Output from a generator."""
    files: dict[str, bytes]  # filename -> content
    manifest: dict           # metadata
    
class BaseGenerator(ABC):
    """Base class for all product generators."""
    
    @abstractmethod
    def generate(self, spec: ProductSpec) -> GeneratedProduct:
        """Generate the product from spec."""
        pass
    
    @abstractmethod
    def validate(self, product: GeneratedProduct) -> bool:
        """Validate the generated product."""
        pass
```

### Pattern 2: Single-File HTML Tool Generation
**What:** Generate standalone HTML with embedded CSS/JS
**When to use:** Calculators, generators, simple interactive tools
**Example:**
```python
from jinja2 import Template

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        {{ css }}
    </style>
</head>
<body>
    {{ body }}
    <script>
        {{ javascript }}
    </script>
</body>
</html>
'''

def generate_html_tool(title: str, body: str, css: str, javascript: str) -> str:
    template = Template(HTML_TEMPLATE)
    return template.render(
        title=title,
        body=body,
        css=css,
        javascript=javascript
    )
```

### Pattern 3: Reddit Pain Point Mining
**What:** Search Reddit for complaints and problems
**When to use:** Identifying product opportunities
**Example:**
```python
def search_pain_points(
    reddit: praw.Reddit,
    subreddits: list[str],
    keywords: list[str],
    limit: int = 100
) -> list[dict]:
    """
    Search for pain point discussions on Reddit.
    
    Keywords should include complaint indicators:
    - "struggling with", "frustrated", "hate", "wish"
    - "can't figure out", "is broken", "doesn't work"
    - "need help", "looking for solution"
    """
    pain_points = []
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        
        for keyword in keywords:
            for post in subreddit.search(keyword, limit=limit, time_filter="month"):
                # Score by engagement (high engagement = real pain)
                pain_points.append({
                    "title": post.title,
                    "body": post.selftext[:500],
                    "score": post.score,
                    "comments": post.num_comments,
                    "url": f"https://reddit.com{post.permalink}",
                    "keyword": keyword,
                    "subreddit": subreddit_name,
                })
    
    # Sort by engagement
    return sorted(pain_points, key=lambda x: x["score"] + x["comments"], reverse=True)
```

### Pattern 4: PDF Framework Generation with fpdf2
**What:** Create styled PDF guides/frameworks
**When to use:** Actionable frameworks, checklists, guides
**Example:**
```python
# Source: https://py-pdf.github.io/fpdf2/Tutorial.html
from fpdf import FPDF

class FrameworkPDF(FPDF):
    def header(self):
        self.set_font("helvetica", style="B", size=15)
        self.cell(0, 10, self.title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", style="I", size=8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
    
    def chapter_title(self, title: str):
        self.set_font("helvetica", style="B", size=12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
    
    def chapter_body(self, body: str):
        self.set_font("Times", size=12)
        self.multi_cell(0, 5, body)
        self.ln()

def generate_pdf_framework(title: str, sections: list[dict]) -> bytes:
    pdf = FrameworkPDF()
    pdf.set_title(title)
    pdf.add_page()
    
    for section in sections:
        pdf.chapter_title(section["title"])
        pdf.chapter_body(section["content"])
    
    return pdf.output()
```

### Pattern 5: Google Sheets Template Creation
**What:** Create Sheets with formulas and formatting
**When to use:** Calculators, trackers, dashboards
**Example:**
```python
# Source: https://docs.gspread.org
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def create_template_sheet(
    template_name: str,
    headers: list[str],
    formulas: dict[str, str],  # cell -> formula
    sample_data: list[list]
) -> str:
    """Create a Google Sheet template and return shareable URL."""
    creds = Credentials.from_service_account_file(
        'service_account.json', scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    
    # Create spreadsheet
    sh = gc.create(template_name)
    worksheet = sh.sheet1
    
    # Add headers
    worksheet.update('A1', [headers])
    worksheet.format('A1:Z1', {'textFormat': {'bold': True}})
    
    # Add sample data
    if sample_data:
        worksheet.update('A2', sample_data)
    
    # Add formulas
    for cell, formula in formulas.items():
        worksheet.update_acell(cell, formula)
    
    # Make it publicly viewable (for product delivery)
    sh.share(None, perm_type='anyone', role='reader')
    
    return sh.url
```

### Pattern 6: Custom GPT Configuration Package
**What:** Instructions + knowledge files for ChatGPT
**When to use:** Specialized AI assistants
**Example:**
```python
import json
from pathlib import Path

def create_gpt_config(
    name: str,
    description: str,
    instructions: str,
    conversation_starters: list[str],
    knowledge_files: list[Path] = None
) -> dict:
    """
    Create a Custom GPT configuration package.
    
    Users manually create the GPT in ChatGPT interface,
    but this provides all the components they need.
    """
    config = {
        "name": name,
        "description": description,
        "instructions": instructions,
        "conversation_starters": conversation_starters[:4],  # Max 4
        "capabilities": {
            "web_browsing": False,
            "dall_e": False,
            "code_interpreter": False
        }
    }
    
    # Package structure
    package = {
        "gpt_config.json": json.dumps(config, indent=2),
        "INSTRUCTIONS.md": f"# {name}\n\n{instructions}",
        "SETUP_GUIDE.md": generate_setup_guide(name),
    }
    
    # Add knowledge files if provided
    if knowledge_files:
        for f in knowledge_files:
            package[f"knowledge/{f.name}"] = f.read_bytes()
    
    return package
```

### Anti-Patterns to Avoid
- **Over-engineering products:** Start simple, validate before adding features
- **Generic solutions:** Products must solve ONE specific narrow problem
- **Missing sales copy:** Every product needs complete packaging before delivery
- **No perceived value signals:** Always include value anchors ($1K+ worth)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation | Custom PDF binary | fpdf2 | PDF spec is complex, edge cases abound |
| Sheets API | Raw HTTP requests | gspread | Auth, rate limits, retries handled |
| Reddit API | Raw HTTP/scraping | PRAW | Rate limits, auth, pagination handled |
| HTML templating | String concatenation | Jinja2 | Escaping, inheritance, filters |
| File packaging | Manual zip | zipfile stdlib | Handles compression, paths correctly |

**Key insight:** The generation logic is where value lives - use libraries for everything else.

## Common Pitfalls

### Pitfall 1: Reddit API Rate Limits
**What goes wrong:** Hitting 60 requests/minute limit during pain point research
**Why it happens:** Aggressive searching across multiple subreddits
**How to avoid:** Batch searches, cache results, respect rate limits
**Warning signs:** 429 errors, temporary bans

### Pitfall 2: Google Sheets Auth Complexity
**What goes wrong:** Service account auth fails or sheets not accessible
**Why it happens:** Wrong scopes, sharing permissions, quota limits
**How to avoid:** 
- Use service account (not OAuth for automation)
- Share sheets with service account email
- Enable both Sheets AND Drive APIs
**Warning signs:** 403 forbidden, "insufficient permissions"

### Pitfall 3: PDF Font Issues
**What goes wrong:** Unicode characters not rendering
**Why it happens:** Default fonts don't support all characters
**How to avoid:** Use add_font() with TTF files that support needed chars
**Warning signs:** Missing characters, "?" boxes

### Pitfall 4: Overly Broad Products
**What goes wrong:** Products try to solve too many problems
**Why it happens:** Combining multiple pain points into one product
**How to avoid:** One product = one narrow problem = one clear solution
**Warning signs:** Long feature lists, unclear value prop

### Pitfall 5: Missing Perceived Value
**What goes wrong:** Products feel cheap despite solving real problems
**Why it happens:** No value anchoring, poor packaging
**How to avoid:** 
- Compare to expensive alternatives
- Quantify time/money saved
- Professional presentation
**Warning signs:** Price objections, "I could build this myself"

## Code Examples

Verified patterns from official sources:

### Pain Point Search Query Builder
```python
# Complaint indicator keywords for e-commerce
PAIN_KEYWORDS = [
    # Frustration signals
    "frustrated with shopify",
    "hate my shopify",
    "shopify is terrible",
    "shopify problem",
    
    # Help-seeking signals
    "struggling with ecommerce",
    "need help with store",
    "can't figure out",
    
    # Specific pain areas
    "conversion rate low",
    "cart abandonment",
    "shipping nightmare",
    "inventory management hell",
    "returns killing me",
]

PAIN_SUBREDDITS = [
    "shopify",
    "ecommerce", 
    "dropship",
    "Entrepreneur",
    "smallbusiness",
    "FulfillmentByAmazon",
]
```

### Product Sales Copy Template
```python
SALES_COPY_PROMPT = '''
Generate sales copy for this digital product:

PRODUCT: {product_name}
PROBLEM IT SOLVES: {problem}
TARGET AUDIENCE: {audience}
KEY BENEFITS:
{benefits}

Generate:
1. HEADLINE (curiosity + benefit, under 10 words)
2. SUBHEADLINE (expands on promise)
3. PROBLEM SECTION (2-3 sentences agitating the pain)
4. SOLUTION SECTION (how this product solves it)
5. BENEFIT BULLETS (5 specific outcomes)
6. VALUE ANCHOR (what this is worth / what alternatives cost)
7. PRICE JUSTIFICATION (why this price is a steal)
8. CTA (action-oriented call to action)

Write in {voice_profile} style. Be specific, use numbers, avoid fluff.
'''
```

### Product Manifest Structure
```python
PRODUCT_MANIFEST = {
    "id": "prod_001",
    "name": "Shopify Profit Calculator",
    "type": "html_tool",
    "version": "1.0.0",
    "created_at": "2026-01-31T12:00:00Z",
    
    "problem": {
        "pain_point": "E-com owners don't know their true profit margins",
        "source_reddit": "https://reddit.com/r/shopify/...",
        "audience": "Shopify store owners doing $10K-100K/mo"
    },
    
    "deliverables": [
        {"file": "profit-calculator.html", "type": "primary"},
        {"file": "README.md", "type": "documentation"}
    ],
    
    "sales": {
        "headline": "Know Your REAL Profit in 30 Seconds",
        "price_cents": 4700,
        "price_display": "$47",
        "perceived_value": "$500+ (replaces spreadsheet templates)"
    },
    
    "packaging": {
        "ready_to_sell": True,
        "sales_page_copy": "sales_copy.md",
        "thumbnail": "thumbnail.png"
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ReportLab for PDFs | fpdf2 | 2020+ | Simpler, pure Python, actively maintained |
| Manual Reddit scraping | PRAW | Standard | Rate limit handling, auth |
| Google Sheets v3 API | v4 via gspread | 2017 | Better performance, cleaner API |

**Deprecated/outdated:**
- pyfpdf (original): Replaced by fpdf2, no longer maintained
- gspread v5: v6 has breaking changes (parameter order)

## Open Questions

Things that couldn't be fully resolved:

1. **Google Sheets Distribution**
   - What we know: Can create sheets programmatically
   - What's unclear: Best way to "sell" sheets - link to copy template?
   - Recommendation: Create sheet, set to "anyone with link can view", buyer copies it

2. **Custom GPT Packaging**
   - What we know: Can generate instructions and knowledge files
   - What's unclear: No API for creating GPTs - users must do manually
   - Recommendation: Provide complete package with step-by-step setup guide

3. **HTML Tool Hosting**
   - What we know: Single-file HTML works offline
   - What's unclear: How to deliver - download link? Embedded?
   - Recommendation: Zip file download, works locally in browser

## Sources

### Primary (HIGH confidence)
- PRAW 7.7 docs - Subreddit search, ListingGenerator
- fpdf2 2.8 docs - Tutorial, Tables, Text styling
- gspread 6.x GitHub README - Basic usage, authentication

### Secondary (MEDIUM confidence)
- Custom GPT Actions docs (OpenAI) - Configuration structure
- Value-based pricing patterns (industry practice)

### Tertiary (LOW confidence)
- Reddit pain point search patterns (common practice, not documented)
- Perceived value multipliers (marketing convention, varies by niche)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs verified
- Architecture: MEDIUM - Patterns based on best practices
- Pain point mining: MEDIUM - Extends existing reddit_fetcher
- Product packaging: MEDIUM - Based on industry patterns
- Pitfalls: MEDIUM - Common issues from forums/experience

**Research date:** 2026-01-31
**Valid until:** 2026-03-01 (30 days - stable libraries)
