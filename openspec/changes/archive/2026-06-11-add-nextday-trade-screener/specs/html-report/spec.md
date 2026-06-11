## ADDED Requirements

### Requirement: 產出 HTML 選股報表
系統 SHALL 以 Jinja2 模板（templates/report_template.html）將選股結果渲染為單一 HTML 檔案，輸出至 output/report.html；報表 MUST 包含報表產出時間（台北時間）、每檔標的的代號、名稱、收盤價、漲跌幅、成交量（張）、四項條件得分與加權總分。

#### Scenario: 渲染完整報表
- **WHEN** 選股引擎輸出 10 檔標的
- **THEN** 系統產出 output/report.html，內含 10 列標的明細與產出時間戳

#### Scenario: 輸出目錄不存在
- **WHEN** output/ 目錄不存在
- **THEN** 系統自動建立目錄後寫入 report.html

### Requirement: 內嵌互動圖表
報表 SHALL 為每檔入選標的內嵌 Plotly 互動圖表，呈現最近 20 個交易日的 K 線（或收盤價走勢）與成交量；圖表 MUST 以內嵌方式置於 HTML 中，離線開啟仍可顯示。

#### Scenario: 檢視個股圖表
- **WHEN** 使用者在瀏覽器開啟 report.html
- **THEN** 每檔標的顯示可互動的近 20 日走勢與成交量圖表，無需額外網路請求載入資料

### Requirement: 空結果處理
當選股結果為空（無任何候選通過資料檢查）時，系統 SHALL 仍產出報表並顯示「本日無符合條件標的」訊息，且程序以成功狀態結束。

#### Scenario: 無符合條件標的
- **WHEN** 選股結果為 0 檔
- **THEN** report.html 顯示無標的訊息與產出時間，程序回傳成功
