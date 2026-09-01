"""Run blind progressive-disclosure element-adjustment benchmark sessions."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from axiomfig.structured_io import load_yaml
from tests.evaluation.blind_agent import prepare_sanitized_workspace
from tests.evaluation.element_adjustment.scoring import parse_adjustment_decision
from tests.evaluation.read_broker import ProgressiveReadBroker

ELEMENT_FILES = (
    "references/figure-anatomy.md",
    "references/style-contract.md",
    "references/layout-contract.md",
    "references/typography.md",
    "references/validation.md",
)
ELEMENT_GLOB = "references/element-contracts/*.md"

_DECISION_INSTRUCTIONS = """Return either exactly {"read":"relative/path"} to request one
allowlisted AxiomFig file, or one final JSON object with exactly these fields:
element, needs_nondefault, topic, recommended_surface, surface_status, implementation_level,
default_retained_elsewhere, low_level_parameters_proposed, backend_names_exposed,
scientific_anchor_preserved, reason.

topic is none, axes, marks, ornaments, or annotations. surface_status is DEFAULT, AVAILABLE,
INTERNAL_ONLY, PLANNED, or NOT_SUPPORTED. implementation_level is none, public, or runtime.
low_level_parameters_proposed contains only low-level numeric/backend parameters you actively
recommend as the user-facing solution; do not copy rejected wording from the request.
backend_names_exposed contains only backend/library names you expose as part of the recommended
user-facing adjustment. Use empty arrays when none. Do not return chain-of-thought or an essay."""


def prepare_condition_workspace(source_root: Path, destination: Path) -> frozenset[Path]:
    """Copy only normal Agent-facing files; include element contracts only when present."""

    source_root = Path(source_root).resolve()
    destination = Path(destination).resolve()
    copied = set(prepare_sanitized_workspace(source_root, destination))
    extras = [source_root / relative for relative in ELEMENT_FILES]
    extras.extend(sorted(source_root.glob(ELEMENT_GLOB)))
    for source in extras:
        if not source.is_file():
            continue
        if source.is_symlink():
            raise ValueError("Agent surface must not contain symbolic links")
        target = destination / source.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.add(target)
    return frozenset(copied)


def parse_codex_metadata(stderr: str) -> dict[str, Any]:
    """Extract observable Codex session identity and actual total-token accounting."""

    session = re.search(r"session id:\s*([0-9a-f-]{36})", stderr, re.IGNORECASE)
    tokens = re.search(r"tokens used\s*\n\s*([0-9,]+)", stderr, re.IGNORECASE)
    return {
        "session_id": session.group(1) if session else None,
        "total_tokens": int(tokens.group(1).replace(",", "")) if tokens else None,
    }


def _case_prompt(
    workspace: Path,
    case: Mapping[str, Any],
    history: Sequence[tuple[str | None, str | None]],
) -> str:
    skill = (workspace / "SKILL.md").read_text(encoding="utf-8")
    disclosed = []
    for path, content in history:
        if path is None:
            disclosed.append("<broker-denied>read denied</broker-denied>")
        else:
            disclosed.append(f'<broker-response path="{path}">\n{content}\n</broker-response>')
    history_block = ""
    if disclosed:
        history_block = "\n\n<broker-history>\n" + "\n\n".join(disclosed) + "\n</broker-history>"
    case_input = json.dumps(
        {"request": case["request"], "available_data": case["available_data"]},
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"""You are the AxiomFig figure-adjustment decision Agent. Start only from the embedded
top-level Skill. Preserve deterministic defaults unless the researcher has a real non-default
semantic need. Never invent a Figure Intent field, backend option, physical visual number, or
plotting-library argument. Request additional AxiomFig files only through the read broker, one file
per turn. Do not list/search/browse files, execute code, call tools, or access host paths.

{_DECISION_INSTRUCTIONS}

