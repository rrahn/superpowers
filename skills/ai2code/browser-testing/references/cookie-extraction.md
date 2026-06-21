# Cookie Extraction — Detailed Reference

This document covers the `extract-cookies.py` script in depth: how it works, browser-specific
quirks, troubleshooting, and security considerations.

The script lives at `~/.opencode/scripts/extract-cookies.py`.

---

## How It Works

### Overview

1. **Locate** the browser's cookie SQLite database on disk
2. **Read** the macOS Keychain to get the browser's "Safe Storage" password
3. **Derive** an AES-128-CBC key via PBKDF2 (salt: `saltysalt`, iterations: 1003, SHA-1)
4. **Decrypt** each `v10`-prefixed `encrypted_value` in the Cookies table
5. **Output** Playwright-compatible JSON to stdout

All operations are local. The script makes **zero network calls**.

### Decryption Pipeline

```
macOS Keychain
  → security find-generic-password -s "<Browser> Safe Storage" -w
  → base64-encoded password string

PBKDF2
  → password + salt="saltysalt" + 1003 iterations + SHA-1 + keylen=16
  → 16-byte AES-128 key

For each cookie row:
  → Strip "v10" prefix (3 bytes)
  → IV = 16 bytes of 0x20 (space character)
  → AES-128-CBC decrypt
  → PKCS7 unpad
  → UTF-8 decode → cookie value
```

`pycookiecheat` handles this pipeline internally. The script is a thin wrapper that adds
multi-browser support, profile selection, and Playwright-compatible output formatting.

---

## Installation

The script uses an inline PEP 723 metadata block plus a `uv run` shebang — dependencies
are resolved automatically on first run into an ephemeral uv-managed environment.
**No manual install is required.** Execute the script directly:

```bash
~/.opencode/scripts/extract-cookies.py --domain github.com
```

On first run, `uv` fetches `pycookiecheat` and its transitive deps and caches them.
Subsequent runs reuse the cache and start near-instantly.

If you prefer an explicit invocation (debugging, forcing a fresh env), call `uv run`:

```bash
uv run ~/.opencode/scripts/extract-cookies.py --domain github.com
```

The only prerequisite is `uv` itself on your `PATH` (`uv --version` to check).

### Dependencies (resolved automatically by `uv run`)

| Package | Purpose | Risk |
|---------|---------|------|
| `pycookiecheat` | Cookie decryption + Keychain access | MIT license, 800+ stars, audited — no network calls |
| `cryptography` | AES + PBKDF2 primitives (transitive dep) | Industry-standard, PyCA-maintained |
| `keyring` | macOS Keychain access (transitive dep) | Well-known, audited |

No other dependencies are required. The inline PEP 723 block in the script pins these
explicitly; nothing else leaks into the runtime.

---

## Usage

### Basic Extraction

```bash
# Extract cookies for a single domain from the default browser
~/.opencode/scripts/extract-cookies.py --domain github.com

# Output:
# [
#   {"name": "_gh_sess", "value": "abc123...", "domain": "github.com", "path": "/", ...},
#   {"name": "user_session", "value": "def456...", "domain": "github.com", "path": "/", ...}
# ]
```

### Specifying a Browser

```bash
~/.opencode/scripts/extract-cookies.py --domain github.com --browser arc
~/.opencode/scripts/extract-cookies.py --domain github.com --browser brave
~/.opencode/scripts/extract-cookies.py --domain github.com --browser edge
~/.opencode/scripts/extract-cookies.py --domain github.com --browser chrome
```

### Specifying a Profile

Chromium-based browsers support multiple profiles (`Default`, `Profile 1`, `Profile 2`, etc.).

```bash
# List available browsers and profiles first
~/.opencode/scripts/extract-cookies.py --list-browsers

# Extract from a specific profile
~/.opencode/scripts/extract-cookies.py --domain github.com --browser chrome --profile "Profile 1"
```

### Multiple Domains

```bash
~/.opencode/scripts/extract-cookies.py \
  --domain github.com \
  --domain gitlab.com \
  --domain bitbucket.org
```

### Subdomain Matching

By default, cookies are extracted for the exact domain. Use `--include-subdomains` to
prefix the domain with a dot, which makes the cookie valid for all subdomains:

```bash
# Without: cookie domain = "github.com" (exact match only)
~/.opencode/scripts/extract-cookies.py --domain github.com

# With: cookie domain = ".github.com" (matches api.github.com, gist.github.com, etc.)
~/.opencode/scripts/extract-cookies.py --domain github.com --include-subdomains
```

### Output Formats

```bash
# JSON (default) — pipe-friendly, parseable by agents
~/.opencode/scripts/extract-cookies.py --domain github.com --format json

# Shell — human-readable summary with instructions for manual injection
~/.opencode/scripts/extract-cookies.py --domain github.com --format shell
```

---

## Browser-Specific Notes

### Chrome

- **Keychain service**: `Chrome Safe Storage`
- **Data directory**: `~/Library/Application Support/Google/Chrome/`
- **Profiles**: `Default`, `Profile 1`, `Profile 2`, ...
- **Notes**: Most reliable. The "standard" Chromium cookie format.

### Arc

- **Keychain service**: `Arc Safe Storage`
- **Data directory**: `~/Library/Application Support/Arc/User Data/`
- **Profiles**: `Default`, `Profile 1`, ...
- **Notes**: Arc uses the same Chromium cookie format. Works identically to Chrome.

### Brave

- **Keychain service**: `Brave Safe Storage`
- **Data directory**: `~/Library/Application Support/BraveSoftware/Brave-Browser/`
- **Profiles**: `Default`, `Profile 1`, ...
- **Notes**: Brave's aggressive cookie blocking may mean fewer cookies are stored.
  If cookies are missing, check Brave's shield settings for that site.

