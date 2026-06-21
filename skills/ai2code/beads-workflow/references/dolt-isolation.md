# Multi-Project Dolt Isolation

Read this when `bd list` shows wrong or missing issues, or when you suspect a Dolt port collision
between multiple beads-enabled projects.

---

## Problem

`bd` connects to a Dolt SQL server on a configured port (default: 3307). When multiple
beads-enabled projects share the same port, `bd` silently connects to **whichever server
happens to be running** — regardless of which project owns it. This causes:

- **Silent data loss**: `bd list` returns issues from the wrong project's snapshot
- **Stale reads**: The connected server may hold a frozen copy of your database from when
  it was first created, while the on-disk Dolt repo has advanced far beyond
- **Remote divergence**: Dolt auto-push (`dolt.auto-push=true`) from the wrong server pushes a stale snapshot to S3, overwriting the correct remote state

The failure is silent because a single Dolt server can host multiple databases. If project A's
server is running and project B connects to it, the server may contain a `projectB` database —
but it's a stale snapshot from when both projects shared the server, not the live on-disk data.

## Prevention: assign unique ports per project

Each project must configure a distinct Dolt port. Persist the port in both the Dolt server
config and the beads metadata so all tools agree:

```bash
bd dolt set port 3307 --update-config   # writes to metadata.json AND .beads/dolt/config.yaml
```

Codify port assignments in each project's justfile to prevent drift:

```just
_bd_dolt_port := "3307"    # project A
# In project B's justfile: _bd_dolt_port := "3308"
```

## Diagnosis: detecting a port collision

**Symptom**: `bd list` shows fewer issues than expected, or issues you created are missing.

1. **Compare live server vs on-disk data**:
   ```bash
   # What the server thinks (via bd):
   bd list --json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"

   # What's actually on disk:
   cd .beads/dolt/<dbname> && dolt sql -r json -q "SELECT COUNT(*) FROM issues;"
   ```
   If these differ, the server is stale.

2. **Check which process owns the port**:
   ```bash
   lsof -iTCP:3307 -sTCP:LISTEN
   # Look at the PID's CWD — does it point to YOUR project's .beads/dolt?
   lsof -p <PID> -Fn | grep '\.beads/dolt'
   ```

3. **Cross-reference git commits against beads IDs**:
   ```bash
   # Issue IDs referenced in git commits:
   git log --oneline --all --format="%s" | grep -oE '<prefix>-[a-zA-Z0-9.]+' | sort -u

   # Issue IDs in beads:
   bd list --json | python3 -c "import sys,json; [print(d['id']) for d in json.load(sys.stdin)]" | sort
   ```
   Any git-referenced IDs missing from `bd list` confirms data loss.

## Recovery

```bash
bd dolt stop                                   # stop the stale/wrong server
bd dolt set port <correct-port> --update-config  # ensure correct port
bd dolt start                                  # restart from on-disk data
bd dolt test                                   # verify connection
bd list --json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"  # verify count
```

## Beads startup recipes (justfile pattern)

```just
_bd_dolt_port := "3307"
_bd_ui_port   := "3000"

bd-start:
  #!/usr/bin/env bash
  set -euo pipefail
  bd dolt set port {{_bd_dolt_port}} --update-config
  if lsof -iTCP:{{_bd_dolt_port}} -sTCP:LISTEN -t >/dev/null 2>&1; then
    STALE_PID=$(lsof -iTCP:{{_bd_dolt_port}} -sTCP:LISTEN -t)
    STALE_CWD=$(lsof -p "$STALE_PID" -Fn 2>/dev/null | grep '^n.*\.beads/dolt' | head -1 || true)
    if echo "$STALE_CWD" | grep -q "$(pwd)/.beads/dolt"; then
      echo "Dolt already running for this project (PID $STALE_PID)"
    else
      echo "Port {{_bd_dolt_port}} held by PID $STALE_PID (wrong project) — killing"
      kill "$STALE_PID" 2>/dev/null || true
      sleep 1
    fi
  fi
  bd dolt start
  bd dolt test

bdui-start:
  #!/usr/bin/env bash
  set -euo pipefail
  bdui start --port {{_bd_ui_port}}

bd-up: bd-start bdui-start
bd-down: bdui-stop bd-stop
```
