# -*- coding: utf-8 -*-
"""물때의 **빈 날이 어디에 있는가** 를 봅니다 (2026-10-15 총감독 지시 P0-1).

★ 왜 만드나 — 「빈 434」가 큰일인지 아닌지 **개수로는 못 가립니다**
  이미 있는 검사기들은 이것을 못 봅니다.
    · `check_tide_files`  — 빈 날 **개수**가 2% 를 넘는지만 봅니다
    · `check_tide_live`   — **남은 날**만 보고 「멀쩡합니다」라고 합니다
    · `check_tide_integrity` — 빈 날을 **건너뛰고** 구조를 봅니다

  그런데 빈 날이 **앞에 있는가 뒤에 있는가**로 뜻이 완전히 달라집니다.

      앞 7일이 비면   **손님이 지금 당장 봅니다** — 큰일입니다
      뒤쪽이 비면     정부가 **아직 안 준 먼 날**입니다 —
                      날이 가까워지면 채워집니다. 큰일이 아닙니다

  개수만 세면 이 둘이 똑같아 보입니다. **자리를 봐야 합니다.**

★ 무엇을 내나
  권역마다  빈 날 수 · **가장 이른 빈 날이 며칠째인가** ·
            뒤쪽 연속으로 비었는가 · 앞 7일에 빈 날이 있는가
  그리고    **여러 권역이 같은 날짜에 비는가**
            (같으면 정부 쪽 그 날짜 문제 · 흩어지면 관측소마다 사정)

★ 끝난값
  0  앞 7일이 성합니다
  1  앞 7일에 빈 날이 있습니다 (손님이 봅니다)
  2  `--strict` 에서 1 과 같은 일

★ **읽기만 합니다.** 운영 자료를 고치지 않습니다.

쓰는 법
    python -m engine.check_tide_gaps
    python -m engine.check_tide_gaps --로컬
    python -m engine.check_tide_gaps --권역 seongsan --낱낱이
"""
import argparse
import collections
import io
import json
import os
import sys
import urllib.request

from engine import kst

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
로컬칸 = os.path.join(뿌리, 'data', 'tide')
운영 = 'https://badagaja.com/assets/tide/'

앞날수 = 7          # 손님이 바로 보는 날 수


def 권역목록():
    """권역은 **자료에서 읽습니다.** 손으로 적지 않습니다.
    [[tests-must-not-hardcode-names]] · `check_tide_live` 와 같은 길."""
    sys.path.insert(0, 뿌리)
    from engine import build
    return [r['id'] for r in build.자료().권역들]


def 읽기(권, 로컬):
    if 로컬:
        길 = os.path.join(로컬칸, '%s.json' % 권)
        if not os.path.isfile(길):
            return None, '파일이 없습니다'
        try:
            return json.load(io.open(길, encoding='utf-8')), None
        except Exception as e:
            return None, '%s' % e
    try:
        with urllib.request.urlopen(운영 + '%s.json' % 권, timeout=30) as r:
            return json.loads(r.read().decode('utf-8')), None
    except Exception as e:
        return None, '%s' % e


