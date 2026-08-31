"""Blind, provider-independent Agent benchmark preparation and execution."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from axiomfig.intent import FigureIntentError, parse_figure_intent
from axiomfig.templates.registry import load_family_contract, load_template_registry
from tests.evaluation.agent_protocol import VALID_ACTIONS, VALID_INPUT_MODES
from tests.evaluation.read_broker import CORE_FILES, GLOBS, ProgressiveReadBroker

_ACTION_FIELDS = {
    "render": (
        frozenset(
            {
                "action",
                "template",
                "input_mode",
                "mapped_roles",
                "scientific_semantics",
                "scientific_inferences",
                "figure_intent",
            }
        ),
        frozenset(),
    ),
    "clarify": (frozenset({"action", "question", "reason"}), frozenset()),
    "require_precomputed": (
        frozenset({"action", "missing_result", "reason"}),
        frozenset({"candidate_template"}),
    ),
    "unsupported": (frozenset({"action", "reason"}), frozenset()),
}

_DECISION_INSTRUCTIONS = """Return exactly one JSON object using the fields for one action:
- render: action, template, input_mode, mapped_roles, scientific_semantics,
  scientific_inferences, figure_intent
- clarify: action, question, reason
- require_precomputed: action, missing_result, reason, and optional candidate_template
- unsupported: action, reason

Do not emit fields from another action and omit inapplicable fields rather than setting them to
null. mapped_roles maps executable scientific roles to one supplied column/key each and is only for
render. scientific_semantics contains only explicit meanings needed by the render decision.
scientific_inferences lists extra scientific assumptions and should normally be empty. A render
decision must include a minimal valid Figure Intent. A clarification question must ask only for a
material missing scientific distinction. A require_precomputed decision must name the missing
scientific result and explain why current data are insufficient; include candidate_template only
when the downstream registered figure is already resolved. Do not include an evaluation identifier
or explanatory essay."""


def _allowed_files(source_root: Path) -> tuple[Path, ...]:
    source_root = Path(source_root).resolve()
    paths = [source_root / relative for relative in CORE_FILES]
    for pattern in GLOBS:
        paths.extend(sorted(source_root.glob(pattern)))
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"missing Agent surface files: {missing}")
    if any(path.is_symlink() for path in paths):
        raise ValueError("Agent surface must not contain symbolic links")
    return tuple(dict.fromkeys(paths))


def prepare_sanitized_workspace(source_root: Path, destination: Path) -> frozenset[Path]:
    """Copy only the normal Agent-facing Skill surface into ``destination``."""

    source_root = Path(source_root).resolve()
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("sanitized workspace must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    copied: set[Path] = set()
    for source in _allowed_files(source_root):
        relative = source.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.add(target)
    return frozenset(copied)


def _surface_text(workspace: Path) -> str:
    workspace = Path(workspace).resolve()
    sections: list[str] = []
    for path in sorted(item for item in workspace.rglob("*") if item.is_file()):
        relative = path.relative_to(workspace)
        content = path.read_text(encoding="utf-8")
        sections.append(f'<axiomfig-file path="{relative}">\n{content}\n</axiomfig-file>')
    return "\n\n".join(sections)


def build_agent_prompt(workspace: Path, case: Mapping[str, Any]) -> str:
    """Build one case prompt without case identifiers, classes, or expected decisions."""

    request = case.get("request")
    available_data = case.get("available_data")
    if not isinstance(request, str) or not request.strip():
        raise ValueError("case request must be a non-empty string")
    if not isinstance(available_data, Mapping):
        raise ValueError("case available_data must be a mapping")
    case_input = json.dumps(
        {"request": request, "available_data": dict(available_data)},
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"""You are the AxiomFig scientific-routing Agent. Use only the embedded AxiomFig Skill
surface and the supplied researcher request. Decide conservatively: scientific safety is more
important than render rate. Never perform missing upstream analysis or infer material scientific
semantics. Do not provide chain-of-thought.

{_DECISION_INSTRUCTIONS}

