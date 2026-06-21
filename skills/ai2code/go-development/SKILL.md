---
name: go-development
description: >
  Go project tooling with go build, go test, go vet, golangci-lint, and Cobra CLI patterns —
  project discovery, validation commands, coding standards, and interface design principles.
  Use when: working in a Go project, writing Go code, running tests, linting, or designing
  Go interfaces. Covers module layout, error handling, table-driven tests, and the internal/
  package convention.
markers:
  - go.mod
  - go.sum
globs:
  - "**/*.go"
  - "**/go.mod"
alwaysApply: false
tier: 1
metadata:
  version: "1.0"
  sources: "https://go.dev/doc/effective_go, https://go.dev/wiki/CodeReviewComments"
user-invocable: true
---

# Go Development

Build, test, lint, and ship Go code. Front-loads the commands you run most.

## Project Discovery

Detect the Go project root and understand its layout before doing anything else.

### Identify the module root

Look for `go.mod` in the working directory or its ancestors. The directory containing
`go.mod` is the module root. All commands run from here.

```
go.mod          → module root (run all commands here)
go.sum          → dependency checksums (committed, never hand-edit)
Makefile        → build/test/lint targets
.golangci.yml   → golangci-lint v2 configuration
```

### Map the source tree

Standard Go project layout:

```
cmd/
  gt/              → main CLI binary (Cobra root command)
  gt-proxy-client/ → proxy client binary
  gt-proxy-server/ → proxy server binary
internal/          → private packages (65 subdirectories)
  hooks/           → git hook system (install, config, merge)
  config/          → configuration and agent system (agents.go)
  convoy/          → batch work tracking
  tui/             → terminal UI (bubbletea)
  cmd/             → CLI command definitions
  testutil/        → shared test helpers
plugins/           → plugin system
docs/              → documentation and skills
```

### Key conventions

- `internal/` enforces Go's import restriction — only this module can import it.
- Each `cmd/` subdirectory has a `main.go` that wires up the Cobra root command.
- Cobra command tree lives in `internal/cmd/` (not `cmd/`).

## Validation Commands

Run these in order. Fix errors at each step before moving on.

### 1. Build

```
make build
```

Or directly:

```
go build ./...
```

Build compiles all packages. Catches type errors, missing imports, and syntax errors.
The Makefile injects version/commit/build-time via `-ldflags`.

### 2. Test

```
make test
```

Or directly:

```
go test ./...
```

Run all unit tests. For a specific package:

```
go test ./internal/convoy/...
```

For verbose output with a specific test:

```
go test -v -run TestStageLaunch ./internal/convoy/...
```

For race detection:

```
go test -race ./...
```

### 3. Vet

```
go vet ./...
```

Catches subtle bugs: printf format mismatches, unreachable code, struct tag errors,
suspicious constructs the compiler accepts but are almost always wrong.

### 4. Lint

```
golangci-lint run ./...
```

Uses `.golangci.yml` (v2 format). Enabled linters:

- **errcheck** — unchecked error returns
- **gosec** — security issues (with project-specific exclusions)
- **misspell** — spelling errors in comments/strings
- **unconvert** — unnecessary type conversions
- **unparam** — unused function parameters

The config excludes common false positives (Close, Rollback, RemoveAll in tests;
G304 file inclusion in internal/; math/rand for jitter).

### 5. Full validation sequence

```
go build ./... && go test ./... && go vet ./... && golangci-lint run ./...
```

Use this as a pre-commit check. The Makefile `install` target runs `build` but not
lint/test — run those yourself.

## Errand Runner Delegation

When delegating validation to @errand-runner, specify commands explicitly.

### Build + test errand

```
Run these commands from the module root and report results:
  1. go build ./...
  2. go test ./...
Report: number of packages built, tests passed/failed, any compilation errors.
```

### Lint errand

```
Run these commands from the module root and report results:
  1. go vet ./...
  2. golangci-lint run ./...
Report: number of findings per linter, file locations, severity.
```

### Scoped test errand (single package)

