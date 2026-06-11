# pages-deploy

## Purpose

將分析器產出的 report.html 部署至 gh-pages 分支，使 GitHub Pages 網站根網址公開顯示最新報表。

## Requirements

### Requirement: 部署報表至 gh-pages 分支
Workflow SHALL 在分析器成功產出後，將 output/report.html 以 index.html 發佈至 gh-pages 分支，使 GitHub Pages 網站根網址直接顯示最新報表。

#### Scenario: 成功部署
- **WHEN** 分析器成功產出 output/report.html
- **THEN** workflow 將其發佈為 gh-pages 分支的 index.html，Pages 網站根網址顯示最新報表

#### Scenario: 重複部署覆蓋舊報表
- **WHEN** 隔日 workflow 再次執行並部署
- **THEN** gh-pages 上的 index.html 被最新報表取代，網站顯示新內容

### Requirement: 部署權限最小化
Workflow MUST 以 GITHUB_TOKEN 完成 gh-pages 推送，僅授予 contents: write 權限，不得要求額外的個人存取權杖。

#### Scenario: 使用內建權杖部署
- **WHEN** workflow 執行部署步驟
- **THEN** 以 GITHUB_TOKEN（contents: write）推送 gh-pages，無需設定額外 secrets
