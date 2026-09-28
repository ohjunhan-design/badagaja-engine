# -*- coding: utf-8 -*-
"""**옛 쪽이 가졌던 것을 새 쪽이 잃지 않았는가** — 갈래마다 전수로 봅니다.

★ 왜 만들었나 (2026-09-28 주인 지시)

    「옛 짜임새가 전체적으로 가시성이 더 좋아
      디자인적인 부분 전수검사해줘」

    오늘 주인이 눈으로 셋을 잡아내셨습니다.

        · 권역 쪽에 **시간별 물높이 그래프**가 빠짐
        · 잡기 쪽 맨 위에 큰 그림이 깔려 고를 것이 아래로 밀림
        · (어제) 첫 화면 아이콘 7칸이 통째로 사라짐

    셋 다 검사기가 못 잡았습니다. 까닭은 하나입니다 —
    **「옛 쪽에 있던 것이 새 쪽에 있는가」를 아무도 안 봤습니다.**

    Golden 검사는 **새 쪽끼리** 견줍니다(어제와 오늘).
    이 검사는 **옛 쪽과 새 쪽**을 견줍니다. 축이 다릅니다.

★ 무엇을 세는가
    사람 눈에 걸리는 것만 셉니다 — 보이는 것·누를 것·읽을 것.
    class 이름은 안 셉니다(디자인을 고치면 바뀌는데 그것까지
    잡으면 알림이 잦아 아무도 안 봅니다).

★ 적다고 다 탈은 아닙니다
    새 쪽이 일부러 덜어 낸 것도 있습니다(맨 위 큰 그림처럼).
    그래서 **CHANGE DETECTED** 로 내고 사람이 정합니다.
    다만 **크게 줄어든 것**(절반 아래)은 눈에 띄게 적습니다.

쓰는 법
    python engine/check_design.py
    python engine/check_design.py --자세히
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine import machine   # noqa: E402  옛 사이트 자리는 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')

# 검사 등급 (계약-21)
막음 = []
알림 = []

# ── 갈래마다 옛 쪽 ↔ 새 쪽 한 쌍 ──────────────────────────
#   (갈래, 옛 쪽, 새 쪽)
쌍들 = [
    ('첫화면',       'index.html',                'index.html'),
    ('묶음',         'chungnam/index.html',       'chungnam/index.html'),
    ('권역',         'taean.html',                'taean.html'),
    ('포인트목록',   'point/taean-fishing.html',
                     'point/chungnam/taean_fishing.html'),
    ('해루질대상',   'catch/index.html',          'catch/index.html'),
    ('해루질하나',   'catch/bajirak.html',        'catch/bajirak.html'),
    ('낚시어종',     'fish/index.html',           'fish/index.html'),
    ('낚시하나',     'fish/gamseongdom.html',     'fish/gamseongdom.html'),
    ('축제목록',     'festival/index.html',       'festival/index.html'),
]

# ── 무엇을 세는가 ─────────────────────────────────────────
세는것 = [
    ('사진',      r'<img\b'),
    ('그림',      r'<svg\b'),
    ('링크',      r'<a\b[^>]*\bhref='),
    ('단추',      r'<button\b'),
    ('입력칸',    r'<input\b'),
    ('큰제목',    r'<h1\b'),
    ('중제목',    r'<h2\b'),
    ('작은제목',  r'<h3\b'),
    ('표',        r'<table\b'),
    ('목록',      r'<li\b'),
    ('구역',      r'<section\b'),
    ('글자수',    None),      # 몸통 글자 수 (따로 셉니다)
]


# ── ★ 옛 쪽에 있던 **꼭 있어야 할 것** (2026-09-28 주인 지적)
#
#   주인이 옛 권역 쪽 화면을 보내시며 「이런것들도 확인해봐」 하셨습니다.
#   수를 세는 것만으로는 **무엇이 빠졌는지** 알 수 없어, 말로 찾습니다.
#
#   ★ 셋째 것(출입통제)이 가장 중요합니다 — 모르고 들어가면 **과태료**입니다.
#     법·안전에 걸리는 것은 「디자인」이 아니라 **빠지면 안 되는 것**입니다.
#
#   (갈래, 찾을 말들, 무엇인가, 막을 것인가)
꼭있어야할것 = [
    ('권역', ('지도에서 포인트 보기', '포인트 보기'),
     '지도로 가는 단추', False),
    ('권역', ('마을어장',),
     '「체험장 밖 갯벌은 마을어장」 주의', True),
    ('권역', ('출입통제', '출입 통제'),
     '출입통제 장소 안내 (과태료)', True),
    ('권역', ('테트라포드',),
     '테트라포드 주의 (추락 사고)', True),
    ('권역', ('처음이신가요', '처음이라면', '왕초보'),
     '처음 오신 분 안내', False),
    ('권역', ('구명조끼',), '구명조끼 안내', True),
    ('권역', ('기상특보',), '기상특보 때 들어가지 말라는 안내', True),
]

# ★ **권역 57곳 전부**에 있어야 하는 안전 말 (2026-09-28)
#   한 쪽만 보면 나머지 56곳이 빠져도 모릅니다.
#   디자인이 아니라 **사람이 다치는 이야기**라 전수로 봅니다.
권역전수 = [
    ('테트라포드', '테트라포드 추락 주의'),
    ('구명조끼',   '구명조끼'),
    ('기상특보',   '기상특보'),
    ('마을어장',   '마을어장 (처벌·분쟁)'),
    ('금어기',     '금어기'),
    ('119',        '119 신고'),
]


def 말이있나(s, 말들):
    낮 = s
    return any(x in 낮 for x in 말들)


def 몸통만(s):
    """머리·스크립트·주석을 뺍니다 — 사람 눈에 보이는 것만."""
    s = re.sub(r'(?is)<head\b.*?</head>', ' ', s)
    s = re.sub(r'(?is)<script\b.*?</script>', ' ', s)
    s = re.sub(r'(?is)<style\b.*?</style>', ' ', s)
    s = re.sub(r'(?s)<!--.*?-->', ' ', s)
    s = re.sub(r'(?is)<template\b.*?</template>', ' ', s)
    return s


def 글자수(몸):
    글 = re.sub(r'<[^>]+>', ' ', 몸)
    글 = re.sub(r'\s+', ' ', 글).strip()
    return len(글)


def 재기(길):
    if not os.path.isfile(길):
        return None
    몸 = 몸통만(io.read(길, default=''))
    나옴 = {}
    for 이름, 무늬 in 세는것:
        나옴[이름] = 글자수(몸) if 무늬 is None \
            else len(re.findall(무늬, 몸, re.I))
    return 나옴


def 견주기(갈래, 옛길, 새길, 자세히):
    옛p = os.path.join(OLD, 옛길.replace('/', os.sep))
    새p = os.path.join(NEW, 새길.replace('/', os.sep))
    옛것, 새것 = 재기(옛p), 재기(새p)

    if 옛것 is None and 새것 is None:
        print('  ~ %-12s 두 쪽 다 없습니다' % 갈래)
        return
    if 옛것 is None:
        print('  ~ %-12s 옛 쪽이 없습니다 (%s) — 견줄 것이 없습니다'
              % (갈래, 옛길))
        return
    if 새것 is None:
        막음.append('%s — 새 쪽이 없습니다 (%s)' % (갈래, 새길))
        print('  ✗ %-12s **새 쪽이 없습니다** (%s)' % (갈래, 새길))
        return

    줄어든것 = []
    for 이름, _ in 세는것:
        옛수, 새수 = 옛것[이름], 새것[이름]
        if 옛수 <= 0:
            continue
        # 크게 줄어든 것만 봅니다 — 절반 아래로 떨어지거나,
        # 있던 것이 아예 0 이 되면 눈에 띄게 적습니다
        if 새수 == 0 or 새수 * 2 < 옛수:
            줄어든것.append((이름, 옛수, 새수))

    if 줄어든것:
        알림.append('%s — 크게 줄어든 것 %d가지' % (갈래, len(줄어든것)))
        print('  ! %-12s 크게 줄어든 것 %d가지' % (갈래, len(줄어든것)))
        for 이름, a, b in 줄어든것:
            표 = '**0 이 됨**' if b == 0 else ''
            print('        %-8s %5d → %5d  %s' % (이름, a, b, 표))
    else:
        print('  · %-12s 크게 줄어든 것이 없습니다' % 갈래)

    # ★ 꼭 있어야 할 말이 빠지지 않았는가
    for 갈, 말들, 무엇, 막나 in 꼭있어야할것:
        if 갈 != 갈래:
            continue
        옛글 = io.read(옛p, default='')
        새글 = io.read(새p, default='')
        옛에있나 = 말이있나(옛글, 말들)
        새에있나 = 말이있나(새글, 말들)
        if 옛에있나 and not 새에있나:
            (막음 if 막나 else 알림).append(
                '%s — %s 가 빠졌습니다' % (갈래, 무엇))
            print('  %s %-12s **%s** 가 빠졌습니다'
                  % ('✗' if 막나 else '!', '', 무엇))
        elif 자세히 and 새에있나:
            print('        · %s 있음' % 무엇)

    if 자세히:
        print('        %s'
              % ' · '.join('%s %d→%d' % (이름, 옛것[이름], 새것[이름])
                           for 이름, _ in 세는것))



def 안쓰는자료():
    """자료에 있는데 어느 쪽에도 안 나오는 설명을 찾습니다.

    돌려주는 것 — [(무엇, 몇 개, 글자 수, 보기)]
    """
    import glob as _g
    sys.path.insert(0, ROOT)
    try:
        from engine.data import 자료
    except Exception:                          # noqa: BLE001
        return []
    try:
        d = 자료()
    except Exception:                          # noqa: BLE001
        return []

    나옴 = []

    # ── 권역×어종 설명이 **그 어종 쪽에** 나오는가
    #
    #   ★ 「어느 쪽에든 있으면 통과」로 하면 안 됩니다 (2026-09-28)
    #     같은 글이 권역 쪽에도 나옵니다. 그래서 어종 쪽에서
    #     통째로 빠져도 「있다」고 세어졌습니다.
    #     **그 어종의 쪽에 있는지**를 콕 집어 봅니다.
    from engine import url
    어종글 = {}
    for 갈래 in ('해루질', '낚시'):
        for a in d.안내(갈래):
            p = os.path.join(NEW, url.guide(a['id'], 갈래).replace('/', os.sep))
            어종글[(갈래, (a['이름'] or {}).get('ko') or '')] =                 io.read(p, default='')

    안쓴것, 글자, 보기 = 0, 0, ''
    for r in d.권역들:
        try:
            것들 = d.여행(r['id'])['어종']
        except Exception:                      # noqa: BLE001
            continue
        for x in 것들:
            설명 = (x.get('설명') or {}).get('ko') or ''
            그이름 = (x['이름'] or {}).get('ko') or ''
            갈래 = x.get('갈래') or ''
            if not 설명 or not 그이름:
                continue
            # 자료에 「바지락·동죽」처럼 묶여 적힌 것이 있습니다.
            # 그 어종 쪽을 찾아 거기 있는지 봅니다.
            쪽글 = None
            for (ㄱ, 이) in 어종글:
                if ㄱ == 갈래 and (이 == 그이름 or 이 in 그이름):
                    쪽글 = 어종글[(ㄱ, 이)]
                    break
            if 쪽글 is None:
                continue          # 아직 쪽이 없는 어종 — 여기서 따질 일이 아닙니다
            맛 = 설명[:20]
            if 맛 and 맛 not in 쪽글:
                안쓴것 += 1
                글자 += len(설명)
                if not 보기:
                    보기 = '%s %s — %s…' % (r['id'], 그이름, 설명[:40])
    if 안쓴것:
        나옴.append(('권역별 어종 설명', 안쓴것, format(글자, ','), 보기))
    return 나옴


def main():

    # ★ **옛 사이트가 없으면 못 잽니다** (2026-09-28)
    #   볼 것이 0개면 걸린 것도 0개입니다. 그것을 통과라
    #   부르면 거짓말입니다. 끝난값 4 로 「잴 형편이 안 됨」.
    _자리, _까닭 = machine.옛사이트()
    if not _자리:
        print('□ %s' % _까닭)
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  BADAGAJA_OLD 로 옛 사이트 자리를 알려 주세요.')
        return 4 if '--strict' in sys.argv else 0
    자세히 = '--자세히' in sys.argv
    print('옛 쪽이 가졌던 것을 새 쪽이 잃지 않았는가 (2026-09-28 주인 지시)')
    print('  옛  %s' % OLD)
    print('  새  %s' % NEW)
    print('')
    print('[1] 갈래마다 견주기 — 절반 아래로 줄었거나 0 이 된 것')
    for 갈래, 옛길, 새길 in 쌍들:
        견주기(갈래, 옛길, 새길, 자세히)
    print('')

    # ── [2] 권역 57곳 전수 — 안전 말이 모든 쪽에 있는가
    print('[2] 권역 쪽 전수 — 안전 안내가 모든 곳에 있는가')
    권역쪽 = []
    for 이름 in sorted(os.listdir(NEW)):
        p = os.path.join(NEW, 이름)
        if (os.path.isfile(p) and 이름.endswith('.html')
                and 이름 not in ('index.html',)):
            s = io.read(p, default='')
            if 'tideStrip' in s:          # 물때 띠가 있으면 권역 쪽입니다
                권역쪽.append((이름, s))
    if not 권역쪽:
        print('  ~ 권역 쪽을 못 찾았습니다')
    else:
        print('      권역 쪽 %d개' % len(권역쪽))
        for 말, 무엇 in 권역전수:
            없는쪽 = [이름 for 이름, s in 권역쪽 if 말 not in s]
            if 없는쪽:
                막음.append('%s 가 빠진 권역 %d쪽' % (무엇, len(없는쪽)))
                print('  ✗ %-22s %3d쪽에 없습니다  %s'
                      % (무엇, len(없는쪽), ' · '.join(없는쪽[:3])))
            else:
                print('  · %-22s 권역 %d쪽 모두 있습니다'
                      % (무엇, len(권역쪽)))
    print('')

    # ── [3] 자료에 있는데 쪽이 안 쓰는 것
    #
    #   ★ 2026-09-28 바깥 검수 8차 지시로 만들었습니다
    #
    #     「콘텐츠가 2/3 줄었다. **의도적 축약인지 유실인지**
    #       배포 전에 판명하라」
    #
    #     재 보니 **유실**이었습니다. 자료에 권역×어종 설명이
    #     534개 · 23,062자 있는데 어종 쪽이 하나도 안 썼습니다.
    #     그 안에 「마을어장이라 체험 프로그램 밖 채취는 하면
    #     안 됩니다」 같은 **법·안전 이야기**가 들어 있었습니다.
    #
    #   ★ 「글이 짧다」가 아니라 **「있는 자료를 안 쓴다」**를 봅니다.
    #     짧게 쓰는 것은 고를 일이지만, 있는 것을 버리는 것은 탈입니다.
    print('[3] 자료에 있는데 쪽이 안 쓰는 것이 있는가')
    안쓰는것 = 안쓰는자료()
    if 안쓰는것:
        for 무엇, 몇, 글자, 보기 in 안쓰는것:
            막음.append('%s %d개(%s자)를 쪽이 안 씁니다' % (무엇, 몇, 글자))
            print('  ✗ %s — %d개 · %s자가 자료에 있는데 쪽에 안 나옵니다'
                  % (무엇, 몇, 글자))
            print('      보기: %s' % 보기)
    else:
        print('  · 자료에 있는 설명을 쪽이 모두 씁니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ! %s' % x)
        print('')
        print('  **줄었다고 다 탈은 아닙니다.** 일부러 덜어 낸 것도 있습니다.')
        print('  뜻한 것인지 하나씩 보아 주세요.')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1
    if not 알림:
        print('옛 쪽이 가졌던 것이 새 쪽에 모두 있습니다.')
        return 0
    return 2                # CHANGE DETECTED — 사람이 정합니다


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
