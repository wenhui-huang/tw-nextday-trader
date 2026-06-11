"""台股隔日沖選股分析器。

流程：擷取觀察清單日線資料 -> 四條件加權評分 -> 選出前 10 檔 -> 渲染 HTML 報表。
執行：python stock_analyzer.py
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from jinja2 import Environment, FileSystemLoader, select_autoescape
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots

logger = logging.getLogger("stock_analyzer")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = OUTPUT_DIR / "report.html"

TAIPEI_TZ = ZoneInfo("Asia/Taipei")

# ---------------------------------------------------------------------------
# 觀察清單與族群對照表
# ---------------------------------------------------------------------------

# 族群對照表：代號 -> 族群（記憶體 / 面板 / AI）
SECTOR_MAP: dict[str, str] = {
    # 記憶體
    "2408": "memory",  # 南亞科
    "2344": "memory",  # 華邦電
    "2337": "memory",  # 旺宏
    "3006": "memory",  # 晶豪科
    "2451": "memory",  # 創見
    "4967": "memory",  # 十銓
    "8299": "memory",  # 群聯
    "3260": "memory",  # 威剛
    # 面板
    "2409": "panel",  # 友達
    "3481": "panel",  # 群創
    "6116": "panel",  # 彩晶
    "8069": "panel",  # 元太
    # AI / 伺服器供應鏈
    "2330": "ai",  # 台積電
    "2317": "ai",  # 鴻海
    "2382": "ai",  # 廣達
    "3231": "ai",  # 緯創
    "2356": "ai",  # 英業達
    "6669": "ai",  # 緯穎
    "2376": "ai",  # 技嘉
    "2377": "ai",  # 微星
    "3017": "ai",  # 奇鋐
    "2421": "ai",  # 建準
    "3661": "ai",  # 世芯-KY
    "3443": "ai",  # 創意
    "2454": "ai",  # 聯發科
    "3035": "ai",  # 智原
    "2308": "ai",  # 台達電
    "2301": "ai",  # 光寶科
    "8210": "ai",  # 勤誠
    "5274": "ai",  # 信驊
    "3529": "ai",  # 力旺
    "4966": "ai",  # 譜瑞-KY
    "3105": "ai",  # 穩懋
}

SECTOR_LABELS = {"memory": "記憶體", "panel": "面板", "ai": "AI"}

# 觀察清單：代號 -> 名稱（含族群股與一般高流動性個股）
WATCHLIST: dict[str, str] = {
    # 記憶體
    "2408": "南亞科", "2344": "華邦電", "2337": "旺宏", "3006": "晶豪科",
    "2451": "創見", "4967": "十銓", "8299": "群聯", "3260": "威剛",
    # 面板
    "2409": "友達", "3481": "群創", "6116": "彩晶", "8069": "元太",
    # AI / 伺服器
    "2330": "台積電", "2317": "鴻海", "2382": "廣達", "3231": "緯創",
    "2356": "英業達", "6669": "緯穎", "2376": "技嘉", "2377": "微星",
    "3017": "奇鋐", "2421": "建準", "3661": "世芯-KY",
    "3443": "創意", "2454": "聯發科", "3035": "智原", "2308": "台達電",
    "2301": "光寶科", "8210": "勤誠", "5274": "信驊", "3529": "力旺",
    "4966": "譜瑞-KY", "3105": "穩懋",
    # 一般高流動性
    "2303": "聯電", "2002": "中鋼", "2603": "長榮", "2609": "陽明",
    "2615": "萬海", "2618": "長榮航", "2610": "華航", "1101": "台泥",
    "1216": "統一", "2881": "富邦金", "2882": "國泰金", "2891": "中信金",
    "2886": "兆豐金", "2884": "玉山金", "2357": "華碩", "2327": "國巨",
    "2379": "瑞昱", "3034": "聯詠", "3037": "欣興", "2383": "台光電",
    "6505": "台塑化", "2412": "中華電", "3008": "大立光", "1303": "南亞",
    "1301": "台塑", "5483": "中美晶", "6488": "環球晶", "6147": "頎邦",
}

# 上櫃股票代號（yfinance 後綴 .TWO，其餘為上市 .TW）
TWO_CODES: frozenset[str] = frozenset({
    "8299", "3260", "8069", "5274", "3529", "4966", "3105",
    "5483", "6488", "6147",
})

# ---------------------------------------------------------------------------
# 評分參數
# ---------------------------------------------------------------------------

VOLUME_THRESHOLD_LOTS = 50_000   # 日成交量門檻（張）
ATR_THRESHOLD_PCT = 4.0          # ATR 佔收盤價比率門檻（%）
CHANGE_THRESHOLD_PCT = 6.0       # 前日漲跌幅門檻（%）
MA5_GAP_LIMIT_PCT = 5.0          # 低於 5 日均線的乖離上限（%）

WEIGHT_LIQUIDITY = 40
WEIGHT_VOLATILITY = 30
WEIGHT_SECTOR = 20
WEIGHT_TECHNICAL = 10

TOP_N = 10
MIN_TRADING_DAYS = 6   # 資料完整性：至少需要的交易日數
MAX_RETRIES = 2        # 單檔擷取失敗重試次數
CHART_DAYS = 20        # 圖表顯示的交易日數
FETCH_PERIOD = "3mo"   # 涵蓋 ATR(14) 與 5MA 所需歷史並留緩衝


def to_yf_ticker(code: str) -> str:
    """台股代號轉 yfinance ticker（上市 .TW / 上櫃 .TWO）。"""
    suffix = ".TWO" if code in TWO_CODES else ".TW"
    return f"{code}{suffix}"


# ---------------------------------------------------------------------------
# 資料擷取
# ---------------------------------------------------------------------------

def _extract_single(raw: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    """從 yf.download(group_by='ticker') 的結果取出單檔 OHLCV。"""
    if raw is None or raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        if ticker not in raw.columns.get_level_values(0):
            return None
        df = raw[ticker].copy()
    else:
        df = raw.copy()
    df = df.dropna(how="all")
    return df if not df.empty else None


def _validate(code: str, df: pd.DataFrame | None) -> pd.DataFrame | None:
    """資料完整性檢查：剔除收盤缺值列後需有足夠交易日，否則回傳 None。"""
    if df is None or df.empty:
        logger.warning("%s 無資料，剔除", code)
        return None
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        logger.warning("%s 缺少欄位 %s，剔除", code, required - set(df.columns))
        return None
    df = df[df["Close"].notna()]
    if len(df) < MIN_TRADING_DAYS:
        logger.warning("%s 交易日數不足（%d < %d），剔除", code, len(df), MIN_TRADING_DAYS)
        return None
    return df


def fetch_stock_data(codes: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """擷取觀察清單日線資料，回傳 代號 -> OHLCV DataFrame（成交量含「張」欄位）。

    先批次下載，缺漏者單檔重試最多 MAX_RETRIES 次（指數退避）；
    仍失敗或資料不完整者跳過，不中斷整體流程。
    """
    codes = list(codes or WATCHLIST)
    tickers = {code: to_yf_ticker(code) for code in codes}

    logger.info("批次下載 %d 檔（period=%s）...", len(tickers), FETCH_PERIOD)
    try:
        raw = yf.download(
            list(tickers.values()), period=FETCH_PERIOD,
            group_by="ticker", auto_adjust=False, progress=False, threads=True,
        )
    except Exception:
        logger.warning("批次下載失敗，改逐檔重試", exc_info=True)
        raw = None

    data: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for code, ticker in tickers.items():
        df = _extract_single(raw, ticker)
        if df is None:
            missing.append(code)
        else:
            data[code] = df

    for code in missing:
        ticker = tickers[code]
        for attempt in range(1, MAX_RETRIES + 1):
            time.sleep(2 ** (attempt - 1))  # 1s, 2s 指數退避
            try:
                raw_one = yf.download(
                    [ticker], period=FETCH_PERIOD,
                    group_by="ticker", auto_adjust=False, progress=False,
                )
                df = _extract_single(raw_one, ticker)
                if df is not None:
                    data[code] = df
                    break
            except Exception:
                logger.warning("%s 第 %d 次重試失敗", code, attempt, exc_info=True)
        else:
            logger.warning("%s 重試 %d 次後仍失敗，跳過", code, MAX_RETRIES)

    validated: dict[str, pd.DataFrame] = {}
    for code, df in data.items():
        df = _validate(code, df)
        if df is not None:
            df = df.copy()
            df["VolumeLots"] = df["Volume"] / 1000.0  # 股 -> 張
            validated[code] = df

    logger.info("有效資料 %d / %d 檔", len(validated), len(codes))
    return validated


# ---------------------------------------------------------------------------
# 技術指標
# ---------------------------------------------------------------------------

def wilder_atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    """Wilder ATR(period) 佔最新收盤價的百分比。"""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()
    return float(atr.iloc[-1] / close.iloc[-1] * 100.0)


def prev_change_pct(df: pd.DataFrame) -> float:
    """最近一個交易日的漲跌幅（%）。"""
    close = df["Close"]
    if len(close) < 2:
        return 0.0
    return float((close.iloc[-1] / close.iloc[-2] - 1.0) * 100.0)


def ma5_gap_pct(df: pd.DataFrame) -> float:
    """收盤價相對 5 日均線的乖離（%）；正值代表收盤價低於 5MA。"""
    close = df["Close"]
    ma5 = close.rolling(5).mean().iloc[-1]
    return float((ma5 - close.iloc[-1]) / ma5 * 100.0)


# ---------------------------------------------------------------------------
# 四條件評分（純函式）
# ---------------------------------------------------------------------------

def liquidity_score(volume_lots: float) -> float:
    """流動性子分數 0-1：成交量達 5 萬張為滿分，否則依比例。"""
    return min(max(volume_lots, 0.0) / VOLUME_THRESHOLD_LOTS, 1.0)


def volatility_score(atr_pct: float, change_pct: float) -> float:
    """波動性子分數 0-1：ATR% 達 4% 或前日漲跌幅達 6% 為滿分，取兩者較高比例。"""
    atr_part = min(max(atr_pct, 0.0) / ATR_THRESHOLD_PCT, 1.0)
    chg_part = min(abs(change_pct) / CHANGE_THRESHOLD_PCT, 1.0)
    return max(atr_part, chg_part)


def sector_score(code: str) -> float:
    """族群熱度子分數 0-1：屬記憶體／面板／AI 族群為 1，否則 0。"""
    return 1.0 if code in SECTOR_MAP else 0.0


def technical_score(gap_pct: float) -> float:
    """技術面子分數 0-1：收盤價低於 5MA 且乖離 < 5% 為 1，否則 0。"""
    return 1.0 if 0.0 < gap_pct < MA5_GAP_LIMIT_PCT else 0.0


def compute_scores(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """對每檔股票計算四條件加權總分（0-100），回傳評分表。"""
    rows = []
    for code, df in data.items():
        vol_lots = float(df["VolumeLots"].iloc[-1])
        atr = wilder_atr_pct(df)
        chg = prev_change_pct(df)
        gap = ma5_gap_pct(df)

        s_liq = liquidity_score(vol_lots)
        s_vol = volatility_score(atr, chg)
        s_sec = sector_score(code)
        s_tech = technical_score(gap)
        total = (
            WEIGHT_LIQUIDITY * s_liq
            + WEIGHT_VOLATILITY * s_vol
            + WEIGHT_SECTOR * s_sec
            + WEIGHT_TECHNICAL * s_tech
        )

        rows.append({
            "code": code,
            "name": WATCHLIST.get(code, code),
            "sector": SECTOR_LABELS.get(SECTOR_MAP.get(code, ""), "—"),
            "close": float(df["Close"].iloc[-1]),
            "change_pct": chg,
            "volume_lots": vol_lots,
            "atr_pct": atr,
            "ma5_gap_pct": gap,
            "score_liquidity": WEIGHT_LIQUIDITY * s_liq,
            "score_volatility": WEIGHT_VOLATILITY * s_vol,
            "score_sector": WEIGHT_SECTOR * s_sec,
            "score_technical": WEIGHT_TECHNICAL * s_tech,
            "total_score": total,
        })
    return pd.DataFrame(rows)


def select_top(scores: pd.DataFrame, n: int = TOP_N) -> tuple[pd.DataFrame, str | None]:
    """依總分排序取前 n 檔；同分以成交量大者優先。回傳 (入選表, 註記)。"""
    if scores.empty:
        return scores, "本日無符合條件標的"
    ranked = scores.sort_values(
        ["total_score", "volume_lots"], ascending=[False, False]
    ).reset_index(drop=True)
    picks = ranked.head(n)
    note = None
    if len(picks) < n:
        note = f"候選數不足：僅 {len(picks)} 檔通過資料檢查（目標 {n} 檔）"
    return picks, note


# ---------------------------------------------------------------------------
# 圖表與報表
# ---------------------------------------------------------------------------

def build_charts(picks: pd.DataFrame, data: dict[str, pd.DataFrame]) -> dict[str, str]:
    """為每檔入選標的產生近 CHART_DAYS 日 K 線＋成交量的 Plotly HTML 片段。"""
    charts: dict[str, str] = {}
    for _, row in picks.iterrows():
        code = row["code"]
        df = data[code].tail(CHART_DAYS)
        dates = [d.strftime("%m/%d") for d in df.index]

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.72, 0.28], vertical_spacing=0.04,
        )
        fig.add_trace(
            go.Candlestick(
                x=dates, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"],
                increasing_line_color="#d62728", decreasing_line_color="#2ca02c",
                name="K線", showlegend=False,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Bar(
                x=dates, y=df["VolumeLots"],
                marker_color="#7f9bb3", name="成交量(張)", showlegend=False,
            ),
            row=2, col=1,
        )
        fig.update_layout(
            height=380, margin=dict(l=40, r=20, t=10, b=20),
            xaxis_rangeslider_visible=False, template="plotly_white",
        )
        fig.update_xaxes(type="category")
        charts[code] = fig.to_html(
            full_html=False, include_plotlyjs=False,
            config={"displayModeBar": False},
        )
    return charts


def render_report(
    picks: pd.DataFrame,
    charts: dict[str, str],
    base_date: str,
    note: str | None = None,
) -> Path:
    """以 Jinja2 模板渲染報表並寫入 output/report.html。"""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report_template.html")

    pick_rows = []
    for _, row in picks.iterrows():
        item = row.to_dict()
        item["chart"] = charts.get(row["code"], "")
        pick_rows.append(item)

    html = template.render(
        generated_at=datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        base_date=base_date,
        picks=pick_rows,
        note=note,
        plotly_js=get_plotlyjs(),
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(html, encoding="utf-8")
    logger.info("報表已輸出：%s", REPORT_PATH)
    return REPORT_PATH


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    data = fetch_stock_data()

    if not data:
        logger.warning("無任何有效資料，輸出空報表")
        render_report(pd.DataFrame(), {}, base_date="—", note="本日無符合條件標的")
        return 0

    base_date = max(df.index[-1] for df in data.values()).strftime("%Y-%m-%d")
    scores = compute_scores(data)
    picks, note = select_top(scores)
    charts = build_charts(picks, data)
    render_report(picks, charts, base_date=base_date, note=note)

    logger.info(
        "完成：入選 %d 檔（基準日 %s）：%s",
        len(picks), base_date, ", ".join(picks["code"]),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
