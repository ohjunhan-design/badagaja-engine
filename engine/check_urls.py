# -*- coding: utf-8 -*-
"""옛 주소가 새 사이트에서 어떻게 되는지 **하나도 빠짐없이** 봅니다.

★ 왜 이 검사가 따로 필요한가 (2026-09-26, 바깥 검수에서 지적받음)

    「쪽 416개 · 전수 대조 손볼 곳 0」이라고 보고했습니다.
    그런데 옛 사이트는 434쪽입니다. 18쪽이 준 것처럼 보였지만
    실제로는 **139쪽이 사라지고 121쪽이 새로 생긴** 것이었습니다.

    compare_page.py 는 「짝이 있는 쪽」만 견줍니다.
    짝이 아예 없는 쪽은 견줄 것이 없으니 조용히 넘어갑니다.
    그래서 「손볼 곳 0」이 나왔습니다. **없는 것을 못 본 것입니다.**

    옛 주소는 이미 검색엔진에 올라가 있고 손님이 즐겨찾기 해 두었습니다.
    주소가 사라지면 그 자리는 404 가 되고, 쌓아 둔 검색 순위가 날아갑니다.

무엇을 보나
    1. 옛 주소마다 — 새 주소가 있는가 / 넘김(리다이렉트)이 있는가 /
                     일부러 없앤 것인가
    2. 넘김 표(data/raw/url-map.json)가 실제로 맞는가
    3. 새 주소가 제 자리를 가리키는가 (canonical)

「일부러 없앤 것」은 자료에 적어 두어야 합니다. 적지 않으면 실수입니다.

쓰는 법
    python engine/check_urls.py
    python engine/check_urls.py --strict

★ 이 도구는 **읽기만 합니다** (계약-09)
    넘김 표(url-map.json)는 사람이 정해 손으로 적습니다.
    검사가 자료를 고치기 시작하면, 잘못된 자료를 스스로 「맞다」고
    적어 놓고 통과시킬 수 있습니다.
"""
import os
import re
import sys
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, url   # noqa: E402
from engine import pages     # noqa: E402  주소의 갈래는 pages.py 한 곳에서만
from engine.data import 자료   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 옛 사이트에서 배포 대상이 아닌 폴더
건너뛸것 = ('cloud/', 'data-private/', 'zh-tw/', '_preview/')

막음, 알림 = [], []


def 옛주소들(중국어=False):
    """옛 사이트의 한국어 쪽 주소 (중국어는 따로)"""
    나옴 = set()
    for p in (glob.glob(os.path.join(OLD, '*.html'))
              + glob.glob(os.path.join(OLD, '*', '*.html'))
              + glob.glob(os.path.join(OLD, '*', '*', '*.html'))):
        q = os.path.relpath(p, OLD).replace('\\', '/')
        if q.startswith(건너뛸것):
            continue
        if q.startswith('zh-cn/') != 중국어:
            continue
        나옴.add(q)
    return 나옴


def 새주소들():
    나옴 = set()
    # 쪽은 io.쪽들() 한 곳에서 모읍니다 — 재는 동안 남은
    # `__` 자국을 진짜 쪽으로 세면 헛 FAIL 이 납니다 (2026-10-06)
    for p in io.쪽들(NEW):
        나옴.add(os.path.relpath(p, NEW).replace('\\', '/'))
    return 나옴


def 넘김표():
    """옛 주소 → 새 주소, 그리고 「아직 안 만듦」·「일부러 없앰」.

    ★ 셋을 갈라 봐야 합니다 (2026-09-26 바깥 검수 지적)
        넘김        새 주소로 보냅니다
        아직 안 만듦  사라진 것이 아니라 순서상 나중입니다
        일부러 없앰   두지 않기로 한 것입니다 — 이유를 적습니다

      이 셋을 뭉뚱그리면 「404 가 될 쪽」과 「곧 만들 쪽」이 섞여
      무엇이 진짜 문제인지 안 보입니다.
    """
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    넘김 = d.get('넘김', {})
    아직 = set((d.get('아직_안_만듦') or {}).get('쪽') or [])
    없앰 = set((d.get('일부러_없앰') or {}).get('쪽') or {})
    return 넘김, 아직, 없앰


