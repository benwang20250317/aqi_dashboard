import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from sqlalchemy import create_engine, text
import pandas as pd
import logging
import sys

# --- 1. 設定與環境變數載入 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從專案根目錄的 .env 檔案載入環境變數
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- 2. 資料庫連接 ---
# 檢查必要的環境變數是否存在
required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME', 'DB_PORT']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"[*] 致命錯誤：.env 檔案中缺少必要的資料庫變數：{', '.join(missing_vars)}")
    sys.exit(1)

# 從環境變數安全地建立資料庫連線字串
DB_CONNECTION_STR = (
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

try:
    engine = create_engine(DB_CONNECTION_STR)
    logging.info("資料庫引擎建立成功。")
except Exception as e:
    logging.error(f"資料庫引擎建立失敗: {e}")
    engine = None

# --- 欄位標準化對應表 (維持不變) ---
COLUMN_MAPPING = {
    'sitename': 'SiteName', 'county': 'County', 'aqi': 'AQI', 'pollutant': 'Pollutant',
    'status': 'Status', 'so2': 'SO2', 'co': 'CO', 'o3': 'O3', 'o3_8hr': 'O3_8hr',
    'pm10': 'PM10', 'pm2.5': 'PM2_5', 'pm2_5': 'PM2_5', 'no2': 'NO2', 'nox': 'NOx',
    'no': 'NO', 'windspeed': 'WindSpeed', 'winddirec': 'WindDirec',
    'datacreationdate': 'DataCreationDate', 'unit': 'Unit', 'co_8hr': 'CO_8hr',
    'pm2.5_avg': 'PM2_5_AVG', 'pm10_avg': 'PM10_AVG', 'so2_avg': 'SO2_AVG',
    'longitude': 'Longitude', 'latitude': 'Latitude', 'siteid': 'SiteId'
}

# --- 網站首頁路由 (維持不變) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Helper Function (維持不變) ---
def execute_query(sql, params):
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)
        return df

# --- API 路由 (所有路由邏輯維持不變) ---
@app.route('/api/county-summary')
def get_county_summary():
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        WITH RankedRecords AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY SiteName ORDER BY DataCreationDate DESC) as rn
            FROM air_quality_records
        )
        SELECT County, ROUND(AVG(AQI)) as average_aqi
        FROM RankedRecords WHERE rn = 1 AND AQI IS NOT NULL GROUP BY County;
    """)
    try:
        df = execute_query(query_sql, {})
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢 county-summary 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

@app.route('/api/county-data/<string:county_name>')
def get_county_data(county_name):
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        WITH RankedRecords AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY SiteName ORDER BY DataCreationDate DESC) as rn
            FROM air_quality_records WHERE County = :county_param
        )
        SELECT * FROM RankedRecords WHERE rn = 1;
    """)
    try:
        df = execute_query(query_sql, {"county_param": county_name})
        rename_map = {col: COLUMN_MAPPING.get(col.lower(), col) for col in df.columns}
        df.rename(columns=rename_map, inplace=True)
        if 'DataCreationDate' in df.columns:
            df['DataCreationDate'] = pd.to_datetime(df['DataCreationDate']).dt.strftime('%Y-%m-%dT%H:%M:%S')
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫", "details": str(e)}), 500
        
@app.route('/api/historical/annual-trend')
def get_annual_trend():
    county = request.args.get('county')
    if not county: return jsonify({"error": "County parameter is required"}), 400
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        SELECT YEAR(DataCreationDate) as year, ROUND(AVG(AQI)) as average_aqi
        FROM historical_aqi_analysis
        WHERE County = :county_param AND AQI IS NOT NULL
        GROUP BY YEAR(DataCreationDate) ORDER BY year;
    """)
    try:
        df = execute_query(query_sql, {"county_param": county})
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢 annual-trend 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

@app.route('/api/historical/annual-map')
def get_annual_map_data():
    year = request.args.get('year')
    if not year: return jsonify({"error": "Year parameter is required"}), 400
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        SELECT County, ROUND(AVG(AQI)) as average_aqi
        FROM historical_aqi_analysis
        WHERE YEAR(DataCreationDate) = :year_param AND AQI IS NOT NULL GROUP BY County;
    """)
    try:
        df = execute_query(query_sql, {"year_param": year})
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢 annual-map 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

