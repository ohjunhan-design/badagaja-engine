# -*- coding: utf-8 -*-
"""권역 쪽에 쓰는 자료를 옮깁니다 — 명소·먹거리·축제·어종·코스·마을·통제

왜 따로 두나
    포인트(points/)는 양이 많고 자주 바뀝니다. 명소·먹거리는 적고 덜 바뀝니다.
    한 파일에 섞으면 편집기가 느려지고 두 작업이 부딪힙니다 (DATA.md).

무엇이 어디서 오나
    42권역  data/coast-regions*.json · jeju-regions.json  — 자료가 있습니다
    전남 15 zh-cn/i18n/region-ko.json (먹거리·명소만)
            나머지(어종·패류·코스)는 **쪽에만** 있어 따로 캐냅니다
            → engine/extract_jeonnam_travel.py

쓰는 법
    python engine/migrate_travel.py            보여만 줍니다
    python engine/migrate_travel.py --write    씁니다
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))


def 글(s):
    return re.sub(r'\s+', ' ', (s or '')).strip() or None


def 좌표(x):
    위, 경 = x.get('lat'), x.get('lng')
    if 위 is None or 경 is None:
        return None
    return {'위도': 위, '경도': 경}


def 명소옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-spot-%02d' % (권역, i),
            '이름': {'ko': 글(x.get('name')), 'zh': None},
            '갈래': 글(x.get('kind')),
            '주소': 글(x.get('addr')),
            '설명': {'ko': 글(x.get('desc')), 'zh': None},
            '좌표': 좌표(x),
            '배로가나': bool(x.get('ferry')),
        })
    return 나옴


def 먹거리옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-eat-%02d' % (권역, i),
            '이름': {'ko': 글(x.get('name') or x.get('n')), 'zh': None},
            '설명': {'ko': 글(x.get('desc') or x.get('d')), 'zh': None},
            '철': 글(x.get('when')),
            '그림': 글(x.get('icon') or x.get('i')),
        })
    return 나옴


def 축제옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-fest-%02d' % (권역, i),
            '이름': {'ko': 글(x.get('name')), 'zh': None},
            '달': x.get('month'),
            '곳': 글(x.get('place')),
            '설명': {'ko': 글(x.get('desc')), 'zh': None},
            '해': x.get('year'),
        })
    return 나옴


def 어종옮기기(권역, 목록, 갈래):
    """제철 어종(fish)·해루질 대상(catch)"""
    표 = 'fish' if 갈래 == '낚시' else 'catch'
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-%s-%02d' % (권역, 표, i),
            '이름': {'ko': 글(x.get('name')), 'zh': None},
            '갈래': 갈래,
            '철': 글(x.get('season')),
            '설명': {'ko': 글(x.get('text')), 'zh': None},
            '그림': 글(x.get('icon')),
        })
    return 나옴


def 코스옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-course-%02d' % (권역, i),
            '이름': {'ko': 글(x.get('title')), 'zh': None},
            '누구와': 글(x.get('theme')),
            '차례': [글(s) for s in (x.get('steps') or []) if 글(s)],
        })
    return 나옴


def 마을옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-village-%02d' % (권역, i),
            '이름': {'ko': 글(x.get('name')), 'zh': None},
            '주소': 글(x.get('addr')),
            '좌표': 좌표(x),
            '무엇을': {'ko': 글(x.get('what')), 'zh': None},
            '근거': 글(x.get('source')),      # 웹에 안 냅니다 (주인 규칙 11)
        })
    return 나옴


def 통제옮기기(권역, 목록):
    나옴 = []
    for i, x in enumerate(목록 or [], 1):
        나옴.append({
            'id': '%s-ban-%02d' % (권역, i),
            '곳': 글(x.get('place')),
            '내용': {'ko': 글(x.get('note')), 'zh': None},
        })
    return 나옴


def 자료묶음들():
    나옴 = []
    파일 = sorted(glob.glob(os.path.join(OLD, 'data', 'coast-regions*.json')))
    파일 += [os.path.join(OLD, 'data', 'jeju-regions.json')]
    for p in 파일:
        d = io.read_json(p, default={})
        묶음 = (d.get('group') or {}).get('key')
        if not 묶음:
            묶음 = 'jeju' if 'jeju' in os.path.basename(p) else 'chungnam'
        for r in d.get('regions', []):
            나옴.append((묶음, r))
    return 나옴


def main():
    쓰기 = '--write' in sys.argv

    묶음별 = {}
    센것 = {'명소': 0, '먹거리': 0, '축제': 0, '어종': 0, '코스': 0,
            '마을': 0, '통제': 0}

    for 묶음, r in 자료묶음들():
        권역 = r['slug']
        한권역 = {
            'id': 권역,
            '명소': 명소옮기기(권역, r.get('spots')),
            '먹거리': 먹거리옮기기(권역, r.get('eat')),
            '축제': 축제옮기기(권역, r.get('festivals')),
            '어종': (어종옮기기(권역, r.get('fish'), '낚시')
                     + 어종옮기기(권역, r.get('catch'), '해루질')),
            '코스': 코스옮기기(권역, r.get('courses')),
            '마을': 마을옮기기(권역, r.get('villages')),
            '통제': 통제옮기기(권역, r.get('restricted')),
            '관광안내': ({'이름': None, '주소': r.get('tourUrl')}
                         if r.get('tourUrl') else None),
        }
        for k in 센것:
            센것[k] += len(한권역[k])
        묶음별.setdefault(묶음, []).append(한권역)

    print('권역 여행 자료 옮기기')
    print('  옛 사이트: %s' % OLD)
    print('')
    print('  묶음        권역  명소 먹거리 축제 어종 코스 마을 통제')
    for 묶음 in sorted(묶음별):
        목록 = 묶음별[묶음]
        print('  %-12s %3d %5d %5d %4d %4d %4d %4d %4d' % (
            묶음, len(목록),
            sum(len(x['명소']) for x in 목록),
            sum(len(x['먹거리']) for x in 목록),
            sum(len(x['축제']) for x in 목록),
            sum(len(x['어종']) for x in 목록),
            sum(len(x['코스']) for x in 목록),
            sum(len(x['마을']) for x in 목록),
            sum(len(x['통제']) for x in 목록)))
    print('')
    print('  합계  권역 %d · %s' % (
        sum(len(v) for v in 묶음별.values()),
        ' · '.join('%s %d' % (k, v) for k, v in 센것.items())))
    print('')
    print('  ~ 전남 15권역은 여기 없습니다 — 자료가 없어 쪽에서 캐냅니다')
    print('    (engine/extract_jeonnam_travel.py)')
    print('')

    # 비어 있는 칸이 많으면 알립니다 — 뽑기가 실패한 것일 수 있습니다
    빈것 = []
    for 묶음, 목록 in 묶음별.items():
        for x in 목록:
            if not x['명소'] and not x['먹거리']:
                빈것.append(x['id'])
    if 빈것:
        print('  ~ 명소도 먹거리도 없는 권역 %d곳: %s'
              % (len(빈것), ' · '.join(빈것[:6])))
        print('')

    if 쓰기:
        for 묶음, 목록 in sorted(묶음별.items()):
            목록.sort(key=lambda x: x['id'])
            io.write_json(os.path.join(DATA, 'raw', 'travel', '%s.json' % 묶음), {
                '_설명': '%s 권역의 명소·먹거리·축제·어종·코스·마을·통제. '
                         '옮기는 도구가 만듭니다 — 손으로 고치려면 '
                         'data/overrides/travel/ 에' % 묶음,
                '권역': 목록,
            })
        print('자료에 썼습니다: data/raw/travel/')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
