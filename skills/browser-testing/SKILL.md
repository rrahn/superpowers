---
name: browser-testing
description: >
  Browser-based QA and testing using headless Playwright via MCP. Use when: (1) you need to
  test a web UI, verify page rendering, check form interactions, or validate auth flows,
  (2) the user asks to "open", "browse", "test the UI", "check the page", "screenshot",
  or "verify the login flow", (3) you need to import cookies from a real browser session
  (Chrome, Arc, Brave, Edge) into the headless context for authenticated testing,
  (4) you see errors like "not logged in", "session expired", or "403 Forbidden" during
  browser testing. Covers the full workflow: cookie extraction → injection → navigation →
  snapshot → interact → diff → verify.
dependencies:
  - playwright
  - "@playwright/test"
alwaysApply: false
tier: 4
metadata:
  version: "1.0"
  sources: "https://github.com/microsoft/playwright-mcp"
---

# Browser Testing — Headless QA with Playwright MCP

Test web UIs, verify rendering, validate auth flows, and perform interactive QA using the
headless Playwright browser via MCP tools. Includes cookie import from real browser sessions
for authenticated testing.

---

## Prerequisites

The Playwright MCP server must be configured in `opencode.json` with `vision,storage` capabilities:

```json
"playwright": {
  "type": "local",
  "command": ["npx", "@playwright/mcp@latest", "--headless", "--caps", "vision,storage", "--ignore-https-errors"],
  "enabled": true
}
```

---

## Tool Reference (Quick)

All Playwright MCP tools are prefixed with `playwright_`. The most-used tools:

| Tool | Purpose |
|------|---------|
| `playwright_browser_navigate` | Go to a URL |
| `playwright_browser_snapshot` | Get accessibility tree (structured text, NOT pixels) |
| `playwright_browser_take_screenshot` | Capture a PNG screenshot |
| `playwright_browser_click` | Click an element by `ref` |
| `playwright_browser_type` | Type text into a focused element |
| `playwright_browser_fill` | Fill a form field by `ref` |
| `playwright_browser_select_option` | Select from a dropdown |
| `playwright_browser_hover` | Hover over an element |
| `playwright_browser_wait_for_page` | Wait for navigation to complete |
| `playwright_browser_cookie_set` | Set a cookie in the browser context |
| `playwright_browser_cookie_get_all` | Get all cookies for current page |
| `playwright_browser_cookie_delete` | Delete cookies |

For the full list, read `references/playwright-mcp-tools.md`.

---

## Core Methodology: Snapshot-First, Not Screenshot-First

The Playwright MCP uses **accessibility tree snapshots** — structured text representations of
the page, not pixel screenshots. Each element gets a `ref` ID you can target for interaction.

**This is the most important concept.** Always snapshot before acting:

1. **Snapshot** → read the accessibility tree, identify element `ref` IDs
2. **Act** → click, fill, select using `ref` IDs (not CSS selectors)
3. **Snapshot again** → compare the new tree to verify your action worked
4. **Screenshot** only when you need visual evidence or layout verification

### Why snapshots beat screenshots

- Snapshots are **text** — they consume far fewer tokens than base64 PNG images
- Snapshots give you **semantic structure** (buttons, links, headings, form fields)
- Snapshots give you **ref IDs** for precise interaction targeting
- Screenshots are useful for **visual regression** and **layout bugs** but expensive

---

## Workflow 1: Unauthenticated Page Testing

For pages that don't require login:

### Step 1: Navigate

```
playwright_browser_navigate({ url: "https://example.com/page" })
```

### Step 2: Snapshot and Orient

```
playwright_browser_snapshot()
```

Read the accessibility tree. Identify:
- Page structure (headings, navigation, content areas)
- Interactive elements and their `ref` IDs
- Any error states or unexpected content

### Step 3: Interact

Target elements by their `ref` from the snapshot:

```
playwright_browser_click({ ref: "e15" })
playwright_browser_fill({ ref: "e22", value: "search term" })
playwright_browser_select_option({ ref: "e30", values: ["option-value"] })
```

### Step 4: Verify

Snapshot again after each interaction to confirm the expected state change:

```
playwright_browser_snapshot()
```

Compare the new tree to the previous one. Look for:
- New elements that appeared (success messages, results, modals)
- Elements that disappeared (loading spinners, previous state)
- Changed text content
- Error messages

### Step 5: Screenshot for Evidence

