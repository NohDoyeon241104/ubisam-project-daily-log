@echo off
REM UBISAM 프로젝트 일일 기록 - 더블클릭 실행
REM pandas 가 설치된 Python310 을 직접 지정 (py 런처가 다른 파이썬을 잡는 문제 회피)
cd /d "%~dp0"

set PYEXE=C:\Users\User\AppData\Local\Programs\Python\Python310\python.exe

if exist "%PYEXE%" (
    "%PYEXE%" main_ui.py
) else (
    echo [경고] 지정한 파이썬을 찾을 수 없습니다: %PYEXE%
    echo py 런처로 대체 실행합니다.
    py main_ui.py
)

if %errorlevel% neq 0 (
    echo.
    echo [실행 중 오류가 발생했습니다. 위 메시지를 확인하세요.]
    pause
)
