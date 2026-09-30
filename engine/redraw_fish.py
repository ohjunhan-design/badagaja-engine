# -*- coding: utf-8 -*-
"""어종 그림 속 물고기를 **사실적인 모양으로 갈아 끼웁니다.**

★ 2026-09-30 주인 지적 — 「이런것들도 좀 사실적으로 그려
                          이건 유치원생 그림같잖아」

  `data/raw/lessons.json` 의 그림 141장 가운데 **60장**에 물고기가
  있는데, 모두 **뾰족한 타원 + 삼각 꼬리 + 반달 선** 이었습니다.
  입도 아가미도 가슴지느러미도 없었습니다.

무엇을 하나
    물고기 한 마리는 `<g transform="translate(…) scale(…)">` 덩이입니다.
    그 안에서 **크기(a·b)와 색**을 읽어, `_fish_shape.물고기()` 가
    그리는 새 모양으로 **덩이 속을 통째로** 갈아 끼웁니다.
    자리(translate)와 크기(scale)는 **손대지 않습니다** —
    그래야 다른 요소와 어긋나지 않습니다.

★ **먼저 보여 주고, --write 를 붙여야 씁니다** (계약-19)
★ **두 번 돌려도 결과가 같아야 합니다** (계약-26).
  이미 바꾼 덩이는 옛 몸통 무늬가 없으니 저절로 건너뜁니다.

쓰는 법
    python engine/redraw_fish.py            # 몇 마리인지 보여만 줍니다
    python engine/redraw_fish.py --write    # 정말 바꿉니다
"""
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)
sys.path.insert(0, ROOT)

from engine import io                        # noqa: E402
from engine._fish_shape import 물고기          # noqa: E402

자료길 = os.path.join(ROOT, 'data', 'raw', 'lessons.json')

# 물고기 한 마리 = translate 로 옮긴 덩이
덩이무늬 = re.compile(
    r'<g transform="translate\([^)]*\)(?:\s*scale\([^)]*\))?">'
    r'((?:(?!</g>).)*?)</g>', re.S)

# 옛 몸통 — M-{a} 0 q.. -{b} … z 꼴
몸통무늬 = re.compile(r'<path d="M-([\d.]+) 0 q[\d.]+ -([\d.]+)[^"]*z"'
                      r'\s+fill="(#[0-9A-Fa-f]{6})"')
# 옛 꼬리 — 몸통 바로 뒤의 삼각
꼬리무늬 = re.compile(r'<path d="M-[\d.]+ 0 l-[\d.]+ -[\d.]+[^"]*z"'
                      r'\s+fill="(#[0-9A-Fa-f]{6})"')


def 바꾼덩이(속):
    """덩이 속을 새 물고기로 바꿉니다. 물고기가 아니면 None."""
    m = 몸통무늬.search(속)
    if not m:
        return None
    a = float(m.group(1))
    b = float(m.group(2))
    몸색 = m.group(3)
    꼬 = 꼬리무늬.search(속)
    짙은색 = 꼬.group(1) if 꼬 else 몸색
    # 눈 색은 마지막 circle 에서 (있으면)
    눈 = re.findall(r'<circle[^>]*fill="(#[0-9A-Fa-f]{3,6})"', 속)
    눈색 = 눈[-1] if 눈 else '#223036'
    return 물고기(a, b, 몸색, 짙은색, 눈색=눈색)


def main():
    쓸까 = '--write' in sys.argv
    d = io.read_json(자료길, default={})
    차례 = d.get('차례') or {}
    if not 차례:
        print('배우는 차례 자료가 없습니다.')
        return 1

    바꾼수 = 0
    바꾼그림 = []
    for 어종 in sorted(차례):
        for n, 단 in enumerate(차례[어종], 1):
            g = 단.get('그림') or ''
            if not g:
                continue
            이그림 = 0

            def 한덩이(m):
                nonlocal 이그림
                새속 = 바꾼덩이(m.group(1))
                if 새속 is None:
                    return m.group(0)
                이그림 += 1
                머리 = m.group(0)[:m.group(0).index('>') + 1]
                return 머리 + 새속 + '</g>'

            새g = 덩이무늬.sub(한덩이, g)
            if 이그림:
                바꾼수 += 이그림
                바꾼그림.append((어종, n, 이그림))
                단['그림'] = 새g

    print('물고기를 사실적인 모양으로 갈아 끼웁니다')
    print('  그림 %d장 · 물고기 %d마리' % (len(바꾼그림), 바꾼수))
    for 어종, n, c in 바꾼그림[:10]:
        print('      %-12s %d단계  %d마리' % (어종, n, c))
    if len(바꾼그림) > 10:
        print('      … 그 밖 %d장' % (len(바꾼그림) - 10))
    print('')

    if not 바꾼수:
        print('바꿀 물고기가 없습니다 — 이미 다 바꿨습니다.')
        return 0
    if not 쓰기허락(쓸까):
        return 0

    # ★ `io.write_json` 은 **열쇠를 정렬**합니다 (계약-07).
    #   lessons.json 은 사람이 쓴 자료라 차례에 뜻이 있어,
    #   정렬하면 파일이 통째로 뒤집혀 무엇이 바뀌었는지 못 봅니다.
    #   그래서 차례를 지킨 채 씁니다. 쓰기는 io 를 거칩니다 (계약-13).
    io.write(자료길,
             json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    print('  ✓ data/raw/lessons.json 에 썼습니다.')
    print('    build.py 를 돌려 쪽에 반영하세요.')
    return 0


def 쓰기허락(쓸까):
    if 쓸까:
        return True
    print('  보여만 드렸습니다. 정말 바꾸려면 --write 를 붙이세요.')
    return False


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
