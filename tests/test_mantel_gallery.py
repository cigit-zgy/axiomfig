from __future__ import annotations

from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_formal_mantel_gallery_is_four_deliberate_cases() -> None:
    from axiomfig.templates.association.mantel.gallery_cases import (
        MANTEL_GALLERY_CASE_IDS,
        mantel_gallery_values,
    )

    assert MANTEL_GALLERY_CASE_IDS == (
        "canonical",
        "dense",
        "long_labels",
        "multigroup",
    )
    expected = {
        "canonical": (10, 3, 15),
        "dense": (14, 4, 28),
        "long_labels": (10, 3, 15),
        "multigroup": (12, 4, 20),
    }
    for case_id, (variable_count, source_count, link_count) in expected.items():
        values = mantel_gallery_values(case_id)
        labels = tuple(values["labels"])
        links = tuple(values["links"])
        assert len(labels) == variable_count
        assert len({str(link["source"]) for link in links}) == source_count
        assert len(links) == link_count
        assert values.get("matrix_region", "lower_left") == "lower_left"
        assert values.get("matrix_method", "circle") == "circle"
        assert values.get("diagonal", "hide") == "hide"
        assert values.get("p_value_mode", "canonical") == "canonical"


def test_gallery_projection_expands_only_deliberate_mantel_and_bar_cases() -> None:
    from axiomfig.gallery import GALLERY_SPECS
    from axiomfig.templates.registry import public_template_specs

    counts = Counter(spec.template_id for spec in GALLERY_SPECS)
    assert set(counts) == {
        spec.template_id for spec in public_template_specs() if spec.agent_recommended
    }
    assert counts["association/mantel"] == 4
    assert {
        template: count for template, count in counts.items() if template.startswith("bar/")
    } == {
        "bar/simple": 4,
        "bar/grouped": 3,
        "bar/stacked": 2,
        "bar/normalized_stacked": 1,
        "bar/grouped_stacked": 1,
        "bar/diverging_stacked": 1,
        "bar/range": 2,
        "bar/mirrored": 1,
        "bar/waterfall": 1,
    }
    assert all(
        count == 1
        for template, count in counts.items()
        if template != "association/mantel" and not template.startswith("bar/")
    )
    assert tuple(
        spec.output_id for spec in GALLERY_SPECS if spec.template_id == "association/mantel"
    ) == (
        "association/mantel_canonical",
        "association/mantel_dense",
        "association/mantel_long_labels",
        "association/mantel_multigroup",
    )


def test_obsolete_mantel_parity_atlas_is_not_a_formal_gallery_surface() -> None:
    assert not (ROOT / "gallery" / "parity" / "mantel").exists()
    assert not (ROOT / "references" / "mantel-r-parity.yaml").exists()
    assert not (ROOT / "scripts" / "build_mantel_parity.py").exists()
