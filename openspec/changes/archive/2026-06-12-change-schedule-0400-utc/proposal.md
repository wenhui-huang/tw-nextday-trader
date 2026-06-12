## Why

目前排程為每日 12:00 UTC（台北 20:00，收盤後）執行。需求改為 04:00 UTC（台北中午 12:00，盤中）執行，以便在當日盤中即產出隔日沖標的清單，供使用者在收盤前提早佈局判斷。

## What Changes

- 將 `.github/workflows/daily.yml` 的 cron 由 `0 12 * * *` 改為 `0 4 * * *`（04:00 UTC = 台北 12:00 盤中）。
- 更新 workflow 內註解，反映新的觸發時間與台北對應時間。
- 同步更新 `daily-schedule` 規格中所有「12:00 UTC」描述為「04:00 UTC」。
- 同步 `CLAUDE.md` 專案目標中的「12:00 UTC」敘述。
- 不變更選股邏輯、資料抓取、報表產出、部署流程與手動觸發行為。

## Capabilities

### New Capabilities

（無）

### Modified Capabilities

- `daily-schedule`: 「每日定時自動執行」需求的觸發時間由 12:00 UTC 改為 04:00 UTC。

## Impact

- 程式碼：`.github/workflows/daily.yml`（cron 與註解）。
- 文件：`CLAUDE.md`（專案目標時間敘述）、`openspec/specs/daily-schedule/spec.md`。
- 行為影響：執行時點移至台北盤中（12:00）。此時當日尚未收盤，yfinance 取得之當日 K 線為盤中即時/未定值，可能影響選股輸入資料完整度——屬本次需求的已知取捨，詳見 design.md。
- 無相依套件、API 或部署目標變更。
