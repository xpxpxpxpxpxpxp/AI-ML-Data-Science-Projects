"""Render the fully synthetic exhibit: python render.py"""

import itertools
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from geo_case import analyze, generate


def main() -> None:
    result = analyze(generate())
    effects = result["pair_effects"]
    observed = result["adjusted_weekly_orders_per_market"]
    null = [sum(sign * effect for sign, effect in zip(signs, effects)) / len(effects)
            for signs in itertools.product((-1, 1), repeat=len(effects))]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, (left, right) = plt.subplots(1, 2, figsize=(12.8, 5.4), dpi=180,
                                      gridspec_kw={"width_ratios": [1, 1.15]})
    fig.patch.set_facecolor("#FAFAF7")
    for ax in (left, right):
        ax.set_facecolor("#FAFAF7")
        ax.grid(axis="x", alpha=.22)
        ax.set_axisbelow(True)

    y = list(range(len(effects)))
    left.barh(y, effects, color="#247B75", height=.64)
    left.set_yticks(y, [f"Pair {i + 1}" for i in y])
    left.invert_yaxis()
    left.axvline(observed, color="#C45334", linewidth=2, linestyle="--")
    left.set_xlim(0, 90)
    left.set_xlabel("Paired change in orders / market / week")
    left.set_title("Every pair has a positive adjusted change", loc="left", pad=14,
                   fontsize=12, fontweight="bold")
    left.text(observed + 2, 7.45, f"Mean {observed:.1f}", color="#A43F25", fontsize=10)

    right.hist(null, bins=31, range=(-90, 90), color="#90AAA5", edgecolor="#FAFAF7")
    right.axvline(observed, color="#C45334", linewidth=2.5)
    right.axvline(-observed, color="#C45334", linewidth=2.5)
    right.set_xlabel("Mean paired change under assignment flips")
    right.set_ylabel("Number of assignments")
    right.set_title("Exact assignment test under zero effect", loc="left", pad=14,
                    fontsize=12, fontweight="bold")
    right.annotate("Observed", xy=(observed, 2), xytext=(33, 27),
                   arrowprops={"arrowstyle": "->", "color": "#A43F25"},
                   color="#A43F25", fontsize=10)
    extreme = round(result["p_value"] * len(null))
    right.text(.03, .94,
               f"{extreme} of {len(null)} assignments as extreme\nTwo-sided p = {result['p_value']:.4f}",
               transform=right.transAxes, va="top", fontsize=10,
               bbox={"facecolor": "white", "edgecolor": "#CBD5D2", "boxstyle": "round,pad=.5"})

    fig.suptitle("Can incremental orders pay for incremental media?", x=.06, y=.99,
                 ha="left", fontsize=18, fontweight="bold", color="#173A3A")
    fig.text(.06, .015,
             "Fictional deterministic data · 8 randomized pairs · 6 pre + 4 campaign weeks · p tests the sharp null",
             color="#52605E", fontsize=10)
    fig.tight_layout(rect=(0, .06, 1, .91), w_pad=3.2)
    output = Path(__file__).with_name("geo_inference.png")
    fig.savefig(output, dpi=180, facecolor=fig.get_facecolor())
    print(output)


if __name__ == "__main__":
    main()
