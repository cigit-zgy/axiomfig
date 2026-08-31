#!/usr/bin/env python3
"""Build the 20-case Matplotlib-first complex figure capability audit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import shutil
import subprocess
import sys
import textwrap
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, Patch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from axiomfig.config import build_rcparams, load_contracts  # noqa: E402
from axiomfig.style import axiom_colormap, palette_color, semantic_colormap  # noqa: E402
from axiomfig.typography import discover_fonts  # noqa: E402
from scripts import build_layout_benchmark as round01  # noqa: E402

AUDIT = ROOT / "gallery" / "capability_audit"
TMP = ROOT / "tmp" / "figure-capability-audit"
CASES_PATH = ROOT / "tests" / "evaluation" / "figure_capability" / "cases.yaml"
ARCHIVE = ROOT / "gallery" / "archive" / "layout_engine_round01"

BLUE = palette_color("AxiomBlue")
CYAN = palette_color("AxiomCyan")
ORANGE = palette_color("AxiomOrange")
GREEN = palette_color("AxiomGreen")
PURPLE = palette_color("AxiomPurple")
RED = palette_color("AxiomRed")
GREY = palette_color("AxiomGrey")
WHITE = palette_color("AxiomWhite", palette_name="axiom_neutral")
PALE_GREY = palette_color("AxiomGrey", palette_name="grayscale")
COLORS = (BLUE, ORANGE, GREEN, PURPLE)
NATIVE_BUILDERS: dict[str, Callable[[], mpl.figure.Figure]] = {}


def _cases() -> list[dict[str, Any]]:
    document = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    return list(document["cases"])


def _name(case: dict[str, Any]) -> str:
    return f"{case['id']}_{case['name']}.pdf"


def _rcparams() -> dict[str, Any]:
    params = build_rcparams(load_contracts(), geometry="double-column", typography="serif")
    params.update(
        {
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": None,
            "savefig.pad_inches": 0.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    return params


def _style(axis: mpl.axes.Axes) -> None:
    axis.tick_params(top=False, right=False)


def _save(figure: mpl.figure.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        path,
        format="pdf",
        bbox_inches=None,
        metadata={"Creator": "AxiomFig capability audit", "CreationDate": None, "ModDate": None},
    )


def _legacy_builder(case_id: str) -> mpl.figure.Figure:
    builder = getattr(round01, f"_build_{case_id}")
    return builder("default").figure


def _draw_dendrogram(axis: mpl.axes.Axes, linkage: np.ndarray, *, orientation: str) -> list[int]:
    """Draw SciPy-computed tree geometry with Matplotlib-owned artists."""

    from scipy.cluster.hierarchy import dendrogram

    geometry = dendrogram(
        linkage,
        no_plot=True,
        no_labels=True,
        color_threshold=0,
    )
    for independent, distance in zip(geometry["icoord"], geometry["dcoord"], strict=True):
        if orientation == "left":
            axis.plot(distance, independent, color=GREY, lw=0.55)
        else:
            axis.plot(independent, distance, color=GREY, lw=0.55)
    if orientation == "left":
        axis.invert_xaxis()
    axis.axis("off")
    return [int(index) for index in geometry["leaves"]]


for _case_id in (f"{index:02d}" for index in range(1, 11)):
    NATIVE_BUILDERS[_case_id] = lambda case_id=_case_id: _legacy_builder(case_id)


def _build_01_complex() -> mpl.figure.Figure:
    data = round01.FIXTURES["01"]
    figure = plt.figure(figsize=(7.48, 6.4))
    column_dendrogram = figure.add_axes((0.30, 0.84, 0.45, 0.11))
    column_strip = figure.add_axes((0.30, 0.805, 0.45, 0.022))
    row_dendrogram = figure.add_axes((0.04, 0.18, 0.12, 0.61))
    row_strip_a = figure.add_axes((0.175, 0.18, 0.018, 0.61))
    row_strip_b = figure.add_axes((0.198, 0.18, 0.018, 0.61))
    matrix_axis = figure.add_axes((0.30, 0.18, 0.45, 0.61))
    color_axis = figure.add_axes((0.915, 0.31, 0.014, 0.40))
    _draw_dendrogram(column_dendrogram, data["column_linkage"], orientation="top")
    _draw_dendrogram(row_dendrogram, data["row_linkage"], orientation="left")
    row_order = data["row_order"]
    column_order = data["column_order"]
    ordered = data["matrix"][np.ix_(row_order, column_order)]
    annotation_cmap = mpl.colors.ListedColormap(COLORS[:3])
    row_strip_a.imshow(
        data["row_annotation"][row_order][:, None],
        aspect="auto",
        cmap=annotation_cmap,
        origin="lower",
    )
    second = (np.arange(18)[row_order] // 3) % 3
    row_strip_b.imshow(second[:, None], aspect="auto", cmap=annotation_cmap, origin="lower")
    column_strip.imshow(
        data["column_annotation"][column_order][None, :], aspect="auto", cmap=annotation_cmap
    )
    image = matrix_axis.imshow(
        ordered,
        aspect="auto",
        cmap=axiom_colormap("axiom_diverging"),
        vmin=-3,
        vmax=3,
        origin="lower",
    )
    matrix_axis.set_xticks(
        range(12), [data["column_labels"][index] for index in column_order], rotation=90
    )
    matrix_axis.set_yticks(range(18), [data["row_labels"][index] for index in row_order])
    matrix_axis.yaxis.tick_right()
    matrix_axis.tick_params(axis="y", labelright=True, labelleft=False, pad=2, length=0)
    matrix_axis.tick_params(axis="x", length=0)
    for axis in (column_dendrogram, column_strip, row_dendrogram, row_strip_a, row_strip_b):
        axis.axis("off")
    figure.colorbar(image, cax=color_axis, label="Standardized abundance")
    figure.legend(
        handles=[
            Patch(color=COLORS[index], label=f"Annotation class {index + 1}") for index in range(3)
        ],
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.51, 0.01),
    )
    return figure


def _build_02_complex() -> mpl.figure.Figure:
    figure, axes = plt.subplots(5, 5, figsize=(7.48, 7.2), sharex="col", sharey="row")
    rng = np.random.default_rng(202)
    groups = np.repeat(np.arange(3), 30)
    latent = rng.normal(size=90)
    values = np.column_stack(
        (
            6.2 + 0.9 * latent + groups * 0.22 + rng.normal(0, 0.35, 90),
            3.1 - 0.45 * latent + groups * 0.16 + rng.normal(0, 0.26, 90),
            4.2 + 0.70 * latent + groups * 0.18 + rng.normal(0, 0.31, 90),
            1.4 + 0.30 * latent + groups * 0.13 + rng.normal(0, 0.20, 90),
            0.3 - 0.62 * latent + groups * 0.10 + rng.normal(0, 0.30, 90),
        )
    )
    labels = ("Oxygen", "Ammonium", "Nitrate", "Phosphate", "Redox")
    limits = []
    for column in range(5):
        low, high = values[:, column].min(), values[:, column].max()
        pad = (high - low) * 0.06
        limits.append((low - pad, high + pad))
    for row in range(5):
        for column in range(5):
            axis = axes[row, column]
            for group in range(3):
                selected = groups == group
                if row == column:
                    axis.hist(
                        values[selected, column],
                        bins=np.linspace(*limits[column], 9),
                        histtype="step",
                        color=COLORS[group],
                        lw=0.7,
                    )
                else:
                    axis.scatter(
                        values[selected, column],
                        values[selected, row],
                        s=8,
                        color=COLORS[group],
                        edgecolor="black",
                        linewidth=0.18,
                        alpha=0.5,
                    )
            axis.set_xlim(limits[column])
            if row != column:
                axis.set_ylim(limits[row])
            if row == 4:
                axis.set_xlabel(labels[column])
            if column == 0:
                axis.set_ylabel(labels[row])
            axis.tick_params(labelsize=6, top=False, right=False)
    figure.legend(
        handles=[
            Line2D([], [], marker="o", ls="", color=COLORS[i], markeredgecolor="black", label=name)
            for i, name in enumerate(("Control", "Low dose", "High dose"))
        ],
        loc="upper center",
        ncol=3,
        frameon=False,
    )
    figure.subplots_adjust(left=0.10, right=0.98, bottom=0.09, top=0.93, wspace=0.08, hspace=0.08)
    return figure


def _build_03_complex() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(5.51, 5.4))
    grid = figure.add_gridspec(
        2,
        2,
        width_ratios=(4.5, 1.15),
        height_ratios=(1.15, 4.5),
        left=0.13,
        right=0.96,
        bottom=0.12,
        top=0.94,
        hspace=0.04,
        wspace=0.04,
    )
    joint = figure.add_subplot(grid[1, 0])
    top = figure.add_subplot(grid[0, 0], sharex=joint)
    right = figure.add_subplot(grid[1, 1], sharey=joint)
    rng = np.random.default_rng(203)
    centers = ((2.5, 2.6), (4.2, 3.7), (5.7, 5.1))
    x_grid = np.linspace(0, 8, 120)
    y_grid = np.linspace(0, 8, 120)
    xx, yy = np.meshgrid(x_grid, y_grid)
    selected_points = []
    for index, (cx, cy) in enumerate(centers):
        points = rng.multivariate_normal((cx, cy), ((0.65, 0.36), (0.36, 0.75)), 35)
        joint.scatter(
            points[:, 0],
            points[:, 1],
            s=20,
            color=COLORS[index],
            edgecolor="black",
            linewidth=0.3,
            alpha=0.55,
            label=("Control", "Low dose", "High dose")[index],
        )
        density = np.exp(-0.5 * (((xx - cx) / 1.0) ** 2 + ((yy - cy) / 1.1) ** 2))
        joint.contour(
            xx,
            yy,
            density,
            levels=(0.25, 0.50, 0.75),
            colors=(COLORS[index],),
            linewidths=0.55,
            alpha=0.72,
        )
        top.hist(points[:, 0], bins=11, histtype="step", color=COLORS[index])
        right.hist(
            points[:, 1], bins=11, histtype="step", orientation="horizontal", color=COLORS[index]
        )
        selected_points.append(points[np.argmax(points[:, 0] + points[:, 1])])
    for index, point in enumerate(selected_points):
        joint.annotate(
            f"Sample {index + 1}",
            point,
            xytext=(8, 8 + index * 3),
            textcoords="offset points",
            arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.45},
        )
    joint.set(
        xlabel="Predictor concentration", ylabel="Response concentration", xlim=(0, 8), ylim=(0, 8)
    )
    joint.legend(frameon=False, loc="upper left")
    top.tick_params(labelbottom=False)
    top.set_yticks([])
    right.tick_params(labelleft=False)
    right.set_xticks([])
    for axis in (joint, top, right):
        _style(axis)
    return figure


def _build_04_complex() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(7.48, 7.0))
    axis = figure.add_axes((0.40, 0.09, 0.33, 0.84))
    rng = np.random.default_rng(204)
    rows = 24
    estimates = rng.normal(0.05, 0.31, rows)
    half = rng.uniform(0.12, 0.28, rows)
    y = np.arange(rows)[::-1]
    labels = [f"Long scientific outcome {index + 1:02d}" for index in range(rows)]
    axis.hlines(y, estimates - half, estimates + half, color=GREY, lw=0.8)
    axis.scatter(estimates, y, s=22, color=BLUE, edgecolor="black", linewidth=0.4, zorder=3)
    axis.axvline(0, color="black", ls="-.", lw=0.7)
    axis.set_yticks(y, labels)
    axis.set(xlabel="Standardized effect (95% CI)", ylim=(-1, rows + 2), xlim=(-0.9, 1.0))
    for _row, (yy, value, width) in enumerate(zip(y, estimates, half, strict=True)):
        axis.text(
            1.05,
            yy,
            f"{value:+.2f} [{value - width:+.2f}, {value + width:+.2f}]",
            transform=axis.get_yaxis_transform(),
            va="center",
            clip_on=False,
        )
    for section, yy in zip(
        ("Primary outcomes", "Secondary outcomes", "Sensitivity analyses"),
        (24.5, 16.5, 8.5),
        strict=True,
    ):
        axis.text(
            -0.02,
            yy,
            section,
            transform=axis.get_yaxis_transform(),
            ha="right",
            va="center",
            fontweight="bold",
        )
        axis.axhline(yy - 0.5, color=PALE_GREY, lw=0.45)
    axis.tick_params(axis="y", length=0)
    _style(axis)
    return figure


def _build_06_complex() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(7.48, 6.0))
    grid = figure.add_gridspec(
        3,
        2,
        height_ratios=(2.5, 1, 1),
        left=0.10,
        right=0.97,
        bottom=0.10,
        top=0.90,
        hspace=0.42,
        wspace=0.24,
    )
    calibration = figure.add_subplot(grid[0, :])
    hist_axes = [
        figure.add_subplot(grid[row, column], sharex=calibration)
        for row in (1, 2)
        for column in (0, 1)
    ]
    x = np.linspace(0.05, 0.95, 10)
    names = ("Logistic", "Forest", "Gradient boost", "Isotonic")
    calibration.plot((0, 1), (0, 1), color="black", ls="-.", lw=0.7, label="Perfect calibration")
    for index, (name, axis) in enumerate(zip(names, hist_axes, strict=True)):
        curve = np.clip(
            x + (index - 1.5) * 0.035 * np.sin(np.pi * x) + 0.04 * np.sin((index + 1) * np.pi * x),
            0,
            1,
        )
        calibration.plot(
            x, curve, marker=("o", "s", "^", "D")[index], color=COLORS[index], label=name
        )
        counts = 3 + 26 * np.exp(-0.5 * ((x - (0.25 + index * 0.16)) / 0.20) ** 2)
        axis.step(x, counts, where="mid", color=COLORS[index])
        axis.set_ylabel("Count")
        axis.set_title(name, loc="left", fontsize=7)
        if index >= 2:
            axis.set_xlabel("Predicted probability")
        _style(axis)
    calibration.set(xlim=(0, 1), ylim=(0, 1), ylabel="Observed frequency")
    calibration.tick_params(labelbottom=False)
    calibration.legend(loc="upper left", ncol=2, frameon=False)
    _style(calibration)
    return figure


def _build_07_complex() -> mpl.figure.Figure:
    figure, axes = plt.subplots(2, 3, figsize=(7.48, 5.8))
    rng = np.random.default_rng(207)
    x = np.linspace(-2.5, 2.5, 80)
    for index, axis in enumerate(axes.flat[:4]):
        ice = np.array(
            [
                np.tanh(x * (0.7 + 0.05 * index))
                + rng.normal(0, 0.14, x.size)
                + rng.normal(0, 0.18)
                for _ in range(24)
            ]
        )
        axis.plot(x, ice.T, color=CYAN, alpha=0.16, lw=0.45)
        axis.plot(x, ice.mean(0), color=BLUE, lw=1.3, label="PDP")
        axis.scatter(
            np.linspace(-2.2, 2.2, 9),
            np.full(9, axis.get_ylim()[0]),
            marker="|",
            color="black",
            s=15,
            clip_on=False,
        )
        axis.set(
            xlabel=f"Feature {index + 1}", ylabel="Partial dependence" if index % 3 == 0 else None
        )
        _style(axis)
    xx, yy = np.meshgrid(np.linspace(-2, 2, 70), np.linspace(-2, 2, 70))
    zz = np.sin(xx) * np.cos(yy) + 0.15 * xx * yy
    contour = axes[1, 1].contourf(xx, yy, zz, levels=12, cmap=axiom_colormap("axiom_diverging"))
    axes[1, 1].set(xlabel="Feature 5", ylabel="Feature 6", title="2-D partial dependence")
    figure.colorbar(contour, ax=axes[1, 1], fraction=0.046, pad=0.04, label="Partial dependence")
    axes[1, 2].axis("off")
    axes[1, 2].legend(
        handles=(
            Line2D([], [], color=BLUE, label="PDP"),
            Line2D([], [], color=CYAN, alpha=0.4, label="ICE"),
        ),
        loc="center",
        frameon=False,
    )
    figure.subplots_adjust(left=0.09, right=0.96, bottom=0.11, top=0.94, wspace=0.34, hspace=0.40)
    return figure


def _label_lanes(
    axis: mpl.axes.Axes, x: np.ndarray, y: np.ndarray, labels: list[str], *, levels: int
) -> None:
    order = np.argsort(y)
    half = len(order) // 2
    y_min, y_max = axis.get_ylim()
    left_x, right_x = axis.get_xlim()
    span = y_max - y_min
    for side, indices in (("left", order[:half]), ("right", order[half:])):
        slots = np.linspace(y_min + 0.10 * span, y_max - 0.08 * span, max(len(indices), levels))
        for slot, index in zip(slots, indices, strict=False):
            text_x = (
                left_x + 0.02 * (right_x - left_x)
                if side == "left"
                else right_x - 0.02 * (right_x - left_x)
            )
            axis.annotate(
                labels[index],
                (x[index], y[index]),
                xytext=(text_x, slot),
                textcoords="data",
                ha="left" if side == "left" else "right",
                va="center",
                arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.42},
                clip_on=True,
            )


def _build_08_complex() -> mpl.figure.Figure:
    data = round01.FIXTURES["08"]
    figure, axis = plt.subplots(figsize=(5.51, 4.8))
    axis.scatter(
        data["x"],
        data["y"],
        s=18 + 170 * data["x"],
        color=BLUE,
        alpha=0.48,
        edgecolor="black",
        linewidth=0.28,
    )
    axis.axhline(0, color="black", ls="-.", lw=0.7)
    axis.set(xlabel="Leverage", ylabel="Studentized residual")
    selected = data["candidate"][:18]
    _label_lanes(
        axis, data["x"][selected], data["y"][selected], list(data["labels"][:18]), levels=9
    )
    figure.subplots_adjust(left=0.13, right=0.97, bottom=0.14, top=0.95)
    _style(axis)
    return figure


def _build_09_complex() -> mpl.figure.Figure:
    data = round01.FIXTURES["09"]
    figure, axis = plt.subplots(figsize=(7.48, 5.8))
    effect = data["effect"]
    significance = data["significance"]
    classes = np.select(
        (
            (effect <= -1) & (significance >= 2),
            (effect >= 1) & (significance >= 2),
            significance >= 2,
        ),
        (0, 1, 2),
        default=3,
    )
    for index, color in enumerate((BLUE, RED, PURPLE, GREY)):
        selected = classes == index
        axis.scatter(
            effect[selected],
            significance[selected],
            s=13,
            color=color,
            alpha=0.58 if index < 3 else 0.22,
            edgecolor="black" if index < 3 else "none",
            linewidth=0.2,
            label=("Down", "Up", "p only", "NS")[index],
        )
    axis.axhline(2, color="black", ls="-.", lw=0.7)
    axis.axvline(-1, color="black", ls="--", lw=0.6)
    axis.axvline(1, color="black", ls="--", lw=0.6)
    axis.set(
        xlabel="log2 fold change",
        ylabel="-log10 adjusted p-value",
        xlim=(-6.2, 6.2),
        ylim=(-0.2, 9.8),
    )
    axis.legend(frameon=False, ncol=4, loc="lower center")
    selected = np.argsort(significance + np.abs(effect))[-30:]
    _label_lanes(
        axis,
        effect[selected],
        significance[selected],
        [f"Gene {index + 1:02d}" for index in range(30)],
        levels=15,
    )
    figure.subplots_adjust(left=0.11, right=0.98, bottom=0.13, top=0.96)
    _style(axis)
    return figure


def _build_10_complex() -> mpl.figure.Figure:
    data = round01.FIXTURES["10"]
    figure = plt.figure(figsize=(7.48, 5.6))
    grid = figure.add_gridspec(
        1,
        4,
        width_ratios=(0.14, 0.64, 0.055, 0.16),
        left=0.08,
        right=0.97,
        bottom=0.16,
        top=0.94,
        wspace=0.18,
    )
    dendrogram_axis = figure.add_subplot(grid[0, 0])
    matrix_axis = figure.add_subplot(grid[0, 1])
    color_axis = figure.add_subplot(grid[0, 2])
    size_axis = figure.add_subplot(grid[0, 3])
    order = _draw_dendrogram(dendrogram_axis, data["linkage"], orientation="left")
    colormap = axiom_colormap("axiom_diverging")
    for row, group_index in enumerate(order):
        for column in range(len(data["genes"])):
            matrix_axis.scatter(
                column,
                row,
                s=18 + 95 * data["fraction"][group_index, column],
                c=[data["mean"][group_index, column]],
                cmap=colormap,
                vmin=-1.2,
                vmax=2.5,
                edgecolors="black",
                linewidths=0.25,
            )
    matrix_axis.set_xticks(range(len(data["genes"])), data["genes"], rotation=60, ha="right")
    matrix_axis.set_yticks(range(len(order)), [data["groups"][index] for index in order])
    matrix_axis.set_xlim(-0.6, len(data["genes"]) - 0.4)
    matrix_axis.set_ylim(-0.5, len(order) - 0.5)
    scalar = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(-1.2, 2.5), cmap=colormap)
    figure.colorbar(scalar, cax=color_axis, label="Mean expression")
    size_axis.set(xlim=(0, 1), ylim=(0, 1))
    for index, fraction in enumerate((0.25, 0.50, 0.75)):
        size_axis.scatter(
            0.27,
            0.73 - index * 0.25,
            s=18 + 95 * fraction,
            facecolor=WHITE,
            edgecolor="black",
            linewidth=0.45,
        )
        size_axis.text(0.52, 0.73 - index * 0.25, f"{fraction:.0%}", va="center")
    size_axis.set_title("Fraction expressing", fontsize=7)
    size_axis.axis("off")
    _style(matrix_axis)
    return figure


NATIVE_BUILDERS.update(
    {
        "01": _build_01_complex,
        "02": _build_02_complex,
        "03": _build_03_complex,
        "04": _build_04_complex,
        "06": _build_06_complex,
        "07": _build_07_complex,
        "08": _build_08_complex,
        "09": _build_09_complex,
        "10": _build_10_complex,
    }
)


def _build_11() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(7.48, 5.6))
    grid = figure.add_gridspec(
        2,
        2,
        width_ratios=(1.45, 5.0),
        height_ratios=(2.4, 2.2),
        left=0.11,
        right=0.97,
        bottom=0.13,
        top=0.94,
        wspace=0.05,
        hspace=0.05,
    )
    intersections = np.array([82, 64, 51, 44, 37, 29, 22, 18, 13, 9])
    membership = np.array(
        [
            [1, 0, 0, 0, 1, 1, 0, 1, 1, 1],
            [0, 1, 0, 0, 1, 0, 1, 1, 1, 1],
            [0, 0, 1, 0, 0, 1, 1, 1, 0, 1],
            [0, 0, 0, 1, 0, 0, 0, 0, 1, 1],
        ],
        dtype=bool,
    )
    matrix = figure.add_subplot(grid[1, 1])
    bars = figure.add_subplot(grid[0, 1], sharex=matrix)
    totals = figure.add_subplot(grid[1, 0], sharey=matrix)
    x = np.arange(intersections.size)
    bars.bar(x, intersections, color=BLUE, edgecolor="black", linewidth=0.45)
    for index, value in enumerate(intersections):
        bars.text(index, value + 2, str(value), ha="center", va="bottom")
    bars.set_ylabel("Intersection size")
    bars.tick_params(labelbottom=False)
    set_names = ("Proteome", "Transcriptome", "Metabolome", "Phenotype")
    totals_values = membership @ intersections
    totals.barh(np.arange(4), totals_values, color=GREY, edgecolor="black", linewidth=0.45)
    totals.invert_xaxis()
    totals.set_yticks(np.arange(4), set_names)
    totals.set_xlabel("Set size")
    for column in range(membership.shape[1]):
        active = np.flatnonzero(membership[:, column])
        matrix.scatter(
            np.full(4, column),
            np.arange(4),
            s=27,
            facecolors=np.where(membership[:, column], BLUE, PALE_GREY),
            edgecolors="black",
            linewidths=0.35,
            zorder=2,
        )
        if active.size > 1:
            matrix.plot([column, column], [active.min(), active.max()], color=BLUE, lw=1.2)
    matrix.set_xlim(-0.6, intersections.size - 0.4)
    matrix.set_ylim(-0.6, 3.6)
    matrix.set_xticks(x, [f"I{i + 1}" for i in x], rotation=90)
    matrix.tick_params(labelleft=False)
    matrix.grid(False)
    for axis in (bars, totals, matrix):
        _style(axis)
    return figure


def _build_12() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(7.48, 5.8))
    grid = figure.add_gridspec(
        2,
        2,
        width_ratios=(5.4, 0.9),
        height_ratios=(1.15, 4.5),
        left=0.15,
        right=0.91,
        bottom=0.15,
        top=0.93,
        wspace=0.05,
        hspace=0.05,
    )
    matrix_ax = figure.add_subplot(grid[1, 0])
    top_ax = figure.add_subplot(grid[0, 0], sharex=matrix_ax)
    right_ax = figure.add_subplot(grid[1, 1], sharey=matrix_ax)
    rng = np.random.default_rng(212)
    rows, columns = 10, 24
    mutation = rng.random((rows, columns)) < 0.20
    amplification = rng.random((rows, columns)) < 0.10
    deletion = rng.random((rows, columns)) < 0.08
    for row in range(rows):
        for column in range(columns):
            matrix_ax.add_patch(Rectangle((column - 0.47, row - 0.42), 0.94, 0.84, color=PALE_GREY))
            if mutation[row, column]:
                matrix_ax.add_patch(Rectangle((column - 0.47, row - 0.42), 0.94, 0.84, color=BLUE))
            if amplification[row, column]:
                matrix_ax.add_patch(Rectangle((column - 0.47, row - 0.16), 0.94, 0.32, color=RED))
            if deletion[row, column]:
                matrix_ax.add_patch(Rectangle((column - 0.47, row + 0.18), 0.94, 0.22, color=GREEN))
    genes = ("TP53", "PIK3CA", "KRAS", "PTEN", "APC", "BRAF", "EGFR", "MYC", "RB1", "CDKN2A")
    matrix_ax.set(xlim=(-0.5, columns - 0.5), ylim=(-0.5, rows - 0.5))
    matrix_ax.set_yticks(np.arange(rows), genes)
    matrix_ax.set_xticks(np.arange(columns), [f"S{i + 1:02d}" for i in range(columns)], rotation=90)
    matrix_ax.invert_yaxis()
    top_counts = mutation.sum(0) + amplification.sum(0) + deletion.sum(0)
    top_ax.bar(np.arange(columns), top_counts, color=GREY, width=0.82)
    top_ax.set_ylabel("Alterations")
    top_ax.tick_params(labelbottom=False)
    right_counts = mutation.sum(1) + amplification.sum(1) + deletion.sum(1)
    right_ax.barh(np.arange(rows), right_counts, color=GREY, height=0.72)
    right_ax.tick_params(labelleft=False)
    right_ax.set_xlabel("Samples")
    for row, value in enumerate((mutation | amplification | deletion).mean(1) * 100):
        right_ax.text(right_counts[row] + 0.25, row, f"{value:.0f}%", va="center")
    figure.legend(
        handles=(
            Patch(color=BLUE, label="Mutation"),
            Patch(color=RED, label="Amplification"),
            Patch(color=GREEN, label="Deletion"),
        ),
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.53, 0.01),
    )
    for axis in (matrix_ax, top_ax, right_ax):
        _style(axis)
    return figure


def _build_13() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(5.51, 6.2))
    grid = figure.add_gridspec(12, 1, left=0.17, right=0.96, bottom=0.10, top=0.96, hspace=-0.56)
    x = np.linspace(-4.0, 4.0, 320)
    axes: list[mpl.axes.Axes] = []
    for index in range(12):
        axis = figure.add_subplot(grid[index, 0], sharex=axes[0] if axes else None)
        center = -1.3 + 2.6 * index / 11
        scale = 0.55 + 0.08 * math.sin(index)
        density = np.exp(-0.5 * ((x - center) / scale) ** 2)
        density += 0.28 * np.exp(-0.5 * ((x + center * 0.4) / 0.42) ** 2)
        density /= density.max()
        color = COLORS[index % len(COLORS)]
        axis.fill_between(x, 0, density, color=color, alpha=0.65, lw=0)
        axis.plot(x, density, color="black", lw=0.55)
        axis.axhline(0, color="black", lw=0.45)
        axis.set_xlim(-5.0, 4.5)
        axis.set_ylim(-0.05, 1.05)
        axis.set_yticks([])
        axis.spines[["left", "bottom"]].set_visible(False)
        if index < 11:
            axis.tick_params(labelbottom=False, bottom=False)
        axes.append(axis)
    for index, axis in enumerate(axes):
        bounds = axis.get_position()
        figure.text(
            0.065,
            bounds.y0 + 0.32 * bounds.height,
            f"Condition {index + 1:02d}",
            ha="left",
            va="center",
        )
    axes[-1].set_xlabel("Standardized response")
    return figure


def _build_14() -> mpl.figure.Figure:
    figure, axis = plt.subplots(figsize=(7.48, 5.6))
    rng = np.random.default_rng(214)
    data = [
        rng.normal(0.18 * index + 0.3 * (index % 2), 0.42 + 0.03 * index, 34) for index in range(10)
    ]
    positions = np.arange(10)
    violins = axis.violinplot(data, positions=positions, widths=0.78, showextrema=False)
    for index, body in enumerate(violins["bodies"]):
        body.set_facecolor(COLORS[index % 4])
        body.set_edgecolor("black")
        body.set_linewidth(0.55)
        body.set_alpha(0.45)
    axis.boxplot(
        data,
        positions=positions,
        widths=0.20,
        patch_artist=True,
        showfliers=False,
        boxprops={"facecolor": WHITE, "edgecolor": "black", "linewidth": 0.6},
        medianprops={"color": "black", "linewidth": 0.8},
        whiskerprops={"linewidth": 0.6},
        capprops={"linewidth": 0.6},
    )
    for index, values in enumerate(data):
        jitter = np.linspace(-0.13, 0.13, len(values))
        axis.scatter(
            index + jitter,
            values,
            s=8,
            color=COLORS[index % 4],
            edgecolor="black",
            linewidth=0.25,
            alpha=0.58,
        )
    levels = (3.65, 4.05, 4.45)
    for (left, right), level, label in zip(
        ((0, 3), (3, 6), (6, 9)), levels, ("p = 0.012", "p < 0.001", "p = 0.031"), strict=True
    ):
        axis.plot(
            [left, left, right, right],
            [level - 0.08, level, level, level - 0.08],
            color="black",
            lw=0.65,
        )
        axis.text((left + right) / 2, level + 0.04, label, ha="center", va="bottom")
    axis.set_xticks(
        positions, [f"Long treatment {index + 1}" for index in positions], rotation=35, ha="right"
    )
    axis.set_ylabel("Measured response (a.u.)")
    axis.set_ylim(-1.7, 4.8)
    axis.legend(
        handles=[
            Patch(facecolor=COLORS[i], edgecolor="black", alpha=0.45, label=f"Block {i + 1}")
            for i in range(4)
        ],
        loc="upper left",
        ncol=2,
        frameon=False,
    )
    _style(axis)
    figure.subplots_adjust(left=0.11, right=0.97, bottom=0.25, top=0.95)
    return figure


def _build_15() -> mpl.figure.Figure:
    figure, axis = plt.subplots(figsize=(5.51, 5.2))
    rng = np.random.default_rng(215)
    centers = ((-1.6, 0.8), (1.25, 1.0), (0.2, -1.5))
    for index, (center_x, center_y) in enumerate(centers):
        scores = rng.normal((center_x, center_y), (0.62, 0.45), (24, 2))
        axis.scatter(
            scores[:, 0],
            scores[:, 1],
            s=24,
            color=COLORS[index],
            edgecolor="black",
            linewidth=0.4,
            alpha=0.58,
            label=f"Treatment {index + 1}",
        )
        axis.add_patch(
            Ellipse(
                (center_x, center_y),
                2.35,
                1.60,
                angle=12 - 8 * index,
                fill=False,
                edgecolor=COLORS[index],
                lw=1.0,
            )
        )
    angles = np.linspace(0.15, 2 * np.pi - 0.35, 12, endpoint=False)
    lengths = np.linspace(1.3, 2.35, 12)
    for index, (angle, length) in enumerate(zip(angles, lengths, strict=True)):
        x, y = length * np.cos(angle), length * np.sin(angle)
        axis.annotate(
            "", xy=(x, y), xytext=(0, 0), arrowprops={"arrowstyle": "->", "color": GREY, "lw": 0.7}
        )
        radial = 0.19 + 0.04 * (index % 3)
        axis.annotate(
            f"Loading {index + 1:02d}",
            xy=(x, y),
            xytext=(x + radial * np.cos(angle), y + radial * np.sin(angle)),
            arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.45},
            ha="left" if x >= 0 else "right",
            va="center",
        )
    axis.axhline(0, color=GREY, lw=0.55, ls="--")
    axis.axvline(0, color=GREY, lw=0.55, ls="--")
    axis.set(xlabel="PC1 (41.2%)", ylabel="PC2 (23.8%)", xlim=(-3.4, 3.4), ylim=(-3.2, 3.2))
    axis.legend(loc="upper left", frameon=False)
    _style(axis)
    figure.subplots_adjust(left=0.14, right=0.97, bottom=0.14, top=0.96)
    return figure


def _build_16() -> mpl.figure.Figure:
    figure = plt.figure(figsize=(7.48, 5.8))
    axis = figure.add_axes((0.11, 0.15, 0.70, 0.76))
    cax = figure.add_axes((0.86, 0.26, 0.018, 0.54))
    rng = np.random.default_rng(216)
    labels = ("DO", "NH4-N", "NO3-N", "TN", "PO4-P", "TP", "COD", "pH", "Temperature", "ORP")
    raw = rng.normal(size=(10, 10))
    corr = (raw + raw.T) / 4
    np.fill_diagonal(corr, 1)
    cmap = axiom_colormap("axiom_diverging")
    for row in range(10):
        for column in range(row):
            value = corr[row, column]
            axis.add_patch(Rectangle((column, row), 1, 1, fill=False, edgecolor=PALE_GREY, lw=0.35))
            axis.scatter(
                column + 0.5,
                row + 0.5,
                s=700 * abs(value),
                color=cmap((value + 1) / 2),
                edgecolor="black",
                linewidth=0.45,
                zorder=3,
            )
    target = np.column_stack((np.arange(10) + 0.5, np.arange(10) + 0.5))
    source = np.array(((7.2, 0.8), (8.1, 2.0), (8.8, 3.25), (9.25, 4.55)))
    source_labels = ("Water chemistry", "Nutrient profile", "Process state", "Community structure")
    for _index, (x, y) in enumerate(target):
        axis.scatter(x, y, s=26, facecolor=WHITE, edgecolor="black", linewidth=0.55, zorder=7)
    for index, ((sx, sy), source_label) in enumerate(zip(source, source_labels, strict=True)):
        axis.scatter(
            sx, sy, s=48, facecolor=COLORS[index], edgecolor="black", linewidth=0.6, zorder=8
        )
        axis.text(sx + 0.18, sy - 0.04, source_label, va="center")
        for target_index in (index, index + 2, index + 5, index + 7):
            tx, ty = target[target_index % 10]
            p = (0.004, 0.025, 0.12)[target_index % 3]
            color = ORANGE if p < 0.01 else GREEN if p < 0.05 else GREY
            width = (0.6, 1.2, 2.0)[target_index % 3]
            control = ((sx + tx) / 2 + 0.65, (sy + ty) / 2 - 0.65)
            path = mpl.path.Path(
                ((sx, sy), control, (tx, ty)),
                (mpl.path.Path.MOVETO, mpl.path.Path.CURVE3, mpl.path.Path.CURVE3),
            )
            axis.add_patch(
                mpl.patches.PathPatch(
                    path,
                    fill=False,
                    color=color,
                    alpha=0.25 if p >= 0.05 else 0.9,
                    lw=width,
                    zorder=4,
                )
            )
    axis.set_xlim(-0.2, 10.3)
    axis.set_ylim(10.35, -0.25)
    axis.set_aspect("equal")
    axis.set_xticks(np.arange(10) + 0.5, labels, rotation=90)
    axis.set_yticks(np.arange(10) + 0.5, labels)
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    mpl.colorbar.ColorbarBase(
        cax, cmap=cmap, norm=Normalize(-1, 1), orientation="vertical", label="Pearson r"
    )
    figure.legend(
        handles=(
            Line2D([], [], color=ORANGE, label="p < 0.01"),
            Line2D([], [], color=GREEN, label="0.01-0.05"),
            Line2D([], [], color=GREY, label=">= 0.05"),
        ),
        loc="lower center",
        ncol=3,
        frameon=False,
    )
    return figure


def _build_17() -> mpl.figure.Figure:
    figure, axes = plt.subplots(2, 2, figsize=(7.48, 6.2))
    grid = np.linspace(0, 1, 101)
    for index, name in enumerate(("Mechanistic", "Hybrid")):
        color = COLORS[index]
        roc = np.clip(grid ** (0.48 + 0.20 * index), 0, 1)
        precision = np.clip(1 - 0.55 * grid ** (0.75 + index * 0.15), 0, 1)
        det = np.clip((1 - grid) ** (1.45 - 0.2 * index), 0, 1)
        axes[0, 0].plot(grid, roc, color=color, label=name)
        axes[0, 1].plot(grid, precision, color=color, label=name)
        axes[1, 0].plot(grid, det, color=color, label=name)
    axes[0, 0].plot((0, 1), (0, 1), color=GREY, ls="--", lw=0.7)
    axes[0, 0].set(title="ROC", xlabel="False positive rate", ylabel="True positive rate")
    axes[0, 1].axhline(0.25, color=GREY, ls="--", lw=0.7)
    axes[0, 1].set(title="Precision-recall", xlabel="Recall", ylabel="Precision")
    axes[1, 0].set(title="DET", xlabel="False positive rate", ylabel="False negative rate")
    matrix = np.array(((68, 7), (12, 53)))
    image = axes[1, 1].imshow(matrix, cmap=semantic_colormap("sequential"), aspect="equal")
    for row in range(2):
        for column in range(2):
            axes[1, 1].text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color="white" if matrix[row, column] > 40 else "black",
            )
    axes[1, 1].set(
        title="Confusion matrix",
        xlabel="Predicted",
        ylabel="Observed",
        xticks=(0, 1),
        yticks=(0, 1),
    )
    figure.colorbar(image, ax=axes[1, 1], fraction=0.046, pad=0.04, label="Count")
    figure.legend(
        handles=[
            Line2D([], [], color=COLORS[i], label=name)
            for i, name in enumerate(("Mechanistic", "Hybrid"))
        ],
        loc="upper center",
        ncol=2,
        frameon=False,
    )
    for label, axis in zip(("(a)", "(b)", "(c)", "(d)"), axes.flat, strict=True):
        axis.text(-0.17, 1.07, label, transform=axis.transAxes, fontweight="bold")
        _style(axis)
    figure.subplots_adjust(left=0.10, right=0.93, bottom=0.10, top=0.88, hspace=0.38, wspace=0.31)
    return figure


def _build_18() -> mpl.figure.Figure:
    figure, axes = plt.subplots(2, 2, figsize=(7.48, 6.2))
    rng = np.random.default_rng(218)
    fitted = np.linspace(2, 18, 100)
    residual = rng.normal(0, 0.75 + fitted * 0.035)
    standardized = (residual - residual.mean()) / residual.std()
    leverage = np.clip(rng.beta(1.3, 10, 100), 0, 0.45)
    theoretical = np.sort(rng.normal(size=100))
    sample = np.sort(standardized)
    axes[0, 0].scatter(
        fitted, residual, s=16, color=BLUE, edgecolor="black", linewidth=0.3, alpha=0.55
    )
    axes[0, 0].axhline(0, color=GREY, ls="--", lw=0.7)
    axes[0, 0].set(title="Residuals vs fitted", xlabel="Fitted", ylabel="Residual")
    axes[0, 1].scatter(
        theoretical, sample, s=16, color=BLUE, edgecolor="black", linewidth=0.3, alpha=0.55
    )
    qmin, qmax = min(theoretical.min(), sample.min()), max(theoretical.max(), sample.max())
    axes[0, 1].plot((qmin, qmax), (qmin, qmax), color=GREY, ls="--", lw=0.7)
    axes[0, 1].set(title="Normal Q-Q", xlabel="Theoretical quantile", ylabel="Sample quantile")
    axes[1, 0].scatter(
        fitted,
        np.sqrt(np.abs(standardized)),
        s=16,
        color=BLUE,
        edgecolor="black",
        linewidth=0.3,
        alpha=0.55,
    )
    axes[1, 0].set(title="Scale-location", xlabel="Fitted", ylabel="sqrt(|standardized residual|)")
    sizes = 18 + 260 * leverage
    axes[1, 1].scatter(
        leverage, standardized, s=sizes, color=ORANGE, edgecolor="black", linewidth=0.35, alpha=0.55
    )
    axes[1, 1].axhline(0, color=GREY, ls="--", lw=0.7)
    axes[1, 1].set(title="Residuals vs leverage", xlabel="Leverage", ylabel="Standardized residual")
    selected = np.argsort(np.abs(standardized) + 6 * leverage)[-8:]
    _label_lanes(
        axes[1, 1],
        leverage[selected],
        standardized[selected],
        [f"Obs {index + 1}" for index in selected],
        levels=4,
    )
    for label, axis in zip(("(a)", "(b)", "(c)", "(d)"), axes.flat, strict=True):
        axis.text(-0.17, 1.07, label, transform=axis.transAxes, fontweight="bold")
        _style(axis)
    figure.subplots_adjust(left=0.11, right=0.97, bottom=0.10, top=0.93, hspace=0.40, wspace=0.34)
    return figure


def _build_19() -> mpl.figure.Figure:
    figure, axes = plt.subplots(3, 2, figsize=(7.48, 7.0))
    sizes = np.array((80, 160, 320, 640, 1280))
    for model_index, model in enumerate(("Gaussian model", "Kernel model")):
        color = COLORS[model_index]
        train = 0.96 - (0.09 + 0.02 * model_index) * np.log10(sizes / sizes[0] + 1)
        valid = 0.60 + (0.25 - 0.03 * model_index) * (
            1 - np.exp(-sizes / (300 + 100 * model_index))
        )
        train_sd = np.linspace(0.035, 0.012, 5)
        valid_sd = np.linspace(0.055, 0.020, 5)
        axes[model_index, 0].plot(sizes, train, color=color, marker="o", label="Training")
        axes[model_index, 0].fill_between(
            sizes, train - train_sd, train + train_sd, color=color, alpha=0.18
        )
        axes[model_index, 0].plot(sizes, valid, color=GREY, marker="o", label="Validation")
        axes[model_index, 0].fill_between(
            sizes, valid - valid_sd, valid + valid_sd, color=GREY, alpha=0.18
        )
        axes[model_index, 0].set_title(f"Learning curve: {model}")
        fit = (0.015 + 0.055 * model_index) * (sizes / sizes[0]) ** (0.75 + 0.35 * model_index)
        score = 0.006 * (sizes / sizes[0]) ** (0.50 + 0.22 * model_index)
        axes[model_index, 1].plot(sizes, fit, color=color, marker="o", label="Fit time")
        axes[model_index, 1].plot(sizes, score, color=GREY, marker="s", label="Score time")
        axes[model_index, 1].set_title(f"Scalability: {model}")
    for model_index, model in enumerate(("Gaussian model", "Kernel model")):
        fit = (0.015 + 0.055 * model_index) * (sizes / sizes[0]) ** (0.75 + 0.35 * model_index)
        valid = 0.60 + (0.25 - 0.03 * model_index) * (
            1 - np.exp(-sizes / (300 + 100 * model_index))
        )
        axes[2, 0].plot(fit, valid, color=COLORS[model_index], marker="o", label=model)
        axes[2, 1].plot(sizes, valid / fit, color=COLORS[model_index], marker="o", label=model)
    axes[2, 0].set(
        title="Validation score vs fit time", xlabel="Fit time (s)", ylabel="Validation score"
    )
    axes[2, 1].set(
        title="Validation score per fit time", xlabel="Training size", ylabel="Score / second"
    )
    for row in range(2):
        axes[row, 0].set(xlabel="Training size", ylabel="Accuracy")
        axes[row, 1].set(xlabel="Training size", ylabel="Time (s)")
    figure.legend(
        handles=[
            Line2D([], [], color=COLORS[i], marker="o", label=name)
            for i, name in enumerate(("Gaussian model", "Kernel model"))
        ],
        loc="upper center",
        ncol=2,
        frameon=False,
    )
    for label, axis in zip(("(a)", "(b)", "(c)", "(d)", "(e)", "(f)"), axes.flat, strict=True):
        axis.text(-0.18, 1.08, label, transform=axis.transAxes, fontweight="bold")
        _style(axis)
    figure.subplots_adjust(left=0.11, right=0.97, bottom=0.08, top=0.90, hspace=0.60, wspace=0.33)
    return figure


def _build_20() -> mpl.figure.Figure:
    figure, (manhattan, qq) = plt.subplots(
        1, 2, figsize=(7.48, 5.2), gridspec_kw={"width_ratios": (3.2, 1.35)}
    )
    rng = np.random.default_rng(220)
    offsets: list[float] = []
    centers: list[float] = []
    cursor = 0.0
    observed_values: list[float] = []
    selected: list[tuple[float, float, str]] = []
    for chromosome in range(1, 23):
        n = 150
        base_pair = np.sort(rng.uniform(0, 1, n))
        p = np.clip(rng.uniform(0, 1, n) ** 1.7, 1e-12, 1)
        if chromosome in (3, 8, 17):
            p[10 + chromosome] = 10 ** (-(8.2 + chromosome / 10))
        x = cursor + base_pair
        y = -np.log10(p)
        manhattan.scatter(
            x,
            y,
            s=6,
            color=BLUE if chromosome % 2 else ORANGE,
            alpha=0.60,
            edgecolor="none",
            rasterized=True,
        )
        centers.append(cursor + 0.5)
        offsets.extend(x)
        observed_values.extend(p)
        top = np.argmax(y)
        if y[top] > 7.3:
            selected.append((x[top], y[top], f"rs{chromosome:02d}{top:03d}"))
        cursor += 1.08
    manhattan.axhline(-np.log10(5e-8), color=RED, lw=0.7, ls="--", label="Genome-wide")
    manhattan.axhline(-np.log10(1e-5), color=GREY, lw=0.7, ls=":", label="Suggestive")
    for index, (x, y, label) in enumerate(selected):
        manhattan.annotate(
            label,
            (x, y),
            xytext=(5, 8 + index % 2 * 7),
            textcoords="offset points",
            arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.4},
            ha="left",
        )
    manhattan.set_xticks(centers, [str(index) for index in range(1, 23)])
    manhattan.set(xlabel="Chromosome", ylabel="-log10(p)", title="Manhattan")
    manhattan.legend(frameon=False, loc="upper left")
    p_sorted = np.sort(np.asarray(observed_values))
    expected = -np.log10((np.arange(1, p_sorted.size + 1) - 0.5) / p_sorted.size)
    observed = -np.log10(p_sorted)
    qq.scatter(
        expected,
        observed,
        s=7,
        color=BLUE,
        edgecolor="black",
        linewidth=0.2,
        alpha=0.58,
        rasterized=True,
    )
    limit = max(expected.max(), observed.max())
    qq.plot((0, limit), (0, limit), color=GREY, ls="--", lw=0.7)
    qq.set(xlabel="Expected -log10(p)", ylabel="Observed -log10(p)", title="Q-Q", aspect="equal")
    for label, axis in zip(("(a)", "(b)"), (manhattan, qq), strict=True):
        axis.text(-0.15, 1.05, label, transform=axis.transAxes, fontweight="bold")
        _style(axis)
    figure.subplots_adjust(left=0.10, right=0.97, bottom=0.14, top=0.92, wspace=0.32)
    return figure


NATIVE_BUILDERS.update(
    {
        "11": _build_11,
        "12": _build_12,
        "13": _build_13,
        "14": _build_14,
        "15": _build_15,
        "16": _build_16,
        "17": _build_17,
        "18": _build_18,
        "19": _build_19,
        "20": _build_20,
    }
)


def _signature(figure: mpl.figure.Figure) -> str:
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    values: list[float | int | str] = []
    for axis in figure.axes:
        values.extend(round(value, 8) for value in axis.get_position().bounds)
        values.extend((len(axis.lines), len(axis.patches), len(axis.collections), len(axis.texts)))
    for text in figure.findobj(mpl.text.Text):
        if text.get_visible() and text.get_text():
            bounds = text.get_window_extent(renderer).bounds
            values.extend((text.get_text(), *(round(value, 5) for value in bounds)))
    for line in figure.findobj(mpl.lines.Line2D):
        values.extend(round(float(value), 7) for value in np.asarray(line.get_xydata()).ravel())
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _append_attempt(record: dict[str, Any]) -> None:
    path = TMP / "attempts.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _next_attempt(case_id: str) -> int:
    path = TMP / "attempts.jsonl"
    if not path.exists():
        return 1
    return 1 + sum(
        json.loads(line).get("case_id") == case_id
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def load_attempts(path: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            grouped[str(record["case_id"])].append(record)
    return dict(grouped)


def build_native(case_ids: set[str] | None = None, *, record_attempts: bool = True) -> None:
    discover_fonts("serif")
    cases = {str(case["id"]): case for case in _cases()}
    output = AUDIT / "matplotlib_native"
    output.mkdir(parents=True, exist_ok=True)
    with mpl.rc_context(rc=_rcparams()):
        for case_id, builder in NATIVE_BUILDERS.items():
            if case_ids is not None and case_id not in case_ids:
                continue
            started = time.perf_counter()
            status = "success"
            validation = "PDF written"
            try:
                figure = builder()
                geometry = cases[case_id]["publication_geometry"]
                figure.set_size_inches(geometry["width_in"], geometry["height_in"], forward=False)
                figure.canvas.draw()
                _save(figure, output / _name(cases[case_id]))
                plt.close(figure)
            except Exception as exc:
                status = "failure"
                validation = f"{type(exc).__name__}: {exc}"
            if record_attempts:
                _append_attempt(
                    {
                        "case_id": case_id,
                        "attempt_number": _next_attempt(case_id),
                        "stage": "matplotlib_native",
                        "problem_observed": "first complete implementation attempt",
                        "anatomy_element": "complete figure",
                        "relation_violated": None,
                        "change_made": "initial Matplotlib-core implementation",
                        "change_scope": "benchmark case",
                        "status": status,
                        "validation": validation,
                        "manual_visual_verdict": "pending review"
                        if status == "success"
                        else "not rendered",
                        "elapsed_seconds": round(time.perf_counter() - started, 4),
                        "case_specific_constants_added": True,
                    }
                )
            if status == "failure":
                raise RuntimeError(f"case {case_id} failed: {validation}")


def build_originals() -> None:
    output = AUDIT / "original"
    output.mkdir(parents=True, exist_ok=True)
    cases = {str(case["id"]): case for case in _cases()}
    legacy_names = round01.FILENAMES
    for index, legacy_name in enumerate(legacy_names, start=1):
        case_id = f"{index:02d}"
        shutil.copy2(ARCHIVE / "original" / legacy_name, output / _name(cases[case_id]))
    shutil.copy2(
        ROOT / "gallery" / "sans" / "ordination" / "pca_biplot.pdf", output / _name(cases["15"])
    )
    shutil.copy2(
        ROOT / "gallery" / "sans" / "association" / "mantel_canonical.pdf",
        output / _name(cases["16"]),
    )


def build_repeatability() -> None:
    discover_fonts("serif")
    results: dict[str, list[str]] = {}
    cases = {str(case["id"]): case for case in _cases()}
    with mpl.rc_context(rc=_rcparams()):
        for case_id, builder in NATIVE_BUILDERS.items():
            signatures = []
            for _ in range(5):
                figure = builder()
                geometry = cases[case_id]["publication_geometry"]
                figure.set_size_inches(geometry["width_in"], geometry["height_in"], forward=False)
                signatures.append(_signature(figure))
                plt.close(figure)
            results[case_id] = signatures
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "repeatability.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


def validate_fonts(root: Path) -> None:
    executable = shutil.which("pdffonts")
    if executable is None:
        raise RuntimeError("pdffonts is required")
    for path in sorted((Path(root) / "matplotlib_native").glob("*.pdf")):
        completed = subprocess.run(
            [executable, str(path)], capture_output=True, text=True, check=False
        )
        if completed.returncode or "Type 3" in completed.stdout:
            raise RuntimeError(f"invalid font embedding: {path}")
        rows = completed.stdout.splitlines()[2:]
        if not any("XCharter" in row or "Charter" in row for row in rows):
            raise RuntimeError(f"native PDF does not embed canonical serif font: {path}")


def engineering_metrics() -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for case_id, builder in NATIVE_BUILDERS.items():
        metric_builder = getattr(round01, f"_build_{case_id}") if case_id == "05" else builder
        try:
            source = inspect.getsource(metric_builder)
        except OSError:
            source = ""
        tree = ast.parse(textwrap.dedent(source)) if source else ast.parse("")
        numeric_literals = sum(
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
            for node in ast.walk(tree)
        )
        metrics[case_id] = {
            "builder_loc": len(source.splitlines()),
            "shared_helper_loc": (
                len(inspect.getsource(_label_lanes).splitlines())
                if case_id in {"08", "09", "18"}
                else 0
            ),
            "renderer_measurement_calls": source.count("get_window_extent")
            + source.count("get_renderer"),
            "manual_absolute_position_calls": source.count("add_axes"),
            "post_draw_correction_passes": source.count("canvas.draw"),
            "case_specific_numeric_literals": numeric_literals,
        }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--case", action="append")
    parser.add_argument("--originals", action="store_true")
    parser.add_argument("--repeatability", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not any((args.native, args.originals, args.repeatability, args.check)):
        args.native = args.originals = args.repeatability = args.check = True
    if args.native:
        build_native(set(args.case) if args.case else None)
    if args.originals:
        build_originals()
    if args.repeatability:
        build_repeatability()
    if args.check:
        validate_fonts(AUDIT)
        print(json.dumps(engineering_metrics(), indent=2))


if __name__ == "__main__":
    main()
