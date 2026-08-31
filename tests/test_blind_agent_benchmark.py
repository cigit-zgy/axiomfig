from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _render_decision() -> dict[str, object]:
    return {
        "action": "render",
        "template": "scatter.parity",
        "input_mode": "direct",
        "mapped_roles": {"observed": "measured", "predicted": "predicted"},
        "scientific_semantics": {},
        "scientific_inferences": [],
        "figure_intent": {
            "template": "scatter.parity",
            "data": {"observed": "measured", "predicted": "predicted"},
        },
    }


def test_sanitized_workspace_exposes_only_the_agent_surface(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    copied = prepare_sanitized_workspace(ROOT, destination)

    assert destination / "SKILL.md" in copied
    assert destination / "references/agent-protocol.md" in copied
    assert destination / "references/figure-intent.md" in copied
    assert destination / "references/template-knowledge/index.yaml" in copied
    assert destination / "src/axiomfig/templates/index.yaml" in copied
    assert len(list(destination.glob("src/axiomfig/templates/*/contract.yaml"))) == 14
    assert not (destination / "tests").exists()
    assert not (destination / "reports").exists()
    assert not (destination / ".git").exists()
    assert not any(path.is_symlink() for path in destination.rglob("*"))


def test_case_prompt_excludes_gold_metadata_and_case_identifier(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import build_agent_prompt, prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    case = {
        "id": "SECRET-CASE-ID",
        "request": "Compare measured and predicted nitrate concentrations.",
        "available_data": {"format": "csv", "columns": ["measured", "predicted"]},
        "language": "en",
        "classes": ["SECRET-CLASS"],
        "expected": {"action": "render", "reason": "GOLD-ANSWER-SENTINEL"},
    }

    prompt = build_agent_prompt(destination, case)

    assert case["request"] in prompt
    assert '"measured"' in prompt
    assert "SECRET-CASE-ID" not in prompt
    assert "SECRET-CLASS" not in prompt
    assert "GOLD-ANSWER-SENTINEL" not in prompt
    assert "agent_protocol_cases.yaml" not in prompt
    assert "agent_scoring.py" not in prompt
    assert "reports/" not in prompt
    assert ".git/" not in prompt


def test_progressive_prompt_starts_with_skill_only_and_broker_instructions(
    tmp_path: Path,
) -> None:
    from tests.evaluation.blind_agent import (
        build_progressive_agent_prompt,
        prepare_sanitized_workspace,
    )

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    case = {
        "id": "SECRET-CASE-ID",
        "request": "Compare measured and predicted nitrate concentrations.",
        "available_data": {"format": "csv", "columns": ["measured", "predicted"]},
        "expected": {"action": "render", "reason": "GOLD-ANSWER-SENTINEL"},
    }

    prompt = build_progressive_agent_prompt(destination, case)

    assert (destination / "SKILL.md").read_text(encoding="utf-8") in prompt
    assert "references/agent-protocol.md" in prompt
    assert "Request additional AxiomFig files only through" in prompt
    assert "# Agent execution protocol" not in prompt
    assert "# Figure Intent contract" not in prompt
    assert "GOLD-ANSWER-SENTINEL" not in prompt
    assert "SECRET-CASE-ID" not in prompt


@pytest.mark.parametrize(
    "path",
    [
        "../SKILL.md",
        "/private/repository/SKILL.md",
        ".git/config",
        "reports/agent/260831_agent_03.md",
        "tests/evaluation/agent_protocol_cases.yaml",
        "tests/evaluation/agent_scoring.py",
        "references/template-knowledge/*.md",
        "src/axiomfig/templates",
        "tmp/agent-benchmark/predictions.jsonl",
        "SKILL.md; python -c 'print(1)'",
    ],
)
def test_read_broker_rejects_every_non_allowlisted_route(tmp_path: Path, path: str) -> None:
    from tests.evaluation.read_broker import ProgressiveReadBroker

    destination = tmp_path / "sandbox"
    from tests.evaluation.blind_agent import prepare_sanitized_workspace

    prepare_sanitized_workspace(ROOT, destination)
    broker = ProgressiveReadBroker(destination)

    with pytest.raises(ValueError, match="read denied"):
        broker.read(path)


def test_read_broker_reads_one_allowed_file_and_records_physical_usage(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import prepare_sanitized_workspace
    from tests.evaluation.read_broker import ProgressiveReadBroker

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    log_path = tmp_path / "reads.jsonl"
    broker = ProgressiveReadBroker(destination, log_path)

    content = broker.read("references/agent-protocol.md")

    assert content.startswith("# Agent execution protocol")
    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record == {
        "path": "references/agent-protocol.md",
        "bytes": len(content.encode("utf-8")),
    }


def test_read_broker_rejects_symlink_even_when_name_matches_allowlist(tmp_path: Path) -> None:
    from tests.evaluation.read_broker import ProgressiveReadBroker

    workspace = tmp_path / "sandbox"
    (workspace / "references").mkdir(parents=True)
    secret = tmp_path / "secret.md"
    secret.write_text("gold", encoding="utf-8")
    (workspace / "references/agent-protocol.md").symlink_to(secret)

    broker = ProgressiveReadBroker(
        workspace,
        allowed_paths={"references/agent-protocol.md"},
    )

    with pytest.raises(ValueError, match="read denied"):
        broker.read("references/agent-protocol.md")


def test_read_broker_stdio_exposes_only_read_tool_and_fails_closed(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    log_path = tmp_path / "reads.jsonl"
    environment = os.environ.copy()
    environment["AXIOMFIG_BROKER_ROOT"] = str(destination)
    environment["AXIOMFIG_BROKER_LOG"] = str(log_path)
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {}},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "read", "arguments": {"path": "SKILL.md"}},
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "read", "arguments": {"path": "../secret"}},
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "shell", "arguments": {"command": "pwd"}},
        },
    ]

    completed = subprocess.run(
        [sys.executable, "-m", "tests.evaluation.read_broker"],
        input="".join(json.dumps(item) + "\n" for item in requests),
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert responses[1]["result"]["tools"] == [
        {
            "name": "read",
            "description": "Read one allowlisted AxiomFig Agent-facing file by relative path.",
            "inputSchema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        }
    ]
    assert "# AxiomFig" in responses[2]["result"]["content"][0]["text"]
    assert responses[3]["result"]["isError"] is True
    assert responses[4]["result"]["isError"] is True


def test_read_broker_stdio_accepts_explicit_root_and_log_arguments(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import prepare_sanitized_workspace

    destination = tmp_path / "sandbox"
    prepare_sanitized_workspace(ROOT, destination)
    log_path = tmp_path / "reads.jsonl"
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "read", "arguments": {"path": "SKILL.md"}},
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.evaluation.read_broker",
            "--root",
            str(destination),
            "--log",
            str(log_path),
        ],
        input=json.dumps(request) + "\n",
        cwd=ROOT,
        env={key: value for key, value in os.environ.items() if not key.startswith("AXIOMFIG_")},
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "# AxiomFig" in json.loads(completed.stdout)["result"]["content"][0]["text"]
    assert json.loads(log_path.read_text(encoding="utf-8"))["path"] == "SKILL.md"


def test_progressive_turn_parser_accepts_read_or_final_decision() -> None:
    from tests.evaluation.blind_agent import parse_progressive_turn

    assert parse_progressive_turn('{"read":"references/agent-protocol.md"}') == {
        "read": "references/agent-protocol.md"
    }
    assert parse_progressive_turn(json.dumps(_render_decision()))["action"] == "render"


@pytest.mark.parametrize(
    "payload",
    [
        '{"read":"SKILL.md","action":"render"}',
        '{"read":null}',
        '{"read":""}',
        '{"path":"SKILL.md"}',
    ],
)
def test_progressive_turn_parser_rejects_ambiguous_or_invalid_messages(payload: str) -> None:
    from tests.evaluation.blind_agent import parse_progressive_turn

    with pytest.raises(ValueError):
        parse_progressive_turn(payload)


def test_progressive_runner_reconstructs_only_same_case_reads_and_records_usage(
    tmp_path: Path,
) -> None:
    from tests.evaluation.blind_agent import run_progressive_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render, gold: GOLD-SENTINEL}
