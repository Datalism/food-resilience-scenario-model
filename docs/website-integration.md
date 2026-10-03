# Website integration boundary

The scenario model can emit `food-resilience-web-scenario-summary-v0.1` JSON for a website panel.

It should appear under a label such as **Scenario explorer** or **What-if resilience test**, not inside the current global-risk judgement.

Keep two data streams separate:

1. **Current assessment** — evidence-led monitoring based on FAO, WMO, JRC, WFP and other sources.
2. **Scenario illustration** — counterfactual output from this model using explicit assumptions.

The JSON contains `content_type: scenario_illustration` and a warning field specifically to preserve that distinction in presentation code.

The canonical website contracts for current assessment, indicators and regional views live in the separate **Food Resilience Shared Data Contracts v0.1** package. Scenario output must never be coerced into those current-state schemas.
