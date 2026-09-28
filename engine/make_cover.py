# -*- coding: utf-8 -*-
"""사진 자료가 없는 쪽에 쓸 **그림**을 만듭니다.

★ 왜 생겼나 (2026-09-27 주인 지시 「정보가 없다면 너가 어울리게 사진으로 만들어」)

    목록 쪽 셋은 사진 자료가 없습니다.

        catch/index.html      해루질 대상 목록
        fish/index.html       낚시 어종 목록
        festival/index.html   축제 달력

    규칙 6-1 은 「쪽에는 보이는 것이 있어야 한다」입니다. 그런데
    없는 사진을 끌어다 쓸 수는 없습니다.

★ 사진인 척하지 않습니다 (주인 규칙 5)
    이것은 **그림**입니다. 설명에 「그림 · 바다가자닷컴」이라 적고,
    촬영자를 지어내지 않습니다. 없는 촬영자를 적는 것이 없는 사진을
    쓰는 것보다 나쁩니다.

★ 손으로 그려 두지 않습니다 (주인 규칙 26)
    엔진이 만듭니다. 색을 바꾸거나 쪽이 늘면 여기만 고칩니다.

★ 두 번 돌려도 같아야 합니다 (계약-07)
    아무 흔들림도 넣지 않습니다. 같은 자료면 같은 그림입니다.

쓰는 법
    python engine/make_cover.py            무엇을 만들지 봅니다
    python engine/make_cover.py --write    assets/cover/ 에 씁니다
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# 사이트 색 — assets/css/site.css 와 같은 값을 씁니다
하늘 = '#FBE9D2'
하늘아래 = '#F6D6B4'
바다 = '#2E5C6E'
바다얕은 = '#4A8095'
모래 = '#E8D5B7'
짙은 = '#24343C'
주황 = '#C07B22'

# 만들 그림들 — (파일이름, 제목, 그릴것)
그릴것들 = [
    ('catch-cover.svg', '갯벌과 조개', '갯벌'),
    ('fish-cover.svg', '바다와 물고기', '물고기'),
    ('festival-cover.svg', '바닷가 축제', '축제'),
]


def _물결(y, 색, 진하기, 높이=14, 너비=1200):
    """물결 한 줄. 같은 값이면 늘 같은 모양입니다."""
    조각 = []
    칸 = 너비 // 6
    조각.append('M0 %d' % y)
    위 = True
    for i in range(6):
        x1 = 칸 * i + 칸 // 2
        x2 = 칸 * (i + 1)
        조각.append('Q %d %d %d %d' % (x1, y - 높이 if 위 else y + 높이, x2, y))
        위 = not 위
    return ('<path d="%s" fill="none" stroke="%s" stroke-width="2.4" '
            'stroke-linecap="round" opacity="%.2f"/>'
            % (' '.join(조각), 색, 진하기))


def 갯벌():
    """썰물에 드러난 갯벌 — 물골이 굽이치고 조개가 흩어져 있습니다."""
    몸 = []
    몸.append('<rect width="1200" height="800" fill="%s"/>' % 하늘)
    몸.append('<circle cx="940" cy="132" r="56" fill="#F3C083" opacity="0.95"/>')
    # 먼 섬 — 바다가 주제로 보이게 (규칙 3)
    몸.append('<path d="M0 316 Q 90 292 170 316 Z" fill="#9BB0B8" '
              'opacity="0.55"/>')
    몸.append('<path d="M1010 318 Q 1090 286 1200 318 Z" fill="#9BB0B8" '
              'opacity="0.5"/>')
    # 먼 바다
    몸.append('<path d="M0 318 H1200 V392 H0 Z" fill="%s"/>' % 바다얕은)
    for i, y in enumerate((334, 358, 380)):
        몸.append(_물결(y, '#FFFFFF', 0.30 - i * 0.07, 6))
    # 갯벌 — 물이 빠진 자리
    몸.append('<path d="M0 392 H1200 V800 H0 Z" fill="%s"/>' % 모래)
    # 물골 — 굽이치게 (곧게 그었더니 돗자리처럼 보였습니다)
    골들 = (
        (430, 'M-30 430 C 180 404, 300 462, 520 438 S 900 400 1230 436'),
        (512, 'M-30 512 C 220 556, 380 470, 640 520 S 980 566 1230 506'),
        (614, 'M-30 614 C 160 572, 420 660, 700 606 S 1010 556 1230 618'),
        (724, 'M-30 724 C 260 682, 460 780, 760 716 S 1040 668 1230 730'),
    )
    for i, (y, d) in enumerate(골들):
        몸.append('<path d="%s" fill="none" stroke="%s" stroke-width="%d" '
                  'opacity="%.2f" stroke-linecap="round"/>'
                  % (d, 바다얕은, 9 + i * 4, 0.34 + i * 0.07))
        몸.append('<path d="%s" fill="none" stroke="#FFFFFF" stroke-width="%d" '
                  'opacity="0.18" stroke-linecap="round"/>' % (d, 3 + i))
    # 조개 — 크고 또렷하게
    조개들 = ((250, 560, 46, -14), (470, 668, 38, 10), (760, 620, 42, -6),
              (980, 726, 34, 16), (355, 762, 30, -20))
    for cx, cy, r, 돌 in 조개들:
        몸.append('<g transform="translate(%d %d) rotate(%d)">' % (cx, cy, 돌))
        몸.append('<path d="M-%d 0 Q -%d -%d 0 -%d Q %d -%d %d 0 Z" '
                  'fill="#FFF7EB" stroke="#CDB795" stroke-width="2"/>'
                  % (r, int(r * 0.9), int(r * 0.95), int(r * 1.02),
                     int(r * 0.9), int(r * 0.95), r))
        for k in (-3, -1.5, 0, 1.5, 3):
            몸.append('<path d="M0 0 L %d -%d" stroke="#D9C5A6" '
                      'stroke-width="2" opacity="0.8"/>'
                      % (int(k * r / 4.0), int(r * 0.82)))
        몸.append('</g>')
    return ''.join(몸)


def 물고기():
    """바닷속 — 깊어질수록 어두워지고 물고기가 떠다닙니다."""
    몸 = []
    몸.append('<defs><linearGradient id="깊이" x1="0" y1="0" x2="0" y2="1">'
              '<stop offset="0" stop-color="#3C7488"/>'
              '<stop offset="1" stop-color="#17323E"/></linearGradient></defs>')
    몸.append('<rect width="1200" height="800" fill="url(#깊이)"/>')
    # 빛줄기
    for x in (170, 400, 690, 960):
        몸.append('<path d="M%d 0 L%d 800 L%d 800 L%d 0 Z" fill="#FFFFFF" '
                  'opacity="0.055"/>' % (x, x - 80, x + 46, x + 104))
    for i, y in enumerate((70, 116, 160)):
        몸.append(_물결(y, '#FFFFFF', 0.24 - i * 0.06, 9))
    # 물방울
    for cx, cy, r in ((150, 240, 7), (210, 180, 5), (1040, 300, 6),
                      (980, 230, 4), (620, 160, 5)):
        몸.append('<circle cx="%d" cy="%d" r="%d" fill="#FFFFFF" '
                  'opacity="0.22"/>' % (cx, cy, r))
    # 물고기 — 멀수록 흐리게
    물고기들 = ((300, 360, 1.05, 주황, 1.0), (660, 268, 0.62, '#E8B06A', 0.75),
                (820, 540, 1.3, '#F0D6A8', 1.0), (420, 640, 0.5, '#E8B06A', 0.6),
                (1000, 420, 0.7, '#D9A05B', 0.8))
    for cx, cy, sc, 색, 진 in 물고기들:
        몸.append('<g transform="translate(%d %d) scale(%.2f)" opacity="%.2f">'
                  % (cx, cy, sc, 진))
        몸.append('<path d="M-92 0 C -58 -48, 58 -48, 98 0 C 58 48, -58 48, '
                  '-92 0 Z" fill="%s"/>' % 색)
        몸.append('<path d="M-92 0 L -146 -36 L -132 0 L -146 36 Z" '
                  'fill="%s" opacity="0.8"/>' % 색)
        몸.append('<path d="M-30 -34 Q 4 -58 36 -30 Z" fill="%s" '
                  'opacity="0.55"/>' % 짙은)
        몸.append('<path d="M-24 30 Q 0 48 24 30 Z" fill="%s" '
                  'opacity="0.35"/>' % 짙은)
        몸.append('<circle cx="60" cy="-10" r="8" fill="#FFFFFF"/>')
        몸.append('<circle cx="62" cy="-10" r="4.5" fill="%s"/>' % 짙은)
        몸.append('</g>')
    # 바닥 해초
    몸.append('<path d="M0 800 Q 110 686 72 604 Q 186 700 148 800 Z" '
              'fill="#12463A" opacity="0.85"/>')
    몸.append('<path d="M1200 800 Q 1086 694 1136 598 Q 1014 698 1056 800 Z" '
              'fill="#12463A" opacity="0.85"/>')
    몸.append('<path d="M560 800 Q 606 716 586 662 Q 656 728 632 800 Z" '
              'fill="#12463A" opacity="0.6"/>')
    return ''.join(몸)


def 축제():
    """바닷가 밤 축제 — 등이 걸리고 물에 불빛이 어립니다."""
    몸 = []
    몸.append('<defs>'
              '<radialGradient id="불빛"><stop offset="0" stop-color="#FFE9B8" '
              'stop-opacity="0.55"/><stop offset="1" stop-color="#FFE9B8" '
              'stop-opacity="0"/></radialGradient>'
              '<linearGradient id="밤" x1="0" y1="0" x2="0" y2="1">'
              '<stop offset="0" stop-color="#101C24"/>'
              '<stop offset="1" stop-color="#1D3440"/></linearGradient>'
              '</defs>')
    몸.append('<rect width="1200" height="800" fill="url(#밤)"/>')
    # 달과 별
    몸.append('<circle cx="1010" cy="118" r="70" fill="url(#불빛)"/>')
    몸.append('<circle cx="1010" cy="118" r="46" fill="#F5E2B8"/>')
    for cx, cy, r in ((160, 92, 3), (330, 58, 2), (520, 118, 2.5),
                      (700, 70, 2), (860, 150, 2.5), (1140, 210, 2),
                      (240, 168, 2), (620, 196, 1.8)):
        몸.append('<circle cx="%d" cy="%d" r="%s" fill="#F5E2B8" '
                  'opacity="0.75"/>' % (cx, cy, r))

    # 등 줄 두 개 — 번짐을 **먼저** 깔고 그 위에 등을 놓습니다
    등자리 = []
    for 줄, y0 in ((0, 176), (1, 252)):
        몸.append('<path d="M-20 %d Q 600 %d 1220 %d" fill="none" '
                  'stroke="#6C5A48" stroke-width="3"/>' % (y0, y0 + 74, y0))
        for i in range(9):
            x = 60 + i * 135
            t = (x + 20) / 1240.0
            cy = int((1 - t) ** 2 * y0 + 2 * (1 - t) * t * (y0 + 74)
                     + t ** 2 * y0)
            색 = (주황, '#E8B06A', '#F5E2B8')[(i + 줄) % 3]
            등자리.append((x, cy + 37, 색))
    for x, y, 색 in 등자리:                      # 번짐 먼저
        몸.append('<circle cx="%d" cy="%d" r="44" fill="url(#불빛)"/>'
                  % (x, y))
    for 줄, y0 in ((0, 176), (1, 252)):          # 줄과 등
        for i in range(9):
            x = 60 + i * 135
            t = (x + 20) / 1240.0
            cy = int((1 - t) ** 2 * y0 + 2 * (1 - t) * t * (y0 + 74)
                     + t ** 2 * y0)
            색 = (주황, '#E8B06A', '#F5E2B8')[(i + 줄) % 3]
            몸.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#6C5A48" '
                      'stroke-width="2"/>' % (x, cy, x, cy + 16))
            몸.append('<ellipse cx="%d" cy="%d" rx="17" ry="21" fill="%s"/>'
                      % (x, cy + 37, 색))

    # 방파제와 등대 — 사람은 넣지 않습니다 (규칙 2)
    몸.append('<path d="M0 456 H320 V440 H348 V456 H1200 V474 H0 Z" '
              'fill="#0A1318"/>')
    몸.append('<rect x="330" y="366" width="16" height="76" fill="#0A1318"/>')
    몸.append('<circle cx="338" cy="360" r="40" fill="url(#불빛)"/>')
    몸.append('<circle cx="338" cy="360" r="11" fill="#F5E2B8"/>')

    # 바다
    몸.append('<path d="M0 474 H1200 V800 H0 Z" fill="#15303C"/>')
    # 물에 어린 불빛
    #
    # ★ 두 번 고쳤습니다 (2026-09-27)
    #   처음: 넓은 삼각형 → 물에 비친 것이 아니라 **조명**처럼 보임
    #   두 번째: 등마다 세로줄 → 줄이 스물여덟이라 **그물**처럼 보임
    #   지금: 몇 개만, 넓고 흐리게. 달빛 하나만 또렷하게 둡니다.
    for i, (x, _, 색) in enumerate(등자리):
        if i % 4:                      # 넷에 하나만 비칩니다
            continue
        몸.append('<ellipse cx="%d" cy="560" rx="26" ry="86" fill="%s" '
                  'opacity="0.10"/>' % (x, 색))
    # 달빛 — 물 위로 길게 퍼집니다
    몸.append('<path d="M986 480 L1034 480 L1076 800 L944 800 Z" '
              'fill="#F5E2B8" opacity="0.13"/>')
    몸.append('<ellipse cx="1010" cy="500" rx="30" ry="14" fill="#F5E2B8" '
              'opacity="0.35"/>')
    # 물결 — 아래로 갈수록 넓고 느리게
    for i, y in enumerate((496, 542, 598, 664, 740)):
        몸.append(_물결(y, '#F5E2B8', 0.26 - i * 0.04, 8 + i * 4))
    return ''.join(몸)


그리개 = {'갯벌': 갯벌, '물고기': 물고기, '축제': 축제}


def 만들기(무엇, 제목):
    몸 = 그리개[무엇]()
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" '
            'width="1200" height="800" role="img" aria-label="%s">'
            '<title>%s</title>%s</svg>' % (제목, 제목, 몸))


def main():
    쓰기 = '--write' in sys.argv
    나갈뿌리 = os.path.join(ASSETS, 'cover')

    print('사진 자료가 없는 쪽에 쓸 그림 만들기')
    print('  (2026-09-27 주인 지시. **사진이 아니라 그림입니다** —')
    print('   설명에 「그림 · 바다가자닷컴」이라 적고 촬영자를 지어내지 않습니다)')
    print('')
    for 이름, 제목, 무엇 in 그릴것들:
        글 = 만들기(무엇, 제목)
        print('  %-22s %-14s %6.1fKB' % (이름, 제목, len(글) / 1024.0))
        if 쓰기:
            io.write(os.path.join(나갈뿌리, 이름), 글)
    print('')
    if 쓰기:
        print('썼습니다: assets/cover/ (%d개)' % len(그릴것들))
    else:
        print('--write 를 붙이면 assets/cover/ 에 씁니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
