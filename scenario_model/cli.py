from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import simulate, website_summary
from .contracts import validate


def load(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description="Run a counterfactual food-resilience scenario against a read-only coordination snapshot.")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--baseline-scenario", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--web-output", default=None)
    args = parser.parse_args()

    snapshot = load(args.snapshot)
    scenario = load(args.scenario)
    scenario.setdefault("schema", "food-resilience-scenario-definition-v0.1")
    scenario.setdefault("schema_version", "0.1.0")
    scenario.setdefault("content_type", "scenario_assumption")
    scenario.setdefault("assumptions", ["Counterfactual research scenario; not a forecast."])
    validate("snapshot", snapshot)
    validate("scenario", scenario)
    result = simulate(snapshot, scenario)
    validate("result", result)
    Path(args.output).write_text(json.dumps(result, indent=2))

    if args.web_output:
        baseline_scenario = load(args.baseline_scenario) if args.baseline_scenario else {"id": "baseline", "name": "Baseline", "description": "Unmodified network baseline.", "effects": []}
        baseline = simulate(snapshot, baseline_scenario)
        web = website_summary(baseline, result)
        validate("web_summary", web)
        Path(args.web_output).write_text(json.dumps(web, indent=2))


if __name__ == "__main__":
    main()
