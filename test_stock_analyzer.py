"""評分邏輯單元測試：python -m unittest test_stock_analyzer -v"""

import unittest

import pandas as pd

from stock_analyzer import (
    SECTOR_MAP,
    compute_scores,
    liquidity_score,
    ma5_gap_pct,
    sector_score,
    select_top,
    technical_score,
    volatility_score,
    wilder_atr_pct,
)


def make_df(closes, volume_lots=80_000, spread=0.02):
    """以收盤價序列建構 OHLCV DataFrame（高低價以 spread 比例展開）。"""
    closes = pd.Series(closes, dtype=float)
    idx = pd.date_range("2026-05-01", periods=len(closes), freq="B")
    return pd.DataFrame(
        {
            "Open": closes.values,
            "High": closes.values * (1 + spread),
            "Low": closes.values * (1 - spread),
            "Close": closes.values,
            "Volume": [volume_lots * 1000] * len(closes),
            "VolumeLots": [float(volume_lots)] * len(closes),
        },
        index=idx,
    )


class TestSubScores(unittest.TestCase):
    def test_liquidity_full_score(self):
        self.assertEqual(liquidity_score(80_000), 1.0)
        self.assertEqual(liquidity_score(50_000), 1.0)

    def test_liquidity_proportional(self):
        self.assertAlmostEqual(liquidity_score(25_000), 0.5)

    def test_volatility_full_by_atr(self):
        self.assertEqual(volatility_score(atr_pct=5.0, change_pct=1.0), 1.0)

    def test_volatility_full_by_change(self):
        self.assertEqual(volatility_score(atr_pct=2.0, change_pct=-7.0), 1.0)

    def test_volatility_proportional_takes_max(self):
        # ATR 2%/4% = 0.5；漲跌 3%/6% = 0.5；取較高者
        self.assertAlmostEqual(volatility_score(2.0, 3.0), 0.5)
        # 漲跌幅比例較高時取漲跌幅
        self.assertAlmostEqual(volatility_score(1.0, 4.5), 0.75)

    def test_sector_score(self):
        self.assertEqual(sector_score("2330"), 1.0)  # AI 族群
        self.assertEqual(sector_score("2412"), 0.0)  # 不在對照表

    def test_technical_score_below_ma5_within_limit(self):
        self.assertEqual(technical_score(2.0), 1.0)

    def test_technical_score_above_ma5_or_too_far(self):
        self.assertEqual(technical_score(-1.0), 0.0)  # 收盤在 5MA 之上
        self.assertEqual(technical_score(5.0), 0.0)   # 乖離達上限
        self.assertEqual(technical_score(8.0), 0.0)


class TestIndicators(unittest.TestCase):
    def test_ma5_gap_positive_when_below_ma(self):
        # 收盤一路下跌，最新收盤低於 5MA -> 乖離為正
        df = make_df([100, 100, 100, 100, 100, 96])
        self.assertGreater(ma5_gap_pct(df), 0.0)

    def test_atr_pct_positive(self):
        df = make_df([100] * 20)
        self.assertGreater(wilder_atr_pct(df), 0.0)


class TestComputeScores(unittest.TestCase):
    def test_full_score_stock(self):
        # 量 8 萬張、ATR 高（spread 大）、AI 族群、收盤略低於 5MA -> 100
        code = "2330"
        self.assertEqual(SECTOR_MAP.get(code), "ai")
        df = make_df([100] * 19 + [98], volume_lots=80_000, spread=0.05)
        scores = compute_scores({code: df})
        row = scores.iloc[0]
        self.assertEqual(row["score_liquidity"], 40.0)
        self.assertEqual(row["score_volatility"], 30.0)
        self.assertEqual(row["score_sector"], 20.0)
        self.assertEqual(row["score_technical"], 10.0)
        self.assertEqual(row["total_score"], 100.0)

    def test_partial_score_stock(self):
        # 量 2.5 萬張（門檻 50%）、低波動、非族群、收盤高於 5MA -> 總分 20
        code = "2412"
        df = make_df([100, 100, 100, 100, 100, 101],
                     volume_lots=25_000, spread=0.0)
        scores = compute_scores({code: df})
        row = scores.iloc[0]
        self.assertAlmostEqual(row["score_liquidity"], 20.0)
        self.assertLess(row["score_volatility"], 10.0)
        self.assertEqual(row["score_sector"], 0.0)
        self.assertEqual(row["score_technical"], 0.0)


class TestSelectTop(unittest.TestCase):
    @staticmethod
    def make_scores(rows):
        return pd.DataFrame(
            [{"code": c, "total_score": s, "volume_lots": v} for c, s, v in rows]
        )

    def test_top_n_by_score(self):
        rows = [(f"{1000 + i}", float(i), 10_000.0) for i in range(30)]
        picks, note = select_top(self.make_scores(rows), n=10)
        self.assertEqual(len(picks), 10)
        self.assertIsNone(note)
        self.assertEqual(picks.iloc[0]["total_score"], 29.0)

    def test_tie_break_by_volume(self):
        rows = [("1111", 50.0, 10_000.0), ("2222", 50.0, 90_000.0),
                ("3333", 80.0, 5_000.0)]
        picks, _ = select_top(self.make_scores(rows), n=2)
        self.assertEqual(list(picks["code"]), ["3333", "2222"])

    def test_fewer_than_n_adds_note(self):
        rows = [(f"{1000 + i}", float(i), 1_000.0) for i in range(7)]
        picks, note = select_top(self.make_scores(rows), n=10)
        self.assertEqual(len(picks), 7)
        self.assertIsNotNone(note)
        self.assertIn("7", note)

    def test_empty_scores(self):
        picks, note = select_top(pd.DataFrame(), n=10)
        self.assertEqual(len(picks), 0)
        self.assertIsNotNone(note)


if __name__ == "__main__":
    unittest.main()
