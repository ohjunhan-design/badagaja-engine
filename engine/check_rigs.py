# -*- coding: utf-8 -*-
"""**채비 자료를 전수로 봅니다** (2026-09-30 주인 지시)

주인 말씀 — 「채비마다 전수검사하고 시중에서 파는제품 검색해서
              꼭 사실과 같도록 잘 만들어줘」
           「채비관련된건 매우 중요한 바다가자의 자산이야」

★ 왜 만들었나

    채비 그림은 이름을 보고 모양을 고릅니다(`art._부품모양`).
    그런데 **이름이 안 맞으면 조용히 빈 자리가 됩니다.**
    오류도 안 나고 쪽도 만들어집니다. 사람이 그림을 하나하나
    들여다보지 않으면 모릅니다.

    실제로 이렇게 당했습니다 (2026-09-30).

      · **막대찌** — 모양이 아예 없어 빈 자리가 될 뻔했습니다
      · **좁쌀봉돌** — `'봉돌' in 이름` 이 가로채 **고리봉돌**로
        그려져 **배포까지 나갔습니다**
      · **찌멈춤고무** — `'고무' in 이름` 이 가로채 검은 쿠션고무로
        그려질 뻔했습니다

    앞의 둘은 **사람 눈으로 겨우 찾았습니다.** 채비가 늘어날수록
    눈으로는 못 잡습니다. 그래서 기계가 봅니다 (주인 규칙 26 —
    「새 검사는 잡은 뒤에 만듭니다」).

★ 무엇을 보나

    [1] 자료가 갖춰졌는가 — 이름·대상·장비·부품·왜·근거
    [2] **모든 부품이 그림을 갖는가** ← 가장 중요합니다
    [3] 갈래마다 아이콘이 있는가
    [4] 쪽이 실제로 만들어졌는가
    [5] 그림 조건 차례가 안전한가 (넓은 이름이 좁은 이름을 가로채나)

`docs/채비자료-규칙.md` 에 만드는 규칙을 적어 두었습니다.
"""
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)
sys.path.insert(0, ROOT)

from engine import art                                    # noqa: E402
from engine import io                                     # noqa: E402
from engine import url                                    # noqa: E402

# ★ 다른 검사기와 같은 방식으로 **딴 자리를 가리킬 수 있게** 둡니다.
#   시험(tests/test_checkers.py)이 사본을 망가뜨려 「정말 잡는가」를
#   재려면 이 문이 있어야 합니다 (계약-28 — 검사기도 시험받는다).
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
나온곳 = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
자료길 = os.path.join(DATA, 'raw', 'rigs.json')

막음, 알림 = [], []


def 자료():
    글 = io.read(자료길, default='')
    if not 글:
        return {}
    return json.loads(글)


# ── [5] 그림 조건 차례가 안전한가 ─────────────────────────
#
#   `_부품모양()` 은 위에서부터 보고 **맞으면 거기서 끝냅니다.**
#   그래서 넓은 이름이 위에 있으면 좁은 이름을 통째로 가로챕니다.
#
#   아래 짝은 **가로채면 안 되는 것들**입니다.
#   왼쪽(좁은 이름)이 오른쪽(넓은 이름)보다 **위**에 있어야 합니다.
가로채면안되는짝 = [
    ('좁쌀', '봉돌'),          # 좁쌀봉돌 ≠ 고리봉돌
    ('찌멈춤', '고무'),        # 찌멈춤고무 ≠ O형 쿠션고무
    ('막대찌', '찌'),          # 막대찌 ≠ 구멍찌
    ('지그헤드', '봉돌'),      # 지그헤드는 봉돌+바늘 한 몸
    ('가지바늘', '바늘'),      # 가지바늘은 옆으로 뻗습니다
]


def 조건차례():
    """`_부품모양()` 안의 `if '…' in 이름` 을 나온 차례대로 모읍니다."""
    글 = io.read(os.path.join(여기, 'art.py'), default='')
    m = re.search(r'def _부품모양\(.*?\n(.*?)\ndef ', 글, re.S)
    몸 = m.group(1) if m else ''
    차례 = []
    for mm in re.finditer(r"if '([^']+)' in 이름", 몸):
        차례.append(mm.group(1))
    return 차례


def 먼저나오나(차례, 좁은, 넓은):
    """좁은 이름이 넓은 이름보다 먼저 나오는가.

    둘 중 하나가 아예 없으면 **가로챌 일도 없으므로** 참입니다.
    """
    if 좁은 not in 차례 or 넓은 not in 차례:
        return True
    return 차례.index(좁은) < 차례.index(넓은)