""",
        encoding="utf-8",
    )
    decision = json.dumps(_render_decision())
    fake_agent = (
        "import json,os,sys; prompt=sys.stdin.read(); "
        "assert all(name not in os.environ for name in "
        "('CODEX_APP_TOOLS_PIPE_PATH','CODEX_SESSION_ID','CODEX_THREAD_ID',"
        "'CODEX_PERMISSION_PROFILE','CODEX_MCP_NODE_PATH')); "
        "assert 'hidden-case' not in prompt; assert 'GOLD-SENTINEL' not in prompt; "
        "print("
        f"{decision!r} if '<broker-response path=\"references/agent-protocol.md\">' in prompt "
        "else json.dumps({'read':'references/agent-protocol.md'}))"
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_progressive_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", fake_agent],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (1, 0)
    assert json.loads(output.read_text(encoding="utf-8"))["id"] == "hidden-case"
    disclosure = json.loads(output.with_suffix(".disclosure.jsonl").read_text(encoding="utf-8"))
    assert disclosure["id"] == "hidden-case"
    assert disclosure["read_count"] == 1
    assert disclosure["files"] == ["references/agent-protocol.md"]
    assert disclosure["read_bytes"] > 0
    assert disclosure["agent_facing_bytes"] > disclosure["read_bytes"]
    assert disclosure["process_count"] == 2
    assert (tmp_path / "run/logs/001/turn-01.stdout").is_file()
    assert (tmp_path / "run/logs/001/turn-02.stdout").is_file()


def test_progressive_runner_returns_denial_without_exposing_host_paths(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import run_progressive_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Use an unavailable specialty plot.
    available_data: {format: csv, columns: [subject, before, after]}
    expected: {action: unsupported}
""",
        encoding="utf-8",
    )
    unsupported = {"action": "unsupported", "reason": "No registered grammar."}
    fake_agent = (
        "import json,sys; prompt=sys.stdin.read(); "
        "print("
        f"{json.dumps(unsupported)!r} if '<broker-denied>' in prompt "
        "else json.dumps({'read':'../tests/evaluation/agent_protocol_cases.yaml'}))"
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_progressive_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", fake_agent],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (1, 0)
    denial_prompt = (tmp_path / "run/logs/001/turn-02.prompt").read_text(encoding="utf-8")
    assert "<broker-denied>read denied</broker-denied>" in denial_prompt
    assert str(ROOT) not in denial_prompt
    disclosure = json.loads(output.with_suffix(".disclosure.jsonl").read_text(encoding="utf-8"))
    assert disclosure["read_count"] == 0
    assert disclosure["denied_reads"] == 1


def test_blind_agent_cli_runs_all_cases_with_progressive_disclosure(tmp_path: Path) -> None:
    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: first
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render}
  - id: second
    request: Compare measured and predicted values again.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render}
