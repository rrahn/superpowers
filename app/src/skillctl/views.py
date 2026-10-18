"""Rich renderables for domain objects; commands print these and nothing else."""

from rich.table import Table

from skillctl.catalog import CatalogSkill


def catalog_table(skills: list[CatalogSkill], source: str) -> Table:
    """Tabulate catalog skills grouped by collection."""
    table = Table(title=f"Available skills · {source}", title_justify="left", expand=True)
    table.add_column("Skill", style="bold cyan", no_wrap=True)
    table.add_column("Collection", style="magenta", no_wrap=True)
    table.add_column("Description", ratio=1)
    for skill in skills:
        table.add_row(skill.name, skill.collection, skill.description)
    table.caption = f"{len(skills)} skill{'s' if len(skills) != 1 else ''}"
    return table
