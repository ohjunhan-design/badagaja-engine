# -*- coding: utf-8 -*-
"""사진 위에 **임의로 얹은 위치 표시**가 없는가 (2026-10-08).

★ 주인 지시
    「**서는자리 모래바닥 이런거 다 잘못되었어.** 이렇게 하려면
      **빼는 게 더 좋아.** 아니면 사진 이미지가 아닌 **일반 그림으로
      그려주는 게 더 좋지.** 못하면 제외, 할 수 있을 것 같으면 진행」

★ 무엇이 잘못이었나

  하루 전(10-07) 「현실성이 떨어진다」는 지적을 받고 현장 사진을
  그림 바탕에 깔았습니다. 그런데 **바탕 사진은 갈래마다 한 장
  고정**입니다(방파제·갯바위·하구). 그 한 장 위에 어종마다 다른
  표시를 얹으니, 그 사진의 **실제 지형과 표시가 맞지 않습니다.**
  방파제 사진 한 장에 붕장어의 「모래 바닥」을 찍는 식이었습니다.

  바깥 검수 —
    「실제 사진의 지형을 근거로 정확히 판독한 게 아니라면 **오히려
      잘못된 정보를 확정적으로** 보여줍니다. 관광 사진에 선과 점을
      얹어 마치 『여기가 실제 캐스팅 지점』처럼 보이기 때문에
      위험합니다」
    「사진은 『이런 환경』, 도해는 『이런 식으로 노린다』로 **역할을
      분리**하세요」

★ 가르는 축 — 바깥 검수가 정한 둘

    A. 실제 사진 **위** 오버레이   → **막습니다**
       서는 자리 · 캐스팅 방향 · 목표 지점 · 바닥 표시 ·
       사진을 깔고 그 위에 올린 점·선·화살표
    B. 사진과 **떨어진** 일반 도해 → 괜찮습니다
       방파제·갯바위·해변 구조, 낚싯줄 방향, 목표 수심

  둘을 가르는 것은 **같은 그림 안에 사진이 깔려 있는가**입니다.
  `<image>` 나 배경 사진이 있는 `<svg>` 안에 글자·도형이 함께
  있으면 A 입니다.

★ **글은 막지 않습니다.** 「어디서 — 방파제, 내만의 진흙·모래
  바닥」 같은 설명은 자료에서 온 사실입니다. 그림으로 특정 지점을
  **가리키는 것**만 문제입니다.

쓰는 법
    python engine/check_overlay.py
    python engine/check_overlay.py --strict
"""
import io as _io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402
from engine import io    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

막음, 알림 = [], []                 # 계약-21

# 사진 위에 얹으면 **그 자리를 주장하는** 말들
자리주장 = ('서는 자리', '서는자리', '캐스팅', '목표 지점', '노리는 곳',
            '여기서', '이 자리')
# 바닥을 단정하는 말 — 사진 속 바닥이 무엇인지 알 수 없습니다
바닥단정 = ('모래 바닥', '모래바닥', '진흙 바닥', '진흙바닥',
            '자갈 바닥', '암반 바닥')


def 그림들(글):
    """`<svg>…</svg>` 를 통째로 꺼냅니다."""
    return re.findall(r'<svg\b.*?</svg>', 글, re.S)


def 사진깔렸나(그림):
    """그 그림 안에 **사진이 바탕으로 깔려 있는가**."""
    if re.search(r'<image\b', 그림):
        return True
    if re.search(r'url\(["\']?[^)"\']+\.(?:jpg|jpeg|png|webp)', 그림, re.I):
        return True
    return False


def main():
    엄격 = '--strict' in sys.argv
    본쪽 = 0
    # ★ 쪽을 하나도 못 읽어도 「덧그림 0」이라 통과였습니다 (2026-10-08)
    mustmeasure.있어야한다(list(io.쪽들(NEW)), '쪽', 최소=50, 어디=NEW)
    읽은쪽 = 0
    본그림 = 0
    사진깔린그림 = 0

    for 길 in io.쪽들(NEW):
        짧 = os.path.relpath(길, NEW).replace(os.sep, '/')
        try:
            글 = _io.open(길, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        읽은쪽 += 1
        것들 = 그림들(글)
        if not 것들:
            continue
        본쪽 += 1
        for 그림 in 것들:
            본그림 += 1
            if not 사진깔렸나(그림):
                continue        # B — 사진과 떨어진 일반 도해입니다
            사진깔린그림 += 1

            # ── 사진이 깔린 그림 **안**에 자리를 주장하는 것이 있는가
            걸린말 = [m for m in 자리주장 if m in 그림]
            걸린바닥 = [m for m in 바닥단정 if m in 그림]
            # 점·선·화살표 — 사진 위에 올린 도형
            도형수 = len(re.findall(
                r'<(?:circle|path|line|polygon|polyline|rect)\b', 그림))
            # 사진을 담는 <image> 자체는 빼고 셉니다
            if 걸린말 or 걸린바닥:
                막음.append(
                    '%s — 사진 위에 「%s」를 얹었습니다'
                    % (짧, ', '.join((걸린말 + 걸린바닥)[:3])))
            elif 도형수 >= 3:
                알림.append(
                    '%s — 사진 위에 도형 %d개가 얹혀 있습니다'
                    % (짧, 도형수))

    # ★ 목록은 있는데 **내용을 하나도 못 읽으면** 못잼입니다
    mustmeasure.있어야한다(range(읽은쪽), '읽은 쪽', 최소=50, 어디=NEW)

    print()
    print('  사진 위에 임의로 얹은 위치 표시가 없는가')
    print()
    print('  그림 있는 쪽 %d개 · 그림 %d개 · 그 가운데 사진이 깔린 것 %d개'
          % (본쪽, 본그림, 사진깔린그림))
    if not 본그림:
        print()
        print('  □ 그림을 하나도 못 찾았습니다 — 못 쟀습니다')
        return 4 if 엄격 else 0

    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        if len(막음) > 12:
            print('  … 그 밖 %d가지' % (len(막음) - 12))
        print()
        print('  **사진의 그 자리를 자료로 입증할 수 없으면 얹지')
        print('  않습니다.** 설명은 사진과 떨어진 일반 도해로 합니다.')
        print('  (engine/art.py 의 `사진위에얹을까` 를 보세요)')
        return 1
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:6]:
            print('  ! %s' % t)
    print('  · 사진 위에 자리를 주장하는 표시가 없습니다')
    print('  · 글에 적힌 「모래 바닥」 같은 설명은 자료에서 온 사실이라')
    print('    그대로 둡니다 — 그림으로 **가리키는 것**만 막습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
