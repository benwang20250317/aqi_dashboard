# AQI 儀表板：從即時監控到百萬級數據分析
這是一個全端的空氣品質儀表板專案，旨在提供一個從宏觀到微觀、從即時到歷史的完整數據監控與分析平台。
**線上 Demo 網站**: http://20.2.118.193 http://114portfolio.duckdns.org
*(請注意：此為 Azure VM，可能非永久託管)* *(請注意：網域名為免費 DNS 服務提供，可能異常，請改使用 IP連線)*

### 專業認證 (Professional Certification)
* **Information Technology Specialist (ITS) in Python**

## 主要功能 (Key Features)

#### 1. 即時戰情室 (Real-time Dashboard)
* **全台狀態分區**：將全台所有縣市依即時 AQI 平均值，自動分類至「良好」、「普通」、「不健康」燈號區，提供最宏觀的全台概覽。
* **縣市數據查詢**：可選擇任一縣市，以表格形式呈現其下所有測站的詳細即時數據。
* **互動式地理地圖 (Leaflet.js)**：點擊表格中的測站，地圖會即時聚焦。地圖上的標記顏色也與 AQI 等級同步，實現數據與地理資訊的完美結合。

#### 2. 歷史資料分析 (Historical Analysis)
* **多維度互動式篩選**：提供「分析項目」、「縣市」、「年份」等多維度篩選器，讓使用者能自由探索近 370 萬筆歷史資料。
* **動態圖表生成 (Chart.js)**：根據使用者選擇，動態生成多種分析圖表：
    * **年度地圖分佈**：將特定年份的全台各縣市平均 AQI 視覺化於地圖上。
    * **年度/季節性趨勢**：分析特定縣市的長期或季節性空氣品質變化趨勢。
    * **AQI 等級分佈**：以堆疊長條圖呈現特定縣市在某年份中，每個月的「良好/普通/不健康」天數分佈。
    * **不健康日統計**：以數據儀表卡片形式，呈現特定縣市在某年份的不健康日總數，並與前一年進行數據對比。
#### 3. 響應式網頁設計 (Responsive Web Design)
* **跨裝置體驗一致**：儀表板介面採用 Mobile-First (行動裝置優先) 的設計理念，無論在電腦、平板還是手機上，都能自動適應螢幕尺寸，提供最佳的瀏覽與操作體驗。
* **智慧佈局調整**：在手機等小螢幕上，版面會自動重新排列，將最重要的「數據查詢」與「地圖」功能優先顯示，並將次要資訊區塊進行優化佈局，確保核心功能的可及性。


## 技術棧 (Tech Stack)

* **後端 (Backend)**: Flask, Gunicorn
* **前端 (Frontend)**: HTML, CSS, JavaScript, Chart.js, Leaflet.js, **Tailwind CSS** (用於實現 Utility-First 與響應式網頁設計 RWD)
* **資料庫 (Database)**: MariaDB (MySQL), SQLAlchemy, `mysqlclient`, `mysql-connector-python`
* **腳本與自動化 (Scripts & Automation)**:
    * ETL: `requests` (API 請求), `pandas` (資料清洗)
    * 環境設定: `python-dotenv` (環境變數), `certifi` (SSL 憑證)
* **部署 (Deployment)**: Microsoft Azure VM, Ubuntu Server, Nginx (反向代理), Cron (排程任務)


## 關鍵挑戰與解決方案 (Key Challenges & Solutions)

### 挑戰一：從「失聯」到「整合」- 解決全端通訊的混亂局面
* **遇到的困境 (Situation):**
    專案初期，前端儀表板與後端 API 完全無法溝通，反覆陷入了 `404 Not Found` (找不到路徑)、`CORS` (跨域安全策略) 與部署到雲端後的 `502 Bad Gateway` 的混亂循環中，難以定位問題根源。

* **我的解決方案 (Action):**
    我意識到，根本問題在於將前後端視為兩個獨立服務的部署模型。為此，我重新設計並建立了一個專業、整合的全端架構：
    1.  **後端驅動前端**：由 Flask 統一負責 API 服務與 `index.html` 網頁的渲染 (`render_template`)，確保了所有服務來源的一致性。
    2.  **Nginx 統一入口**：在雲端伺服器上配置 Nginx 作為反向代理，將所有外部對 Port 80 的標準請求，安全地轉發給在背景運行的 Gunicorn/Flask 服務，不僅隱藏了內部複雜性，更大幅提升了安全性與效能。

