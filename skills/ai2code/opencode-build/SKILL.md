---
name: opencode-build
description: >
  Build, sign, and install the OpenCode CLI binary from a local source checkout.
  Use when: building opencode from source, compiling opencode, installing opencode
  from a fork, rebuilding the opencode binary, updating opencode to include local
  changes, or opencode --version shows an old version. Triggers on: build opencode,
  compile opencode, install opencode from source, rebuild opencode binary, Killed: 9
  after running opencode, SELF_SIGNED_CERT_IN_CHAIN during bun build,
  UNABLE_TO_GET_ISSUER_CERT_LOCALLY, codesign, Mach-O, opencode dev build.
metadata:
  version: "1.0.0"
  sources: "https://github.com/anomalyco/opencode, https://bun.sh/docs/bundler/executables"
user-invocable: true
---

# Build OpenCode from Source

Compile the OpenCode CLI into a standalone binary from a local clone and install
it, replacing the existing `~/.opencode/bin/opencode` binary.

---

## Problem

The installed OpenCode binary (`~/.opencode/bin/opencode`) is outdated or missing
local changes from your fork. You need to rebuild from source, produce a single-file
executable, and install it — without breaking the existing install or triggering macOS
Gatekeeper rejections.

## Trigger Conditions

- You want to test local OpenCode changes end-to-end.
- `opencode --version` shows a version older than expected.
- You need a dev build that includes uncommitted or branched changes.
- Build fails with `SELF_SIGNED_CERT_IN_CHAIN` or `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`.
- Running the freshly built binary produces `Killed: 9` (macOS Gatekeeper).

---

## Solution

### Prerequisites

- **Bun >= 1.3.10** installed (`bun --version` to check).
- A local clone of the OpenCode repo (monorepo layout with `packages/opencode/`).

### Step 1: Navigate to the CLI package

```sh
cd ~/Code/opencode/packages/opencode
```

The repo is a monorepo. The CLI lives at `packages/opencode/`, not the repo root.

### Step 2: Build the standalone binary

```sh
bun run script/build.ts --single --skip-install
```

**Flags explained:**

| Flag              | Purpose                                                                      |
| ----------------- | ---------------------------------------------------------------------------- |
| `--single`        | Build only for the current platform (not all 11 targets). Much faster.       |
| `--skip-install`  | Skip downloading cross-platform native addons. Avoids TLS/proxy cert errors. |

The build script:
1. Fetches the latest models snapshot from models.dev.
2. Bundles SQL migrations into the binary.
3. Uses Bun's native `compile` mode to produce a single-file ~110 MB Mach-O executable.
4. Produces an ad-hoc signed binary (no manual codesigning needed).

**Output path** (Apple Silicon Mac):

```
dist/opencode-darwin-arm64/bin/opencode
```

Dev builds produce version `0.0.0-<branch>-YYYYMMDDHHmm`, where the branch name is embedded in the version string (e.g., `0.0.0-main-202603231252` on the `main` branch, `0.0.0-dev-202603231252` on a `dev` branch). To override:

```sh
OPENCODE_VERSION=1.2.3 bun run script/build.ts --single --skip-install
```

### Step 3: Backup the current binary

```sh
cp ~/.opencode/bin/opencode ~/.opencode/bin/opencode.bak.$(date +%Y%m%d)
```

Timestamped backup so you can roll back if the new build is broken.

### Step 4: Install the new binary

```sh
cp dist/opencode-darwin-arm64/bin/opencode ~/.opencode/bin/opencode
```

### Step 5: Verify

```sh
opencode --version
```

Expected output: the version you built (e.g., `0.0.0-main-202506151430` on the `main` branch, `0.0.0-dev-202506151430` on a `dev` branch, or the
`OPENCODE_VERSION` you set).

---

## Quick Copy-Paste (Full Sequence)

Run from the `packages/opencode/` directory:

```sh
bun run script/build.ts --single --skip-install
cp ~/.opencode/bin/opencode ~/.opencode/bin/opencode.bak.$(date +%Y%m%d)
cp dist/opencode-darwin-arm64/bin/opencode ~/.opencode/bin/opencode
opencode --version
```

---

## Troubleshooting

### `Killed: 9` when running the binary

macOS Gatekeeper rejected the executable. Re-sign it with an ad-hoc signature:

```sh
codesign -s - ~/.opencode/bin/opencode
```

Then retry `opencode --version`. This happens when the copy operation or a
quarantine attribute strips the existing ad-hoc signature.

### `SELF_SIGNED_CERT_IN_CHAIN` or `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`

Corporate proxy / TLS inspection is intercepting HTTPS. The `--skip-install`
flag avoids the network calls that trigger this. If you already used
`--skip-install` and still see the error, the models.dev fetch may be failing.
Set `NODE_TLS_REJECT_UNAUTHORIZED=0` as a last resort:

```sh
NODE_TLS_REJECT_UNAUTHORIZED=0 bun run script/build.ts --single --skip-install
```

### Build output path varies by platform

| Platform            | Output path                               |
| ------------------- | ----------------------------------------- |
| macOS Apple Silicon | `dist/opencode-darwin-arm64/bin/opencode`  |
| macOS Intel         | `dist/opencode-darwin-x64/bin/opencode`    |
| Linux x64           | `dist/opencode-linux-x64/bin/opencode`     |

### Rolling back

If the new build is broken, restore from the backup:

```sh
cp ~/.opencode/bin/opencode.bak.YYYYMMDD ~/.opencode/bin/opencode
```

Replace `YYYYMMDD` with the actual date suffix from Step 3.

---

## Notes

- The build produces a fully self-contained binary — no runtime dependencies on Bun or Node.
- Bun's compile mode embeds the JavaScript bundle, SQLite native addon, and the Bun runtime into a single Mach-O executable.
- The `--single` flag is critical for speed — without it, the build script compiles for all 11 platform/arch combinations.
- Dev builds (`0.0.0-<branch>-*`) are functionally identical to release builds; only the version string differs.
- Clean old backups periodically: `ls ~/.opencode/bin/opencode.bak.*` to list, `rm` to remove.