@app.route('/api/historical/seasonal-trend')
def get_seasonal_trend():
    county = request.args.get('county')
    if not county: return jsonify({"error": "County parameter is required"}), 400
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        SELECT MONTH(DataCreationDate) as month, ROUND(AVG(AQI)) as average_aqi
        FROM historical_aqi_analysis
        WHERE County = :county_param AND AQI IS NOT NULL
        GROUP BY MONTH(DataCreationDate) ORDER BY month;
    """)
    try:
        df = execute_query(query_sql, {"county_param": county})
        df_full_month = pd.DataFrame({'month': range(1, 13)})
        df = pd.merge(df_full_month, df, on='month', how='left').fillna(0)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢 seasonal-trend 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

@app.route('/api/historical/monthly-distribution')
def get_monthly_distribution():
    county = request.args.get('county'); year = request.args.get('year')
    if not county or not year: return jsonify({"error": "County and Year parameters are required"}), 400
    if not engine: return jsonify({"error": "資料庫未連接"}), 500
    query_sql = text("""
        SELECT month,
            SUM(CASE WHEN daily_avg_aqi <= 50 THEN 1 ELSE 0 END) as good_days,
            SUM(CASE WHEN daily_avg_aqi > 50 AND daily_avg_aqi <= 100 THEN 1 ELSE 0 END) as moderate_days,
            SUM(CASE WHEN daily_avg_aqi > 100 THEN 1 ELSE 0 END) as unhealthy_days
        FROM (
            SELECT MONTH(DataCreationDate) as month, DATE(DataCreationDate) as day, AVG(AQI) as daily_avg_aqi
            FROM historical_aqi_analysis
            WHERE County = :county_param AND YEAR(DataCreationDate) = :year_param AND AQI IS NOT NULL
            GROUP BY month, day
        ) as daily_data GROUP BY month ORDER BY month;
    """)
    try:
        df = execute_query(query_sql, {"county_param": county, "year_param": year})
        df_full_month = pd.DataFrame({'month': range(1, 13)})
        df = pd.merge(df_full_month, df, on='month', how='left').fillna(0)
        for col in ['good_days', 'moderate_days', 'unhealthy_days']:
            df[col] = df[col].astype(int)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        logging.error(f"查詢 monthly-distribution 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

@app.route('/api/historical/unhealthy-days-count')
def get_unhealthy_days_count():
    county = request.args.get('county'); year_str = request.args.get('year')
    if not county or not year_str: return jsonify({"error": "County and Year parameters are required"}), 400
    if not engine: return jsonify({"error": "資料庫未連接"}), 500

    try:
        year = int(year_str)
        previous_year = year - 1

        query_sql = text("""
            SELECT COUNT(*) as unhealthy_days_count
            FROM (
                SELECT DATE(DataCreationDate) as day, AVG(AQI) as daily_avg_aqi
                FROM historical_aqi_analysis
                WHERE County = :county_param AND YEAR(DataCreationDate) = :year_param AND AQI IS NOT NULL
                GROUP BY day
            ) as daily_data
            WHERE daily_avg_aqi > 100;
        """)
        
        current_year_df = execute_query(query_sql, {"county_param": county, "year_param": year})
        current_year_count = current_year_df.iloc[0]['unhealthy_days_count'] if not current_year_df.empty else 0

        previous_year_df = execute_query(query_sql, {"county_param": county, "year_param": previous_year})
        previous_year_count = previous_year_df.iloc[0]['unhealthy_days_count'] if not previous_year_df.empty else 0
        
        change_percentage = None
        if previous_year_count > 0:
            change_percentage = round(((current_year_count - previous_year_count) / previous_year_count) * 100, 2)

        result = {
            "current_year": year,
            "unhealthy_days": int(current_year_count),
            "previous_year": previous_year,
            "previous_unhealthy_days": int(previous_year_count),
            "change_percentage": change_percentage
        }
        return jsonify(result)

    except Exception as e:
        logging.error(f"查詢 unhealthy-days-count 時發生錯誤: {e}")
        return jsonify({"error": "無法查詢資料庫"}), 500

if __name__ == '__main__':
    # 從環境變數讀取 HOST 和 PORT，提供預設值
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(debug=True, host=host, port=port)