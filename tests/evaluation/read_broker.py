"""Fail-closed read broker for progressive-disclosure Agent evaluation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any

CORE_FILES = (
    "SKILL.md",
    "references/agent-protocol.md",
    "references/figure-intent.md",
    "references/mantel.md",
    "references/template-knowledge/index.yaml",
    "src/axiomfig/templates/index.yaml",
)
GLOBS = (
    "references/template-knowledge/*.md",
    "src/axiomfig/templates/*/contract.yaml",
)


def allowed_relative_paths(root: Path) -> frozenset[str]:
    """Return the explicit Agent-facing allowlist present under ``root``."""

    root = Path(root).resolve()
    paths = set(CORE_FILES)
    for pattern in GLOBS:
        paths.update(path.relative_to(root).as_posix() for path in root.glob(pattern))
    missing = [relative for relative in paths if not (root / relative).is_file()]
    if missing:
        raise ValueError(f"missing Agent surface files: {sorted(missing)}")
    return frozenset(paths)


class ProgressiveReadBroker:
    """Read exactly one allowlisted relative file and record successful disclosure."""

    def __init__(
        self,
        root: Path,
        log_path: Path | None = None,
        *,
        allowed_paths: Iterable[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.log_path = Path(log_path).resolve() if log_path is not None else None
        self.allowed_paths = frozenset(
            allowed_relative_paths(self.root) if allowed_paths is None else allowed_paths
        )

    def read(self, requested_path: str) -> str:
        """Return one allowed UTF-8 file or reject the request without path disclosure."""

        if not isinstance(requested_path, str) or not requested_path:
            raise ValueError("read denied")
        if "\\" in requested_path or any(char in requested_path for char in "*?[]{};"):
            raise ValueError("read denied")
        relative = PurePosixPath(requested_path)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValueError("read denied")
        normalized = relative.as_posix()
        if normalized not in self.allowed_paths:
            raise ValueError("read denied")

        candidate = self.root / normalized
        current = self.root
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise ValueError("read denied")
        if not candidate.is_file() or not candidate.resolve().is_relative_to(self.root):
            raise ValueError("read denied")

        content = candidate.read_text(encoding="utf-8")
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps(
                        {"path": normalized, "bytes": len(content.encode("utf-8"))},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        return content


def _tool() -> dict[str, Any]:
    return {
        "name": "read",
        "description": "Read one allowlisted AxiomFig Agent-facing file by relative path.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
    }


def _result(request_id: object, result: Mapping[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": dict(result)}


def _error(request_id: object, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": message},
    }


def _handle(message: Mapping[str, Any], broker: ProgressiveReadBroker) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params", {})
    if method == "initialize":
        protocol = (
            params.get("protocolVersion", "2025-06-18")
            if isinstance(params, Mapping)
            else "2025-06-18"
        )
        return _result(
            request_id,
            {
                "protocolVersion": protocol,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "axiomfig-read", "version": "1"},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": [_tool()]})
    if method == "tools/call":
        if not isinstance(params, Mapping) or params.get("name") != "read":
            return _result(
                request_id,
                {"content": [{"type": "text", "text": "read denied"}], "isError": True},
            )
        arguments = params.get("arguments", {})
        try:
            if not isinstance(arguments, Mapping) or set(arguments) != {"path"}:
                raise ValueError("read denied")
            content = broker.read(arguments["path"])
        except (OSError, UnicodeError, ValueError):
            return _result(
                request_id,
                {"content": [{"type": "text", "text": "read denied"}], "isError": True},
            )
        return _result(request_id, {"content": [{"type": "text", "text": content}]})
    if request_id is None:
        return None
    return _error(request_id, "method not found")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    root_value = str(args.root) if args.root is not None else os.environ.get("AXIOMFIG_BROKER_ROOT")
    if not root_value:
        raise SystemExit("AXIOMFIG_BROKER_ROOT is required")
    log_value = str(args.log) if args.log is not None else os.environ.get("AXIOMFIG_BROKER_LOG")
    broker = ProgressiveReadBroker(root_value, Path(log_value) if log_value else None)
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if not isinstance(message, Mapping):
                raise ValueError
            response = _handle(message, broker)
        except (json.JSONDecodeError, ValueError):
            response = _error(None, "invalid request")
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
