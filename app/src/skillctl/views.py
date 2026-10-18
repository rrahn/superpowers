"""Rich renderables for domain objects; commands print these and nothing else."""

from rich.table import Table

from skillctl.catalog import CatalogSkill


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