def main():
    엄격 = '--strict' in sys.argv
    d = 자료()
    채비 = (d or {}).get('채비') or {}
    if not 채비:
        print('채비 자료가 없습니다 — data/raw/rigs.json')
        print('NOT_TESTED')
        return 2

    print('채비 자료를 전수로 봅니다 (주인 지시 2026-09-30)')
    print('  갈래 %d가지' % len(채비))
    print('')

    # ── [1] 자료가 갖춰졌는가 ────────────────────────────
    print('[1] 갈래마다 있어야 할 것이 다 있는가')
    꼭있을것 = ('이름', '대상', '미끼', '장비', '부품', '왜', '_근거')
    빠진것 = []
    for 갈, 것 in 채비.items():
        for 열쇠 in 꼭있을것:
            if not 것.get(열쇠):
                빠진것.append('%s — %s 없음' % (갈, 열쇠))
    if 빠진것:
        막음.append('갈래 자료가 덜 찼습니다 %d곳' % len(빠진것))
        for x in 빠진것[:6]:
            print('  ✗ %s' % x)
    else:
        print('  · %d가지 모두 갖췄습니다' % len(채비))
    print('')

    # ── [2] 모든 부품이 그림을 갖는가 ★ 가장 중요 ────────
    print('[2] 모든 부품이 그림을 갖는가 ★')
    줄없음 = []           # 줄처럼 모양이 없어도 되는 것
    줄같은것 = ('원줄', '목줄', '쇼크리더', '기둥줄', '단차')
    빈것 = []
    본부품 = 0
    for 갈, 것 in 채비.items():
        for 한개 in (것.get('부품') or []):
            이름 = (한개.get('이름') or '').strip()
            if not 이름:
                막음.append('%s — 이름 없는 부품' % 갈)
                continue
            본부품 += 1
            그림 = art._부품모양(이름, 100, 100)
            if 그림:
                continue
            if any(x in 이름 for x in 줄같은것):
                줄없음.append('%s / %s' % (갈, 이름))
                continue
            빈것.append('%s / %s' % (갈, 이름))
    if 빈것:
        막음.append('그림이 없는 부품 %d개 — 쪽에 **빈 자리**가 남습니다'
                    % len(빈것))
        for x in 빈것:
            print('  ✗ %s' % x)
        print("      → engine/art.py 의 _부품모양() 에 모양을 더하세요.")
        print('      → 그리기 전에 **쇼핑몰에서 실제 제품을 찾습니다**')
        print('        (docs/채비자료-규칙.md 3번)')
    else:
        print('  · 부품 %d개가 모두 그림을 갖습니다' % 본부품)
    if 줄없음:
        print('  ~ 줄붙이 %d개는 모양 없이 선으로 그립니다 (괜찮습니다)'
              % len(줄없음))
    print('')

    # ── [5] 조건 차례가 안전한가 ─────────────────────────
    print('[3] 넓은 이름이 좁은 이름을 가로채지 않는가')
    차례 = 조건차례()
    뒤집힌것 = []
    for 좁은, 넓은 in 가로채면안되는짝:
        if not 먼저나오나(차례, 좁은, 넓은):
            뒤집힌것.append("'%s' 가 '%s' 보다 아래에 있습니다" % (좁은, 넓은))
    if 뒤집힌것:
        막음.append('그림 조건 차례가 뒤집혔습니다 %d곳' % len(뒤집힌것))
        for x in 뒤집힌것:
            print('  ✗ %s' % x)
        print('      → 파이썬은 위에서부터 보고 맞으면 끝냅니다.')
        print('        **좁은 이름을 위로** 올리세요.')
    else:
        print('  · 조건 %d개의 차례가 안전합니다' % len(차례))
    print('')

    # ── [3] 갈래마다 아이콘이 있는가 ─────────────────────
    print('[4] 갈래마다 아이콘이 있는가')
    없는아이콘 = [갈 for 갈 in 채비
                  if not os.path.isfile(
                      os.path.join(ROOT, 'assets', 'icon', '%s.svg' % 갈))]
    if 없는아이콘:
        알림.append('아이콘 없는 갈래 %d개 — 카드가 허전합니다'
                    % len(없는아이콘))
        for x in 없는아이콘:
            print('  ! %s — assets/icon/%s.svg 가 없습니다' % (x, x))
        print('      → engine/make_icons.py 에 더하고 --write 로 그립니다')
    else:
        print('  · %d가지 모두 아이콘이 있습니다' % len(채비))
    print('')

    # ── [4] 쪽이 만들어졌는가 ────────────────────────────
    print('[5] 쪽이 실제로 만들어졌는가')
    # ★ 주소는 **url.py 에서 받습니다** (계약-03)
    #   여기서 쪽 이름을 손으로 이어 붙이면 주소를 만드는 곳이
    #   둘이 됩니다. 언젠가 반드시 어긋납니다.
    #   (check_contracts.py 가 이것을 잡아 주었습니다 — 2026-09-30)
    def _쪽파일(길):
        return os.path.join(나온곳, 길.replace('/', os.sep))

    없는쪽 = []
    for 갈 in 채비:
        if not os.path.isfile(_쪽파일(url.rig(갈))):
            없는쪽.append(url.rig(갈))
    if not os.path.isfile(_쪽파일(url.rig_list())):
        없는쪽.append(url.rig_list())
    if 없는쪽:
        알림.append('아직 안 만든 쪽 %d개 — build 를 돌리세요'
                    % len(없는쪽))
        for x in 없는쪽:
            print('  ! %s' % x)
    else:
        print('  · 모음 1쪽 + 갈래 %d쪽이 모두 있습니다' % len(채비))
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ! %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1
    if 알림 and 엄격:
        return 2
    print('채비 %d가지가 모두 멀쩡합니다.' % len(채비))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
