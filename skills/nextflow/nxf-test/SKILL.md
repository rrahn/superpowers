---
name: nxf-test
description: >
  Run the test suite of a Nextflow / nf-core pipeline after changing pipeline code —
  discover the available test profiles and container runtimes, ask the user which runtime
  profile to use, validate the DAG with a stub run, execute the `test` profile, and run
  nf-test if the repository is configured for it.
  Use when: you edited a `.nf` file, a `nextflow.config`, a module, a subworkflow, or a
  script called by a process, and you need to prove the pipeline still executes; or the
  user says "run the nextflow tests", "test the pipeline", "does the pipeline still run".
  This skill EXECUTES tests. It does not write them.
markers:
  - nextflow.config
  - main.nf
globs:
  - "**/*.nf"
  - "**/nextflow.config"
  - "**/conf/*.config"
  - "**/*.nf.test"
alwaysApply: false
---

# Running the tests of a Nextflow pipeline

## Core rule

**Changing a Nextflow pipeline is a code change, so it follows TDD like any other.**
A change to `main.nf`, a workflow, a module, a `.config`, or a script a process calls is
not finished until the pipeline has been shown to still execute. "It looks right" is not
evidence. A green stub run is evidence.

Never report a pipeline change as done without having run at least Phase 2 below.

## Scope

This skill executes an existing test suite. Writing `.nf.test` files, designing test data
or adding a `test` profile is out of scope — if the repository has no tests, say so and
stop; do not invent them here.

---

## Phase 0 — Discover what the repository offers

Never assume the profile names or that a container runtime is on PATH. Look first.

```fish
cd <pipeline-root>

# Which profiles exist? The `test*` ones and the runtime ones are what matter.
grep -n "^profiles" -A 200 nextflow.config | grep -E "^\s*[0-9]+[-:]\s*[a-z_]+\s*\{"

# Which test configs exist?
ls conf/test*.config

# Is nf-test configured for this repo? (config at the root is what makes
# `nf-test test` work pipeline-wide)
ls nf-test.config
find . -name "*.nf.test" -not -path "./work/*"

# What does CI actually run? This is the authoritative command to copy.
sed -n 1,200p .github/workflows/ci.yml
```

Then check the tooling:

```fish
command -v nextflow; nextflow -v
command -v nf-test; nf-test version
command -v docker; command -v singularity; command -v apptainer; command -v conda
```

**PATH gotcha:** a container runtime can be installed but missing from the shell's PATH
(common on macOS with Docker Desktop). If `command -v docker` fails, check the usual
locations before concluding it is unavailable:

```fish
ls /usr/local/bin/docker /opt/homebrew/bin/docker ~/.docker/bin/docker
```

If it is there, prepend it for the session rather than telling the user docker is missing:

```fish
set -x PATH /usr/local/bin $PATH
docker info --format "{{.ServerVersion}}"
```

## Phase 1 — Ask which runtime profile to use

**Always ask. Do not pick silently.** The runtime profile decides whether the run uses
containers, conda or the bare host, and only the user knows which one is appropriate on
this machine or cluster.

Ask with the choices you actually found in Phase 0, marking the CI profile as
recommended, and say which runtimes are and are not installed. Typical set:

| Profile | When |
|---|---|
| `docker` | Default. Matches most nf-core CI. |
| `singularity` / `apptainer` | HPC, no root. |
| `podman` | Rootless docker replacement. |
| `conda` / `mamba` | No container runtime available; slow first build. |
| `wave` | Containers built on the fly from conda recipes. |

Combine the runtime profile with the pipeline's own profiles in CI order, for example
`-profile nonroot,test,docker`. Profile order matters: later profiles override earlier
ones.

## Phase 2 — Stub run (the fast gate, always do this)

A stub run walks the whole DAG and executes each process's `stub:` block instead of its
real script. It proves the channel wiring, the output globs and the emitted file names
still line up — which is exactly what a refactor breaks — in seconds, with no credentials,
no S3 and no compute.

```fish
cd <pipeline-root>
nextflow run . -profile test,<runtime> -stub-run --outdir /tmp/nxf-stub -ansi-log false
```

Read the outcome carefully:

- **`Succeeded: N`, exit 0** → the DAG is intact. Good.
- **`Missing output file(s) ... expected by process`** → an output glob in a module no
  longer matches what the `stub:` block touches. Renaming a published file is the usual
  cause. Fix both the `output:` and the `stub:` in that module.
- **`No such variable` / `Unknown method`** → a channel or param was renamed in one place
  only.
- **`Access to 'X' is undefined`** → a `.out.<name>` emit was renamed; update the consumer.

A stub run only tests what the stubs declare. If a process has no `stub:` block, it is
skipped in this phase — note that in your report rather than claiming full coverage.

### Override: continue even though the stub run failed

A stub run can fail for a reason that has nothing to do with your change — most often a
`stub:` block that was already broken before you touched the repository, and that blocks
the DAG at a process upstream of the one you edited. Fixing it may be a separate piece of
work the user wants to defer.

