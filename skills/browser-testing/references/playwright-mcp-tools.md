# Playwright MCP Tools Reference

Complete reference for all Playwright MCP tools available when the server is configured
with `--caps vision,storage`. All tool names are prefixed with `playwright_` in OpenCode's
permission system.

---

## Navigation

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_navigate` | `url` (string, required) | Navigate to a URL. Waits for page load. |
| `browser_go_back` | — | Go back in browser history. |
| `browser_go_forward` | — | Go forward in browser history. |
| `browser_wait_for_page` | `timeout` (number, ms, optional) | Wait for navigation or page load to complete. Default timeout varies by config. |

---

## Reading & Snapshots

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_snapshot` | — | Return the page's **accessibility tree** as structured text. Each interactive element gets a `ref` ID (e.g., `[ref=e3]`). This is the primary way to "see" the page — cheaper and more useful than screenshots. |
| `browser_take_screenshot` | `raw` (boolean, optional) | Capture a full-page PNG screenshot. Returns base64-encoded image. Use `raw: true` for uncompressed. **Token-expensive** — prefer snapshots for routine checks. |
| `browser_get_text` | `selector` (string, optional) | Extract visible text content from the page or a specific selector. |

### Snapshot output format

```
[heading] My Page Title
[navigation] Main Nav
  [link ref=e1] Home
  [link ref=e2] Dashboard
  [link ref=e3] Settings
[main]
  [heading] Welcome Back
  [textbox ref=e4] Search...
  [button ref=e5] Search
  [list]
    [listitem] Item one
    [listitem] Item two
```

Use `ref` values (e.g., `e4`, `e5`) to target elements in interaction tools.

---

## Interaction — Click & Press

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_click` | `ref` (string, required) | Click an element identified by its snapshot `ref`. |
| `browser_drag` | `startRef` (string), `endRef` (string) | Drag from one element to another. |
| `browser_hover` | `ref` (string, required) | Hover over an element. Useful for revealing tooltips, dropdown menus. |
| `browser_press_key` | `key` (string, required) | Press a keyboard key. Supports combo syntax: `Control+a`, `Enter`, `Tab`, `Escape`, `ArrowDown`, etc. |

---

## Interaction — Text Input

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_type` | `text` (string, required), `submit` (boolean, optional) | Type text into the currently focused element. Set `submit: true` to press Enter after typing. |
| `browser_fill` | `ref` (string, required), `value` (string, required) | Clear a form field and fill it with the given value. More reliable than `type` for form fields — clears existing content first. |
| `browser_select_option` | `ref` (string, required), `values` (string[], required) | Select option(s) in a `<select>` element by their value attribute. |

### When to use `fill` vs `type`

- **`fill`** — For form fields (inputs, textareas). Clears existing content first. Targets by `ref`.
- **`type`** — For typing into the focused element. Does NOT clear. Use after clicking into a field, or for search boxes and non-standard inputs.

---

## Tabs

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_tab_list` | — | List all open tabs with their titles and URLs. |
| `browser_tab_new` | `url` (string, optional) | Open a new tab, optionally navigating to a URL. |
| `browser_tab_select` | `index` (number, required) | Switch to a tab by index (0-based). |
| `browser_tab_close` | `index` (number, optional) | Close a tab by index. Closes current tab if index omitted. |

---

## Storage — Cookies (requires `--caps storage`)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_cookie_get` | `name` (string, required), `url` (string, optional) | Get a specific cookie by name. |
| `browser_cookie_get_all` | `url` (string, optional) | Get all cookies, optionally filtered by URL. |
| `browser_cookie_set` | `name`, `value`, `domain`, `path`, `secure`, `httpOnly`, `sameSite`, `expires` | Set a cookie. Required: `name`, `value`, `domain`. |
| `browser_cookie_delete` | `name` (string, required), `url` (string, optional), `domain` (string, optional), `path` (string, optional) | Delete a cookie by name. |
| `browser_cookie_clear` | — | Delete all cookies in the browser context. |

