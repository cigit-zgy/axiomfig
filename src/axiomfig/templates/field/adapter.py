from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import numeric_1d, numeric_matrix, optional_text, scalar, text


def _color(values: dict[str, object]) -> str:
    semantics = text(values["color_semantics"], "color_semantics")
    if semantics not in {"sequential", "diverging", "cyclic"}:
        raise ValueError("field color_semantics must be sequential, diverging, or cyclic")
    values["color_semantics"] = semantics
    return semantics


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    semantics = _color(values)
    if variant == "contour":
        x = np.asarray(values["x_grid"], dtype=float)
        y = np.asarray(values["y_grid"], dtype=float)
        z = numeric_matrix(values["z"], "z")
        if x.ndim == y.ndim == 1:
            if z.shape != (y.size, x.size):
                raise ValueError("z shape must match one-dimensional x_grid and y_grid")
        elif x.shape != z.shape or y.shape != z.shape or x.ndim != 2 or y.ndim != 2:
            raise ValueError("x_grid, y_grid, and z must have compatible grid shapes")
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
            raise ValueError("x_grid and y_grid must be finite")
        values.update(x_grid=x, y_grid=y, z=z)
        if semantics == "diverging":
            if "center" not in values:
                raise ValueError("diverging contour requires an explicit center")
            values["center"] = scalar(values["center"], "center")
        elif "center" in values:
            raise ValueError("center is only valid for diverging contour semantics")
        if "levels" in values:
            levels = numeric_1d(values["levels"], "levels", minimum=2)
            if np.any(np.diff(levels) <= 0):
                raise ValueError("contour levels must be strictly increasing")
            values["levels"] = levels
    else:
        arrays = {name: np.asarray(values[name], dtype=float) for name in ("x", "y", "u", "v")}
        if not all(np.all(np.isfinite(array)) for array in arrays.values()):
            raise ValueError("quiver arrays must be finite")
        x, y, u, v = (arrays[name] for name in ("x", "y", "u", "v"))
        valid_grid = x.ndim == y.ndim == 1 and u.shape == v.shape == (y.size, x.size)
        valid_mesh = (
            x.ndim == y.ndim == u.ndim == v.ndim == 2
            and len({x.shape, y.shape, u.shape, v.shape}) == 1
        )
        if not (valid_grid or valid_mesh):
            raise ValueError("x, y, u, and v must have compatible quiver grid shapes")
        values.update(arrays)
        if "magnitude" in values:
            magnitude = numeric_matrix(values["magnitude"], "magnitude")
            if magnitude.shape != u.shape:
                raise ValueError("magnitude must match u and v")
            values["magnitude"] = magnitude
    optional_text(values, "colorbar_label", "xlabel", "ylabel")
    return values