When you need visual proof:

```
playwright_browser_take_screenshot()
```

---

## Workflow 2: Authenticated Testing (Cookie Import)

When testing pages behind login, import cookies from a real browser session.

### Step 1: Obtain cookies

Ask the user to provide cookies as a JSON array. Each cookie object should have at minimum:
`name`, `value`, `domain`, `path`. Optional fields: `secure`, `httpOnly`, `sameSite`, `expires`.

Example format:

```json
[
  { "name": "_session", "value": "abc123", "domain": ".github.com", "path": "/" },
  { "name": "user_id", "value": "42", "domain": ".github.com", "path": "/" }
]
```

Cookies can be exported from browser DevTools (Application → Cookies), browser extensions
like EditThisCookie or Cookie-Editor, or any tool that produces Playwright-compatible JSON.

### Step 2: Inject cookies into the headless session

First navigate to the target domain (cookies need a matching domain context):

```
playwright_browser_navigate({ url: "https://github.com" })
```

Then set each cookie using the `browser_cookie_set` tool. For each cookie from the JSON:

```
playwright_browser_cookie_set({
  name: "cookie_name",
  value: "cookie_value",
  domain: ".github.com",
  path: "/",
  secure: true,
  httpOnly: false,
  sameSite: "Lax"
})
```

### Step 3: Reload the page

After injecting cookies, reload to pick up the authenticated session:

```
playwright_browser_navigate({ url: "https://github.com" })
```

### Step 4: Verify authentication

Snapshot and confirm you see the authenticated state (user avatar, dashboard, etc.):

```
playwright_browser_snapshot()
```

If you still see a login page, the cookies may have expired. Ask the user to log in to
the browser first, then re-export their cookies.

---

## Workflow 3: Form Testing

Systematic form testing follows this pattern:

1. **Navigate** to the form page
2. **Snapshot** to identify all form fields and their `ref` IDs
3. **Fill** each field in order using `playwright_browser_fill`
4. **Verify** field values stuck by snapshotting again
5. **Submit** via `playwright_browser_click` on the submit button
6. **Check** the response — snapshot for success/error messages
7. **Test error cases** — submit with empty fields, invalid data, boundary values

### Form testing checklist

- [ ] All required fields identified via snapshot
- [ ] Happy path: fill all fields correctly → submit → verify success
- [ ] Empty submission: skip required fields → submit → verify validation errors
- [ ] Boundary values: max-length strings, special characters, unicode
- [ ] Dropdown/select fields: verify all options are present
- [ ] File upload fields: note these may not work in headless mode

---

## Workflow 4: Multi-Page Flow Testing

For flows that span multiple pages (signup, checkout, wizard):

1. **Document the expected flow** before starting (page 1 → page 2 → ... → confirmation)
2. **Snapshot each page** before and after interaction
3. **Track state changes** — what carries forward between pages (form data, URL params, cookies)
4. **Verify the final state** — confirmation page, email sent, data persisted
5. **Test the back button** — `playwright_browser_go_back()` should preserve state

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Session expired" after cookie import | Cookies are stale | Log in to browser, re-extract |
| Snapshot shows login page despite cookies | Wrong domain or path | Check `--include-subdomains`, verify cookie domain matches |
| Snapshot is empty or minimal | Page uses heavy JS/SPA | Wait: `playwright_browser_wait_for_page({ timeout: 5000 })` then re-snapshot |
| Element `ref` not found | Page changed since snapshot | Re-snapshot to get fresh `ref` IDs |
| Cookie injection has no effect | Wrong domain or missing fields | Ensure cookie `domain` matches the target site; include `path: "/"` |
| `playwright_*` tools not available | MCP server not connected | Check `opencode.json` Playwright config (needs `vision,storage` caps); restart OpenCode session |

---

## Performance Tips

- **Snapshot first, screenshot rarely** — snapshots are ~100x cheaper in tokens
- **Don't screenshot every step** — only for visual evidence or layout verification
- **Batch cookie injection** — if many cookies, iterate the JSON array programmatically
- **Reuse sessions** — cookies persist within a Playwright session, no need to re-inject
- **Use `wait_for_page`** for SPAs — JavaScript-heavy apps need time to hydrate

---

## Full Playwright MCP Tool List

For the complete list of 40+ Playwright MCP tools with parameters and usage notes,
read `references/playwright-mcp-tools.md`.