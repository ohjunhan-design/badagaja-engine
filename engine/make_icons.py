# -*- coding: utf-8 -*-
"""어종·해루질 대상 **아이콘 15가지**를 그립니다.

★ 왜 (2026-09-28)

    주인 지적으로 목록 쪽 맨 위의 큰 덮개 그림을 뺐더니,
    `check_photos` 가 바로 잡았습니다.

        ✗ 2쪽에 그림이 하나도 없습니다
            catch/index.html · fish/index.html
        → 글만 있는 쪽에는 손님이 머물지 않습니다 (주인 규칙 6-1)

    **큰 그림을 빼는 것과 아무것도 안 보이는 것은 다릅니다.**
    옛 쪽도 카드마다 작은 그림이 있었습니다.

    자료(`data/raw/guide/`)에 이미 `그림` 칸이 있습니다 —
    35가지 대상 전부에 이름이 적혀 있는데(shell · crab · float …)
    정작 그 그림이 없었습니다. 여기서 만듭니다.

★ 사진이 아니라 **그린 그림**입니다
    주인 규칙 5 — 사진의 촬영자는 API 가 준 값만 적습니다.
    이건 사진이 아니라 제가 그린 것이라 촬영자가 없습니다.
    `assets/icon/` 에 따로 두어 사진과 섞이지 않게 합니다.

쓰는 법
    python engine/make_icons.py            무엇을 그릴지 봅니다
    python engine/make_icons.py --write    그립니다
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# 색 — 사이트 차림표와 같은 결로
바다 = '#2E7D9A'
연한바다 = '#BFDCE6'
모래 = '#E5C99A'
진한모래 = '#B8935C'
잉크 = '#3B4A52'
주황 = '#D9873A'

틀 = ('<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" '
      'role="img" aria-label="%s">%s</svg>')


# ── 그림 15가지 ────────────────────────────────────────────
#
#   ★ 알아볼 수 있을 만큼만 단순하게 그립니다.
#     카드 안에서 28px 로 작게 나오므로 자잘한 선은 뭉개집니다.
그림들 = {
    'shell': ('조개', (
        '<path d="M24 38 C10 30 8 18 24 10 C40 18 38 30 24 38Z" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<path d="M24 11 V37 M16 14 L20 36 M32 14 L28 36" '
        'stroke="%s" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        % (모래, 진한모래, 진한모래))),

    'razor': ('맛조개', (
        '<rect x="20" y="8" width="8" height="32" rx="4" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<path d="M24 11 V37" stroke="%s" stroke-width="1.4"/>'
        % (모래, 진한모래, 진한모래))),

    'snail': ('고둥', (
        '<path d="M28 12 C16 12 12 22 18 30 C22 36 32 36 34 28" '
        'fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>'
        '<circle cx="26" cy="24" r="5" fill="%s"/>'
        % (진한모래, 모래))),

    'abalone': ('전복', (
        '<ellipse cx="24" cy="24" rx="15" ry="11" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<circle cx="17" cy="21" r="1.7" fill="%s"/>'
        '<circle cx="22" cy="19" r="1.7" fill="%s"/>'
        '<circle cx="27" cy="19" r="1.7" fill="%s"/>'
        % (잉크, 바다, 연한바다, 연한바다, 연한바다))),

    'crab': ('게', (
        '<ellipse cx="24" cy="26" rx="11" ry="8" fill="%s"/>'
        '<path d="M13 22 L7 16 M35 22 L41 16" stroke="%s" '
        'stroke-width="3" stroke-linecap="round"/>'
        '<path d="M15 32 L10 37 M33 32 L38 37 M20 34 L18 39 M28 34 L30 39" '
        'stroke="%s" stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="20" cy="23" r="1.7" fill="#fff"/>'
        '<circle cx="28" cy="23" r="1.7" fill="#fff"/>'
        % (주황, 주황, 주황))),

    'octopus': ('문어·낙지', (
        '<path d="M24 10 C32 10 36 16 36 22 L36 26 L12 26 L12 22 '
        'C12 16 16 10 24 10Z" fill="%s"/>'
        '<path d="M14 27 C12 33 10 36 8 38 M20 27 C19 34 18 37 17 40 '
        'M28 27 C29 34 30 37 31 40 M34 27 C36 33 38 36 40 38" '
        'stroke="%s" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        '<circle cx="20" cy="20" r="1.8" fill="#fff"/>'
        '<circle cx="28" cy="20" r="1.8" fill="#fff"/>'
        % (주황, 주황))),

    'worm': ('갯지렁이', (
        '<path d="M8 30 C14 20 20 38 26 26 C31 16 37 32 42 24" '
        'stroke="%s" stroke-width="4" fill="none" stroke-linecap="round"/>'
        % 주황)),

    'fish': ('물고기', (
        '<path d="M8 24 C14 15 28 15 36 24 C28 33 14 33 8 24Z" fill="%s"/>'
        '<path d="M36 24 L43 18 L43 30Z" fill="%s"/>'
        '<circle cx="16" cy="22" r="2" fill="#fff"/>'
        % (바다, 바다))),

    'rock': ('갯바위', (
        '<path d="M6 38 L16 18 L24 30 L32 14 L42 38Z" '
        'fill="%s" stroke="%s" stroke-width="1.6"/>'
        '<path d="M6 38 H42" stroke="%s" stroke-width="2.6" '
        'stroke-linecap="round"/>'
        % (잉크, 잉크, 바다))),

    # ── 채비 ──────────────────────────────────────────────
    'float': ('찌 채비', (
        '<path d="M24 6 V20" stroke="%s" stroke-width="2"/>'
        '<path d="M24 20 C29 24 29 31 24 35 C19 31 19 24 24 20Z" fill="%s"/>'
        '<path d="M24 35 V42" stroke="%s" stroke-width="2"/>'
        % (잉크, 주황, 잉크))),

    'bottom': ('바닥 채비', (
        '<path d="M24 6 V26" stroke="%s" stroke-width="2"/>'
        '<path d="M18 26 H30 L27 34 H21Z" fill="%s"/>'
        '<path d="M24 34 C24 40 30 40 30 36" stroke="%s" '
        'stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        '<path d="M6 42 H42" stroke="%s" stroke-width="2.4" '
        'stroke-linecap="round"/>'
        % (잉크, 잉크, 주황, 진한모래))),

    'jighead': ('지그헤드', (
        '<circle cx="18" cy="18" r="7" fill="%s"/>'
        '<path d="M18 25 C18 34 28 36 30 30" stroke="%s" '
        'stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        '<path d="M18 11 V5" stroke="%s" stroke-width="2"/>'
        % (잉크, 주황, 잉크))),

    'egi': ('에기', (
        '<path d="M14 34 L30 12 C34 16 35 24 30 30 L18 38Z" fill="%s"/>'
        '<path d="M14 34 L8 40 M18 38 L12 42" stroke="%s" '
        'stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="28" cy="18" r="2" fill="#fff"/>'
        % (주황, 주황))),

    'sabiki': ('카드 채비', (
        '<path d="M24 5 V43" stroke="%s" stroke-width="2"/>'
        '<path d="M24 13 C30 13 31 18 27 19 M24 23 C30 23 31 28 27 29 '
        'M24 33 C30 33 31 38 27 39" stroke="%s" stroke-width="2.2" '
        'fill="none" stroke-linecap="round"/>'
        % (잉크, 주황))),

    'lure': ('루어', (
        '<ellipse cx="22" cy="22" rx="12" ry="7" '
        'transform="rotate(-25 22 22)" fill="%s"/>'
        '<circle cx="15" cy="17" r="1.8" fill="#fff"/>'
        '<path d="M30 28 C30 35 36 35 36 31 M22 32 C22 39 28 39 28 35" '
        'stroke="%s" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        % (바다, 주황))),
}


def main():
    쓰기 = '--write' in sys.argv
    칸 = os.path.join(ASSETS, 'icon')
    print('어종·해루질 아이콘을 그립니다 (주인 규칙 6-1)')
    print('  자리: %s' % os.path.relpath(칸, ROOT))
    print('')
    for 이름 in sorted(그림들):
        대체글, 속 = 그림들[이름]
        s = 틀 % (대체글, 속)
        print('  · %-10s %-12s %4d바이트' % (이름, 대체글, len(s)))
        if 쓰기:
            io.write(os.path.join(칸, '%s.svg' % 이름), s)
    print('')
    if not 쓰기:
        print('  보여만 준 것입니다. 그리려면 --write 를 붙이세요.')
        return 0
    print('아이콘 %d개를 그렸습니다.' % len(그림들))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