<axiomfig-skill-surface>
{_surface_text(workspace)}
</axiomfig-skill-surface>

<researcher-input>
{case_input}
</researcher-input>
"""


def build_progressive_agent_prompt(
    workspace: Path,
    case: Mapping[str, Any],
    history: Sequence[tuple[str | None, str | None]] = (),
) -> str:
    """Build a blind case prompt that preloads only the top-level AxiomFig Skill."""

    request = case.get("request")
    available_data = case.get("available_data")
    if not isinstance(request, str) or not request.strip():
        raise ValueError("case request must be a non-empty string")
    if not isinstance(available_data, Mapping):
        raise ValueError("case available_data must be a mapping")
    workspace = Path(workspace).resolve()
    skill = (workspace / "SKILL.md").read_text(encoding="utf-8")
    case_input = json.dumps(
        {"request": request, "available_data": dict(available_data)},
        ensure_ascii=False,
        sort_keys=True,
    )
    disclosed: list[str] = []
    for path, content in history:
        if path is None:
            disclosed.append("<broker-denied>read denied</broker-denied>")
        else:
            disclosed.append(f'<broker-response path="{path}">\n{content}\n</broker-response>')
    disclosure = "\n\n".join(disclosed)
    disclosure_block = f"\n\n<broker-history>\n{disclosure}\n</broker-history>" if disclosed else ""
    return f"""You are the AxiomFig scientific-routing Agent. Start from the embedded top-level
AxiomFig Skill and the supplied researcher request. Request additional AxiomFig files only through
the read broker by returning exactly `{{"read":"relative/path"}}`, one path per turn, following the
Skill's normal progressive-disclosure route. A later prompt will include only that broker response
and this case's prior broker history. Do not try to list, search, browse, execute code, use another
tool, or access any host/repository path. Decide conservatively: scientific safety is more important
than render rate. Never perform missing upstream analysis or infer material scientific semantics.
Do not provide chain-of-thought.

{_DECISION_INSTRUCTIONS}

<axiomfig-file path="SKILL.md">
{skill}
</axiomfig-file>

