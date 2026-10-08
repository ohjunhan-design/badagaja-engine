# -*- coding: utf-8 -*-
"""서로 다른 곳이 **같은 좌표**를 쓰는 묶음을 가립니다 (2026-10-08).

★ 왜 묶음 단위인가 — 바깥 검수가 바로잡았습니다

      「693곳을 전부 다시 찍으려 하지 마세요. **포인트 단위가
        아니라 『같은 좌표 묶음』 단위로 관리**해야 합니다.
        693개보다 묶음 수가 훨씬 적습니다.
        … 지금은 693곳을 정확하게 고치는 프로젝트가 아니라,
        **693곳에서 거짓 정확함을 제거하는 프로젝트**로
        접근하는 게 맞습니다」

  포인트 693곳이지만 묶음은 297개입니다. 묶음 하나를 보면
  그 안의 여러 곳이 한꺼번에 정리됩니다.

★ 세 갈래로만 가립니다 (바깥 검수가 정한 분류)

    같은자리    같은 항·방파제 둘레를 낚시/해루질/지형만 달리 적음
                → 좌표가 같아도 **말이 됩니다.** 후순위.
    대표좌표    서로 다른 소분류인데 권역 대표 좌표를 임시로 넣음
    잘못겹침  북측/남측, 서로 다른 마을·해변·방파제처럼
                **같은 좌표일 수 없는** 것. 먼저 봅니다.

★ **좌표를 고치지 않습니다.** 가리기만 합니다.
  바깥 검수 — 「자동으로 좌표를 고치지는 말고, 이 세 분류만
  먼저 하세요」

쓰는 법
    python tools/dup_coords.py            # 표를 냅니다
    python tools/dup_coords.py --적기     # data-private 에 적습니다
"""
import io
import json
import os
import re
import sys
import glob
import collections

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

자료길 = os.path.join(여기, 'data', 'raw', 'points')
낼곳 = os.path.join(여기, 'data-private', '좌표-겹친묶음.md')

from engine import dupspot   # 가리는 법은 **한 곳**에만

방위 = dupspot.방위
생김새 = dupspot.생김새
알맹이 = dupspot.알맹이


def 가리기(들):
    """묶음 하나를 세 갈래 가운데 하나로 가립니다.

    ★ 가리는 법은 `engine/dupspot.py` **한 곳**에만 둡니다 —
      화면(패널)도 같은 갈래를 써야 하는데, 두 곳에서 따로 가리면
      반드시 어긋납니다 (기억 「숫자는 한 곳에서만」).
    """
    return dupspot.가리기([x['이름'] for x in 들],
                          [x.get('갈래') for x in 들])


def 모으기():
    자리표 = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(자료길, '*.json'))):
        d = json.loads(io.open(f, encoding='utf-8').read())
        for x in (d.get('포인트') or d.get('points') or []):
            좌 = x.get('좌표') or {}
            if 좌.get('위도') is None:
                continue
            키 = (round(좌['위도'], 6), round(좌['경도'], 6))
            이름 = x.get('이름')
            if isinstance(이름, dict):
                이름 = 이름.get('ko') or ''
            자리표[키].append({
                'id': x.get('id'), '이름': 이름 or '',
                '권역': x.get('권역'), '갈래': x.get('갈래'),
                '지형': x.get('지형'),
            })
    return {k: v for k, v in 자리표.items() if len(v) > 1}


def main():
    겹침 = 모으기()
    묶음 = []
    for (la, lo), 들 in 겹침.items():
        갈래, 까닭 = 가리기(들)
        묶음.append({'위도': la, '경도': lo, '곳수': len(들),
                     '갈래': 갈래, '까닭': 까닭, '것들': 들})
    # ★ 차례를 정해 둡니다 — 돌릴 때마다 달라지면 못 견줍니다
    차례 = {'잘못겹침': 0, '대표좌표': 1, '같은자리': 2}
    묶음.sort(key=lambda m: (차례[m['갈래']], -m['곳수'],
                             m['위도'], m['경도']))

    셈 = collections.Counter(m['갈래'] for m in 묶음)
    곳셈 = collections.Counter()
    for m in 묶음:
        곳셈[m['갈래']] += m['곳수']

    print('서로 다른 곳이 같은 좌표를 쓰는 묶음')
    print('')
    print('  묶음 %d개 · 포인트 %d곳'
          % (len(묶음), sum(m['곳수'] for m in 묶음)))
    print('')
    for 갈래 in ('잘못겹침', '대표좌표', '같은자리'):
        print('  %-10s 묶음 %3d개 · %4d곳'
              % (갈래, 셈[갈래], 곳셈[갈래]))
    print('')
    print('  먼저 볼 것 — 「잘못겹침」 묶음 가운데 큰 쪽 10개')
    for m in [x for x in 묶음 if x['갈래'] == '잘못겹침'][:10]:
        print('   ! %.6f, %.6f · %d곳 · %s'
              % (m['위도'], m['경도'], m['곳수'], m['까닭']))
        for x in m['것들'][:3]:
            print('       %-10s %s' % (x['권역'], x['이름']))

    if '--적기' in sys.argv:
        줄 = ['# 서로 다른 곳이 같은 좌표를 쓰는 묶음', '',
              '> 바깥 검수 — 「693곳을 전부 다시 찍으려 하지 마세요.',
              '> **포인트 단위가 아니라 「같은 좌표 묶음」 단위로**',
              '> 관리해야 합니다. … 지금은 693곳을 정확하게 고치는',
              '> 프로젝트가 아니라, **693곳에서 거짓 정확함을 제거하는**',
              '> 프로젝트로 접근하는 게 맞습니다」', '',
              '**좌표를 고치지 않았습니다.** 가리기만 했습니다.', '',
              '| 갈래 | 묶음 | 곳 | 무엇인가 |', '|---|---|---|---|',
              '| 잘못겹침 | %d | %d | 북측/남측처럼 **같은 좌표일 수'
              ' 없는** 것. 먼저 봅니다 |'
              % (셈['잘못겹침'], 곳셈['잘못겹침']),
              '| 대표좌표 | %d | %d | 권역 대표 좌표를 임시로 넣은 것 |'
              % (셈['대표좌표'], 곳셈['대표좌표']),
              '| 같은자리 | %d | %d | 같은 항 둘레를 생김새·갈래만 달리'
              ' 적은 것. 후순위 |'
              % (셈['같은자리'], 곳셈['같은자리']), '']
        for 갈래 in ('잘못겹침', '대표좌표', '같은자리'):
            줄 += ['', '## %s' % 갈래, '']
            for m in [x for x in 묶음 if x['갈래'] == 갈래]:
                줄.append('- `%.6f, %.6f` · **%d곳** — %s'
                          % (m['위도'], m['경도'], m['곳수'], m['까닭']))
                줄.append('  - 위성으로 보기 — '
                          '[카카오맵](https://map.kakao.com/link/map/'
                          '%s,%s,%s)'
                          % (m['것들'][0]['이름'].replace(',', ' ')
                             .replace(' ', '%20'), m['위도'], m['경도']))
                for x in m['것들']:
                    줄.append('  - %s · `%s` · %s'
                              % (x['이름'], x['id'], x['지형'] or ''))
        os.makedirs(os.path.dirname(낼곳), exist_ok=True)
        io.open(낼곳, 'w', encoding='utf-8').write('\n'.join(줄) + '\n')
        print('')
        print('  · %s 에 적었습니다' % os.path.relpath(낼곳, 여기))
    return 0


if __name__ == '__main__':
    sys.exit(main())
