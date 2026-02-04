# Publishing Workflow

Newsletter publishing follows a structured workflow with status tracking and source management.

## Folder Structure

```
publishing/
├── drafts/             # Newsletters awaiting review
│   ├── issue-5.md      # Draft content
│   └── issue-5.meta.json
│
├── published/          # Approved newsletters
│   ├── 2026-02-04-issue-5.md
│   └── 2026-02-04-issue-5.meta.json
│
└── README.md
```

## Workflow

```
DRAFT → REVIEW → APPROVED → PUBLISHED
              ↘ REJECTED
```

### Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Generated, not yet reviewed |
| `review` | Under editorial review |
| `approved` | Ready to publish |
| `published` | Live, sent to subscribers |
| `rejected` | Needs rework |

## Metadata

Each newsletter has a `.meta.json` file tracking:

```json
{
  "issue_number": 5,
  "status": "draft",
  "draft_created": "2026-02-04T10:00:00Z",
  "last_modified": "2026-02-04T12:00:00Z",
  "tentative_publish_date": "2026-02-11",
  "published_date": null,
  "subject_line": "Issue #5: The $50K Ad Secret",
  "viral_edge_title": "...",
  "tactic": "Day-1 ROAS optimization",
  "sources": [...],
  "review_notes": ["[2026-02-04] Needs stronger CTA"],
  "sponsor_name": null
}
```

## Source Tracking

Each newsletter includes sources at the bottom (removed before publishing):

```markdown
---

## Sources (For Fact-Checking)

*This section is removed before publishing.*

**[1] Reddit r/dropshipping post**
- URL: https://reddit.com/r/dropshipping/...
- Type: reddit
- Accessed: 2026-02-04T10:00:00Z
- Key claim: "$50K/month with 2.8x ROAS"

**[2] YouTube video by XYZ**
- URL: https://youtube.com/...
- Type: youtube
- Accessed: 2026-02-04T10:05:00Z
```

## Commands

```bash
# List all drafts
python execution/publishing_manager.py --list-drafts

# List published newsletters
python execution/publishing_manager.py --list-published

# Check status of issue #5
python execution/publishing_manager.py --status 5

# Mark for review
python execution/publishing_manager.py --set-status 5 --new-status review

# Add review note
python execution/publishing_manager.py --set-status 5 --new-status review \
  --note "Needs stronger CTA in section 5"

# Approve and publish
python execution/publishing_manager.py --approve 5
```

## Integration with Orchestrator

The newsletter orchestrator automatically:
1. Saves to `publishing/drafts/`
2. Extracts sources from viral content
3. Creates metadata with dates and status
4. Appends sources section for fact-checking

```bash
# Generate newsletter (saves to drafts)
python execution/newsletter_orchestrator.py --issue 5

# Review in drafts folder
cat publishing/drafts/issue-5.md

# When ready, approve and publish
python execution/publishing_manager.py --approve 5
```

## Fact-Checking Workflow

1. **Generate** - Orchestrator creates draft with sources
2. **Review sources** - Check each URL, verify claims
3. **Mark reviewed** - Update status to "review"
4. **Approve/Reject** - Based on fact-check results
5. **Publish** - Sources section auto-removed

## Example Timeline

| Day | Action |
|-----|--------|
| Monday | Generate Issue #6 → drafts |
| Tuesday | Review sources, check facts |
| Wednesday | Mark approved |
| Thursday | Schedule publish |
| Friday | Auto-publish (or manual) |
