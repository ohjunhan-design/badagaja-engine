# -*- coding: utf-8 -*-
"""**한 이름을 서로 다른 뜻으로 두 번 정하지 않았는가** (2026-10-08)

★ 왜 이 검사가 있나 — 오늘 사이트가 망가진 까닭입니다

    `.rig-zoom` 은 **「크게 보는 칸」**이었습니다. 평소에는
    `display:none` 이고 `:target` 일 때만 펴지는 덮개입니다.

        .rig-zoom{display:none}                     ← 1169줄

    그런데 어종 쪽에 「크게 보기」 **단추**를 만들며 같은 이름을
    썼습니다. 그 규칙이 차림표 **뒤**에 있었습니다.

        .rig-zoom{position:absolute; ...}           ← 4881줄

    **뒤가 이깁니다.** `display:none` 이 덮여, 1372×980 짜리 확대
    그림이 **채비 16쪽 전부에서 늘 펼쳐져** 본문을 가렸습니다.
    CSS 는 오류를 내지 않습니다. 쪽을 눈으로 보기 전에는 모릅니다.

    바깥 검수도 같은 곳을 짚었습니다 —
      「.rig-* { position: absolute; } … 이 중 하나가 있으면
        거의 원인입니다」

무엇을 보나

    한 클래스 이름이 **서로 다른 블록**에서 `display` 나 `position`
    을 **다르게** 정하면 알립니다. 그 둘은 거의 언제나 **다른 것**을
    가리키려던 이름입니다.

    ★ **거짓 양성이 많은 검사는 두지 않습니다.** 그래서
      · 미디어쿼리 안의 재정의는 **봐 줍니다** (일부러 바꾸는 자리)
      · `:hover` · `:target` 같은 **상태**가 붙은 것도 봐 줍니다
      · 그러고도 남는 것은 기준선에 쌓아 두고 **새로 느는 것만** 막습니다

끝난값
    0 통과 · 1 어김(새로 생김) · 4 못잼
"""
import io
import os
import re
import sys
import json
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402

차림표터 = os.environ.get('BADAGAJA_CSS',
                           os.path.join(ROOT, 'assets', 'css'))
기준길 = os.path.join(ROOT, 'tests', 'golden', '차림표이름겹침.json')

# 이것이 다르면 **다른 것을 가리키려던 이름**입니다
볼것 = ('display', 'position')

_주석 = re.compile(r'/\*.*?\*/', re.S)
_블록 = re.compile(r'([^{}]+)\{([^{}]*)\}')


def 읽기(길):
    return io.open(길, encoding='utf-8', errors='replace').read()


def 블록들(글):
    """(고르개, 속, 미디어쿼리안인가) 를 냅니다.

    미디어쿼리는 **일부러 다시 정하는 자리**라 따로 셉니다.
    """
    글 = _주석.sub(' ', 글)
    난것 = []
    깊이 = 0
    미디어 = 0
    i = 0
    쌓임 = ''
    while i < len(글):
        c = 글[i]
        if c == '{':
            고르개 = 쌓임.strip()
            쌓임 = ''
            if 고르개.startswith('@'):
                깊이 += 1
                if 고르개.startswith('@media') or 고르개.startswith('@supports'):
                    미디어 += 1
                i += 1
                continue
            # 평범한 규칙 — 닫는 괄호까지
            j = 글.find('}', i)
            if j < 0:
                break
            난것.append((고르개, 글[i + 1:j], 미디어 > 0))
            i = j + 1
            continue
        if c == '}':
            if 깊이 > 0:
                깊이 -= 1
                if 미디어 > 0:
                    미디어 -= 1
            쌓임 = ''
            i += 1
            continue
        쌓임 += c
        i += 1
    return 난것


_이름 = re.compile(r'\.([A-Za-z_][\w-]*)')


def 홀로된이름(고르개):
    """**상태·자손이 붙지 않은** 클래스 하나만 냅니다.

    `.rig-zoom` → 'rig-zoom'
    `.rig-zoom:target` · `.rig-zoom img` · `.a .b` → 없음
    상태나 자손이 붙으면 **일부러 다르게 정하는 자리**입니다.
    """
    한쪽 = 고르개.split(',')
    난것 = []
    for 쪽 in 한쪽:
        쪽 = 쪽.strip()
        if not 쪽 or ' ' in 쪽 or '>' in 쪽 or '+' in 쪽 or '~' in 쪽:
            continue
        if ':' in 쪽 or '[' in 쪽 or '#' in 쪽:
            continue
        m = _이름.fullmatch(쪽)
        if m:
            난것.append(m.group(1))
    return 난것


def 값뽑기(속):
    난것 = {}
    for 줄 in 속.split(';'):
        if ':' not in 줄:
            continue
        키, 값 = 줄.split(':', 1)
        키 = 키.strip().lower()
        if 키 in 볼것:
            난것[키] = 값.strip().lower().split('!')[0].strip()
    return 난것


