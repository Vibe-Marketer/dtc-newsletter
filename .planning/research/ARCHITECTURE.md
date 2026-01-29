# Architecture Research: Newsletter Automation System

**Research Date:** 2026-01-29

## System Components

### 1. Content Aggregation Engine
**Responsibility:** Pull trending/relevant content from multiple sources on a schedule.

| Source | Data Type | Frequency |
|--------|-----------|-----------|
| TikTok Shop | Trending products, sales data | Daily |
| YouTube | E-com tutorials, breakdowns, creator content | Daily |
| Twitter/X | DTC founder tweets, hot takes, threads | Daily |
| Amazon | Movers & Shakers, trending categories | Daily |
| Reddit | r/shopify, r/dropship, r/ecommerce discussions | Daily |
| Perplexity | Research queries, fact-checking, summaries | On-demand |

### 2. Content Storage Layer
**Responsibility:** Store aggregated content with metadata for later processing.

- Raw content cache (what was scraped)
- Processed content (summaries, extracted insights)
- Content scoring (relevance, engagement potential)
- Deduplication tracking

### 3. AI Content Generator
**Responsibility:** Transform raw content into newsletter sections using Alex Hormozi voice rules.

Sub-components:
- **Voice Enforcer**: Applies Hormozi style (short sentences, concrete examples, math-driven, zero fluff)
- **Section Generator**: Creates each of the 5 newsletter sections
- **Quality Validator**: Checks word counts, format compliance, tone consistency

### 4. Affiliate Opportunity Finder
**Responsibility:** Identify monetization opportunities that match newsletter content.

- Product-to-affiliate matching
- Commission rate lookup
- Pitch angle generation
- Link generation/tracking

### 5. Digital Product Factory
**Responsibility:** Create one sellable digital product per week.

Product types:
- GPTs (custom prompts configured)
- Prompt Packs (downloadable text files)
- PDFs (guides, frameworks, checklists)
- Google Sheets (templates, trackers)
- Small Tools (calculators, generators)

Sub-components:
- Product ideation (based on newsletter topic)
- Product generation (actual asset creation)
- Sales copy generator
- Pricing engine
- Delivery packaging

### 6. Beehiiv Integration Layer
**Responsibility:** Create drafts in Beehiiv, manage publication workflow.

- Draft creation via API
- Template formatting (plain text, no HTML)
- Preview/review URL generation
- Publication scheduling (human triggers actual send)

### 7. Orchestration Controller
**Responsibility:** Coordinate the entire weekly workflow.

- Trigger management (cron/scheduler)
- Pipeline sequencing
- Error handling and retries
- Status reporting
- Cost tracking

---

## Component Boundaries

### Content Aggregation Engine
**Owns:**
- API connections to all source platforms
- Rate limiting and credential management per source
- Raw content extraction and initial parsing
- Error handling for failed scrapes

**Does NOT own:**
- Content interpretation or summarization
- Deciding what content is "good"
- Storage persistence (hands off to Storage Layer)

### Content Storage Layer
**Owns:**
- Database/file system operations
- Content deduplication
- Metadata indexing
- Historical content retrieval

**Does NOT own:**
- Fetching content from sources
- Processing or transforming content
- Making decisions about content quality

### AI Content Generator
**Owns:**
- LLM API calls (Anthropic/OpenAI)
- Prompt engineering for voice/style
- Section assembly and formatting
- Output validation against format rules

**Does NOT own:**
- Raw content sourcing
- Final publication
- Affiliate link insertion
- Product creation

### Affiliate Opportunity Finder
**Owns:**
- Affiliate network API connections
- Product matching algorithms
- Commission rate data
- Link generation

**Does NOT own:**
- Newsletter content creation
- Product research (uses newsletter topic as input)
- Publication

### Digital Product Factory
**Owns:**
- Product template library
- Asset generation (GPTs, prompts, PDFs, sheets)
- Sales copy generation
- Pricing logic
- Delivery file packaging

**Does NOT own:**
- Payment processing
- Customer delivery (external platform)
- Product ideation strategy (takes topic as input)

### Beehiiv Integration Layer
**Owns:**
- Beehiiv API authentication
- Draft CRUD operations
- Format conversion (markdown to Beehiiv format)
- Draft URL retrieval

**Does NOT own:**
- Content creation
- Publication decisions (human approves)
- Subscriber management

### Orchestration Controller
**Owns:**
- Weekly schedule execution
- Component sequencing
- Cross-component error handling
- Pipeline status and logging
- Cost aggregation

