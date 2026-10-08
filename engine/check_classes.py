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

    그래서 `btn--primary` 처럼 **`--` 가 든 수식어**만 봅니다.
    수식어는 **「바탕 클래스를 이렇게 바꿔라」는 뜻**이라, 규칙이
    없으면 바꿀 것이 없습니다 — 쓰나 마나입니다. 100% 잘못입니다.

    ★ 자바스크립트가 붙였다 뗐다 하는 수식어가 있어 **기준선**을
      두고 **새로 느는 것만** 막습니다.

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
        빠진 = sorted(x for x in 쪽이쓰는이름(p)
                      if '--' in x and x not in 있음)
        for x in 빠진:
            없는것.setdefault(x, []).append(이름)
    return 없는것


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

    if 받아:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        io.open(기준길, 'w', encoding='utf-8').write(
            json.dumps({'_왜': '차림표에 규칙이 없는 클래스. 자바스크립트가 '
                               '붙이는 것이라 알고 둡니다. 여기 없는 이름이 '
                               '새로 생기면 막습니다',
                        '이름': dict((k, len(v))
                                     for k, v in sorted(이번.items()))},
                       ensure_ascii=False, indent=1) + '\n')
        print('기준선을 깔았습니다 — 이름 %d가지' % len(이번))
        return 0

    기준 = {}
    if os.path.exists(기준길):
        기준 = (json.load(io.open(기준길, encoding='utf-8')) or {}).get('이름', {})

    새것 = {k: v for k, v in 이번.items() if k not in 기준}

    print('차림표에 없는 클래스 — 쪽 %d개 · 차림표 이름 %d가지'
          % (len(것들), len(있음)))
    print('  · 알고 두는 것 %d가지' % len(기준))
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
