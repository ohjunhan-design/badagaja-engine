# -*- coding: utf-8 -*-
"""**검증판임을 밝히고 검색에서 감춥니다** — /_stage/ 에 올리기 직전에 돌립니다.

★ 왜 (2026-09-28 바깥 검수 8차)

    「운영 배포와 검증 배포를 분리하라」

    20번(올린 뒤 서버에서 확인)은 **올려야만** 잴 수 있습니다.
    그렇다고 운영 자리에 바로 올리면 나쁠 때 손님이 먼저 봅니다.
    그래서 같은 서버의 하위 칸(`/_stage/`)에 먼저 올립니다.

★ 검색에서 감추는 법 — **막지 않고 noindex 로** 합니다

    robots.txt 의 `Disallow: /_stage/` 로 막으면 얼핏 깔끔해 보이지만
    **틀렸습니다.** 막으면 검색엔진이 쪽을 읽지 못하고, 읽지 못하면
    쪽 안의 `noindex` 도 못 봅니다. 그런데 다른 데서 링크가 걸리면
    **내용 없이 주소만** 검색에 오를 수 있습니다.

    읽게 두고 `noindex` 를 보여 주는 쪽이 확실합니다.
    canonical 은 그대로 둡니다 — 운영 주소를 가리키고 있어
    검색엔진을 운영 쪽으로 보내 줍니다.

★ 눈으로도 알아보게 합니다

    운영판과 검증판이 똑같이 생기면 주인이 헷갈립니다.
    맨 위에 띠를 하나 답니다. **띠만 보고 바로 알 수 있어야** 합니다.

★ 사이트맵은 지웁니다

    검증판 사이트맵이 남으면 실수로 서치어드바이저에 낼 수 있습니다.

쓰는 법
    python engine/mark_stage.py            무엇이 바뀔지만 봅니다
    python engine/mark_stage.py --write    정말 고칩니다
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

표시 = '<!-- badagaja:stage -->'

메타 = ('<meta name="robots" content="noindex,nofollow">'
        '<meta name="Yeti" content="noindex,nofollow">')

띠 = (
    '<div style="position:sticky;top:0;z-index:9999;background:#b3261e;'
    'color:#fff;font:700 14px/1.4 system-ui,sans-serif;'
    'padding:8px 16px;text-align:center">'
    '검증판입니다 — 손님에게 보이는 쪽이 아닙니다. '
    '<span style="font-weight:400">badagaja.com/_stage/</span>'
    '</div>'
)

지울것 = ('sitemap.xml', 'sitemap-zh.xml')


def 쪽들():
    끝 = []
    for 뿌리, 폴더들, 파일들 in os.walk(NEW):
        폴더들[:] = [x for x in 폴더들 if x not in ('assets', 'img')]
        for 이름 in 파일들:
            if 이름.endswith('.html'):
                끝.append(os.path.join(뿌리, 이름))
    return sorted(끝)


def 고치기(s):
    """이미 표시가 있으면 그냥 둡니다 — 두 번 돌려도 같습니다."""
    if 표시 in s:
        return s, False
    새 = s
    # ── 머리에 noindex
    m = re.search(r'<head[^>]*>', 새, re.I)
    if not m:
        return 새, False
    자리 = m.end()
    새 = 새[:자리] + 표시 + 메타 + 새[자리:]
    # ── 몸 맨 위에 띠
    m = re.search(r'<body[^>]*>', 새, re.I)
    if m:
        자리 = m.end()
        새 = 새[:자리] + 띠 + 새[자리:]
    return 새, True


# ★ **.txt 가 아니라 .json 입니다** (2026-09-28)
#   운영 .htaccess 가 .txt 를 막고 robots·llms·ads 만 허용합니다.
#   처음에 identity.txt 로 두었다가 403 을 받았습니다.
#   검사기는 제대로 일했습니다 — 「안 올라갔거나 딴 곳을 재고
#   있다」며 거기서 멈췄습니다. **몰라서 멈춘 것은 옳습니다.**
#   .htaccess 는 건드리지 않습니다 (주인 규칙 27 — 한 번에 하나).
이름표길 = '__probe__/identity.json'


def 이름표(칸):
    """★ **여기가 어디인지 밝히는 쪽지** (2026-09-28 바깥 검수 9차 숙제 3)

    오늘 이런 일이 있었습니다. 20번 검사가

        assets/css/site.css   404
        about.html            404

    라고 했습니다. 서버 탓인 줄 알고 반나절을 의심했습니다 —
    카페24가 요청을 막나, 해외 IP 를 막나, 구글봇도 못 읽나.
    진단 워크플로까지 만들어 재 봤습니다.

    **검사기가 딴 곳을 묻고 있었습니다.**

        자산:  badagaja.com/assets/css/site.css     ← _stage 가 빠짐
        옛 쪽: badagaja.com/_stage/about.html       ← _stage 가 붙음

    카나리도 뮤테이션도 이걸 못 잡습니다. 그것들은 「사이트에
    불량을 넣으면 잡는가」를 봅니다. 이것은 **「검사기가 애초에
    딴 데를 보고 있지 않은가」** 입니다. 다른 이야기입니다.

    그래서 검증판에 **혼동할 수 없는 쪽지**를 하나 둡니다.
    검사기는 재기 전에 이 쪽지부터 열어 봅니다.
    안 나오면 **거기서 멈춥니다** — 딴 데를 재고 「괜찮다」고
    말하느니 「어디를 재는지 모르겠다」고 하는 편이 낫습니다.
    """
    import json as _j
    return _j.dumps({
        '_무엇인가': 'badagaja-probe',
        '_왜있나': ('이 쪽지가 열리는 자리가 검사기가 재고 있는 자리입니다. '
                    '열리지 않으면 검사기가 딴 곳을 보고 있는 것입니다.'),
        'where': 칸,
        'kind': 'stage',
    }, ensure_ascii=False, indent=2) + '\n'


def main():
    쓸까 = '--write' in sys.argv
    print('검증판임을 밝히고 검색에서 감춥니다')
    print('  자리: %s' % NEW)
    print('')

    목록 = 쪽들()
    if not 목록:
        print('✗ 볼 쪽이 없습니다 — 먼저 engine/build.py 를 돌리세요')
        return 1

    바뀔것 = 0
    머리없음 = []
    for p in 목록:
        s = io.read(p, default='')
        새, 바뀜 = 고치기(s)
        if 바뀜:
            바뀔것 += 1
            if 쓸까:
                io.write(p, 새)
        elif 표시 not in s:
            머리없음.append(os.path.relpath(p, NEW))

    print('[1] 쪽에 noindex 와 띠를 넣습니다')
    print('  쪽 %d개 중 %d개' % (len(목록), 바뀔것))
    if 머리없음:
        print('  ✗ <head> 를 못 찾은 쪽 %d개: %s'
              % (len(머리없음), ' · '.join(머리없음[:3])))
        return 1

    print('[2] 사이트맵을 지웁니다 (실수로 낼 수 있어서)')
    for 이름 in 지울것:
        길 = os.path.join(NEW, 이름)
        if os.path.exists(길):
            print('  · %s' % 이름)
            if 쓸까:
                # 생성물이라 build.py 로 다시 만들면 돌아옵니다.
                # 그래도 밝히고 지웁니다 — 조용히 지우는 것과 다릅니다.
                os.remove(길)  # 계약-17 예외
        else:
            print('  ~ %s 는 원래 없습니다' % 이름)

    칸 = os.environ.get('BADAGAJA_STAGE_CARD', '_stage')
    print('[3] 여기가 어디인지 밝히는 쪽지를 둡니다')
    print('  · %s   (칸 이름: %s)' % (이름표길, 칸))

    print('')
    if not 쓸까:
        print('  (아직 안 고쳤습니다. --write 를 붙이면 고칩니다)')
        return 0

    io.write(os.path.join(NEW, *이름표길.split('/')), 이름표(칸))
    print('  고쳤습니다. 이제 /_stage/ 에 올려도 됩니다.')
    print('  ★ 이 자리는 **검증판**입니다. 운영에 그대로 올리면 안 됩니다')
    print('    — 쪽마다 noindex 가 박혀 검색에서 통째로 사라집니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
