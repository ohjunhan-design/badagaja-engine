# -*- coding: utf-8 -*-
"""G 드라이브의 **채비 안내도**를 사이트로 들여옵니다.

★ 2026-10-01 주인 지시 — 「지드라이브에 넣어놨으니까 봐봐」

  주인이 챗지피티로 만든 안내도를 G 드라이브에 올려 주십니다.
  대화로 보내신 것은 제가 일하는 중이면 파일로 안 떨어져,
  **G 드라이브가 가장 확실한 길**입니다.

★ 가로판과 세로판
  · 가로판 1484×1060 (1.4:1) — PC 에서 씁니다
  · 세로판 1024×1536 (1:1.5) — **휴대폰**에서 씁니다
    재 보니 가로판은 휴대폰에서 4.6배 축소라 글씨가 4.3px 이
    되어 못 읽습니다. 세로판은 3.2배라 11px — 읽힙니다.

  **세로가 가로보다 긴 것**을 세로판으로 봅니다. 파일 이름이
  아니라 **크기로** 가릅니다 — 이름은 바뀔 수 있습니다.

★ 어느 채비인지는 **이름에 든 말**로 찾습니다
  「초보자를 위한 카드채비 낚시 가이드.png」 → sabiki
  못 찾으면 **건너뛰고 알려 줍니다** — 짐작으로 짝지으면
  엉뚱한 그림이 붙습니다 (주인 규칙 6-1).

쓰는 법
    python engine/import_guides.py            무엇이 들어올지 봅니다
    python engine/import_guides.py --write    들여옵니다
"""
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)
sys.path.insert(0, ROOT)

G = os.environ.get('BADAGAJA_GUIDES', 'G:' + os.sep)
낼곳 = os.path.join(ROOT, 'data', 'img', 'rig')

# 파일 이름에 이 말이 들어 있으면 그 채비입니다.
#   ★ 긴 말을 **먼저** 둡니다 — 「에기」가 「문어 에기」를
#     가로채면 엉뚱한 그림이 붙습니다.
찾을말 = [
    ('문어 에기', 'octopus'),
    ('문어', 'octopus'),
    ('뜰채', 'landing'),
    ('가프', 'landing'),
    ('카드채비', 'sabiki'),
    ('사비키', 'sabiki'),
    ('민장대', 'minjangdae'),
    ('뻗침대', 'minjangdae'),
    ('처넣기', 'maknak'),
    ('맥낚시', 'maknak'),
    ('갈치', 'galchi'),
    ('메탈지그', 'metal'),
    ('다운샷', 'downshot'),
    ('미노우', 'minnow'),
    ('플로팅', 'minnow'),
]


def 어느채비(이름):
    for 말, 갈래 in 찾을말:
        if 말 in 이름:
            return 갈래
    return None


def main():
    쓰기 = '--write' in sys.argv
    if not os.path.isdir(G):
        print('✗ %s 를 못 찾았습니다' % G)
        return 1
    try:
        from PIL import Image
    except ImportError:
        print('✗ Pillow 가 없습니다')
        return 1

    할것, 모를것 = [], []
    for 이름 in sorted(os.listdir(G)):
        if not 이름.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
            continue
        길 = os.path.join(G, 이름)
        if not os.path.isfile(길):
            continue
        갈래 = 어느채비(이름)
        try:
            with Image.open(길) as im:
                w, h = im.size
        except Exception:
            continue
        # 안내도는 1000px 이 넘습니다. 작은 것은 다른 그림입니다.
        if max(w, h) < 900:
            continue
        if not 갈래:
            모를것.append((이름, w, h))
            continue
        세로판 = h > w        # ★ 이름이 아니라 **크기로** 가릅니다
        할것.append((길, 이름, 갈래, 세로판, w, h))

    print('G 드라이브의 채비 안내도를 들여옵니다')
    print('  %s' % G)
    print('')
    if 할것:
        print('%-11s %-7s %-12s %s' % ('갈래', '판', '크기', '파일'))
        for _, 이름, 갈래, 세로판, w, h in 할것:
            print('%-11s %-7s %-12s %s'
                  % (갈래, '세로' if 세로판 else '가로',
                     '%dx%d' % (w, h), 이름[:40]))
    if 모를것:
        print('')
        print('  ! 어느 채비인지 몰라 건너뜁니다 %d개' % len(모를것))
        for 이름, w, h in 모를것:
            print('      %s (%dx%d)' % (이름[:50], w, h))
        print('      → 파일 이름에 채비 이름을 넣어 주세요')

    if not 쓰기:
        print('')
        print('  보여만 준 것입니다. 들여오려면 --write 를 붙이세요.')
        return 0

    os.makedirs(낼곳, exist_ok=True)
    넣음 = 0
    for 길, 이름, 갈래, 세로판, w, h in 할것:
        목적 = os.path.join(낼곳, 갈래 + ('-m' if 세로판 else '') + '.webp')
        # ★ **webp 로 바꿔** 넣습니다 — png 는 2MB 가 넘어
        #   그대로 쓰면 쪽이 느려집니다.
        with Image.open(길) as im:
            im.save(목적, 'WEBP', quality=86, method=5)
        넣음 += 1
    print('')
    print('  안내도 %d장을 들여왔습니다 (data/img/rig/)' % 넣음)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
