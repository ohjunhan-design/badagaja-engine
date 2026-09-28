# -*- coding: utf-8 -*-
"""옛 사이트의 자료를 새 구조로 옮깁니다.  (계약-26)

규칙
    · **멱등입니다.** 같은 자료를 넣으면 늘 같은 결과가 나옵니다.
      몇 번을 돌려도 됩니다 (계약-26)
    · `data/raw/` 만 씁니다. `data/overrides/` 는 **절대 건드리지 않습니다** (계약-20)
    · 아이디는 한 번 정하면 바뀌지 않습니다. 이름이 바뀌어도 그대로 둡니다
    · 먼저 보여 주고, `--write` 를 붙여야 씁니다

쓰는 법
    python engine/migrate.py                    무엇이 바뀔지 보여만 줍니다
    python engine/migrate.py --write            씁니다
    python engine/migrate.py --only taean       한 권역만 (수직 슬라이스용)
"""
import os
import re
import sys
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

# 옛 사이트가 있는 자리
OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')

# 자료가 나갈 자리. 시험이 딴 자리를 줄 수 있어야 합니다 —
# 안 그러면 멱등성 시험이 진짜 자료를 덮어씁니다 (2026-09-26)
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 묶음 이름 ↔ 옛 자료 파일
# 옛 사이트는 충남만 이름에 묶음이 없고(coast-points.json 이 전남),
# 전남은 아예 이 체계 밖에 있었습니다. 그 예외를 여기서 끝냅니다 (계약-02)
GROUPS = {
    'chungnam':   'coast-points-chungnam.json',   # 옛 이름은 coast-points.json 이 아님 — 아래에서 찾음
    'jeonbuk':    'coast-points-jeonbuk.json',
    'gyeongnam':  'coast-points-gyeongnam.json',
    'busanulsan': 'coast-points-busanulsan.json',
    'gyeongbuk':  'coast-points-gyeongbuk.json',
    'gangwon':    'coast-points-gangwon.json',
    'sudogwon':   'coast-points-sudogwon.json',
    'jeju':       'coast-points-jeju.json',
}

# 어종 이름 → 아이디. 옛 자료는 한글 이름만 있어 아이디로 바꿔야 잇습니다.
# 여기 없는 이름이 나오면 알립니다 — 조용히 버리지 않습니다
SPECIES_ID = {}


def 어종아이디(이름):
    """한글 어종 이름을 아이디로. 없으면 만들어 쓰고 기록해 둡니다."""
    이름 = (이름 or '').strip()
    if not 이름:
        return None
    if 이름 in SPECIES_ID:
        return SPECIES_ID[이름]
    # 아이디는 겹치지 않게 순번으로. 이름이 바뀌어도 아이디는 그대로입니다
    아이디 = 'sp-%03d' % (len(SPECIES_ID) + 1)
    SPECIES_ID[이름] = 아이디
    return 아이디


def 좌표검사(위도, 경도, 어디):
    """한반도 범위인가. 위도·경도를 뒤바꿔 넣으면 여기서 잡힙니다 (계약-25)"""
    탈 = []
    if 위도 is None or 경도 is None:
        탈.append('%s — 좌표가 없음' % 어디)
        return 탈
    if not (33.0 <= 위도 <= 39.0):
        탈.append('%s — 위도 %.4f 가 한반도 밖 (33~39)' % (어디, 위도))
    if not (124.0 <= 경도 <= 132.0):
        탈.append('%s — 경도 %.4f 가 한반도 밖 (124~132)' % (어디, 경도))
    # 뒤바뀐 것으로 보이면 따로 알립니다 — 가장 흔한 사고입니다
    if 33.0 <= 경도 <= 39.0 and 124.0 <= 위도 <= 132.0:
        탈.append('%s — 위도·경도가 뒤바뀐 것 같습니다 (%.4f, %.4f)' % (어디, 위도, 경도))
    return 탈


def 출입등급(p):
    """옛 자료의 여러 표시를 하나로 모읍니다.

    옛 사이트는 ferry·ctrl·warn 이 흩어져 있어 '갈 수 있는가' 를
    한눈에 알 수 없었습니다.
    """
    if p.get('ferry'):
        return '배로만'
    ctrl = (p.get('ctrl') or '').strip()
    if ctrl == 'full':
        return '금지'
    if ctrl:
        return '허가필요'
    warn = (p.get('warn') or '') + ' ' + (p.get('note') or '')
    if re.search(r'통제|금지|출입\s*제한|단속', warn):
        return '확인필요'
    return '자유'


