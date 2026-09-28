# -*- coding: utf-8 -*-
"""**못 잰 것이 PASS 로 안 나오는지** 증명합니다. (검수 지시 3)

★ 왜 이 시험이 따로 필요한가 (2026-09-27 바깥 검수 지시)

    「검사기가 측정 실패를 PASS 로 바꾸는 일이 다시 발생하지 않도록
      한다. 의도적으로 측정 실패를 발생시켰을 때 PASS 가 나오면
      안 된다. 즉 **측정 실패 ≠ PASS** 가 자동 테스트로 증명되어야
      한다」

    제가 이 실수를 **세 번** 했습니다.

        · 광고가 하나도 안 떴는데 「멀쩡합니다」로 통과
        · 12건 전부 측정 실패인데 통과
        · 잴 것이 없는데 「제대로 되어 있습니다」로 통과

    셋 다 같은 성질입니다 — **안 잰 것을 통과로 세는 것.**
    발견할 때마다 고치는 식으로는 또 생깁니다.
    그래서 **일부러 못 재게 만들어 놓고** 통과가 나오는지 봅니다.

어떻게 보나
    검사기가 기대는 것을 하나씩 없앱니다.
      · 볼 쪽이 없을 때
      · 자료가 없을 때
      · 크롬을 못 찾을 때
      · 시간이 넘을 때
    그때 검사기가 **0(통과)으로 끝나면 안 됩니다.**

    「막지 않는 검사」(계약-21 의 알림)는 0 으로 끝나도 됩니다.
    다만 그때도 **「멀쩡하다」고 말하면 안 됩니다.**

쓰는 법
    python tests/test_not_tested.py
"""
import os
import re
import sys
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

통과, 실패 = 0, []

# 「다 잘됐다」는 뜻의 말들 — 못 쟀을 때 나오면 안 됩니다
통과하는말 = (
    '이상 없음', '멀쩡합니다', '탈이 없습니다', '모두 지킵니다',
    '모두 통과', '제대로 그 언어입니다', '모두 갈 곳이 있습니다',
    '길이 모두 이어집니다', '제대로 뜹니다', '하나입니다',
    '끝까지 다듬어져 있습니다', '모두 있습니다',
)


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s' % 이름)
        if 덧:
            for 줄 in str(덧).strip().split('\n')[-4:]:
                print('      %s' % 줄)


def 돌리기(도구, 사이트=None, 자료=None, 인자=(), 길막기=False):
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    if 사이트:
        환경['BADAGAJA_SITE'] = 사이트
    if 자료:
        환경['BADAGAJA_DATA'] = 자료
    if 길막기:
        # ★ 크롬을 못 찾게 만듭니다 (2026-09-27)
        #   PATH 를 비우는 것으로는 모자랍니다 — 검사기가 크롬 자리를
        #   절대 경로로 알고 있기 때문입니다. 그래서 검사기가 보는
        #   BADAGAJA_CHROME 에 **없는 자리**를 줍니다.
        환경['BADAGAJA_CHROME'] = os.path.join(
            ROOT, '없는자리', 'chrome.exe')
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'engine', 도구)] + list(인자),
        capture_output=True, text=True, encoding='utf-8',
        env=환경, timeout=900)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def 통과라고했나(글):
    return any(x in 글 for x in 통과하는말)


def 빈자리():
    t = tempfile.mkdtemp(prefix='nottested-')
    os.makedirs(os.path.join(t, 'site'), exist_ok=True)
    return t, os.path.join(t, 'site')


def 시험_볼쪽이없을때():
    """쪽이 하나도 없으면 「멀쩡하다」고 하면 안 됩니다."""
    print('[1] 볼 쪽이 하나도 없을 때')
    도구들 = ('check_links.py', 'check_seo.py', 'check_ads.py',
              'check_assets.py', 'check_canonical.py', 'check_console.py',
              'check_render.py', 'check_i18n.py')
    for 도구 in 도구들:
        t, 빈곳 = 빈자리()
        try:
            코드, 글 = 돌리기(도구, 사이트=빈곳, 인자=['--strict'])
            나쁜가 = (코드 == 0 and 통과라고했나(글))
            봄('%-22s 빈 사이트를 통과시키지 않는다' % 도구,
               not 나쁜가, 글[-300:])
        finally:
            shutil.rmtree(t, ignore_errors=True)
    print('')


def 시험_자료가없을때():
    """자료가 없으면 「지킨다」고 하면 안 됩니다."""
    print('[2] 자료가 하나도 없을 때')
    도구들 = ('check_stale.py', 'check_keep.py', 'check_refresh.py',
              'check_urls.py')
    for 도구 in 도구들:
        t = tempfile.mkdtemp(prefix='nottested-')
        빈자료 = os.path.join(t, 'data')
        os.makedirs(os.path.join(빈자료, 'raw'), exist_ok=True)
        try:
            코드, 글 = 돌리기(도구, 자료=빈자료, 인자=['--strict'])
            나쁜가 = (코드 == 0 and 통과라고했나(글))
            봄('%-22s 빈 자료를 통과시키지 않는다' % 도구,
               not 나쁜가, 글[-300:])
        finally:
            shutil.rmtree(t, ignore_errors=True)
    print('')