def main():
    받아들이기 = '--받아들이기' in sys.argv
    print()
    print('  한 이름을 서로 다른 뜻으로 두 번 정하지 않았는가')
    print('  (2026-10-08 — `.rig-zoom` 이 겹쳐 채비 16쪽이 가려졌습니다)')
    print()

    길들 = sorted(glob.glob(os.path.join(차림표터, '*.css')))
    mustmeasure.있어야한다(길들, '차림표', 최소=1, 어디=차림표터)

    표 = {}
    본블록 = 0
    for p in 길들:
        짧 = os.path.basename(p)
        for 고르개, 속, 미디어안 in 블록들(읽기(p)):
            본블록 += 1
            if 미디어안:
                continue                 # 일부러 다시 정하는 자리
            값 = 값뽑기(속)
            if not 값:
                continue
            for 이름 in 홀로된이름(고르개):
                표.setdefault(이름, []).append((짧, 값))

    mustmeasure.있어야한다(range(본블록), '차림표 블록', 최소=50, 어디=차림표터)

    # ★ **막을 것과 알릴 것을 나눕니다** (계약-21)
    #   막음 — `display`/`position` 이 서로 어긋나는 곳. 숨겨 둔 것이
    #          펼쳐지거나 자리가 어긋나 **화면이 망가집니다.**
    #   알림 — 같은 이름을 여러 곳에서 정하지만 값은 같은 곳.
    #          당장 탈은 없지만 한 곳에 모으는 편이 낫습니다.
    막음, 알림 = [], []
    탈 = 막음
    for 이름, 것들 in sorted(표.items()):
        if len(것들) < 2:
            continue
        같은값 = []
        for 키 in 볼것:
            값들 = set(v[키] for _, v in 것들 if 키 in v)
            if len(값들) >= 2:
                막음.append('%s — `%s` 를 %s 로 서로 다르게 정합니다 (%s)'
                            % (이름, 키, ' / '.join(sorted(값들)),
                               ' · '.join(sorted(set(f for f, _ in 것들)))))
            elif len(값들) == 1 and sum(1 for _, v in 것들 if 키 in v) >= 2:
                같은값.append(키)
        if 같은값 and len(것들) >= 3:
            알림.append('%s — `%s` 를 %d곳에서 거듭 정합니다 (값은 같습니다)'
                        % (이름, '·'.join(같은값), len(것들)))

    기준 = {}
    try:
        기준 = json.loads(읽기(기준길))
    except Exception:                                 # noqa: BLE001
        기준 = {}
    알던것 = set(기준.get('알던것') or [])

    print('  차림표 %d장 · 블록 %d개를 봤습니다' % (len(길들), 본블록))
    print()

    if 받아들이기:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        io.open(기준길, 'w', encoding='utf-8').write(json.dumps({
            '_무엇인가': ('한 클래스 이름을 서로 다른 뜻으로 두 번 정한 곳의 '
                          '기준선입니다. 여기 있는 것은 **새로 생긴 것이 '
                          '아니라는 뜻**일 뿐, 괜찮다는 뜻이 아닙니다.'),
            '_겪은일': ('2026-10-08 — `.rig-zoom` 이 「크게 보는 칸」과 '
                        '「크게 보기 단추」 둘을 가리켜, 뒤쪽 규칙이 '
                        '`display:none` 을 덮었습니다. 1372×980 확대 그림이 '
                        '채비 16쪽에서 늘 펼쳐져 본문을 가렸습니다.'),
            '_어떻게줄이나': '이름을 가른 뒤 여기서 그 줄을 지웁니다.',
            '알던것': sorted(막음),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(막음), os.path.relpath(기준길, ROOT)))
        return 0

    새것 = [t for t in 막음 if t not in 알던것]
    고쳐진것 = 알던것 - set(막음)
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:5]:
            print('  ~ %s' % t)
        print()
    if 고쳐진것:
        print('  · 고쳐진 곳 %d곳 — `--받아들이기` 로 기준을 조이세요'
              % len(고쳐진것))
        print()
    if 새것:
        print('  손볼 곳 %d가지' % len(새것))
        for t in 새것[:12]:
            print('  ✗ %s' % t)
        print()
        print('  **차림표 맨 뒤가 이깁니다.** 뒤에 적은 규칙이 앞의')
        print('  `display:none` 을 덮으면, 숨겨 두었던 것이 늘 펼쳐집니다.')
        print('  폭을 막지 말고 **이름을 가르세요.**')
        return 1

    print('  · 같은 이름을 다른 뜻으로 쓰는 곳이 새로 생기지 않았습니다'
          ' (쌓인 것 %d곳)' % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
