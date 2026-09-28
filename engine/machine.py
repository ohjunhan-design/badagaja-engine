# -*- coding: utf-8 -*-
"""이 컴퓨터가 어떤 컴퓨터인가 — **한 곳에서만** 봅니다.

★ 왜 만들었나 (2026-09-27 주인 지시 「클라우드에서 진행할 방법」)

    판정을 깃허브 액션(리눅스)에서도 돌리려고 살펴봤더니,
    **같은 코드가 여러 군데 베껴져** 있었습니다.

        크롬 자리   check_ads · check_console · check_months ·
                    check_newmoon · check_render · check_tide   **6곳**
        메모리 재기  check_render · gate                        **2곳**

    `net.py` 를 만든 까닭과 똑같습니다. 한 곳을 고치고 다른 곳을
    잊으면 **검사기마다 답이 달라집니다.** 실제로 그런 일이 있었습니다 —
    크롬 찾기를 셋만 고치고 `check_render` 를 빠뜨려서,
    「크롬이 없을 때」 시험이 **진짜 크롬을 찾아 통과**했습니다.

★ 리눅스에서도 돌아야 합니다
    깃허브 액션 러너는 우분투입니다. 거기에는
      · `C:\\Program Files\\...` 가 없습니다
      · `ctypes.windll` 이 없습니다
      · `powershell` 이 없습니다
    그래서 **못 재면 None** 을 돌려줍니다. 짐작하지 않습니다.
    (「못 잰 것을 지킴으로도, 어김으로도 세지 않는다」)
"""
import os
import sys
import shutil

윈도인가 = sys.platform.startswith('win')

# 크롬 자리 — 윈도와 리눅스 둘 다
#
# ★ 엣지는 쓰지 않습니다 (주인 규칙 25)
#   「화면 확인·캡처는 언제나 크롬으로 합니다. 엣지는 쓰지 않습니다.」
크롬후보_윈도 = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
]
크롬후보_리눅스 = [
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/opt/google/chrome/chrome',
    # 깃허브 액션의 setup-chrome 이 여기에 둡니다
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
]
찾을이름 = ['chrome', 'chrome.exe', 'google-chrome',
            'google-chrome-stable', 'chromium', 'chromium-browser']


def 크롬찾기():
    """크롬 자리. 못 찾으면 **터뜨립니다** — 조용히 넘어가지 않습니다.

    ★ BADAGAJA_CHROME 이 먼저입니다
      · 다른 컴퓨터에 크롬이 딴 자리에 있을 수 있습니다
      · 시험이 「크롬이 없을 때」를 만들어 볼 수 있어야 합니다
        (tests/test_not_tested.py — 못 재면 통과가 아님을 증명)
    """
    정해준것 = os.environ.get('BADAGAJA_CHROME')
    if 정해준것:
        if os.path.exists(정해준것):
            return 정해준것
        raise RuntimeError('정해 준 자리에 크롬이 없습니다: %s' % 정해준것)

    for p in (크롬후보_윈도 if 윈도인가 else 크롬후보_리눅스):
        if os.path.exists(p):
            return p
    for 이름 in 찾을이름:
        p = shutil.which(이름)
        if p:
            return p
    raise RuntimeError(
        '크롬을 찾지 못했습니다. 엣지는 쓰지 않습니다 (주인 규칙 25)')



