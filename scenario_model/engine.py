from __future__ import annotations

from copy import deepcopy
from collections import defaultdict


def _by_id(rows):
    return {row["id"]: row for row in rows}


def _product_maps(snapshot):
    products = _by_id(snapshot.get("products", []))
    by_code = {p["code"]: p for p in products.values()}
    return products, by_code


def apply_scenario(snapshot: dict, scenario: dict) -> dict:
    """Apply explicit counterfactual modifiers to a copy of a coordination snapshot.

    This is research modelling only. It never writes to a Food Resilience Node and
    never creates commitments or decisions.
    """
    state = deepcopy(snapshot)
    products, by_code = _product_maps(state)
    locations = _by_id(state.get("locations", []))
    orgs = _by_id(state.get("organisations", []))

    for effect in scenario.get("effects", []):
        etype = effect["type"]
        factor = float(effect.get("factor", 1.0))
        if factor < 0:
            raise ValueError("Scenario factors must be non-negative")

        if etype == "offer_quantity_factor":
            product_id = effect.get("product_id")
            if effect.get("product_code"):
                product_id = by_code[effect["product_code"]]["id"]
            for offer in state.get("offers", []):
                loc = locations.get(offer["location_id"], {})
                org = orgs.get(offer["organisation_id"], {})
                if product_id and offer["product_id"] != product_id:
                    continue
                if effect.get("region") and loc.get("region") != effect["region"]:
                    continue
                if effect.get("organisation_id") and offer["organisation_id"] != effect["organisation_id"]:
                    continue
                offer["quantity"] *= factor

        elif etype == "route_capacity_factor":
            for route in state.get("routes", []):
                origin = locations.get(route["origin_location_id"], {})
                dest = locations.get(route["destination_location_id"], {})
                if effect.get("route_id") and route["id"] != effect["route_id"]:
                    continue
                if effect.get("mode") and route.get("mode") != effect["mode"]:
                    continue
                if effect.get("origin_region") and origin.get("region") != effect["origin_region"]:
                    continue
                if effect.get("destination_region") and dest.get("region") != effect["destination_region"]:
                    continue
                route["available_capacity"] *= factor

        elif etype == "capacity_quantity_factor":
            for capacity in state.get("capacities", []):
                loc = locations.get(capacity["location_id"], {})
                if effect.get("kind") and capacity.get("kind") != effect["kind"]:
                    continue
                if effect.get("region") and loc.get("region") != effect["region"]:
                    continue
                capacity["quantity"] *= factor
        else:
            raise ValueError(f"Unsupported scenario effect type: {etype}")

    return state


def _substitution_options(snapshot, requested_product_id):
    opts = [(requested_product_id, 1.0, False)]
    for sub in snapshot.get("substitutions", []):
        if sub["requested_product_id"] == requested_product_id:
            opts.append((sub["substitute_product_id"], float(sub.get("substitute_ratio", 1.0)), True))
    return opts


def _route_for(snapshot, origin_location_id, destination_location_id, required_supply_qty):
    routes = [
        r for r in snapshot.get("routes", [])
        if r["origin_location_id"] == origin_location_id
        and r["destination_location_id"] == destination_location_id
        and r.get("status", "available") == "available"
        and float(r.get("available_capacity", 0)) > 0
    ]
    if not routes:
        return None
    routes.sort(key=lambda r: (
        -(float(r.get("available_capacity", 0))),
        float(r.get("cost_per_unit") or 0),
        float(r.get("lead_time_hours") or 0),
    ))
    return routes[0]