* **達成的成果 (Result):**
    此架構不僅**解決了所有通訊錯誤**，更建立了一個**穩健、安全且易於維護的生產級部署模型**。

### 挑戰二：前端的「環境僵化」- 以相對路徑實現無縫遷移
* **遇到的困境 (Situation):**
    前端 `index.html` 寫死了本地開發用的 API 位址 (`http://127.0.0.1:5000`)。這導致專案一旦部署至使用標準 Port 80/443 的雲端正式環境，前端將立刻因找不到 API 而完全癱瘓。

* **我的解決方案 (Action):**
    為了解決這個部署的關鍵障礙，我讓前端程式碼變得「環境無關 (Environment Agnostic)」。我將 `index.html` 中所有對 API 的 `fetch` 請求，全部從絕對 URL 修改為**相對路徑** (例如 `/api/summary`)。這讓瀏覽器能自動向載入頁面的當前網域發送請求。

* **達成的成果 (Result):**
    這個看似微小卻至關重要的修改，讓**同一份前端程式碼無需任何變更**，即可完美運行於本地 Windows 測試站與雲端 Ubuntu 生產環境，實現了真正的「一次編寫，到處運行」。

### 挑戰三：資料庫的「信任危機」- 用 SQL 指令確立唯一事實
* **遇到的困境 (Situation):**
    專案早期，程式碼與資料庫因欄位命名不一致 (例如 `SiteId` vs `siteid`) 而頻繁發生衝突，導致整個開發流程反覆被難以追蹤的 `Unknown column` 錯誤中斷。

* **我的解決方案 (Action):**
    我採用了「資料庫優先」的原則來解決這個問題：
    1.  **以 `DESCRIBE` 指令探查真相**：我首先在資料庫中執行 `DESCRIBE air_quality_records;` 指令，讓資料庫「親口」說出其最真實的結構，結束了混亂的猜測。
    2.  **以重建代替修補**：接著，我並未修改程式碼去將就混亂的結構，而是選擇了更專業的作法——編寫 `db_rebuild.sql` 腳本，**徹底重建資料表**，並在整個專案中強制推行統一的 `PascalCase` 命名標準。

* **達成的成果 (Result):**
    此舉**從根本上消除了所有因欄位不一致引發的錯誤**，並為專案建立了一套清晰、標準化的數據庫開發流程。

### 挑戰四：資料的「即時與唯一」- 以資料庫思維取代繁瑣程式碼
* **遇到的困境 (Situation):**
    每小時執行的即時爬蟲，必須在不產生重複數據的前提下，高效地「更新」現有紀錄、「插入」最新紀錄。

* **我的解決方案 (Action):**
    我選擇了**利用資料庫本身最強大的內建機制**來保證數據的完整性，而非在 Python 中編寫複雜邏輯：
    1.  **複合主鍵 (Composite Primary Key)**：在資料表設計層面，我為 `(SiteId, DataCreationDate)` 欄位組合建立了複合主鍵，從**資料庫結構上**就根本杜絕了重複的可能性。
    2.  **冪等性指令 (Idempotent Command)**：在爬蟲腳本中，我採用了 `REPLACE INTO` 這一具有冪等性的 SQL 指令，它能自動處理「存在即更新，不存在即插入」(UPSERT) 的邏輯，程式碼極其簡潔且執行效率高。

* **達成的成果 (Result):**
    此方案**以最少的程式碼，實現了最高效、最可靠的數據同步機制**，體現了「讓專業工具做專業事」的開發哲學。

### 挑戰五：百萬級資料匯入的「靜默失敗」- 導入數據工程最佳實踐
* **遇到的困境 (Situation):**
    在匯入近 370 萬筆歷史資料時，腳本顯示成功，資料庫卻是空的——這正是最棘手的資料庫交易「靜默回滾 (Silent Rollback)」問題，由資料中隱藏的髒數據 (`"nan"` 字串) 所觸發。