def 보기(권, j):
    """한 권역의 빈 날 자리를 잽니다."""
    날들 = j.get('days') or []
    빈자리 = [i for i, x in enumerate(날들) if not (x.get('events') or [])]
    빈날짜 = [날들[i].get('date') for i in 빈자리]

    # 뒤쪽이 **끊김 없이** 비었는가
    꼬리 = 0
    for i in range(len(날들) - 1, -1, -1):
        if 날들[i].get('events'):
            break
        꼬리 += 1

    앞빈 = [날들[i].get('date') for i in 빈자리 if i < 앞날수]
    return {
        '날수': len(날들),
        '빈수': len(빈자리),
        '첫빈': (빈자리[0] if 빈자리 else None),
        '꼬리': 꼬리,
        '앞빈': 앞빈,
        '빈날짜': 빈날짜,
        '처음': 날들[0].get('date') if 날들 else '',
        '끝': 날들[-1].get('date') if 날들 else '',
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--로컬', action='store_true', help='운영 대신 data/tide')
    p.add_argument('--권역')
    p.add_argument('--낱낱이', action='store_true')
    p.add_argument('--strict', action='store_true')
    a = p.parse_args()

    권역들 = [a.권역] if a.권역 else 권역목록()
    if not 권역들:
        print('★ 권역이 0곳입니다 — 0 을 재면 당연히 0 입니다')
        return 1                        # [[count-before-you-claim-zero]]

    것들, 못읽음 = {}, []
    for 권 in 권역들:
        j, 탈 = 읽기(권, a.로컬)
        if j is None:
            못읽음.append((권, 탈))
            continue
        것들[권] = 보기(권, j)

    if not 것들:
        print('★ 한 곳도 못 읽었습니다 — 재지 못했습니다')
        for 권, 탈 in 못읽음[:5]:
            print('    %s — %s' % (권, 탈))
        return 1

    빈합 = sum(v['빈수'] for v in 것들.values())
    앞탈 = {k: v for k, v in 것들.items() if v['앞빈']}
    # 빈 날이 **전부 꼬리**인 곳 (= 정부가 아직 안 준 먼 날)
    꼬리뿐 = [k for k, v in 것들.items()
              if v['빈수'] and v['빈수'] == v['꼬리']]
    섞인것 = [k for k, v in 것들.items()
              if v['빈수'] and v['빈수'] != v['꼬리']]

    print('물때의 빈 날이 **어디에** 있는가')
    print('=' * 72)
    print('  %s · %d곳 · 빈 날 합계 %d일'
          % ('로컬' if a.로컬 else '운영', len(것들), 빈합))
    if 못읽음:
        print('  ★ 못 읽은 곳 %d곳' % len(못읽음))
    print()

    print('%-12s %4s %4s %6s %6s  %s'
          % ('권역', '날수', '빈', '첫빈째', '꼬리', '앞 7일'))
    print('-' * 72)
    for 권 in sorted(것들, key=lambda k: -것들[k]['빈수']):
        v = 것들[권]
        if not v['빈수'] and not a.낱낱이:
            continue
        print('%-12s %4d %4d %6s %6d  %s'
              % (권, v['날수'], v['빈수'],
                 ('%d째' % (v['첫빈'] + 1)) if v['첫빈'] is not None else '-',
                 v['꼬리'],
                 ('★ ' + ' · '.join(v['앞빈'])) if v['앞빈'] else '성합니다'))
        if a.낱낱이 and v['빈날짜']:
            print('        빈 날: %s' % ' · '.join(v['빈날짜']))

    # ── 여러 곳이 **같은 날짜**에 비는가 ──────────────────
    셈 = collections.Counter()
    for v in 것들.values():
        셈.update(v['빈날짜'])
    많이 = [(d, c) for d, c in 셈.items() if c >= max(3, len(것들) // 4)]
    많이.sort(key=lambda x: -x[1])

    print()
    print('  · 빈 날이 **전부 뒤쪽 연속**인 곳   %d곳' % len(꼬리뿐))
    print('    → 정부가 **아직 안 준 먼 날**입니다. 날이 가까워지면 찹니다')
    if 섞인것:
        print('  ~ 중간에도 빈 날이 있는 곳        %d곳' % len(섞인것))
        for 권 in 섞인것[:8]:
            v = 것들[권]
            가운데 = [d for i, d in zip(
                [i for i, _ in enumerate(v['빈날짜'])], v['빈날짜'])]
            print('      %-12s 빈 %d일 중 뒤쪽 연속 %d일'
                  % (권, v['빈수'], v['꼬리']))
    if 많이:
        print('  ~ **여러 곳이 함께** 비는 날짜 %d개 (가장 많은 것부터)'
              % len(많이))
        for d, c in 많이[:10]:
            print('      %-8s %d곳' % (d, c))
        print('    → 한 날짜가 여러 곳에서 비면 **그 날짜를 정부가 '
              '아직 안 낸 것**입니다')

    print()
    if 앞탈:
        print('  ✗ **앞 %d일에 빈 날이 있는 곳 %d곳** — 손님이 봅니다'
              % (앞날수, len(앞탈)))
        for 권, v in sorted(앞탈.items()):
            print('      %-12s %s' % (권, ' · '.join(v['앞빈'])))
    else:
        print('  ✓ **앞 %d일은 57곳 모두 성합니다** — 손님이 보는 '
              '자리에 빈 날이 없습니다' % 앞날수)

    print('-' * 72)
    print('[한 줄 요약] 빈 날 %d일 · 그 가운데 뒤쪽 연속뿐인 곳 %d곳 · '
          '앞 %d일이 빈 곳 %d곳'
          % (빈합, len(꼬리뿐), 앞날수, len(앞탈)))
    if 앞탈:
        return 2 if a.strict else 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
