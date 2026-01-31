# Product Factory
<!-- DOE-VERSION: 2026.01.31 -->

## Goal
Generate high-value digital products ($1K+ perceived value) from e-commerce pain points.

## Trigger Phrases
- "create a product"
- "find pain points"
- "generate product from problem"
- "make a calculator for"
- "build an automation for"
- "product factory"

## Quick Start

### Discover Pain Points
```bash
python -m execution.product_factory --discover
```

### Create Product from Pain Point
```bash
python -m execution.product_factory --create \
  --type html_tool \
  --name "Shopify Profit Calculator" \
  --problem "E-com owners don't know their true profit margins" \
  --audience "Shopify store owners doing \$10K-100K/mo" \
  --benefits "Know real profit in 30 seconds,Spot margin leaks instantly,Price products confidently"
```

### Create from Pain Point File
```bash
python -m execution.product_factory --from-pain-point data/pain_points/conversion_rate.json --type html_tool
```

## What It Does

1. **Discover Phase** (--discover):
   - Searches Reddit for e-commerce pain points using 25 complaint-focused keywords
   - Targets 6 subreddits: shopify, ecommerce, dropship, Entrepreneur, smallbusiness, FulfillmentByAmazon
   - Scores by engagement (upvotes + comments = real pain validation)
   - Categorizes: shipping, inventory, conversion, returns, pricing, marketing
   - Suggests product types for each pain point based on category and keywords

2. **Create Phase** (--create):
   - Generates product using appropriate generator (6 types available)
   - Creates sales copy with Hormozi/Suby voice profile
   - Recommends pricing ($17-97 based on type and value signals)
   - Packages everything in output/products/[id]/

## Product Types

| Type | What It Creates | Price Range | Best For |
|------|-----------------|-------------|----------|
| html_tool | Single-file calculator/generator with embedded CSS/JS | $27-47 | Calculators, generators, interactive tools |
| automation | Python script + docs with argparse CLI | $47-97 | Workflow automation, repetitive tasks |
| gpt_config | GPT instructions + setup guide + conversation starters | $27-47 | AI assistants, chatbots |
| sheets | Google Sheets template (online or offline mode) | $27-47 | Trackers, dashboards, planners |
| pdf | Styled PDF framework with chapters and callouts | $17-37 | Guides, frameworks, checklists |
| prompt_pack | Curated prompts + examples organized by category | $17-27 | Prompt collections, AI workflows |

## Output

Each product package includes:
```
output/products/[product-id]/
├── manifest.json         # Product metadata + pricing
├── SALES_COPY.md         # Ready-to-use sales page copy
├── [deliverable files]   # The actual product
└── [product-id].zip      # Downloadable package
```

**Manifest contains:**
- Product ID, name, type, version
- Problem solved and target audience
- Key benefits
- Deliverables list with file sizes
- Pricing (price_cents, price_display, perceived_value, justification)
- Sales copy excerpts (headline, subheadline, CTA)

## CLI Reference

```
Usage: python -m execution.product_factory [OPTIONS]

Mode Selection (required - choose one):
  --discover              Find pain points from Reddit
  --create               Create product from specifications
  --from-pain-point FILE Create from pain point JSON file

Discovery Options:
  --limit N              Max pain points to return (default: 20)

Creation Options:
  --type TYPE            Product type (required for --create)
  --name NAME            Product name (required for --create)
  --problem TEXT         Problem being solved (required for --create)
  --audience TEXT        Target audience (default: "E-commerce entrepreneurs")
  --benefits TEXT        Comma-separated benefits list

Output Options:
  --output-dir DIR       Output directory (default: output/products)
  --verbose, -v          Enable verbose logging
```

## Configuration

Environment variables:
- `ANTHROPIC_API_KEY` - Required for Claude generation (sales copy, product content)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` - For pain point discovery
- `GOOGLE_SERVICE_ACCOUNT_JSON` - Optional, for Google Sheets online mode

## Category to Product Mapping

The factory auto-suggests product types based on pain point category:

| Category | Primary Suggestion | Secondary |
|----------|-------------------|-----------|
| shipping | automation | sheets |
| inventory | automation | sheets |
| conversion | html_tool | gpt_config |
| returns | automation | pdf |
| pricing | html_tool | sheets |
| marketing | prompt_pack | gpt_config |

**Keyword overrides:**
- "calculator", "calculate", "roi" → html_tool
- "automate", "automation", "workflow" → automation
- "chatgpt", "gpt", "ai assistant" → gpt_config

## Success Criteria

1. Pain points are specific, not vague ("conversion rate low" not "struggling")
2. Products solve ONE narrow problem clearly
3. Sales copy follows Hormozi/Suby voice (no fluff, direct, valuable)
4. Price includes perceived value justification
5. Package is complete and ready to sell

## Example Workflow

```bash
# 1. Discover pain points
python -m execution.product_factory --discover --limit 10

# Output shows top 10 with engagement scores and suggestions:
# 1. [PRICING] Shipping costs are killing my margins...
#    Engagement: 350 (⬆️ 250 + 💬 100)
#    Suggested: html_tool, sheets

# 2. Pick a pain point and create product
python -m execution.product_factory --create \
  --type html_tool \
  --name "True Profit Calculator" \
  --problem "E-commerce owners don't know actual profit after shipping costs" \
  --benefits "Know real margins in 30 seconds,Find hidden cost leaks,Price products profitably"

# 3. Output in output/products/abc12345/
#    - manifest.json (product info + $27 pricing)
#    - SALES_COPY.md (ready for landing page)
#    - true_profit_calculator.html (the tool)
#    - abc12345.zip (downloadable)
```

## Integration

The Product Factory integrates with the full DTC Newsletter pipeline:
- **Affiliate Finder** discovers tools to recommend
- **Product Factory** creates complementary products from pain points
- **Newsletter Generator** references both in Section 4 (Tool of the Week)

## Troubleshooting

**"Claude client not available"**
- Set ANTHROPIC_API_KEY in .env
- Factory will continue but skip AI-generated content

**"Reddit API error"**
- Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env
- Discovery requires valid Reddit API credentials

**"Unknown product type"**
- Valid types: html_tool, automation, gpt_config, sheets, pdf, prompt_pack
- Use --type with one of these values
