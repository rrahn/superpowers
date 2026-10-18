"""Rich renderables for domain objects; commands print these and nothing else."""

from pathlib import Path

from rich.table import Table

from skillctl.catalog import CatalogSkill
from skillctl.scopes import Installation


def catalog_json(skills: list[CatalogSkill]) -> list[dict[str, str]]:
    """Convert catalog skills to their stable JSON shape.

    Args:
        skills: Skills to convert.

    Returns:
        One object per skill with name, collection, description, and path.
    """
    return [
        {"name": s.name, "collection": s.collection, "description": s.description, "path": s.path}
        for s in skills
    ]


def catalog_table(skills: list[CatalogSkill], source: str) -> Table:
    """Tabulate catalog skills in the order given.

    Args:
        skills: Skills to show.
        source: Catalog location shown in the title, e.g. `owner/repo@main`.

    Returns:
        A table with one row per skill and a count caption.
    """
    table = Table(title=f"Available skills · {source}", title_justify="left", expand=True)
    table.add_column("Skill", style="bold cyan", no_wrap=True)
    table.add_column("Collection", style="magenta", no_wrap=True)
    table.add_column("Description", ratio=1)
    for skill in skills:
        table.add_row(skill.name, skill.collection, skill.description)
    table.caption = f"{len(skills)} skill{'s' if len(skills) != 1 else ''}"
    return table


def installed_json(
    installations: list[Installation], catalog_names: set[str] | None
) -> list[dict[str, object]]:
    """Convert installations to their stable JSON shape.

    Args:
        installations: Installations to convert.
        catalog_names: Names in the catalog, or None when the catalog couldn't be read.

    Returns:
        One object per installation; `in_catalog` is null when unknown.
    """
    return [
        {
            "name": i.name,
            "scope": str(i.scope),
            "status": "managed" if i.managed else "unmanaged",
            "in_catalog": None if catalog_names is None else i.name in catalog_names,
            "link": str(i.link) if i.link else None,
        }
        for i in installations
    ]


def installed_table(
    installations: list[Installation], catalog_names: set[str] | None, home: Path
) -> Table:
    """Tabulate installations across scopes.

    Args:
        installations: Installations to show, in order.
        catalog_names: Names in the catalog, or None when the catalog couldn't be read.
        home: Home directory, abbreviated to `~` in link targets.

    Returns:
        A table with status, catalog membership, and symlink target per installation.
    """
    table = Table(title="Installed skills", title_justify="left", expand=True)
    table.add_column("Skill", style="bold cyan", no_wrap=True)
    table.add_column("Scope", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("In catalog", justify="center", no_wrap=True)
    table.add_column("Link", style="dim", ratio=1, overflow="fold")
    for i in installations:
        status = "[green]managed[/]" if i.managed else "[yellow]unmanaged[/]"
        if catalog_names is None:
            known = "[dim]?[/]"
        else:
            known = "[green]✓[/]" if i.name in catalog_names else "[dim]✗[/]"
        table.add_row(i.name, str(i.scope), status, known, _tilde(i.link, home) if i.link else "")
    managed = sum(i.managed for i in installations)
    table.caption = f"{len(installations)} installed · {managed} managed"
    return table


def _tilde(path: Path, home: Path) -> str:
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)
