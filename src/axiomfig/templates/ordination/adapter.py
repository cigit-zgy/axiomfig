from __future__ import annotations

from axiomfig.templates._adapter import coordinates, labels_1d, numeric_1d, scalar, text


def adapt(variant: str, supplied: dict[str, object]) -> dict[str, object]:
    values = dict(supplied)
    scores = coordinates(values["coordinates"], "coordinates")
    values["coordinates"] = scores
    if "group" in values:
        group = labels_1d(values["group"], "group")
        if group.size != scores.shape[0]:
            raise ValueError("ordination group must match coordinate rows")
        values["group"] = group
    if "sample_labels" in values:
        labels = labels_1d(values["sample_labels"], "sample_labels")
        if labels.size != scores.shape[0]:
            raise ValueError("sample_labels must match coordinate rows")
        values["sample_labels"] = labels
    if "explained_variance" in values:
        variance = numeric_1d(values["explained_variance"], "explained_variance")
        if variance.shape != (2,):
            raise ValueError("explained_variance must contain two values")
        values["explained_variance"] = variance
    if variant == "pca_biplot":
        loadings = coordinates(values["loadings"], "loadings", minimum=1)
        values["loadings"] = loadings
        if "feature_labels" in values:
            labels = labels_1d(values["feature_labels"], "feature_labels")
            if labels.size != loadings.shape[0]:
                raise ValueError("feature_labels must match loading rows")
            values["feature_labels"] = labels
    if "distance_metric" in values:
        values["distance_metric"] = text(values["distance_metric"], "distance_metric")
    if "stress" in values:
        stress = scalar(values["stress"], "stress")
        if stress < 0:
            raise ValueError("stress must be non-negative")
        values["stress"] = stress
    return values
