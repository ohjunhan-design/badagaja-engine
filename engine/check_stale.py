# -*- coding: utf-8 -*-
"""자료가 **어중간한 자리에 멈춰 있는지** 봅니다.

★ 왜 이 검사가 필요한가 (2026-09-26, tests/test_idempotent.py 가 잡음)

    이관 도구는 앞뒤가 있습니다.

        migrate.py      포인트를 캐 씁니다 — 대상이 「감성돔」
        fix_species.py  그 파일을 열어 아이디로 — 「gamseongdom」

    자료를 갱신하려고 migrate 만 다시 돌리면 뒤엣것이 안 돌아
    대상이 다시 한글 이름으로 돌아갑니다. 그런데

        파일 개수     그대로
        포인트 수     그대로
        빈 칸 수      그대로

    **개수를 세는 검사는 하나도 못 잡습니다.**
    쪽은 만들어지고, 어종 안내만 조용히 텅 빕니다.

    engine/refresh.py 가 차례를 묶어 두었지만, 사람이 급할 때
    도구를 직접 부를 수 있습니다. 그때를 여기서 잡습니다.

무엇을 보나
    1. 다 끝난 도구가 지웠어야 할 파일이 남아 있는가
    2. 대상이 아이디가 아니라 한글 이름인가
    3. 포인트가 가리키는 어종이 species.json 에 있는가

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_stale.py
    python engine/check_stale.py --strict
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402
from engine import io   # noqa: E402

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 다 끝났으면 없어야 할 파일 — 있으면 앞 도구만 돌린 것입니다
남으면안되는것 = {
    'raw/species-map.json':
        'migrate.py 가 만들고 fix_species.py 가 지웁니다. '
        '남아 있으면 fix_species 를 안 돌린 것입니다',
}

아이디꼴 = re.compile(r'^[a-z][a-z0-9_-]*$')
한글 = re.compile(r'[가-힣]')

# 검사 등급 (계약-21)
#   막음 — 자료가 어중간합니다. 쪽이 조용히 텅 빕니다
#   알림 — 살펴볼 만한 것. 막지 않습니다
막음, 알림 = [], []


def main():
    print('자료가 어중간한 자리에 멈춰 있는지')
    print('  자리: %s' % DATA)
    print('')

    # ── 1. 다 끝났으면 없어야 할 파일
    print('[1] 앞 도구만 돌린 흔적이 있는가')
    남은것 = []
    for 길, 왜 in sorted(남으면안되는것.items()):
        if os.path.exists(os.path.join(DATA, 길)):
            남은것.append((길, 왜))
    if 남은것:
        막음.append('앞 도구만 돌린 흔적 %d개' % len(남은것))
        for 길, 왜 in 남은것:
            print('  ✗ %s 가 남아 있습니다' % 길)
            print('      %s' % 왜)
    else:
        print('  · 남은 흔적이 없습니다')
    print('')

    # ── 2. 대상이 아이디인가
    print('[2] 포인트의 대상이 아이디인가 (한글 이름이 아니라)')
    파일들 = sorted(glob.glob(os.path.join(DATA, 'raw', 'points', '*.json')))
    # ★ 자료가 0개면 **아무것도 안 보고 통과**였습니다 (2026-10-08)
    mustmeasure.있어야한다(파일들, '포인트 자료', 최소=5,
                           어디=os.path.join(DATA, 'raw', 'points'))
    읽은자료 = 0
    한글대상 = {}
    본포인트 = 0
    쓰인아이디 = set()
    for p in 파일들:
        d = io.read_json(p, default={})
        읽은자료 += 1 if d else 0
        이름 = os.path.basename(p)
        for x in d.get('포인트', []):
            본포인트 += 1
            for s in (x.get('대상') or []):
                if 한글.search(s or '') or not 아이디꼴.match(s or ''):
                    한글대상.setdefault(이름, []).append(s)
                else:
                    쓰인아이디.add(s)
    print('      포인트 %d곳 · 어종 아이디 %d가지' % (본포인트, len(쓰인아이디)))
    if 한글대상:
        수 = sum(len(v) for v in 한글대상.values())
        막음.append('대상이 아이디가 아님 %d건' % 수)
        print('  ✗ 대상이 아이디가 아닌 것 %d건 (파일 %d개)'
              % (수, len(한글대상)))
        for 이름 in sorted(한글대상)[:4]:
            보기 = 한글대상[이름][:3]
            print('      %-22s %d건   %s'
                  % (이름, len(한글대상[이름]), ' · '.join(보기)))
        print('      → fix_species.py 를 안 돌렸습니다.')
        print('        python engine/refresh.py --write 로 차례 전체를 돌리세요.')
    else:
        print('  · 모든 대상이 아이디입니다')
    print('')

    # ── 3. 가리키는 어종이 있는가
    # ★ 목록은 있는데 **내용을 하나도 못 읽으면** 못잼입니다
    mustmeasure.있어야한다(range(읽은자료), '읽은 포인트 자료',
                           최소=5, 어디=DATA)

    print('[3] 포인트가 가리키는 어종이 자료에 있는가')
    어종 = io.read_json(os.path.join(DATA, 'raw', 'species.json'), default={})
    있는것 = set(x.get('id') for x in (어종.get('어종') or []))
    print('      species.json 에 어종 %d가지' % len(있는것))
    없는것 = sorted(쓰인아이디 - 있는것)
    if 없는것:
        막음.append('없는 어종을 가리킴 %d가지' % len(없는것))
        print('  ✗ 자료에 없는 어종을 가리킵니다 %d가지: %s'
              % (len(없는것), ' · '.join(없는것[:6])))
    elif not 있는것:
        막음.append('species.json 이 비어 있음')
        print('  ✗ species.json 이 비어 있습니다')
    else:
        print('  · 가리키는 어종이 모두 있습니다')
        안쓰는것 = sorted(있는것 - 쓰인아이디)
        if 안쓰는것:
            알림.append('아무 데서도 안 쓰는 어종 %d가지' % len(안쓰는것))
            print('  ~ 아무 데서도 안 쓰는 어종 %d가지: %s'
                  % (len(안쓰는것), ' · '.join(안쓰는것[:5])))
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
        print('  자료가 어중간합니다. 차례 전체를 한 번 돌리세요:')
        print('    python engine/refresh.py --write')
        return 1 if '--strict' in sys.argv else 0
    print('자료가 끝까지 다듬어져 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