def 시험_판정도구():
    """gate.py 가 못 잰 것을 PASS 로 세지 않는가.

    ★ gate 가 나를 부른 것이면 건너뜁니다 (2026-09-27)
        gate → 이 시험 → gate → 이 시험 … 끝이 없습니다.
        gate 가 BADAGAJA_GATE 를 남기므로 그때는 안 돌립니다.
        **건너뛴 것은 「통과」가 아닙니다** — 그렇다고 적습니다.
    """
    print('[3] 판정 도구가 못 잰 것을 PASS 로 세는가')
    if os.environ.get('BADAGAJA_GATE'):
        print('  ~ gate 가 부른 것이라 건너뜁니다 (고리를 끊습니다)')
        print('    gate → 이 시험 → gate … 로 끝이 없어집니다')
        print('    따로 돌리면 잽니다: python tests/test_not_tested.py')
        print('')
        return
    # ★ **빈 사이트**에 대고 돌립니다 (2026-09-27 — 속도)
    #   여기서 보려는 것은 「gate 가 검산을 내고, 못 잰 것이 있으면
    #   NO-GO 라고 하는가」입니다. 진짜 사이트를 다시 잴 까닭이
    #   없습니다. 전에는 gate 를 통째로 돌려 **4분 넘게** 걸렸고,
    #   그 안에서 이 시험을 또 불러 고리까지 생겼습니다.
    #
    #   빈 사이트면 검사기들이 곧바로 넘어져, 오히려
    #   「못 잰 것이 있을 때 NO-GO 인가」를 더 또렷이 봅니다.
    t = tempfile.mkdtemp(prefix='nottested-gate-')
    빈곳 = os.path.join(t, 'site')
    os.makedirs(빈곳, exist_ok=True)
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_SITE'] = 빈곳
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'engine',
                                                         'gate.py')],
                           capture_output=True, text=True, encoding='utf-8',
                           env=환경, timeout=600)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    글 = (r.stdout or '') + (r.stderr or '')

    # 검산이 반드시 나와야 합니다
    m = re.search(r'검산\s+(\d+) \+ (\d+) \+ (\d+) \+ (\d+) = (\d+) (=|≠) (\d+)',
                  글)
    봄('검산을 스스로 냅니다', bool(m), 글[-300:])
    if m:
        합 = sum(int(m.group(i)) for i in (1, 2, 3, 4))
        봄('검산이 맞습니다', 합 == int(m.group(7)) and m.group(6) == '=',
           m.group(0))

    # NOT_TESTED 가 하나라도 있으면 NO-GO 여야 합니다
    안잰것 = re.search(r'NOT_TESTED\s+(\d+)', 글)
    if 안잰것 and int(안잰것.group(1)) > 0:
        봄('못 잰 것이 있으면 NO-GO 라고 합니다',
           'NO-GO' in 글, 글[-300:])
        봄('못 잰 것이 있으면 0 이 아닌 값으로 끝납니다',
           r.returncode != 0, '끝난값 %d' % r.returncode)
    else:
        봄('못 잰 것이 없으면 GO 후보라고 합니다',
           'GO 후보' in 글, 글[-300:])

    # 「PASS 6」 같은 말이 나오는데 표에 없는 항목이 있으면 안 됩니다
    표항목 = len(re.findall(r'^  [·✗?-] \d+ ', 글, re.M))
    총 = re.search(r'TOTAL\s+(\d+)', 글)
    봄('표에 적은 항목 수가 TOTAL 과 같습니다',
       bool(총) and 표항목 == int(총.group(1)),
       '표 %d개 · TOTAL %s' % (표항목, 총.group(1) if 총 else '?'))
    print('')


def 시험_크롬을못찾을때():
    """브라우저를 못 찾으면 통과시키면 안 됩니다."""
    print('[4] 브라우저를 못 찾을 때')
    # ★ 한 쪽만 재도 충분합니다 (2026-09-27 — 속도)
    #   전에는 check_render 가 416쪽을 다 시도해 10분 넘게 걸렸습니다.
    #   크롬이 없으면 첫 쪽에서 이미 드러납니다.
    한쪽 = os.path.join(ROOT, 'site', 'index.html')
    for 도구, 인자 in (('check_render.py', [한쪽, '--strict']),
                       ('check_ads.py', ['--strict']),
                       ('check_console.py', ['--strict'])):
        코드, 글 = 돌리기(도구, 인자=인자, 길막기=True)
        # 크롬을 못 찾으면 넘어지거나(0 아님) 「못 쟀다」고 해야 합니다
        나쁜가 = (코드 == 0 and 통과라고했나(글))
        봄('%-22s 브라우저가 없으면 통과시키지 않는다' % 도구,
           not 나쁜가, 글[-300:])
    print('')


def main():
    print('못 잰 것이 PASS 로 안 나오는지 (검수 지시 3)')
    print('')
    시험_볼쪽이없을때()
    시험_자료가없을때()
    시험_판정도구()
    시험_크롬을못찾을때()

    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 안 잰 것을 통과로 세면, 검사가 있는 것이')
        print('    없는 것보다 나쁩니다 — 믿어 버리기 때문입니다.')
        return 1
    print('%d가지 모두 통과 — 못 잰 것은 통과가 되지 않습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
