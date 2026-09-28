@echo off
chcp 65001 > nul
setlocal

rem ============================================================
rem  재시동 뒤에 이것만 두 번 누르시면 됩니다.
rem
rem  2026-09-27 — 메모리가 1.9GB 밖에 안 남아 판정이 넘어졌습니다.
rem    커밋 45.4GB / 한계 48.7GB · 프로그램이 잡은 것은 12.3GB 뿐
rem    → 33GB 를 시스템이 쥐고 있어 껐다 켜야 풀립니다.
rem
rem  하는 일
rem    1. 남은 임시 파일을 치웁니다
rem    2. 쪽 416개를 다시 만듭니다
rem    3. 전체 판정을 돌립니다
rem    4. 결과를 파일로 남깁니다  →  tests\out\판정결과.txt
rem
rem  다 되면 창이 저절로 닫히지 않습니다. 결과를 보시고 닫으세요.
rem  클로드에게는 「판정 끝났어」라고만 말씀해 주시면 읽겠습니다.
rem ============================================================

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo.
echo   바다가자닷컴 두번째도전 — 재시동 뒤 판정
echo   ============================================
echo.

echo   [1/4] 쓸 수 있는 메모리를 봅니다
powershell -NoProfile -Command "$os=Get-CimInstance Win32_OperatingSystem; $p=Get-CimInstance Win32_PerfRawData_PerfOS_Memory; '        메모리 {0:N1}GB 중 {1:N1}GB 쓸 수 있음' -f ($os.TotalVisibleMemorySize/1MB),($os.FreePhysicalMemory/1MB); '        커밋 {0:N1}GB / 한계 {1:N1}GB' -f ($p.CommittedBytes/1GB),($p.CommitLimit/1GB)"
echo.

echo   [2/4] 묵은 임시 파일을 치웁니다
python engine\tmp.py --청소
echo.

echo   [3/4] 쪽 416개를 다시 만듭니다
python engine\build.py > tests\out\만들기결과.txt 2>&1
if errorlevel 1 (
  echo        X 만들다 멈췄습니다. tests\out\만들기결과.txt 를 보세요.
  goto 끝
)
powershell -NoProfile -Command "Get-Content tests\out\만들기결과.txt -Tail 3"
echo.

echo   [4/4] 전체 판정을 돌립니다 (10~15분)
echo        기다리는 동안 다른 프로그램을 띄우지 마세요.
echo        특히 크롬을 쓰면 판정이 못 잽니다.
echo.
python engine\gate.py --full --json > tests\out\판정결과.txt 2>&1
echo.
powershell -NoProfile -Command "Get-Content tests\out\판정결과.txt -Tail 28"

:끝
echo.
echo   ============================================
echo   결과가 여기 있습니다:
echo       tests\out\판정결과.txt
echo       tests\out\gate.json
echo.
echo   클로드에게 「판정 끝났어」라고만 말씀해 주세요.
echo.
pause
endlocal
