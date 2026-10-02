# -*- coding: utf-8 -*-
"""**단추가 약속한 것이 간 쪽에 정말 있는가** (계약-33 곁가지)

★ 왜 만들었나 (2026-10-02 주인 꾸중 — 「왜 자꾸 빠트려 똑바로해」)

    권역 쪽 57곳에 「**14일 물때표 보기**」 단추가 있고 `/tide/`
    로 갑니다. 그런데 `/tide/` 에는 지도와 57권역 목록만 있고
    **14일 달력이 없었습니다.**

    제가 `/tide/` 를 지도 쪽으로 다시 지으면서 빠뜨린 것입니다.
    코드 주석에는 「10일 전체는 /tide/ 에서 그대로 봅니다」라고
    적어 두고 실제로는 안 옮겼습니다.

    ★ **링크 검사는 멀쩡히 통과했습니다.**
      쪽이 있고 404 도 아니니까요. 「약속한 것이 거기 있는가」를
      재는 검사가 **없었습니다.**

    같은 날 첫 쪽에서도 하나 더 나왔습니다 —
    「어종별 채비법, 입질이 오는 자리, **기타 준비물 안내**」가
    `fish/` 로 가는데 그 쪽에 준비물이 없었습니다.

★ 이 검사가 보는 것

    링크 글(또는 `data-*-url` 이 뜻하는 단추 이름)에 **약속하는
    말**이 들어 있으면, 간 쪽에 그 표식이 **정말 있는지** 봅니다.

    짐작하지 않습니다 — 아래 표에 적힌 말과 표식만 봅니다.
    말을 늘릴 때는 **그 말이 가리키는 표식도 함께** 적습니다.

쓰는 법
    python engine/check_promise.py
    python engine/check_promise.py --strict    어기면 끝난값 1
    python engine/check_promise.py --list      어느 쪽인지 다 보기
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# ── 약속하는 말 → 간 쪽에 있어야 할 표식 (정규식)
#
#   ★ **글자 그대로** 봅니다. 「14일 물때표」라 적었으면 간 쪽에
#     14일치 달력이 있어야 합니다.
#   ★ 말을 더할 때는 표식도 같이 적습니다. 표식 없이 말만 더하면
#     이 검사가 무엇을 봐야 할지 모릅니다.
약속표 = [
    ('14일 물때표', [r'data-days="14"', r'tide-days']),
    ('10일 물때', [r'data-days="1[04]"', r'tide-days']),
    ('물때 보는 법', [r'사리', r'조금']),
    ('금어기', [r'금어기']),
    ('준비물', [r'준비물']),
    ('채비', [r'채비']),
    ('축제', [r'축제']),
]

# `data-*-url` 이 뜻하는 단추 이름 — 자바스크립트가 만드는 단추는
# HTML 에 글자가 없어 이 표가 없으면 못 봅니다.
자리이름 = {
    'tide': '14일 물때표',
    'muldae': '물때 보는 법',
    'rule': '금어기',
    'gear': '준비물',
}


def 쪽들():
    for 뿌리, _, 들 in os.walk(NEW):
        for n in sorted(들):
            if n.endswith('.html') and not n.startswith('__'):
                yield os.path.join(뿌리, n)


def 읽기(p):
    try:
        with io.open(p, encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


def _주석빼기(글):
    """자바스크립트에서 주석을 걷어냅니다.

    ★ **주석에 남은 말에 속지 않으려고** 만들었습니다 (2026-10-02).
      실제 호출을 지웠는데 주석에 같은 말이 있어 검사가 통과했습니다.
      「문구만 있고 기능은 없는」 것을 잡으려는 검사기가 바로 그
      덫에 걸려 있었습니다. 뮤테이션이 잡아 주었습니다.
    """
    if not 글:
        return 글
    글 = re.sub(r'/\*[\s\S]*?\*/', ' ', 글)        # 여러 줄 주석
    글 = re.sub(r'(?m)^[ \t]*//[^\r\n]*', ' ', 글)   # 줄 전체가 주석
    글 = re.sub(r'(?m)[ \t]//[^\r\n]*', ' ', 글)     # 줄 끝 주석
    return 글


def 약속찾기(글자):
    for 말, 표식들 in 약속표:
        if 말 in 글자:
            return 말, 표식들
    return None, None


def 간쪽길(뿌리, 주소):
    깨끗 = 주소.split('#')[0].split('?')[0]
    if not 깨끗:
        return None
    길 = os.path.normpath(os.path.join(뿌리, 깨끗.replace('/', os.sep)))
    if os.path.isdir(길) or not 길.endswith('.html'):
        길 = os.path.join(길, 'index.html')
    return os.path.normpath(길)


# 검사 등급 (계약-21)
#   막음 — 약속한 것이 간 쪽에 없습니다. 고쳐야 합니다
#   알림 — 재 볼 수 없었던 것. 막지 않습니다
막음, 알림 = [], []


def main():
    모두 = {}
    못읽은것 = []
    for p in 쪽들():
        글 = 읽기(p)
        if not 글:
            못읽은것.append(os.path.relpath(p, NEW))
            continue
        모두[os.path.normpath(p)] = 글
    if 못읽은것:
        알림.append('못 읽은 쪽 %d개' % len(못읽은것))

    print('')
    print('[1] 단추가 약속한 것이 간 쪽에 정말 있는가')
    print('      쪽 %d개' % len(모두))

    어긴것, 본것 = [], 0
    for p, s in 모두.items():
        뿌리 = os.path.dirname(p)

        덩이 = []
        for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                             s, re.S):
            글자 = re.sub(r'\s+', ' ',
                          re.sub(r'<[^>]+>', ' ', m.group(2))).strip()
            덩이.append((m.group(1), 글자))
        # 자바스크립트가 만드는 단추 — 자리 이름으로 봅니다
        for m in re.finditer(r'data-(%s)-url="([^"]+)"'
                             % '|'.join(자리이름), s):
            덩이.append((m.group(2), 자리이름[m.group(1)]))

        for 주소, 글자 in 덩이:
            if not 글자 or 주소.startswith(('http', '#', 'mailto:',
                                            'tel:', 'javascript:')):
                continue
            말, 표식들 = 약속찾기(글자)
            if not 말:
                continue
            길 = 간쪽길(뿌리, 주소)
            if not 길:
                continue
            간 = 모두.get(길)
            if 간 is None:
                continue        # 없는 쪽은 링크 검사가 잡습니다
            본것 += 1
            if not any(re.search(t, 간) for t in 표식들):
                어긴것.append((os.path.relpath(p, NEW), 글자[:40], 주소, 말))

    print('      약속이 든 링크 %d갈래를 쟀습니다' % 본것)
    print('')

    # ── [2] 약속한 **기능이 정말 돌아가는가**
    #
    #   ★ 바깥 검수 요구 (2026-10-02)
    #     「문자열만 찾는 식이면 안 됩니다. **버튼 존재 → 상세
    #       컨테이너 존재 → 14일 데이터 렌더 경로 존재** 세 조건을
    #       확인하세요. 「문구만 넣고 기능은 없는」 상태가 다시
    #       통과하면 안 됩니다」
    #
    #   표식 하나만 보면 **껍데기**가 통과합니다. 그것이 이 검사기를
    #   만든 까닭인데, 검사기 자신이 같은 덫에 빠져 있었습니다.
    print('[2] 약속한 기능이 정말 돌아가는가')
    기능 = [
        ('/tide/ 2주 물때', 'tide/index.html', [
            ('누를 단추', r'data-open-tide'),
            ('펼칠 칸', r'id="tide-detail"'),
            ('14일 그릴 자리', r'id="tideStrip"[^>]*data-days="14"'),
            ('그릴 코드', r'tide\.js'),
            ('권역을 갈아 끼울 코드', r'tide-map\.js'),
        ]),
    ]
    모자란것 = []
    for 이름, 쪽, 볼것 in 기능:
        길2 = os.path.normpath(os.path.join(NEW, 쪽.replace('/', os.sep)))
        글 = 모두.get(길2)
        if 글 is None:
            알림.append('%s — 쪽을 못 찾았습니다 (%s)' % (이름, 쪽))
            print('  ~ %s — 쪽이 없습니다' % 이름)
            continue
        빠진것 = [무엇 for 무엇, 표식 in 볼것
                  if not re.search(표식, 글)]
        if 빠진것:
            모자란것.append('%s — %s 가 없습니다' % (이름, ' · '.join(빠진것)))
        else:
            print('  · %s — %d가지가 모두 있습니다' % (이름, len(볼것)))

    # 자바스크립트가 **정말 그 입구를 부르는지**도 봅니다.
    #   쪽에 칸만 있고 코드가 안 부르면 빈 칸이 남습니다.
    입구길 = os.path.join(ROOT, 'assets', 'js', 'tide.js')
    지도길 = os.path.join(ROOT, 'assets', 'js', 'tide-map.js')
    # ★ **주석을 걷어내고 봅니다** (2026-10-02 뮤테이션이 잡았습니다)
    #   처음에는 글자만 찾았습니다. 그랬더니 실제 호출을 지워도
    #   **주석에 남은 같은 말** 때문에 통과했습니다 — 바깥 검수가
    #   말한 「문구만 넣고 기능은 없는」 꼴을 검사기가 그대로
    #   되풀이한 셈입니다.
    입구글 = _주석빼기(읽기(입구길))
    지도글 = _주석빼기(읽기(지도길))
    if 입구글 and not re.search(r'갈아끼우기\s*:', 입구글):
        모자란것.append('tide.js 에 권역을 갈아 끼우는 입구가 없습니다')
    if 지도글 and not re.search(r'\.갈아끼우기\s*\(', 지도글):
        모자란것.append('tide-map.js 가 그 입구를 부르지 않습니다')
    if 지도글 and 'region=' not in 지도글:
        모자란것.append('tide-map.js 가 ?region= 을 안 읽습니다')
    if (입구글 and 지도글
            and re.search(r'갈아끼우기\s*:', 입구글)
            and re.search(r'\.갈아끼우기\s*\(', 지도글)):
        print('  · 지도가 물때 입구를 부릅니다 (?region= 도 읽습니다)')

    # ── 권역·관측소·요청이 **한 세트**인가 (2026-10-02 바깥 검수)
    #
    #   겪은 일 — `/tide/?region=buan` 에서 제목은 「부안 2주 물때」
    #   인데 바로 옆이 「**강화대교** 관측소 기준」이었습니다.
    #   쪽을 만들 때 첫 권역으로 찍히는데, 갈아 끼울 때 **이름만
    #   바꾸고 관측소를 안 바꿨습니다.**
    #
    #   손님이 **엉뚱한 관측소 기준**으로 물때를 읽게 됩니다.
    #   문구 문제가 아니라 바인딩 결함입니다.
    지도글2 = _주석빼기(읽기(지도길))
    if 지도글2:
        한세트 = [
            ('제목을 갈아 끼움', r'상세이름칸\(\)'),
            # ★ **글자가 아니라 실제 대입**을 봅니다 (2026-10-02)
            #   처음에는 `tdStation` 이라는 글자만 찾았습니다.
            #   뮤테이션으로 **대입 줄을 지웠는데 통과**했습니다 —
            #   `getElementById('tdStation')` 줄이 남아 있었기
            #   때문입니다. 「문구만 있고 기능은 없는」 것을 잡으려는
            #   검사기가 또 그 덫에 걸렸습니다.
            ('관측소를 갈아 끼움',
             r"""관칸\.textContent\s*="""),
            ('물때 입구에 관측소를 넘김',
             r'갈아끼우기\s*\(\s*r\.id\s*,\s*r\.관측소'),
        ]
        빠진세트 = [무엇 for 무엇, 표식 in 한세트
                    if not re.search(표식, 지도글2)]
        if 빠진세트:
            모자란것.append('권역을 갈아 끼울 때 %s'
                            % ' · '.join(빠진세트))
        else:
            print('  · 권역·관측소·요청이 한 세트로 바뀝니다')

    if 모자란것:
        막음.append('약속한 기능이 모자란 곳 %d가지' % len(모자란것))
        print('  ✗ 약속한 기능이 모자랍니다 %d가지' % len(모자란것))
        for x in 모자란것:
            print('      %s' % x)
        print('      → **글만 넣고 기능을 안 만들면** 손님은 헛걸음합니다.')
    if 어긴것:
        묶음 = {}
        for 쪽, 글자, 주소, 말 in 어긴것:
            묶음.setdefault((말, 주소), []).append((쪽, 글자))
        막음.append('약속한 것이 간 쪽에 없는 곳 %d갈래' % len(어긴것))
        print('  ✗ 약속한 것이 간 쪽에 없는 곳 %d갈래' % len(어긴것))
        for (말, 주소), 들 in sorted(묶음.items(), key=lambda t: -len(t[1])):
            print('      「%s」 → %s  (그런 쪽 %d개)'
                  % (말, 주소, len(들)))
            if '--list' in sys.argv:
                for 쪽, 글자 in 들:
                    print('          %s — %s' % (쪽, 글자))
            else:
                print('          보기: %s — %s' % (들[0][0], 들[0][1]))
    else:
        print('  · 단추가 약속한 것이 모두 간 쪽에 있습니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림[:4]:
            print('  ~ %s' % x)
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  **링크가 살아 있는 것과 약속을 지킨 것은 다릅니다.**')
        print('  쪽은 있고 404 도 아니지만, 손님이 찾던 것이')
        print('  거기 없으면 헛걸음입니다.')
        print('  글을 사실대로 고치거나, 그 자료를 그 쪽에 두세요.')
        return 1 if '--strict' in sys.argv else 0

    print('단추가 약속한 것이 모두 제자리에 있습니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