def simulate(snapshot: dict, scenario: dict) -> dict:
    state = apply_scenario(snapshot, scenario)
    products = _by_id(state.get("products", []))
    locations = _by_id(state.get("locations", []))
    organisations = _by_id(state.get("organisations", []))
    offers = _by_id(state.get("offers", []))
    routes = _by_id(state.get("routes", []))

    needs = sorted(state.get("needs", []), key=lambda n: (-int(n.get("priority", 0)), n["id"]))
    need_results = []
    total_demand = 0.0
    total_fulfilled = 0.0
    exact_fulfilled = 0.0
    substitute_fulfilled = 0.0
    route_constrained_needs = 0

    for need in needs:
        demand = float(need["quantity"])
        total_demand += demand
        remaining = demand
        assignments = []
        feasible_supplier_ids = set()

        candidates = []
        for product_id, ratio, is_sub in _substitution_options(state, need["product_id"]):
            for offer in offers.values():
                if offer.get("status", "open") != "open" or offer["product_id"] != product_id or float(offer["quantity"]) <= 0:
                    continue
                route = _route_for(state, offer["location_id"], need["location_id"], 0)
                if route is None:
                    continue
                max_equiv = min(float(offer["quantity"]) / ratio, float(route["available_capacity"]) / ratio)
                if max_equiv <= 0:
                    continue
                feasible_supplier_ids.add(offer["organisation_id"])
                score = (
                    10.0 if is_sub else 0.0,
                    float(route.get("cost_per_unit") or 0),
                    float(route.get("lead_time_hours") or 0),
                    -max_equiv,
                )
                candidates.append((score, offer, route, ratio, is_sub, max_equiv))

        candidates.sort(key=lambda x: x[0])
        for _, offer, route, ratio, is_sub, max_equiv in candidates:
            if remaining <= 0:
                break
            # Re-read mutable availability because previous assignments may consume it.
            offer = offers[offer["id"]]
            route = routes[route["id"]]
            max_equiv = min(float(offer["quantity"]) / ratio, float(route["available_capacity"]) / ratio)
            if max_equiv <= 0:
                continue
            q_equiv = min(remaining, max_equiv)
            supply_q = q_equiv * ratio
            offer["quantity"] -= supply_q
            route["available_capacity"] -= supply_q
            remaining -= q_equiv
            assignments.append({
                "offer_id": offer["id"],
                "supplier": organisations.get(offer["organisation_id"], {}).get("name", offer["organisation_id"]),
                "matched_product": products.get(offer["product_id"], {}).get("name", offer["product_id"]),
                "requested_equivalent_quantity": round(q_equiv, 3),
                "supply_quantity": round(supply_q, 3),
                "used_substitution": is_sub,
                "route_id": route["id"],
                "route_mode": route.get("mode"),
            })
            if is_sub:
                substitute_fulfilled += q_equiv
            else:
                exact_fulfilled += q_equiv

        fulfilled = demand - remaining
        total_fulfilled += fulfilled
        if remaining > 0 and feasible_supplier_ids:
            route_constrained_needs += 1
        need_results.append({
            "need_id": need["id"],
            "organisation": organisations.get(need["organisation_id"], {}).get("name", need["organisation_id"]),
            "product": products.get(need["product_id"], {}).get("name", need["product_id"]),
            "demand": demand,
            "fulfilled": round(fulfilled, 3),
            "shortfall": round(remaining, 3),
            "fulfilment_rate": round(fulfilled / demand, 4) if demand else 1.0,
            "feasible_supplier_count": len(feasible_supplier_ids),
            "assignments": assignments,
        })

    fulfilment_rate = total_fulfilled / total_demand if total_demand else 1.0
    return {
        "schema": "food-resilience-scenario-result-v0.1",
        "schema_version": "0.1.0",
        "model": "food-resilience-scenario-model-v0.1.1",
        "scenario": {
            "id": scenario.get("id", "unnamed"),
            "name": scenario.get("name", "Unnamed scenario"),
            "description": scenario.get("description", ""),
        },
        "interpretation_boundary": "counterfactual_research_not_operational_decision",
        "metrics": {
            "total_demand": round(total_demand, 3),
            "fulfilled": round(total_fulfilled, 3),
            "shortfall": round(total_demand - total_fulfilled, 3),
            "fulfilment_rate": round(fulfilment_rate, 4),
            "exact_product_fulfilled": round(exact_fulfilled, 3),
            "substitute_product_fulfilled": round(substitute_fulfilled, 3),
            "needs_with_shortfall": sum(1 for r in need_results if r["shortfall"] > 0),
            "route_constrained_needs": route_constrained_needs,
            "mean_feasible_supplier_count": round(sum(r["feasible_supplier_count"] for r in need_results) / len(need_results), 3) if need_results else 0,
        },
        "needs": need_results,
    }


def compare(baseline: dict, scenario_result: dict) -> dict:
    b = baseline["metrics"]
    s = scenario_result["metrics"]
    return {
        "baseline_fulfilment_rate": b["fulfilment_rate"],
        "scenario_fulfilment_rate": s["fulfilment_rate"],
        "fulfilment_rate_change": round(s["fulfilment_rate"] - b["fulfilment_rate"], 4),
        "shortfall_change": round(s["shortfall"] - b["shortfall"], 3),
        "supplier_option_change": round(s["mean_feasible_supplier_count"] - b["mean_feasible_supplier_count"], 3),
    }


def website_summary(baseline: dict, scenario_result: dict) -> dict:
    comparison = compare(baseline, scenario_result)
    rate = scenario_result["metrics"]["fulfilment_rate"]
    if rate >= 0.95:
        resilience = "strong"
    elif rate >= 0.80:
        resilience = "strained"
    else:
        resilience = "severely_strained"
    return {
        "schema": "food-resilience-web-scenario-summary-v0.1",
        "schema_version": "0.1.0",
        "source": "Food Resilience Scenario Model v0.1.1",
        "content_type": "scenario_illustration",
        "warning": "Counterfactual research output. Do not present as the current food-risk assessment or as an operational allocation.",
        "scenario": scenario_result["scenario"],
        "resilience_judgement": resilience,
        "metrics": scenario_result["metrics"],
        "comparison_to_baseline": comparison,
    }
