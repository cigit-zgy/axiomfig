"""Run the 20-case frozen Skill baseline through the existing blind broker."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from tests.evaluation.blind_agent import run_progressive_cases


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--turn-timeout", type=float, default=240.0)
    parser.add_argument("agent_command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.agent_command[1:] if args.agent_command[:1] == ["--"] else args.agent_command
    case_ids = [f"{index:02d}" for index in range(1, 21)]
    manifest_path = Path(__file__).with_name("cases.yaml")
    document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    projected = {
        "version": document["version"],
        "cases": [
            {
                "id": case["id"],
                "request": case["researcher_request"],
                "available_data": case["available_data"],
            }
            for case in document["cases"]
        ],
    }
    projected_cases = args.workspace.parent / "agent-cases.yaml"
    projected_cases.parent.mkdir(parents=True, exist_ok=True)
    projected_cases.write_text(yaml.safe_dump(projected, sort_keys=False), encoding="utf-8")
    passed, failed = run_progressive_cases(
        root,
        projected_cases,
        case_ids,
        command,
        args.output,
        args.workspace,
        max_turns=args.max_turns,
        turn_timeout=args.turn_timeout,
    )
    print(f"Figure capability Skill baseline: {passed} parsed, {failed} format failures")
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
