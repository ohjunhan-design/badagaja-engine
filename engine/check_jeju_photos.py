# -*- coding: utf-8 -*-
"""제주 명소 사진이 **제자리에 붙었는가** 전수로 봅니다 (2026-10-15).

★ 왜 만들었나 (총감독 지시 P0①)
  제주 명소 사진 25장에 `권역`·`쓰임`을 손으로 채웠습니다.
  기존 배정에서 권역 경계를 읽어 넣었지만, **사람이 넣은 값은
  틀릴 수 있습니다.** 특히 표선해비치해변은 근거가 없어
  성산으로 두었습니다.

★ 무엇을 근거로 재나 — **`data/raw/travel/jeju.json`**
  거기에 권역마다 **명소 목록이 이름·주소·좌표와 함께** 있습니다.
  쪽에 나오는 명소도 그것입니다. 그러므로
      사진의 (권역, 쓰임)  이  그 권역의 명소 목록에 있는가
  를 보면 **짐작 없이** 가릴 수 있습니다.
  [[photo-check-by-distance]] — 이름만 믿지 않고 자료와 맞댑니다.

보는 것
  ① 사진의 쓰임이 **그 권역 명소 목록에 있는가**
  ② 다른 권역 목록에 있지 않은가 (잘못 배정)
  ③ 사진이 **없는** 명소가 몇인가
  ④ 촬영자·이용허락이 비어 있지 않은가 (주인 규칙 5)
  ⑤ 그림 파일이 실제로 있는가

쓰는 법
    python -m engine.check_jeju_photos
    python -m engine.check_jeju_photos --strict
"""
import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def 씻기(t):
    """괄호와 가운뎃점·사이띄기를 걷어 이름을 맞대기 쉽게."""
    t = re.sub(r'\(.*?\)', '', t or '')
    return re.sub(r'[·\s]', '', t)


def 읽기(길):
    return json.load(io.open(os.path.join(ROOT, 길), encoding='utf-8'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--strict', action='store_true')
    a = p.parse_args()

    여행 = 읽기('data/raw/travel/jeju.json')
    사진들 = 읽기('data/raw/photos.json')['사진']

    # 권역마다 명소 이름 모음
    명소 = {}
    for 권 in 여행['권역']:
        것 = {}
        for x in (권.get('명소') or []):
            이 = ((x.get('이름') or {}).get('ko') or '').strip()
            if 이:
                것[씻기(이)] = {'이름': 이, '주소': x.get('주소') or '',
                                '좌표': x.get('좌표')}
        명소[권['id']] = 것

    제주사진 = [x for x in 사진들
                if (x.get('파일') or '').startswith('img/jeju/')]

    막음, 알림 = [], []
    맞은것 = 0
    표 = []
    for x in sorted(제주사진, key=lambda y: (y.get('권역') or '',
                                             y.get('쓰임') or '')):
        파 = (x.get('파일') or '')
        쓰 = x.get('쓰임') or ''
        권 = x.get('권역') or ''
        이름 = 파.split('/')[-1]

        if not 권 or not 쓰:
            알림.append('%s — 권역/쓰임이 비었습니다 (안 쓰입니다)' % 이름)
            continue
        if 쓰.startswith(('hero', 'home')):
            continue                       # 대표 사진은 명소가 아닙니다

        # ⑤ 파일이 있는가
        if not os.path.isfile(os.path.join(ROOT, 'site', 파)):
            막음.append('%s — 그림 파일이 없습니다' % 이름)
            continue
        # ④ 촬영자·이용허락 (주인 규칙 5)
        if not (x.get('촬영자') or '').strip():
            막음.append('%s — 촬영자가 비었습니다' % 이름)
        if not (x.get('이용허락') or '').strip():
            막음.append('%s — 이용허락이 비었습니다' % 이름)

        # ① 그 권역 명소 목록에 있는가
        칸 = 명소.get(권) or {}
        키 = 씻기(쓰)
        맞 = None
        for k, v in 칸.items():
            if k and (키 in k or k in 키):
                맞 = v
                break
        if 맞:
            맞은것 += 1
            표.append((권, 쓰, 맞['주소'], '맞음'))
            continue

        # ② 다른 권역에 있는가 — 있으면 **잘못 배정**입니다
        딴데 = None
        for 권2, 칸2 in 명소.items():
            if 권2 == 권:
                continue
            for k, v in 칸2.items():
                if k and (키 in k or k in 키):
                    딴데 = (권2, v)
                    break
            if 딴데:
                break
        if 딴데:
            막음.append('%s — **%s 가 아니라 %s** 입니다 (%s)'
                        % (이름, 권, 딴데[0], 딴데[1]['주소']))
            표.append((권, 쓰, 딴데[1]['주소'], '★ %s 여야' % 딴데[0]))
        else:
            알림.append('%s — 「%s」가 어느 권역 명소 목록에도 '
                        '없습니다 (쪽에 안 나올 수 있습니다)' % (이름, 쓰))
            표.append((권, 쓰, '-', '목록에 없음'))

    # ③ 사진이 없는 명소
    사진있는이름 = {}
    for x in 제주사진:
        권, 쓰 = x.get('권역'), x.get('쓰임') or ''
        if 권 and 쓰 and not 쓰.startswith(('hero', 'home')):
            사진있는이름.setdefault(권, set()).add(씻기(쓰))
    빈명소 = []
    for 권, 칸 in sorted(명소.items()):
        있 = 사진있는이름.get(권) or set()
        for k, v in sorted(칸.items()):
            if not any(k in b or b in k for b in 있):
                빈명소.append((권, v['이름']))

    print('제주 명소 사진이 제자리에 붙었는가')
    print('=' * 72)
    print('  근거: data/raw/travel/jeju.json 의 권역별 명소 목록')
    print('  제주 사진 %d장 · 명소 %d곳'
          % (len(제주사진), sum(len(v) for v in 명소.values())))
    print()
    print('%-10s %-24s %-28s %s' % ('권역', '쓰임', '자료의 주소', ''))
    print('-' * 72)
    for 권, 쓰, 주, 판 in 표:
        print('%-10s %-24s %-28s %s' % (권, 쓰[:24], 주[:28], 판))

    print()
    if 막음:
        print('  ✗ 고쳐야 할 것 %d가지' % len(막음))
        for m in 막음:
            print('      %s' % m)
    else:
        print('  · 잘못 배정된 사진이 **없습니다**')
    if 알림:
        print('  ~ 살펴볼 것 %d가지' % len(알림))
        for m in 알림[:8]:
            print('      %s' % m)
    if 빈명소:
        print('  ~ 아직 사진이 없는 명소 %d곳' % len(빈명소))
        for 권, 이 in 빈명소[:10]:
            print('      %-10s %s' % (권, 이))

    print('-' * 72)
    print('[한 줄 요약] 맞은 사진 %d장 · 잘못 %d · 살펴볼 것 %d · '
          '사진 없는 명소 %d곳'
          % (맞은것, len(막음), len(알림), len(빈명소)))
    if 막음:
        return 2 if a.strict else 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
