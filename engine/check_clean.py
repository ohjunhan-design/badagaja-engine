# -*- coding: utf-8 -*-
"""**시험이 망가뜨린 파일이 커밋되지 않게** 막습니다.

★ 왜 생겼나 (2026-09-27 — 제가 실제로 저질렀습니다)

    tests/test_checkers.py 는 검사기가 잘못을 잡는지 보려고
    **일부러 파일을 망가뜨렸다가 되돌립니다.**

        assets/js/tide.js 의 물때 식을 한 칸 밀어 보고,
        check_tide 가 잡는지 본 뒤 되돌립니다.

    그런데 그 시험이 **돌고 있는 동안** 제가 `git add -A` 로
    커밋했습니다. 망가진 상태가 그대로 들어갔습니다.

        var m = (음력날(날짜) + 6) % 15;   ← 시험이 민 것이 커밋됨

    물때가 통째로 한 칸 밀렸고, 손님이 보는 날이 하루 어긋납니다.
    **물때는 이 사이트의 뼈대입니다.** 그대로 배포됐으면 큰일이었습니다.

무엇을 보나
    자료·움직임에 **시험이 넣는 표시**가 남아 있는지 봅니다.
    시험이 쓰는 값은 정해져 있으므로, 그것이 보이면 되돌리다 만 것입니다.

★ 커밋하기 전에 돌립니다
    engine/gate.py 가 가장 먼저 부릅니다.

쓰는 법
    python engine/check_clean.py
    python engine/check_clean.py --strict
    python engine/check_clean.py --strict --커밋전   커밋 직전 (시험이 도는 중이면 막습니다)
"""
import os
import re
import sys
import glob
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402
from engine import io   # noqa: E402

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []

# 시험이 일부러 넣는 것들 — 남아 있으면 되돌리다 만 것입니다
시험자국 = [
    ('assets/js/tide.js', r'\(음력날\(날짜\) \+ 6\) % 15',
     'tests/test_checkers.py 가 물때 식을 한 칸 민 자국'),
    ('docs/CONTRACTS.md', r'### 계약-99',
     'tests/test_checkers.py 가 넣은 가짜 계약'),
]

# 자료에 있으면 안 되는 시험용 값
자료자국 = [
    ('raw/ads.json', '없는자리-pc', '시험이 넣은 가짜 광고 자리'),
    ('raw/site.json', '딴 제목', '시험이 넣은 가짜 제목'),
    ('raw/species-map.json', None, 'fix_species 가 지웠어야 할 중간 파일'),
]


def 안커밋한것():
    try:
        r = subprocess.run(['git', 'status', '--porcelain'],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=30)
        if r.returncode != 0:
            return None
        return [x[3:].strip().strip('"') for x in (r.stdout or '').split('\n')
                if x.strip()]
    except OSError:
        return None


def 시험이도나():
    """지금 시험이 돌고 있는가 — 돌고 있으면 커밋하면 안 됩니다."""
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | Select-Object -ExpandProperty CommandLine) -join '|'"],
            capture_output=True, text=True, timeout=30)
        글 = r.stdout or ''
        도는것 = [x for x in ('test_checkers', 'test_not_tested',
                              'test_idempotent', 'test_rollback')
                  if x in 글]
        return 도는것
    except (OSError, subprocess.SubprocessError):
        return None



