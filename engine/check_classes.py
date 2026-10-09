# -*- coding: utf-8 -*-
"""**쪽이 쓰는 클래스가 차림표에 정말 있는가** (2026-10-09)

★ 왜 이 검사가 있나

    동호회 지원 쪽을 만들며 `class="btn btn--primary"` 라고 썼습니다.
    그런 클래스는 **이 사이트에 없습니다.** 있는 것은 `btn--dark`·
    `btn--white` 입니다.

    브라우저는 아무 말도 하지 않습니다. 그냥 **그 줄을 버립니다.**
    그래서 단추가 바탕도 없이 글자만 남아 링크처럼 보였습니다.
    화면을 눈으로 보지 않았으면 그대로 올라갔을 것입니다.

    같은 일을 전에도 겪었습니다 — 없는 CSS 색 이름을 썼더니
    그 줄이 조용히 버려져 단추가 안 보였습니다.

무엇을 재나 — **수식어 클래스만** 봅니다 (`--` 가 든 이름)

    처음에는 모든 클래스를 봤습니다. 그랬더니 `.hm-left`·`.fn-col`
    처럼 **규칙이 없어도 정상인 것**이 잔뜩 걸렸습니다 —
    그리드 칸을 가리키기만 하는 이름은 전용 규칙이 없어도 됩니다.
    거짓이 많은 검사기는 아무도 안 봅니다.

    그래서 처음에는 `btn--primary` 처럼 **`--` 가 든 수식어**만
    봤습니다. 수식어는 「바탕 클래스를 이렇게 바꿔라」는 뜻이라
    규칙이 없으면 쓰나 마나입니다.

    ★ **그 좁힘이 큰 것을 놓쳤습니다** (2026-10-09)

      방문 기록 쪽(stats.html)의 차림표가 **통째로 없었습니다.**
      `.st-chart` · `.st-table` · `.st-top` · `.st-key` 등 아홉
      가지가 쪽에는 쓰이는데 규칙이 하나도 없어, 카드가 맨 글줄로
      나오고 막대 자리는 빈 테두리였습니다. 열흘 가까이 그랬는데
      이 검사기는 **수식어가 아니라서 쳐다보지도 않았습니다.**

      그래서 **모든 클래스**를 봅니다. 대신 지금 있는 것은
      기준선에 담아 두고 **새로 생기는 것만** 막습니다.
      (기억: 못 가리면 보여 드립니다 — 기계가 좁히고 사람이 확인)

    ★ 기준선에 든 28가지는 손으로 확인했습니다 — `fn-col`(꼬리
      칸) · `filters`(`.filters--fish` 로 꾸밈) 처럼 **묶음 이름만
      하는 것들**이라 전용 규칙이 없어도 정상입니다.

쓰는 법
    python engine/check_classes.py
    python engine/check_classes.py --받아들이기
"""
import io
import os
import re
import sys
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
CSS = os.path.join(ROOT, 'assets', 'css')
기준길 = os.path.join(ROOT, 'tests', 'golden', '없는클래스.json')

_클래스적힘 = re.compile(r'class="([^"]*)"')
_주석 = re.compile(r'/\*.*?\*/', re.S)
_차림표이름 = re.compile(r'\.(-?[_a-zA-Z][\w-]*)')


def 차림표이름들():
    """차림표에 규칙이 있는 클래스 이름을 모두 모읍니다"""
    있음 = set()
    for p in sorted(glob.glob(os.path.join(CSS, '*.css'))):
        s = _주석.sub(' ', io.open(p, encoding='utf-8').read())
        # 중괄호 앞(고르개)만 봅니다 — 값에 든 점은 빼려고
        for 고르개 in re.findall(r'([^{}]+)\{', s):
            if '@' in 고르개:
                continue
            for 이름 in _차림표이름.findall(고르개):
                있음.add(이름)
    return 있음


def 쪽이쓰는이름(길):
    s = io.open(길, encoding='utf-8').read()
    나옴 = set()
    for m in _클래스적힘.finditer(s):
        for 이름 in m.group(1).split():
            if 이름:
                나옴.add(이름)
    return 나옴


def 쪽들():
    것 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    return [p for p in 것 if os.path.basename(p) != '404.html']


def 재기():
    있음 = 차림표이름들()
    없는것 = {}
    for p in 쪽들():
        이름 = os.path.relpath(p, NEW).replace('\\', '/')
        빠진 = sorted(x for x in 쪽이쓰는이름(p) if x not in 있음)
        for x in 빠진:
            없는것.setdefault(x, []).append(이름)
    return 없는것


_안적음 = '(아직 안 적음)'

# ★ **생성이 잘못된 꼴** — 기준선에 있어도 막습니다 (총감독 ⑥)
#   `class="p-"` 처럼 자리값이 비어 **이름이 잘린** 것입니다.
#   「규칙이 없어도 정상」이 아니라 **만드는 쪽이 틀린 것**이라
#   예외로 둘 수 없습니다.
_잘린꼴 = re.compile(r'(^-)|(-$)|(--$)')


def 잘린이름인가(이름):
    """`p-` · `-foo` 처럼 끝이 잘려 나온 이름인가"""
    return bool(_잘린꼴.search(이름))


