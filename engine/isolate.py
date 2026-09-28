# -*- coding: utf-8 -*-
"""뮤테이션 시험이 **본 작업 트리를 건드리지 못하게** 따로 떼어 줍니다.

★ 왜 생겼나 (2026-09-27 — 실제로 물때가 한 칸 밀린 채 커밋됐습니다)

    `tests/test_checkers.py` 는 검사기가 잘못을 잡는지 보려고
    일부러 파일을 망가뜨렸다 되돌립니다. 그런데 그 시험이
    **돌고 있는 동안** `git add -A` 로 커밋했습니다.

        var m = (음력날(날짜) + 6) % 15;   ← 시험이 민 것이 커밋됨

    처음에는 `check_clean.py` 로 막았습니다. 그러나 그것은
    **응급 브레이크**입니다. 바깥 검수(2026-09-27 3차)가 짚었습니다.

      「근본적인 해결책은 시험이 운영 작업 트리의 tide.js 자체를
        건드리지 않게 만드는 것입니다」

    맞습니다. 여기가 그 답입니다.

무엇을 하나
    지금 작업 트리를 **바이트까지 똑같이** 임시 자리에 복사하고,
    그 사본의 뿌리를 돌려줍니다. 시험은 사본만 망가뜨립니다.
    다 쓰면 통째로 지웁니다.

★ 「쓰는 것과 재는 것이 같다」는 그대로입니다
    사본은 원본과 바이트가 같습니다. 그것을 **셈해서 증명합니다**
    (`같은가()`). 브라우저가 읽는 tide.js 는 원본과 한 바이트도
    다르지 않습니다. 있는 자리만 다릅니다.

쓰는 법
    from engine import isolate

    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        ...망가뜨리고 검사기를 뿌리에서 돌립니다...
    # 여기서 사본은 이미 지워졌습니다. 본 트리는 손댄 적이 없습니다.

    python engine/isolate.py        제대로 떠지는지 봅니다
"""
import os
import sys
import shutil
import hashlib
import tempfile
import subprocess
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io    # noqa: E402  (파일 쓰기는 여기만 — 계약-13)
from engine import tmp   # noqa: E402  (임시 파일을 작업 드라이브로)

# 떠 갈 것 — 검사기가 읽는 것은 모두 들어가야 합니다
뜰것 = ('engine', 'tests', 'assets', 'template', 'docs', 'data', 'site',
        'tools')

# 떠 가지 않을 것 — 무겁거나, 사본에서는 뜻이 없는 것
뺄것 = ('.git', '.tmp', 'release', '__pycache__', '.pytest_cache',
        'node_modules')


def _뺀다(길, 이름들):
    return [n for n in 이름들 if n in 뺄것 or n.endswith('.pyc')]


def 셈(뿌리, 갈래=('assets', 'template', 'data', 'engine')):
    """그 뿌리 밑 파일들의 지문. 원본과 사본이 같은지 볼 때 씁니다."""
    h = hashlib.sha256()
    for 갈 in sorted(갈래):
        d = os.path.join(뿌리, 갈)
        if not os.path.isdir(d):
            continue
        for 위, 폴더들, 파일들 in os.walk(d):
            폴더들[:] = sorted(x for x in 폴더들 if x not in 뺄것)
            for f in sorted(파일들):
                if f.endswith('.pyc'):
                    continue
                p = os.path.join(위, f)
                h.update(os.path.relpath(p, 뿌리)
                         .replace(os.sep, '/').encode('utf-8'))
                try:
                    with open(p, 'rb') as fp:
                        for 덩이 in iter(lambda: fp.read(1 << 20), b''):
                            h.update(덩이)
                except OSError:
                    h.update('<못읽음>'.encode('utf-8'))
    return h.hexdigest()


def 같은가(뿌리):
    """사본이 본 트리와 바이트까지 같은가 — 「쓰는 것과 재는 것이 같다」."""
    return 셈(뿌리) == 셈(ROOT)


def 본트리가깨끗한가():
    """본 작업 트리에서 **git 이 아는 파일**이 바뀐 것이 있는가.

    바깥 검수가 더하라고 한 통과 조건입니다.

      「mutation test 종료 후: 메인 worktree tracked file 변경 0개」

    돌려주는 것
        (알아냈나, 바뀐 파일 목록)
        알아냈나 가 False 면 git 을 못 물어본 것입니다 —
        **깨끗하다고 세지 않습니다.**
    """
    try:
        r = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False, []
    if r.returncode != 0:
        return False, []
    바뀐것 = [x[3:].strip().strip('"')
              for x in (r.stdout or '').split('\n') if x.strip()]
    return True, 바뀐것


@contextlib.contextmanager
def 일터(prefix='mutation-'):
    """본 트리를 그대로 뜬 임시 뿌리. 나올 때 지웁니다."""
    바깥 = tempfile.mkdtemp(prefix=prefix)
    뿌리 = os.path.join(바깥, '두번째도전')
    os.makedirs(뿌리)
    try:
        for 갈 in 뜰것:
            원 = os.path.join(ROOT, 갈)
            if not os.path.isdir(원):
                continue
            shutil.copytree(원, os.path.join(뿌리, 갈), ignore=_뺀다)
        # 뿌리에 바로 있는 파일들도 (.htaccess·설정 같은 것)
        for 이름 in os.listdir(ROOT):
            p = os.path.join(ROOT, 이름)
            if os.path.isfile(p) and 이름 not in 뺄것:
                try:
                    shutil.copy2(p, os.path.join(뿌리, 이름))
                except OSError:
                    pass
        yield 뿌리
    finally:
        # 우리가 방금 만든 임시 자리만 지웁니다 — 남의 것은 안 건드립니다
        shutil.rmtree(바깥, ignore_errors=True)  # 계약-17 예외


def main():
    print('뮤테이션 시험을 본 트리에서 떼어 놓을 수 있는가')
    print('')
    with 일터() as 뿌리:
        print('  임시 일터   %s' % 뿌리)
        있나 = [갈 for 갈 in 뜰것 if os.path.isdir(os.path.join(뿌리, 갈))]
        print('  떠 온 갈래  %s' % ' · '.join(있나))
        똑같나 = 같은가(뿌리)
        print('  바이트까지 같은가   %s'
              % ('같습니다 — 「쓰는 것과 재는 것이 같다」가 지켜집니다'
                 if 똑같나 else '✗ 다릅니다'))
        if not 똑같나:
            return 1
        # 사본을 망가뜨려도 본 트리는 그대로여야 합니다
        p = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        if os.path.exists(p):
            # 파일 쓰기는 io.write() 만 씁니다 (계약-13)
            io.write(p, io.read(p) + chr(10) + '// 시험용 자국' + chr(10))
            원본 = os.path.join(ROOT, 'assets', 'js', 'tide.js')
            샜나 = '시험용 자국' in io.read(원본, default='')
            print('  사본을 망가뜨려도 본 트리는 그대로인가   %s'
                  % ('✗ 샜습니다' if 샜나 else '그대로입니다'))
            if 샜나:
                return 1
    print('  사본을 지웠습니다')
    print('')
    알았나, 바뀐것 = 본트리가깨끗한가()
    if not 알았나:
        print('  ~ git 을 못 물어봤습니다 — 깨끗하다고 세지 않습니다')
    else:
        print('  본 트리에서 바뀐 파일 %d개' % len(바뀐것))
        for x in 바뀐것[:6]:
            print('      %s' % x)
    print('')
    print('본 트리를 건드리지 않고 시험할 수 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
