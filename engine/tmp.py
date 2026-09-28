# -*- coding: utf-8 -*-
"""임시 파일이 **어느 드라이브에 쌓일지** 정하는 단 하나의 곳.

★ 왜 생겼나 (2026-09-27 — 실제로 멈췄습니다)

    전체 판정(`gate.py --full`)이 FAIL 3개로 끝났는데,
    까닭이 검사기가 아니라 **디스크였습니다.**

        f.write(text)
        OSError: [Errno 28] No space left on device

    C: 가 139GB 가운데 **0 바이트 남음**이었습니다.
    작업 폴더는 D: 인데, 검사기가 쓰는 임시 파일은
    `tempfile.mkdtemp()` 가 정하는 대로 **전부 C: 로 갔습니다.**

      · 크롬 프로필 (check_render — 쪽 416개를 그려 보는 동안)
      · 검사기가 만드는 시험용 site/ 사본
      · 뮤테이션 시험이 망가뜨렸다 되돌리는 사본

    한 번 돌 때마다 수 GB 가 C: 에 오갑니다. C: 가 빠듯하면
    **검사기가 제 일을 못 하고, 그것이 FAIL 로 보입니다.**
    없는 잘못을 쫓느라 시간을 흘립니다.

무엇을 하나
    이 파일을 **한 번이라도 불러오면** 그 뒤의 모든
    `tempfile.mkdtemp()` · `tempfile.NamedTemporaryFile()` 이
    작업 폴더 옆(`두번째도전/.tmp`)에 만들어집니다.

    `engine/io.py` 가 이 파일을 불러옵니다. io 는 검사기·시험이
    모두 불러오므로, **따로 기억할 것이 없습니다.**

바꾸고 싶으면
    BADAGAJA_TMP 에 길을 적습니다.

쓰는 법
    python engine/tmp.py          지금 어디로 가는지 봅니다
    python engine/tmp.py --청소   하루 지난 임시 폴더를 지웁니다
"""
import os
import sys
import time
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 작업 폴더 옆에 둡니다 — 자료와 같은 드라이브라 옮겨 붙일 일도 없습니다
기본자리 = os.path.join(ROOT, '.tmp')


def 자리():
    """임시 파일이 갈 곳. 없으면 만듭니다."""
    p = os.environ.get('BADAGAJA_TMP') or 기본자리
    try:
        os.makedirs(p, exist_ok=True)
    except OSError:
        # 만들 수 없으면 윈도우가 정한 자리를 그대로 씁니다
        return None
    return p


def 맞춤():
    """`tempfile` 이 쓰는 자리를 바꿉니다. 불러올 때 저절로 돕니다."""
    p = 자리()
    if not p:
        return None
    tempfile.tempdir = p
    # 밑으로 부르는 프로그램(크롬·다른 파이썬)도 같은 자리를 쓰게 합니다
    os.environ['TMP'] = p
    os.environ['TEMP'] = p
    os.environ['TMPDIR'] = p
    return p


def 남은공간(길=None):
    """그 자리가 있는 드라이브에 몇 GB 남았는지."""
    길 = 길 or 자리() or tempfile.gettempdir()
    try:
        return shutil.disk_usage(길).free / (1024 ** 3)
    except OSError:
        return None


def 청소(지난시간=24):
    """오래된 임시 폴더를 지웁니다.

    ★ 그냥은 안 지웁니다 (계약-17) — 우리가 만든 자리 안에서,
      정해진 이름으로 시작하고, 시간이 지난 것만 지웁니다.
    """
    p = 자리()
    if not p or not os.path.isdir(p):
        return 0, 0
    우리것 = ('badagaja-render-', 'checker-test-', 'console-', 'ads-check-',
              'tide-check-', 'contract07-', 'species-test-',
              'mutation-', 'newmoon-', 'months-')
    지금 = time.time()
    지운수, 지운바이트 = 0, 0
    for 이름 in os.listdir(p):
        if not 이름.startswith(우리것):
            continue          # 우리가 만든 것이 아니면 손대지 않습니다
        길 = os.path.join(p, 이름)
        try:
            if 지금 - os.path.getmtime(길) < 지난시간 * 3600:
                continue      # 아직 쓰고 있을 수 있습니다
            크기 = sum(os.path.getsize(os.path.join(뿌리, f))
                       for 뿌리, _, 파일들 in os.walk(길)
                       for f in 파일들)
            # 우리가 만든 이름으로 시작하고, 하루가 지난 것만 지웁니다
            shutil.rmtree(길, ignore_errors=True)  # 계약-17 예외
            지운수 += 1
            지운바이트 += 크기
        except OSError:
            continue
    return 지운수, 지운바이트


# 불러오는 순간 자리를 바꿉니다
현재자리 = 맞춤()


def main():
    print('임시 파일이 어디로 가는가')
    print('')
    print('  정해진 자리   %s' % (현재자리 or '(못 만들었습니다)'))
    print('  tempfile 이 쓰는 자리   %s' % tempfile.gettempdir())
    남 = 남은공간()
    print('  그 드라이브 남은 공간   %s'
          % ('%.1f GB' % 남 if 남 is not None else '못 쟀습니다'))
    if 남 is not None and 남 < 5:
        print('  ✗ 5GB 도 안 남았습니다 — 검사기가 도중에 멈춥니다')
    print('')

    if '--청소' in sys.argv:
        수, 바이트 = 청소()
        print('오래된 임시 폴더 %d개를 지웠습니다 (%.1f GB)'
              % (수, 바이트 / (1024 ** 3)))
    else:
        if 현재자리 and os.path.isdir(현재자리):
            것들 = os.listdir(현재자리)
            print('지금 남아 있는 임시 폴더 %d개' % len(것들))
            print('  (--청소 로 하루 지난 것을 지웁니다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
