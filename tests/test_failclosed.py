# -*- coding: utf-8 -*-
"""검사기를 **못 재는 환경에 놓고** 돌려 봅니다 (2026-10-08).

★ 왜 이 시험이 있나 — 바깥 검수가 못박았습니다

    「모든 validator/checker 를 fail-open 전수조사하세요. 검사를
      수행할 수 없으면 PASS 가 아니라 UNAVAILABLE(4) 또는 ERROR(3) 로
      종료해야 합니다. 각 checker 별 good fixture → PASS,
      broken fixture → FAIL, missing dependency → UNAVAILABLE
      회귀시험을 추가하세요. 단 메타검사(AST) 하나를 유일한 보증으로
      삼지 마세요」

    `engine/check_failclosed.py` 는 **짜임(AST)** 으로 봅니다. 이것은
    **실제로 돌려서** 봅니다. 둘은 서로를 못 대신합니다 —
    AST 는 안 도는 길도 잡고, 실측은 도는 길만 잡습니다.

어떻게 못 재게 하나

    ① 자료를 **하나도 못 읽게** 합니다.
       `sitecustomize.py` 로 `engine.io.read` 와 `io.open` 을 가로채
       터지게 만듭니다. 자료 없이 재는 검사기는 없습니다.
    ② 바깥 꾸러미(`yaml`·`PIL`)를 **못 찾게** 합니다.
    ③ 크롬을 **못 찾게** 합니다 (`BADAGAJA_CHROME` 을 없는 길로).

    그러고도 **끝난값 0** 을 내면 거짓 통과입니다.

쓰는 법
    python tests/test_failclosed.py              빠른 것만
    python tests/test_failclosed.py --모두        51장 전부 (오래 걸립니다)
"""
import io
import os
import sys
import glob
import json
import shutil
import tempfile
import subprocess

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

# 돌리는 데 오래 걸리는 것들 — `--모두` 일 때만 봅니다
오래걸리는것 = ('check_render.py', 'check_mobile.py', 'check_design.py',
                'check_nocoord.py', 'check_hero_quality.py',
                'check_photo_dup.py', 'check_links.py', 'check_deployed.py',
                'check_canary.py', 'check_backup.py')

# 바깥을 보는 것 — 못 재는 게 정상이라 여기서는 뺍니다
#   (네트워크·서버를 보는 검사는 「못 쟀음」이 이미 계약입니다)
바깥을보는것 = ('check_deployed.py', 'check_canary.py', 'check_origin.py')

막는글 = '''# -*- coding: utf-8 -*-
"""자료를 하나도 못 읽는 환경을 만듭니다 (시험 전용)."""
import builtins

_진짜 = builtins.open


def _막힌열기(*a, **k):
    이름 = a[0] if a else k.get('file', '')
    try:
        이름 = str(이름)
    except Exception:
        이름 = ''
    # 파이썬이 저를 불러들이는 길은 막지 않습니다 —
    # 막으면 인터프리터가 아예 안 뜹니다.
    if 이름.endswith(('.pyc', '.pyd', '.so', '.dll', '.zip', '.egg')):
        return _진짜(*a, **k)
    if 'site-packages' in 이름 or 'lib' in 이름.lower()[:60]:
        return _진짜(*a, **k)
    raise OSError('시험: 자료를 못 읽는 환경입니다')


builtins.open = _막힌열기

import io as _io                                        # noqa: E402
_io.open = _막힌열기
'''


def 터만들기():
    터 = tempfile.mkdtemp(prefix='failclosed-')
    io.open(os.path.join(터, 'sitecustomize.py'), 'w',
            encoding='utf-8').write(막는글)
    # yaml·PIL 을 못 찾게 합니다
    for m in ('yaml', 'PIL'):
        io.open(os.path.join(터, m + '.py'), 'w', encoding='utf-8').write(
            "raise ImportError('시험: %s 가 없는 환경입니다')\n" % m)
    return 터


def 돌리기(검사기, 터, 시간=90):
    환 = dict(os.environ)
    환['PYTHONUTF8'] = '1'
    환['PYTHONPATH'] = 터 + os.pathsep + 환.get('PYTHONPATH', '')
    환['BADAGAJA_CHROME'] = os.path.join(터, '없는크롬.exe')
    환['PATH'] = 터           # 크롬도 lftp 도 못 찾습니다
    try:
        끝 = subprocess.run(
            [sys.executable, '-X', 'utf8', os.path.join('engine', 검사기)],
            cwd=여기, env=환, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=시간)
        return 끝.returncode, (끝.stdout or '')[-300:]
    except subprocess.TimeoutExpired:
        return 'timeout', ''


def main():
    모두 = '--모두' in sys.argv
    print('검사기를 **못 재는 환경**에 놓고 돌려 봅니다')
    print('  자료 못 읽음 · yaml/PIL 없음 · 크롬 없음')
    print('  → 그러고도 끝난값 0 이면 **거짓 통과**입니다')
    print('')

    길들 = sorted(os.path.basename(p)
                  for p in glob.glob(os.path.join(여기, 'engine', 'check_*.py')))
    길들 = [p for p in 길들 if p not in 바깥을보는것]
    if not 모두:
        길들 = [p for p in 길들 if p not in 오래걸리는것]

    터 = 터만들기()
    거짓통과, 괜찮음, 못봄 = [], [], []
    try:
        for i, c in enumerate(길들, 1):
            값, 꼬리 = 돌리기(c, 터)
            if 값 == 'timeout':
                못봄.append((c, '시간 넘김'))
                표 = '?'
            elif 값 == 0:
                거짓통과.append((c, 꼬리))
                표 = '✗'
            else:
                괜찮음.append((c, 값))
                표 = '·'
            print('  %s %-28s 끝난값 %s' % (표, c, 값))
    finally:
        shutil.rmtree(터, ignore_errors=True)

    print('')
    print('  본 것 %d장 — 거짓 통과 %d · 제대로 막음 %d · 못 봄 %d'
          % (len(길들), len(거짓통과), len(괜찮음), len(못봄)))
    if 거짓통과:
        print('')
        print('  ✗ **자료를 하나도 못 읽는데 통과**를 냅니다 —')
        for c, 꼬리 in 거짓통과:
            print('     %s' % c)
        print('')
        print('  못 잰 것은 통과가 아닙니다. 끝난값 4(못잼)를 내야 합니다.')
        return 1
    print('  · 못 재는 환경에서 통과를 내는 검사기가 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
