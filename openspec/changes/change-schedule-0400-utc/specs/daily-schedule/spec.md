## MODIFIED Requirements

### Requirement: 每日定時自動執行
系統 SHALL 以 GitHub Actions 於每日 04:00 UTC（台北 12:00 盤中）自動執行 stock_analyzer.py，於 Linux runner 安裝 Python 3.13 與 requirements.txt 相依套件後產出 output/report.html。

#### Scenario: 排程觸發
- **WHEN** UTC 時間到達每日 04:00
- **THEN** workflow 自動啟動，執行分析器並產出 report.html

#### Scenario: 相依套件安裝
- **WHEN** workflow 啟動
- **THEN** runner 安裝 Python 3.13 並依 requirements.txt 安裝套件後才執行分析器