def 크롬앞머리():
    """크롬을 부르는 **앞머리**. 여기 한 곳에서만 정합니다.

    ★ 왜 만들었나 (2026-09-28 — 클라우드 판정이 통째로 못 쟀습니다)

      크롬을 부르는 자리가 **열한 군데**였는데, `--no-sandbox` 를
      주는 곳은 한 곳뿐이었습니다. 내 컴퓨터에서는 아무 탈이
      없어서 몰랐습니다. 깃허브 러너는 **루트로 돌기 때문에**
      그 깃발이 없으면 크롬이 아예 시작하지 않습니다.

      그래서 쪽마다 180초를 넘겼고, 검사기는 「잴 형편이 안 됨」
      이라 했습니다. 판정표에는 이렇게 찍혔습니다.

          5  자바스크립트 콘솔   INFRA_FAIL
          9  광고 lazy-load      INFRA_FAIL
          10 광고 레이아웃        FAIL
          4  416쪽 렌더링        NOT_TESTED
          8  물때 독립 검증       NOT_TESTED

      **한 쪽도 못 쟀는데 그 까닭이 깃발 하나였습니다.**
      게다가 메시지가 「크롬이 도는 자리에서 다시 재세요」라
      크롬이 없는 것처럼 읽혀, 없는 길을 한참 찾았습니다.

      같은 사실을 열한 곳에서 관리하면 언젠가 반드시 어긋납니다.
      (덧검사 「짜임」이 가리키던 것이 바로 이것입니다)
    """
    깃발 = [크롬찾기(), '--headless=new', '--disable-gpu']
    if not 윈도인가:
        # 리눅스 CI 는 루트로 돕니다. /dev/shm 도 작습니다.
        깃발 += ['--no-sandbox', '--disable-dev-shm-usage']
    return 깃발


def 남은메모리GB():
    """지금 쓸 수 있는 메모리(GB). **못 재면 None** — 짐작하지 않습니다.

    ★ 윈도에서는 실제 메모리와 **커밋 여유** 중 작은 쪽을 봅니다.
      C 가 꽉 차면 페이징 파일을 못 늘려 커밋이 먼저 바닥납니다.
      2026-09-27 에 실제로 그랬습니다 — 메모리는 있는데 커밋이
      없어 크롬이 안 떴습니다.
    """
    if 윈도인가:
        return _윈도메모리()
    return _리눅스메모리()


def _윈도메모리():
    try:
        import ctypes

        class _상태(ctypes.Structure):
            _fields_ = [('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

        것 = _상태()
        것.dwLength = ctypes.sizeof(_상태)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(것)):
            return None
        return min(것.ullAvailPhys, 것.ullAvailPageFile) / (1024.0 ** 3)
    except Exception:          # noqa: BLE001  못 재면 못 잰 것입니다
        return None


def _리눅스메모리():
    """/proc/meminfo 의 MemAvailable 을 봅니다.

    MemTotal 에서 빼는 것이 아닙니다 — 리눅스는 남는 메모리를 캐시로
    쓰므로 MemFree 는 늘 작게 나옵니다. **MemAvailable 이 참값**입니다.
    """
    try:
        with open('/proc/meminfo') as f:
            for 줄 in f:
                if 줄.startswith('MemAvailable:'):
                    킬로 = float(줄.split()[1])
                    return 킬로 / (1024.0 * 1024.0)
    except (OSError, ValueError, IndexError):
        return None
    return None


def 어디서도나():
    """판정 결과에 적어 둘 한 줄. 어느 컴퓨터에서 쟀는지 남깁니다.

    ★ 바깥 검수 5차 지시 — 「환경을 기록하십시오」
      같은 판인데 결과가 다를 때, 무엇이 달랐는지 알려면
      **잰 형편을 함께 남겨야** 합니다.
    """
    import platform
    나옴 = {
        '운영체제': platform.system(),
        '버전': platform.release(),
        '파이썬': platform.python_version(),
        '코어': os.cpu_count(),
        '클라우드인가': bool(os.environ.get('GITHUB_ACTIONS')),
    }
    남은 = 남은메모리GB()
    나옴['쓸수있는메모리GB'] = round(남은, 1) if 남은 is not None else None
    try:
        나옴['크롬'] = 크롬찾기()
    except RuntimeError:
        나옴['크롬'] = None
    return 나옴


if __name__ == '__main__':
    import json
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(어디서도나(), ensure_ascii=False, indent=2))
