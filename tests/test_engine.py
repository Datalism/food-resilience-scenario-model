import json
from pathlib import Path

from scenario_model.engine import simulate, website_summary
from scenario_model.contracts import validate

ROOT = Path(__file__).parents[1]
snapshot = json.loads((ROOT / "examples/swedish_network.json").read_text())
baseline_scenario = json.loads((ROOT / "examples/scenarios/baseline.json").read_text())
shock_scenario = json.loads((ROOT / "examples/scenarios/compound_supply_route_shock.json").read_text())


def test_baseline_fulfils_all_needs():
    result = simulate(snapshot, baseline_scenario)
    assert result["metrics"]["fulfilment_rate"] == 1.0
    assert result["metrics"]["shortfall"] == 0
    assert result["interpretation_boundary"] == "counterfactual_research_not_operational_decision"


def test_compound_shock_reduces_fulfilment():
    baseline = simulate(snapshot, baseline_scenario)
    shocked = simulate(snapshot, shock_scenario)
    assert shocked["metrics"]["fulfilment_rate"] < baseline["metrics"]["fulfilment_rate"]
    assert shocked["metrics"]["shortfall"] > 0


def test_web_summary_is_explicitly_not_current_risk_assessment():
    baseline = simulate(snapshot, baseline_scenario)
    shocked = simulate(snapshot, shock_scenario)
    web = website_summary(baseline, shocked)
    assert web["content_type"] == "scenario_illustration"
    assert "Do not present as the current food-risk assessment" in web["warning"]


def test_shared_contracts_validate_inputs_and_outputs():
    validate("snapshot", snapshot)
    validate("scenario", shock_scenario)
    result = simulate(snapshot, shock_scenario)
    validate("result", result)
    baseline = simulate(snapshot, baseline_scenario)
    validate("web_summary", website_summary(baseline, result))