```
Run from the module root:
  go test -v -count=1 ./internal/convoy/...
Report: each test name and pass/fail status, total duration.
```

### Integration test errand

```
Run from the module root:
  go test -v -tags=integration -count=1 ./internal/...
Report: pass/fail per test, any container startup failures, total duration.
```

## Report Template Labels

Use these labels in validation reports for consistent formatting.

| Label | Meaning |
|-------|---------|
| `BUILD_OK` | `go build ./...` succeeded with zero errors |
| `BUILD_FAIL` | Compilation errors (list each with file:line) |
| `TEST_PASS` | All tests passed |
| `TEST_FAIL` | Test failures (list each with `TestName: reason`) |
| `VET_CLEAN` | `go vet` reported zero findings |
| `VET_WARN` | Vet findings (list each with file:line:message) |
| `LINT_CLEAN` | `golangci-lint` reported zero findings |
| `LINT_WARN` | Lint findings (group by linter, then file:line) |

## Coding Standards

These are non-negotiable for all Go code in the project.

### Naming

- **MixedCaps** everywhere. `GetUser`, `httpClient`, `maxRetries`. Never `get_user`.
- **Acronyms** stay all-caps: `HTTPServer`, `userID`, `parseJSON`.
- **Package names** are lowercase, single-word when possible: `convoy`, `hooks`, `config`.
- **Interface names**: single-method interfaces use method name + `er`: `Reader`, `Closer`.
  Multi-method interfaces describe behavior: `ReadWriteCloser`.
- **Unexported first**: default to unexported. Export only what other packages need.

### Error Handling

- **Always handle errors.** Never write `_ = someFunc()` when it returns an error.
- **Wrap with context** using `fmt.Errorf` and `%w`:

```go
  f, err := os.Open(path)
  if err != nil {
      return fmt.Errorf("open config %s: %w", path, err)
  }
```

- **Return early** on error. Happy path stays at the left margin.
- **Sentinel errors** with `errors.New` for package-level error values:

```go
  var ErrNotFound = errors.New("not found")
```

- **Check with `errors.Is`** and **`errors.As`**, not `==`.
- **Never panic** in library code. Reserve `panic` for truly unrecoverable states
  in `main` or test helpers.

### Interfaces

- **Accept interfaces, return structs.** Functions take the narrowest interface they need
  and return concrete types.
- **Define interfaces at the consumer**, not the implementer. If only one package uses
  an interface, define it there.
- **Keep interfaces small.** One to three methods. Compose with embedding if needed.
- Use **`any`** instead of `interface{}`.

### Testing

- **Standard library preferred.** Use `testing` package. Avoid testify unless already
  in the dependency tree.
- **Table-driven tests** with `t.Run()`:

```go
  tests := []struct {
      name    string
      input   string
      want    string
      wantErr bool
  }{
      {name: "empty", input: "", want: "", wantErr: false},
      {name: "valid", input: "abc", want: "ABC", wantErr: false},
  }
  for _, tt := range tests {
      t.Run(tt.name, func(t *testing.T) {
          got, err := Transform(tt.input)
          if (err != nil) != tt.wantErr {
              t.Errorf("Transform() error = %v, wantErr %v", err, tt.wantErr)
              return
          }
          if got != tt.want {
              t.Errorf("Transform() = %v, want %v", got, tt.want)
          }
      })
  }
```

- **Test file naming**: `foo_test.go` next to `foo.go`.
- **Test helpers** go in `internal/testutil/`. Use `t.Helper()` in helper functions.
- **testcontainers** for integration tests that need databases or services.
- **`-count=1`** to bypass test caching when debugging flaky tests.
- **`t.Parallel()`** for independent tests, but be careful with shared state.

### Package Organization

- **`internal/`** for all private packages. This is the default location.
- **`cmd/`** for binary entry points only. Minimal code — just wiring.
- **No `pkg/`** directory unless the code is genuinely a reusable library for external
  consumers (rare in application code).
- **One responsibility per package.** If a package does two unrelated things, split it.

