from __future__ import annotations

import numpy as np

from axiomfig.templates._adapter import labels_1d, numeric_1d


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    del variant
    values = dict(supplied)
    time = numeric_1d(values["time"], "time", minimum=2)
    survival = numeric_1d(values["survival_probability"], "survival_probability", minimum=2)
    if time.size != survival.size:
        raise ValueError("time and survival_probability must be equal-length")
    if np.any(survival < 0) or np.any(survival > 1):
        raise ValueError("survival_probability must lie between 0 and 1")
    values.update(time=time, survival_probability=survival)
    if "group" in values:
        group = labels_1d(values["group"], "group")
        if group.size != time.size:
            raise ValueError("group must match survival data")
        values["group"] = group
    if "censoring" in values:
        censoring = np.asarray(values["censoring"], dtype=bool)
        if censoring.shape != time.shape:
            raise ValueError("censoring must match survival data")
        values["censoring"] = censoring
    for role in ("lower_ci", "upper_ci"):
        if role in values:
            bound = numeric_1d(values[role], role, minimum=2)
            if bound.size != time.size:
                raise ValueError(f"{role} must match survival data")
            values[role] = bound
    if ("lower_ci" in values) != ("upper_ci" in values):
        raise ValueError("lower_ci and upper_ci must be supplied together")
    if "lower_ci" in values and (
        np.any(values["lower_ci"] > survival) or np.any(values["upper_ci"] < survival)
    ):
        raise ValueError("survival confidence bounds must contain the curve")
    if "censor_time" in values:
        values["censor_time"] = numeric_1d(values["censor_time"], "censor_time")
        if "group" in values and len(set(np.asarray(values["group"], dtype=object).tolist())) > 1:
            raise ValueError("censor_time without group labels only supports one survival series")
    return values
