---
name: confluence-research
description: >
  Search and synthesize knowledge from Confluence Data Center using a Personal Access
  Token (PAT) and the REST API. Use when: the user wants to research a topic on
  Confluence, search Confluence pages, query Confluence with CQL, extract information
  from a Confluence wiki, or automate Confluence lookups. Covers PAT authentication,
  CQL query construction, URL-encoding pitfalls, parallel search execution, page
  content fetching, and report synthesis. Works with any Confluence Data Center instance.
alwaysApply: false
tier: 4
metadata:
  version: "1.0"
  sources: "https://developer.atlassian.com/server/confluence/advanced-searching-using-cql/, https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/"
user-invocable: true
---

# Confluence Research — Automated Search via PAT + REST API

## Problem

Agents need to search a Confluence Data Center instance programmatically to gather
internal documentation on a topic. The Confluence REST API requires correct
authentication, properly URL-encoded CQL queries, and a multi-pass strategy (search →
rank → fetch → synthesize) to produce useful results. Getting any of these wrong leads
to silent failures (HTTP 400 from bad encoding) or shallow results (only searching one
query term).

## Trigger Conditions

- User provides a Confluence PAT and wants to search for information
- User says "search Confluence for ...", "find Confluence pages about ...", "research X on our wiki"
- User wants to query Confluence Data Center REST API
- Task requires gathering internal documentation from a Confluence instance
- Error: `HTTP Status 400 – Bad Request` when querying Confluence search endpoint (URL-encoding issue)

## Prerequisites

The user must provide two values before the workflow can start:

| Input | Example | How to obtain |
|-------|---------|---------------|
| `CONFLUENCE_URL` | `https://confluence.example.com` | The base URL of the Confluence Data Center instance (no trailing slash) |
| `PAT` | `NTEwMDE0MzY...` | Personal Access Token — generate at `<CONFLUENCE_URL>/plugins/personaltokens/usertokens.action` |

If either value is missing, stop and ask the user. Do not guess or fabricate these values.

## Solution

### Step 1 — Verify connectivity

Confirm the PAT works and the instance is reachable before running real queries. This
catches expired tokens and wrong URLs early instead of mid-research.

```sh
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $PAT" \
  "$CONFLUENCE_URL/rest/api/search?cql=type=page&limit=1"
```

- `200` → proceed.
- `401` → PAT is invalid or expired. Ask the user to regenerate it.
- `403` → PAT lacks read permissions.
- Any other code → check `CONFLUENCE_URL` for typos or network issues.

### Step 2 — Derive CQL search terms from the research goal

From the user's research goal, generate 5–8 CQL search terms that cover the topic from
different angles. Each term uses the `text~"..."` full-text search operator.

**Query design principles:**
- Start broad (`text~"PingFederate"`), then narrow with AND (`text~"PingFederate" AND text~"OAuth"`)
- Include synonyms and abbreviations the wiki authors might have used
- Include specific error messages or config keys if the user mentioned them
- Cap at 8 queries — diminishing returns beyond that

Example for a PingFederate research goal:

```
text~"PingFederate"
text~"PingFederate" AND text~"OAuth"
text~"PingFederate" AND text~"OBO"
text~"On-Behalf-Of" AND text~"PingFederate"
text~"OAuth token exchange"
text~"PingFederate" AND text~"integration"
text~"PingFederate" AND text~"SSO"
text~"PXED"
```

### Step 3 — Execute all searches in parallel

Run all CQL queries simultaneously. Use `curl -s -G` with `--data-urlencode` for the
`cql` parameter — this is critical because CQL contains double quotes that cause HTTP 400
if embedded as literal characters in the URL.

```sh
curl -s -G \
  -H "Authorization: Bearer $PAT" \
  --data-urlencode 'cql=text~"PingFederate"' \
  --data-urlencode 'limit=25' \
  "$CONFLUENCE_URL/rest/api/search"
```

> **Known pitfall — HTTP 400**: If you place the CQL directly in the URL string
> (e.g., `?cql=text~"PingFederate"`), the unescaped quotes cause a 400 error.
> The fix: use `-G` (convert data to GET params) with `--data-urlencode` (auto-encode
> special characters). This was the #1 failure in the original workflow and cost an
> entire retry cycle.

