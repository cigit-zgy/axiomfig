"""Explicit association-family builder registry."""

from axiomfig.templates.association.correlation_network import build_correlation_network
from axiomfig.templates.association.mantel import build_mantel

BUILDERS = {"mantel": build_mantel, "correlation_network": build_correlation_network}

__all__ = ["BUILDERS"]