### Edge

- **Keychain service**: `Microsoft Edge Safe Storage`
- **Data directory**: `~/Library/Application Support/Microsoft Edge/`
- **Profiles**: `Default`, `Profile 1`, ...
- **Notes**: Same Chromium format. Works reliably.

### Chromium (vanilla)

- **Keychain service**: `Chromium Safe Storage`
- **Data directory**: `~/Library/Application Support/Chromium/`
- **Notes**: Uncommon on macOS. Only present if manually installed.

### Opera

- **Keychain service**: `Opera Safe Storage`
- **Data directory**: `~/Library/Application Support/com.operasoftware.Opera/`
- **Notes**: Less tested. Report issues if encountered.

### Unsupported Browsers

| Browser | Status | Reason |
|---------|--------|--------|
| Safari | ❌ Not supported | Uses a completely different cookie storage format (binary cookies, not SQLite + AES) |
| Firefox | ❌ Not supported | Uses its own NSS-based encryption, not Chromium's v10 scheme |
| Comet (Perplexity) | ❌ Not yet | Uses `Comet Safe Storage` — could be added to the registry |

---

## Troubleshooting

### Keychain Access Prompts

**Symptom**: macOS shows a dialog: "python wants to use your confidential information
stored in 'Chrome Safe Storage' in your keychain."

**Fix**: Click **Always Allow** (not just Allow). If you click "Allow" once, the prompt
will reappear on the next extraction. "Always Allow" persists the permission.

If you accidentally clicked "Deny":
1. Open **Keychain Access** (Spotlight → "Keychain Access")
2. Search for "Chrome Safe Storage" (or the relevant browser)
3. Double-click the entry → Access Control tab
4. Add the Python binary to the allowed applications list

### Database Locked Errors

**Symptom**: `sqlite3.OperationalError: database is locked`

**Cause**: The browser is running and has an exclusive lock on the Cookies database.

**Fix**: `pycookiecheat` handles this automatically by copying the database + WAL + SHM
files to a temporary location before reading. If you still encounter lock errors:
1. Quit the browser
2. Re-run the extraction
3. Restart the browser

### No Cookies Found

**Symptom**: Script outputs `[]` with a "No cookies found" warning.

**Possible causes**:

| Cause | Check | Fix |
|-------|-------|-----|
| Never logged in | Open the domain in the browser and log in | Log in, then re-extract |
| Wrong browser | `--list-browsers` to check what's installed | Specify `--browser <name>` |
| Wrong profile | `--list-browsers` shows profiles | Specify `--profile <name>` |
| Cookies cleared | Check browser settings for auto-clear | Re-login and extract immediately |
| Brave shields | Brave blocks third-party cookies aggressively | Disable shields for that site |
| Expired cookies | Session timed out | Re-login to the site |

### Expired or Invalid Cookies

**Symptom**: Cookies inject successfully, but the site still shows a login page.

**Cause**: The session cookie has expired server-side even though it still exists in
the browser's database.

**Fix**: Open the site in your browser, verify you're logged in (refresh the page),
then immediately re-extract. Session cookies are typically valid for the duration of
the browser session or until the server expires them.

### pycookiecheat Import Error

**Symptom**: `Error: pycookiecheat is not installed.`

**Cause**: The script was invoked in a way that bypassed the `uv run` shebang — typically
by running `python ~/.opencode/scripts/extract-cookies.py ...` instead of executing the
script directly. The `python` interpreter doesn't honor the PEP 723 metadata block, so it
starts without `pycookiecheat` in scope.

**Fix** — let the shebang fire (or invoke `uv run` explicitly):

```bash
# Recommended: execute the script directly so the shebang resolves deps
~/.opencode/scripts/extract-cookies.py --domain github.com

# Equivalent: explicit uv run
uv run ~/.opencode/scripts/extract-cookies.py --domain github.com
```

If the error persists, verify `uv` is installed and on your `PATH`: `uv --version`.

---

## Security Considerations

### What the Script Accesses

- **macOS Keychain**: reads the browser's "Safe Storage" password (encrypted at rest by macOS)
- **Cookie SQLite database**: read-only access to `~/Library/Application Support/<browser>/*/Cookies`
- **stdout**: outputs decrypted cookies as JSON

### What the Script Does NOT Do

- ❌ Makes no network calls of any kind
- ❌ Does not write to disk (unless you redirect stdout)
- ❌ Does not modify the browser's cookie database
- ❌ Does not send cookies to any remote endpoint
- ❌ Does not log or cache cookies between runs

### Risks

| Risk | Mitigation |
|------|------------|
| Cookies in terminal scrollback | Pipe to a temp file, delete after injection: `> /tmp/cookies.json && rm /tmp/cookies.json` |
| Cookies in OpenCode session history | Session context includes tool output — be aware that extracted cookies may appear in session logs |
| Stale temp files | The script itself never writes temp files. If you redirect to a file, clean it up promptly. |
| Keychain permission persisted | "Always Allow" grants permanent Python access to the keychain item. Revoke in Keychain Access if needed. |

### Best Practices

1. **Extract only what you need** — specify `--domain` precisely, don't extract everything
2. **Clean up temp files** — if you pipe to `/tmp/cookies.json`, delete it after injection
3. **Don't commit cookies** — add `/tmp/cookies.json` patterns to `.gitignore` as defense in depth
4. **Re-extract rather than cache** — cookies change frequently; don't store them long-term
5. **Use `--profile`** — if you have a dedicated testing profile, use that instead of your main profile