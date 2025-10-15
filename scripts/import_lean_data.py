# =============================================================================
# AQI 精簡歷史資料匯入工具 (Ubuntu 伺服器命令列版)
#
# 使用說明:
# 在終端機中，使用以下指令來執行：
#
# 1. 第一階段 (資料檢查):
#    python import_lean_data.py --check
#
# 2. 第二階段 (資料匯入):
#    python import_lean_data.py --import
# =============================================================================

import os
import json
import logging
import decimal
import argparse
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# --- 全域設定 ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- 1. 從 .env 載入環境變數 ---
# 腳本位於 aqi_dashboard/scripts/，.env 在 aqi_dashboard/，所以往上一層找
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# --- 2. 檢查並組合資料庫連線字串 ---
required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"[*] 錯誤：.env 檔案中缺少必要的資料庫變數：{', '.join(missing_vars)}")
    sys.exit(1)

DB_CONNECTION_STR = (
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

# --- 3. 使用更穩健的方式定義路徑 ---
# 專案根目錄 (aqi_dashboard)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'history_records')
TARGET_TABLE = 'historical_aqi_analysis'

# --- 核心功能函式 (此區塊完全不變) ---

def to_numeric(value):
    """將值穩健地轉換為整數，處理 'nan' 等情況"""
    if value is None or isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.strip() == '':
            return None
        if value.lower() == 'nan':
            return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

def create_db_engine():
    """建立資料庫引擎"""
    try:
        engine = create_engine(DB_CONNECTION_STR)
        with engine.connect():
            logging.info("資料庫連接成功！")
        return engine
    except Exception as e:
        logging.error(f"資料庫連接失敗: {e}")
        return None

def read_and_clean_file_lean(file_path):
    """讀取並清洗單一 JSON 檔案，只提取核心欄位"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"讀取檔案 {os.path.basename(file_path)} 失敗: {e}")
        return [], 0

    records_data = data.get('records', data) if isinstance(data, dict) else data
    if not isinstance(records_data, list):
        return [], 0

    valid_records = []
    invalid_count = 0
    for record in records_data:
        cleaned_record = {
            'SiteId': to_numeric(record.get('siteid')),
            'SiteName': record.get('sitename'),
            'County': record.get('county'),
            'AQI': to_numeric(record.get('aqi')),
            'Status': record.get('status'),
            'DataCreationDate': record.get('datacreationdate')
        }
        
        # 核心驗證
        if cleaned_record.get('SiteId') is not None and cleaned_record.get('DataCreationDate'):
            # 再次清洗 Status, 避免 'nan' 字串
            if isinstance(cleaned_record['Status'], str) and cleaned_record['Status'].lower() == 'nan':
                cleaned_record['Status'] = None
            valid_records.append(cleaned_record)
        else:
            invalid_count += 1
            
    return valid_records, invalid_count

def insert_records_to_db(engine, records_to_insert, file_name):
    """將紀錄列表分批匯入資料庫"""
    if not records_to_insert:
        return 0
    
    CHUNK_SIZE = 5000 
    total_inserted_for_file = 0
    
    try:
        with engine.connect() as conn:
            for i in range(0, len(records_to_insert), CHUNK_SIZE):
                chunk = records_to_insert[i:i + CHUNK_SIZE]
                with conn.begin() as transaction:
                    try:
                        stmt = text(
                            f"INSERT IGNORE INTO {TARGET_TABLE} "
                            "(SiteId, SiteName, County, AQI, Status, DataCreationDate) "
                            "VALUES (:SiteId, :SiteName, :County, :AQI, :Status, :DataCreationDate)"
                        )
                        conn.execute(stmt, chunk)
                        total_inserted_for_file += len(chunk)
                    except Exception as e:
                        logging.error(f"檔案 {file_name} 的批次 {i//CHUNK_SIZE + 1} 匯入失敗: {e}")
                        transaction.rollback()
                        
            return total_inserted_for_file

    except Exception as e:
        logging.error(f"匯入檔案 {file_name} 時發生無法預期的錯誤: {e}")
        return 0

# --- 兩階段執行函式 (此區塊完全不變) ---

def run_check(json_files):
    """執行第一階段：資料檢查"""
    logging.info("--- 模式: 資料檢查 (精簡模式) ---")
    total_valid = 0
    total_invalid = 0
    for file_name in json_files:
        file_path = os.path.join(JSON_FOLDER_PATH, file_name)
        valid_records, invalid_count = read_and_clean_file_lean(file_path)
        logging.info(f"檔案 {file_name}: 找到 {len(valid_records)} 筆有效紀錄，{invalid_count} 筆無效紀錄。")
        total_valid += len(valid_records)
        total_invalid += invalid_count
    
    logging.info("="*50 + f"\n所有檔案檢查完畢！\n總計找到 {total_valid} 筆『有效』紀錄。\n總計找到 {total_invalid} 筆『無效』紀錄。\n" + "="*50)

def run_import(engine, json_files):
    """執行第二階段：資料匯入"""
    logging.info("--- 模式: 資料匯入 (精簡模式) ---")
    
    try:
        with engine.connect() as conn:
            with conn.begin() as transaction:
                logging.info(f"正在清空資料表 '{TARGET_TABLE}'...")
                conn.execute(text(f"DELETE FROM {TARGET_TABLE}"))
        logging.info("資料表已清空。")
    except Exception as e:
        logging.error(f"清空資料表失敗: {e}")
        return

    total_inserted = 0
    for file_name in json_files:
        file_path = os.path.join(JSON_FOLDER_PATH, file_name)
        valid_records, _ = read_and_clean_file_lean(file_path)
        inserted_count = insert_records_to_db(engine, valid_records, file_name)
        logging.info(f"檔案 {file_name}: 腳本嘗試匯入 {inserted_count} / {len(valid_records)} 筆紀錄。")
        total_inserted += inserted_count
        
    # --- 最終驗證 ---
    logging.info("="*50)
    logging.info(f"腳本記錄的總匯入筆數為: {total_inserted}")
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {TARGET_TABLE}"))
            final_count = result.scalar_one()
            logging.info(f"資料庫回報: '{TARGET_TABLE}' 中目前共有 {final_count} 筆紀錄。")
            if final_count == total_inserted:
                logging.info(">>> 驗證成功！腳本紀錄與資料庫紀錄一致。")
            else:
                logging.warning(">>> 警告！腳本紀錄與資料庫紀錄不一致！")
    except Exception as e:
        logging.error(f"最終驗證失敗: {e}")
    logging.info("="*50)

# --- 主程式執行區 (此區塊完全不變) ---
def main():
    """主執行函式，處理命令列參數"""
    parser = argparse.ArgumentParser(description='AQI 精簡歷史資料匯入工具 (兩階段模式)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='第一階段：僅檢查與驗證資料，不寫入資料庫。')
    group.add_argument('--import', dest='run_import', action='store_true', help='第二階段：將資料實際匯入資料庫。')
    
    args = parser.parse_args()

    if not os.path.isdir(JSON_FOLDER_PATH):
        logging.error(f"找不到指定的資料夾: '{JSON_FOLDER_PATH}'")
        return

    json_files = [f for f in os.listdir(JSON_FOLDER_PATH) if f.endswith('.json')]
    if not json_files:
        logging.warning(f"在 '{JSON_FOLDER_PATH}' 資料夾中找不到任何 .json 檔案。")
        return
    
    if args.check:
        run_check(json_files)
    elif args.run_import:
        user_input = input(f"警告：即將清空資料表 '{TARGET_TABLE}' 並重新匯入所有資料！\n確定要繼續嗎？ (請輸入 yes 確認): ")
        if user_input.lower() != 'yes':
            logging.info("操作已取消。")
            return
            
        engine = create_db_engine()
        if not engine: return
        run_import(engine, json_files)

if __name__ == '__main__':
    main()