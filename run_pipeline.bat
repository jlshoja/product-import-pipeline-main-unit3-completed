@echo off
setlocal EnableExtensions

chcp 65001 >nul
title Product Import Pipeline - Main Menu
color 0B

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

REM ============================================================================
REM GLOBAL SETTINGS (can be overridden via command line args)
REM Usage: run_pipeline.bat [--timeout SECONDS] [--retries COUNT] [--no-resume] [--mode MODE]
REM ============================================================================

set "DEFAULT_TIMEOUT=3600"
set "DEFAULT_RETRIES=1"
set "DEFAULT_RESUME=1"
set "DEFAULT_MODE=auto"

set "TIMEOUT=%DEFAULT_TIMEOUT%"
set "RETRIES=%DEFAULT_RETRIES%"
set "RESUME=%DEFAULT_RESUME%"
set "MODE=%DEFAULT_MODE%"

REM Parse global args
:PARSE_GLOBAL_ARGS
if "%~1"=="" goto SHOW_MENU
if /I "%~1"=="--timeout" (
    set "TIMEOUT=%~2"
    shift & shift
    goto PARSE_GLOBAL_ARGS
)
if /I "%~1"=="--retries" (
    set "RETRIES=%~2"
    shift & shift
    goto PARSE_GLOBAL_ARGS
)
if /I "%~1"=="--no-resume" (
    set "RESUME=0"
    shift
    goto PARSE_GLOBAL_ARGS
)
if /I "%~1"=="--mode" (
    set "MODE=%~2"
    shift & shift
    goto PARSE_GLOBAL_ARGS
)
shift
goto PARSE_GLOBAL_ARGS

:SET_GLOBAL_ENV
set "PROCESS_TIMEOUT=%TIMEOUT%"
set "PROCESS_SUBPROCESS_RETRY=%RETRIES%"
if "%RESUME%"=="1" (
    set "AUTO_RESUME=1"
) else (
    set "AUTO_RESUME=0"
)

:SHOW_MENU
cls
echo.
echo ============================================================================
echo                     Product Import Pipeline - Main Menu
echo ============================================================================
echo.
echo   Global Settings:  Timeout=%TIMEOUT%s  Retries=%RETRIES%  Resume=%RESUME%  Auto-Mode=%MODE%
echo.
echo   ----- Pipeline Commands -----
echo   [1]  Run Automatic Pipeline (auto)      --mode %MODE%       ^(default: first=full, then=incremental^)
echo   [2]  Run Full Pipeline (full)           --mode full         ^(always reprocess everything^)
echo   [3]  Run Incremental Pipeline           --mode incremental  ^(only new/changed products^)
echo.
echo   ----- Individual Steps -----
echo   [4]  Scrape Product Links
echo   [5]  Scrape Product Specifications
echo   [6]  Standardize Data
echo   [7]  Change Detection (Compare Scans)
echo   [8]  Image Processing (Download + Process)
echo   [9]  Import Builder (WooCommerce CSV)
echo.
echo   ----- Utilities -----
echo   [10] Track Prices
echo   [11] Generate Dashboard
echo   [12] Run Unit Tests
echo   [13] Open Web Panel
echo   [14] Open Reports Folder
echo.
echo   ----- Settings -----
echo   [S]  Change Global Settings
echo.
echo   [0]  Exit
echo.
echo ============================================================================
echo.
set /p "choice=Select an option (0-14, S): "

if /I "%choice%"=="1" goto RUN_AUTO
if /I "%choice%"=="2" goto RUN_FULL
if /I "%choice%"=="3" goto RUN_INCREMENTAL
if "%choice%"=="4" goto SCRAPE_LINKS
if "%choice%"=="5" goto SCRAPE_SPECS
if "%choice%"=="6" goto STANDARDIZE
if "%choice%"=="7" goto COMPARE_SCANS
if "%choice%"=="8" goto IMAGE_PROCESSING
if "%choice%"=="9" goto IMPORT_BUILDER
if "%choice%"=="10" goto TRACK_PRICES
if "%choice%"=="11" goto DASHBOARD
if "%choice%"=="12" goto RUN_TESTS
if "%choice%"=="13" goto WEB_PANEL
if "%choice%"=="14" goto OPEN_REPORTS
if /I "%choice%"=="S" goto CHANGE_SETTINGS
if "%choice%"=="0" goto EXIT

