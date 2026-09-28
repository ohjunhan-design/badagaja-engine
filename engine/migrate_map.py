# -*- coding: utf-8 -*-
"""옛 첫 화면의 **전국 바다지도**를 자료로 뽑아냅니다.

★ 2026-09-27 주인 지시 「이건 예전 지도로 권역선택하게 하고」

    옛 첫 화면에는 전국 지도가 있었습니다. 묶음(수도권·충남·전북…)
    아홉 곳이 각각 눌러지는 땅 모양으로 그려져 있고, 누르면 그
    묶음 쪽으로 갑니다.

    새 틀은 그 자리에 **사진 카드 아홉 개**를 놓았습니다. 사진은
    좋지만, 지도만큼 「어디인지」가 한눈에 안 들어옵니다.
    바닷가는 **자리가 곧 정보**입니다.

무엇을 뽑아내나
    옛 index.html 의 `<section class="hm">` 안에서

        묶음마다  땅 모양(polygon) · 이름표 자리 · 색
        가운데    내륙 모양과 글자 (충북 같은 바다 없는 곳)
        오른쪽    「바다가자닷컴에서 볼 수 있는 것」 차림표

    를 읽어 data/raw/map.json 에 적습니다.

★ 좌표를 손으로 옮기지 않습니다
    폴리곤 하나에 점이 수십 개입니다. 손으로 옮기면 반드시 틀립니다.
    읽어서 그대로 적습니다.

★ 차림표 링크는 **옮기지 않습니다**
    옛 차림표에는 「해루질 대상 17」·「바다 축제 190」처럼 숫자가
    박혀 있습니다. 그것은 build.py 가 자료에서 세어 넣습니다
    (주인 규칙 29). 여기서는 **자리와 차례만** 가져옵니다.

쓰는 법
    python engine/migrate_map.py            무엇이 나올지 봅니다
    python engine/migrate_map.py --write    data/raw/map.json 을 씁니다
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []


def 지도덩이():
    s = io.read(os.path.join(OLD, 'index.html'), default='')
    if '<section class="hm"' not in s:
        막음.append('옛 index.html 에서 지도를 못 찾았습니다')
        return ''
    i = s.index('<section class="hm"')
    j = s.index('</svg>', i) + len('</svg>')
    return s[i:j]


def 뽑기():
    덩이 = 지도덩이()
    if not 덩이:
        return None

    m = re.search(r'viewBox="([^"]+)"', 덩이)
    보임칸 = m.group(1) if m else '0 0 255 353'

    # ── 내륙 (바다가 없는 곳)
    내륙 = []
    for m in re.finditer(
            r'<polygon class="hm-inland" points="([^"]+)"[^>]*/?>', 덩이):
        내륙.append({'점': m.group(1).strip()})
    내륙글자 = []
    for m in re.finditer(
            r'<text class="hm-inl" x="([^"]+)" y="([^"]+)">([^<]+)</text>',
            덩이):
        내륙글자.append({'x': float(m.group(1)), 'y': float(m.group(2)),
                         '글': m.group(3)})

    # ── 묶음마다
    묶음들 = []
    for m in re.finditer(
            r'<a href="([a-z]+)/" class="hm-r" style="--c:([^"]+)"'
            r'[^>]*aria-label="([^"]*)"\s*>(.*?)</a>', 덩이, re.S):
        아이디, 색, 읽는이름, 안 = m.groups()
        점들 = [x.strip() for x in
                re.findall(r'<polygon points="([^"]+)"', 안)]
        알약 = None
        p = re.search(r'<rect class="hm-pill" x="([^"]+)" y="([^"]+)" '
                      r'width="([^"]+)" height="([^"]+)" rx="([^"]+)"', 안)
        if p:
            알약 = {'x': float(p.group(1)), 'y': float(p.group(2)),
                    'w': float(p.group(3)), 'h': float(p.group(4)),
                    'r': float(p.group(5))}
        글 = re.search(r'<text class="hm-lb" x="([^"]+)" y="([^"]+)">'
                       r'([^<]+)</text>', 안)
        묶음들.append({
            '묶음': 아이디,
            '색': 색,
            '읽는이름': 읽는이름,
            '땅': 점들,
            '이름표': 알약,
            '글': ({'x': float(글.group(1)), 'y': float(글.group(2)),
                    '글': 글.group(3)} if 글 else None),
        })

    return {'보임칸': 보임칸, '내륙': 내륙, '내륙글자': 내륙글자,
            '묶음': 묶음들}


# 오른쪽 차림표 — **자리와 차례만** 가져옵니다.
# 숫자가 든 이름은 build.py 가 자료에서 세어 넣습니다 (주인 규칙 29).
차림표 = [
    {'머리': '물때', '줄': [
        {'글': '전국 물때표', '길': 'tide/'},
        {'글': '물때표 보는 법', '길': 'muldae.html'},
    ]},
    {'머리': '잡기', '줄': [
        {'글': '해루질 대상 {해루질수}가지', '길': 'catch/'},
        {'글': '낚시 어종 {낚시수}가지', '길': 'fish/'},
        {'글': '포인트 {포인트수}곳', '길': '#bada'},
    ]},
    {'머리': '처음이라면', '줄': [
        {'글': '장비와 안전', '길': 'gear.html'},
        {'글': '금어기 · 크기 · 마을어장', '길': 'rule.html'},
    ]},
    {'머리': '축제와 관광', '줄': [
        {'글': '바다 축제 {축제수}개', '길': 'festival/'},
        {'글': '향토 먹거리 · 명소', '길': '#bada'},
    ]},
]


def main():
    쓰기 = '--write' in sys.argv
    것 = 뽑기()

    print('옛 첫 화면의 전국 바다지도를 자료로 뽑아내기')
    print('  (2026-09-27 주인 지시 「이건 예전 지도로 권역선택하게 하고」)')
    print('')
    if not 것:
        for x in 막음:
            print('  ✗ %s' % x)
        return 1

    print('[1] 지도')
    print('      보임칸 %s' % 것['보임칸'])
    print('      내륙 모양 %d개 · 내륙 글자 %d개'
          % (len(것['내륙']), len(것['내륙글자'])))
    print('')
    print('[2] 묶음마다')
    print('      %-12s %-10s %6s %s' % ('묶음', '색', '땅조각', '이름표'))
    for x in 것['묶음']:
        점수 = sum(len(p.split()) for p in x['땅'])
        print('      %-12s %-10s %6d %s'
              % (x['묶음'], x['색'], len(x['땅']),
                 (x['글'] or {}).get('글', '(없음)')))
    print('      땅 조각 합계 %d · 점 합계 %d'
          % (sum(len(x['땅']) for x in 것['묶음']),
             sum(len(p.split()) for x in 것['묶음'] for p in x['땅'])))
    print('')

    # 새 틀에 그 묶음이 다 있는가
    print('[3] 새 틀에 그 묶음이 모두 있는가')
    from engine import data as _data
    try:
        d = _data.자료()
        있는것 = set(d.색인['묶음차례'])
        지도것 = set(x['묶음'] for x in 것['묶음'])
        없는것 = sorted(지도것 - 있는것)
        빠진것 = sorted(있는것 - 지도것)
        print('      지도 %d곳 · 자료 %d곳' % (len(지도것), len(있는것)))
        if 없는것:
            막음.append('지도에 있는데 자료에 없는 묶음: %s' % ' '.join(없는것))
            print('  ✗ 지도에만 있는 것: %s' % ' '.join(없는것))
        if 빠진것:
            막음.append('자료에 있는데 지도에 없는 묶음: %s' % ' '.join(빠진것))
            print('  ✗ 자료에만 있는 것: %s' % ' '.join(빠진것))
        if not (없는것 or 빠진것):
            print('  · 아홉 곳이 그대로 맞습니다')
    except Exception as e:          # noqa: BLE001
        알림.append('자료를 못 읽었습니다: %s' % e)
        print('      ~ 자료를 못 읽었습니다')
    print('')

    if 쓰기:
        것['_설명'] = ('옛 첫 화면의 전국 바다지도. '
                       'engine/migrate_map.py --write 가 뽑아냅니다 — '
                       '손으로 고치지 마세요')
        것['_왜'] = ('2026-09-27 주인 지시 「이건 예전 지도로 권역선택하게 '
                     '하고」. 바닷가는 자리가 곧 정보라, 사진 카드보다 '
                     '지도가 한눈에 들어옵니다')
        것['차림표'] = 차림표
        io.write_json(os.path.join(DATA, 'raw', 'map.json'), 것)
        print('썼습니다: data/raw/map.json')
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0
    if not 쓰기:
        print('--write 를 붙이면 data/raw/map.json 을 씁니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
