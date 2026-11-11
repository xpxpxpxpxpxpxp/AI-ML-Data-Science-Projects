import unittest

from geo_case import PAIRS, POST_WEEKS, PRE_WEEKS, Row, analyze, exact_p_value, generate, pair_effects


def flat_case(lift: int) -> list[Row]:
    return [Row(pair, market, week, market == "A",
                100 + (lift if market == "A" and week >= 0 else 0))
            for pair in range(PAIRS) for market in ("A", "B")
            for week in range(-PRE_WEEKS, POST_WEEKS)]


class GeoCaseTests(unittest.TestCase):
    def test_known_constant_effect(self) -> None:
        result = analyze(flat_case(10))
        self.assertEqual(result["pair_effects"], [10] * PAIRS)
        self.assertEqual(result["adjusted_weekly_orders_per_market"], 10)
        self.assertEqual(result["incremental_orders"], 10 * PAIRS * POST_WEEKS)
        self.assertEqual(result["p_value"], 2 / (2 ** PAIRS))

    def test_exact_null_and_zero_ties(self) -> None:
        result = analyze(flat_case(0))
        self.assertEqual(result["adjusted_weekly_orders_per_market"], 0)
        self.assertEqual(result["p_value"], 1)
        self.assertEqual(exact_p_value([12, 0, 0]), 1)
        self.assertEqual(exact_p_value([12, 12, 0]), 0.5)

    def test_generated_panel_is_deterministic_and_balanced(self) -> None:
        rows = generate()
        self.assertEqual(rows, generate())
        self.assertEqual(len(rows), PAIRS * 2 * (PRE_WEEKS + POST_WEEKS))
        for pair in range(PAIRS):
            assigned = {r.market for r in rows if r.pair == pair and r.treated}
            self.assertEqual(len(assigned), 1)
        self.assertTrue(all(effect > 0 for effect in pair_effects(rows)))


if __name__ == "__main__":
    unittest.main()