* **我的解決方案 (Action):**
    我設計了一套包含**事前優化、過程控制、事後驗證**的完整數據工程流程：
    1.  **精簡化設計 (Lean Design)**：新建一張僅含 6 個核心欄位的分析專用表，從源頭優化儲存與查詢效能。
    2.  **深度清洗與轉型 (In-depth Cleaning & Transformation)**：強化 Python 清洗函式，穩健地處理各類髒數據，如將 `'nan'` 等無效字串轉為 `NULL`，並將數字字串安全地轉換為整數。
    3.  **分批處理 (Chunking)**：將一次性的巨大交易，拆分為每 1000 筆的微型交易，避免單一錯誤導致全局失敗。
    4.  **閉環驗證 (Closed-Loop Validation)**：在腳本結尾加入自動化的資料庫總筆數查詢，實現「自我驗證」，杜絕「假性成功」。

* **達成的成果 (Result):**
    透過這些數據工程實踐，不僅**成功匯入了全部 370 萬筆資料**，更建立了一個**高穩定、高容錯的 ETL (Extract, Transform, Load) 流程**。

### 挑戰六：數據的「無聲錯誤」- 確立後端 API 的守門員職責
* **遇到的困境 (Situation):**
    儀表板上出現了數據欄位時常為空 (`N/A`) 的問題，以及觀測時間永遠比真實時間快 8 小時的「幽靈時區」錯誤。

* **我的解決方案 (Action):**
    我診斷出根源在於前後端對數據格式的「認知不同」，並將所有數據格式化的責任收歸後端，將 API 打造成一個強大的「數據守門員」：
    1.  **欄位名稱標準化**：在後端 API 中建立 `COLUMN_MAPPING`，在回傳 JSON 前，將所有欄位名強制統一為 `PascalCase` 格式。
    2.  **時區問題根治**：後端 API 在回傳時間時，統一將其格式化為 **ISO 8601 標準** (`YYYY-MM-DDTHH:MM:SS`)，明確告知瀏覽器無需再做任何時區轉換。

* **達成的成果 (Result):**
    此舉建立了**清晰的前後端數據契約 (Data Contract)**，大幅提升了數據呈現的穩定性與前端開發的可靠性。

### 挑戰七：程式碼中的「機密外洩」- 導入環境變數管理
* **遇到的困境 (Situation):**
    專案中三支核心 Python 腳本的原始版本，都包含了寫死的資料庫密碼與 API 金鑰等機密資訊，存在嚴重的安全隱患與部署彈性問題。

* **我的解決方案 (Action):**
    我利用 `python-dotenv` 套件，將所有機密資訊從程式碼中抽離，統一存放於不受版本控制的 `.env` 檔案中。所有 Python 腳本現在都從這個安全的來源動態讀取設定。

* **達成的成果 (Result):**
    此舉**徹底實現了「設定與程式碼」的分離**，大幅提升了專案的安全性與可移植性，使其能輕易地在不同環境中使用不同的設定，而無需修改任何一行程式碼。

### 挑戰八：HTTPS 的「信任鏈謎團」- 深入診斷與解決 SSL 驗證失敗
* **遇到的困境 (Situation):**
    `crawler.py` 在特定網路環境下，持續地因 `[SSL: CERTIFICATE_VERIFY_FAILED]` 錯誤而失敗，即使目標網站憑證正常。

* **我的解決方案 (Action):**
    在診斷出這是由客戶端網路環境中的 SSL 攔截所導致後，我**拒絕採用 `verify=False` 這種犧牲安全性的捷徑**。我為專案引入了 `certifi` 套件，它提供了一組即時更新的根憑證庫，並在 `requests` 發出請求時，明確指定使用 `certifi` 的憑證庫進行驗證。

* **達成的成果 (Result):**
    此方案在**不犧牲任何安全性的前提下**，成功克服了由特定網路環境造成的憑證驗證問題。這個偵錯過程讓我對 HTTPS/SSL 的運作原理，以及如何診斷複雜的網路安全問題，有了遠超課程所學的深刻理解。

### 挑戰九：最棘手的「幽靈錯誤」- 偵錯 CSS 與 JS 的渲染衝突
* **遇到的困境 (Situation):**
    在專案收尾階段，出現了最詭異的錯誤：電腦版的兩個頁籤都完全沒有回應，但手機版卻一切正常。更棘手的是，瀏覽器 Console 中沒有任何錯誤訊息，且透過 `alert` 探針測試，證明了所有 JavaScript 初始化函式都已成功執行完畢。

