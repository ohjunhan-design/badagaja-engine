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
import glob
import os
import subprocess
import tempfile
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



# ── 재는 자리를 적는 데 쓰는 것들 (바깥 검수 11차) ──
def 크롬판():
    """크롬 판. **못 알아내면 그렇다고 적습니다** — 지어내지 않습니다.

    ★ 윈도와 리눅스가 다릅니다 (2026-09-28)

      리눅스 크롬은 `--version` 으로 잘 답합니다.
      윈도 크롬은 잘 안 답합니다. 이미 떠 있으면
      「기존 브라우저 세션에서 여는 중입니다」라 하고,
      따로 띄우면 아무 말도 안 합니다.

      대신 윈도에는 크롬이 깔린 자리에 **판 번호로 된 폴더**가
      있습니다. Chrome/Application/141.0.7390.55/ 처럼.
      그것을 읽으면 확실합니다.
    """
    try:
        길 = 크롬찾기()
    except Exception as e:
        return '크롬을 못 찾았습니다: %s' % str(e)[:40]

    if 윈도인가:
        칸 = os.path.dirname(길)
        판들 = []
        try:
            for 이름 in os.listdir(칸):
                # 141.0.7390.55 처럼 숫자와 점으로만 된 폴더
                if (os.path.isdir(os.path.join(칸, 이름))
                        and 이름.replace('.', '').isdigit()
                        and '.' in 이름):
                    판들.append(이름)
        except OSError as e:
            return '깔린 자리를 못 읽었습니다: %s' % str(e)[:40]
        if 판들:
            판들.sort(key=lambda v: [int(x) for x in v.split('.')])
            return 'Chrome ' + 판들[-1]
        return '판 폴더를 못 찾았습니다 (%s)' % 칸

    try:
        r = subprocess.run([길, '--version'], capture_output=True,
                           timeout=30)
        덩이 = (r.stdout or r.stderr or b'')
        return 덩이.decode('utf-8', 'replace').strip()[:60] or '(말이 없습니다)'
    except subprocess.TimeoutExpired:
        # ★ 2026-09-28 — 이것 때문에 416쪽을 못 잰 적이 있습니다.
        #   그래서 여기서는 **적기만** 하고 판단은 안 합니다.
        return '30초 안에 대답하지 않았습니다'
    except OSError as e:
        return '못 물어봤습니다: %s' % str(e)[:40]


