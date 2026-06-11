@echo off
REM UBISAM 프로젝트 일일 기록 - 더블클릭 실행
REM 이 배치 파일이 있는 폴더(scripts)로 이동 후 py 런처로 실행
cd /d "%~dp0"

REM py 런처가 있으면 py 로, 없으면 python 으로 실행
where py >nul 2>nul
if %errorlevel%==0 (
    py main_ui.py
) else (
    python main_ui.py
)

REM 오류로 창이 바로 닫히면 메시지 확인용으로 일시정지
if %errorlevel% neq 0 (
    echo.
    echo [실행 중 오류가 발생했습니다. 위 메시지를 확인하세요.]
    pause
)
