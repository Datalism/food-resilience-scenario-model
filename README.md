# Food Resilience Scenario Model v0.1.1

**Status: research / counterfactual modelling tool. Separate from the Food Resilience Node coordination software.**

This package tests how a described food-coordination network behaves under explicit hypothetical shocks. It does **not** coordinate real organisations, publish offers, reserve capacity, commit stock or exercise emergency authority.

The separation is deliberate:

- **Food Resilience Node v0.2.1** = coordination software for real offers, needs, routes, capacities, recommendations and human decisions.
- **Scenario Model v0.1.1** = research software for counterfactual questions such as “what happens if route capacity falls by 60%?”

The model consumes the Node's read-only `/coordination/snapshot` schema, or a compatible synthetic snapshot. It copies that state, applies scenario modifiers, and runs a deterministic priority-ordered feasibility calculation. No changes are written back to the Node.

## v0.1 scope

Supported shock modifiers:

- offer quantity factor
- route capacity factor
- shared capacity quantity factor

Current metrics:

- demand fulfilled / shortfall
- fulfilment rate
- exact-product vs substitute-product fulfilment
- needs with shortfall
- route-constrained needs
- mean feasible supplier count

This is deliberately a small first model. It does not forecast crops, prices or conflict, and it does not claim to simulate the entire food system.

## Website use

The CLI can emit a compact `food-resilience-web-scenario-summary-v0.1` JSON object. This is intended for a clearly labelled **scenario illustration** panel on the website. It must remain separate from the evidence-led current risk assessment.

## Run

```bash
python -m scenario_model.cli \
  --snapshot examples/swedish_network.json \
  --scenario examples/scenarios/route_capacity_shock.json \
  --output outputs/route_capacity_shock.json \
  --web-output outputs/route_capacity_shock.web.json
```

## Scientific / governance boundary

Scenario outputs are counterfactual model results. They are not forecasts and are not operational recommendations. The model never performs Food Resilience Node decisions.

## Shared contracts

The model validates its Node snapshot input, scenario definition, full result and website summary against the versioned JSON Schemas in `contracts/`. The website summary remains explicitly counterfactual.


## Limitations and validation status

This is an early research model. Results depend on the supplied network state, explicit shock assumptions and the current deterministic feasibility logic. Outputs have not been empirically validated as forecasts of real regional food availability or as proof that a particular coordination architecture improves food security. Comparative scenarios and appropriate benchmarks are future validation work.

## Licence

Licensed under the Apache License 2.0. See `LICENSE`. The licence applies to this software package; it does not license the accompanying Digital Crossroads report or third-party materials.