def 개인연락처():
    """★ **개인 휴대전화가 쪽에 나가면 안 됩니다** (2026-09-28)

    저장소를 공개로 바꿀지 살피다 찾았습니다.

        "채취 범위·방법은 운영자(010-****-****)에게 확인"

    (★ 실제 번호는 여기에도 적지 않습니다. 저장소가 공개라
     설명글에 적어 두면 그것도 똑같이 드러납니다.)

    갯벌체험장 운영자의 개인 휴대전화가 자료에 적혀 있었고,
    그것이 쪽에 그대로 나가고 있었습니다.
    옛 사이트에는 없던 것입니다 — 새 틀이 자료를 더 많이 쓰면서
    딸려 나왔습니다.

    ★ 기관 번호(031-310-3460 같은 것)는 **괜찮습니다.**
      공개된 안내 번호이고, 손님이 물어볼 곳입니다.
      막아야 하는 것은 **010 으로 시작하는 개인 휴대전화**입니다.

    개인 연락처를 웹에 내면 그분이 낯선 전화를 받게 됩니다.
    우리가 대신 결정할 일이 아닙니다.
    """
    print('[개인 연락처] 휴대전화가 쪽에 나가는가')
    # ★ **구분자를 꼭 끼워 찾습니다** (2026-09-28 · 고친 것)
    #
    #   처음에는 구분자를 없어도 되게(?) 두었더니 사진 제목
    #
    #       "Ilgwang Station Platform 20170311 172319"
    #
    #   의 가운데 토막(0170311 1723)을 전화번호로 읽어
    #   멀쩡한 쪽 2개를 막았습니다.
    #   **검사기가 없는 잘못을 만들면 진짜 잘못이 묻힙니다.**
    #
    #   그래서 - 또는 . 또는 빈칸을 **반드시** 끼우게 하고,
    #   앞뒤에 숫자가 더 붙어 있으면 전화번호가 아니라고 봅니다.
    #   (\b 는 안 씁니다 — 파이썬 글자열에서 백스페이스로 먹습니다)
    무늬 = re.compile(
        r'(?<![0-9])01[016789](?:[-. ]\d{3,4}[-. ]\d{4}'
        r'|\d{7,8})(?![0-9])')
    걸린것 = []
    쪽자리 = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
    for p2 in sorted(glob.glob(os.path.join(쪽자리, '**', '*.html'),
                               recursive=True)):
        이름 = os.path.relpath(p2, 쪽자리).replace(os.sep, '/')
        글 = io.read(p2, default='')
        for m in 무늬.finditer(글):
            앞 = 글[max(0, m.start() - 40):m.start()]
            앞 = re.sub(r'<[^>]*>', '', 앞).strip()[-28:]
            걸린것.append('%s — …%s%s' % (이름, 앞, m.group(0)))
            break
    if 걸린것:
        막음.append('개인 휴대전화가 쪽에 나갑니다 %d곳' % len(걸린것))
        print('  ✗ 개인 휴대전화가 나가는 쪽 %d개' % len(걸린것))
        for x in 걸린것[:4]:
            print('      %s' % x)
        print('      → 그분이 낯선 전화를 받게 됩니다.')
        print('        기관 번호는 괜찮지만 010 은 빼세요.')
    else:
        print('  · 개인 휴대전화가 나가는 쪽이 없습니다')
    print('')

    # ── ★ **쪽만 보면 반쪽이었습니다** (2026-09-28)
    #
    #   위 검사를 만들어 쪽에서는 번호를 지웠습니다.
    #   그런데 저장소를 공개로 옮기려고 훑어보니, 하필
    #   **바로 이 검사기의 설명글**에 실제 번호를 적어
    #   두었습니다. 「무엇을 잡았는지」 예로 남겨 둔 것이었습니다.
    #
    #   공개 저장소는 쪽과 똑같이 누구나 봅니다. 더구나
    #   **git 기록은 나중에 지워도 남습니다.** 올리기 전에 봅니다.
    #
    print('[개인 연락처] 저장소 파일에도 없는가')
    엄한무늬 = 무늬          # 위에서 정한 것을 그대로 씁니다
    볼꼬리 = ('.py', '.json', '.md', '.yml', '.yaml',
              '.html', '.css', '.js', '.txt')
    건너뛸칸 = {'.git', 'site', 'img', 'out', '__pycache__',
                'node_modules', '.venv', '.tmp'}   # .tmp 는 시험 복사본
    소스걸림 = []
    for 뿌리, 칸들, 파일들 in os.walk(ROOT):
        칸들[:] = [c for c in 칸들 if c not in 건너뛸칸]
        for f in sorted(파일들):
            if not f.endswith(볼꼬리):
                continue
            전체 = os.path.join(뿌리, f)
            이름 = os.path.relpath(전체, ROOT).replace(os.sep, '/')
            m = 엄한무늬.search(io.read(전체, default=''))
            if m:
                소스걸림.append('%s — %s' % (이름, m.group(0)))
    if 소스걸림:
        막음.append('저장소 파일에 개인 휴대전화가 있습니다 %d곳'
                    % len(소스걸림))
        print('  ✗ 개인 휴대전화가 든 파일 %d개' % len(소스걸림))
        for x in 소스걸림[:6]:
            print('      %s' % x)
        print('      → 저장소가 공개입니다. 쪽에서 지워도')
        print('        소스에 남으면 똑같이 드러납니다.')
    else:
        print('  · 저장소 파일에도 없습니다')
    print('')