### Cookie set parameter details

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | ✅ | — | Cookie name |
| `value` | string | ✅ | — | Cookie value |
| `domain` | string | ✅ | — | Domain (prefix with `.` for subdomain matching) |
| `path` | string | ❌ | `"/"` | Cookie path |
| `secure` | boolean | ❌ | `false` | HTTPS only |
| `httpOnly` | boolean | ❌ | `false` | Not accessible via JavaScript |
| `sameSite` | string | ❌ | `"Lax"` | `"Strict"`, `"Lax"`, or `"None"` |
| `expires` | number | ❌ | session | Unix timestamp for expiry. Omit for session cookie. |

---

## Storage — Local/Session Storage (requires `--caps storage`)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_storage_get` | `key` (string, optional), `storageType` (`"local"` or `"session"`) | Get a storage item by key, or all items if key omitted. |
| `browser_storage_set` | `key` (string), `value` (string), `storageType` (`"local"` or `"session"`) | Set a storage item. |
| `browser_storage_delete` | `key` (string), `storageType` (`"local"` or `"session"`) | Delete a storage item. |

---

## JavaScript Evaluation

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_evaluate` | `expression` (string, required) | Execute JavaScript in the page context and return the result. Use for custom checks, data extraction, or interactions not covered by other tools. |

### Common evaluation patterns

```javascript
// Check if an element exists
document.querySelector('.error-banner') !== null

// Get computed styles
getComputedStyle(document.querySelector('.header')).backgroundColor

// Count list items
document.querySelectorAll('li.search-result').length

// Read meta tags
document.querySelector('meta[name="description"]')?.content

// Check console errors (limited — see browser_console tools)
window.__errors || []
```

---

## Console & Network (requires `--caps devtools` for full access)

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_console_messages` | — | Get captured console messages (log, warn, error, info). |

Note: Full network interception (`browser_route_*` tools) requires `--caps network`, which
is not enabled in the default configuration. Add `network` to `--caps` if you need request
mocking or response interception.

---

## Dialogs

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_handle_dialog` | `accept` (boolean, required), `promptText` (string, optional) | Handle a JavaScript dialog (alert, confirm, prompt). Must be called while dialog is open. |

---

## File Upload

| Tool | Parameters | Description |
|------|-----------|-------------|
| `browser_file_upload` | `ref` (string, required), `paths` (string[], required) | Upload file(s) to a file input element. Provide absolute paths to local files. |

---

## Usage Patterns

### Pattern: Snapshot → Act → Verify loop

```
1. browser_snapshot()                    → identify ref IDs
2. browser_click({ ref: "e5" })          → interact
3. browser_snapshot()                    → verify state changed
4. browser_take_screenshot()             → visual evidence (optional)
```

### Pattern: Form fill and submit

```
1. browser_snapshot()                    → find form fields
2. browser_fill({ ref: "e10", value: "user@example.com" })
3. browser_fill({ ref: "e11", value: "password123" })
4. browser_click({ ref: "e12" })         → submit button
5. browser_wait_for_page()               → wait for redirect
6. browser_snapshot()                    → verify logged in
```

### Pattern: Cookie-authenticated testing

```
1. browser_navigate({ url: "https://target.com" })   → establish domain context
2. browser_cookie_set({ name, value, domain, ... })   → inject auth cookies (repeat per cookie)
3. browser_navigate({ url: "https://target.com/dashboard" })  → reload with auth
4. browser_snapshot()                                  → verify authenticated state
```

### Pattern: Multi-tab comparison

```
1. browser_tab_new({ url: "https://staging.app.com/page" })
2. browser_snapshot()                    → snapshot staging
3. browser_tab_new({ url: "https://prod.app.com/page" })
4. browser_snapshot()                    → snapshot production
5. Compare the two snapshots for differences
```