def _까닭있나(값):
    """기준선 한 줄에 **왜 규칙이 없어도 되는지**가 적혔나"""
    if not isinstance(값, dict):
        return False                      # 옛 꼴(숫자만) 은 까닭 없음
    까 = (값.get('까닭') or '').strip()
    return bool(까) and 까 != _안적음


def main():
    받아 = '--받아들이기' in sys.argv
    것들 = 쪽들()
    if not 것들:
        print('✗ 쪽이 없습니다 — 먼저 build 를 돌리세요')
        return 4                  # 못잼 (계약)
    있음 = 차림표이름들()
    if not 있음:
        print('✗ 차림표를 못 읽었습니다')
        return 4

    이번 = 재기()

    기준속 = {}
    if os.path.exists(기준길):
        기준속 = json.load(io.open(기준길, encoding='utf-8')) or {}
    기준 = 기준속.get('이름', {})

    if 받아:
        # ★ **기준선을 혼자 늘리지 않습니다** (총감독 2026-10-10)
        #   「baseline 을 새로 추가하려면 사람이 『왜 CSS 규칙 없어도
        #     정상인지』 확인」. 이미 있는 것의 쪽 수만 고칩니다.
        늘릴것 = sorted(k for k in 이번 if k not in 기준)
        if 늘릴것 and '--정말' not in sys.argv:
            print('✗ 기준선에 **새 이름을 혼자 더하지 않습니다** — %d가지'
                  % len(늘릴것))
            for k in 늘릴것[:10]:
                print('      %-24s %d쪽' % (k, len(이번[k])))
            print()
            print('  왜 규칙이 없어도 정상인지 **사람이 확인**한 뒤')
            print('  tests/golden/없는클래스.json 에 이름과 **까닭**을')
            print('  손으로 적으세요. 쪽 수만 고치려면 그대로 돌립니다.')
            return 1
        남길 = {}
        for k in sorted(이번):
            옛값 = 기준.get(k)
            까닭 = 옛값.get('까닭') if isinstance(옛값, dict) else None
            남길[k] = {'쪽': len(이번[k]), '까닭': 까닭 or _안적음}
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        # ★ `newline=''` 를 안 주면 윈도에서 **CRLF** 로 써집니다.
        #   저장소는 LF 라 돌릴 때마다 파일이 달라집니다(계약-07).
        io.open(기준길, 'w', encoding='utf-8',
                newline=chr(10)).write(
            json.dumps({'_왜': '차림표에 규칙이 없어도 **정상인** 클래스. '
                               '사람이 하나씩 확인해 까닭을 적었습니다. '
                               '여기 없는 이름이 새로 생기면 막습니다',
                        '_규칙': '총감독 2026-10-10 — 새 이름은 무조건 '
                                 '막습니다. 여기 더하려면 사람이 왜 규칙이 '
                                 '없어도 정상인지 확인하고 까닭을 적습니다. '
                                 'p- 처럼 생성이 잘못된 꼴은 등록 금지',
                        '이름': 남길},
                       ensure_ascii=False, indent=1) + '\n')
        print('기준선을 깔았습니다 — 이름 %d가지' % len(이번))
        return 0

    # ⑥ 잘린 이름은 **기준선에 있어도** 새것으로 셉니다
    새것 = {k: v for k, v in 이번.items()
            if k not in 기준 or 잘린이름인가(k)}

    print('차림표에 없는 클래스 — 쪽 %d개 · 차림표 이름 %d가지'
          % (len(것들), len(있음)))
    print('  · 알고 두는 것 %d가지' % len(기준))

    # ④ **쓰임없음 알림** — 쪽에서 사라진 이름이 기준선에 남으면,
    #    다음에 같은 이름이 다시 생겨도 조용히 지나갑니다.
    안쓰임 = sorted(k for k in 기준 if k not in 이번)
    if 안쓰임:
        print('  ! 기준선에 있는데 **쪽에서 사라진 이름** %d가지 — 빼세요'
              % len(안쓰임))
        for k in 안쓰임[:8]:
            print('      %s' % k)

    # ③ 까닭이 안 적힌 것을 알립니다 (막지는 않습니다)
    빈까닭 = sorted(k for k, v in 기준.items() if not _까닭있나(v))
    if 빈까닭:
        print('  ! **까닭이 안 적힌 것** %d가지 — 왜 규칙이 없어도 되는지'
              ' 적으세요' % len(빈까닭))
        for k in 빈까닭[:8]:
            print('      %s' % k)

    if not 새것:
        print('  ✓ 새로 생긴 것 0')
        return 0

    print('  ✗ 새로 생긴 것 %d가지' % len(새것))
    for 이름 in sorted(새것)[:16]:
        쪽 = 새것[이름]
        print('      .%-26s %d쪽 (%s)'
              % (이름, len(쪽), ', '.join(쪽[:2])))
    print('  → 차림표에 규칙이 없으면 그 줄은 **조용히 버려집니다.**')
    print('    이름을 새로 지었으면 assets/css 에 규칙도 함께 넣으세요.')
    return 1                      # 어김 (계약)


if __name__ == '__main__':
    sys.exit(main())
