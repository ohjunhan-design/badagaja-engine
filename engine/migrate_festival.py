# -*- coding: utf-8 -*-
"""축제 쪽 자료를 옮깁니다 — 소개글·프로그램·가는 법까지.

무엇을 옮기나
    data/festival-notes.json   축제마다 손으로 쓴 소개글 191개
                               (조사해서 직접 쓴 글입니다. 가장 값진 자료입니다)
    data/festival-files.json   주소 고정표 197개
                               권역|축제이름 → festival/<파일>

★ 주소 고정표는 소개글보다 **여섯 개 많습니다**  (2026-09-26)
    포항 4개·제주시 3개는 **쪽 주소만 잡아 두고 소개글을 기다리는 것**입니다.
    예전에 이것을 「유령 자료」로 잘못 보고 지울 뻔했습니다.
    생성기 주석에 이유가 적혀 있었는데 안 읽었습니다.

    그래서 이번에는 **자료 안에 적어 둡니다** (계약-18).
    주석은 사람이 안 읽지만, 자료에 적으면 기계가 봅니다.

쓰는 법
    python engine/migrate_festival.py            보여만 줍니다
    python engine/migrate_festival.py --write    씁니다
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
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))


def 글(s):
    return re.sub(r'\s+', ' ', (s or '')).strip() or None


def 목록(v):
    return [글(x) for x in (v or []) if 글(x)]


def main():
    쓰기 = '--write' in sys.argv

    메모 = io.read_json(os.path.join(OLD, 'data', 'festival-notes.json'),
                        default={}).get('items', [])
    주소표 = io.read_json(os.path.join(OLD, 'data', 'festival-files.json'),
                          default={}).get('files', {})
    if not 메모 or not 주소표:
        print('옛 축제 자료를 찾지 못했습니다: %s' % OLD)
        return 1

    # 파일 이름 → 소개글
    소개 = dict((x['file'], x) for x in 메모)
    # 파일 이름 → (권역, 축제이름)
    어디 = {}
    for 키, 파일 in 주소표.items():
        권역, _, 이름 = 키.partition('|')
        어디[파일] = (권역, 이름)

    # 이미 옮겨 둔 축제(travel/)와 이름으로 맞춥니다
    이름표 = {}
    for p in sorted(glob.glob(os.path.join(DATA, 'raw', 'travel', '*.json'))):
        for r in io.read_json(p, default={}).get('권역', []):
            for x in r.get('축제') or []:
                이름표[(r['id'], x['이름']['ko'])] = x

    묶음찾기 = {}
    색인 = io.read_json(os.path.join(DATA, 'raw', 'index.json'), default={})
    for r in 색인.get('권역', []):
        묶음찾기[r['id']] = r['묶음']

    묶음별 = collections.defaultdict(list)
    기다리는것 = []
    못찾음 = []

    for 파일 in sorted(주소표.values()):
        권역, 이름 = 어디[파일]
        묶음 = 묶음찾기.get(권역)
        if not 묶음:
            못찾음.append('%s (권역 %s 를 모릅니다)' % (파일, 권역))
            continue
        n = 소개.get(파일)
        옛것 = 이름표.get((권역, 이름)) or {}

        항 = {
            'id': os.path.splitext(파일)[0],      # sinan-1
            '권역': 권역,
            '이름': {'ko': 이름, 'zh': None},
            '달': 옛것.get('달'),
            # ★ 자세한 장소가 없으면 축제 자료의 곳을 씁니다 (2026-09-26).
            #   처음에는 place_detail 만 보고 없으면 버렸습니다.
            #   「오천항 일원」이 「보령 일원」으로 뭉뚱그려졌습니다.
            '곳': ((글(n.get('place_detail')) if n else None)
                   or 옛것.get('곳')),
            '한줄': (옛것.get('설명') or {}).get('ko'),
            '소개': {'ko': 글(n.get('intro')) if n else None, 'zh': None},
            '프로그램': 목록(n.get('programs')) if n else [],
            '알아둘것': 목록(n.get('tips')) if n else [],
            '지난해': 글(n.get('history')) if n else None,
            '가는법': {'ko': 글(n.get('access')) if n else None, 'zh': None},
            '가까운곳': 목록(n.get('nearby')) if n else [],
            '바다이야기': {'ko': 글(n.get('seaTip')) if n else None, 'zh': None},
            '확실한가': 글(n.get('confidence')) if n else '확인필요',
            '메모': 글(n.get('note')) if n else None,   # 웹에 안 냅니다
            '소개글있나': bool(n),
        }
        묶음별[묶음].append(항)
        if not n:
            기다리는것.append('%s %s' % (권역, 이름))

    print('축제 자료 옮기기')
    print('  옛 사이트: %s' % OLD)
    print('')
    print('  묶음          축제  소개글 있음  기다리는 중')
    for 묶음 in sorted(묶음별):
        것들 = 묶음별[묶음]
        있음 = sum(1 for x in 것들 if x['소개글있나'])
        print('  %-12s %5d %8d %9d'
              % (묶음, len(것들), 있음, len(것들) - 있음))
    모두 = sum(len(v) for v in 묶음별.values())
    있음 = sum(1 for v in 묶음별.values() for x in v if x['소개글있나'])
    print('  %-12s %5d %8d %9d' % ('합계', 모두, 있음, 모두 - 있음))
    print('')

    if 기다리는것:
        print('  ~ 소개글을 기다리는 축제 %d개' % len(기다리는것))
        for x in 기다리는것:
            print('      %s' % x)
        print('    쪽 주소만 잡아 둔 것입니다. **지우면 안 됩니다** —')
        print('    주소를 잃으면 나중에 소개글을 넣어도 검색에서 끊깁니다.')
        print('')

    if 못찾음:
        print('  ★ 옮기지 못한 것 %d개' % len(못찾음))
        for x in 못찾음[:6]:
            print('      %s' % x)
        print('')

    # 채워진 정도 — 뽑기가 실패하면 여기서 드러납니다
    # 옛 자료에 있던 것을 잃지 않았는가 — 옮기다 흘리는 일이 잦습니다
    잃은것 = []
    for 묶음, 것들 in 묶음별.items():
        for x in 것들:
            옛것 = 이름표.get((x['권역'], x['이름']['ko'])) or {}
            if 옛것.get('곳') and not x['곳']:
                잃은것.append('%s 곳' % x['id'])
            if (옛것.get('설명') or {}).get('ko') and not x['한줄']:
                잃은것.append('%s 한줄' % x['id'])
            if 옛것.get('달') and not x['달']:
                잃은것.append('%s 달' % x['id'])
    if 잃은것:
        print('  ★ 옛 자료에 있던 것을 잃었습니다 %d건' % len(잃은것))
        for x in 잃은것[:8]:
            print('      %s' % x)
        print('')
    else:
        print('  · 옛 자료의 곳·한줄·달을 하나도 안 잃었습니다')
        print('')

    칸들 = ('소개', '프로그램', '알아둘것', '가는법', '가까운곳', '바다이야기')

    def 채워졌나(v):
        # ★ {'ko': None} 도 사전이라 참입니다 (2026-09-26).
        #   그대로 세면 빈 칸이 「100% 채워짐」으로 나옵니다.
        if isinstance(v, dict):
            return bool(v.get('ko'))
        return bool(v)

    print('  칸이 채워진 비율')
    모든것 = [x for v in 묶음별.values() for x in v]
    for k in 칸들:
        n = sum(1 for x in 모든것 if 채워졌나(x[k]))
        print('    %-10s %3d / %d  (%.0f%%)'
              % (k, n, len(모든것), 100.0 * n / max(len(모든것), 1)))
    print('')

    if 쓰기:
        for 묶음, 것들 in sorted(묶음별.items()):
            것들.sort(key=lambda x: x['id'])
            기다림 = [x['id'] for x in 것들 if not x['소개글있나']]
            자료 = {
                '_설명': '%s 축제. 소개글은 조사해서 직접 쓴 글입니다' % 묶음,
                '축제': 것들,
            }
            if 기다림:
                # ★ 계약-18 — 지우면 안 되는 것은 **자료에** 적습니다.
                #   주석은 사람이 안 읽지만 자료는 기계가 읽습니다.
                자료['_지우지_말_것'] = (
                    '아래 축제는 쪽 주소만 잡아 두고 소개글을 기다리는 것입니다. '
                    '비어 보인다고 지우면 주소를 잃고, 나중에 소개글을 넣어도 '
                    '검색에서 끊깁니다. (2026-09-26 — 예전에 지울 뻔했습니다)')
                자료['_기다리는_축제'] = 기다림
            io.write_json(
                os.path.join(DATA, 'raw', 'festivals', '%s.json' % 묶음), 자료)
        print('자료에 썼습니다: data/raw/festivals/')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
