# -*- coding: utf-8 -*-
"""어종 안내 자료를 옮깁니다 — 낚시 어종·해루질 대상.

무엇을 옮기나
    data/fish-guide.json      낚시 어종 18가지 (채비·미끼·방법·먹는 법)
    data/catch-guide.json     해루질 대상 17가지 (깊이·흔적·손질법)
    data/species-index.json   철·권역·금어기·크기 제한

    셋이 같은 어종을 다루면서 따로 놀았습니다. 하나로 합칩니다.

★ 이미 옮겨 둔 species.json 과 잇습니다
    포인트가 가리키는 어종 아이디(gamseongdom …)와 같은 것이어야
    「이 어종을 잡을 수 있는 포인트」를 보여 줄 수 있습니다.
    이름이 다르면 그 연결이 끊깁니다 — 여기서 맞춰 둡니다.

쓰는 법
    python engine/migrate_guide.py            보여만 줍니다
    python engine/migrate_guide.py --write    씁니다
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


def 글(s):
    return re.sub(r'\s+', ' ', (s or '')).strip() or None


def 목록(v):
    return [글(x) for x in (v or []) if 글(x)]


def 꺼내기(파일):
    d = io.read_json(os.path.join(OLD, 'data', 파일), default=None)
    if d is None:
        return []
    if isinstance(d, list):
        return d
    for v in d.values():
        if isinstance(v, list) and v:
            return v
    return []


def main():
    쓰기 = '--write' in sys.argv

    낚시 = 꺼내기('fish-guide.json')
    해루질 = 꺼내기('catch-guide.json')
    색인 = 꺼내기('species-index.json')
    if not 낚시 and not 해루질:
        print('옛 어종 자료를 찾지 못했습니다: %s' % OLD)
        return 1

    색인표 = dict((x.get('slug'), x) for x in 색인)

    # 이미 옮겨 둔 어종 아이디 — 이름으로 맞춥니다
    있는어종 = io.read_json(os.path.join(DATA, 'raw', 'species.json'),
                            default={}).get('어종', [])
    이름으로 = dict((x['이름']['ko'], x['id']) for x in 있는어종)

    # ★ 나오는 권역은 **포인트 자료에서 셉니다** (계약-06)
    #   옛 색인(species-index.json)은 손으로 적은 것이라 빈 것이 있었습니다.
    #   주꾸미는 안내 쪽이 있는데 철·권역이 통째로 비어 있었습니다.
    #   셀 수 있는 것은 세어서 넣습니다.
    import glob as _glob
    권역센것 = {}
    for _p in sorted(_glob.glob(os.path.join(DATA, 'raw', 'points', '*.json'))):
        for x in io.read_json(_p, default={}).get('포인트', []):
            for 아 in (x.get('대상') or []):
                권역센것.setdefault(아, set()).add(x['권역'])

    나옴 = []
    끊긴것 = []
    for 목록이름, 것들, 갈래 in (('낚시', 낚시, '낚시'),
                                 ('해루질', 해루질, '해루질')):
        for x in 것들:
            slug = x.get('slug')
            이름 = 글(x.get('n'))
            s = 색인표.get(slug) or {}
            # 포인트가 쓰는 어종 아이디와 이어지는가
            이어짐 = 이름으로.get(이름)
            if not 이어짐:
                끊긴것.append('%s(%s)' % (이름, slug))
            나옴.append({
                'id': slug,
                '갈래': 갈래,
                '이름': {'ko': 이름, 'zh': None},
                '딴이름': 목록(x.get('alias')),
                '무리': 글(x.get('kind')),
                '어려움': 글(x.get('level')),
                '한줄': {'ko': 글(x.get('one')), 'zh': None},
                '어디서': {'ko': 글(x.get('where')), 'zh': None},
                '언제': {'ko': 글(x.get('when')), 'zh': None},
                '채비': {'ko': 글(x.get('rig')), 'zh': None},
                '미끼': {'ko': 글(x.get('bait')), 'zh': None},
                '이렇게': [{'ko': v, 'zh': None} for v in 목록(x.get('how'))],
                '귀띔': {'ko': 글(x.get('tip')), 'zh': None},
                '먹는법': {'ko': 글(x.get('eat')), 'zh': None},
                '손질법': {'ko': 글(x.get('clean')), 'zh': None},
                '깊이cm': x.get('depthCm'),
                '흔적': {'ko': 글(x.get('sign')), 'zh': None},
                '그림': 글(x.get('rigArt') or x.get('art')),
                '철': s.get('months') or [],
                # 포인트에서 센 권역을 먼저 씁니다. 없으면 옛 색인을
                '나오는권역': (sorted(권역센것.get(이어짐) or [])
                               or (s.get('regions') or [])),
                '금어기': 글(s.get('banText')) or None,
                '크기제한': 글(s.get('size')) or None,
                '고시로정함': bool(s.get('byNotice')),
                '어종아이디': 이어짐,          # species.json 과 잇는 고리
            })

    print('어종 안내 자료 옮기기')
    print('  옛 사이트: %s' % OLD)
    print('')
    낚시수 = sum(1 for x in 나옴 if x['갈래'] == '낚시')
    해루수 = len(나옴) - 낚시수
    print('  낚시 어종 %d가지 · 해루질 대상 %d가지 · 합계 %d'
          % (낚시수, 해루수, len(나옴)))
    print('')

    칸들 = ('한줄', '어디서', '언제', '채비', '미끼', '귀띔',
            '먹는법', '손질법', '흔적')

    def 채워졌나(v):
        if isinstance(v, dict):
            return bool(v.get('ko'))
        return bool(v)

    print('  칸이 채워진 비율')
    for k in 칸들:
        n = sum(1 for x in 나옴 if 채워졌나(x[k]))
        print('    %-8s %3d / %d  (%.0f%%)'
              % (k, n, len(나옴), 100.0 * n / max(len(나옴), 1)))
    n = sum(1 for x in 나옴 if x['이렇게'])
    print('    %-8s %3d / %d  (%.0f%%)'
          % ('이렇게', n, len(나옴), 100.0 * n / max(len(나옴), 1)))
    print('')

    # 철·권역이 붙었는가
    철없음 = [x['id'] for x in 나옴 if not x['철']]
    권역없음 = [x['id'] for x in 나옴 if not x['나오는권역']]
    센것 = sum(1 for x in 나옴 if x['어종아이디'] and 권역센것.get(x['어종아이디']))
    print('  · 나오는 권역을 포인트에서 센 어종 %d가지' % 센것)
    if 철없음:
        print('  ~ 철이 없는 어종 %d가지: %s' % (len(철없음), ' · '.join(철없음)))
        print('    (옛 색인에 안 적혀 있습니다. 안내 쪽은 그대로 나옵니다)')
    if 권역없음:
        print('  ~ 나오는 권역이 없는 어종 %d가지: %s'
              % (len(권역없음), ' · '.join(권역없음)))
        print('    (포인트에도 옛 색인에도 없습니다 — 민물·기수역 종일 수 있습니다)')
    print('')

    # ★ 포인트가 쓰는 어종과 이어졌는가 — 안 이어지면 「이 어종 잡는 곳」이 빕니다
    if 끊긴것:
        print('  ★ 포인트의 어종과 못 이은 것 %d가지' % len(끊긴것))
        for x in 끊긴것:
            print('      %s' % x)
        print('    이 어종들은 「잡을 수 있는 포인트」를 못 보여 줍니다.')
        print('    engine/fix_species.py 의 이름과 맞는지 보세요.')
        print('')
    else:
        print('  · 모든 어종이 포인트 자료와 이어집니다')
        print('')

    if 쓰기:
        나옴.sort(key=lambda x: (x['갈래'], x['id']))
        io.write_json(os.path.join(DATA, 'raw', 'guide.json'), {
            '_설명': '낚시 어종·해루질 대상 안내. 채비·미끼·방법·금어기까지. '
                     '어종아이디 로 species.json 과 이어집니다',
            '어종': 나옴,
        })
        print('자료에 썼습니다: data/raw/guide.json')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
