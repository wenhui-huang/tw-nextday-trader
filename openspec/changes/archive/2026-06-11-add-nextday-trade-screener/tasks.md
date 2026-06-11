## 1. 專案基礎

- [x] 1.1 建立 stock_analyzer.py 骨架（main() 進入點、logging 設定、台北時區時間戳）
- [x] 1.2 定義觀察清單與 SECTOR_MAP 族群對照表（記憶體／面板／AI，含 .TW/.TWO 後綴規則）

## 2. 資料擷取（stock-data-fetch）

- [x] 2.1 實作 fetch_stock_data()：yfinance 批次下載 3 個月日線，成交量換算為張
- [x] 2.2 實作單檔重試（最多 2 次、指數退避），失敗跳過並記錄 warning
- [x] 2.3 實作資料完整性檢查：交易日 < 6 或收盤價缺值者剔除並記錄

## 3. 評分與選股（stock-screening）

- [x] 3.1 實作技術指標計算：Wilder ATR(14) 百分比、前日漲跌幅、5 日均線乖離
- [x] 3.2 實作 compute_scores()：四條件子分數（連續比例制）乘權重 40/30/20/10 加總
- [x] 3.3 實作 select_top()：總分排序取前 10，同分以成交量大者優先，不足 10 檔時註記

## 4. HTML 報表（html-report）

- [x] 4.1 建立 templates/report_template.html：報表時間戳、10 檔明細表（代號、名稱、收盤、漲跌幅、成交量、四項得分、總分）
- [x] 4.2 實作 build_charts()：每檔標的近 20 日 candlestick + 成交量 Plotly 圖，內嵌 plotly.js 確保離線可開
- [x] 4.3 實作 render_report()：Jinja2 渲染輸出 output/report.html，自動建立 output/ 目錄
- [x] 4.4 實作空結果處理：0 檔時顯示「本日無符合條件標的」且程序成功結束

## 5. 驗證

- [x] 5.1 撰寫評分邏輯單元測試（純函式：各條件滿分／比例分／同分 tie-break／不足 10 檔）
- [x] 5.2 端對端執行 python stock_analyzer.py，確認 report.html 產出且瀏覽器可正常開啟圖表
