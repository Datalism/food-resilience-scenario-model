# v0.1.1

- Adopt shared versioned JSON contracts.
- Validate snapshots, scenario definitions, full results and website summaries.
- Add explicit schema metadata without changing the counterfactual/operational boundary.

# Changelog

## v0.1.0

- Initial standalone counterfactual model, deliberately separated from the coordination Node.
- Consumes a read-only Node-compatible coordination snapshot.
- Supports offer, route and shared-capacity multiplicative shocks.
- Uses priority-ordered deterministic feasibility matching with explicit substitutions.
- Reports fulfilment, shortfall, substitution use, route constraints and supplier options.
- Emits a compact website-safe scenario-summary JSON with an explicit counterfactual warning.
- Includes baseline, route-capacity and compound-shock examples plus tests.
