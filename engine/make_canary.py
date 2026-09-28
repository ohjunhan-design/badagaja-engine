# -*- coding: utf-8 -*-
"""카나리 — **일부러 망가뜨린 표본 쪽**을 만듭니다.

★ 이 쪽들은 고치면 안 됩니다
    `tests/canary/` 안의 쪽은 **탈이 있는 채로** 저장소에 있습니다.
    검사기가 저것을 못 잡으면 그 검사기가 죽은 것입니다.
    (까닭은 engine/check_canary.py 맨 위에 적었습니다)

★ 만든 뒤 **정말 망가졌는지 확인**합니다
    2026-09-27 에 망가뜨리는 코드가 조용히 죽어서
    「아무것도 안 망가진 표본」을 만든 적이 있습니다.
    그래서 여기서는 만들고 나서 **세어 봅니다.**

쓰는 법
    python engine/make_canary.py            무엇을 만들지 보여만 줍니다
    python engine/make_canary.py --write    만듭니다
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

카나리뿌리 = os.path.join(ROOT, 'tests', 'canary')

머리 = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<link rel="icon" href="favicon.ico">
</head><body>
<p>★ 이 쪽은 <b>일부러 망가뜨린 표본</b>입니다. 고치지 마세요.
   engine/check_canary.py 가 검사기의 생사를 재는 데 씁니다.</p>
"""
꼬리 = """
</body></html>
"""

# 멀쩡한 바탕 — 여기에 탈 하나만 넣습니다
성한몸 = """
<img src="a.webp" alt="바닷가 갯바위" width="800" height="600">
<a href="b.html">다른 쪽으로</a>
"""


def 쪽만들기(제목, 몸):
    return 머리 % 제목 + 몸 + 꼬리


# ── 카나리 목록 ────────────────────────────────────────────
#   (칸이름, 제목, 몸, 정말 망가졌는지 재는 함수)
def _빈링크있나(s):
    return len(re.findall(r'<a\b[^>]*\bhref=(""|\'\')', s)) >= 1


def _링크안링크있나(s):
    for m in re.finditer(r'(?is)<a\b[^>]*>(.*?)</a>', s):
        if re.search(r'<a\b[^>]*\bhref=', m.group(1), re.I):
            return True
    return False


def _보이는것없나(s):
    몸 = re.sub(r'(?is)<head\b.*?</head>', ' ', s)
    return not re.search(r'(?i)<(img|svg|picture)\b', 몸)


def _알트없는사진있나(s):
    for m in re.finditer(r'(?is)<img\b[^>]*>', s):
        if not re.search(r'\balt=', m.group(0), re.I):
            return True
    return False


카나리들 = [
    ('빈링크', '빈 링크 카나리',
     성한몸 + '\n<a href="" >홈으로</a>\n',
     _빈링크있나),

    ('링크안링크', '링크 안에 링크 카나리',
     성한몸 + '\n<a href="c.html">겉<a href="d.html">속</a></a>\n',
     _링크안링크있나),

    ('보이는것없음', '보이는 것이 없는 카나리',
     '\n<p>글만 있습니다. 사진도 그림도 없습니다.</p>\n'
     '<a href="b.html">다른 쪽으로</a>\n',
     _보이는것없나),

    ('알트없음', 'alt 없는 사진 카나리',
     '\n<img src="a.webp" width="800" height="600">\n'
     '<a href="b.html">다른 쪽으로</a>\n',
     _알트없는사진있나),
]


def main():
    쓰기 = '--write' in sys.argv
    print('카나리 — 일부러 망가뜨린 표본을 만듭니다')
    print('  자리: %s' % os.path.relpath(카나리뿌리, ROOT))
    print('')

    탈 = 0
    for 칸, 제목, 몸, 잰다 in 카나리들:
        s = 쪽만들기(제목, 몸)

        # ★ 정말 망가졌는지 **여기서** 봅니다
        #   망가뜨리는 코드가 죽으면 성한 쪽이 나오는데,
        #   그러면 검사기가 못 잡아도 알 길이 없습니다.
        정말망가졌나 = 잰다(s)
        표 = '·' if 정말망가졌나 else '✗'
        print('  %s %-14s %s' % (표, 칸, 제목))
        if not 정말망가졌나:
            print('      **안 망가졌습니다** — 만드는 코드를 보세요')
            탈 += 1
            continue

        if 쓰기:
            io.write(os.path.join(카나리뿌리, 칸, 'index.html'), s)
            # 검사기가 아이콘을 찾으므로 빈 파일을 둡니다
            for 아이콘 in ('favicon.ico',):
                길 = os.path.join(카나리뿌리, 칸, 아이콘)
                if not os.path.exists(길):
                    io.write(길, '')

    print('')
    if 탈:
        print('✗ %d개가 안 망가졌습니다 — 카나리가 아닙니다' % 탈)
        return 1
    if not 쓰기:
        print('보여만 준 것입니다. 만들려면 --write 를 붙이세요.')
        return 0
    print('카나리 %d개를 만들었습니다.' % len(카나리들))
    print('  ★ 이 쪽들은 **고치지 마세요.** 망가진 채로 두어야 합니다.')
    print('  python engine/check_canary.py 로 검사기의 생사를 잽니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
