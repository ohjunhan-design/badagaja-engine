# -*- coding: utf-8 -*-
"""그림이 **어느 쪽에 쓰이는지** 훑습니다 (2026-10-15 감독실 요청).

  ★ **읽기만 합니다.** 그림도 쪽도 고치지 않습니다.

  내는 것
    갈래마다 — 몇 장 · 어느 쪽이 쓰나 · 가장 작은 것 ·
    쓰이지 않는 것 · 쪽이 부르는데 **없는 것**

  ★ 「최소 해상도」는 **쓰임에 따라 다릅니다.**
    공유 미리보기(og:image)는 네이버·구글 가이드가 150×150 보다
    크고 가로세로 3:1 을 넘지 말라 합니다(주인 규칙 28).
    쪽 안의 그림은 그보다 작아도 되는 자리가 있습니다.
    그래서 **한 줄로 자르지 않고 쓰임을 갈라** 적습니다.

쓰는 법
    python -m engine.map_images            # 요약
    python -m engine.map_images --자세히    # 갈래마다 낱낱이
    python -m engine.map_images --갈래 rig  # 한 갈래만
"""
import argparse
import collections
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
그림칸 = os.path.join(ROOT, 'site', 'img')
쪽칸 = os.path.join(ROOT, 'site')

# og:image 는 가이드가 정한 값이 있습니다 (주인 규칙 28)
OG최소 = 150
OG가로세로상한 = 3.0


def 크기재기(길):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(길) as im:
            return im.size
    except Exception:
        return None


def 그림모으기():
    """site/img 아래 그림을 갈래별로 모읍니다."""
    것 = collections.defaultdict(list)
    for 뿌리, _, 파일들 in os.walk(그림칸):
        갈래 = os.path.relpath(뿌리, 그림칸).replace(os.sep, '/')
        if 갈래 == '.':
            갈래 = '(뿌리)'
        for n in 파일들:
            if not n.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif')):
                continue
            길 = os.path.join(뿌리, n)
            것[갈래].append({
                '이름': n,
                '길': 길,
                '주소': 'img/%s/%s' % (갈래, n) if 갈래 != '(뿌리)'
                        else 'img/%s' % n,
                '바이트': os.path.getsize(길),
                '크기': 크기재기(길),
            })
    return 것


def 쪽훑기():
    """쪽이 부르는 그림 주소를 모읍니다. 돌려주는 것: 주소 → 쪽 목록."""
    부름 = collections.defaultdict(set)
    쪽수 = 0
    for 뿌리, _, 파일들 in os.walk(쪽칸):
        for n in 파일들:
            if not n.endswith('.html'):
                continue
            쪽수 += 1
            길 = os.path.join(뿌리, n)
            쪽이름 = os.path.relpath(길, 쪽칸).replace(os.sep, '/')
            try:
                글 = io.open(길, encoding='utf-8').read()
            except Exception:
                continue
            # src · href · content(og:image) · url() 안의 img/…
            for m in re.finditer(r'(?:\.\./)*((?:img|assets/img)/[^"\'\)\s]+)',
                                 글):
                주소 = m.group(1).split('?')[0]
                부름[주소].add(쪽이름)
    return 부름, 쪽수


def og그림(쪽글):
    m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"',
                  쪽글)
    return m.group(1) if m else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--자세히', action='store_true')
    p.add_argument('--갈래', default='')
    a = p.parse_args()

    것 = 그림모으기()
    부름, 쪽수 = 쪽훑기()

    print('그림이 어느 쪽에 쓰이는가 — 읽기만 했습니다')
    print('=' * 72)
    모두 = sum(len(v) for v in 것.values())
    print('  그림 %d장 · 갈래 %d가지 · 쪽 %d장을 훑었습니다'
          % (모두, len(것), 쪽수))
    if 모두 and 것 and not any(x['크기'] for v in 것.values() for x in v):
        print('  ★ 크기를 못 쟀습니다 (Pillow 없음) — 숫자를 믿지 마십시오')
    print()

    머리 = ('%-18s %5s %7s %-14s %-12s %s'
            % ('갈래', '장수', '합계MB', '가장 작은 것', '쓰는 쪽', '안 쓰임'))
    print(머리)
    print('-' * 72)
    안쓰임모두 = []
    for 갈래 in sorted(것):
        if a.갈래 and a.갈래 != 갈래:
            continue
        목록 = 것[갈래]
        바이트 = sum(x['바이트'] for x in 목록)
        크기있 = [x for x in 목록 if x['크기']]
        가장작은 = min(크기있, key=lambda x: x['크기'][0] * x['크기'][1]) \
            if 크기있 else None
        쓰는쪽 = set()
        안쓰임 = []
        for x in 목록:
            곳 = 부름.get(x['주소']) or set()
            if not 곳:
                # assets/img 로도 불릴 수 있습니다
                곳 = 부름.get('assets/' + x['주소']) or set()
            if 곳:
                쓰는쪽 |= 곳
            else:
                안쓰임.append(x['이름'])
        안쓰임모두 += [(갈래, n) for n in 안쓰임]
        print('%-18s %5d %7.1f %-14s %-12s %s'
              % (갈래, len(목록), 바이트 / 1048576.0,
                 ('%dx%d' % 가장작은['크기']) if 가장작은 else '?',
                 '%d쪽' % len(쓰는쪽),
                 ('%d장' % len(안쓰임)) if 안쓰임 else '-'))
        if a.자세히:
            for x in sorted(목록, key=lambda y: y['이름'])[:40]:
                곳 = 부름.get(x['주소']) or \
                     부름.get('assets/' + x['주소']) or set()
                print('      %-28s %-11s %7.0fKB  %s'
                      % (x['이름'],
                         ('%dx%d' % x['크기']) if x['크기'] else '?',
                         x['바이트'] / 1024.0,
                         ('%d쪽' % len(곳)) if 곳 else '★ 안 쓰임'))

    # 쪽이 부르는데 **없는 것**
    있는주소 = {x['주소'] for v in 것.values() for x in v}
    없는것 = []
    for 주소, 쪽들 in 부름.items():
        깔끔 = 주소[len('assets/'):] if 주소.startswith('assets/') else 주소
        if 깔끔 not in 있는주소 and 주소 not in 있는주소:
            없는것.append((주소, len(쪽들)))
    print()
    if 없는것:
        print('  ✗ 쪽이 부르는데 **파일이 없는 것** %d가지' % len(없는것))
        for 주소, n in sorted(없는것, key=lambda x: -x[1])[:8]:
            print('      %-46s %d쪽' % (주소[:46], n))
    else:
        print('  · 쪽이 부르는 그림은 **모두 있습니다**')

    if 안쓰임모두:
        print('  ~ 어느 쪽도 안 쓰는 그림 %d장' % len(안쓰임모두))
        갈래별 = collections.Counter(g for g, _ in 안쓰임모두)
        for g, n in 갈래별.most_common(6):
            print('      %-20s %d장' % (g, n))

    print('-' * 72)
    print('[한 줄 요약] 그림 %d장 · 갈래 %d · 없는 것 %d · 안 쓰임 %d'
          % (모두, len(것), len(없는것), len(안쓰임모두)))
    return 1 if 없는것 else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