The user may therefore say "run the test profile anyway" / "ignore the stub failure" /
"we will fix the stub later". When they do, **skip straight to Phase 3**. Do not refuse,
and do not silently fix the stub instead.

Before continuing, do these three things:

1. **Establish the failure is not yours.** Show it: `git log --oneline -3 -- <failing/module.nf>`
   against the commits on your branch, plus the specific defect (a glob that cannot match
   what the stub touches, an unset `env(...)`, a wrong `prefix`). If the failure *is* in
   code you changed, say so and fix it — the override is not for that case.
2. **Record it**, so it is not forgotten: ask the user, then `gh issue create` rather
   than leaving it only in the chat.
3. **Carry the caveat into the final report.** The stub gate did not pass. Say exactly
   that, and say which process it stopped at.

The real run in Phase 3 exercises the same DAG for real, so a green Phase 3 is stronger
evidence than Phase 2 and it is legitimate to rely on it alone. What is never legitimate
is reporting "tests pass" when neither phase completed.

## Phase 3 — Real `test` profile run (ask before running)

The `test` profile runs the pipeline for real on a small dataset. It usually needs
network, cloud credentials and non-trivial compute, so **ask the user before starting it**
unless they already told you to go all the way.

```fish
# Secrets, if the CI workflow sets any:
nextflow secrets set <NAME> <value>     # never echo the value into the transcript

nextflow run . -profile <ci-profiles> --outdir ./results -ansi-log false -resume
```

- Use exactly the profile string CI uses (Phase 0).
- `-resume` reuses the cached work directory, so a re-run after a small fix is cheap.
- Never run `nextflow clean` or delete `work/` without asking — that throws away the
  resume cache and any in-progress results.
- If the pipeline needs credentials you do not have, stop and say so. Do not guess at
  secret values, and never put a secret in a command you report back.

### The image-lag trap

`ModuleNotFoundError` / `command not found` inside a process, for something you *did* add
to `environment.yml`, almost always means the **published container image is older than the
dependency**. Processes usually pin a floating tag such as `:latest`, and that image is
rebuilt by a separate workflow that only fires on the default branch — so on a feature
branch the pipeline still runs against an image that predates your change.

This is a real finding, not noise: it means the change cannot run until the image is
rebuilt, and the merge order matters. Check `.github/workflows/*docker*` for what triggers
the rebuild, then report it. Building the image locally under the same tag is possible but
often slow and needs registry access, so ask before doing it.

## Phase 4 — nf-test (only if the repo is configured for it)

**Check first, and skip cleanly if it is not set up.** A repository is nf-test-configured
when `nf-test.config` exists at the root; without it `nf-test test` has nothing to
discover, and the stray `*.nf.test` files that ship with the nf-core template do not count.

```fish
ls nf-test.config
```

- **Present** → run the whole suite:
  ```fish
  nf-test test --profile <runtime> --verbose
  ```
  Useful narrowing while fixing one thing: `nf-test test <path/to/main.nf.test>`,
  `--tag <tag>`, and `nf-test test --only-changed` to run just what your diff touches.

  Snapshot failures (`Snapshot mismatch`) mean the recorded output changed. Do **not**
  run `--update-snapshot` on your own: a changed snapshot is either a real regression or
  an intended output change, and only the user can say which. Show the diff and ask.

- **Absent** → skip this phase and say plainly: "nf-test is not configured for this
  repository (no `nf-test.config`), so nf-test was skipped." Writing that configuration is
  a separate task, out of scope for this skill.

## Phase 5 — Report

State, in plain language:

1. Which profile string was used, and which runtime.
2. Stub run: pass or fail, and the process count. If it failed and was overridden, say so
   and name the process it stopped at and the issue that tracks it.
3. Real `test` run: pass, fail, or "not run (why)".
4. nf-test: results, or "skipped — not configured".
5. Anything the run could not cover (processes without `stub:`, phases skipped for lack
   of credentials).

Do not claim more coverage than the phases you actually ran.

---

## Quick reference

```fish
# discovery
grep -n "^profiles" -A 200 nextflow.config
ls conf/test*.config nf-test.config
sed -n 1,200p .github/workflows/ci.yml

# fast gate
nextflow run . -profile test,docker -stub-run --outdir /tmp/nxf-stub -ansi-log false

# real run (ask first)
nextflow run . -profile nonroot,test,docker --outdir ./results -ansi-log false -resume

# nf-test, only when nf-test.config exists
nf-test test --profile docker --verbose
```

## fish shell notes

- No heredocs. Write a script to a file and run it instead.
- Use `;` between commands, and `and` rather than `&&`. A failing command in an `and`
  chain silently swallows the rest of the line — during discovery prefer `;` so every
  probe reports.
- Braces are expanded by fish; quote Go templates, e.g. `docker info --format "{{.ID}}"`.
- `set -x NXF_ANSI_LOG false` once, instead of repeating `-ansi-log false`.