<axiomfig-file path="SKILL.md">
{skill}
</axiomfig-file>
<researcher-input>
{case_input}
</researcher-input>{history_block}
"""


def _parse_turn(payload: str) -> dict[str, Any]:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent response must be one JSON object") from exc
    if isinstance(raw, Mapping) and set(raw) == {"read"}:
        path = raw["read"]
        if not isinstance(path, str) or not path:
            raise ValueError("read must be a non-empty relative path")
        return {"read": path}
    return parse_adjustment_decision(payload)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    document = load_yaml(Path(path).read_text(encoding="utf-8"), source=str(path))
    cases = document.get("cases") if isinstance(document, Mapping) else None
    if not isinstance(cases, list) or not cases:
        raise ValueError("benchmark cases must be a non-empty list")
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("benchmark contains duplicate case IDs")
    return [dict(case) for case in cases]


def _child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in (
        "CODEX_APP_TOOLS_PIPE_PATH",
        "CODEX_MCP_NODE_PATH",
        "CODEX_PERMISSION_PROFILE",
        "CODEX_SESSION_ID",
        "CODEX_THREAD_ID",
    ):
        environment.pop(name, None)
    environment["CODEX_INTERNAL_ORIGINATOR_OVERRIDE"] = "axiomfig-element-adjustment-benchmark"
    return environment


def _run_one(
    case: Mapping[str, Any],
    condition: str,
    replicate: int,
    command: Sequence[str],
    skill_workspace: Path,
    sessions_root: Path,
    max_turns: int,
    timeout: float,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]]:
    case_id = str(case["id"])
    session_name = f"{case_id}-{condition}-r{replicate}"
    case_directory = sessions_root / session_name / "cwd"
    log_directory = sessions_root / session_name / "logs"
    case_directory.mkdir(parents=True)
    log_directory.mkdir(parents=True)
    allowed = {
        path.relative_to(skill_workspace).as_posix()
        for path in skill_workspace.rglob("*")
        if path.is_file()
    }
    broker = ProgressiveReadBroker(skill_workspace, allowed_paths=allowed)
    history: list[tuple[str | None, str | None]] = []
    files_read: list[str] = []
    denied_reads = 0
    read_bytes = 0
    session_ids: list[str] = []
    total_tokens = 0
    tokens_available = True
    final: dict[str, Any] | None = None
    error: str | None = None

    for turn in range(1, max_turns + 1):
        prompt = _case_prompt(skill_workspace, case, history)
        (log_directory / f"turn-{turn:02d}.prompt").write_text(prompt, encoding="utf-8")
        try:
            completed = subprocess.run(
                list(command),
                input=prompt,
                cwd=case_directory,
                env=_child_environment(),
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            error = f"Agent command exceeded {timeout:g} seconds"
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            (log_directory / f"turn-{turn:02d}.stdout").write_text(stdout, encoding="utf-8")
            (log_directory / f"turn-{turn:02d}.stderr").write_text(stderr, encoding="utf-8")
            break
        (log_directory / f"turn-{turn:02d}.stdout").write_text(completed.stdout, encoding="utf-8")
        (log_directory / f"turn-{turn:02d}.stderr").write_text(completed.stderr, encoding="utf-8")
        metadata = parse_codex_metadata(completed.stderr)
        if metadata["session_id"]:
            session_ids.append(metadata["session_id"])
        if metadata["total_tokens"] is None:
            tokens_available = False
        else:
            total_tokens += metadata["total_tokens"]
        if completed.returncode:
            error = f"Agent command exited with status {completed.returncode}"
            break
        try:
            parsed = _parse_turn(completed.stdout)
        except ValueError as exc:
            error = str(exc)
            break
        requested = parsed.get("read")
        if isinstance(requested, str):
            try:
                content = broker.read(requested)
            except (OSError, UnicodeError, ValueError):
                history.append((None, None))
                denied_reads += 1
            else:
                history.append((requested, content))
                files_read.append(requested)
                read_bytes += len(content.encode("utf-8"))
            continue
        final = parsed
        break
    else:
        error = f"Agent did not return a final decision within {max_turns} turns"

    disclosure = {
        "id": case_id,
        "condition": condition,
        "replicate": replicate,
        "files": files_read,
        "read_count": len(files_read),
        "read_bytes": read_bytes,
        "agent_facing_bytes": len((skill_workspace / "SKILL.md").read_bytes()) + read_bytes,
        "denied_reads": denied_reads,
        "process_count": len(list(log_directory.glob("turn-*.stdout"))),
        "session_ids": session_ids,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": total_tokens if tokens_available else None,
    }
    if error or final is None:
        failure = {
            "id": case_id,
            "condition": condition,
            "replicate": replicate,
            "error": error or "missing decision",
        }
        return None, failure, disclosure
    record = {"id": case_id, "condition": condition, "replicate": replicate, **final}
    return record, None, disclosure


def run_condition(
    source_root: Path,
    cases_path: Path,
    condition: str,
    repetitions: int,
    command: Sequence[str],
    output_path: Path,
    workspace_root: Path,
    *,
    jobs: int = 1,
    max_turns: int = 10,
    timeout: float = 240.0,
) -> tuple[int, int]:
    """Run fresh logical sessions for every case/replicate in one condition."""

    if condition not in {"baseline", "treatment"}:
        raise ValueError("condition must be baseline or treatment")
    if repetitions < 1 or jobs < 1 or not command:
        raise ValueError("repetitions, jobs, and external Agent command are required")
    workspace_root = Path(workspace_root).resolve()
    if workspace_root.exists() and any(workspace_root.iterdir()):
        raise ValueError("benchmark workspace must be empty")
    skill_workspace = workspace_root / "sandbox" / "skill"
    prepare_condition_workspace(source_root, skill_workspace)
    cases = _load_cases(cases_path)
    sessions_root = workspace_root / "sandbox" / "sessions"
    tasks = [(case, replicate) for case in cases for replicate in range(1, repetitions + 1)]
    results = []
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(
                _run_one,
                case,
                condition,
                replicate,
                command,
                skill_workspace,
                sessions_root,
                max_turns,
                timeout,
            ): (case["id"], replicate)
            for case, replicate in tasks
        }
        for future in as_completed(futures):
            results.append(future.result())
    records = [record for record, _failure, _disclosure in results if record is not None]
    failures = [failure for _record, failure, _disclosure in results if failure is not None]
    disclosures = [disclosure for _record, _failure, disclosure in results]

    def sort_key(item: Mapping[str, Any]) -> tuple[str, int]:
        return str(item["id"]), int(item["replicate"])

    records.sort(key=sort_key)
    failures.sort(key=sort_key)
    disclosures.sort(key=sort_key)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )
    output_path.with_suffix(".failures.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in failures),
        encoding="utf-8",
    )
    output_path.with_suffix(".disclosure.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in disclosures),
        encoding="utf-8",
    )
    return len(records), len(failures)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.yaml"))
    parser.add_argument("--condition", choices=("baseline", "treatment"), required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--turn-timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("agent_command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.agent_command[1:] if args.agent_command[:1] == ["--"] else args.agent_command
    passed, failed = run_condition(
        args.source_root,
        args.cases,
        args.condition,
        args.repetitions,
        command,
        args.output,
        args.workspace,
        jobs=args.jobs,
        max_turns=args.max_turns,
        timeout=args.turn_timeout,
    )
    print(f"Element adjustment {args.condition}: {passed} parsed, {failed} failures")
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