def 포인트옮기기(권역, 갈래, 차례, p):
    """포인트 하나를 새 모양으로. 아이디는 여기서 확정합니다."""
    갈래표 = 'f' if 갈래 == 'fishing' else 'g'
    대상 = [어종아이디(x) for x in (p.get('targets') or [])]
    return {
        'id': '%s-%s-%03d' % (권역, 갈래표, 차례),
        '권역': 권역,
        '갈래': '낚시' if 갈래 == 'fishing' else '해루질',
        '이름': {'ko': (p.get('name') or '').strip(), 'zh': None},
        '좌표': {'위도': p.get('lat'), '경도': p.get('lng')},
        '지형': (p.get('terrain') or '').strip() or None,
        '대상': [x for x in 대상 if x],
        '철': (p.get('season') or '').strip() or None,
        '등급': (p.get('grade') or '').strip() or None,
        '방법': (p.get('how') or '').strip() or None,
        '메모': (p.get('note') or '').strip() or None,
        '배로가나': bool(p.get('ferry')),
        '출입': 출입등급(p),
    }


def 묶음찾기():
    """옛 사이트의 포인트 자료 파일을 묶음별로 찾습니다.

    옛 이름 규칙이 들쭉날쭉합니다 — coast-points.json 하나만 묶음 이름이 없고,
    전남은 아예 이 체계 밖입니다. 여기서 정리합니다.
    """
    찾음 = {}
    import glob
    for p in sorted(glob.glob(os.path.join(OLD, 'data', 'coast-points*.json'))):
        b = os.path.basename(p)
        if b == 'coast-points-index.json':
            continue
        m = re.match(r'coast-points-([a-z]+)\.json$', b)
        키 = m.group(1) if m else None
        if 키 is None and b == 'coast-points.json':
            # 옛 사이트에서 이 파일이 무슨 묶음인지 안에서 확인합니다
            d = io.read_json(p, default={})
            첫권역 = (d.get('regions') or [{}])[0].get('slug', '')
            키 = 'jeonnam' if 첫권역 in ('sinan', 'muan', 'mokpo', 'yeosu') else 'chungnam'
        if 키:
            찾음[키] = p
    return 찾음


def main():
    쓰기 = '--write' in sys.argv
    만 = None
    if '--only' in sys.argv:
        i = sys.argv.index('--only')
        if i + 1 < len(sys.argv):
            만 = sys.argv[i + 1]

    if not os.path.isdir(OLD):
        print('옛 사이트를 찾지 못했습니다: %s' % OLD)
        print('  BADAGAJA_OLD 환경변수로 자리를 알려 주세요')
        return 1

    파일들 = 묶음찾기()
    print('옛 자료 → 새 구조로 옮기기')
    print('  옛 사이트: %s' % OLD)
    print('  찾은 묶음: %d개' % len(파일들))
    if 만:
        print('  이번에는 %s 만 옮깁니다' % 만)
    print('')

    묶음별 = collections.defaultdict(list)
    탈 = []
    모두 = 0

    for 묶음, 경로 in sorted(파일들.items()):
        d = io.read_json(경로, default={})
        for r in d.get('regions', []):
            권역 = r.get('slug')
            if not 권역 or (만 and 권역 != 만):
                continue
            for 갈래 in ('fishing', 'gleaning'):
                for i, p in enumerate(r.get(갈래) or [], 1):
                    새것 = 포인트옮기기(권역, 갈래, i, p)
                    탈 += 좌표검사(새것['좌표']['위도'], 새것['좌표']['경도'],
                                  '%s (%s)' % (새것['id'], 새것['이름']['ko']))
                    if not 새것['이름']['ko']:
                        탈.append('%s — 이름이 없음' % 새것['id'])
                    묶음별[묶음].append(새것)
                    모두 += 1

    for 묶음, 목록 in sorted(묶음별.items()):
        낚시 = sum(1 for x in 목록 if x['갈래'] == '낚시')
        해루질 = len(목록) - 낚시
        print('  %-12s %4d곳  (낚시 %d · 해루질 %d)' % (묶음, len(목록), 낚시, 해루질))
    print('  %-12s %4d곳' % ('합계', 모두))
    print('')

    if 탈:
        print('★ 살펴볼 것 %d건' % len(탈))
        for x 	in 탈[:10]:
            print('    %s' % x)
        if len(탈) > 10:
            print('    … 그 밖 %d건' % (len(탈) - 10))
        print('')

    if 쓰기:
        for 묶음, 목록 in sorted(묶음별.items()):
            목록.sort(key=lambda x: x['id'])     # 차례 고정 (계약-07)
            io.write_json(os.path.join(DATA, 'raw', 'points', '%s.json' % 묶음), {
                '_설명': '%s 포인트. 옮기는 도구가 만듭니다 — 손으로 고치려면 data/overrides/ 에' % 묶음,
                '포인트': 목록,
            })
        # 어종 이름표도 함께 남깁니다 — 아이디를 고정하기 위해
        io.write_json(os.path.join(DATA, 'raw', 'species-map.json'), {
            '_설명': '옛 자료의 어종 이름 → 아이디. 이름이 바뀌어도 아이디는 그대로 둡니다',
            '이름표': SPECIES_ID,
        })
        print('자료에 썼습니다. (data/raw/points/)')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
