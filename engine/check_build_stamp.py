# -*- coding: utf-8 -*-
"""**모든 쪽이 같은 판을 밝히고 있는가** (2026-10-07 주인 지시).

★ 왜 만들었나
  주인 —
    「지피티가 자꾸 **옛판을 본다**고 하는데 그건 **구조적인 문제**가
      있다는 소리야. 누가 보든지 **새 판**을 보고 판단해야 하는데
      첫번째를 본다는 소리는 **사이트 구조에 문제점이 있다**는 소리고,
      그건 아직 **잔재가 많이 남아 있다**는 소리야」

  실제로 그랬습니다. 바깥 검수가 「기준일 26년 9월」을 보고 옛 판이라
  판단했는데, 그건 **자료의 기준일**이지 판이 아니었습니다. 쪽 어디에도
  **「이 쪽이 어느 판인가」가 적혀 있지 않아** 엉뚱한 단서로 짐작한 것입니다.

★ 바깥 검수가 정한 **세 층**
      사람이 보는 것   꼬리말 「사이트 업데이트 2026.10.07」
      검수기가 보는 것  <meta name="badagaja-build" content="400c262">
      상세 확인        /build.json

  그리고 — 「**모든 새 HTML 이 같은 build id 를 가져야 합니다.**
            일부 쪽이 옛 id 면 그 자체로 **배포 혼재를 잡아냅니다**」

검사 등급 (계약-21)
  막음 — 지문이 없거나 **값이 갈립니다**. 고쳐야 합니다
  알림 — 꼬리말 사람용 표시가 빠진 쪽
"""
import io
import os
import re
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402
_지문 = re.compile(r'name="badagaja-build"\s+content="([^"]*)"')
_날짜 = re.compile(r'name="badagaja-build-date"\s+content="([^"]*)"')
_사람 = re.compile(r'사이트 업데이트\s*([0-9.]+)')

막음, 알림 = [], []


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('모든 쪽이 **같은 판**을 밝히고 있는가')

    밭 = os.path.join(ROOT, 'site')
    if not os.path.isdir(밭):
        print('  ~ site/ 가 없습니다 — 먼저 만들어야 잽니다')
        return 0

    쪽들 = []
    for 뿌, _, 들 in os.walk(밭):
        for 이름 in 들:
            if 이름.endswith('.html'):
                쪽들.append(os.path.join(뿌, 이름))
    # ★ 쪽이 0개면 **안 재고 통과**였습니다 (2026-10-08 실측)
    mustmeasure.있어야한다(쪽들, '쪽', 최소=50, 어디=밭)

    읽은쪽 = 0
    없는것, 판별 = [], {}
    날짜별, 사람없음 = {}, []
    for 길 in 쪽들:
        쪽 = os.path.relpath(길, 밭).replace(os.sep, '/')
        try:
            글 = io.open(길, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        읽은쪽 += 1
        m = _지문.search(글)
        if not m or not m.group(1).strip():
            없는것.append(쪽)
        else:
            판별.setdefault(m.group(1), []).append(쪽)
        d = _날짜.search(글)
        if d and d.group(1).strip():
            날짜별.setdefault(d.group(1), 0)
            날짜별[d.group(1)] += 1
        if not _사람.search(글):
            사람없음.append(쪽)
    # ★ 목록은 있는데 **내용을 하나도 못 읽으면** 역시 못잼입니다
    mustmeasure.있어야한다(range(읽은쪽), '읽은 쪽', 최소=50, 어디=밭)

    print('')
    print('[1] 쪽마다 판 지문이 있는가')
    print('      쪽 %d개' % len(쪽들))
    if 없는것:
        막음.append('판 지문이 없는 쪽 %d개' % len(없는것))
        print('  ✗ 지문이 없는 쪽 %d개 — %s%s'
              % (len(없는것), ' · '.join(없는것[:4]),
                 ' …' if len(없는것) > 4 else ''))
        print('      → 보는 사람이 **엉뚱한 단서로 최신 여부를 짐작**하게 됩니다.')
    else:
        print('  · 모든 쪽이 자기 판을 밝힙니다')

    print('')
    print('[2] 판 값이 **하나로 같은가** (갈리면 배포가 섞인 것입니다)')
    if len(판별) > 1:
        막음.append('판 값이 %d갈래로 갈립니다' % len(판별))
        print('  ✗ 판이 %d갈래입니다 — **배포가 섞였습니다**' % len(판별))
        for k in sorted(판별, key=lambda a: -len(판별[a])):
            print('      %-12s %4d쪽   %s' % (k, len(판별[k]), 판별[k][0]))
        print('      → 일부만 올라갔거나, 올리다 끊긴 것입니다.')
    elif 판별:
        k = list(판별)[0]
        print('  · 쪽 %d개가 모두 같은 판입니다 — %s' % (len(판별[k]), k))

    print('')
    print('[3] 사람이 보는 표시도 있는가')
    if 사람없음:
        알림.append('꼬리말 표시가 없는 쪽 %d개' % len(사람없음))
        print('  ~ 「사이트 업데이트 …」가 없는 쪽 %d개' % len(사람없음))
    else:
        print('  · 모든 쪽에 「사이트 업데이트 …」가 있습니다')
    if 날짜별:
        print('      날짜 %s' % ' · '.join('%s(%d쪽)' % (k, v)
                                           for k, v in 날짜별.items()))

    print('')
    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **누가 보든 새 판을 보고 판단해야 합니다.**')
        print('    지문이 없거나 갈리면, 보는 사람이 옛 것을 보고')
        print('    옛 것으로 판단합니다 (2026-10-07 주인 지시).')
        return 1
    print('모든 쪽이 같은 판을 밝히고 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
