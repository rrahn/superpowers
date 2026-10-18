"""Filesystem helpers for replacing a skill directory without leaving it half-written."""

import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def replacing(target: Path) -> Generator[Path]:
    """Stage a new version of `target` and swap it into place only if the block succeeds.

    The staging directory is hidden and lives next to `target` (same filesystem, so the swap is a
    rename). An existing `target` — directory, file, or symlink (the link, never its target) —
    is moved aside first and restored if the swap fails. On any error nothing changes.

    Args:
        target: The directory to create or replace.

    Yields:
        An empty directory (mode 0755) to fill with the new content.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}-", dir=target.parent))
    try:
        staging.chmod(0o755)
        yield staging
        _swap(staging, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def exists(path: Path) -> bool:
    """Whether `path` exists, counting dangling symlinks."""
    return path.is_symlink() or path.exists()


def is_ignored(name: str) -> bool:
    """Whether a file or directory name is never part of a skill (hidden, `__pycache__`)."""
    return name.startswith(".") or name == "__pycache__"


def _swap(staging: Path, target: Path) -> None:
    backup = target.with_name(f".{target.name}.previous")
    _remove(backup)
    had_previous = exists(target)
    if had_previous:
        target.rename(backup)
    try:
        staging.rename(target)
    except OSError:
        if had_previous:
            backup.rename(target)
        raise
    _remove(backup)


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
