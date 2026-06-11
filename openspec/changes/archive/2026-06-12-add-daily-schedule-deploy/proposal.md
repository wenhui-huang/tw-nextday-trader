## Why

選股分析器（stock_analyzer.py）已完成，但目前需要手動執行。專案目標是每日 12:00 UTC（台北 20:00，收盤後）自動產出報表並公開於 GitHub Pages，因此需要 GitHub Actions 排程與部署自動化，讓整條產線無人值守運作。

## What Changes

- 新增 `.github/workflows/daily.yml`：
  - 排程觸發：每日 12:00 UTC（cron）。
  - 手動觸發：`workflow_dispatch`，便於隨時測試。
  - 執行步驟：checkout → 安裝 Python 3.13 與 requirements.txt → 執行 `python stock_analyzer.py` → 將 `output/report.html` 部署至 `gh-pages` 分支。
- 部署產物以 `index.html` 形式發佈，使 GitHub Pages 網站根網址直接顯示最新報表。

## Capabilities

### New Capabilities
- `daily-schedule`: GitHub Actions 排程——每日 12:00 UTC 自動執行分析器，並支援 workflow_dispatch 手動觸發與失敗可見性。
- `pages-deploy`: 將產出的 report.html 部署到 gh-pages 分支供 GitHub Pages 公開存取。

### Modified Capabilities

（無——既有 stock-data-fetch / stock-screening / html-report 規格不變，僅新增自動化外層。）

## Impact

- 新增 `.github/workflows/daily.yml`。
- GitHub repo 設定：需啟用 GitHub Pages（來源 gh-pages 分支）；workflow 需 `contents: write` 權限以推送 gh-pages。
- 不影響既有程式碼；LINE Notify 推播仍屬後續另一個 change。