* **我的解決方案 (Action):**
    在排除了所有常見可能性後，我將懷疑的焦點轉向了 **CSS 的渲染層**。我假設 JavaScript 成功更新了網頁元素，但 CSS 的樣式衝突導致這些元素在畫面上不可見。我的解決方案是**簡化並統一 CSS 的控制權**：
    1.  **移除衝突**：刪除了 `<style>` 區塊中與 Tailwind CSS 功能重複、可能產生衝突的 `@media` 規則。
    2.  **明確化職責**：將所有 `display` 相關的佈局控制權，完全交由 HTML 標籤上的 Tailwind class (`flex`, `lg:grid` 等) 來管理，消除了樣式來源的模糊地帶。

* **達成的成果 (Result):**
    這個 CSS 結構性調整，清除了潛在的渲染衝突，讓瀏覽器能夠正確繪製畫面，所有功能立刻恢復正常。這個經驗讓我學到：**在沒有 JavaScript 錯誤時，要勇於懷疑 CSS**，並掌握了透過簡化樣式控制來排查複雜前端錯誤的技巧。



## AQI 儀表板：Windows 本地部署安裝指南

這份文件將引導您如何在 Windows 作業系統上，從零開始部署並啟動本專案。
### 一、事前準備 (Prerequisites)

在開始之前，請確保您的系統已安裝以下軟體：

