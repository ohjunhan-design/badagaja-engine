# -*- coding: utf-8 -*-
"""물때가 **살아 있는 채로** 쪽을 찍습니다 (2026-10-02).

★ 왜 따로 필요한가

  `shot_phone.py` 는 `file://` 로 쪽을 엽니다. 그러면 서버가 없어
  `api/marine.php` 가 404 라 **그래프가 아예 안 그려집니다.**
  그 그림을 보고 「괜찮다」 하면, 손님이 보는 화면과 다른 것을
  본 것입니다. 2026-10-01 에 `check_mobile.py` 가 똑같은 까닭으로
  **1490px 넘침을 놓쳤습니다.**

  그래서 `_fake_tide.py` 의 가짜 응답을 쪽에 **심어** 찍습니다.
  바깥에 안 흔들리면서 **실제와 같은 모습**이 나옵니다.

★ 네 폭을 한 번에 찍습니다 — PC 1440 · 휴대폰 360·390·412
  (지피티 검수 제출 규격. 주인 규칙 6-2 — 눈으로 보는 일)

쓰는 법
  python engine/shot_tide.py site/jeju.html out/  [폭들...]
"""
import os
import re
import shutil
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import _fake_tide            # noqa: E402
from engine import shot_phone            # noqa: E402
from engine import io as _io             # 쓰기는 io.write 로 (계약-13)  # noqa: E402

기본폭 = [1440, 412, 390, 360]


def 심은쪽(쪽길, 더심을것=''):
    """쪽 **옆에** 가짜 물때를 심은 복사본을 만들어 그 길을 돌려줍니다.

    ★ 반드시 **같은 폴더**여야 합니다 — 차림표·그림이 상대 주소라,
      다른 데로 옮기면 민낯으로 찍힙니다.
    """
    글 = _io.read(쪽길) if hasattr(_io, 'read') else open(
        쪽길, encoding='utf-8').read()
    심을것 = _fake_tide.심을글() + (더심을것 or '')
    # </head> **바로 앞**에 넣습니다 — 쪽의 js 가 돌기 전이어야
    # window.fetch 를 가로챌 수 있습니다.
    if '</head>' in 글:
        글 = 글.replace('</head>', 심을것 + '</head>', 1)
    else:
        글 = 심을것 + 글
    낼길 = os.path.join(os.path.dirname(os.path.abspath(쪽길)),
                        '_shot_tmp.html')
    _io.write(낼길, 글)
    return 낼길


def 잘라내기(그림길, 폭):
    """오른쪽 **흰 여백**을 떼어 냅니다.

    ★ 윈도 크롬은 창을 **520px 아래로 못 줄입니다.** 그래서 390px
      틀을 넣어도 그림은 520px 로 나오고, 오른쪽 130px 이 흰 여백
      입니다. 그대로 두면 「오른쪽이 비어 보인다」는 **거짓 인상**을
      줍니다. 틀 폭만큼만 남깁니다.
    """
    if 폭 >= 520:
        return
    try:
        from PIL import Image
    except ImportError:
        return                      # 없으면 그냥 둡니다 — 그림은 멀쩡합니다
    with Image.open(그림길) as im:
        if im.size[0] <= 폭:
            return
        im.crop((0, 0, 폭, im.size[1])).save(그림길)


def 찍기(쪽길, 낼곳, 폭들=None, 더심을것='', 꼬리=''):
    폭들 = 폭들 or 기본폭
    이름 = re.sub(r'[^0-9A-Za-z_-]+', '-',
                  os.path.splitext(os.path.basename(쪽길))[0]).strip('-')
    # ★ **절대 경로여야 합니다** (2026-10-02 겪음)
    #   크롬 `--screenshot=` 는 상대 경로를 **크롬 자기 자리** 기준으로
    #   씁니다. 넘겨 준 자리에 그림이 안 생겨 「못 찍었습니다」가
    #   네 번 떴는데, 실은 **다른 데 찍혀 있었습니다.**
    낼곳 = os.path.abspath(낼곳)
    if not os.path.isdir(낼곳):
        os.makedirs(낼곳)
    임시 = 심은쪽(쪽길, 더심을것)
    난것 = []
    try:
        for w in 폭들:
            # PC 는 길게, 휴대폰은 **훨씬 더** 길게 — 좁을수록 모든 것이
            # 아래로 밀립니다. 3200 으로 찍었더니 물때 그래프가
            # 그림 밖(3200px 아래)에 있어 안 찍혔습니다 (2026-10-02).
            h = 2400 if w >= 1000 else 5200
            그림 = os.path.join(낼곳, '%s-%d%s.png' % (이름, w, 꼬리 or ''))
            if shot_phone.찍기(임시, 그림, w, h):
                잘라내기(그림, w)
                난것.append(그림)
                print('  · %4dpx → %s' % (w, os.path.basename(그림)))
            else:
                print('  ! %4dpx 못 찍었습니다' % w)
    finally:
        if os.path.isfile(임시):
            os.remove(임시)
    return 난것


def main():
    if len(sys.argv) < 3:
        print('쓰는 법: python engine/shot_tide.py <쪽.html> <낼폴더> [폭...]')
        return 2
    폭들 = [int(x) for x in sys.argv[3:]] or None
    난것 = 찍기(sys.argv[1], sys.argv[2], 폭들)
    print('%d장 찍었습니다' % len(난것))
    return 0 if 난것 else 1


if __name__ == '__main__':
    sys.exit(main())
