# skillctl

Manage GitHub Copilot skills curated in this repository: browse the catalog on `main`,
see what's installed globally (`~/.copilot/skills`) and per repository (`.github/skills`),
and install skills into either scope.

```sh
cd app
just install          # installs the `skillctl` command via `uv tool`
skillctl --help
```

Development: `just setup`, then `just check`. See [AGENTS.md](AGENTS.md) and [docs/spec.md](docs/spec.md).