### Comments and Documentation

- **Godoc comments on all exported types, functions, and constants.**
- Comments start with the name of the thing they describe:

```go
  // Convoy tracks a batch of work items dispatched to rigs.
  type Convoy struct { ... }

  // NewConvoy creates a convoy with the given options.
  func NewConvoy(opts ...Option) *Convoy { ... }
```

- **Package comments** go in `doc.go` or at the top of the primary file.

### Cobra CLI Patterns

- Command tree lives in `internal/cmd/`.
- Each command is a `cobra.Command` struct. Use `RunE` (not `Run`) to return errors.
- Flags go on the command, not in global variables.
- Use `Args: cobra.ExactArgs(1)` or similar for argument validation.
- Persistent flags on parent commands for shared options.

### Concurrency

- **Share memory by communicating.** Prefer channels over shared state with mutexes.
- **`sync.Mutex`** when channels are awkward (simple counters, caches).
- **`context.Context`** as the first parameter for anything that blocks or does I/O.
- **`errgroup.Group`** for parallel tasks that can fail.
- Never start a goroutine without a plan for how it stops.

## Prohibitions

Never do these. Violations are always worth fixing.

| Rule | Why |
|------|-----|
| No `_ = err` or silently ignoring errors | Hides bugs; errcheck will catch it |
| No `init()` without justification | Hidden side effects, hard to test, ordering surprises |
| No package-level mutable state | Makes packages unpredictable and untestable |
| No `panic()` in library code | Crashes the caller; return errors instead |
| No `interface{}` — use `any` | `any` is the modern alias since Go 1.18 |
| No `go install` for project binaries | Use `make install` to get correct ldflags |
| No hand-editing `go.sum` | Run `go mod tidy` instead |
| No `log.Fatal` / `os.Exit` in library code | Prevents graceful shutdown; only in `main` |
| No naked returns in functions longer than a few lines | Hurts readability |
| No dot imports (`import . "pkg"`) | Pollutes namespace, confuses readers |
| No `time.Sleep` for synchronization | Use channels, sync primitives, or `time.After` with select |

## Output Truncation Rules

When reporting command output, keep it concise.

### Build output

- **Success**: report `BUILD_OK` with package count.
- **Failure**: show the first 5 errors with full `file:line:col: message` format.
  If more than 5, add `... and N more errors`.

### Test output

- **All pass**: report `TEST_PASS` with count and total duration.
- **Failures**: show each failing test name, the first assertion failure message,
  and the file:line. Truncate stack traces to 3 frames.
- **Panic**: show the panic message and first 5 stack frames.

### Lint output

- **Clean**: report `LINT_CLEAN`.
- **Findings**: group by linter. Show up to 10 findings per linter with
  `file:line:col: message`. If more than 10, add `... and N more from <linter>`.

### General truncation

- Cap total output at 200 lines. If exceeded, keep the first 50 and last 50 lines
  with `... (N lines truncated)` in between.
- Always preserve the final summary line of any command.

## Quick Reference

### Common tasks

| Task | Command |
|------|---------|
| Build all | `make build` |
| Test all | `make test` or `go test ./...` |
| Test one package | `go test -v ./internal/convoy/...` |
| Test one function | `go test -v -run TestName ./internal/pkg/...` |
| Lint | `golangci-lint run ./...` |
| Vet | `go vet ./...` |
| Tidy deps | `go mod tidy` |
| Add dependency | `go get github.com/foo/bar@latest` |
| Install binary | `make install` |
| Safe install (no daemon restart) | `make safe-install` |
| Run e2e tests | `make test-e2e-container` |

### File patterns

| Pattern | Purpose |
|---------|---------|
| `*_test.go` | Test files (same package or `_test` package) |
| `internal/*/` | Private packages |
| `cmd/*/main.go` | Binary entry points |
| `.golangci.yml` | Lint configuration (v2 format) |
| `Makefile` | Build/install/test targets |
| `go.mod` | Module definition and dependencies |
