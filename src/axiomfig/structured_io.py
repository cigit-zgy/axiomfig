"""Strict loaders for project-owned structured data."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any

import yaml
from yaml.nodes import MappingNode


class StructuredDataError(ValueError):
    """Raised when structured data is malformed or ambiguous."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Hashable, Any]:
    loader.flatten_mapping(node)
    result: dict[Hashable, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, Hashable):
            raise StructuredDataError("YAML mapping keys must be hashable")
        if key in result:
            raise StructuredDataError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(text: str, *, source: str) -> object:
    """Parse safe YAML while rejecting duplicate keys and malformed input."""

    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    except StructuredDataError as exc:
        raise StructuredDataError(f"{source}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise StructuredDataError(f"cannot parse YAML from {source}: {exc}") from exc
