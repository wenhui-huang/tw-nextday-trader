## Why

隔日沖交易需要在每日收盤後快速從上千檔台股中篩選出高波動、高流動性的候選標的，人工篩選耗時且容易遺漏。本專案需要一個自動化分析器，依據量化條件每日選出 10 檔隔日沖標的並產出可瀏覽的 HTML 報表，作為每日 12:00 UTC 自動化流程（GitHub Actions → GitHub Pages / LINE Notify）的核心。

## What Changes

- 新增台股資料擷取：透過 yfinance 取得上市櫃股票的日 K 線（收盤價、成交量、高低價）資料。
- 新增四條件評分選股引擎，依加權總分排序選出前 10 檔：
  - 日成交量 > 5 萬張（權重 40%）
  - ATR > 4% 或前日漲跌幅 > 6%（權重 30%）
  - 族群熱度：記憶體／面板／AI 族群（權重 20%）
  - 收盤價低於 5 日均線幅度 < 5%（權重 10%）
- 新增 HTML 報表產出：以 Jinja2 模板渲染選股結果（含個股評分明細與 Plotly 圖表），輸出至 `output/report.html`。

## Capabilities

### New Capabilities
- `stock-data-fetch`: 擷取台股日線行情資料（價格、成交量），含失敗重試與資料完整性檢查。
- `stock-screening`: 四條件加權評分選股引擎，計算各股總分並選出前 10 檔隔日沖標的。
- `html-report`: 以 Jinja2 模板將選股結果渲染為 HTML 報表（含圖表），輸出至 output/report.html。

### Modified Capabilities

（無——本專案為初始建置，無既有 spec。）

## Impact

- 新增 `stock_analyzer.py`（核心分析邏輯）。
- 新增 `templates/report_template.html`（Jinja2 模板）。
- 產出 `output/report.html`。
- 相依套件：pandas、yfinance、plotly、jinja2（已列於 requirements.txt）。
- 後續排程（.github/workflows/daily.yml）與 LINE Notify 推播屬另一個 change，不在本次範圍。
