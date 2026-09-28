# -*- coding: utf-8 -*-
"""주소가 **우리 것인가 바깥 것인가** — 한 곳에서만 가릅니다.

★ 왜 만들었나 (2026-09-27 바깥 검수 5차 지시)

    5번 항목이 FAIL 로 나왔습니다. 까닭은 이랬습니다.

        ✗ 사이트 안 파일을 못 받았습니다
            index.html — LINK https://hangeul.pstatic.net/...

    주인이 「네이버 검색창 글씨체로 바꿔 달라」 하셔서 로고 글꼴을
    네이버 공식 자리에서 받아 오게 했습니다. 그런데 검사기는
    인터넷을 막고 재므로 그것을 **못 받습니다.** 당연합니다.
    그것을 「우리 파일이 깨졌다」로 세어 빨간불을 냈습니다.

    **쪽이 잘못된 것이 아니라 검사기가 잘못 센 것입니다.**

    바깥 검수가 이렇게 지적했습니다.

        외부 URL이라고 무조건 PASS시키면 안 됩니다.
        INTERNAL / EXTERNAL_ALLOWED / EXTERNAL_UNKNOWN / BROKEN
        으로 나누십시오.

★ 왜 한 파일에 두나
    전에는 `check_console.py` 만 목록을 들고 있었습니다.
    `check_assets.py`·`check_links.py` 는 저마다 따로 갈랐습니다.
    한 곳을 고치고 다른 곳을 잊으면 **검사기마다 답이 달라집니다.**
    (주인 규칙 29 「숫자는 한곳에서」 와 같은 뜻입니다)

★ 네 갈래
    우리것        badagaja.com · 상대 주소 · file:// — **못 받으면 진짜 탈**
    바깥허락       글꼴·지도·광고 — 못 받아도 탈이 아닙니다
    바깥모름       처음 보는 남의 자리 — **알리되 막지는 않습니다**
                  (모르는 것을 지킴으로도, 어김으로도 세지 않습니다)
    빈것          주소가 없습니다

★ 「바깥허락」이라고 그냥 통과는 아닙니다
    바깥 검수 지적대로, 인터넷을 열고 재는 검사
    (`check_deployed --net`) 에서는 **실제로 200 이 오는지** 봅니다.
    여기서 하는 일은 「인터넷 막고 재는 검사에서 빨간불을 내지 말라」
    까지입니다.
"""

# ── 우리 자리 ────────────────────────────────────────────────
우리도메인 = (
    'badagaja.com',
    'www.badagaja.com',
)

# 우리가 가진 다른 자리 — 우리 것이지만 **이 사이트 밖**입니다.
# 인터넷 막고 재는 검사에서는 못 받아도 탈이 아니고,
# 인터넷 열고 재는 검사에서는 **살아 있는지 꼭 봐야** 합니다.
우리의바깥자리 = (
    'badagaja.cloud',
)

# ── 바깥이지만 허락한 것 ──────────────────────────────────────
#
#   ★ 여기에 더할 때는 **왜 더하는지 한 줄 적습니다.**
#     적지 않으면 나중에 아무도 지울 수 없습니다.
#
바깥허락 = {
    # 글꼴 — 못 받으면 글씨체만 바탕 것으로 바뀝니다. 쪽은 멀쩡합니다
    'hangeul.pstatic.net':   '나눔스퀘어 네오 (네이버 공식) — 상단 로고',
    'fonts.googleapis.com':  '노토 산스·세리프 KR — 본문',
    'fonts.gstatic.com':     '위 글꼴의 실제 파일',
    # 광고 — 없어도 쪽은 멀쩡합니다
    'coupang.com':           '쿠팡 파트너스 배너',
    'ads-partners.coupang.com': '쿠팡 파트너스 배너',
    'googletagmanager.com':  '구글 태그',
    'google-analytics.com':  '방문 셈',
    'googlesyndication.com': '애드센스',
    'doubleclick.net':       '애드센스가 부르는 자리',
    # 지도
    'dapi.kakao.com':        '카카오 지도',
    'map.kakao.com':         '카카오 지도',
    't1.daumcdn.net':        '카카오 지도 그림',
    'daumcdn.net':           '카카오 지도 그림',
}

우리것 = '우리것'
바깥허락함 = '바깥허락'
바깥모름 = '바깥모름'
빈것 = '빈것'


