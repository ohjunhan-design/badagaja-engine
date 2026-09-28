# -*- coding: utf-8 -*-
"""옛 첫 화면의 **차림표**를 새 틀로 옮깁니다.

★ 왜 (2026-09-27 주인 지시)

      「기존 디자인이 더 좋아」
      「기존 인덱스 페이지에 정말 많은 공이 들어가 있어」

    맞습니다. 그 공을 버리지 않습니다. 겉은 옛것 그대로 가져오고,
    속(숫자·물때·링크)만 새 엔진이 채웁니다.

        겉  짜임 · 색 · 카드 · 차례        → 옛것 그대로
        속  숫자 · 물때 셈 · 링크 · 기준일 → 새 엔진

    그냥 옛 index.html 을 쓰면 이런 일이 납니다 (2026-09-27 재어 봄).
      · 축제 190·어종 35 가 **손으로 박혀** 있어 지금 값(197·104)과 다름
      · 물때가 옛 셈으로 돌아감 (흔들림 0항 ↔ 새것 30항)
      · 「○년 ○월 기준」이 없음

무엇을 옮기나
    옛 css/gate.css 가 첫 화면 차림표입니다. 그것이 기대는 색 변수
    여덟 개를 css/style.css 에서 **찾아 읽어** 앞에 붙입니다.
    손으로 베껴 적지 않습니다 — 베끼면 옛것이 바뀌어도 모릅니다.

★ 두 번 돌려도 같아야 합니다 (계약-07)

쓰는 법
    python engine/migrate_home.py            무엇이 옮겨질지 봅니다
    python engine/migrate_home.py --write    assets/css/home.css 를 씁니다
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

바탕차림표 = 'css/gate.css'
변수차림표 = 'css/style.css'

# gate.css 가 제 안에서 정하지 않고 밖에서 받는 색들
# (--c·--bg 는 카드마다 style="" 로 넣으므로 뺍니다)
받을변수 = ('--foam', '--foam-dim', '--ink', '--lantern', '--lantern-dim',
            '--line', '--night', '--teal')

막음, 알림 = [], []


def 변수찾기():
    """옛 style.css 에서 색 값을 **찾아 읽습니다.** 손으로 안 적습니다."""
    p = os.path.join(OLD, 변수차림표.replace('/', os.sep))
    s = io.read(p, default='')
    나옴 = {}
    for v in 받을변수:
        m = re.search(re.escape(v) + r'\s*:\s*([^;]+);', s)
        if m:
            나옴[v] = m.group(1).strip()
    return 나옴


def 만들기():
    바탕 = io.read(os.path.join(OLD, 바탕차림표.replace('/', os.sep)),
                   default='')
    if not 바탕:
        막음.append('%s 를 못 읽었습니다' % 바탕차림표)
        return ''
    값들 = 변수찾기()
    없는것 = [v for v in 받을변수 if v not in 값들]
    if 없는것:
        막음.append('색을 못 찾았습니다: %s' % ' '.join(없는것))

    머리 = [
        '/* 첫 화면 차림표 — 옛 사이트에서 옮겨 왔습니다.',
        ' *',
        ' * ★ engine/migrate_home.py 가 만듭니다. 손으로 고치지 마세요.',
        ' *   바탕: 옛 %s' % 바탕차림표,
        ' *   색  : 옛 %s 에서 찾아 읽었습니다' % 변수차림표,
        ' *',
        ' * 2026-09-27 주인 지시 — 「기존 디자인이 더 좋아」',
        ' *   「기존 인덱스 페이지에 정말 많은 공이 들어가 있어」',
        ' *   그 공을 버리지 않습니다. 겉은 그대로, 속만 새 엔진입니다.',
        ' */',
        ':root{',
    ]
    for v in 받을변수:
        머리.append('  %s: %s;' % (v, 값들.get(v, 'inherit')))
    머리.append('}')
    머리.append('')
    return '\n'.join(머리) + 바탕


def main():
    쓰기 = '--write' in sys.argv
    글 = 만들기()

    print('옛 첫 화면 차림표를 새 틀로 옮기기 (주인 지시 2026-09-27)')
    print('  옛 저장소  %s' % OLD)
    print('')
    값들 = 변수찾기()
    print('[1] 색을 찾았는가 (손으로 안 적습니다)')
    for v in 받을변수:
        print('      %-14s %s' % (v, 값들.get(v, '✗ 못 찾음')))
    print('')
    print('[2] 차림표')
    print('      바탕 %s  %6.1fKB' % (바탕차림표, len(
        io.read(os.path.join(OLD, 바탕차림표.replace('/', os.sep)),
                default='')) / 1024.0))
    print('      나갈 것  assets/css/home.css  %6.1fKB' % (len(글) / 1024.0))
    print('')

    if 쓰기 and 글:
        io.write(os.path.join(ASSETS, 'css', 'home.css'), 글)
        print('썼습니다: assets/css/home.css')
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0
    if not 쓰기:
        print('--write 를 붙이면 assets/css/home.css 를 씁니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
