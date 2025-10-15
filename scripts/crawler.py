import requests
import pandas as pd
import io
import MySQLdb
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import certifi # <-- 1. 匯入 certifi 套件

# =====================================================================
# 1. 組態設定 (Configuration)
# =====================================================================

# (這部分維持不變，從 .env 載入設定)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# ... (DB_CONFIG, API_URL, API_KEY 等設定維持不變)
# --- 從環境變數讀取資料庫連線設定 ---
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT')),
    'database': os.getenv('DB_NAME'),
    'charset': 'utf8mb4'
}

# --- 從環境變數讀取 API 設定 ---
API_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_488"
API_KEY = os.getenv('API_KEY')


# =====================================================================
# 2. 核心功能函式
# =====================================================================

# (get_db_connection 函式維持不變)
def get_db_connection():
    """建立並回傳資料庫連線"""
    try:
        conn = MySQLdb.connect(**DB_CONFIG)
        return conn
    except MySQLdb.Error as e:
        print(f"資料庫連線錯誤: {e}")
        sys.exit(1)


def fetch_recent_data_from_api():
    """從 API 獲取過去 24 小時的數據"""
    print("[*] 正在從 API 獲取過去 24 小時的數據...")
    
    start_time = (datetime.now() - timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S")
    
    PARAMS = {
        "api_key": API_KEY,
        "limit": "5000",
        "sort": "datacreationdate desc",
        "format": "csv",
        "filters": f"datacreationdate,GR,{start_time}"
    }

    try:
        # v-- 2. 在 requests.get 中新增 verify=False 參數 --v
        response = requests.get(API_URL, params=PARAMS, timeout=90, verify=False)
        response.raise_for_status()
        if not response.text:
            print("[!] API 回傳內容為空。")
            return None
        
        csv_data = io.StringIO(response.text)
        df = pd.read_csv(csv_data)
        print(f"[+] 成功獲取 {len(df)} 筆原始記錄。")
        return df
    except requests.exceptions.RequestException as e:
        print(f"API 請求失敗: {e}")
        return None

# (clean_and_prepare_data 和 upsert_data_to_db 函式維持不變)
def clean_and_prepare_data(df):
    """清理 DataFrame 並將欄位名稱標準化為我們統一的 PascalCase 格式"""
    print("[*] 正在清理、轉換並標準化數據...")
    column_rename_map = {
        'siteid': 'SiteId', 'sitename': 'SiteName', 'county': 'County', 'aqi': 'AQI',
        'status': 'Status', 'datacreationdate': 'DataCreationDate', 'longitude': 'Longitude',
        'latitude': 'Latitude'
    }
    for raw_col in column_rename_map.keys():
        if raw_col not in df.columns:
            print(f"[!] 警告：API 回傳資料中缺少欄位 '{raw_col}'，將會被忽略。")
    df.rename(columns=column_rename_map, inplace=True)
    required_cols = list(column_rename_map.values())
    existing_required_cols = [col for col in required_cols if col in df.columns]
    df = df[existing_required_cols].copy()
    if 'DataCreationDate' in df.columns:
        df['DataCreationDate'] = pd.to_datetime(df['DataCreationDate'], errors='coerce')
    numeric_cols = ['AQI', 'Latitude', 'Longitude', 'SiteId']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].replace('nan', None)
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(subset=['SiteId', 'DataCreationDate'], inplace=True)
    df = df.where(pd.notnull(df), None)
    print(f"[+] 清理後剩餘 {len(df)} 筆有效記錄。")
    return df

def upsert_data_to_db(df, conn):
    """使用 REPLACE INTO 將標準化後的數據更新或插入到資料庫"""
    cursor = conn.cursor()
    sql = """
        REPLACE INTO air_quality_records 
        (SiteId, SiteName, County, AQI, Status, DataCreationDate, Latitude, Longitude) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    records_to_insert = [tuple(x) for x in df[['SiteId', 'SiteName', 'County', 'AQI', 'Status', 'DataCreationDate', 'Latitude', 'Longitude']].to_numpy()]
    try:
        cursor.executemany(sql, records_to_insert)
        conn.commit()
        print(f"[+] 成功！共 {cursor.rowcount} 筆記錄已同步至資料庫。")
    except MySQLdb.Error as e:
        print(f"資料庫寫入錯誤: {e}")
        conn.rollback()
    finally:
        cursor.close()


# =====================================================================
# 3. 主程式執行區 (維持不變)
# =====================================================================
if __name__ == "__main__":
    print(f"\n===== 開始執行 ETL 爬蟲 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) =====")
    
    raw_df = fetch_recent_data_from_api()
    
    if raw_df is not None and not raw_df.empty:
        cleaned_df = clean_and_prepare_data(raw_df)
        
        if cleaned_df is not None and not cleaned_df.empty:
            db_conn = get_db_connection()
            if db_conn:
                upsert_data_to_db(cleaned_df, db_conn)
                db_conn.close()
                print("[*] 資料庫連線已關閉。")
    
    print(f"===== ETL 爬蟲執行完畢 =====\n")