def main():
    print('시험이 망가뜨린 것이 남아 있는가')
    print('')

    # ── 1. 시험 자국
    print('[1] 시험이 넣는 표시가 남아 있는가')
    찾음 = []
    # ★ **읽은 파일을 셉니다** (2026-10-08 바깥 검수)
    #   `io.read(p, default='')` 는 못 읽어도 빈 글을 줍니다.
    #   그러면 「자국 없음」이 되어 **안 보고 통과**였습니다.
    읽은것 = 0
    for 길, 꼴, 무엇 in 시험자국:
        p = os.path.join(ROOT, 길.replace('/', os.sep))
        if not os.path.exists(p):
            continue
        s = io.read(p, default='')
        읽은것 += 1 if s else 0
        if re.search(꼴, s):
            찾음.append('%s — %s' % (길, 무엇))
    for 길, 값, 무엇 in 자료자국:
        p = os.path.join(DATA, 길.replace('/', os.sep))
        if 값 is None:
            if os.path.exists(p):
                찾음.append('%s — %s' % (길, 무엇))
            continue
        if os.path.exists(p) and 값 in io.read(p, default=''):
            찾음.append('%s — %s' % (길, 무엇))
    if 찾음:
        막음.append('시험 자국 %d건' % len(찾음))
        print('  ✗ %d건 — **시험이 되돌리다 만 것입니다**' % len(찾음))
        for x in 찾음:
            print('      %s' % x)
        print('      → git checkout 으로 되돌리거나, 손으로 고치세요.')
        print('        이대로 커밋하면 망가진 것이 배포됩니다.')
    else:
        개인연락처()
        print('  · 시험 자국이 없습니다')
    print('')

    # ── 2. 시험이 지금 돌고 있는가
    #
    # ★ 이것은 **커밋 직전에만** 막습니다 (--커밋전). 까닭이 둘입니다.
    #
    #   (1) 고리가 생깁니다.
    #       tests/test_checkers.py 가 check_clean 을 시험하는데,
    #       check_clean 이 「test_checkers 가 돌고 있으니 안 됩니다」라고
    #       답합니다. 검사기가 **자기 자신 때문에** 실패합니다.
    #       바깥 검수(3차)가 끊으라고 한 그 고리입니다.
    #
    #   (2) 이제 필요가 줄었습니다.
    #       시험은 engine/isolate.py 로 뜬 **사본**만 망가뜨립니다.
    #       본 트리는 애초에 건드리지 않습니다. 그러니 이 검사는
    #       「사고를 막는 장치」가 아니라 **마지막 안전망**입니다.
    커밋전 = '--커밋전' in sys.argv
    mustmeasure.있어야한다(range(읽은것), '읽은 파일', 최소=1,
                           어디=ROOT)

    print('[2] 시험이 지금 돌고 있는가%s'
          % ('' if 커밋전 else '  (커밋 직전이 아니므로 알림만)'))
    도는것 = 시험이도나()
    if 도는것 is None:
        알림.append('돌고 있는 것을 못 봤습니다')
        print('  ~ 못 봤습니다 (윈도우가 아니거나 물어볼 수 없었습니다)')
    elif 도는것:
        if 커밋전:
            막음.append('시험이 돌고 있습니다: %s' % ' · '.join(도는것))
            print('  ✗ 시험이 돌고 있습니다 — **지금 커밋하면 안 됩니다**')
        else:
            알림.append('시험이 돌고 있습니다: %s' % ' · '.join(도는것))
            print('  ~ 시험이 돌고 있습니다 (커밋만 하지 않으면 괜찮습니다)')
        for x in 도는것:
            print('      %s' % x)
        if 커밋전:
            print('      시험이 파일을 고쳤다 되돌리는 중이라,')
            print('      지금 커밋하면 **고치다 만 상태**가 들어갑니다.')
    else:
        print('  · 돌고 있는 시험이 없습니다')
    print('')

    # ── 3. 안 커밋한 것 가운데 자료·움직임
    print('[3] 안 커밋한 것 가운데 자료·움직임')
    것들 = 안커밋한것()
    if 것들 is None:
        print('  ~ git 을 못 읽었습니다')
    else:
        중요한것 = [x for x in 것들
                    if x.startswith(('assets/', 'data/', 'engine/',
                                     'template/'))]
        print('      안 커밋한 것 %d개 · 그중 자료·움직임 %d개'
              % (len(것들), len(중요한것)))
        for x in 중요한것[:6]:
            print('      %s' % x)
        if len(중요한것) > 6:
            print('      … 그 밖 %d개' % (len(중요한것) - 6))
    print('')

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 2026-09-27 에 실제로 이것 때문에 물때가 한 칸 밀린 채')
        print('    커밋됐습니다. 손님이 하루 틀린 날에 바다에 갈 뻔했습니다.')
        return 1 if '--strict' in sys.argv else 0
    print('시험이 망가뜨린 것이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