**Does NOT own:**
- Individual component logic
- Direct API calls to external services
- Content decisions

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEEKLY TRIGGER (Cron)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    1. CONTENT AGGREGATION ENGINE                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ TikTok   │ │ YouTube  │ │ Twitter  │ │ Amazon   │ │ Reddit   │      │
│  │ Shop     │ │          │ │ /X       │ │          │ │          │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │            │             │
│       └────────────┴────────────┴────────────┴────────────┘             │
│                                 │                                       │
│                         Raw Content                                     │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    2. CONTENT STORAGE LAYER                             │
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Raw Content DB  │    │ Processed Cache │    │ Content Index   │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
┌───────────────────────────────┐  ┌───────────────────────────────────────┐
│  3. AI CONTENT GENERATOR      │  │  4. AFFILIATE OPPORTUNITY FINDER      │
│                               │  │                                       │
│  Input: Curated content       │  │  Input: Newsletter topic/products     │
│                               │  │                                       │
│  ┌─────────────────────────┐  │  │  ┌─────────────────────────────────┐  │
│  │ Section 1: Quote/Tweet  │  │  │  │ Affiliate Network Lookup        │  │
│  │ Section 2: What's Work  │  │  │  │ Commission Rate Check           │  │
│  │ Section 3: Breakdown    │  │  │  │ Pitch Angle Generation          │  │
│  │ Section 4: Tool of Week │◄─┼──┼──│ Matching Product Links          │  │
│  │ Section 5: PS Statement │  │  │  └─────────────────────────────────┘  │
│  └─────────────────────────┘  │  │                                       │
│                               │  │  Output: Affiliate links + angles     │
│  Voice: Alex Hormozi          │  │                                       │
│  Format: Plain text           │  └───────────────────────────────────────┘
│                               │
│  Output: Draft newsletter     │
└───────────────────┬───────────┘
                    │
                    │  (Also triggers Product Factory)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    5. DIGITAL PRODUCT FACTORY                           │
│                                                                         │
│  Input: Newsletter topic + audience pain point                          │
│                                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ GPT        │  │ Prompt     │  │ PDF        │  │ Sheet      │        │
│  │ Generator  │  │ Pack Gen   │  │ Generator  │  │ Generator  │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
│                                                                         │
│  + Sales Copy Generator                                                 │
│  + Pricing Engine                                                       │
│  + Delivery Packager                                                    │
│                                                                         │
│  Output: Complete product package (asset + copy + pricing)              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    6. BEEHIIV INTEGRATION LAYER                         │
│                                                                         │
│  Input: Complete newsletter draft + product info                        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ - Format to Beehiiv structure                                    │   │
│  │ - Create draft via API                                           │   │
│  │ - Attach product links                                           │   │
│  │ - Generate preview URL                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Output: Draft URL for human review                                     │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEW & APPROVAL                              │
│                                                                         │
│  - Review draft in Beehiiv                                              │
│  - Make edits if needed                                                 │
│  - Approve and schedule publication                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Artifacts at Each Stage

| Stage | Input | Output | Storage |
|-------|-------|--------|---------|
| Aggregation | API credentials | Raw JSON/HTML | `.tmp/raw_content/` |
| Storage | Raw content | Indexed, deduplicated records | `data/content.db` or JSON |
| AI Generator | Curated content | 5-section newsletter draft | `.tmp/drafts/` |
| Affiliate Finder | Topic + products | Links + pitch angles | In-memory (injected) |
| Product Factory | Topic + pain point | Asset files + sales copy | `output/products/` |
| Beehiiv | Final draft | Draft ID + preview URL | Beehiiv platform |

---

## Suggested Build Order

### Phase 1: Foundation (Week 1-2)
**Goal:** Prove content can flow from source to draft

```
1.1 Content Storage Layer (simple file-based)
    - JSON files for now, database later
    - Reason: Everything else depends on having somewhere to put data

1.2 Single Source Aggregator (pick easiest: Reddit or Twitter)
    - Prove the scraping/API pattern works
    - Reason: Need real content to test downstream components

1.3 Basic AI Content Generator (one section only)
    - Generate "What's Working Now" section from stored content
    - Reason: Validates LLM integration + voice rules
```

### Phase 2: Core Pipeline (Week 3-4)
**Goal:** Complete newsletter generation with all sections

```
2.1 Expand Aggregation to all sources
    - TikTok Shop, YouTube, Amazon, Perplexity
    - Reason: Newsletter quality depends on source diversity

2.2 Full AI Content Generator (all 5 sections)
    - Section 1: Quote/Tweet picker
    - Section 2: What's Working Now
    - Section 3: Breakdown
    - Section 4: Tool of Week (placeholder)
    - Section 5: PS Statement
    - Reason: Complete newsletter structure needed before integration

2.3 Beehiiv Integration Layer
    - Create draft, get preview URL
    - Reason: End-to-end flow validation
```

### Phase 3: Monetization (Week 5-6)
**Goal:** Add revenue-generating components

```
3.1 Affiliate Opportunity Finder
    - Product matching + link generation
    - Injects into Section 4 (Tool of Week)
    - Reason: Monetization without own products

3.2 Digital Product Factory (MVP)
    - Start with Prompt Packs (easiest to generate)
    - Add sales copy generator
    - Reason: Own products = higher margins
```

### Phase 4: Automation (Week 7-8)
**Goal:** Full weekly automation with monitoring