echo.
echo Invalid choice. Please select a number from 0 to 14, or S.
timeout /t 2 >nul
goto SHOW_MENU

:CHANGE_SETTINGS
cls
echo.
echo ============================================================================
echo Change Global Settings
echo ============================================================================
echo.
echo Current: Timeout=%TIMEOUT%  Retries=%RETRIES%  Resume=%RESUME%  Mode=%MODE%
echo.
set /p "new_timeout=Timeout in seconds [%TIMEOUT%]: "
if not "%new_timeout%"=="" set "TIMEOUT=%new_timeout%"
set /p "new_retries=Subprocess retries [%RETRIES%]: "
if not "%new_retries%"=="" set "RETRIES=%new_retries%"
set /p "new_resume=Auto-resume (1=yes, 0=no) [%RESUME%]: "
if not "%new_resume%"=="" set "RESUME=%new_resume%"
set /p "new_mode=Auto mode (auto/full/incremental) [%MODE%]: "
if not "%new_mode%"=="" set "MODE=%new_mode%"
goto SET_GLOBAL_ENV

:RUN_AUTO
cls
echo.
echo ============================================================================
echo Running Automatic Pipeline (auto) --mode %MODE%
echo ============================================================================
echo.
echo Settings: Timeout=%TIMEOUT%  Retries=%RETRIES%  Resume=%RESUME%
echo.
pause
pushd product_extraction
python main.py auto --mode %MODE%
popd
call :PAUSE_RETURN

:RUN_FULL
cls
echo.
echo ============================================================================
echo Running Full Pipeline (full)
echo ============================================================================
echo.
echo Settings: Timeout=%TIMEOUT%  Retries=%RETRIES%  Resume=%RESUME%
echo.
pause
pushd product_extraction
python main.py auto --mode full
popd
call :PAUSE_RETURN

:RUN_INCREMENTAL
cls
echo.
echo ============================================================================
echo Running Incremental Pipeline (incremental)
echo ============================================================================
echo.
echo Settings: Timeout=%TIMEOUT%  Retries=%RETRIES%  Resume=%RESUME%
echo.
pause
pushd product_extraction
python main.py auto --mode incremental
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
echo Scraping Product Specifications
echo ============================================================================
echo.
pushd product_extraction
python main.py scrape-specs
popd
call :PAUSE_RETURN

:STANDARDIZE
cls
echo.
echo ============================================================================
echo Standardizing Data
echo ============================================================================
echo.
pushd product_extraction
python main.py standardize
popd
call :PAUSE_RETURN

:COMPARE_SCANS
cls
echo.
echo ============================================================================
echo Comparing Scans (Change Detection)
echo ============================================================================
echo.
pushd product_extraction
python trackers\compare_scans.py
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

:IMPORT_BUILDER
cls
echo.
echo ============================================================================
echo Running Import Builder (WooCommerce CSV)
echo ============================================================================
echo.
pushd product_extraction
python main.py import-build
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

:RUN_TESTS
cls
echo.
echo ============================================================================
echo Running Unit Tests
echo ============================================================================
echo.
pushd product_extraction
python main.py test
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

:OPEN_REPORTS
cls
echo.
echo ============================================================================
echo Opening Reports Folder
echo ============================================================================
echo.
if exist "runtime\reports" (
    start "" "runtime\reports"
) else (
    echo Reports folder not found.
)
echo.
pause
goto SHOW_MENU

:PAUSE_RETURN
echo.
echo ============================================================================
echo Task finished. Press any key to return to the menu...
echo ============================================================================
pause >nul
goto SHOW_MENU

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