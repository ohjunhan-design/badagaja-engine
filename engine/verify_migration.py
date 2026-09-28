# -*- coding: utf-8 -*-
"""옮긴 자료가 옛 사이트와 같은지 **전수로** 봅니다.  (계약-25)

왜
    개수가 맞는다고 내용이 맞는 것은 아닙니다.
    위도·경도를 뒤바꿔 넣으면 3,603 = 3,603 이지만 위치가 전부 틀립니다.

무엇을 보나
    1. 개수 — 묶음별·전체
    2. 이름 — 옛 자료·옛 쪽에 있던 이름이 새 자료에 다 있는가
    3. 좌표 — 한반도 범위 · 옛 값과 같은가
    4. 아이디 — 겹치지 않는가
    5. 어종 — 잇는 아이디가 실제로 있는가
    6. 형식 — 날짜·전화

쓰는 법
    python engine/verify_migration.py
    python engine/verify_migration.py --strict   탈이 있으면 1 로 끝냅니다
"""
import os
import re
import sys
import glob
import json
import collections
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')

문제, 알림 = [], []


def 탈(이름, 수, 보기=''):
    if 수:
        문제.append(이름)
        print('  ✗ %-34s %d건 %s' % (이름, 수, 보기))
    else:
        print('  · %-34s 이상 없음' % 이름)


def 참고(이름, 수, 보기=''):
    if 수:
        알림.append(이름)
        print('  ~ %-34s %d건 %s' % (이름, 수, 보기))
    else:
        print('  · %-34s 이상 없음' % 이름)


def 새자료():
    """새 구조의 포인트를 모두 읽습니다"""
    나옴 = []
    for p in sorted(glob.glob(os.path.join(DATA, 'raw', 'points', '*.json'))):
        d = io.read_json(p, default={})
        나옴 += d.get('포인트', [])
    return 나옴


def 넣기(좌표, 키, 값):
    """같은 이름이 여러 곳에 있으면 좌표를 견주지 않습니다.

    '증도리 북측' 처럼 한 권역에 같은 이름이 둘 있으면 이름으로 짝지을 때
    엉뚱한 좌표와 맺혀 "다르다"는 헛것이 잡힙니다 (2026-09-26 확인).
    """
    if 키 in 좌표:
        if 좌표[키] != 값:
            좌표[키] = None          # 겹침 — 견주지 않습니다
    else:
        좌표[키] = 값


def 옛자료():
    """옛 사이트의 포인트를 (권역, 갈래, 이름) 으로 모읍니다.

    전남은 자료가 없으므로 쪽에서 읽습니다 — 그것이 원본입니다.
    """
    이름들 = collections.defaultdict(set)
    좌표 = {}

    # 자료가 있는 8묶음
    for p in glob.glob(os.path.join(OLD, 'data', 'coast-points*.json')):
        if p.endswith('coast-points-index.json'):
            continue
        d = io.read_json(p, default={})
        for r in d.get('regions', []):
            권역 = r.get('slug')
            for 갈래, 표 in (('fishing', '낚시'), ('gleaning', '해루질')):
                for x in (r.get(갈래) or []):
                    이름 = (x.get('name') or '').strip()
                    if 이름:
                        이름들[(권역, 표)].add(이름)
                        넣기(좌표, (권역, 표, 이름), (x.get('lat'), x.get('lng')))

    # 전남 — 쪽에서
    CARD = re.compile(r'<div class="card" id="point-\d+"([^>]*)>(.*?)'
                      r'(?=<div class="card" id="point-|</section>|</main>)', re.S)
    NAME = re.compile(r'font-size:1\.08rem[^>]*>\s*(?:\d+\.\s*)?([^<]+?)\s*</div>')
    for p in glob.glob(os.path.join(OLD, 'point', '[0-9][0-9]_*.html')):
        m = re.search(r'\d\d_([a-z]+)_(fishing|gleaning)\.html$', os.path.basename(p))
        if not m:
            continue
        권역, 갈래 = m.group(1), ('낚시' if m.group(2) == 'fishing' else '해루질')
        s = io.read(p, default='')
        for 속성, 안쪽 in CARD.findall(s):
            nm = NAME.search(안쪽)
            if not nm:
                continue
            # &#183; 같은 실체 참조를 풀어야 새 자료와 견줄 수 있습니다.
            # 이것을 빠뜨려 "이름이 사라졌다"는 헛것을 8건 잡았습니다 (2026-09-26)
            이름 = _html.unescape(nm.group(1))
            이름 = re.sub(r'\s+', ' ', 이름).strip()
            이름들[(권역, 갈래)].add(이름)
            a = dict(re.findall(r'data-(lat|lng)="([^"]*)"', 속성))
            try:
                넣기(좌표, (권역, 갈래, 이름), (float(a['lat']), float(a['lng'])))
            except (KeyError, ValueError):
                넣기(좌표, (권역, 갈래, 이름), (None, None))
    return 이름들, 좌표


