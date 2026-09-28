# -*- coding: utf-8 -*-
"""**시간별 물높이 그래프**를 옛 사이트에서 새 틀로 옮깁니다.

★ 왜 (2026-09-28 주인 지적)

    주인이 옛 물때 쪽 화면을 보내시며 말씀하셨습니다.

        「물때표도 이 그림이 더 좋은거 같아 그래프가 빠져있어」

    재 보니 맞았습니다 — 새 권역 쪽에 그래프가 **0개**였습니다.

        옛 쪽   🌊 시간별 물높이 — 만조·간조를 곡선으로, 지금 자리를 점선으로
        새 쪽   물때 띠만 있고 그래프가 없음

    숫자만 있는 것과 곡선으로 보는 것은 다릅니다.
    **「지금 물이 차고 있나 빠지고 있나」는 곡선이라야 한눈에 보입니다.**
    주인 규칙 6-1 — 「사람은 눈으로 봅니다」.

★ 무엇을 옮기나
    js/tide-graph.js   →  assets/js/tide-graph.js   (그리는 코드)
    css 의 .tg-* 규칙  →  assets/css/tidegraph.css  (모양)

★ 붙는 자리
    옛 쪽은 `js/region-extra.js` 가 `#tideStrip` **바로 아래**에
    칸을 만들어 붙였습니다. 새 틀에도 `#tideStrip` 이 있으므로
    같은 자리에 같은 방식으로 붙입니다.

★ 자료는 서버에서 옵니다
    `api/tide-cache.php` · `api/marine.php` — 국립해양조사원 조석예보.
    둘 다 `keep.json` 의 「남길것」에 `api/` 로 적혀 있어 서버에 그대로
    있습니다. 새 틀이 만들지 않습니다.

쓰는 법
    python engine/migrate_tidegraph.py            무엇을 옮길지 봅니다
    python engine/migrate_tidegraph.py --write    옮깁니다
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# 그래프가 쓰는 class 이름들 — 이 규칙만 골라 옵니다
무늬 = re.compile(r'\.tg-[\w-]+')


def 그리는코드():
    p = os.path.join(OLD, 'js', 'tide-graph.js')
    return io.read(p, default='') if os.path.isfile(p) else ''


def 모양규칙():
    """옛 css 에서 `.tg-*` 가 들어간 규칙만 골라 옵니다.

    ★ 통째로 베끼지 않습니다 — 그래프에 쓰는 것만 옮깁니다.
      나머지를 끌고 오면 새 틀 차림표와 부딪힙니다.
    """
    모음 = []
    for 이름 in ('style.css', 'tide.css', 'gate.css'):
        p = os.path.join(OLD, 'css', 이름)
        if not os.path.isfile(p):
            continue
        s = io.read(p, default='')
        # 규칙 하나 = 고르개 { 속 }
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', s):
            고르개 = m.group(1).strip()
            if 무늬.search(고르개):
                모음.append('%s{%s}' % (고르개.replace('\n', ' '),
                                        m.group(2).strip()))
    return 모음


머리말 = """/* 시간별 물높이 그래프 — 옛 사이트에서 옮겨 온 모양입니다.
 *
 * ★ engine/migrate_tidegraph.py 가 만듭니다. 손으로 고치지 마세요.
 *   고치려면 그 도구를 고치고 다시 돌리세요 (주인 규칙 26).
 *
 * 옛 css/style.css · tide.css · gate.css 에서 `.tg-*` 규칙만 골라 왔습니다.
 */
"""


def main():
    쓰기 = '--write' in sys.argv
    print('시간별 물높이 그래프를 새 틀로 옮깁니다')
    print('  (2026-09-28 주인 지적 「그래프가 빠져있어」)')
    print('')

    코드 = 그리는코드()
    if not 코드:
        print('✗ 옛 그리는 코드를 못 찾았습니다: %s'
              % os.path.join(OLD, 'js', 'tide-graph.js'))
        return 1
    규칙들 = 모양규칙()
    print('  그리는 코드   %5.1fKB' % (len(코드.encode('utf-8')) / 1024))
    print('  모양 규칙     %5d개' % len(규칙들))
    if not 규칙들:
        print('  ✗ `.tg-*` 규칙을 하나도 못 찾았습니다 — 모양이 깨집니다')
        return 1

    if not 쓰기:
        print('')
        print('  보여만 준 것입니다. 옮기려면 --write 를 붙이세요.')
        return 0

    io.write(os.path.join(ASSETS, 'js', 'tide-graph.js'), 코드)
    io.write(os.path.join(ASSETS, 'css', 'tidegraph.css'),
             머리말 + '\n'.join(규칙들) + '\n')
    print('')
    print('  옮겼습니다')
    print('    assets/js/tide-graph.js')
    print('    assets/css/tidegraph.css')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
