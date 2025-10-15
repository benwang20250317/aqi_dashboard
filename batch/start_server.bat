@ECHO OFF
TITLE AQI Dashboard Server

:: 1. 將當前視窗的編碼模式切換為 UTF-8，解決中文亂碼問題
chcp 65001
CLS

:: 2. 自動切換到此批次檔的 "上一層" 目錄 (也就是專案根目錄)
cd /d "%~dp0..\"

ECHO ===================================================
ECHO  AQI Dashboard 啟動腳本
ECHO ===================================================
ECHO.
ECHO  目前工作目錄：%cd%
ECHO.

:: 檢查 venv 是否存在 (路徑相對於專案根目錄)
IF NOT EXIST ".\venv\Scripts\activate.bat" (
    ECHO [錯誤] 找不到虛擬環境！請確認 'venv' 資料夾是否存在於專案根目錄。
    PAUSE
    EXIT /B
)

ECHO [*] 正在啟動虛擬環境 (Virtual Environment)...
:: 使用 CALL 來執行 activate.bat
CALL .\venv\Scripts\activate

ECHO [*] 虛擬環境已啟動！
ECHO.
ECHO [*] 正在啟動 Flask 網站伺服器...
ECHO [*] 請勿關閉此視窗，關閉即代表伺服器關閉。
ECHO.

:: 執行 Flask 應用程式
python dashboard_api.py

:: 讓視窗在程式結束後暫停
PAUSE