<researcher-input>
{case_input}
</researcher-input>{disclosure_block}
"""


def parse_progressive_turn(payload: str) -> dict[str, Any]:
    """Parse either one broker read request or one final observable decision."""

    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent response must be one JSON object") from exc
    if isinstance(raw, Mapping) and set(raw) == {"read"}:
        path = raw["read"]
        if not isinstance(path, str) or not path:
            raise ValueError("read must be a non-empty relative path")
        return {"read": path}
    return parse_agent_decision(payload)


def _mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{location} must be a mapping with string keys")
    return dict(value)


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a non-empty string")
    return value.strip()


def _string_list(value: object, location: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{location} must be an array")
    if not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{location} must contain non-empty strings")
    return list(value)


def _normalized_template(value: object, location: str) -> str | None:
    if value is None:
        return None
    text = _text(value, location)
    normalized = text.replace(".", "/")
    valid = {spec.template_id for spec in load_template_registry()}
    if normalized not in valid:
        raise ValueError(f"unknown template: {text!r}")
    return normalized


def parse_agent_decision(payload: str) -> dict[str, Any]:
    """Parse exactly one observable Agent decision and validate its executable boundary."""

    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent response must be a single JSON object") from exc
    if not isinstance(raw, Mapping):
        raise ValueError("Agent response must be a single JSON object")
    decision = _mapping(raw, "Agent response")
    action = decision.get("action")
    if action not in VALID_ACTIONS:
        raise ValueError(f"invalid action {action!r}")
    required, optional = _ACTION_FIELDS[action]
    missing = required - set(decision)
    unknown = set(decision) - required - optional
    if missing or unknown:
        raise ValueError(
            f"{action} fields must match its decision schema; "
            f"missing={sorted(missing)}, unknown={sorted(unknown)}"
        )

    if action == "render":
        template_id = _normalized_template(decision["template"], "template")
        input_mode = decision["input_mode"]
        if input_mode not in VALID_INPUT_MODES:
            raise ValueError(f"invalid input_mode {input_mode!r}")
        mapped_roles = _mapping(decision["mapped_roles"], "mapped_roles")
        if not mapped_roles or not all(
            isinstance(value, str) and value for value in mapped_roles.values()
        ):
            raise ValueError("mapped_roles values must be non-empty strings")
        scientific_semantics = _mapping(decision["scientific_semantics"], "scientific_semantics")
        scientific_inferences = _string_list(
            decision["scientific_inferences"], "scientific_inferences"
        )
        figure_intent = _mapping(decision["figure_intent"], "figure_intent")
        try:
            parsed_intent = parse_figure_intent(figure_intent)
        except FigureIntentError as exc:
            raise ValueError(f"invalid Figure Intent: {exc}") from exc
        if parsed_intent.template_id != template_id:
            raise ValueError("template must match Figure Intent template")
        if dict(parsed_intent.data) != mapped_roles:
            raise ValueError("mapped_roles must match Figure Intent data")
        family, variant = template_id.split("/", maxsplit=1)
        contract_mode = load_family_contract(family)["variants"][variant]["input_mode"]
        if input_mode != contract_mode:
            raise ValueError("input_mode must match the selected family contract")
        return {
            **decision,
            "template": template_id,
            "mapped_roles": mapped_roles,
            "scientific_semantics": scientific_semantics,
            "scientific_inferences": scientific_inferences,
            "figure_intent": figure_intent,
        }
    if action == "clarify":
        return {
            "action": action,
            "question": _text(decision["question"], "question"),
            "reason": _text(decision["reason"], "reason"),
        }
    if action == "require_precomputed":
        parsed = {
            "action": action,
            "missing_result": _text(decision["missing_result"], "missing_result"),
            "reason": _text(decision["reason"], "reason"),
        }
        if "candidate_template" in decision:
            candidate = _normalized_template(decision["candidate_template"], "candidate_template")
            assert candidate is not None
            family, variant = candidate.split("/", maxsplit=1)
            contract_mode = load_family_contract(family)["variants"][variant]["input_mode"]
            if contract_mode != "precomputed":
                raise ValueError("candidate_template must use a precomputed family contract")
            parsed["candidate_template"] = candidate
        return parsed
    return {"action": action, "reason": _text(decision["reason"], "reason")}


def scoring_record(case_id: str, decision: Mapping[str, Any]) -> dict[str, Any]:
    """Attach the hidden case ID only after the Agent context has terminated."""

    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case_id must be a non-empty string")
    record = dict(decision)
    record["id"] = case_id
    return record


def _load_selected_cases(path: Path, case_ids: Sequence[str]) -> list[dict[str, Any]]:
    document = _mapping(yaml.safe_load(Path(path).read_text(encoding="utf-8")), "benchmark")
    raw_cases = document.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("benchmark.cases must be a list")
    indexed = {str(case["id"]): _mapping(case, "case") for case in raw_cases}
    if len(indexed) != len(raw_cases):
        raise ValueError("benchmark contains duplicate case IDs")
    missing = set(case_ids) - set(indexed)
    if missing:
        raise ValueError(f"unknown selected case IDs: {sorted(missing)}")
    return [indexed[case_id] for case_id in case_ids]


def run_blind_cases(
    source_root: Path,
    cases_path: Path,
    case_ids: Sequence[str],
    agent_command: Sequence[str],
    output_path: Path,
    workspace_root: Path,
) -> tuple[int, int]:
    """Run one fresh external Agent process per case and persist observable decisions."""

    if not case_ids:
        raise ValueError("at least one case ID is required")
    if not agent_command:
        raise ValueError("an external Agent command is required")
    workspace_root = Path(workspace_root).resolve()
    if workspace_root.exists() and any(workspace_root.iterdir()):
        raise ValueError("benchmark workspace must be empty")
    skill_workspace = workspace_root / "sandbox" / "skill"
    prepare_sanitized_workspace(source_root, skill_workspace)
    cases = _load_selected_cases(cases_path, case_ids)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path = output_path.with_suffix(".failures.jsonl")
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    child_environment = os.environ.copy()
    for name in (
        "CODEX_APP_TOOLS_PIPE_PATH",
        "CODEX_MCP_NODE_PATH",
        "CODEX_PERMISSION_PROFILE",
        "CODEX_SESSION_ID",
        "CODEX_THREAD_ID",
    ):
        child_environment.pop(name, None)
    child_environment["CODEX_INTERNAL_ORIGINATOR_OVERRIDE"] = "axiomfig-blind-benchmark"

    for index, (case_id, case) in enumerate(zip(case_ids, cases, strict=True), start=1):
        case_directory = workspace_root / "sandbox" / "cases" / f"{index:03d}"
        case_directory.mkdir(parents=True)
        completed = subprocess.run(
            list(agent_command),
            input=build_agent_prompt(skill_workspace, case),
            cwd=case_directory,
            env=child_environment,
            capture_output=True,
            check=False,
            text=True,
        )
        log_directory = workspace_root / "logs"
        log_directory.mkdir(parents=True, exist_ok=True)
        (log_directory / f"{index:03d}.stdout").write_text(completed.stdout, encoding="utf-8")
        (log_directory / f"{index:03d}.stderr").write_text(completed.stderr, encoding="utf-8")
        try:
            if completed.returncode:
                raise ValueError(f"Agent command exited with status {completed.returncode}")
            decision = parse_agent_decision(completed.stdout)
        except ValueError as exc:
            failures.append({"id": case_id, "sequence": index, "error": str(exc)})
            continue
        records.append(scoring_record(case_id, decision))

    output_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    failure_path.write_text(
        "".join(json.dumps(failure, ensure_ascii=False) + "\n" for failure in failures),
        encoding="utf-8",
    )
    return len(records), len(failures)


def run_progressive_cases(
    source_root: Path,
    cases_path: Path,
    case_ids: Sequence[str],
    agent_command: Sequence[str],
    output_path: Path,
    workspace_root: Path,
    *,
    max_turns: int = 12,
    turn_timeout: float | None = None,
) -> tuple[int, int]:
    """Run stateless progressive-disclosure turns in one isolated logical context per case."""

    if not case_ids:
        raise ValueError("at least one case ID is required")
    if not agent_command:
        raise ValueError("an external Agent command is required")
    if max_turns < 2:
        raise ValueError("max_turns must allow at least one read and one decision")
    workspace_root = Path(workspace_root).resolve()
    if workspace_root.exists() and any(workspace_root.iterdir()):
        raise ValueError("benchmark workspace must be empty")
    skill_workspace = workspace_root / "sandbox" / "skill"
    prepare_sanitized_workspace(source_root, skill_workspace)
    broker = ProgressiveReadBroker(skill_workspace)
    cases = _load_selected_cases(cases_path, case_ids)
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path = output_path.with_suffix(".failures.jsonl")
    disclosure_path = output_path.with_suffix(".disclosure.jsonl")
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    disclosures: list[dict[str, Any]] = []
    child_environment = os.environ.copy()
    for name in (
        "CODEX_APP_TOOLS_PIPE_PATH",
        "CODEX_MCP_NODE_PATH",
        "CODEX_PERMISSION_PROFILE",
        "CODEX_SESSION_ID",
        "CODEX_THREAD_ID",
    ):
        child_environment.pop(name, None)
    child_environment["CODEX_INTERNAL_ORIGINATOR_OVERRIDE"] = "axiomfig-routed-benchmark"
    initial_bytes = len((skill_workspace / "SKILL.md").read_bytes())

    for index, (case_id, case) in enumerate(zip(case_ids, cases, strict=True), start=1):
        case_directory = workspace_root / "sandbox" / "cases" / f"{index:03d}"
        case_directory.mkdir(parents=True)
        log_directory = workspace_root / "logs" / f"{index:03d}"
        log_directory.mkdir(parents=True)
        history: list[tuple[str | None, str | None]] = []
        files_read: list[str] = []
        read_bytes = 0
        denied_reads = 0
        final_decision: dict[str, Any] | None = None
        error: str | None = None

        for turn_number in range(1, max_turns + 1):
            prompt = build_progressive_agent_prompt(skill_workspace, case, history)
            (log_directory / f"turn-{turn_number:02d}.prompt").write_text(prompt, encoding="utf-8")
            try:
                completed = subprocess.run(
                    list(agent_command),
                    input=prompt,
                    cwd=case_directory,
                    env=child_environment,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=turn_timeout,
                )
            except subprocess.TimeoutExpired as exc:
                stdout = (
                    exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                )
                stderr = (
                    exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
                )
                (log_directory / f"turn-{turn_number:02d}.stdout").write_text(
                    stdout, encoding="utf-8"
                )
                (log_directory / f"turn-{turn_number:02d}.stderr").write_text(
                    stderr, encoding="utf-8"
                )
                error = f"Agent command exceeded {turn_timeout:g} seconds"
                break
            (log_directory / f"turn-{turn_number:02d}.stdout").write_text(
                completed.stdout, encoding="utf-8"
            )
            (log_directory / f"turn-{turn_number:02d}.stderr").write_text(
                completed.stderr, encoding="utf-8"
            )
            if completed.returncode:
                error = f"Agent command exited with status {completed.returncode}"
                break
            try:
                turn = parse_progressive_turn(completed.stdout)
            except ValueError as exc:
                error = str(exc)
                break
            requested_path = turn.get("read")
            if isinstance(requested_path, str):
                try:
                    content = broker.read(requested_path)
                except ValueError:
                    history.append((None, None))
                    denied_reads += 1
                else:
                    history.append((requested_path, content))
                    files_read.append(requested_path)
                    read_bytes += len(content.encode("utf-8"))
                continue
            final_decision = turn
            break
        else:
            error = f"Agent did not return a final decision within {max_turns} turns"

        process_count = len(list(log_directory.glob("turn-*.stdout")))
        agent_facing_bytes = initial_bytes + read_bytes
        disclosures.append(
            {
                "id": case_id,
                "read_count": len(files_read),
                "files": files_read,
                "read_bytes": read_bytes,
                "agent_facing_bytes": agent_facing_bytes,
                "estimated_tokens": (agent_facing_bytes + 3) // 4,
                "denied_reads": denied_reads,
                "process_count": process_count,
            }
        )
        if error is not None or final_decision is None:
            failures.append(
                {"id": case_id, "sequence": index, "error": error or "missing decision"}
            )
            continue
        records.append(scoring_record(case_id, final_decision))

    output_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    failure_path.write_text(
        "".join(json.dumps(failure, ensure_ascii=False) + "\n" for failure in failures),
        encoding="utf-8",
    )
    disclosure_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in disclosures),
        encoding="utf-8",
    )
    return len(records), len(failures)


def _main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases", type=Path, default=root / "tests/evaluation/agent_protocol_cases.yaml"
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--case-id", action="append")
    selection.add_argument("--all-cases", action="store_true")
    parser.add_argument("--progressive", action="store_true")
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--turn-timeout", type=float)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("agent_command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.agent_command[1:] if args.agent_command[:1] == ["--"] else args.agent_command
    if args.all_cases:
        document = _mapping(yaml.safe_load(args.cases.read_text(encoding="utf-8")), "benchmark")
        raw_cases = document.get("cases")
        if not isinstance(raw_cases, list):
            parser.error("benchmark.cases must be a list")
        case_ids = [str(_mapping(case, "case")["id"]) for case in raw_cases]
    else:
        case_ids = args.case_id
    if args.progressive:
        passed, failed = run_progressive_cases(
            root,
            args.cases,
            case_ids,
            command,
            args.output,
            args.workspace,
            max_turns=args.max_turns,
            turn_timeout=args.turn_timeout,
        )
    else:
        passed, failed = run_blind_cases(
            root,
            args.cases,
            case_ids,
            command,
            args.output,
            args.workspace,
        )
    print(f"Agent benchmark completed: {passed} parsed, {failed} format failures")
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    _main()
