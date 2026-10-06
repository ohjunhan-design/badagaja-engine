# -*- coding: utf-8 -*-
"""**달이 바뀌면 틀어질 것**을 미리 찾습니다. (2026-09-27 주인 지시)

★ 왜 이 검사가 필요한가

    「이제 곧 10월이니까 변경되는 것들 잘 확인할 수 있게 해주고
      축제나 어종등도 월이 변경될경우 정보변경에도 각별히 신경써줘
      자동화가 핵심이야」                        (주인, 2026-09-27)

    사이트에는 두 가지 「달」이 섞여 있습니다.

        안 바뀌는 달   「감성돔 4월 – 10월」  ← 제철. 해가 바뀌어도 같습니다
        바뀌는 달     「이 자료는 9월 기준」  ← 10월이 되면 **거짓말**이 됩니다
                      「이달의 축제」        ← 10월에는 10월 것이어야 합니다

    둘을 가려내지 못하면, 달이 바뀔 때마다 사람이 500여 쪽을 뒤져야
    합니다. 그러다 한 번 잊으면 손님이 틀린 것을 봅니다.

무엇을 보나
    1. 쪽에 박힌 「○년 ○월 기준」이 자료를 고친 달과 맞는가
    2. 「이달」에 기대는 것이 **화면에서** 정해지는가
       (쪽에 박혀 있으면 달이 바뀔 때 다시 만들어야 합니다)
    3. 지난 축제가 「예정」처럼 보이지 않는가
    4. 쪽을 다시 만들지 않고 달을 넘겨도 되는가

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_calendar.py
    python engine/check_calendar.py --next     다음 달로 넘어간 척하고 봅니다
    python engine/check_calendar.py --strict
"""
import os
import re
import sys
import glob
import datetime
import subprocess
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine.data import 자료   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []


def 글자만(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def 자료고친달(무늬):
    """그 자료를 마지막으로 고친 달 — git 에서."""
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cI', '--', 무늬],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=30)
        s = (r.stdout or '').strip()
        if s:
            return '%s년 %d월' % (s[:4], int(s[5:7]))
    except (OSError, ValueError):
        pass
    return None


def 다음달(오늘=None):
    오늘 = 오늘 or datetime.date.today()
    return (오늘.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)


def main():
    앞으로 = '--next' in sys.argv
    오늘 = datetime.date.today()
    볼날 = 다음달(오늘) if 앞으로 else 오늘
    d = 자료()

    print('달이 바뀌면 틀어질 것 (주인 지시 2026-09-27)')
    print('  오늘 %s%s' % (오늘.isoformat(),
                           '  →  다음 달(%s)로 넘어간 척하고 봅니다'
                           % 볼날.strftime('%Y-%m') if 앞으로 else ''))
    print('')

    쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))

    # ── 1. 「○년 ○월 기준」이 자료를 고친 달과 맞는가
    print('[1] 쪽에 적힌 기준일이 자료와 맞는가')
    # ★ **짧은 꼴도 봅니다** (2026-10-02)
    #   전에는 「이 자료는 2026년 9월 기준입니다」만 찾았습니다.
    #   그런데 주인 지시로 쪽이 「기준일 26년 9월」로 짧아졌고,
    #   그 뒤로 이 검사는 **「기준일을 적은 쪽이 없습니다」**만
    #   내고 있었습니다. 448쪽 모두에 적혀 있는데도요.
    #   잴 것을 못 찾으면 **아무것도 안 지킵니다.**
    #   두 해 표기(2026년 · 26년)를 모두 네 자리로 맞춰 셉니다.
    적힌것 = collections.Counter()
    _주석 = re.compile(r'<!--.*?-->', re.S)
    _긴꼴 = re.compile(r'이 자료는 (\d{4})년 (\d{1,2})월 기준입니다')
    _짧은꼴 = re.compile(r'기준일\s*(\d{2})년\s*(\d{1,2})월')
    for p in 쪽들:
        s = io.read(p, default='')
        # ★ **주석은 손님에게 안 보입니다** (2026-10-06)
        #   449쪽 모두가 「2026년 9월」로 걸렸는데, 그 자리는
        #   코드 주석 안의 **주인 말씀 인용**이었습니다 —
        #       <!-- 주인 지시 「기준일 26년 9월 이렇게만 적어」 -->
        #       <span class="header-asof">기준일 26년 10월</span>
        #   화면에는 10월만 보입니다. 주석을 세면 **멀쩡한 쪽을
        #   틀렸다고 합니다.** 쪽이 무엇을 보여 주는지 재는
        #   검사이니, 보이지 않는 글자는 빼고 셉니다.
        s = _주석 .sub('', s)
        for m in _긴꼴.finditer(s):
            적힌것['%s년 %s월' % (m.group(1), int(m.group(2)))] += 1
        for m in _짧은꼴.finditer(s):
            해 = 2000 + int(m.group(1))
            적힌것['%d년 %d월' % (해, int(m.group(2)))] += 1
    진짜 = 자료고친달('data/raw/points') or '알 수 없음'
    print('      자료를 마지막으로 고친 달   %s' % 진짜)
    for 값, 수 in 적힌것.most_common():
        맞나 = (값 == 진짜)
        print('      쪽에 적힌 것  %-12s %4d쪽  %s'
              % (값, 수, '·' if 맞나 else '✗ 안 맞음'))
        if not 맞나:
            막음.append('쪽에 적힌 기준일이 자료와 다릅니다 (%s ≠ %s)'
                        % (값, 진짜))
    if not 적힌것:
        알림.append('기준일을 적은 쪽이 없습니다')
        print('      ~ 기준일을 적은 쪽이 없습니다')
    print('')

    # ── 2. 「이달」에 기대는 것이 화면에서 정해지는가
    print('[2] 「이달」을 쪽에 박아 두지 않았는가')
    이달말 = '%d월' % 볼날.month
    지금달말 = '%d월' % 오늘.month
    박힌것 = []
    for p in 쪽들:
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        # 「이달의 축제」처럼 **지금 달**에 기대는 제목만 봅니다.
        #
        # ★ 본문 서술은 봐줍니다 (2026-09-27 헛것을 세 번 냈습니다)
        #   축제 쪽 소개글의 「4월 강진만은 … 동죽도 이달부터 9월까지」는
        #   **그 축제가 열리는 달**을 가리키는 말이지 지금 달이 아닙니다.
        #   탈이 아닌 것을 알리면 검사가 무뎌져 진짜 탈을 놓칩니다.
        for m in re.finditer(r'<(h[1-6]|b|strong)[^>]*>[^<]{0,12}'
                             r'(이번 ?달|이달)[의은는]', s):
            박힌것.append('%s — 「%s」' % (이름, 글자만(m.group(0))[:16]))
            break
        # 「9월 축제」처럼 지금 달이 그대로 박힌 것
        if re.search(r'>[^<]{0,10}%s (축제|어종|물때)' % 지금달말, s):
            박힌것.append('%s — 「%s …」가 박혀 있습니다' % (이름, 지금달말))
    if 박힌것:
        막음.append('「이달」이 쪽에 박힌 곳 %d개' % len(박힌것))
        print('  ✗ %d개 — 달이 바뀌면 다시 만들어야 합니다' % len(박힌것))
        for x in 박힌것[:5]:
            print('      %s' % x)
        print('      → 화면(자바스크립트)에서 정하게 바꾸면')
        print('        쪽을 다시 안 만들어도 저절로 넘어갑니다.')
    else:
        print('  · 「이달」이 박힌 쪽이 없습니다')
    # 화면에서 정하는지 확인
    js = io.read(os.path.join(ROOT, 'assets', 'js', 'festival-list.js'),
                 default='')
    화면이 = 'getMonth' in js
    print('      축제 달력은 %s'
          % ('화면에서 이달을 고릅니다 — 저절로 넘어갑니다' if 화면이
             else '✗ 화면에서 안 고릅니다'))
    if not 화면이:
        막음.append('축제 달력이 화면에서 이달을 안 고릅니다')
    print('')

    # ── 3. 지난 축제가 「예정」처럼 보이는가
    print('[3] 지난 축제가 「곧 열림」처럼 보이지 않는가')
    지난것 = [x for x in d.축제들
              if x.get('달') and int(x['달']) < 볼날.month]
    앞으로것 = [x for x in d.축제들
                if x.get('달') and int(x['달']) >= 볼날.month]
    print('      %d월 기준 — 지난 축제 %d개 · 남은 축제 %d개'
          % (볼날.month, len(지난것), len(앞으로것)))
    # 쪽이 「곧」·「예정」 같은 말을 박아 두었나
    잘못된말 = []
    for x in 지난것[:60]:
        p = os.path.join(NEW, 'festival', '%s.html' % x['id'])
        if not os.path.exists(p):
            continue
        s = io.read(p, default='')
        # ★ **축제를 가리키는 말만 잡습니다** (2026-10-02)
        #   전에는 「다가오」 두 글자만 보고 잡았습니다. 그래서
        #   추자 축제 쪽의 「참돔 철이 **다가오는** 때라」가
        #   걸렸습니다 — 축제가 아니라 **물고기 철** 이야기입니다.
        #   거짓 경보가 나면 사람이 검사기를 안 믿게 됩니다.
        #   「곧 열립니다」처럼 **축제의 때를 말하는 꼴**만 봅니다.
        if re.search(r'곧 (열립|시작|있습)|열릴 예정|개최 예정'
                     r'|(축제|행사|대회)[가는이] 다가', s):
            잘못된말.append('%s (%s월)' % (x['id'], x['달']))
    if 잘못된말:
        막음.append('지난 축제가 「곧 열림」으로 보임 %d개' % len(잘못된말))
        print('  ✗ %d개: %s' % (len(잘못된말), ' · '.join(잘못된말[:4])))
    else:
        print('  · 지난 축제를 「곧 열림」으로 쓰지 않습니다')
    print('')

    # ── 4. 달을 넘겨도 다시 안 만들어도 되는가
    print('[4] 달이 바뀌어도 쪽을 다시 안 만들어도 되는가')
    되는것 = not 박힌것 and 화면이
    print('      %s' % ('· 됩니다 — 달이 바뀌어도 쪽은 그대로여도 됩니다'
                        if 되는것 else
                        '✗ 안 됩니다 — 달이 바뀌면 다시 만들어야 합니다'))
    if 되는것:
        print('      다만 **자료를 고치면** 기준일이 바뀌므로')
        print('      그때는 다시 만들어야 합니다 (engine/build.py --all)')
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
        print('  ★ 달이 바뀔 때마다 사람이 500여 쪽을 뒤지게 두면')
        print('    언젠가 한 번은 잊습니다. 그때 손님이 틀린 것을 봅니다.')
        return 1 if '--strict' in sys.argv else 0
    print('달이 바뀌어도 탈이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