def 한글글꼴있나():
    """한글 글꼴이 정말 깔려 있는가.

    ★ 없으면 크롬이 한글을 대체 글꼴로 그려 **글자 너비가
      달라집니다.** 그러면 넘침·줄바꿈이 어긋납니다.
    """
    if 윈도인가:
        칸 = os.path.join(os.environ.get('WINDIR', r'C:\\Windows'), 'Fonts')
        있는것 = []
        for 이름 in ('malgun.ttf', 'gulim.ttc', 'batang.ttc'):
            if os.path.exists(os.path.join(칸, 이름)):
                있는것.append(이름)
        return 있는것 or '없습니다'
    try:
        r = subprocess.run(['fc-list', ':lang=ko', 'family'],
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
        줄들 = sorted(set(x.strip() for x in (r.stdout or '').split('\n')
                          if x.strip()))
        return 줄들[:4] or '없습니다'
    except (OSError, subprocess.TimeoutExpired):
        return 'fc-list 를 못 돌렸습니다'


def 로케일():
    import locale
    try:
        쓰는것 = str(locale.getlocale())
    except Exception:
        쓰는것 = '(못 읽음)'
    return {
        'LANG': os.environ.get('LANG') or '(없음)',
        'LC_ALL': os.environ.get('LC_ALL') or '(없음)',
        '쓰는것': 쓰는것,
    }


def 시간대():
    """★ 물때는 시간대가 다르면 **하루가 밀립니다.**"""
    import datetime
    지금 = datetime.datetime.now()
    return {
        'TZ': os.environ.get('TZ') or '(없음)',
        '지금': 지금.strftime('%Y-%m-%d %H:%M'),
        'UTC와의차': str(지금.astimezone().utcoffset()),
    }

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

    # ★ **크롬마다 제 폴더를 줍니다** (2026-09-28 바깥 검수 11차)
    #
    #   판정 #22 에서 2번이 이렇게 말했습니다.
    #       끝난값 -6 · 내놓은 글 0자 · FATAL:chrome/browser
    #   -6 은 리눅스에서 죽었다는 뜻입니다(SIGABRT).
    #
    #   크롬은 아무 말 없이 **기본 프로필 폴더**를 씁니다.
    #   뮤테이션은 사본에서 검사기를 여러 번 돌리고 그때마다
    #   크롬이 뜹니다. 여럿이 같은 폴더를 잡으려 하면 죽습니다.
    #
    #   5·9·10번이 통과하는 것은 크롬을 하나씩 쓰기 때문으로
    #   보입니다. 뮤테이션만 겹칩니다.
    #
    #   폴더는 임시 자리에 만들고 그대로 둡니다 — 클라우드는
    #   매번 새 기계이고, 내 컴퓨터는 임시 폴더라 저절로 치워집니다.
    깃발.append('--user-data-dir=' + 크롬프로필자리())
    return 깃발


def 크롬프로필자리():
    """크롬이 쓸 **짧은** 프로필 자리 (2026-09-29).

    ★ 리눅스 소켓 경로는 108바이트를 못 넘습니다

      크롬은 프로필 폴더 안에 SingletonSocket 을 만듭니다.
      폴더가 깊으면 그 길이를 넘겨 이렇게 죽습니다.

          process_singleton_posix.cc:313] Socket path too long

      깃허브 러너는 임시 폴더가 작업 폴더 안(.tmp)이라 깁니다.
          /home/runner/work/badagaja-engine/badagaja-engine/.tmp/...
      그래서 리눅스에서는 **/tmp 밑에 짧은 이름**으로 만듭니다.
      윈도는 그런 제한이 없어 평소대로 둡니다.
    """
    if 윈도인가:
        return tempfile.mkdtemp(prefix='bada-chrome-')
    # 이름을 짧게 — /tmp/bc-abc123 쯤이면 30바이트 안쪽입니다
    바탕 = '/tmp' if os.path.isdir('/tmp') else None
    return tempfile.mkdtemp(prefix='bc-', dir=바탕)



def 옛사이트():
    """옛 사이트 자리. **없으면 (None, 까닭)** 을 돌려줍니다.

    ★ 왜 만들었나 (2026-09-28 — 거짓 통과를 찾았습니다)

      옛 사이트를 빈 폴더로 놓고 검사기를 돌려 봤더니
      셋이 **아무 말 없이 통과**했습니다.

        16 중국어 옛 자산 보호  「바꿔도 중국어판이 멀쩡합니다」
        24 옛쪽대비            「옛 쪽이 가졌던 것이 새 쪽에 모두 있습니다」

      **아무것도 안 봤는데 괜찮다고 합니다.**
      볼 것이 0개라 걸린 것도 0개였던 것입니다.

      클라우드에는 옛 사이트가 없습니다. 그러니 지금까지
      클라우드 판정의 16·24번 PASS 는 **거짓**이었습니다.

      못 잰 것은 통과가 아닙니다. 모르면 PASS 가 아닙니다.
      「거짓 판정은 판정이 없는 것보다 나쁩니다」
    """
    자리 = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
    if not 자리 or not os.path.isdir(자리):
        return None, '옛 사이트가 없습니다 (%s)' % (자리 or '자리를 안 알려 줌')
    # ★ 폴더만 있고 비어 있어도 **없는 것**입니다.
    #   있는 척하는 빈 폴더가 가장 고약합니다.
    if not glob.glob(os.path.join(자리, '*.html')):
        return None, '옛 사이트에 쪽이 한 장도 없습니다 (%s)' % 자리
    return 자리, ''


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
        # ★ **재는 자리를 낱낱이 적습니다** (2026-09-28 바깥 검수 11차)
        #
        #   「클라우드에서 실패했으니 코드가 틀렸다고 바로 결론
        #     내려도 안 되고, 윈도에서 통과했으니 코드가 맞다고
        #     결론 내려도 안 됩니다. 지금은 재현성 검증 단계입니다.」
        #
        #   그러려면 **두 자리의 기록을 나란히 놓고 다른 줄만
        #   보면 되게** 해야 합니다. 전에는 넷만 적어서, 글꼴이
        #   없는 것도 시간대가 다른 것도 안 보였습니다.
        '크롬판': 크롬판(),
        '한글글꼴': 한글글꼴있나(),
        '로케일': 로케일(),
        '시간대': 시간대(),
        '줄바꿈기본': repr(os.linesep),
        '경로구분자': os.sep,
        '작업폴더': os.getcwd(),
        '파일이름인코딩': sys.getfilesystemencoding(),
        '글자인코딩': sys.getdefaultencoding(),
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
