#!/usr/bin/env python3
"""Build the isolated scientific-layout benchmark and its measurement evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import time
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.text import Text
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage

from axiomfig.config import build_rcparams, load_contracts
from axiomfig.style import axiom_colormap, palette_color
from axiomfig.typography import discover_fonts

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "gallery" / "layout_benchmark"
BACKENDS = ("default", "kiwi", "adjusttext", "textalloc")
ALL_BACKENDS = ("original", *BACKENDS)
FILENAMES = (
    "01_clustered_heatmap.pdf",
    "02_pairgrid.pdf",
    "03_joint_marginal.pdf",
    "04_forest_plot.pdf",
    "05_km_risk_table.pdf",
    "06_calibration_histogram.pdf",
    "07_pdp_ice_grid.pdf",
    "08_influence_labels.pdf",
    "09_volcano_labels.pdf",
    "10_dotplot_dendrogram.pdf",
)
SIZES_IN = {
    "01": (7.48, 6.10),
    "02": (7.48, 7.20),
    "03": (5.51, 5.10),
    "04": (5.51, 5.20),
    "05": (7.48, 5.60),
    "06": (5.51, 5.20),
    "07": (7.48, 5.20),
    "08": (5.51, 4.20),
    "09": (5.51, 4.70),
    "10": (7.48, 5.40),
}

BLUE = palette_color("AxiomBlue")
CYAN = palette_color("AxiomCyan")
GREEN = palette_color("AxiomGreen")
ORANGE = palette_color("AxiomOrange")
RED = palette_color("AxiomRed")
PURPLE = palette_color("AxiomPurple")
GREY = palette_color("AxiomGrey")
COLORS = (BLUE, ORANGE, GREEN, PURPLE)


@dataclass
class RenderedCase:
    figure: Figure
    label_anchors: tuple[tuple[Text, float, float], ...] = ()
    alignment_groups: tuple[tuple[Axes, ...], ...] = ()
    height_alignment_groups: tuple[tuple[Axes, ...], ...] = ()
    x_edge_groups: tuple[tuple[Axes, ...], ...] = ()
    y_edge_groups: tuple[tuple[Axes, ...], ...] = ()
    shared_x_groups: tuple[tuple[Axes, ...], ...] = ()
    shared_y_groups: tuple[tuple[Axes, ...], ...] = ()
    primary_axes: tuple[Axes, ...] = ()
    ornament_pairs: tuple[tuple[Any, Any], ...] = ()
    gap_constraints: tuple[tuple[Axes, Axes, str, float], ...] = ()
    data_avoidance_artists: tuple[Any, ...] = ()


def _rcparams() -> dict[str, object]:
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


def _register_benchmark_fonts() -> None:
    discover_fonts("serif")


def _save(figure: Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        path,
        format="pdf",
        bbox_inches=None,
        metadata={"Creator": "AxiomFig layout benchmark", "CreationDate": None, "ModDate": None},
    )


def _grid_rects(
    backend: str,
    rows: int,
    columns: int,
    *,
    margins: tuple[float, float, float, float],
    width_ratios: Sequence[float] | None = None,
    height_ratios: Sequence[float] | None = None,
    hgap: float = 0.04,
    vgap: float = 0.05,
) -> dict[tuple[int, int], tuple[float, float, float, float]]:
    left, right, bottom, top = margins
    widths = tuple(width_ratios or (1.0,) * columns)
    heights = tuple(height_ratios or (1.0,) * rows)
    bottom_up_heights = tuple(reversed(heights))
    if backend != "kiwi":
        available_width = right - left - hgap * (columns - 1)
        available_height = top - bottom - vgap * (rows - 1)
        column_widths = [available_width * value / sum(widths) for value in widths]
        row_heights = [
            available_height * value / sum(bottom_up_heights) for value in bottom_up_heights
        ]
        x_values = [left]
        for width in column_widths[:-1]:
            x_values.append(x_values[-1] + width + hgap)
        y_bottoms = [bottom]
        for height in row_heights[:-1]:
            y_bottoms.append(y_bottoms[-1] + height + vgap)
    else:
        import kiwisolver as kiwi

        solver = kiwi.Solver()
        x_values_raw = [kiwi.Variable(f"x{index}") for index in range(columns)]
        column_widths_raw = [kiwi.Variable(f"w{index}") for index in range(columns)]
        y_bottoms_raw = [kiwi.Variable(f"y{index}") for index in range(rows)]
        row_heights_raw = [kiwi.Variable(f"h{index}") for index in range(rows)]
        solver.addConstraint(x_values_raw[0] == left)
        solver.addConstraint(y_bottoms_raw[0] == bottom)
        for index in range(columns - 1):
            solver.addConstraint(
                x_values_raw[index + 1] == x_values_raw[index] + column_widths_raw[index] + hgap
            )
        for index in range(rows - 1):
            solver.addConstraint(
                y_bottoms_raw[index + 1] == y_bottoms_raw[index] + row_heights_raw[index] + vgap
            )
        solver.addConstraint(x_values_raw[-1] + column_widths_raw[-1] == right)
        solver.addConstraint(y_bottoms_raw[-1] + row_heights_raw[-1] == top)
        for index in range(1, columns):
            solver.addConstraint(
                column_widths_raw[index] * widths[0] == column_widths_raw[0] * widths[index]
            )
        for index in range(1, rows):
            solver.addConstraint(
                row_heights_raw[index] * bottom_up_heights[0]
                == row_heights_raw[0] * bottom_up_heights[index]
            )
        for variable in (*column_widths_raw, *row_heights_raw):
            solver.addConstraint(variable >= 0.01)
        solver.updateVariables()
        x_values = [value.value() for value in x_values_raw]
        column_widths = [value.value() for value in column_widths_raw]
        y_bottoms = [value.value() for value in y_bottoms_raw]
        row_heights = [value.value() for value in row_heights_raw]
    rects: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    for row in range(rows):
        source_row = rows - 1 - row
        for column in range(columns):
            rects[row, column] = (
                x_values[column],
                y_bottoms[source_row],
                column_widths[column],
                row_heights[source_row],
            )
    return rects


def _style_axis(axis: Axes, *, categorical_x: bool = False, categorical_y: bool = False) -> None:
    axis.tick_params(which="both", top=False, right=False)
    if categorical_x:
        axis.tick_params(axis="x", length=0)
    if categorical_y:
        axis.tick_params(axis="y", length=0)


def _fixture_01() -> dict[str, Any]:
    rng = np.random.default_rng(101)
    row_effect = np.repeat((-1.5, 0.0, 1.4), 6)[:, None]
    column_effect = np.sin(np.linspace(0, 2.8 * np.pi, 12))[None, :]
    matrix = row_effect + column_effect + rng.normal(0, 0.35, (18, 12))
    row_linkage = linkage(matrix, method="average", metric="euclidean")
    column_linkage = linkage(matrix.T, method="average", metric="euclidean")
    return {
        "matrix": matrix,
        "row_linkage": row_linkage,
        "column_linkage": column_linkage,
        "row_order": leaves_list(row_linkage),
        "column_order": leaves_list(column_linkage),
        "row_annotation": np.repeat(np.arange(3), 6),
        "column_annotation": np.tile(np.arange(3), 4),
        "row_labels": tuple(f"Environmental sample {index + 1:02d}" for index in range(18)),
        "column_labels": (
            "Dissolved oxygen",
            "Ammonium nitrogen",
            "Nitrate nitrogen",
            "Total phosphorus",
            "Chemical oxygen demand",
            "Redox potential",
            "Temperature",
            "Conductivity",
            "Alkalinity",
            "Turbidity",
            "Chlorophyll a",
            "pH",
        ),
    }


def _fixture_02() -> dict[str, Any]:
    rng = np.random.default_rng(102)
    groups = np.repeat(("Control", "Low dose", "High dose"), 30)
    offsets = np.repeat((-0.9, 0.0, 0.9), 30)
    latent = rng.normal(size=90) + offsets
    values = np.column_stack(
        (
            6.0 + 0.8 * latent + rng.normal(0, 0.45, 90),
            3.0 - 0.35 * latent + rng.normal(0, 0.30, 90),
            4.5 + 0.55 * latent + rng.normal(0, 0.42, 90),
            1.4 + 0.25 * latent + rng.normal(0, 0.20, 90),
        )
    )
    return {"values": values, "groups": groups, "labels": ("Length", "Width", "Mass", "Rate")}


def _fixture_03() -> dict[str, Any]:
    fixture = _fixture_02()
    return {"x": fixture["values"][:, 0], "y": fixture["values"][:, 2], "groups": fixture["groups"]}


def _fixture_04() -> dict[str, Any]:
    labels = (
        "Aerobic treatment — complete",
        "Aerobic treatment — partial",
        "Anaerobic treatment — complete",
        "Anaerobic treatment — partial",
        "Membrane bioreactor — pilot",
        "Membrane bioreactor — full scale",
        "Constructed wetland — warm season",
        "Constructed wetland — cold season",
        "Oxidation ditch — low loading",
        "Oxidation ditch — high loading",
        "Sequencing batch — municipal",
        "Sequencing batch — industrial",
        "Granular sludge — laboratory",
        "Granular sludge — demonstration",
    )
    estimate = np.array(
        (-0.42, -0.18, 0.12, 0.35, -0.28, 0.08, 0.44, 0.62, -0.11, 0.21, -0.36, 0.17, 0.04, 0.31)
    )
    half = np.array(
        (0.21, 0.24, 0.19, 0.29, 0.16, 0.18, 0.27, 0.31, 0.17, 0.22, 0.20, 0.23, 0.15, 0.19)
    )
    return {
        "labels": labels,
        "estimate": estimate,
        "lower": estimate - half,
        "upper": estimate + half,
    }


def _fixture_05() -> dict[str, Any]:
    time_values = np.linspace(0, 24, 25)
    survival = np.vstack(
        (np.exp(-0.045 * time_values), np.exp(-0.070 * time_values), np.exp(-0.105 * time_values))
    )
    lower = np.clip(survival - np.linspace(0.02, 0.09, 25), 0, 1)
    upper = np.clip(survival + np.linspace(0.02, 0.07, 25), 0, 1)
    risk_times = np.arange(0, 25, 4)
    at_risk = np.maximum(
        0,
        np.round(np.array((48, 46, 44))[:, None] * survival[:, risk_times]).astype(int),
    )
    return {
        "time": time_values,
        "survival": survival,
        "lower": lower,
        "upper": upper,
        "risk_times": risk_times,
        "at_risk": at_risk,
    }


def _fixture_06() -> dict[str, Any]:
    x = np.linspace(0.04, 0.96, 10)
    curves = np.vstack((x, np.clip(x**0.82 - 0.025, 0, 1), np.clip(x**1.23 + 0.025, 0, 1)))
    centers = np.linspace(0.05, 0.95, 10)
    histograms = np.vstack(
        (
            np.array((4, 8, 13, 19, 27, 31, 25, 18, 10, 5)),
            np.array((10, 15, 21, 26, 29, 24, 17, 10, 5, 2)),
            np.array((2, 5, 9, 15, 22, 28, 30, 24, 15, 8)),
        )
    )
    return {"x": x, "curves": curves, "centers": centers, "histograms": histograms}


def _fixture_07() -> dict[str, Any]:
    rng = np.random.default_rng(107)
    grids = tuple(np.linspace(-2.2, 2.2, 32) for _ in range(6))
    pdp = tuple(
        np.sin(grid * (0.55 + index * 0.08)) * (0.9 - index * 0.06) + index * 0.12
        for index, grid in enumerate(grids)
    )
    ice = tuple(
        curve[None, :]
        + rng.normal(0, 0.13, (18, 1))
        + rng.normal(0, 0.05, (18, len(curve))).cumsum(axis=1)
        for curve in pdp
    )
    return {
        "grids": grids,
        "pdp": pdp,
        "ice": ice,
        "labels": tuple(f"Feature {index + 1}" for index in range(6)),
    }


def _fixture_08() -> dict[str, Any]:
    rng = np.random.default_rng(108)
    leverage = np.sort(rng.beta(2.0, 8.0, 220)) * 0.55
    residual = rng.normal(0, 1.0, 220) * (0.75 + leverage * 2.2)
    candidate = np.argsort(np.abs(residual) * (0.4 + leverage))[-16:]
    labels = tuple(f"Obs {index + 1}" for index in candidate)
    return {"x": leverage, "y": residual, "candidate": candidate, "labels": labels}


def _fixture_09() -> dict[str, Any]:
    rng = np.random.default_rng(109)
    effect = rng.normal(0, 1.35, 1000)
    significance = np.clip(rng.gamma(1.5, 1.2, 1000) + 0.48 * np.abs(effect), 0.02, 9.5)
    score = significance + 0.65 * np.abs(effect)
    candidate = np.argsort(score)[-18:]
    labels = tuple(
        (
            "VCAM1",
            "KCTD12",
            "ADAM12",
            "CXCL12",
            "CACNB2",
            "SPARCL1",
            "DUSP1",
            "SAMHD1",
            "MAOA",
            "STAT1",
            "IRF7",
            "CXCL10",
            "IFI44",
            "ISG15",
            "OAS1",
            "GBP1",
            "IL6",
            "SOCS3",
        )
    )
    return {
        "effect": effect,
        "significance": significance,
        "candidate": candidate,
        "labels": labels,
    }


def _fixture_10() -> dict[str, Any]:
    rng = np.random.default_rng(110)
    groups = ("Naive T", "Memory T", "B cell", "NK cell", "Monocyte", "Dendritic", "Platelet")
    genes = (
        "IL7R",
        "LTB",
        "CD3D",
        "MS4A1",
        "CD79A",
        "NKG7",
        "GNLY",
        "LYZ",
        "S100A8",
        "FCGR3A",
        "CST3",
        "PPBP",
    )
    base = rng.normal(0.1, 0.5, (len(groups), len(genes)))
    for index in range(len(groups)):
        base[index, (2 * index) % len(genes) : (2 * index) % len(genes) + 3] += 1.8
    fraction = np.clip(
        0.12 + 0.75 / (1 + np.exp(-base)) + rng.normal(0, 0.05, base.shape), 0.05, 0.95
    )
    group_linkage = linkage(base, method="average")
    order = leaves_list(group_linkage)
    return {
        "mean": base,
        "fraction": fraction,
        "groups": groups,
        "genes": genes,
        "linkage": group_linkage,
        "order": order,
    }


FIXTURES: dict[str, dict[str, Any]] = {
    "01": _fixture_01(),
    "02": _fixture_02(),
    "03": _fixture_03(),
    "04": _fixture_04(),
    "05": _fixture_05(),
    "06": _fixture_06(),
    "07": _fixture_07(),
    "08": _fixture_08(),
    "09": _fixture_09(),
    "10": _fixture_10(),
}


def _figure(case_id: str) -> Figure:
    return plt.figure(figsize=SIZES_IN[case_id])


def _build_01(backend: str) -> RenderedCase:
    data = FIXTURES["01"]
    figure = _figure("01")
    rects = _grid_rects(
        backend,
        3,
        5,
        margins=(0.04, 0.94, 0.22, 0.96),
        width_ratios=(0.10, 0.025, 0.15, 0.67, 0.035),
        height_ratios=(0.15, 0.03, 0.82),
        hgap=0.006,
        vgap=0.010,
    )
    column_axis = figure.add_axes(rects[0, 3])
    column_annotation_axis = figure.add_axes(rects[1, 3])
    row_axis = figure.add_axes(rects[2, 0])
    row_annotation_axis = figure.add_axes(rects[2, 1])
    matrix_axis = figure.add_axes(rects[2, 3])
    color_axis = figure.add_axes(rects[2, 4])
    dendrogram(
        data["column_linkage"],
        ax=column_axis,
        no_labels=True,
        color_threshold=0,
        above_threshold_color=GREY,
    )
    dendrogram(
        data["row_linkage"],
        ax=row_axis,
        no_labels=True,
        orientation="left",
        color_threshold=0,
        above_threshold_color=GREY,
    )
    ordered = data["matrix"][np.ix_(data["row_order"], data["column_order"])]
    annotation_cmap = mpl.colors.ListedColormap(COLORS[:3])
    column_annotation_axis.imshow(
        data["column_annotation"][data["column_order"]][None, :],
        aspect="auto",
        cmap=annotation_cmap,
        interpolation="nearest",
    )
    row_annotation_axis.imshow(
        data["row_annotation"][data["row_order"]][:, None],
        aspect="auto",
        cmap=annotation_cmap,
        interpolation="nearest",
        origin="lower",
    )
    image = matrix_axis.imshow(
        ordered,
        aspect="auto",
        cmap=axiom_colormap("axiom_diverging"),
        vmin=-3,
        vmax=3,
        interpolation="nearest",
        origin="lower",
    )
    matrix_axis.set_xticks(
        range(12),
        [data["column_labels"][index] for index in data["column_order"]],
        rotation=90,
        ha="right",
        rotation_mode="anchor",
    )
    matrix_axis.set_yticks(range(18), [data["row_labels"][index] for index in data["row_order"]])
    _style_axis(matrix_axis, categorical_x=True, categorical_y=True)
    column_axis.axis("off")
    column_annotation_axis.axis("off")
    row_axis.axis("off")
    row_annotation_axis.axis("off")
    figure.colorbar(image, cax=color_axis, label="Standardized abundance")
    return RenderedCase(
        figure,
        alignment_groups=((column_axis, column_annotation_axis, matrix_axis),),
        height_alignment_groups=((row_axis, row_annotation_axis, matrix_axis),),
        x_edge_groups=((column_axis, column_annotation_axis, matrix_axis),),
        y_edge_groups=((row_axis, row_annotation_axis, matrix_axis),),
        primary_axes=(matrix_axis,),
        ornament_pairs=((matrix_axis, color_axis),),
        gap_constraints=(
            (column_axis, column_annotation_axis, "vertical", 3.0),
            (row_axis, row_annotation_axis, "horizontal", 3.0),
            (matrix_axis, color_axis, "horizontal", 3.0),
        ),
    )


def _build_02(backend: str) -> RenderedCase:
    data = FIXTURES["02"]
    figure = _figure("02")
    rects = _grid_rects(backend, 4, 4, margins=(0.09, 0.93, 0.09, 0.91), hgap=0.018, vgap=0.018)
    limits = []
    for column in range(4):
        lower = float(data["values"][:, column].min())
        upper = float(data["values"][:, column].max())
        padding = 0.05 * (upper - lower)
        limits.append((lower - padding, upper + padding))
    axes: list[Axes] = []
    for row in range(4):
        for column in range(4):
            axis = figure.add_axes(rects[row, column])
            axes.append(axis)
            for group_index, group in enumerate(("Control", "Low dose", "High dose")):
                selected = data["groups"] == group
                if row == column:
                    axis.hist(
                        data["values"][selected, column],
                        bins=np.linspace(limits[column][0], limits[column][1], 9),
                        histtype="step",
                        color=COLORS[group_index],
                    )
                else:
                    axis.scatter(
                        data["values"][selected, column],
                        data["values"][selected, row],
                        s=12,
                        color=COLORS[group_index],
                        alpha=0.55,
                        edgecolors="black",
                        linewidths=0.25,
                    )
            if row < 3:
                axis.set_xticklabels([])
            else:
                axis.set_xlabel(data["labels"][column])
            if column > 0:
                axis.set_yticklabels([])
            else:
                axis.set_ylabel(data["labels"][row])
            axis.set_xlim(limits[column])
            if row != column:
                axis.set_ylim(limits[row])
            _style_axis(axis)
    handles = [
        mpl.lines.Line2D(
            [], [], marker="o", linestyle="", color=color, markeredgecolor="black", label=group
        )
        for color, group in zip(COLORS, ("Control", "Low dose", "High dose"), strict=False)
    ]
    figure.legend(handles=handles, loc="upper center", ncols=3, frameon=False)
    shared_x = tuple(tuple(axes[row * 4 + column] for row in range(4)) for column in range(4))
    shared_y = tuple(
        tuple(axes[row * 4 + column] for column in range(4) if column != row) for row in range(4)
    )
    return RenderedCase(
        figure,
        alignment_groups=(tuple(axes),),
        height_alignment_groups=(tuple(axes),),
        shared_x_groups=shared_x,
        shared_y_groups=shared_y,
        primary_axes=tuple(axes),
    )


def _build_03(backend: str) -> RenderedCase:
    data = FIXTURES["03"]
    figure = _figure("03")
    rects = _grid_rects(
        backend,
        2,
        2,
        margins=(0.14, 0.92, 0.12, 0.92),
        width_ratios=(0.80, 0.20),
        height_ratios=(0.20, 0.80),
        hgap=0.025,
        vgap=0.025,
    )
    top = figure.add_axes(rects[0, 0])
    right = figure.add_axes(rects[1, 1])
    joint = figure.add_axes(rects[1, 0])
    top.sharex(joint)
    right.sharey(joint)
    for index, group in enumerate(("Control", "Low dose", "High dose")):
        selected = data["groups"] == group
        joint.scatter(
            data["x"][selected],
            data["y"][selected],
            s=24,
            color=COLORS[index],
            alpha=0.55,
            edgecolors="black",
            linewidths=0.35,
            label=group,
        )
        top.hist(data["x"][selected], bins=10, histtype="step", color=COLORS[index])
        right.hist(
            data["y"][selected],
            bins=10,
            histtype="step",
            color=COLORS[index],
            orientation="horizontal",
        )
    joint.set(xlabel="Predictor concentration", ylabel="Response concentration")
    joint.legend(frameon=False)
    top.set_xticklabels([])
    top.set_yticks([])
    right.set_xticks([])
    right.set_yticklabels([])
    for axis in (joint, top, right):
        _style_axis(axis)
    return RenderedCase(
        figure,
        alignment_groups=((top, joint),),
        height_alignment_groups=((right, joint),),
        x_edge_groups=((top, joint),),
        y_edge_groups=((right, joint),),
        shared_x_groups=((top, joint),),
        shared_y_groups=((right, joint),),
        primary_axes=(joint,),
        gap_constraints=(
            (top, joint, "vertical", 3.0),
            (joint, right, "horizontal", 3.0),
        ),
    )


def _build_04(backend: str) -> RenderedCase:
    data = FIXTURES["04"]
    figure = _figure("04")
    axis = figure.add_axes(_grid_rects(backend, 1, 1, margins=(0.43, 0.78, 0.10, 0.94))[0, 0])
    y = np.arange(len(data["labels"]))[::-1]
    axis.hlines(y, data["lower"], data["upper"], color=GREY, linewidth=1.1)
    axis.scatter(
        data["estimate"], y, s=30, color=BLUE, edgecolors="black", linewidths=0.5, zorder=3
    )
    axis.axvline(0, color="black", linestyle="-.", linewidth=0.8)
    axis.set_yticks(y, data["labels"])
    axis.set_xlabel("Standardized effect (95% CI)")
    axis.set_ylim(-0.8, len(y) - 0.2)
    axis.set_xlim(-0.82, 0.95)
    for ypos, value, lower, upper in zip(
        y, data["estimate"], data["lower"], data["upper"], strict=True
    ):
        axis.text(
            1.02,
            ypos,
            f"{value:+.2f} [{lower:+.2f}, {upper:+.2f}]",
            transform=axis.get_yaxis_transform(),
            va="center",
            ha="left",
            clip_on=False,
        )
    _style_axis(axis, categorical_y=True)
    return RenderedCase(figure, primary_axes=(axis,))


def _build_05(backend: str) -> RenderedCase:
    data = FIXTURES["05"]
    figure = _figure("05")
    rects = _grid_rects(
        backend,
        2,
        1,
        margins=(0.11, 0.96, 0.08, 0.92),
        height_ratios=(0.72, 0.28),
        vgap=0.045,
    )
    survival_axis = figure.add_axes(rects[0, 0])
    risk_axis = figure.add_axes(rects[1, 0])
    risk_axis.sharex(survival_axis)
    names = ("Reference", "Treatment A", "Treatment B")
    for index, name in enumerate(names):
        survival_axis.step(
            data["time"], data["survival"][index], where="post", color=COLORS[index], label=name
        )
        survival_axis.fill_between(
            data["time"],
            data["lower"][index],
            data["upper"][index],
            step="post",
            color=COLORS[index],
            alpha=0.16,
        )
        censor = np.array((5, 11, 17, 22))
        survival_axis.scatter(
            censor, data["survival"][index, censor], marker="+", color=COLORS[index], s=26
        )
    survival_axis.set(xlim=(0, 24), ylim=(0, 1.03), ylabel="Survival probability")
    survival_axis.set_yticks(np.linspace(0.0, 1.0, 6))
    survival_axis.legend(frameon=False, ncols=3, loc="upper right")
    survival_axis.set_xticklabels([])
    risk_axis.set_xlim(0, 24)
    risk_axis.set_ylim(-0.6, 2.6)
    risk_axis.set_yticks((2, 1, 0), names)
    risk_axis.set_xticks(data["risk_times"])
    risk_axis.set_xlabel("Time (months)")
    risk_axis.set_title("Number at risk", loc="left", fontsize=8)
    for group_index in range(3):
        for x, value in zip(data["risk_times"], data["at_risk"][group_index], strict=True):
            risk_axis.text(x, 2 - group_index, str(value), ha="center", va="center")
    risk_axis.spines[["left", "bottom"]].set_visible(False)
    risk_axis.tick_params(axis="y", length=0, pad=8)
    _style_axis(survival_axis)
    return RenderedCase(
        figure,
        alignment_groups=((survival_axis, risk_axis),),
        x_edge_groups=((survival_axis, risk_axis),),
        shared_x_groups=((survival_axis, risk_axis),),
        primary_axes=(survival_axis, risk_axis),
        gap_constraints=((survival_axis, risk_axis, "vertical", 3.0),),
    )


def _build_06(backend: str) -> RenderedCase:
    data = FIXTURES["06"]
    figure = _figure("06")
    rects = _grid_rects(
        backend, 2, 1, margins=(0.14, 0.95, 0.11, 0.93), height_ratios=(0.70, 0.30), vgap=0.055
    )
    calibration = figure.add_axes(rects[0, 0])
    histogram = figure.add_axes(rects[1, 0])
    histogram.sharex(calibration)
    names = ("Perfectly calibrated", "Random forest", "Logistic model")
    calibration.plot((0, 1), (0, 1), linestyle="-.", color="black", label=names[0])
    for index in range(1, 3):
        calibration.plot(
            data["x"],
            data["curves"][index],
            marker=("o", "s")[index - 1],
            color=COLORS[index - 1],
            label=names[index],
        )
    for index in range(1, 3):
        histogram.step(
            data["centers"],
            data["histograms"][index],
            where="mid",
            color=COLORS[index - 1],
            label=names[index],
        )
    calibration.set(xlim=(0, 1), ylim=(0, 1), ylabel="Observed frequency")
    calibration.set_xticklabels([])
    histogram.set(xlim=(0, 1), xlabel="Mean predicted probability", ylabel="Count")
    calibration.legend(frameon=False, loc="upper left")
    _style_axis(calibration)
    _style_axis(histogram)
    return RenderedCase(
        figure,
        alignment_groups=((calibration, histogram),),
        x_edge_groups=((calibration, histogram),),
        shared_x_groups=((calibration, histogram),),
        primary_axes=(calibration, histogram),
        gap_constraints=((calibration, histogram, "vertical", 3.0),),
    )


def _build_07(backend: str) -> RenderedCase:
    data = FIXTURES["07"]
    figure = _figure("07")
    rects = _grid_rects(backend, 2, 3, margins=(0.08, 0.95, 0.11, 0.92), hgap=0.055, vgap=0.12)
    axes: list[Axes] = []
    for index, (grid, curve, ice) in enumerate(
        zip(data["grids"], data["pdp"], data["ice"], strict=True)
    ):
        row, column = divmod(index, 3)
        axis = figure.add_axes(rects[row, column])
        axes.append(axis)
        axis.plot(grid, ice.T, color=CYAN, alpha=0.18, linewidth=0.55)
        axis.plot(grid, curve, color=BLUE, linewidth=1.4, label="PDP")
        axis.scatter(
            np.linspace(grid.min(), grid.max(), 9),
            np.full(9, axis.get_ylim()[0]),
            marker="|",
            color="black",
            s=18,
            clip_on=False,
        )
        axis.set_xlabel(data["labels"][index])
        if column == 0:
            axis.set_ylabel("Partial dependence")
        _style_axis(axis)
    axes[0].legend(frameon=False)
    return RenderedCase(
        figure,
        alignment_groups=(tuple(axes),),
        height_alignment_groups=(tuple(axes),),
        primary_axes=tuple(axes),
    )


def _allocate_labels(
    backend: str,
    axis: Axes,
    x: np.ndarray,
    y: np.ndarray,
    labels: Sequence[str],
    *,
    all_x: np.ndarray,
    all_y: np.ndarray,
) -> tuple[tuple[Text, float, float], ...]:
    np.random.seed(0)
    if backend == "adjusttext":
        from adjustText import adjust_text

        texts = [
            axis.text(xv, yv, label, ha="center", va="bottom")
            for xv, yv, label in zip(x, y, labels, strict=True)
        ]
        adjust_text(
            texts,
            x=all_x,
            y=all_y,
            target_x=x,
            target_y=y,
            ax=axis,
            ensure_inside_axes=True,
            prevent_crossings=True,
            expand=(1.08, 1.16),
            force_text=(0.10, 0.18),
            force_static=(0.08, 0.12),
            force_pull=(0.01, 0.01),
            iter_lim=250,
            arrowprops={"arrowstyle": "-", "color": GREY, "linewidth": 0.45},
        )
    elif backend == "textalloc":
        import textalloc as ta

        before = set(axis.texts)
        ta.allocate(
            axis,
            x,
            y,
            list(labels),
            x_scatter=all_x,
            y_scatter=all_y,
            textsize=float(mpl.rcParams["font.size"]),
            draw_lines=True,
            linecolor=GREY,
            linewidth=0.45,
            draw_all=True,
            nbr_candidates=180,
            priority_strategy=0,
            max_distance=0.18,
            min_distance=0.015,
            verbose=False,
        )
        texts = [text for text in axis.texts if text not in before]
    else:
        texts = []
        for index, (xv, yv, label) in enumerate(zip(x, y, labels, strict=True)):
            dx = 5 if index % 2 == 0 else -5
            dy = 4 + (index % 3) * 2
            annotation = axis.annotate(
                label,
                (xv, yv),
                xytext=(dx, dy),
                textcoords="offset points",
                ha="left" if dx > 0 else "right",
                va="bottom",
                arrowprops={"arrowstyle": "-", "color": GREY, "linewidth": 0.45},
            )
            texts.append(annotation)
    return tuple((text, float(xv), float(yv)) for text, xv, yv in zip(texts, x, y, strict=False))


def _build_08(backend: str) -> RenderedCase:
    data = FIXTURES["08"]
    figure = _figure("08")
    axis = figure.add_axes(_grid_rects(backend, 1, 1, margins=(0.13, 0.97, 0.14, 0.94))[0, 0])
    points = axis.scatter(
        data["x"], data["y"], s=20, color=BLUE, alpha=0.50, edgecolors="black", linewidths=0.3
    )
    reference = axis.axhline(0, color="black", linestyle="-.", linewidth=0.8)
    axis.set(xlabel="Leverage", ylabel="Standardized residual")
    selected = data["candidate"]
    labels = _allocate_labels(
        backend,
        axis,
        data["x"][selected],
        data["y"][selected],
        data["labels"],
        all_x=data["x"],
        all_y=data["y"],
    )
    axis.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, prune="both"))
    axis.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, prune="both"))
    _style_axis(axis)
    return RenderedCase(
        figure,
        labels,
        primary_axes=(axis,),
        data_avoidance_artists=(points, reference),
    )


def _build_09(backend: str) -> RenderedCase:
    data = FIXTURES["09"]
    figure = _figure("09")
    axis = figure.add_axes(_grid_rects(backend, 1, 1, margins=(0.13, 0.97, 0.13, 0.95))[0, 0])
    significant = (np.abs(data["effect"]) >= 1.0) & (data["significance"] >= 2.0)
    background = axis.scatter(
        data["effect"][~significant],
        data["significance"][~significant],
        s=12,
        color=GREY,
        alpha=0.28,
        edgecolors="none",
    )
    foreground = axis.scatter(
        data["effect"][significant],
        data["significance"][significant],
        s=18,
        color=np.where(data["effect"][significant] > 0, RED, BLUE),
        alpha=0.62,
        edgecolors="black",
        linewidths=0.2,
    )
    horizontal = axis.axhline(2.0, color="black", linestyle="-.", linewidth=0.8)
    left_threshold = axis.axvline(-1.0, color="black", linestyle="--", linewidth=0.7)
    right_threshold = axis.axvline(1.0, color="black", linestyle="--", linewidth=0.7)
    axis.set(xlabel="log2 fold change", ylabel="-log10 adjusted p-value")
    selected = data["candidate"]
    labels = _allocate_labels(
        backend,
        axis,
        data["effect"][selected],
        data["significance"][selected],
        data["labels"],
        all_x=data["effect"],
        all_y=data["significance"],
    )
    axis.xaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, prune="both"))
    axis.yaxis.set_major_locator(mpl.ticker.MaxNLocator(nbins=5, prune="both"))
    _style_axis(axis)
    return RenderedCase(
        figure,
        labels,
        primary_axes=(axis,),
        data_avoidance_artists=(
            background,
            foreground,
            horizontal,
            left_threshold,
            right_threshold,
        ),
    )


def _build_10(backend: str) -> RenderedCase:
    data = FIXTURES["10"]
    figure = _figure("10")
    rects = _grid_rects(
        backend,
        1,
        4,
        margins=(0.08, 0.97, 0.16, 0.94),
        width_ratios=(0.14, 0.64, 0.055, 0.16),
        hgap=0.070,
    )
    dendrogram_axis = figure.add_axes(rects[0, 0])
    matrix_axis = figure.add_axes(rects[0, 1])
    color_axis = figure.add_axes(rects[0, 2])
    size_axis = figure.add_axes(rects[0, 3])
    dendrogram_result = dendrogram(
        data["linkage"],
        ax=dendrogram_axis,
        no_labels=True,
        orientation="left",
        color_threshold=0,
        above_threshold_color=GREY,
    )
    dendrogram_axis.axis("off")
    order = np.asarray(dendrogram_result["leaves"])
    for row, group_index in enumerate(order):
        for column in range(len(data["genes"])):
            matrix_axis.scatter(
                column,
                row,
                s=18 + 95 * data["fraction"][group_index, column],
                c=[data["mean"][group_index, column]],
                cmap="cividis",
                vmin=-1.2,
                vmax=2.5,
                edgecolors="black",
                linewidths=0.25,
            )
    matrix_axis.set_xticks(range(len(data["genes"])), data["genes"], rotation=60, ha="right")
    matrix_axis.set_yticks(range(len(order)), [data["groups"][index] for index in order])
    matrix_axis.set_xlim(-0.6, len(data["genes"]) - 0.4)
    matrix_axis.set_ylim(-0.5, len(order) - 0.5)
    _style_axis(matrix_axis, categorical_x=True, categorical_y=True)
    scalar = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(-1.2, 2.5), cmap="cividis")
    figure.colorbar(scalar, cax=color_axis, label="Mean expression")
    size_axis.set_xlim(0, 1)
    size_axis.set_ylim(0, 1)
    for index, fraction in enumerate((0.25, 0.50, 0.75)):
        size_axis.scatter(
            0.25,
            0.75 - index * 0.25,
            s=18 + 95 * fraction,
            color="white",
            edgecolors="black",
            linewidths=0.5,
        )
        size_axis.text(0.55, 0.75 - index * 0.25, f"{fraction:.0%}", va="center")
    size_axis.set_title("Expressing")
    size_axis.axis("off")
    return RenderedCase(
        figure,
        height_alignment_groups=((dendrogram_axis, matrix_axis),),
        y_edge_groups=((dendrogram_axis, matrix_axis),),
        primary_axes=(matrix_axis,),
        ornament_pairs=(
            (matrix_axis, color_axis),
            (matrix_axis, size_axis),
            (color_axis, size_axis),
        ),
        gap_constraints=(
            (dendrogram_axis, matrix_axis, "horizontal", 3.0),
            (matrix_axis, color_axis, "horizontal", 3.0),
            (color_axis, size_axis, "horizontal", 3.0),
        ),
    )


BUILDERS: dict[str, Callable[[str], RenderedCase]] = {
    "01": _build_01,
    "02": _build_02,
    "03": _build_03,
    "04": _build_04,
    "05": _build_05,
    "06": _build_06,
    "07": _build_07,
    "08": _build_08,
    "09": _build_09,
    "10": _build_10,
}


def _original_01(path: Path) -> None:
    import seaborn as sns

    data = FIXTURES["01"]
    annotation_palette = sns.color_palette("Set2", 3)
    grid = sns.clustermap(
        data["matrix"],
        row_linkage=data["row_linkage"],
        col_linkage=data["column_linkage"],
        cmap="vlag",
        figsize=SIZES_IN["01"],
        xticklabels=data["column_labels"],
        yticklabels=data["row_labels"],
        row_colors=[annotation_palette[index] for index in data["row_annotation"]],
        col_colors=[annotation_palette[index] for index in data["column_annotation"]],
        cbar_kws={"label": "Standardized abundance"},
    )
    grid.savefig(path)
    plt.close(grid.fig)


def _original_02(path: Path) -> None:
    import pandas as pd
    import seaborn as sns

    data = FIXTURES["02"]
    frame = pd.DataFrame(data["values"], columns=data["labels"])
    frame["Group"] = data["groups"]
    grid = sns.PairGrid(
        frame, vars=data["labels"], hue="Group", height=SIZES_IN["02"][0] / 4, aspect=1
    )
    grid.map_diag(sns.histplot, element="step", fill=False)
    grid.map_offdiag(sns.scatterplot, s=18, alpha=0.65, edgecolor="black", linewidth=0.3)
    grid.add_legend()
    grid.figure.set_size_inches(SIZES_IN["02"])
    grid.savefig(path)
    plt.close(grid.figure)


def _original_03(path: Path) -> None:
    import pandas as pd
    import seaborn as sns

    data = FIXTURES["03"]
    frame = pd.DataFrame({"Predictor": data["x"], "Response": data["y"], "Group": data["groups"]})
    grid = sns.JointGrid(
        data=frame, x="Predictor", y="Response", hue="Group", height=SIZES_IN["03"][0]
    )
    grid.plot_joint(sns.scatterplot, s=28, alpha=0.65, edgecolor="black", linewidth=0.3)
    grid.plot_marginals(sns.histplot, element="step", fill=False)
    grid.figure.set_size_inches(SIZES_IN["03"])
    grid.savefig(path)
    plt.close(grid.figure)


def _original_04(path: Path) -> None:
    from statsmodels.graphics.dotplots import dot_plot

    data = FIXTURES["04"]
    figure = plt.figure(figsize=(7.48, SIZES_IN["04"][1]))
    axis = figure.add_subplot()
    dot_plot(
        data["estimate"],
        intervals=(data["upper"] - data["lower"]) / 2,
        lines=data["labels"],
        striped=True,
        ax=axis,
    )
    axis.axvline(0, color="black", linestyle="--", linewidth=1)
    axis.set_xlabel("Standardized effect (95% CI)")
    figure.subplots_adjust(left=0.50, right=0.96, bottom=0.10, top=0.96)
    _save(figure, path)
    plt.close(figure)


def _original_05(path: Path) -> None:
    import pandas as pd
    from lifelines import KaplanMeierFitter
    from lifelines.plotting import add_at_risk_counts

    rng = np.random.default_rng(205)
    figure, axis = plt.subplots(figsize=SIZES_IN["05"])
    fitters = []
    for name, rate in zip(
        ("Reference", "Treatment A", "Treatment B"), (0.045, 0.070, 0.105), strict=True
    ):
        durations = np.minimum(rng.exponential(1 / rate, 48), 24)
        observed = durations < 24
        fitter = KaplanMeierFitter(label=name).fit(pd.Series(durations), pd.Series(observed))
        fitter.plot_survival_function(ax=axis, ci_show=True, show_censors=True)
        fitters.append(fitter)
    add_at_risk_counts(*fitters, ax=axis, rows_to_show=["At risk"])
    axis.set(xlabel="Time (months)", ylabel="Survival probability", xlim=(0, 24))
    figure.subplots_adjust(left=0.12, right=0.96, bottom=0.28, top=0.94)
    _save(figure, path)
    plt.close(figure)


def _original_06(path: Path) -> None:
    from matplotlib.gridspec import GridSpec
    from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import GaussianNB

    features, target = make_classification(
        n_samples=100_000,
        n_features=20,
        n_informative=2,
        n_redundant=10,
        random_state=42,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.99, random_state=42
    )
    naive_bayes = GaussianNB()
    classifiers = (
        (LogisticRegression(C=1.0), "Logistic"),
        (naive_bayes, "Naive Bayes"),
        (CalibratedClassifierCV(naive_bayes, cv=2, method="isotonic"), "Naive Bayes + Isotonic"),
        (CalibratedClassifierCV(naive_bayes, cv=2, method="sigmoid"), "Naive Bayes + Sigmoid"),
    )
    figure = plt.figure(figsize=(10, 10))
    grid = GridSpec(4, 2, figure=figure)
    calibration = figure.add_subplot(grid[:2, :2])
    colors = plt.get_cmap("Dark2")
    displays = {}
    for index, (classifier, name) in enumerate(classifiers):
        classifier.fit(x_train, y_train)
        displays[name] = CalibrationDisplay.from_estimator(
            classifier,
            x_test,
            y_test,
            n_bins=10,
            name=name,
            ax=calibration,
            color=colors(index),
        )
    calibration.grid()
    calibration.set_title("Calibration plots (Naive Bayes)")
    for index, ((_, name), (row, column)) in enumerate(
        zip(classifiers, ((2, 0), (2, 1), (3, 0), (3, 1)), strict=True)
    ):
        histogram = figure.add_subplot(grid[row, column])
        histogram.hist(
            displays[name].y_prob,
            range=(0, 1),
            bins=10,
            label=name,
            color=colors(index),
        )
        histogram.set(title=name, xlabel="Mean predicted probability", ylabel="Count")
    figure.tight_layout()
    _save(figure, path)
    plt.close(figure)


def _original_07(path: Path) -> None:
    from sklearn.datasets import make_friedman1
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.inspection import PartialDependenceDisplay

    features, target = make_friedman1(n_samples=500, n_features=8, random_state=207)
    model = RandomForestRegressor(n_estimators=40, max_depth=5, random_state=207).fit(
        features, target
    )
    figure, axes = plt.subplots(2, 3, figsize=SIZES_IN["07"])
    PartialDependenceDisplay.from_estimator(
        model,
        features,
        features=(0, 1, 2, 3, 4, 5),
        kind="both",
        subsample=18,
        random_state=207,
        ax=axes,
    )
    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.10, top=0.95, wspace=0.28, hspace=0.35)
    _save(figure, path)
    plt.close(figure)


def _original_08(path: Path) -> None:
    import statsmodels.api as sm
    from statsmodels.graphics.regressionplots import influence_plot

    rng = np.random.default_rng(208)
    predictors = rng.normal(size=(80, 3))
    response = 2.0 + predictors @ np.array((0.8, -0.5, 0.35)) + rng.normal(0, 0.7, 80)
    response[[6, 23, 67]] += (3.0, -3.5, 4.0)
    model = sm.OLS(response, sm.add_constant(predictors)).fit()
    figure, axis = plt.subplots(figsize=(7.48, 5.20))
    influence_plot(model, ax=axis, criterion="cooks", size=36)
    axis.margins(y=0.14)
    figure.subplots_adjust(left=0.13, right=0.96, bottom=0.14, top=0.86)
    _save(figure, path)
    plt.close(figure)


class _ImageFinder(HTMLParser):
    def __init__(self, *, alt: str) -> None:
        super().__init__()
        self.alt = alt
        self.source: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("alt") == self.alt:
            self.source = values.get("src")


def _official_image_to_pdf(
    url: str,
    path: Path,
    *,
    alt: str | None = None,
    cache_path: Path | None = None,
    expected_sha256: str,
    expected_dimensions: tuple[int, int],
) -> None:
    if cache_path is not None and cache_path.is_file():
        payload = cache_path.read_bytes()
    else:
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
    if alt is not None:
        parser = _ImageFinder(alt=alt)
        parser.feed(payload.decode("utf-8"))
        if parser.source is None or not parser.source.startswith("data:image/png;base64,"):
            raise RuntimeError(f"official image not found: {alt}")
        payload = base64.b64decode(parser.source.split(",", 1)[1])
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise RuntimeError(
            f"official image checksum mismatch: expected {expected_sha256}, received {digest}"
        )
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("official image is not a valid PNG payload")
    dimensions = struct.unpack(">II", payload[16:24])
    if dimensions != expected_dimensions:
        raise RuntimeError(
            f"official image dimensions mismatch: expected {expected_dimensions}, "
            f"received {dimensions}"
        )
    import img2pdf

    path.write_bytes(
        img2pdf.convert(payload, layout_fun=img2pdf.get_fixed_dpi_layout_fun((180, 180)))
    )


def _original_09(path: Path) -> None:
    _official_image_to_pdf(
        "https://bioconductor.org/packages/release/bioc/vignettes/EnhancedVolcano/inst/doc/EnhancedVolcano.html",
        path,
        alt="Fit more labels by adding connectors.",
        cache_path=ROOT / "tmp" / "layout-benchmark-sources" / "enhancedvolcano.html",
        expected_sha256="771ac408207672c636c6c4c0b78057d752ae0ee26656b7c2d657506b83db1bd3",
        expected_dimensions=(1920, 1632),
    )


def _original_10(path: Path) -> None:
    _official_image_to_pdf(
        "https://scanpy.readthedocs.io/en/latest/_images/2c9701ef266c8b3b9490dcb11623e4e2a3d69eaadb9f187953a8c0613a65ad00.png",
        path,
        cache_path=ROOT / "tmp" / "layout-benchmark-sources" / "scanpy-dotplot.png",
        expected_sha256="2c9701ef266c8b3b9490dcb11623e4e2a3d69eaadb9f187953a8c0613a65ad00",
        expected_dimensions=(1055, 908),
    )


ORIGINAL_BUILDERS: dict[str, Callable[[Path], None]] = {
    "01": _original_01,
    "02": _original_02,
    "03": _original_03,
    "04": _original_04,
    "05": _original_05,
    "06": _original_06,
    "07": _original_07,
    "08": _original_08,
    "09": _original_09,
    "10": _original_10,
}


def _intersection_area(first: mpl.transforms.Bbox, second: mpl.transforms.Bbox) -> float:
    x0, y0 = max(first.x0, second.x0), max(first.y0, second.y0)
    x1, y1 = min(first.x1, second.x1), min(first.y1, second.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _shared_axis_error(groups: tuple[tuple[Axes, ...], ...], *, dimension: str) -> float | None:
    if not groups:
        return None
    error = 0.0
    for group in groups:
        reference_limits = group[0].get_xlim() if dimension == "x" else group[0].get_ylim()
        endpoints = []
        for axis in group:
            if dimension == "x":
                endpoints.append(
                    (
                        axis.transData.transform((reference_limits[0], 0.0))[0],
                        axis.transData.transform((reference_limits[1], 0.0))[0],
                    )
                )
            else:
                endpoints.append(
                    (
                        axis.transData.transform((0.0, reference_limits[0]))[1],
                        axis.transData.transform((0.0, reference_limits[1]))[1],
                    )
                )
        if endpoints:
            error = max(
                error,
                max(value[0] for value in endpoints) - min(value[0] for value in endpoints),
                max(value[1] for value in endpoints) - min(value[1] for value in endpoints),
            )
    return float(error)


def _edge_alignment_error(
    groups: tuple[tuple[Axes, ...], ...], *, dimension: str, figure: Figure
) -> float | None:
    if not groups:
        return None
    error_px = 0.0
    for group in groups:
        if dimension == "x":
            lower = [axis.bbox.x0 for axis in group]
            upper = [axis.bbox.x1 for axis in group]
        else:
            lower = [axis.bbox.y0 for axis in group]
            upper = [axis.bbox.y1 for axis in group]
        error_px = max(error_px, max(lower) - min(lower), max(upper) - min(upper))
    return float(error_px * 72.0 / figure.dpi)


def _text_hits_artist(text: Text, artist: Any, renderer: Any) -> bool:
    box = text.get_window_extent(renderer)
    if isinstance(artist, PathCollection):
        offsets = artist.get_offset_transform().transform(artist.get_offsets())
        sizes = artist.get_sizes()
        if not len(sizes):
            sizes = np.zeros(len(offsets))
        if len(sizes) == 1:
            sizes = np.repeat(sizes, len(offsets))
        radii_px = np.sqrt(sizes / np.pi) * renderer.points_to_pixels(1.0)
        return any(
            _intersection_area(
                box,
                mpl.transforms.Bbox.from_extents(
                    x_value - radius,
                    y_value - radius,
                    x_value + radius,
                    y_value + radius,
                ),
            )
            > 0.5
            for (x_value, y_value), radius in zip(offsets, radii_px, strict=False)
        )
    if isinstance(artist, Line2D):
        path = artist.get_path().transformed(artist.get_transform())
        return bool(path.intersects_bbox(box, filled=False))
    return False


def _text_data_overlap_count(rendered: RenderedCase, renderer: Any) -> int | None:
    if not rendered.data_avoidance_artists:
        return None
    return sum(
        any(_text_hits_artist(text, artist, renderer) for artist in rendered.data_avoidance_artists)
        for text, _, _ in rendered.label_anchors
    )


def _artist_bbox(artist: Any, renderer: Any) -> mpl.transforms.Bbox:
    if isinstance(artist, Axes):
        return artist.get_tightbbox(renderer)
    return artist.get_window_extent(renderer)


def _ornament_overlap_count(rendered: RenderedCase, renderer: Any) -> int | None:
    if not rendered.ornament_pairs:
        return None
    return sum(
        _intersection_area(_artist_bbox(first, renderer), _artist_bbox(second, renderer)) > 0.5
        for first, second in rendered.ornament_pairs
    )


def _gap_metrics(
    rendered: RenderedCase, figure: Figure
) -> tuple[int, int | None, float | None, float | None]:
    if not rendered.gap_constraints:
        return 0, None, None, None
    violations = 0
    measured_points = []
    shortfalls = []
    for first, second, direction, minimum_pt in rendered.gap_constraints:
        if direction == "horizontal":
            gap_px = max(second.bbox.x0 - first.bbox.x1, first.bbox.x0 - second.bbox.x1)
        else:
            gap_px = max(second.bbox.y0 - first.bbox.y1, first.bbox.y0 - second.bbox.y1)
        gap_pt = float(gap_px * 72.0 / figure.dpi)
        measured_points.append(gap_pt)
        if gap_pt + 0.05 < minimum_pt:
            violations += 1
            shortfalls.append(minimum_pt - gap_pt)
    return (
        len(rendered.gap_constraints),
        violations,
        min(measured_points),
        max(shortfalls, default=0.0),
    )


def _bbox_union_area(boxes: Sequence[mpl.transforms.Bbox]) -> float:
    if not boxes:
        return 0.0
    x_values = sorted({value for box in boxes for value in (box.x0, box.x1)})
    area = 0.0
    for left, right in zip(x_values, x_values[1:], strict=False):
        intervals = sorted((box.y0, box.y1) for box in boxes if box.x0 < right and box.x1 > left)
        covered = 0.0
        if intervals:
            start, end = intervals[0]
            for next_start, next_end in intervals[1:]:
                if next_start <= end:
                    end = max(end, next_end)
                else:
                    covered += end - start
                    start, end = next_start, next_end
            covered += end - start
        area += (right - left) * covered
    return area


def _anchor_edge_distance(text: Text, anchor_x: float, anchor_y: float, renderer: Any) -> float:
    anchor = text.axes.transData.transform((anchor_x, anchor_y))
    box = text.get_window_extent(renderer)
    dx = max(box.x0 - anchor[0], 0.0, anchor[0] - box.x1)
    dy = max(box.y0 - anchor[1], 0.0, anchor[1] - box.y1)
    return float(np.hypot(dx, dy) * 72.0 / text.figure.dpi)


def _append_path_geometry(values: list[float], artist: Any, *, point_scale: float) -> None:
    path = artist.get_path().transformed(artist.get_transform())
    vertices = np.asarray(path.vertices, dtype=float).ravel()
    values.extend(float(value * point_scale) for value in vertices if np.isfinite(value))


def _visible_texts(figure: Figure) -> list[Text]:
    all_tick_labels: set[Text] = set()
    active_tick_labels: set[Text] = set()
    for axis in figure.axes:
        for tick_axis in (axis.xaxis, axis.yaxis):
            for tick in (*tick_axis.majorTicks, *tick_axis.minorTicks):
                all_tick_labels.update((tick.label1, tick.label2))
            if axis.axison:
                for tick in tick_axis._update_ticks():
                    active_tick_labels.update((tick.label1, tick.label2))
    return [
        text
        for text in figure.findobj(Text)
        if text.get_visible()
        and text.get_text().strip()
        and (text not in all_tick_labels or text in active_tick_labels)
    ]


def _size_error(
    groups: tuple[tuple[Axes, ...], ...], *, dimension: str, figure: Figure
) -> float | None:
    if not groups:
        return None
    error_px = 0.0
    for group in groups:
        values = [axis.bbox.width if dimension == "width" else axis.bbox.height for axis in group]
        error_px = max(error_px, max(values) - min(values))
    return float(error_px * 72.0 / figure.dpi)


def _measure(rendered: RenderedCase, elapsed: float, *, draw: bool = True) -> dict[str, Any]:
    figure = rendered.figure
    if draw:
        figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    texts = _visible_texts(figure)
    boxes = [text.get_window_extent(renderer) for text in texts]
    overlap_count = 0
    overlap_area = 0.0
    for index, first in enumerate(boxes):
        for second in boxes[index + 1 :]:
            area = _intersection_area(first, second)
            if area > 0.5:
                overlap_count += 1
                overlap_area += area
    page = figure.bbox
    clipped = sum(
        box.x0 < page.x0 - 0.5
        or box.y0 < page.y0 - 0.5
        or box.x1 > page.x1 + 0.5
        or box.y1 > page.y1 + 0.5
        for box in boxes
    )
    axes_overlap = 0
    axes = [axis for axis in figure.axes if axis.get_visible()]
    for index, first in enumerate(axes):
        for second in axes[index + 1 :]:
            if _intersection_area(first.bbox, second.bbox) > 1.0:
                axes_overlap += 1
    equal_width_error = _size_error(rendered.alignment_groups, dimension="width", figure=figure)
    equal_height_error = _size_error(
        rendered.height_alignment_groups, dimension="height", figure=figure
    )
    x_edge_error = _edge_alignment_error(rendered.x_edge_groups, dimension="x", figure=figure)
    y_edge_error = _edge_alignment_error(rendered.y_edge_groups, dimension="y", figure=figure)
    shared_x_error_px = _shared_axis_error(rendered.shared_x_groups, dimension="x")
    shared_y_error_px = _shared_axis_error(rendered.shared_y_groups, dimension="y")
    shared_x_error = None if shared_x_error_px is None else shared_x_error_px * 72.0 / figure.dpi
    shared_y_error = None if shared_y_error_px is None else shared_y_error_px * 72.0 / figure.dpi
    gap_checks, gap_violations, minimum_gap, maximum_gap_shortfall = _gap_metrics(rendered, figure)
    displacement = [
        _anchor_edge_distance(text, anchor_x, anchor_y, renderer)
        for text, anchor_x, anchor_y in rendered.label_anchors
    ]
    point_scale = 72.0 / figure.dpi
    signature_values: list[float] = []
    for axis in axes:
        signature_values.extend(float(value * point_scale) for value in axis.bbox.bounds)
    for text in texts:
        signature_values.extend(
            float(value * point_scale) for value in text.get_window_extent(renderer).bounds
        )
    path_artists: dict[int, Any] = {}
    for axis in axes:
        for artist in (*axis.lines, *axis.patches):
            path_artists[id(artist)] = artist
    for text in texts:
        arrow = getattr(text, "arrow_patch", None)
        if arrow is not None:
            path_artists[id(arrow)] = arrow
    for artist in path_artists.values():
        _append_path_geometry(signature_values, artist, point_scale=point_scale)
    text_data_overlap = _text_data_overlap_count(rendered, renderer)
    ornament_overlap = _ornament_overlap_count(rendered, renderer)
    primary_area_ratio = (
        None
        if not rendered.primary_axes
        else _bbox_union_area([axis.bbox for axis in rendered.primary_axes])
        / (figure.bbox.width * figure.bbox.height)
    )
    return {
        "text_count": int(len(texts)),
        "text_text_overlap_count": int(overlap_count),
        "text_text_overlap_area_pt2": float(round(overlap_area * point_scale**2, 3)),
        "text_data_check_count": int(len(rendered.label_anchors)),
        "text_data_overlap_count": (None if text_data_overlap is None else int(text_data_overlap)),
        "clipping_count": int(clipped),
        "axes_overlap_count": int(axes_overlap),
        "ornament_check_count": int(len(rendered.ornament_pairs)),
        "ornament_overlap_count": (None if ornament_overlap is None else int(ornament_overlap)),
        "minimum_gap_check_count": int(gap_checks),
        "minimum_gap_violation_count": gap_violations,
        "minimum_gap_pt": None if minimum_gap is None else float(round(minimum_gap, 3)),
        "maximum_gap_shortfall_pt": (
            None if maximum_gap_shortfall is None else float(round(maximum_gap_shortfall, 3))
        ),
        "equal_width_error_pt": (
            None if equal_width_error is None else float(round(equal_width_error, 4))
        ),
        "equal_height_error_pt": (
            None if equal_height_error is None else float(round(equal_height_error, 4))
        ),
        "x_edge_alignment_error_pt": (
            None if x_edge_error is None else float(round(x_edge_error, 4))
        ),
        "y_edge_alignment_error_pt": (
            None if y_edge_error is None else float(round(y_edge_error, 4))
        ),
        "shared_x_alignment_error_pt": (
            None if shared_x_error is None else float(round(shared_x_error, 4))
        ),
        "shared_y_alignment_error_pt": (
            None if shared_y_error is None else float(round(shared_y_error, 4))
        ),
        "primary_visual_area_ratio": (
            None if primary_area_ratio is None else float(round(primary_area_ratio, 6))
        ),
        "mean_label_anchor_displacement_pt": (
            None if not displacement else float(round(float(np.mean(displacement)), 3))
        ),
        "median_label_anchor_displacement_pt": (
            None if not displacement else float(round(float(np.median(displacement)), 3))
        ),
        "maximum_label_anchor_displacement_pt": (
            None if not displacement else float(round(float(np.max(displacement)), 3))
        ),
        "layout_render_seconds": float(round(elapsed, 6)),
        "geometry_signature": hashlib.sha256(
            np.asarray(signature_values, dtype=np.float64).round(4).tobytes()
        ).hexdigest(),
        "_geometry_vector_pt": signature_values,
    }


def build_experimental(output_root: Path, *, repeats: int) -> dict[str, Any]:
    metrics: dict[str, Any] = {backend: {} for backend in BACKENDS}
    _register_benchmark_fonts()
    with mpl.rc_context(rc=_rcparams()):
        for backend in BACKENDS:
            for filename in FILENAMES:
                case_id = filename[:2]
                runs = []
                for repeat in range(repeats):
                    np.random.seed(0)
                    started = time.perf_counter()
                    rendered = BUILDERS[case_id](backend)
                    rendered.figure.canvas.draw()
                    elapsed = time.perf_counter() - started
                    measurement = _measure(rendered, elapsed, draw=False)
                    if repeat == 0:
                        _save(rendered.figure, output_root / backend / filename)
                    runs.append(measurement)
                    plt.close(rendered.figure)
                reference = np.asarray(runs[0]["_geometry_vector_pt"], dtype=float)
                drifts = []
                for run in runs:
                    vector = np.asarray(run.pop("_geometry_vector_pt"), dtype=float)
                    drifts.append(
                        float("inf")
                        if vector.shape != reference.shape
                        else float(np.max(np.abs(vector - reference), initial=0.0))
                    )
                maximum_drift = max(drifts, default=0.0)
                tolerance = 0.01
                metrics[backend][case_id] = {
                    "runs": runs,
                    "max_geometry_drift_pt": float(round(maximum_drift, 6)),
                    "repeatability_tolerance_pt": tolerance,
                    "repeatable": maximum_drift <= tolerance,
                }
    return metrics


def build_originals(output_root: Path) -> None:
    with mpl.rc_context(rc={"pdf.fonttype": 42, "ps.fonttype": 42}):
        for filename in FILENAMES:
            case_id = filename[:2]
            path = output_root / "original" / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            ORIGINAL_BUILDERS[case_id](path)


def check_projection(output_root: Path) -> None:
    expected = set(FILENAMES)
    actual_directories = {path.name for path in output_root.iterdir() if path.is_dir()}
    if actual_directories != set(ALL_BACKENDS):
        raise RuntimeError(f"unexpected benchmark directories: {sorted(actual_directories)}")
    for backend in ALL_BACKENDS:
        actual = {path.name for path in (output_root / backend).iterdir()}
        if actual != expected:
            raise RuntimeError(f"{backend} artifact mismatch: {sorted(actual ^ expected)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument(
        "--metrics", type=Path, default=ROOT / "tmp" / "layout-benchmark" / "metrics.json"
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--skip-originals", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_projection(args.output)
        return 0
    if args.repeats < 5:
        raise SystemExit("--repeats must be at least 5")
    if not args.skip_originals:
        build_originals(args.output)
    metrics = build_experimental(args.output, repeats=args.repeats)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    check_projection(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
