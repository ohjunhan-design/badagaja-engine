# -*- coding: utf-8 -*-
"""옛 주소 434개가 **각각 어떻게 됐는지** 표로 냅니다. (검수 지시 11)

★ 왜 표가 필요한가 (2026-09-27 바깥 검수 지시)

    「434개의 URL 이 전부 갈 곳이 있다」와
      「434페이지가 416페이지로 정확히 이관됐다」는 서로 다른
      이야기입니다. 특히 SEO 에서는 페이지 수 감소 자체가
      문제라기보다 **그 18개가 무엇인지 모르는 게 문제**입니다」

    맞습니다. check_urls.py 는 「갈 곳 없음 0」만 말합니다.
    그것으로는 **무엇이 사라졌는지** 모릅니다.

각 옛 주소는 반드시 넷 중 하나입니다
    그대로       같은 주소로 새 틀이 만듭니다
    옛것을남김   새 틀이 안 만들지만 서버에 그대로 둡니다 (keep.json)
    아직안만듦   나중에 만들 쪽 (url-map.json)
    일부러없앰   두지 않기로 한 쪽 — 까닭을 적습니다

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/url_table.py              간추려 봅니다
    python engine/url_table.py --list       434개를 모두 봅니다
    python engine/url_table.py --write      data-private/ 에 표를 씁니다
"""
import os
import re
import sys
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

건너뛸것 = ('cloud/', 'data-private/', 'zh-tw/', '_preview/', 'zh-cn/')

막음, 알림 = [], []


def 옛주소들():
    나옴 = set()
    for p in (glob.glob(os.path.join(OLD, '*.html'))
              + glob.glob(os.path.join(OLD, '*', '*.html'))
              + glob.glob(os.path.join(OLD, '*', '*', '*.html'))):
        q = os.path.relpath(p, OLD).replace(os.sep, '/')
        if q.startswith(건너뛸것):
            continue
        나옴.add(q)
    return 나옴


def 새주소들():
    # 쪽은 io.쪽들() 한 곳에서 모읍니다 (2026-10-06)
    return set(os.path.relpath(p, NEW).replace(os.sep, '/')
               for p in io.쪽들(NEW))


