"""Fully synthetic paired geo experiment; Python 3.11+ standard library only."""

from __future__ import annotations

import argparse
import csv
import itertools
import random
from dataclasses import dataclass
from pathlib import Path

PAIRS = 8
PRE_WEEKS = 6
POST_WEEKS = 4
ASSIGNMENT_SEED = 0
INCREMENTAL_MEDIA_SPEND = 80_000
CONTRIBUTION_PER_ORDER = 45


@dataclass(frozen=True)
class Row:
    pair: int
    market: str
    week: int
    treated: bool
    orders: int


def generate() -> list[Row]:
    """Fix both markets' untreated paths before applying a seeded assignment."""
    rng = random.Random(ASSIGNMENT_SEED)
    treated_market = [rng.choice(("A", "B")) for _ in range(PAIRS)]
    rows = []
    for pair in range(PAIRS):
        for market in ("A", "B"):
            treated = market == treated_market[pair]
            for week in range(-PRE_WEEKS, POST_WEEKS):
                # Shared pair trend and seasonal movement cancel in paired changes.
                # Fixed intercepts cancel in pre/post differences; market-week deviations remain.
                seasonal = (0, 8, -4, 12, -7)[(week + PRE_WEEKS) % 5]
                deviation = ((pair * 7 + (0 if market == "A" else 5)
                              + (week + PRE_WEEKS) * (3 if market == "A" else 4)) % 11) - 5
                untreated = (900 + 65 * pair + (50 if market == "B" else -50)
                             + (12 + pair) * week + seasonal + deviation)
                lift = (55 + 3 * pair) if treated and week >= 0 else 0
                rows.append(Row(pair, market, week, treated, untreated + lift))
    return rows


def pair_effects(rows: list[Row]) -> list[float]:
    """Treated minus control difference of post versus pre weekly means."""
    effects = []
    for pair in range(PAIRS):
        def mean(treated: bool, post: bool) -> float:
            values = [r.orders for r in rows if r.pair == pair
                      and r.treated == treated and (r.week >= 0) == post]
            if len(values) != (POST_WEEKS if post else PRE_WEEKS):
                raise ValueError("Each pair needs one treated and one control market in every week")
            return sum(values) / len(values)
        effects.append((mean(True, True) - mean(True, False))
                       - (mean(False, True) - mean(False, False)))
    return effects


def exact_p_value(effects: list[float]) -> float:
    """Two-sided exact sign-flip test for the sharp null of zero effect."""
    if not effects:
        raise ValueError("At least one pair is required")
    observed = abs(sum(effects))
    # Integer arithmetic avoids rounding ties: each mean has denominator 12.
    scaled = [round(value * 12) for value in effects]
    if any(abs(value * 12 - scaled_value) > 1e-8
           for value, scaled_value in zip(effects, scaled)):
        raise ValueError("Effects must be multiples of 1/12 for exact comparison")
    observed_scaled = abs(sum(scaled))
    assert abs(observed * 12 - observed_scaled) < 1e-8
    extreme = sum(abs(sum(sign * value for sign, value in zip(signs, scaled)))
                  >= observed_scaled
                  for signs in itertools.product((-1, 1), repeat=len(scaled)))
    return extreme / (2 ** len(scaled))


def analyze(rows: list[Row]) -> dict[str, float | list[float] | None]:
    effects = pair_effects(rows)
    adjusted = sum(effects) / PAIRS
    post_treated = [r.orders for r in rows if r.treated and r.week >= 0]
    post_control = [r.orders for r in rows if not r.treated and r.week >= 0]
    naive = sum(post_treated) / len(post_treated) - sum(post_control) / len(post_control)
    incremental_orders = adjusted * PAIRS * POST_WEEKS
    leave_one_out = [(sum(effects) - effect) / (PAIRS - 1) for effect in effects]
    return {
        "pair_effects": effects,
        "naive_weekly_gap": naive,
        "adjusted_weekly_orders_per_market": adjusted,
        "p_value": exact_p_value(effects),
        "incremental_orders": incremental_orders,
        "incremental_contribution": incremental_orders * CONTRIBUTION_PER_ORDER,
        "net_contribution_after_media": incremental_orders * CONTRIBUTION_PER_ORDER - INCREMENTAL_MEDIA_SPEND,
        "break_even_margin": (INCREMENTAL_MEDIA_SPEND / incremental_orders
                              if incremental_orders > 0 else None),
        "leave_one_out_low": min(leave_one_out),
        "leave_one_out_high": max(leave_one_out),
    }


def write_csv(rows: list[Row], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("pair", "market", "week", "treated", "orders"))
        writer.writerows((r.pair + 1, r.market, r.week, int(r.treated), r.orders) for r in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="write the generated market-week data")
    args = parser.parse_args()
    rows = generate()
    if args.csv:
        write_csv(rows, args.csv)
    result = analyze(rows)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