Parse each response with `jq` or `python3` to extract per-result:
- `results[].content.id` — page ID (needed for full fetch)
- `results[].content.title` — page title
- `results[].excerpt` — search snippet (contains `@@@hl@@@` highlight markers)
- `results[].url` — relative web URL
- `results[].resultGlobalContainer.title` — space name
- `totalSize` — total matches for this query

Quick extraction with jq:

```sh
curl -s -G \
  -H "Authorization: Bearer $PAT" \
  --data-urlencode 'cql=text~"PingFederate"' \
  --data-urlencode 'limit=25' \
  "$CONFLUENCE_URL/rest/api/search" \
| jq -r '.results[] | "\(.content.id)\t\(.content.title)\t\(.resultGlobalContainer.title)\t\(.url)"'
```

### Step 4 — Deduplicate and rank

The same page often surfaces across multiple CQL queries. Deduplicate by page ID, then
rank the top 10 pages by relevance. Relevance heuristics:

1. Pages whose title directly matches the research goal rank highest
2. Pages that appeared in multiple queries rank higher (cross-query signal)
3. Prefer pages from spaces that sound authoritative (e.g., architecture, platform, security spaces)
4. Prefer recently modified pages (check `lastModified` in search results)

### Step 5 — Fetch full content for top 10 pages (in parallel)

For each top-ranked page ID, fetch the full body in storage format:

```sh
curl -s \
  -H "Authorization: Bearer $PAT" \
  "$CONFLUENCE_URL/rest/api/content/$PAGE_ID?expand=body.storage,version,space"
```

The content is in `body.storage.value` as Confluence storage format (XML/HTML). Parse it
to extract readable text — strip HTML tags or use `python3` with `html.parser` for
cleaner extraction.

Run these fetches in parallel (up to 10 concurrent) to minimize wall-clock time.

### Step 6 — Synthesize a report

Structure the output to directly answer the user's research goal:

```markdown
## Summary
2–3 sentence answer to the core research question.

## Key Findings
- Bullet list of the most important facts discovered across all pages.

## Details
Sub-sections organized by topic area (e.g., "Supported Auth Flows", "Endpoints",
"Configuration", "Limitations"). Include direct quotes or paraphrased content with
attribution to the source page.

## Pages Consulted
| # | Page Title | Space | URL | Relevance |
|---|-----------|-------|-----|-----------|
| 1 | ... | ... | CONFLUENCE_URL/... | High — directly covers X |

## Gaps / Unanswered Questions
Topics that were searched for but not found in Confluence.
```

## Verification

1. The connectivity check in Step 1 returned HTTP 200
2. Each CQL search returned a JSON response with `results[]` array (not an HTML error page)
3. At least one search returned `totalSize > 0`
4. Full page fetches returned JSON with non-empty `body.storage.value`
5. The synthesized report addresses the user's original research goal

## Notes

- **Security**: PATs are sensitive credentials. Remind the user to rotate the PAT after
  the research session. Do not log or store the PAT beyond the current session.
- **Rate limiting**: Confluence Data Center does not enforce strict rate limits by default,
  but large instances may have reverse-proxy throttling. If you get HTTP 429 or
  connection resets, add 1-second delays between requests.
- **Pagination**: The search endpoint returns `limit` results per call (max 200). If
  `totalSize` exceeds your limit, paginate with `&start=N`. For research purposes,
  the first 25 results per query are usually sufficient.
- **Content types**: The default search returns pages. To include blog posts, add
  `AND type in ("page","blogpost")` to the CQL. Attachments require `type="attachment"`.
- **Space-scoped search**: To restrict to a single space, add `AND space="SPACEKEY"` to
  the CQL query.
- **Confluence Cloud vs. Data Center**: This skill targets Data Center (on-premise). Cloud
  uses a different auth mechanism (OAuth 2.0 or API token as Basic auth) and different
  REST API base paths (`/wiki/rest/api/` instead of `/rest/api/`).

## CQL Quick Reference

For additional CQL operators and field reference, read `references/cql-cheatsheet.md`.
