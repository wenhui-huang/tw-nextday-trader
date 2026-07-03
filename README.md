# tw-nextday-trader

台股隔日沖選股自動化：每日 04:00 UTC（台北 12:00 盤中）由 GitHub Actions 自動執行分析器，
從觀察清單中依四條件加權評分選出 10 檔隔日沖標的，產出互動式 HTML 報表並部署至 GitHub Pages。

## 專案狀態

- ✅ 選股分析器（`stock_analyzer.py`）：資料擷取 → 評分 → 選股 → 報表，已完成並有單元測試
- ✅ GitHub Actions 每日排程（04:00 UTC）＋ 手動觸發（`workflow_dispatch`）
- ✅ GitHub Pages 部署：報表以 `index.html` 發佈至 `gh-pages` 分支
- ⬜ LINE Notify 推播：規劃中，尚未實作

## 運作流程

1. **資料擷取**：透過 yfinance 抓取觀察清單（61 檔上市／上櫃股票）最近 20+ 個交易日的日 K 線，
   含失敗重試與資料完整性檢查，成交量換算為「張」。
2. **四條件加權評分**（0–100 分）：
   | 條件 | 標準 | 權重 |
   |---|---|---|
   | 流動性 | 日成交量 > 5 萬張（未達門檻依比例給分） | 40% |
   | 波動性 | 14 日 ATR 佔收盤價 > 4%，或前日漲跌幅 > 6% | 30% |
   | 族群熱度 | 屬記憶體／面板／AI 族群 | 20% |
   | 技術面 | 收盤價低於 5 日均線且乖離 < 5% | 10% |
3. **選股**：依總分由高至低取前 10 檔，同分以成交量大者優先。
4. **報表**：以 Jinja2 模板渲染自包含 HTML（含 Plotly K 線互動圖表），輸出至 `output/report.html`。
5. **部署**：workflow 將報表複製為 `index.html` 發佈至 `gh-pages`，Pages 根網址即最新報表。

## 專案結構

```
stock_analyzer.py                核心分析邏輯（擷取、評分、選股、渲染）
test_stock_analyzer.py           單元測試（評分、指標、選股邏輯）
templates/report_template.html   Jinja2 報表模板
output/report.html               產出報表（不納入版控）
.github/workflows/daily.yml      每日排程與 gh-pages 部署
openspec/                        OpenSpec 規格與變更紀錄
```

## 本機執行

```bash
pip install -r requirements.txt
python stock_analyzer.py          # 產出 output/report.html
python -m unittest test_stock_analyzer.py   # 執行測試
```

環境需求：Python 3.13。

## 排程與部署

- 排程：`.github/workflows/daily.yml`，cron `0 4 * * *`（每日 04:00 UTC = 台北 12:00 盤中）。
- 手動測試：GitHub Actions 頁面點選 Run workflow。
- 失敗處理：分析器非零結束或報表不存在時，workflow 標記失敗且不部署。
- 部署：`peaceiris/actions-gh-pages@v4` 以 `force_orphan` 發佈 `output/` 至 `gh-pages`。

## OpenSpec 紀錄

主規格（`openspec/specs/`）：

| 規格 | 內容 |
|---|---|
| `stock-data-fetch` | yfinance 日線擷取、重試、完整性檢查、張數換算 |
| `stock-screening` | 四條件加權評分與前 10 檔選股規則 |
| `html-report` | Jinja2 自包含 HTML 報表與 Plotly 圖表 |
| `daily-schedule` | 每日 04:00 UTC 排程、手動觸發、失敗可見性 |
| `pages-deploy` | gh-pages 部署與最小權限 |

已封存變更（`openspec/changes/archive/`）：

| 日期 | 變更 | 摘要 |
|---|---|---|
| 2026-06-11 | `add-nextday-trade-screener` | 建立選股分析器與 HTML 報表 |
| 2026-06-12 | `add-daily-schedule-deploy` | 新增每日 12:00 UTC 排程與 gh-pages 部署 |
| 2026-06-12 | `change-schedule-0400-utc` | 排程改為 04:00 UTC（台北盤中），同步規格 |

目前無進行中的變更。

## 待辦 / 規劃

- LINE Notify 推播每日選股結果（CLAUDE.md 專案目標之一，尚未有規格與實作）。