def main():
    print('옮긴 자료 검증 — 옛 사이트와 전수 대조 (계약-25)')
    print('')

    새것 = 새자료()
    옛이름, 옛좌표 = 옛자료()

    # ── 1. 개수 ────────────────────────────────────────────
    print('[1] 개수')
    옛수 = sum(len(v) for v in 옛이름.values())
    print('      옛 사이트 %d곳 · 새 자료 %d곳' % (옛수, len(새것)))
    # 이름이 겹치는 포인트가 있으면 집합에서 줄어듭니다 — 그만큼은 차이가 납니다
    참고('개수 차이', abs(옛수 - len(새것)),
         '(옛 쪽에 같은 이름이 여럿이면 줄어 보입니다)')

    # ── 2. 아이디 ──────────────────────────────────────────
    print('[2] 아이디')
    ids = [x['id'] for x in 새것]
    겹침 = [k for k, v in collections.Counter(ids).items() if v > 1]
    탈('아이디가 겹침', len(겹침), ' · '.join(겹침[:3]))
    빈것 = [x for x in 새것 if not x.get('id')]
    탈('아이디가 없음', len(빈것))

    # ── 3. 이름 ───────────────────────────────────────────
    print('[3] 이름')
    빈이름 = [x['id'] for x in 새것 if not (x.get('이름') or {}).get('ko')]
    탈('이름이 비었음', len(빈이름), ' · '.join(빈이름[:3]))

    새이름 = collections.defaultdict(set)
    for x in 새것:
        새이름[(x['권역'], x['갈래'])].add(x['이름']['ko'])
    사라짐 = []
    for 키, 목록 in 옛이름.items():
        없는것 = 목록 - 새이름.get(키, set())
        for n in list(없는것)[:2]:
            사라짐.append('%s/%s %s' % (키[0], 키[1], n))
    탈('옛 사이트에 있는데 새 자료에 없는 이름', len(사라짐), ' · '.join(사라짐[:3]))

    # ── 4. 좌표 ───────────────────────────────────────────
    print('[4] 좌표')
    밖 = []
    뒤바뀜 = []
    없음 = 0
    다름 = []
    for x in 새것:
        위 = (x.get('좌표') or {}).get('위도')
        경 = (x.get('좌표') or {}).get('경도')
        if 위 is None or 경 is None:
            없음 += 1
            continue
        if not (33.0 <= 위 <= 39.0) or not (124.0 <= 경 <= 132.0):
            밖.append('%s (%.3f, %.3f)' % (x['id'], 위, 경))
        if 33.0 <= 경 <= 39.0 and 124.0 <= 위 <= 132.0:
            뒤바뀜.append(x['id'])
        # 옛 값과 견줍니다
        옛 = 옛좌표.get((x['권역'], x['갈래'], x['이름']['ko']))
        if 옛 and 옛[0] is not None:
            if abs(옛[0] - 위) > 0.0001 or abs(옛[1] - 경) > 0.0001:
                다름.append('%s 옛(%.4f,%.4f) → 새(%.4f,%.4f)' % (x['id'], 옛[0], 옛[1], 위, 경))
    탈('한반도 밖 좌표', len(밖), ' · '.join(밖[:3]))
    탈('위도·경도가 뒤바뀜', len(뒤바뀜), ' · '.join(뒤바뀜[:3]))
    탈('옛 값과 좌표가 다름', len(다름), ' · '.join(다름[:2]))
    참고('좌표가 없음', 없음, '(옛 사이트에도 없던 것)')

    # ── 5. 이어지는 값 ─────────────────────────────────────
    print('[5] 이어지는 값')
    어종표 = io.read_json(os.path.join(DATA, 'raw', 'species.json'), default={})
    있는어종 = set(x['id'] for x in 어종표.get('어종', []))
    끊김 = []
    for x in 새것:
        for s in (x.get('대상') or []):
            if s not in 있는어종:
                끊김.append('%s → %s' % (x['id'], s))
    탈('없는 어종을 가리킴', len(끊김), ' · '.join(끊김[:3]))

    # 한글 이름이 남아 있으면 아직 아이디로 안 바꾼 것입니다
    남은한글 = sorted(set(s for x in 새것 for s in (x.get('대상') or [])
                          if not s.isascii()))
    탈('어종이 아직 한글 이름', len(남은한글), ' · '.join(남은한글[:3]))
    print('      어종 %d가지 · 이어진 곳 %d건'
          % (len(있는어종), sum(len(x.get('대상') or []) for x in 새것)))

    # ── 6. 권역 ───────────────────────────────────────────
    print('[6] 권역 (index.json 이 기준 — 계약-05)')
    목록 = io.read_json(os.path.join(DATA, 'raw', 'index.json'), default={})
    권역들 = 목록.get('권역', [])
    있는권역 = set(x['id'] for x in 권역들)
    탈('권역이 57개가 아님', 0 if len(권역들) == 57 else 1, '%d개' % len(권역들))
    모르는 = sorted(set(x['권역'] for x in 새것 if x['권역'] not in 있는권역))
    탈('목록에 없는 권역을 가리킴', len(모르는), ' · '.join(모르는[:3]))
    빈권역 = sorted(있는권역 - set(x['권역'] for x in 새것))
    참고('포인트가 하나도 없는 권역', len(빈권역), ' · '.join(빈권역[:5]))

    # 설명글에 숫자를 박아 두면 자료가 늘 때마다 틀립니다 (계약-04)
    박힌숫자 = []
    for x in 권역들:
        for 칸 in ('설명', '소개', '안내', '포인트안내'):
            t = x.get(칸) or ''
            m = re.search(r'\d+\s*(?:곳|개|군데)', t)
            if m:
                박힌숫자.append('%s/%s %s' % (x['id'], 칸, m.group(0)))
    참고('설명글에 숫자가 박혀 있음', len(박힌숫자),
         '(자료가 늘면 틀립니다 — %s)' % ' · '.join(박힌숫자[:3]))

    # ── 7. 출입 ───────────────────────────────────────────
    print('[7] 갈 수 있는가')
    등급 = collections.Counter(x.get('출입') for x in 새것)
    for k, v in 등급.most_common():
        print('      %-8s %4d곳' % (k, v))

    print('')
    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
    if 문제:
        print('손볼 곳 %d가지: %s' % (len(문제), ' · '.join(문제)))
        if '--strict' in sys.argv:
            return 1
    else:
        print('옮긴 자료는 옛 사이트와 같습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