def main():
    다보기 = '--list' in sys.argv
    쓰기 = '--write' in sys.argv

    옛 = 옛주소들()
    새 = 새주소들()
    넘김표 = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    남길표 = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))

    넘김 = 넘김표.get('넘김') or {}
    아직 = set((넘김표.get('아직_안_만듦') or {}).get('쪽') or [])
    없앰 = (넘김표.get('일부러_없앰') or {}).get('쪽') or {}
    남길것 = set(k for k in (남길표.get('남길것') or {}) if not k.startswith('_'))
    남길까닭 = 남길표.get('남길것') or {}

    # 폴더로 적은 것도 알아봅니다
    def 남기나(길):
        if 길 in 남길것:
            return 길
        for k in 남길것:
            if k.endswith('/') and 길.startswith(k):
                return k
        return None

    표 = []
    for 옛길 in sorted(옛):
        if 옛길 in 새:
            표.append((옛길, '그대로', 옛길, '새 틀이 같은 주소로 만듭니다'))
        elif 넘김.get(옛길) in 새:
            표.append((옛길, '넘김', 넘김[옛길], '새 주소로 보냅니다'))
        elif 남기나(옛길):
            k = 남기나(옛길)
            표.append((옛길, '옛것을남김', 옛길,
                       남길까닭.get(k, '서버에 그대로 둡니다')))
        elif 옛길 in 아직:
            표.append((옛길, '아직안만듦', '-',
                       '나중에 만들 쪽 (url-map.json)'))
        elif 옛길 in 없앰:
            표.append((옛길, '일부러없앰', '-', 없앰[옛길]))
        else:
            표.append((옛길, '갈곳없음', '-',
                       '★ 어디에도 안 적혀 있습니다 — 404 가 됩니다'))

    셈 = collections.Counter(x[1] for x in 표)
    print('옛 주소가 각각 어떻게 됐는가 (검수 지시 11)')
    print('  옛 한국어 쪽 %d개 · 새 쪽 %d개' % (len(옛), len(새)))
    print('')
    print('  %-14s %5s' % ('어떻게', '몇 개'))
    print('  ' + '─' * 26)
    for 갈래 in ('그대로', '넘김', '옛것을남김', '아직안만듦',
                 '일부러없앰', '갈곳없음'):
        if 셈.get(갈래):
            print('  %-14s %5d' % (갈래, 셈[갈래]))
    print('  ' + '─' * 26)
    print('  %-14s %5d' % ('합계', sum(셈.values())))
    맞나 = (sum(셈.values()) == len(옛))
    print('  검산  %d = %d %s'
          % (sum(셈.values()), len(옛), '·' if 맞나 else '✗ 안 맞습니다'))
    if not 맞나:
        막음.append('표 합계가 옛 주소 수와 다릅니다')
    print('')

    # ★ 줄어든 만큼이 무엇인지 (검수가 물은 것)
    줄어든것 = [x for x in 표 if x[1] != '그대로']
    print('[줄어든 %d개가 무엇인가]' % len(줄어든것))
    if not 줄어든것:
        print('  · 모든 옛 주소가 같은 자리에 그대로 있습니다')
    else:
        갈래별 = collections.defaultdict(list)
        for x in 줄어든것:
            갈래별[x[1]].append(x)
        for 갈래, 것들 in sorted(갈래별.items()):
            print('')
            print('  ▸ %s — %d개' % (갈래, len(것들)))
            보일수 = len(것들) if 다보기 else 6
            for 옛길, _, 새길, 까닭 in 것들[:보일수]:
                print('      %-38s → %-22s %s'
                      % (옛길, 새길, 까닭[:34]))
            if len(것들) > 보일수:
                print('      … 그 밖 %d개 (--list 로 다 봅니다)'
                      % (len(것들) - 보일수))
    print('')

    갈곳없음 = [x for x in 표 if x[1] == '갈곳없음']
    if 갈곳없음:
        막음.append('갈 곳 없는 옛 주소 %d개' % len(갈곳없음))
        print('★ 갈 곳 없는 옛 주소 %d개 — 404 가 됩니다' % len(갈곳없음))
        for x in 갈곳없음[:8]:
            print('    %s' % x[0])
        print('')

    if 쓰기:
        # ★ 근거 자료는 웹에 안 냅니다 (주인 규칙 11)
        나갈곳 = os.path.join(OLD, 'data-private', '주소이관표.md')
        줄 = ['# 옛 주소 %d개가 각각 어떻게 됐는가' % len(옛),
              '',
              '바깥 검수 지시 11 — 「434개의 URL 이 전부 갈 곳이 있다」와',
              '「434페이지가 416페이지로 정확히 이관됐다」는 다릅니다.',
              '',
              '`engine/url_table.py` 가 만듭니다. 손으로 고치지 마세요.',
              '']
        for 갈래 in ('그대로', '넘김', '옛것을남김', '아직안만듦',
                     '일부러없앰', '갈곳없음'):
            것들 = [x for x in 표 if x[1] == 갈래]
            if not 것들:
                continue
            줄.append('')
            줄.append('## %s — %d개' % (갈래, len(것들)))
            줄.append('')
            줄.append('| 옛 주소 | 새 주소 | 까닭 |')
            줄.append('|---|---|---|')
            for 옛길, _, 새길, 까닭 in 것들:
                줄.append('| %s | %s | %s |' % (옛길, 새길, 까닭))
        io.write(나갈곳, '\n'.join(줄) + '\n')
        print('표를 썼습니다: data-private/주소이관표.md')
        print('  (근거 자료라 웹에 안 냅니다 — 주인 규칙 11)')
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0
    print('옛 주소 %d개가 모두 어떻게 됐는지 적혀 있습니다.' % len(옛))
    return 0


if __name__ == '__main__':
    sys.exit(main())
