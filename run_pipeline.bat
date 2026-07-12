@echo off
setlocal EnableExtensions

chcp 65001 >nul
title Product Import Pipeline - Main Menu
color 0B

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:MENU
cls
echo.
echo ============================================================================
echo                     Product Import Pipeline - Main Menu
echo ============================================================================
echo.
echo   [1] Run Full Product Extraction Pipeline
echo   [2] Scrape Product Links
echo   [3] Scrape Product Specifications
echo   [4] Compare Scans
echo   [5] Track Prices
echo   [6] Generate Dashboard
echo   [7] Open Product Extraction Web Panel
echo   [8] Run Import Builder (WooCommerce CSV)
echo   [9] Run Image Processing Menu
echo   [10] Open Reports Folder
echo   [0] Exit
echo.
echo ============================================================================
echo.
set /p "choice=Select an option (0-10): "

if "%choice%"=="1" goto FULL_PIPELINE
if "%choice%"=="2" goto SCRAPE_LINKS
if "%choice%"=="3" goto SCRAPE_SPECS
if "%choice%"=="4" goto COMPARE_SCANS
if "%choice%"=="5" goto TRACK_PRICES
if "%choice%"=="6" goto DASHBOARD
if "%choice%"=="7" goto WEB_PANEL
if "%choice%"=="8" goto IMPORT_BUILDER
if "%choice%"=="9" goto IMAGE_PROCESSING
if "%choice%"=="10" goto OPEN_REPORTS
if "%choice%"=="0" goto EXIT

echo.
echo Invalid choice. Please select a number from 0 to 10.
timeout /t 2 >nul
goto MENU

:FULL_PIPELINE
cls
echo.
echo ============================================================================
echo Running Full Product Extraction Pipeline
echo ============================================================================
echo.
echo This runs:
echo   1. Scrape Product Links
echo   2. Scrape Product Specifications
echo   3. Track Prices
echo   4. Generate Dashboard
echo.
pause
REM NOTE: pushd/popd kept as an extra safety net (defense in depth) even
REM though the underlying Python scripts now resolve their file paths
REM relative to the project root instead of the current working directory.
pushd product_extraction
python main.py full
popd
call :PAUSE_RETURN

:SCRAPE_LINKS
cls
echo.
echo ============================================================================
echo Scraping Product Links
echo ============================================================================
echo.
pushd product_extraction
python main.py scrape-links
popd
call :PAUSE_RETURN

:SCRAPE_SPECS
cls
echo.
echo ============================================================================
echo Scraping Product Specifications + Standardize
echo ============================================================================
echo.
pushd product_extraction
python main.py scrape-specs
python main.py standardize
popd
call :PAUSE_RETURN

:COMPARE_SCANS
cls
echo.
echo ============================================================================
echo Comparing Scans
echo ============================================================================
echo.
pushd product_extraction
python trackers\compare_scans.py
popd
call :PAUSE_RETURN

:TRACK_PRICES
cls
echo.
echo ============================================================================
echo Tracking Prices
echo ============================================================================
echo.
pushd product_extraction
python main.py track
popd
call :PAUSE_RETURN

:DASHBOARD
cls
echo.
echo ============================================================================
echo Generating Dashboard
echo ============================================================================
echo.
pushd product_extraction
python main.py dashboard
popd
call :PAUSE_RETURN

:WEB_PANEL
cls
echo.
echo ============================================================================
echo Opening Product Extraction Web Panel
echo ============================================================================
echo.
pushd product_extraction
python web_panel_interactive.py
popd
call :PAUSE_RETURN

:IMPORT_BUILDER
cls
echo.
echo ============================================================================
echo Running Import Builder (Automated)
echo ============================================================================
echo.
pushd product_extraction
python main.py import-build
popd
call :PAUSE_RETURN

:IMAGE_PROCESSING
cls
echo.
echo ============================================================================
echo Starting Image Processing Menu
echo ============================================================================
echo.
pushd image_processing
call run_menu.bat
popd
call :PAUSE_RETURN

:OPEN_REPORTS
cls
echo.
echo ============================================================================
echo Opening Reports Folder
echo ============================================================================
echo.
if exist "product_extraction\reports\outputs" (
    start "" "runtime\reports"
) else (
    echo Reports folder not found.
)
echo.
pause
goto MENU

:PAUSE_RETURN
echo.
echo ============================================================================
echo Task finished. Press any key to return to the menu...
echo ============================================================================
pause >nul
goto MENU

:EXIT
cls
echo.
echo ============================================================================
echo Exiting Product Import Pipeline
echo ============================================================================
echo.
timeout /t 2 >nul
endlocal
exit /b 0
