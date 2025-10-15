@ECHO OFF
TITLE AQI Real-time Data Crawler

:: 將當前視窗的編碼模式切換為 UTF-8
chcp 65001
CLS

:: 自動切換到專案根目錄
cd /d "%~dp0..\"

ECHO ===================================================
ECHO  AQI 即時資料更新腳本
ECHO ===================================================
ECHO.

:: 檢查 venv 是否存在
IF NOT EXIST ".\venv\Scripts\activate.bat" (
    ECHO [錯誤] 找不到虛擬環境！此視窗將於 5 秒後關閉。
    TIMEOUT /T 5 /NOBREAK
    EXIT /B
)

ECHO [*] 正在啟動虛擬環境...
CALL .\venv\Scripts\activate

ECHO [*] 虛擬環境已啟動！
ECHO.
ECHO [*] 正在執行即時資料爬蟲 (crawler.py)...
ECHO.

:: 執行 Python 爬蟲腳本
python scripts/crawler.py

ECHO.
ECHO [*] 爬蟲執行完畢，此視窗將於 5 秒後自動關閉...

:: 等待 5 秒
TIMEOUT /T 5 /NOBREAK

:: 自動退出
EXIT