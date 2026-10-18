"""Rich renderables for domain objects; commands print these and nothing else."""

from dataclasses import asdict
from pathlib import Path

from rich.table import Table

from skillctl.catalog import CatalogSkill
from skillctl.scopes import Installation
from skillctl.sources import CollectionOverview
from skillctl.upstream import CollectionReport, SkillChange

_STATUS_STYLE = {
    "changed": "[yellow]changed[/]",
    "new": "[green]new[/]",
    "orphaned": "[magenta]orphaned[/]",
    "unavailable": "[red]unavailable[/]",
    "no upstream": "[dim]no upstream[/]",
}


def upstream_json(reports: list[CollectionReport]) -> list[dict[str, object]]:
    """Convert upstream reports to their stable JSON shape.

    Args:
        reports: Collection reports to convert.

    Returns:
        One object per collection with its skills' change sets.
    """
    return [
        {
            "collection": r.collection,
            "status": r.status,
            "upstream": r.upstream,
            "reason": r.reason,
            "skills": [
                {
                    "skill": s.skill,
                    "status": s.status,
                    "added": list(s.added),
                    "modified": list(s.modified),
                    "deleted": list(s.deleted),
                }
                for s in r.skills
            ],
        }
        for r in reports
    ]


def upstream_table(reports: list[CollectionReport]) -> Table:
    """Tabulate what a sync would change; unchanged skills are counted, not listed.

    Args:
        reports: Collection reports to show, in order.

    Returns:
        A table with one row per changed/new/orphaned skill and per collection that wasn't
        compared, with file-level detail.
    """
    table = Table(title="Upstream check (dry run)", title_justify="left", expand=True)
    table.add_column("Collection", style="bold magenta", no_wrap=True)
    table.add_column("Skill", style="bold cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Would change", ratio=1, overflow="fold")
    counts = dict.fromkeys(("changed", "new", "orphaned", "unchanged"), 0)
    for report in reports:
        if report.status != "checked":
            reason = f"[dim]{report.reason or ''}[/]"
            table.add_row(report.collection, "—", _STATUS_STYLE[report.status], reason)
            continue
        for skill in report.skills:
            counts[skill.status] += 1
            if skill.status != "unchanged":
                table.add_row(
                    report.collection, skill.skill, _STATUS_STYLE[skill.status], _changes(skill)
                )
    table.caption = " · ".join(f"{n} {status}" for status, n in counts.items())
    return table


def _changes(skill: SkillChange) -> str:
    if skill.status == "orphaned":
        return "[dim]kept — no longer upstream[/]"
    lines = [f"[green]+ {p}[/]" for p in skill.added]
    lines += [f"[yellow]~ {p}[/]" for p in skill.modified]
    lines += [f"[red]- {p}[/]" for p in skill.deleted]
    return "\n".join(lines)


def sources_json(rows: list[CollectionOverview]) -> list[dict[str, object]]:
    """Convert collection overviews to their stable JSON shape.

    Args:
        rows: Collections to convert.

    Returns:
        One object per collection.
    """
    return [asdict(r) for r in rows]


def sources_table(rows: list[CollectionOverview], path: str) -> Table:
    """Tabulate collections and their upstream sources.

    Args:
        rows: Collections to show, in order.
        path: Sources file location shown in the title.

    Returns:
        A table with kind, upstream, local skill count, and note per collection.
    """
    kinds = {"github": "[green]github[/]", "local": "[blue]local[/]", "none": "[dim]none[/]"}
    table = Table(title=f"Upstream sources · {path}", title_justify="left", expand=True)
    table.add_column("Collection", style="bold magenta", no_wrap=True)
    table.add_column("Kind", no_wrap=True)
    table.add_column("Upstream", overflow="fold")
    table.add_column("Skills", justify="right")
    table.add_column("Note", style="dim", ratio=1)
    for r in rows:
        table.add_row(r.collection, kinds[r.kind], r.upstream or "—", str(r.skills), r.note or "")
    table.caption = f"{len(rows)} collections · {sum(r.skills for r in rows)} skills"
    return table


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