```
4.1 Orchestration Controller
    - Cron/scheduler setup
    - Error handling and retries
    - Cost tracking integration
    - Reason: Human-free execution

4.2 Product Factory Expansion
    - Add GPT generation
    - Add PDF generation
    - Add Sheet templates
    - Reason: Product variety = more opportunities

4.3 Monitoring & Alerting
    - Failure notifications
    - Quality checks
    - Cost alerts
    - Reason: Trust the automation
```

### Build Order Rationale

```
Storage ──► Single Aggregator ──► Basic Generator ──► Full Aggregation
                                                            │
                                                            ▼
Product Factory ◄── Affiliate Finder ◄── Beehiiv ◄── Full Generator
        │
        ▼
Orchestration Controller ──► Monitoring
```

**Why this order:**
1. **Storage first**: Everything needs somewhere to write/read
2. **One aggregator**: Proves the pattern before scaling
3. **Basic generator**: Validates LLM integration early
4. **Full aggregation**: Quality depends on diverse sources
5. **Full generator**: Complete product before integration
6. **Beehiiv**: End-to-end validation
7. **Monetization**: Revenue layer added to working pipeline
8. **Automation**: Only automate what's proven to work

---

## Integration Points

### External APIs

| Component | External Service | Integration Type | Auth Method |
|-----------|-----------------|------------------|-------------|
| Aggregation | TikTok Shop | Scraping/API | API Key or Apify |
| Aggregation | YouTube | YouTube Data API v3 | OAuth/API Key |
| Aggregation | Twitter/X | API v2 or scraping | Bearer Token |
| Aggregation | Amazon | Product Advertising API | Access Key |
| Aggregation | Reddit | Reddit API | OAuth |
| Aggregation | Perplexity | Perplexity API | API Key |
| AI Generator | Anthropic Claude | REST API | API Key |
| AI Generator | OpenAI (backup) | REST API | API Key |
| Affiliate | Various networks | Per-network APIs | Per-network |
| Publication | Beehiiv | REST API | API Key |

### Internal Interfaces

| Producer | Consumer | Data Format | Transfer |
|----------|----------|-------------|----------|
| Aggregation | Storage | JSON (raw content) | Function call |
| Storage | AI Generator | JSON (curated list) | Function call |
| Storage | Affiliate Finder | JSON (topic/products) | Function call |
| AI Generator | Beehiiv | Markdown string | Function call |
| Affiliate Finder | AI Generator | JSON (links + angles) | Function call |
| Product Factory | Beehiiv | JSON (product info) | Function call |
| Orchestration | All components | Function calls | Direct invocation |

### File System Interfaces

| Path | Purpose | Written By | Read By |
|------|---------|------------|---------|
| `.tmp/raw_content/` | Raw scraped data | Aggregation | Storage |
| `data/content.db` | Processed content | Storage | AI Generator, Affiliate |
| `.tmp/drafts/` | Newsletter drafts | AI Generator | Beehiiv, Human |
| `output/products/` | Digital products | Product Factory | Human, Delivery |
| `.tmp/cost_log.jsonl` | API cost tracking | All AI calls | Orchestration |

### Error Escalation Flow

```
Component Error
      │
      ▼
┌─────────────────┐
│ Is it transient?│──Yes──► Retry (1s, 2s, 4s backoff)
│ (rate limit,    │                    │
│  timeout)       │                    ▼
└────────┬────────┘              ┌─────────────┐
         │                       │ 3 failures? │──Yes──► Escalate to human
         No                      └──────┬──────┘
         │                              │ No
         ▼                              ▼
┌─────────────────┐              Continue pipeline
│ Is it config?   │──Yes──► Log error, skip component, notify
│ (missing key,   │
│  bad creds)     │
└────────┬────────┘
         │
         No
         │
         ▼
┌─────────────────┐
│ Is it critical? │──Yes──► Halt pipeline, notify human
│ (API changed,   │
│  data corrupt)  │
└────────┬────────┘
         │
         No
         │
         ▼
Log warning, continue with degraded output
```

---

## Key Architecture Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| File-based storage first | Simple, debuggable, no DB setup | SQLite/Postgres from start |
| Stateless components | Easier testing, no race conditions | Shared state object |
| Human approval checkpoint | 100K subscribers = high stakes | Full automation |
| Single LLM provider (Claude) | Consistency in voice/quality | Multi-provider routing |
| Sequential pipeline | Predictable debugging | Parallel async processing |
| Plain text output | Deliverability + brand guidelines | HTML templates |

---

## Risk Areas

1. **TikTok Shop data access**: May require Apify or reverse engineering
2. **Twitter/X API costs**: Can be expensive at scale
3. **Voice consistency**: LLM may drift from Hormozi style
4. **Affiliate link validation**: Links can go stale
5. **Beehiiv API limits**: Unknown rate limits
6. **Product Factory quality**: Generated products may need heavy editing

---

*Architecture research completed: 2026-01-29*
*Ready to inform roadmap phase structure*
