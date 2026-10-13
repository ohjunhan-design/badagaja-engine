# -*- coding: utf-8 -*-
"""어종 ↔ 장소 유형 매핑을 **자료에서 뽑습니다** (설계 ①).

★ 지어내지 않습니다
  `data/raw/guide.json` 의 「어디서」 글에 **실제로 적힌 낱말**로만
  고릅니다. 맞는 낱말이 없으면 **빈 채로 둡니다** — 억지로 채우면
  없는 사실을 만드는 것입니다.

★ 1:N 을 허용합니다 (지시 C)
  우럭은 테트라포드·갯바위·자갈밭에 다 적혀 있습니다. 하나만
  고르면 자료를 버리는 것입니다.

★ 테트라포드는 **장소 유형이 아니라 위험 경고**입니다 (지시 A·E)
  「추천 발판」으로 세우지 않습니다. 걸리면 경고 딱지만 답니다.

이 스크립트는 **읽기만** 하고 결과를 화면에 냅니다.
자료 파일은 감독실 확인 뒤에 만듭니다.
"""
import json
import re
import sys

# ── 장소 유형 여덟 (지시 A) ───────────────────────────────
유형 = [
    ('harbor-in', '방파제 내항', ['내항', '항내', '선착장', '내만', '제방']),
    ('harbor-out', '방파제 외항', ['외항', '방파제 끝', '끝자락', '끝머리',
                                   '모서리', '홈통']),
    ('rock-low', '낮은 갯바위', ['낮은 갯바위', '갯바위']),
    ('rock-point', '곶부리·외곽 갯바위', ['곶부리', '본류', '수중여',
                                          '물골', '포말']),
    ('sand', '모래사장·사니질', ['모래', '사니질', '백사장', '펄', '진흙']),
    ('estuary', '하구·수로', ['하구', '강', '수로', '기수']),
    ('weed', '여밭·해초대·수중여', ['해조', '여밭', '암초', '자갈밭',
                                    '암초지대']),
    ('boat', '선상·깊은 수심', ['선상', '배를 타']),
]
# ★ 장소가 아니라 **경고**입니다
경고 = [('tetra', '테트라포드 — 위험', ['테트라포드', '테트라'])]


def 글(v):
    return (v.get('ko') if isinstance(v, dict) else v) or ''


def 평(o, 모):
    if isinstance(o, dict):
        if '어디서' in o:
            모.append(o)
        for v in o.values():
            평(v, 모)
    elif isinstance(o, list):
        for v in o:
            평(v, 모)


d = json.load(open(r'D:\바다가자\두번째도전\data\raw\guide.json',
                   encoding='utf-8'))
모 = []
평(d, 모)

# 어종 쪽이 있는 것만 (쪽이 없으면 404 가 됩니다 — 지시 C)
import os
있는쪽 = {f[:-5] for f in os.listdir(r'D:\바다가자\두번째도전\site\fish')
          if f.endswith('.html') and f not in ('index.html', 'basics.html')}

print('어종 쪽 %d개 · 「어디서」 가진 자료 %d개' % (len(있는쪽), len(모)))
print('=' * 70)

결과 = {}
빈것 = []
for 것 in 모:
    i = 것.get('id')
    if i not in 있는쪽:
        continue
    어디 = 글(것.get('어디서'))
    붙 = [코 for 코, 이름, 말들 in 유형 if any(w in 어디 for w in 말들)]
    경 = [코 for 코, 이름, 말들 in 경고 if any(w in 어디 for w in 말들)]
    결과[i] = {'이름': 글(것.get('이름')), '장소': 붙, '경고': 경,
               '어디서': 어디}
    if not 붙:
        빈것.append(i)

이름표 = {코: 이름 for 코, 이름, _ in 유형}
이름표.update({코: 이름 for 코, 이름, _ in 경고})

for i in sorted(결과):
    r = 결과[i]
    print('%-14s %-8s %s%s'
          % (i, r['이름'],
             ' · '.join(이름표[x] for x in r['장소']) or '★ 없음',
             '   [%s]' % ' '.join(이름표[x] for x in r['경고'])
             if r['경고'] else ''))

print('')
import collections
셈 = collections.Counter()
for r in 결과.values():
    for x in r['장소']:
        셈[x] += 1
print('장소 유형별 어종 수')
for 코, 이름, _ in 유형:
    print('  %-22s %d종' % (이름, 셈.get(코, 0)))
print('')
print('장소를 하나도 못 고른 어종: %s' % (', '.join(빈것) if 빈것 else '없음'))
print('어종당 평균 장소 %.1f개'
      % (sum(len(r['장소']) for r in 결과.values()) / max(len(결과), 1)))