1.  **Python 3.8 或更高版本**:
    * 請至 [Python 官方網站](https://www.python.org/downloads/) 下載並安裝。
    * **重要**：在安裝過程中，請務必勾選 `Add Python to PATH` 的選項。

2.  **MariaDB (或 MySQL)**:
    * 本專案使用 MariaDB 作為資料庫，您可至 [MariaDB 官方網站](https://mariadb.org/download/) 下載。MySQL 也完全相容。
    * 安裝過程中，請記下您設定的 `root` 使用者密碼。
    * 建議安裝圖形化管理工具，如 [HeidiSQL](https://www.heidisql.com/download.php) (通常會同 MariaDB 一併安裝) 或 [DBeaver](https://dbeaver.io/download/)，方便後續操作。

3.  **專案原始碼**:
    * 請確保您已取得本專案的完整原始碼資料夾 (`aqi_dashboard/`)。

        aqi_dashboard/
        ├── .env                      # 環境變數檔案 (包含資料庫密碼、API金鑰等機敏資訊)
        ├── batch/
        │   ├── run_crawler.bat       # 批次檔：手動執行或排程執行爬蟲
        │   └── start_server.bat      # 批次檔：啟動本地 Flask 網站伺服器
        ├── database/
        │   └── initialize_database.sql # 資料庫初始化腳本 (建立 Table Schema)
        ├── history_records/
        │   └── ... (多個 .json 歷史資料檔案) # 存放原始歷史資料的 .json 檔案
        ├── scripts/
        │   ├── crawler.py          # Python 腳本：爬取並更新「即時」AQI 資料
        │   └── import_lean_data.py # Python 腳本：匯入「歷史」AQI 資料
        ├── templates/
        │   └── index.html          # 前端核心：儀表板的 HTML/CSS/JavaScript 介面
        ├── venv/                     # Python 虛擬環境資料夾
        ├── dashboard_api.py        # 後端核心：Flask 主程式 (提供 API 服務)
        ├── requirements.txt        # Python 專案所需的套件清單
        └── README.md               # 專案說明文件 (包含介紹、挑戰與安裝指南)



### 二、資料庫設定 (Database Setup)

1.  **建立資料庫與使用者**:
    * 打開您的資料庫管理工具 (如 HeidiSQL)，使用 `root` 帳號登入。
    * 執行以下 SQL 指令碼，以建立專案所需的資料庫 (`aqi_db`) 和專用使用者 (`aqi_user`)。請將 `'1234'` 替換為您自訂的安全密碼。

    ```sql
    CREATE DATABASE IF NOT EXISTS `aqi_db`
      CHARACTER SET utf8mb4
      COLLATE utf8mb4_unicode_ci;
    CREATE USER IF NOT EXISTS 'aqi_user'@'localhost'
      IDENTIFIED BY '1234';
    GRANT ALL PRIVILEGES ON `aqi_db`.* TO 'aqi_user'@'localhost';
    FLUSH PRIVILEGES;
    ```

2.  **建立資料表 (Table Schema)**:
    * 在資料庫管理工具中，選擇 `aqi_db` 資料庫。
    * 找到專案中的 `database/initialize_database.sql` 檔案，將其內容完整複製並執行。
    * 執行成功後，您會在 `aqi_db` 中看到 `air_quality_records` 和 `historical_aqi_analysis` 這兩個空的資料表。

### 三、專案環境設定 (Project Environment Setup)

1.  **設定環境變數 (`.env` 檔案)**:
    * 在專案的根目錄 (`aqi_dashboard/`) 中，建立一個名為 `.env` 的新檔案。
    * 將以下內容複製到 `.env` 檔案中，並根據您**第二步**的設定，修改對應的值（特別是 `DB_PASSWORD`）。

    ```env
    # 資料庫連線資訊
    DB_USER=aqi_user
    DB_PASSWORD=1234
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_NAME=aqi_db

    # 環境部資料平台 API 金鑰 (請自行替換個人 金鑰)
    API_KEY=12345678-2da7-4511-9d8f-123456789012
    ```

2.  **建立並設定 Python 虛擬環境**:
    * 打開 Windows 的命令提示字元 (cmd)，並切換到專案根目錄。
        ```cmd
        cd C:\路徑\到\您的\aqi_dashboard
        ```
    * **步驟 A：建立虛擬環境** (`venv` 資料夾)
        ```cmd
        python -m venv venv
        ```
    * **步驟 B：啟動虛擬環境** (您會看到路徑前方出現 `(venv)`)
        ```cmd
        .\venv\Scripts\activate
        ```
    * **步驟 C：升級 Pip (建議)**
        ```cmd
        python -m pip install --upgrade pip
        ```
    * **步驟 D：安裝所有必要的 Python 套件**
        ```cmd
        pip install -r requirements.txt
        ```

### 四、資料匯入 (Data Population)

1.  **匯入歷史資料 (執行一次即可)**:
    * 請將所有歷史資料的 `.json` 檔案，放入 `history_records/` 資料夾中。
    * 在已啟動虛擬環境的命令提示字元中，執行以下指令：
        ```cmd
        python scripts/import_lean_data.py --import
        ```
    * 程式會要求您輸入 `yes` 確認，之後便會開始匯入數百萬筆資料，請耐心等候其執行完畢。

2.  **獲取即時資料 (首次執行)**:
    * 要讓即時儀表板有初始資料，請手動執行一次爬蟲腳本。
    * 直接雙擊 `batch/run_crawler.bat` 檔案即可。

### 五、啟動與測試 (Running and Testing)

1.  **啟動網站服務**:
    * 直接雙擊 `batch/start_server.bat` 批次檔。
    * 您會看到一個命令提示字元視窗彈出，顯示 Flask 服務正在 `http://127.0.0.1:5000` 上運行。**請勿關閉此視窗**。

2.  **瀏覽網站**:
    * 打開您的網頁瀏覽器 (如 Chrome)。
    * 在網址列輸入 `http://127.0.0.1:5000` 並按下 Enter。
    * 您現在應該可以看到功能完整的 AQI 儀表板了。

### 六、(選用) 設定定時更新 (Scheduling Updates)

若要讓即時資料每小時自動更新，您可以使用 Windows 內建的「工作排程器」。

1.  打開「工作排程器」。
2.  建立新任務。
3.  在「觸發程序」中，設定為每小時觸發一次。
4.  在「動作」中，設定為「啟動程式」，並將「程式或指令碼」指向 `C:\路徑\到\您的\aqi_dashboard\batch\run_crawler.bat` 這個批次檔。
5.  儲存任務即可。

### 七、疑難排解 (Troubleshooting)

* **執行爬蟲時出現 `[SSL: CERTIFICATE_VERIFY_FAILED]` 錯誤**:
    * 這通常不是程式問題，而是您所在的網路環境（如公司、學校）設有防火牆或代理伺服器，攔截了 SSL 加密連線。
    * **解決方案**：本專案程式碼已包含 `certifi` 套件作為標準解法。若問題持續，代表攔截層級較高，需向網管索取根憑證。在標準的家庭網路或雲端主機上，此腳本可以正常執行。