def main():
    d = 자료()
    옛 = 옛주소들()
    새 = 새주소들()
    넘김, 아직, 없앰 = 넘김표()
    # ★ keep.json 의 「남긴 옛 쪽」 — 서버에 그대로 있어 404 가 안 납니다
    #   (2026-09-27 — 이 검사기만 keep.json 을 안 읽어 travel/index.html
    #    을 「갈 곳 없음」으로 세었습니다. check_assets 는 통과시켰습니다)
    남긴것 = pages.남긴옛쪽들()

    print('옛 주소가 새 사이트에서 어떻게 되는지')
    print('  옛 %d쪽 · 새 %d쪽' % (len(옛), len(새)))
    print('')

    # ── 1. 옛 주소마다 갈 곳이 있는가
    print('[1] 옛 주소가 갈 곳')
    그대로 = 옛 & 새
    사라짐 = sorted(옛 - 새)
    갈곳있음, 갈곳없음, 없애기로, 아직것, 남긴것들 = [], [], [], [], []
    for 옛길 in 사라짐:
        if 옛길 in 남긴것:
            남긴것들.append(옛길)
        elif 옛길 in 없앰:
            없애기로.append(옛길)
        elif 옛길 in 아직:
            아직것.append(옛길)
        elif 넘김.get(옛길) in 새:
            갈곳있음.append(옛길)
        else:
            갈곳없음.append(옛길)

    print('      주소 그대로        %4d쪽' % len(그대로))
    print('      넘김 표가 있음      %4d쪽' % len(갈곳있음))
    print('      아직 안 만든 쪽     %4d쪽' % len(아직것))
    print('      일부러 남긴 옛 쪽    %4d쪽' % len(남긴것들))
    print('      일부러 없앤 것      %4d쪽' % len(없애기로))
    print('      갈 곳이 없음        %4d쪽' % len(갈곳없음))

    if 갈곳없음:
        막음.append('갈 곳 없는 옛 주소 %d쪽' % len(갈곳없음))
        print('  ✗ 갈 곳이 없는 옛 주소 %d쪽 — 404 가 됩니다' % len(갈곳없음))
        c = collections.Counter(
            x.split('/')[0] if '/' in x else '(루트)' for x in 갈곳없음)
        for k, v in c.most_common(8):
            보기 = [y for y in 갈곳없음
                    if (y.split('/')[0] if '/' in y else '(루트)') == k][:2]
            print('      %-12s %3d쪽   %s' % (k, v, ' · '.join(보기)))
    else:
        print('  · 갈 곳 없는 옛 주소가 없습니다')
    if 아직것:
        알림.append('아직 안 만든 쪽 %d개' % len(아직것))
        print('  ~ 아직 안 만든 쪽 %d개 — 만들면 url-map.json 에서 빼세요'
              % len(아직것))
        print('      %s' % ' · '.join(아직것[:4]))
    print('')

    # 아직 안 만들기로 적어 놓고 이미 만든 것 — 목록을 안 치운 것입니다
    이미만듦 = sorted(아직 & 새)
    if 이미만듦:
        알림.append('만들었는데 목록에 남은 쪽 %d개' % len(이미만듦))
        print('  ~ 이미 만들었는데 「아직 안 만듦」에 남아 있습니다 %d개: %s'
              % (len(이미만듦), ' · '.join(이미만듦[:3])))
        print('')

    # ── 2. 새로 생긴 주소
    print('[2] 새로 생긴 주소')
    새것 = sorted(새 - 옛)
    print('      %d쪽' % len(새것))
    if 새것:
        c = collections.Counter(
            x.split('/')[0] if '/' in x else '(루트)' for x in 새것)
        for k, v in c.most_common(6):
            print('      %-12s %3d쪽' % (k, v))
        print('    (넘김 표가 가리키는 곳이면 정상입니다)')
    print('')

    # ── 3. 넘김 표가 맞는가
    print('[3] 넘김 표')
    없는옛것 = [k for k in 넘김 if k not in 옛]
    없는새것 = [v for v in 넘김.values() if v not in 새]
    돌아가는것 = [k for k, v in 넘김.items() if v in 넘김]
    print('      적힌 넘김 %d개' % len(넘김))
    if 없는옛것:
        알림.append('넘김 표에 옛 사이트에 없는 주소 %d개' % len(없는옛것))
        print('  ~ 옛 사이트에 없는 주소를 적어 두었습니다 %d개: %s'
              % (len(없는옛것), ' · '.join(없는옛것[:3])))
    if 없는새것:
        막음.append('넘김이 없는 쪽을 가리킴 %d개' % len(없는새것))
        print('  ✗ 없는 쪽으로 넘기고 있습니다 %d개: %s'
              % (len(없는새것), ' · '.join(없는새것[:3])))
    if 돌아가는것:
        막음.append('넘김이 또 넘김을 가리킴 %d개' % len(돌아가는것))
        print('  ✗ 넘긴 곳이 또 넘김입니다 %d개 — 한 번에 가야 합니다: %s'
              % (len(돌아가는것), ' · '.join(돌아가는것[:3])))
    if not (없는옛것 or 없는새것 or 돌아가는것):
        print('  · 넘김 표에 탈이 없습니다')
    print('')

    # ── 4. 새 쪽이 제 주소를 가리키는가
    print('[4] 새 쪽의 canonical')
    틀린것 = []
    본것 = 0
    for 길 in sorted(새):
        s = io.read(os.path.join(NEW, 길), default='')
        m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not m:
            틀린것.append('%s — canonical 이 없음' % 길)
            continue
        본것 += 1
        바람 = url.full(길)
        if m.group(1) != 바람:
            틀린것.append('%s → %s (있어야 할 것 %s)' % (길, m.group(1), 바람))
    print('      본 쪽 %d개' % 본것)
    if 틀린것:
        막음.append('canonical 이 틀림 %d쪽' % len(틀린것))
        print('  ✗ canonical 이 제 주소가 아닌 쪽 %d개' % len(틀린것))
        for x in 틀린것[:3]:
            print('      %s' % x)
    else:
        print('  · 모든 쪽이 제 주소를 가리킵니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  data/raw/url-map.json 에 갈 곳을 적어 주세요.')
        return 1 if '--strict' in sys.argv else 0
    print('옛 주소가 모두 갈 곳이 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
