from skillctl.upstream import SkillChange, plan


def test_identical_skills_are_unchanged() -> None:
    tree = {"tdd": {"SKILL.md": "a1"}}

    assert plan(local=tree, upstream=tree) == [SkillChange("tdd", "unchanged")]


def test_file_level_changes_are_classified() -> None:
    local = {"tdd": {"SKILL.md": "a1", "tests.md": "b1", "old.md": "c1"}}
    upstream = {"tdd": {"SKILL.md": "a2", "tests.md": "b1", "mocking.md": "d1"}}

    assert plan(local=local, upstream=upstream) == [
        SkillChange(
            "tdd", "changed", added=("mocking.md",), modified=("SKILL.md",), deleted=("old.md",)
        ),
    ]


def test_upstream_only_skill_is_new_with_all_files_added() -> None:
    upstream = {"engineering/triage": {"SKILL.md": "e1", "labels.md": "e2"}}

    assert plan(local={}, upstream=upstream) == [
        SkillChange("engineering/triage", "new", added=("SKILL.md", "labels.md")),
    ]


def test_local_only_skill_is_orphaned_and_nothing_is_scheduled_for_deletion() -> None:
    local = {"caveman": {"SKILL.md": "f1"}}

    assert plan(local=local, upstream={}) == [SkillChange("caveman", "orphaned")]


def test_results_are_sorted_by_skill_path() -> None:
    upstream = {"b": {"SKILL.md": "1"}, "a": {"SKILL.md": "1"}}

    assert [c.skill for c in plan(local={}, upstream=upstream)] == ["a", "b"]
