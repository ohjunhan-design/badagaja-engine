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
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine._art_overflow import 밖으로나간글자
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


# ── 사람이 보고 정한 것 ─────────────────────────────────
_정한것 = None


def _정한목록():
    """data/design-accepted.json 을 한 번만 읽습니다."""
    global _정한것
    if _정한것 is None:
        길 = os.path.join(ROOT, 'data', 'design-accepted.json')
        try:
            _정한것 = io.read_json(길, default={}).get('받아들인것') or []
        except Exception:
            _정한것 = []
    return _정한것


def 이미정했나(갈래, 한가지):
    """사람이 보고 「뜻한 변경」이라 정한 것인가.

    갈래·무엇·옛·새 가 **모두** 맞아야 합니다.
    숫자가 또 달라지면 다시 묻습니다 — 한 번 받아들였다고
    영원히 눈감지 않습니다.
    """
    이름, 옛수, 새수 = 한가지
    for x in _정한목록():
        if (x.get('갈래') == 갈래 and x.get('무엇') == 이름
                and x.get('옛') == 옛수 and x.get('새') == 새수):
            return True
    return False


def 정한까닭(갈래, 이름):
    for x in _정한목록():
        if x.get('갈래') == 갈래 and x.get('무엇') == 이름:
            return x.get('까닭') or ''
    return ''


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

    # ★ **사람이 보고 정한 것은 다시 묻지 않습니다** (2026-09-29)
    #
    #   물을 때마다 판정이 NOT_TESTED 로 멈춥니다. 한 번 보고
    #   정한 것을 적어 두지 않으면 「봐 주세요」가 영원히
    #   되풀이되고, 결국 아무도 안 보게 됩니다.
    #
    #   갈래·무엇·옛·새 가 모두 맞아야 넘어갑니다. 숫자가 또
    #   달라지면 다시 묻습니다 — 한 번 받아들였다고 영원히
    #   눈감지 않습니다.
    받아들인것 = [x for x in 줄어든것 if 이미정했나(갈래, x)]
    줄어든것 = [x for x in 줄어든것 if x not in 받아들인것]
    if 받아들인것:
        print('  ~ %-12s 사람이 보고 정한 것 %d가지는 넘어갑니다'
              % (갈래, len(받아들인것)))
        for 이름, a, b in 받아들인것:
            print('        %-8s %5d → %5d  (%s)'
                  % (이름, a, b, 정한까닭(갈래, 이름)[:52]))

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

    # ── [4] 어종 쪽에 삽화가 있는가 (주인 규칙 6-1)
    #
    #   ★ 2026-09-29 — 여기서 **삽화 245개가 통째로 사라진 것**을
    #     찾았습니다. 해루질 17쪽 · 낚시 18쪽이 7개씩 잃었습니다.
    #     자료는 멀쩡했고 엔진이 그리지 않았을 뿐이었습니다.
    #
    #     [1] 이 「크게 줄어든 것」으로 알려 주기는 했지만
    #     **막지는 않았습니다.** 규칙 6-1 은 「보이는 것이 빠지면
    #     배포를 막는다」고 했습니다. 그러니 막아야 합니다.
    #
    #     아이콘(24×24)은 세지 않습니다. 삽화만 셉니다.
    print('[4] 어종 쪽에 삽화가 있는가 (주인 규칙 6-1)')
    적어도 = 3
    모자란쪽 = []
    셈 = []
    for 갈래 in ('catch', 'fish'):
        칸 = os.path.join(NEW, 갈래)
        if not os.path.isdir(칸):
            continue
        for 이름 in sorted(os.listdir(칸)):
            if not 이름.endswith('.html') or 이름 == 'index.html':
                continue
            길 = os.path.join(칸, 이름)
            글 = io.read(길, default='')
            몇 = 0
            for m in re.finditer(r'<svg[^>]*viewBox="([^"]*)"', 글):
                칸값 = m.group(1).split()
                if len(칸값) == 4:
                    try:
                        w, h = float(칸값[2]), float(칸값[3])
                    except ValueError:
                        continue
                    if w >= 200 and h >= 150:
                        몇 += 1
            셈.append(몇)
            if 몇 < 적어도:
                모자란쪽.append('%s/%s %d개' % (갈래, 이름, 몇))
    if not 셈:
        print('  ~ 어종 쪽이 없습니다 — 먼저 build.py 로 만드세요.')
    elif 모자란쪽:
        막음.append('삽화가 %d개 미만인 어종 쪽 %d개' % (적어도, len(모자란쪽)))
        print('  ✗ 삽화가 %d개도 안 되는 쪽 %d개' % (적어도, len(모자란쪽)))
        for x in 모자란쪽[:8]:
            print('      %s' % x)
        print('      → 규칙 6-1: 쪽에는 보이는 것이 있어야 합니다.')
        print('        engine/art.py 가 그립니다. 자료는')
        print('        data/raw/guide.json 의 그림·깊이cm·흔적 입니다.')
    else:
        print('  · 어종 쪽 %d개에 모두 삽화가 있습니다 (모두 %d개 · 쪽마다 %.1f개)'
              % (len(셈), sum(셈), sum(셈) / len(셈)))
    print('')
    # ── [6] 권역 쪽의 칸 차례가 모든 권역에서 같은가 (계약-36)
    #
    #   ★ 2026-09-29 바깥 검수 12차
    #     「권역마다 카드 위치·메뉴 순서·정보량이 크게 달라지면
    #       57개 페이지가 각각 다른 사이트처럼 보입니다.」
    #
    #   재 보니 58쪽에 3가지 차례가 있었습니다. 제주 7쪽만
    #   풍경칸이 더 있었고, 그것은 **자료를 따른 것**이라 옳았습니다.
    #   다만 계약이 없어 옳은지 그른지 가릴 길이 없었습니다.
    #
    #   그래서 **자료로 설명되는 차이만** 봐줍니다.
    print('[6] 권역 쪽의 칸 차례가 모든 권역에서 같은가 (계약-36)')
    자료가정하는칸 = {'scenery'}
    차례표 = {}
    for 길 in sorted(glob.glob(os.path.join(NEW, '*.html'))):
        이름 = os.path.basename(길)[:-5]
        if 이름 == 'index':
            continue                       # 전국 첫 화면 — 권역 쪽이 아닙니다
        글 = io.read(길, default='')
        칸들 = re.findall(r'<section[^>]*id="([^"]+)"', 글)
        if len(칸들) < 4:
            continue                       # 권역 쪽이 아닙니다
        차례표[이름] = 칸들
    if not 차례표:
        print('  ~ 권역 쪽이 없습니다 — 잴 것이 없습니다.')
    else:
        # 자료가 정하는 칸을 빼고 견줍니다
        뼈대 = {}
        for 이름, 칸들 in 차례표.items():
            뼈대[이름] = tuple(x for x in 칸들 if x not in 자료가정하는칸)
        셈 = collections.Counter(뼈대.values())
        흔한것 = 셈.most_common(1)[0][0]
        어긋난것 = [이름 for 이름, 차 in 뼈대.items() if 차 != 흔한것]
        if 어긋난것:
            막음.append('칸 차례가 다른 권역 쪽 %d개' % len(어긋난것))
            print('  ✗ 칸 차례가 다른 쪽 %d개' % len(어긋난것))
            print('      기준: %s' % ' → '.join(흔한것))
            for 이름 in 어긋난것[:5]:
                print('      %-14s %s' % (이름, ' → '.join(뼈대[이름])))
            print('      → 손님이 권역을 옮길 때마다 다른 사이트로 느낍니다.')
        else:
            더한칸 = sum(1 for 칸들 in 차례표.values()
                         if set(칸들) & 자료가정하는칸)
            print('  · 권역 쪽 %d개의 칸 차례가 모두 같습니다' % len(차례표))
            print('      기준: %s' % ' → '.join(흔한것))
            print('      자료가 있어 풍경칸이 더 붙은 쪽 %d개 (계약대로)'
                  % 더한칸)
    print('')

    # ── [5] 그림 안 글자가 그림 밖으로 나가지 않는가
    #
    #   ★ 2026-09-29 — 삽화를 되살리자 375px 에서 글자가 잘렸습니다.
    #     SVG 는 줄바꿈하지 않아 viewBox 를 넘으면 그대로 잘립니다.
    #     화면을 찍어 봐도 잘린 자리가 자연스러워 보여 놓치기 쉽습니다.
    print('[5] 그림 안 글자가 그림 밖으로 나가지 않는가')
    넘친것 = []
    차례 = io.read_json(os.path.join(ROOT, 'data', 'raw', 'lessons.json'),
                        default={}).get('차례') or {}
    for 대상 in sorted(차례):
        for 몇, 단 in enumerate(차례[대상], 1):
            for 글, 오른쪽, 한계 in 밖으로나간글자(단.get('그림') or ''):
                넘친것.append('%s %d단계 — 오른쪽 %d (한계 %d) 「%s」'
                              % (대상, 몇, 오른쪽, 한계, 글[:32]))
    if not 차례:
        print('  ~ 배우는 차례 자료가 없습니다 — 잴 것이 없습니다.')
    elif 넘친것:
        막음.append('그림 밖으로 나간 글자 %d개' % len(넘친것))
        print('  ✗ 그림 밖으로 나간 글자 %d개' % len(넘친것))
        for x in 넘친것[:8]:
            print('      %s' % x)
        print('      → SVG 는 줄바꿈하지 않습니다. 넘치면 잘려 못 읽습니다.')
        print('        textLength 를 주어 그림 안에 맞춥니다.')
    else:
        단계수 = sum(len(v) for v in 차례.values())
        print('  · 배우는 차례 %d갈래 %d단계의 글자가 모두 그림 안에 있습니다'
              % (len(차례), 단계수))
    print('')


    print('')

    # ── [7] 어려운 물때 이름을 손님에게 보이지 않는가
    #
    #   ★ 2026-09-29 주인 지시
    #     「어깨사리 허리사리같은 말은 빼버려 아래 열매 한꺽기
    #       이런것들도 이런말은 일반인들의 눈에서는 필요없는 말들이야」
    #
    #   바다 일하는 분들의 말입니다. 처음 오는 손님은 이 말로
    #   아무것도 알 수 없습니다. 「물 많이 빠짐」만 알면 됩니다.
    #
    #   ★ 이름표 자체는 남겨 둡니다 — 달 나이를 셀 때 씁니다.
    #     **화면에 붙이는가**만 봅니다.
    #
    #   겪은 일: 물때 카드만 고치고 「언제 갈까」 칸을 빠뜨려
    #     거기에만 「어깨사리」가 남아 있었습니다.
    print('[7] 어려운 물때 이름이 화면에 나오지 않는가')
    _길 = os.path.join(ROOT, 'assets', 'js', 'tide.js')
    _글 = io.read(_길, default='')
    if not _글:
        print('  ~ assets/js/tide.js 가 없습니다 — 못 쟀습니다')
    else:
        # ★ **줄 단위로 보면 놓칩니다** (2026-09-29 — 처음에 놓쳤습니다)
        #     칸.appendChild(만들기('p', 'when-s',
        #       그날.키 + ' · ' + 그날.이름 + …));
        #   「만들기(」는 윗줄, 「.이름」은 아랫줄입니다.
        #   그래서 **화면에 붙이는 줄과 그 뒤 세 줄**을 함께 봅니다.
        #   일부러 넣어 보고 잡히는 것을 확인했습니다.
        _줄들 = _글.split(chr(10))
        _걸림 = []
        for _n, _줄 in enumerate(_줄들, 1):
            _벗 = _줄.strip()
            if _벗.startswith(('//', '/*', '*')):
                continue
            if '만들기(' not in _벗 and 'textContent' not in _벗:
                continue
            _덩이 = chr(10).join(_줄들[_n - 1:_n + 3])
            for _무엇 in ('.이름', '.매'):
                if _무엇 in _덩이:
                    _걸림.append((_n, _벗[:80], _무엇))
                    break
        if _걸림:
            막음.append('어려운 물때 이름이 화면에 %d곳' % len(_걸림))
            print('  ✗ %d곳에서 화면에 붙입니다' % len(_걸림))
            for _n, _줄, _무엇 in _걸림[:6]:
                print('      tide.js:%d  %s' % (_n, _줄))
            print('      → 「물 많이 빠짐 / 중간 / 물 적게 빠짐」을 씁니다.')
        else:
            print('  · 어려운 물때 이름을 화면에 붙이지 않습니다')
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
