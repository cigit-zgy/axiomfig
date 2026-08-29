from pathlib import Path


def test_project_skill_validator_accepts_canonical_skill() -> None:
    from scripts.validate_skill import validate_skill

    root = Path(__file__).resolve().parents[1]
    validate_skill(root / "SKILL.md")
