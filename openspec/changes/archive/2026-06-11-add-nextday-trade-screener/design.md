## Context

專案目前僅有 requirements.txt 與 CLAUDE.md，尚無程式碼。本 change 建立核心分析器 `stock_analyzer.py`：擷取台股日線資料 → 四條件加權評分 → 選出 10 檔 → 渲染 HTML 報表。後續會由 GitHub Actions 於每日 12:00 UTC（台北 20:00，收盤後）執行，因此程式必須可無人值守、單一指令完成，且對個股資料異常具容錯能力。

技術約束（依 CLAUDE.md）：Python 3.13、pandas、yfinance、plotly、jinja2。

## Goals / Non-Goals

**Goals:**
- 單一進入點 `python stock_analyzer.py` 完成「擷取 → 評分 → 報表」全流程。
- 評分邏輯與資料來源解耦，便於單元測試（評分函式吃 DataFrame，不直接呼叫網路）。
- 報表為單一自包含 HTML 檔，適合直接部署到 GitHub Pages。

**Non-Goals:**
- GitHub Actions 排程與 GitHub Pages 部署（另一個 change）。
- LINE Notify 推播（另一個 change）。
- 即時／盤中資料、回測框架、下單功能。
- 完整上市櫃全市場掃描的效能最佳化（first version 以靜態觀察清單為範圍）。

## Decisions

### D1. 資料來源：yfinance 批次下載
使用 `yfinance.download()` 批次抓取觀察清單（台股代號加 `.TW`／`.TWO` 後綴），`period="3mo"` 以涵蓋 ATR(14) 與 5MA 所需的歷史長度並保留緩衝。
- 替代方案：TWSE OpenAPI／FinMind——資料品質較好，但需另外處理 API key 或 rate limit；yfinance 零設定且 CLAUDE.md 已指定。
- 失敗重試：單檔最多重試 2 次（指數退避 1s/2s），仍失敗則記 warning 跳過，確保排程不中斷。

### D2. 觀察清單與族群對照表：模組內常數 dict
以 `SECTOR_MAP: dict[str, str]`（代號 → "memory" | "panel" | "ai"）加上一份一般高流動性候選清單，合併為觀察清單。
- 替代方案：外部 YAML/JSON 設定檔——彈性較高，但目前無動態更新需求，常數最簡單；之後若要讓非工程師維護再抽出成設定檔。

### D3. 評分模型：連續比例分而非二元門檻
四條件各自先算 0–1 的子分數再乘權重（40/30/20/10），加總為 0–100：
- 流動性：`min(volume_lots / 50000, 1.0)`。
- 波動性：`max(min(atr_pct / 4%, 1), min(|prev_change| / 6%, 1))`，封頂 1。
- 族群：在 SECTOR_MAP 內得 1，否則 0。
- 技術面：`0 < (MA5 - close) / MA5 < 5%` 得 1，否則 0。
- 理由：純二元門檻會造成大量同分，連續分數讓 Top 10 排序穩定；同分仍以成交量大者優先（spec 要求）。
- ATR 採 Wilder 14 日 ATR，以 `ATR / close` 轉為百分比。

### D4. 報表：Jinja2 + Plotly 內嵌
- Plotly 圖表以 `fig.to_html(full_html=False, include_plotlyjs=False)` 產生片段，模板 `<head>` 內嵌一次 plotly.js（`include_plotlyjs="inline"` 於第一張圖或直接引入 bundle），確保離線可開、單檔自包含。
- 每檔標的一張 candlestick + volume 子圖（近 20 交易日）。
- 替代方案：matplotlib 靜態圖——檔案較小但不可互動，CLAUDE.md 指定 plotly。

### D5. 模組結構：單檔 stock_analyzer.py、函式分層
```
stock_analyzer.py
├─ fetch_stock_data(tickers) -> dict[str, DataFrame]   # 網路 I/O、重試、完整性檢查
├─ compute_scores(data) -> DataFrame                   # 純函式：四條件評分
├─ select_top(scores, n=10) -> DataFrame               # 排序與 tie-break
├─ build_charts(picks, data) -> dict[str, str]         # Plotly HTML 片段
├─ render_report(picks, charts) -> None                # Jinja2 → output/report.html
└─ main()
```
- 理由：專案結構由 CLAUDE.md 指定為單一 `stock_analyzer.py`；以純函式切層保留可測試性，未來要拆模組成本低。
- 時間戳使用 `zoneinfo.ZoneInfo("Asia/Taipei")`。

## Risks / Trade-offs

- [yfinance 對台股資料延遲或缺漏（停牌、新上市）] → 完整性檢查（< 6 交易日或收盤缺值即剔除）＋重試後跳過，流程不中斷；空結果仍產出「無標的」報表。
- [yfinance 非官方 API，介面可能變動] → 資料層集中在 `fetch_stock_data` 單一函式，更換資料源只需改一處。
- [靜態觀察清單會漏掉清單外的飆股] → 接受為 v1 限制；族群對照表與清單為常數，更新成本低，後續可改為全市場掃描或外部設定檔。
- [Plotly 內嵌使 report.html 體積大（約 3–5 MB）] → 對 GitHub Pages 可接受；若超標可改 CDN 載入（犧牲離線能力）。
- [12:00 UTC 執行時 yfinance 當日資料尚未更新的時差風險] → 以「資料中最新交易日」為基準日計分並標示於報表，不假設等於今天。

## Open Questions

- 觀察清單初版規模（建議 80–150 檔高流動性個股）與族群對照表的具體成分股，實作時依市場現況填入。
