## Context

stock_analyzer.py 已可在本機以單一指令完成「擷取 → 評分 → 報表」（前一個 change：add-nextday-trade-screener）。本 change 加上自動化外層：GitHub Actions 每日 12:00 UTC 執行並把 output/report.html 發佈到 GitHub Pages。Repo 目前只有 main 分支，尚無 workflow 與 gh-pages 分支。

## Goals / Non-Goals

**Goals:**
- 每日 12:00 UTC 無人值守執行；失敗時 run 標記 failed（GitHub 預設會寄通知信給 repo owner）。
- 可由 workflow_dispatch 隨時手動測試。
- 報表發佈為 Pages 根網址的 index.html。

**Non-Goals:**
- LINE Notify 推播（後續 change）。
- 歷史報表保存／版本化（gh-pages 每次覆蓋，不保留歷史）。
- 台股休市日偵測（休市日跑出的報表基準日即為最近交易日，分析器已正確標示）。

## Decisions

### D1. 部署方式：peaceiris/actions-gh-pages 推送 gh-pages 分支
使用 `peaceiris/actions-gh-pages@v4` 將 `output/` 目錄發佈到 gh-pages 分支（`publish_dir: ./output`），並於部署前把 report.html 複製為 index.html。
- 替代方案：官方 `actions/deploy-pages`（Pages artifact 流程）——較新且不需 gh-pages 分支，但需在 repo 啟用「GitHub Actions」Pages 來源；使用者明確指定 gh-pages 分支，故採分支推送式。
- 權杖：內建 `GITHUB_TOKEN` 加 `permissions: contents: write`，不需額外 secrets。

### D2. 觸發：cron + workflow_dispatch
```yaml
on:
  schedule:
    - cron: "0 12 * * *"
  workflow_dispatch:
```
- 排程僅在週一至週日皆觸發（不過濾週末）：台股週末休市，但 yfinance 仍回傳最近交易日資料，報表內容正確且網站維持每日更新時間戳；過濾週末（`* * 1-5`）會因台灣國定假日仍不準確，乾脆不過濾，邏輯最簡單。
- GitHub cron 可能延遲數分鐘至數十分鐘，對日報表無影響。

### D3. 環境：ubuntu-latest + actions/setup-python@v5（Python 3.13）
- `pip install -r requirements.txt`，啟用 setup-python 內建 pip cache 加速。
- 不使用本機 venv 概念；CI 直接裝在 runner。

### D4. 失敗即中止，不部署壞產出
步驟順序天然保證：分析器非零退出 → 後續部署步驟不執行 → run 標記 failed。額外在部署前檢查 `output/report.html` 存在（防呆：分析器意外成功但無產出）。

## Risks / Trade-offs

- [yfinance 在 CI 偶發 rate limit 或網路錯誤] → 分析器已有單檔重試與跳過機制；整體失敗時 run 標 failed，隔日自動重跑，必要時可手動 workflow_dispatch 補跑。
- [gh-pages 分支首次部署前 Pages 未啟用，網站 404] → 首次部署後需在 repo Settings → Pages 選 gh-pages 分支（一次性手動設定，寫入 tasks 驗證步驟）。
- [report.html 約 4–5 MB，每日 force push gh-pages] → peaceiris action 預設 force_orphan 可用 `force_orphan: true` 保持分支單一 commit，避免 repo 體積累積。

## Open Questions

（無）
