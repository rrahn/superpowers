from skillctl.upstream import SkillChange, group_by_skill, plan


def test_files_belong_to_the_deepest_skill_directory() -> None:
    files = [
        ("tdd/SKILL.md", "1"),
        ("tdd/tests.md", "2"),
        ("tdd/examples/demo/SKILL.md", "3"),
        ("tdd/examples/demo/run.sh", "4"),
    ]

    assert group_by_skill(files) == {
        "tdd": {"SKILL.md": "1", "tests.md": "2"},
        "tdd/examples/demo": {"SKILL.md": "3", "run.sh": "4"},
    }


def test_root_skill_md_hidden_files_and_loose_files_are_ignored() -> None:
    files = [("SKILL.md", "1"), ("README.md", "2"), ("x/SKILL.md", "3"), ("x/.DS_Store", "4")]

    assert group_by_skill(files) == {"x": {"SKILL.md": "3"}}


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
