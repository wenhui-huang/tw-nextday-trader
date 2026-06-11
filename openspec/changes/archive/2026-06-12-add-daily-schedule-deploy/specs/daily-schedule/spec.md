## ADDED Requirements

### Requirement: 每日定時自動執行
系統 SHALL 以 GitHub Actions 於每日 12:00 UTC 自動執行 stock_analyzer.py，於 Linux runner 安裝 Python 3.13 與 requirements.txt 相依套件後產出 output/report.html。

#### Scenario: 排程觸發
- **WHEN** UTC 時間到達每日 12:00
- **THEN** workflow 自動啟動，執行分析器並產出 report.html

#### Scenario: 相依套件安裝
- **WHEN** workflow 啟動
- **THEN** runner 安裝 Python 3.13 並依 requirements.txt 安裝套件後才執行分析器

### Requirement: 手動觸發
Workflow SHALL 支援 workflow_dispatch 手動觸發，使開發者能隨時從 GitHub Actions 頁面執行完整流程以便測試。

#### Scenario: 從 Actions 頁面手動執行
- **WHEN** 開發者在 GitHub Actions 頁面點選 Run workflow
- **THEN** workflow 立即執行與排程相同的完整流程

### Requirement: 失敗可見性
當分析器以非零狀態結束時，workflow run MUST 標記為失敗且不得部署不完整的產出。

#### Scenario: 分析器執行失敗
- **WHEN** stock_analyzer.py 以非零 exit code 結束
- **THEN** workflow run 顯示為 failed，後續部署步驟不執行