""",
        encoding="utf-8",
    )
    decision = json.dumps(_render_decision())
    output = tmp_path / "predictions.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.evaluation.blind_agent",
            "--cases",
            str(cases_path),
            "--all-cases",
            "--progressive",
            "--output",
            str(output),
            "--workspace",
            str(tmp_path / "run"),
            "--",
            sys.executable,
            "-c",
            f"print({decision!r})",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert len(output.read_text(encoding="utf-8").splitlines()) == 2
    assert (
        len(output.with_suffix(".disclosure.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    )


def test_agent_decision_parser_accepts_one_valid_render_decision() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = parse_agent_decision(json.dumps(_render_decision()))

    assert decision["template"] == "scatter/parity"
    assert decision["mapped_roles"] == {
        "observed": "measured",
        "predicted": "predicted",
    }


@pytest.mark.parametrize("payload", ["", "not json", "{}\n{}"])
def test_agent_decision_parser_rejects_missing_invalid_or_multiple_results(payload: str) -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    with pytest.raises(ValueError, match="single JSON object"):
        parse_agent_decision(payload)


def test_agent_decision_parser_rejects_unknown_action() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["action"] = "guess"

    with pytest.raises(ValueError, match="invalid action"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_unknown_template() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["template"] = "scatter.unknown"
    figure_intent = decision["figure_intent"]
    assert isinstance(figure_intent, dict)
    figure_intent["template"] = "scatter.unknown"

    with pytest.raises(ValueError, match="unknown template"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_role_mapping_that_differs_from_intent() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = _render_decision()
    decision["mapped_roles"] = {"observed": "predicted", "predicted": "measured"}

    with pytest.raises(ValueError, match="mapped_roles must match Figure Intent data"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_requires_material_clarification_question() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {"action": "clarify", "question": "", "reason": "Meaning is missing."}

    with pytest.raises(ValueError, match="question"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_candidate_render_fields_on_clarification() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        "action": "clarify",
        "template": "line.single",
        "question": "Should x map to time and y map to concentration?",
        "reason": "The variable roles are ambiguous.",
    }

    with pytest.raises(ValueError, match="unknown=.*template"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_null_or_extra_semantics_when_clarifying() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        "action": "clarify",
        "scientific_semantics": None,
        "question": "Are these differences or ratios, and what null applies?",
        "reason": "The null differs by effect type.",
    }

    with pytest.raises(ValueError, match="unknown=.*scientific_semantics"):
        parse_agent_decision(json.dumps(decision))


def test_agent_decision_parser_rejects_provisional_mapping_on_clarification() -> None:
    from tests.evaluation.blind_agent import parse_agent_decision

    decision = {
        "action": "clarify",
        "mapped_roles": {"x": "x", "y": "y"},
        "question": "Does dose order represent a trajectory?",
        "reason": "Trajectory meaning changes the template.",
    }

    with pytest.raises(ValueError, match="unknown=.*mapped_roles"):
        parse_agent_decision(json.dumps(decision))


def test_scoring_record_attaches_hidden_case_id_after_agent_response() -> None:
    from tests.evaluation.blind_agent import scoring_record

    record = scoring_record("S04-unrelated-quantities-scatter", _render_decision())

    assert record["id"] == "S04-unrelated-quantities-scatter"
    assert "question" not in record
    assert "reason" not in record


def test_blind_runner_hides_id_from_external_agent_and_attaches_it_afterward(
    tmp_path: Path,
) -> None:
    from tests.evaluation.blind_agent import run_blind_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render, template: scatter.parity, gold: GOLD-SENTINEL}
""",
        encoding="utf-8",
    )
    decision = json.dumps(_render_decision())
    fake_agent = (
        "import sys; prompt=sys.stdin.read(); "
        "assert 'hidden-case' not in prompt; assert 'GOLD-SENTINEL' not in prompt; "
        f"print({decision!r})"
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_blind_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", fake_agent],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (1, 0)
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["id"] == "hidden-case"
    assert not output.with_suffix(".failures.jsonl").read_text(encoding="utf-8")


def test_blind_runner_preserves_raw_stdout_for_parser_failures(tmp_path: Path) -> None:
    from tests.evaluation.blind_agent import run_blind_cases

    cases_path = tmp_path / "cases.yaml"
    cases_path.write_text(
        """version: 1
cases:
  - id: hidden-case
    request: Compare measured and predicted values.
    available_data: {format: csv, columns: [measured, predicted]}
    expected: {action: render}
""",
        encoding="utf-8",
    )
    output = tmp_path / "predictions.jsonl"

    passed, failed = run_blind_cases(
        ROOT,
        cases_path,
        ["hidden-case"],
        [sys.executable, "-c", "print('not-json')"],
        output,
        tmp_path / "run",
    )

    assert (passed, failed) == (0, 1)
    assert (tmp_path / "run/logs/001.stdout").read_text(encoding="utf-8") == "not-json\n"
