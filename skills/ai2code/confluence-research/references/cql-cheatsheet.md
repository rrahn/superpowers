# CQL (Confluence Query Language) — Cheatsheet

Quick reference for constructing Confluence search queries via the REST API.
Only relevant when the agent needs to go beyond the standard `text~"..."` patterns
documented in the core SKILL.md.

---

## Text Search Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `text ~ "term"` | Full-text search (tokenized, stemmed) | `text ~ "PingFederate"` |
| `title ~ "term"` | Search only in page titles | `title ~ "OAuth setup"` |
| `text ~ "term*"` | Wildcard prefix match | `text ~ "Ping*"` |
| `text ~ "term1 term2"` | Both tokens present (implicit AND) | `text ~ "OAuth token"` |

> **Quoting rule**: Multi-word phrases must be wrapped in double quotes.
> Single words work with or without quotes.

---

## Boolean Operators

| Operator | Example |
|----------|---------|
| `AND` | `text ~ "PingFederate" AND text ~ "OBO"` |
| `OR` | `text ~ "PingFederate" OR text ~ "PingOne"` |
| `NOT` | `text ~ "OAuth" NOT text ~ "deprecated"` |

Operator precedence: `NOT` > `AND` > `OR`. Use parentheses to override:

```
(text ~ "PingFederate" OR text ~ "PingOne") AND text ~ "token exchange"
```

---

## Field Filters

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `type` | Exact | `type = "page"` | `page`, `blogpost`, `attachment`, `comment` |
| `space` | Exact | `space = "DEVOPS"` | Space key (uppercase) |
| `space.type` | Exact | `space.type = "global"` | `global` or `personal` |
| `label` | Exact | `label = "architecture"` | Page label |
| `ancestor` | Exact | `ancestor = 123456` | All descendants of page ID |
| `parent` | Exact | `parent = 123456` | Direct children only |
| `creator` | Exact | `creator = "jsmith"` | Username who created the page |
| `contributor` | Exact | `contributor = "jsmith"` | Anyone who edited the page |
| `id` | Exact | `id = 654321` | Specific content ID |

---

## Date Filters

| Field | Example | Notes |
|-------|---------|-------|
| `created` | `created >= "2024-01-01"` | ISO date format |
| `lastModified` | `lastModified >= "2024-06-01"` | Last edit date |

Relative dates:

```
lastModified >= now("-30d")    # Modified in last 30 days
created >= now("-7d")          # Created in last 7 days
lastModified >= startOfYear()  # Modified this year
```

---

## Sorting

Append `ORDER BY` to any query:

```
text ~ "PingFederate" ORDER BY lastModified DESC
text ~ "OAuth" AND space = "ARCH" ORDER BY title ASC
```

Sortable fields: `title`, `created`, `lastModified`, `space`.

---

## Combining Filters — Practical Patterns

### Search within a single space
```
text ~ "authentication" AND space = "PLATFORM"
```

### Recently updated pages on a topic
```
text ~ "PingFederate" AND lastModified >= now("-90d") ORDER BY lastModified DESC
```

### Pages by a specific author on a topic
```
text ~ "OAuth" AND contributor = "jsmith"
```

### Exclude a noisy space
```
text ~ "SSO" AND space != "ARCHIVE"
```

### Pages with a specific label
```
label = "security" AND text ~ "token"
```

### Blog posts only
```
text ~ "migration" AND type = "blogpost" ORDER BY created DESC
```

---

## REST API URL Patterns

### Search endpoint
```
GET /rest/api/search?cql=<URL_ENCODED_CQL>&limit=25&start=0
```

### Fetch page content
```
GET /rest/api/content/<PAGE_ID>?expand=body.storage,version,space
```

### Fetch page with ancestors (breadcrumb context)
```
GET /rest/api/content/<PAGE_ID>?expand=body.storage,ancestors,space
```

### Fetch child pages
```
GET /rest/api/content/<PAGE_ID>/child/page?limit=50
```

### Fetch page labels
```
GET /rest/api/content/<PAGE_ID>/label
```

---

## URL Encoding Reminder

CQL queries contain characters that break URLs if not encoded:

| Character | Encoded | Appears in |
|-----------|---------|------------|
| `"` | `%22` | Every text search |
| ` ` | `%20` or `+` | Multi-word phrases |
| `~` | `%7E` | Text search operator |
| `(` `)` | `%28` `%29` | Boolean grouping |
| `>=` | `%3E%3D` | Date comparisons |

The safe approach documented in the core SKILL.md is `curl -s -G --data-urlencode 'cql=...'`
which handles all encoding automatically. Only use manual encoding as a fallback.

---

## Pagination

The search API defaults to `limit=25`, maximum `200`. To paginate:

```sh
START=0
LIMIT=25

while true; do
  RESPONSE=$(curl -s -G \
    -H "Authorization: Bearer $PAT" \
    --data-urlencode 'cql=text~"PingFederate"' \
    --data-urlencode "limit=$LIMIT" \
    --data-urlencode "start=$START" \
    "$CONFLUENCE_URL/rest/api/search")

  SIZE=$(echo "$RESPONSE" | jq '.size')
  # Process results...

  if [ "$SIZE" -lt "$LIMIT" ]; then
    break  # Last page
  fi
  START=$((START + LIMIT))
done
```

For most research tasks, the first 25 results per query are sufficient — pagination is
only needed for exhaustive audits or bulk exports.

---

## Sources

- [CQL syntax reference (Atlassian Data Center)](https://developer.atlassian.com/server/confluence/advanced-searching-using-cql/)
- [Confluence REST API examples](https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/)
- [CQL fields reference](https://developer.atlassian.com/server/confluence/cql-field-reference/)
- [CQL functions reference](https://developer.atlassian.com/server/confluence/cql-function-reference/)