def 갈래(주소):
    """주소 한 개가 어느 갈래인지. **짐작하지 않습니다.**

    >>> 갈래('css/site.css')
    '우리것'
    >>> 갈래('https://hangeul.pstatic.net/x.css')
    '바깥허락'
    >>> 갈래('https://badagaja.com/index.html')
    '우리것'
    >>> 갈래('https://example.com/x.js')
    '바깥모름'
    """
    글 = (주소 or '').strip()
    if not 글:
        return 빈것

    낮 = 글.lower()

    # data: · blob: · about: 는 받아 올 것이 없습니다
    for 머리 in ('data:', 'blob:', 'about:', 'javascript:', '#'):
        if 낮.startswith(머리):
            return 빈것

    # 상대 주소 · file:// 는 우리 자리입니다
    if not (낮.startswith('http://') or 낮.startswith('https://')
            or 낮.startswith('//')):
        return 우리것

    # //cdn.x.com/... 꼴도 바깥입니다
    남은 = 낮.split('//', 1)[1] if '//' in 낮 else 낮
    자리 = 남은.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    자리 = 자리.split('@')[-1].split(':')[0]      # 사용자@·포트 떼기

    if 자리 in 우리도메인:
        return 우리것
    if 자리 in 우리의바깥자리:
        return 바깥허락함

    # 정확히 같거나, 그 아래 자리(sub.도메인)이면 허락한 것입니다.
    # ★ `endswith` 만 쓰면 `evil-coupang.com` 도 통과합니다 — 점을 붙입니다
    for 허락 in 바깥허락:
        if 자리 == 허락 or 자리.endswith('.' + 허락):
            return 바깥허락함

    return 바깥모름


def 왜허락했나(주소):
    """허락한 까닭 한 줄. 없으면 빈 글."""
    남은 = (주소 or '').lower()
    for 허락, 까닭 in 바깥허락.items():
        if 허락 in 남은:
            return 까닭
    for x in 우리의바깥자리:
        if x in 남은:
            return '우리가 가진 다른 자리'
    return ''


def 우리것인가(주소):
    """못 받으면 **진짜 탈**인가.

    ★ 빈 주소는 우리 것이 아닙니다. 「모르는 것」입니다.
      빈 것을 우리 것으로 세면 애먼 FAIL 이 납니다.
    """
    return 갈래(주소) == 우리것


def 말에서주소(말):
    """탈 메시지 안에 섞인 주소를 갈래 나눕니다.

    콘솔 탈은 주소만 오는 게 아니라
    `Failed to load resource: https://... ` 처럼 섞여 옵니다.
    그래서 **문자열 안에 허락한 자리가 들어 있는지**로 봅니다.

    ★ 여기서는 「우리것」을 함부로 내지 않습니다.
      섞인 글에서는 상대 주소인지 아닌지 알 수 없습니다.
      허락한 자리가 보이면 바깥, 아니면 **모름**입니다.
    """
    낮 = (말 or '').lower()
    if not 낮.strip():
        return 빈것
    for 허락 in 바깥허락:
        if 허락 in 낮:
            return 바깥허락함
    for x in 우리의바깥자리:
        if x in 낮:
            return 바깥허락함
    for x in 우리도메인:
        if x in 낮:
            return 우리것
    if 'http://' in 낮 or 'https://' in 낮:
        return 바깥모름
    return 우리것          # 주소가 안 보이면 우리 코드에서 난 탈입니다


if __name__ == '__main__':
    import sys
    표 = [
        ('css/site.css',                              우리것),
        ('/img/a.webp',                               우리것),
        ('https://badagaja.com/tide/',                우리것),
        ('https://www.badagaja.com/',                 우리것),
        ('https://hangeul.pstatic.net/x/nanum.css',   바깥허락함),
        ('https://fonts.googleapis.com/css2?x=1',     바깥허락함),
        ('https://fonts.gstatic.com/s/a.woff2',       바깥허락함),
        ('https://badagaja.cloud/',                   바깥허락함),
        ('//t1.daumcdn.net/map.js',                   바깥허락함),
        ('https://evil-coupang.com/x.js',             바깥모름),
        ('https://example.com/x.js',                  바깥모름),
        ('data:image/png;base64,AAA',                 빈것),
        ('',                                          빈것),
    ]
    틀린것 = 0
    for 주소, 바람 in 표:
        난것 = 갈래(주소)
        맞나 = 난것 == 바람
        if not 맞나:
            틀린것 += 1
        print('  %s %-46s %s%s'
              % ('·' if 맞나 else '✗', 주소[:46], 난것,
                 '' if 맞나 else '   ← %s 여야 합니다' % 바람))
    print('')
    if 틀린것:
        print('✗ %d개가 틀립니다' % 틀린것)
        sys.exit(1)
    print('· %d개 모두 맞습니다' % len(표))
