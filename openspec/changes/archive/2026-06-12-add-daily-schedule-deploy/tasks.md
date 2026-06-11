## 1. Workflow（daily-schedule）

- [x] 1.1 建立 .github/workflows/daily.yml：cron "0 12 * * *" 與 workflow_dispatch 觸發、permissions contents: write
- [x] 1.2 加入執行步驟：checkout → setup-python 3.13（含 pip cache）→ pip install -r requirements.txt → python stock_analyzer.py

## 2. 部署（pages-deploy）

- [x] 2.1 加入部署前防呆：檢查 output/report.html 存在，並複製為 output/index.html
- [x] 2.2 加入 peaceiris/actions-gh-pages@v4 部署步驟：publish_dir ./output、force_orphan true、使用 GITHUB_TOKEN

## 3. 驗證

- [x] 3.1 本機驗證 workflow YAML 語法（yaml 解析或 actionlint）
- [x] 3.2 推送後以 workflow_dispatch 手動觸發一次，確認 run 成功且 gh-pages 分支含 index.html
- [x] 3.3 確認 repo Settings → Pages 來源設為 gh-pages 分支，網站根網址顯示最新報表
