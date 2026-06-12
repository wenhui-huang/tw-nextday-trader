# 台股隔日沖分析自動化

## 專案目標
每日 04:00 UTC（台灣中午12點盤中）自動分析台股，挑選 10 檔隔日沖標的，
輸出至 GitHub Pages 並推播 LINE Notify。

## 技術堆疊
- Python 3.13, pandas, yfinance, plotly, jinja2
- GitHub Actions（排程）
- GitHub Pages（部署）
- LINE Notify（推播）

## 專案結構
- stock_analyzer.py：核心分析邏輯
- output/report.html：產出報表
- templates/report_template.html：Jinja2 模板
- .github/workflows/daily.yml：排程設定

## 選股邏輯
- 日成交量 > 5萬張（權重 40%）
- ATR > 4% 或前日漲跌 > 6%（權重 30%）
- 族群熱度：記憶體/面板/AI（權重 20%）
- 低於5日均線 < 5%（權重 10%）