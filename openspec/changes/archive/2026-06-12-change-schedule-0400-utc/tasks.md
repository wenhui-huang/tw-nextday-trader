## 1. 修改排程

- [x] 1.1 將 `.github/workflows/daily.yml` 的 cron 由 `0 12 * * *` 改為 `0 4 * * *`
- [x] 1.2 更新該行註解為「每日 04:00 UTC（台北 12:00，盤中）」

## 2. 同步文件

- [x] 2.1 更新 `CLAUDE.md` 專案目標中的「12:00 UTC」為「04:00 UTC（台灣中午12點盤中）」

## 3. 驗證

- [x] 3.1 確認 daily.yml YAML 語法正確且 cron 為 `0 4 * * *`
- [x] 3.2 從 GitHub Actions 頁面以 workflow_dispatch 手動觸發一次，確認流程仍正常產出並部署
