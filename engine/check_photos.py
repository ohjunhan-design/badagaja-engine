# -*- coding: utf-8 -*-
"""쪽마다 **보이는 것**이 있는지 봅니다. (주인 규칙 6-1)

★ 왜 생겼나 (2026-09-27)

    새 틀로 만든 416쪽에 **사진이 한 장도 없었습니다.**
    옛 사이트는 500장을 씁니다.

    그런데 판정 20개가 전부 PASS 였습니다. 어디에도
    「사진이 있는가」를 묻는 검사가 없었기 때문입니다.
    검사가 없으면 없는 것도 통과합니다.

    게다가 `build.py` 가 대표 사진 주소를 **자료를 안 보고
    지어내고** 있었습니다.

        지어낸 것   img/taean/hero.jpg        ← 없는 파일
        실제 파일   img/coast/taean-hero.jpg

    57권역 가운데 15곳만 맞았습니다. 공유 미리보기(og:image)가
    52갈래 깨진 채였습니다. 카톡·네이버로 나눠도 그림이 안 떴을
    것입니다.

무엇을 보나
    [1] 쪽마다 보이는 것이 있는가          (규칙 6-1)
    [2] 가리키는 그림 파일이 진짜 있는가    (지어낸 주소를 잡습니다)
    [3] 촬영자가 적혀 있는가               (규칙 5)
    [4] 설명에 이용허락 종류를 안 적었는가  (규칙 6)
    [5] og:image 가 가이드를 지키는가       (규칙 28)
    [6] 사진과 그림을 구별해 적었는가       (규칙 5)

쓰는 법
    python engine/check_photos.py
    python engine/check_photos.py --strict
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []

# 쪽에 적으면 안 되는 말 — 이용허락 종류는 photos.html 에만 (규칙 6)
이용허락말 = re.compile(r'공공누리|CC BY|CC0|Public domain', re.I)


def 쪽들():
    return sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))


def 자료사진들():
    """`data/raw/photos.json` 이 적은 사진 목록. 못 읽으면 빈 것."""
    d = io.read_json(os.path.join(DATA, 'raw', 'photos.json'), default={})
    if isinstance(d, list):
        return d
    for 열쇠 in ('사진', 'photos', 'items'):
        if isinstance(d.get(열쇠), list):
            return d[열쇠]
    return []


def main():
    것들 = 쪽들()
    if not 것들:
        print('잴 것이 없습니다 — site/ 에 쪽이 없습니다.')
        return 0

    print('쪽마다 보이는 것이 있는가 (주인 규칙 6-1)')
    print('  쪽 %d개' % len(것들))
    print('')

    # ── 0. 자료에 같은 사진이 두 번 적혀 있는가
    #
    #   ★ 2026-09-28 — 바깥 검수가 숫자를 의심해 찾아냈습니다
    #
    #     검수서에 「사진 264장」이라 적었는데 저장소에는 263장뿐이었습니다.
    #     바깥 검수가 **「숫자의 정의가 불명확한 것 자체가 위험 신호」**
    #     라고 해서 파고들었더니, 자료에 같은 줄이 두 번 있었습니다.
    #
    #         img/jeju/photo/jejusi-yongduam.jpg · 용두암   (같은 줄 두 번)
    #
    #     주인 규칙 29 는 「숫자는 자료에서 센다」인데,
    #     **자료에 겹친 줄이 있으면 센 숫자가 틀립니다.**
    #     사이트에 적히는 사진 수가 하나 많았습니다.
    print('[0] 자료에 같은 사진이 두 번 적혀 있는가')
    겹친것, 본것 = [], {}
    for x in 자료사진들():
        파일 = x.get('파일')
        if not 파일:
            continue
        if 파일 in 본것:
            겹친것.append('%s (%s · %s)'
                          % (파일, 본것[파일], x.get('제목') or '?'))
        else:
            본것[파일] = x.get('제목') or '?'
    if 겹친것:
        막음.append('자료에 같은 사진이 두 번 적힌 것 %d건' % len(겹친것))
        print('  ✗ 같은 사진이 두 번 적혀 있습니다 %d건' % len(겹친것))
        for x in 겹친것[:5]:
            print('      %s' % x)
        print('      자료에서 센 숫자가 틀어집니다 (주인 규칙 29)')
    else:
        print('  · 서로 다른 사진 %d장 — 겹친 줄이 없습니다' % len(본것))
    print('')

    # ── 1. 보이는 것이 있는가
    print('[1] 쪽마다 보이는 것이 있는가')
    사진없는쪽 = []
    모든그림 = {}
    for p in 것들:
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        그림들 = re.findall(r'<img[^>]+src="([^"]+)"', s)
        if not 그림들:
            사진없는쪽.append(이름)
        모든그림[이름] = (그림들, s)
    print('      보이는 것이 있는 쪽 %d개 · 없는 쪽 %d개'
          % (len(것들) - len(사진없는쪽), len(사진없는쪽)))
    if 사진없는쪽:
        막음.append('보이는 것이 없는 쪽 %d개' % len(사진없는쪽))
        print('  ✗ %d쪽에 그림이 하나도 없습니다' % len(사진없는쪽))
        for x in 사진없는쪽[:8]:
            print('      %s' % x)
        print('      → 글만 있는 쪽에는 손님이 머물지 않습니다 (규칙 6-1)')
    else:
        print('  · 모든 쪽에 보이는 것이 있습니다')
    print('')

    # ── 2. 가리키는 파일이 진짜 있는가
    print('[2] 가리키는 그림 파일이 진짜 있는가')
    없는파일 = []
    본것 = set()
    for 이름, (그림들, _) in 모든그림.items():
        뿌리 = os.path.dirname(os.path.join(NEW, 이름.replace('/', os.sep)))
        for 주소 in 그림들:
            if 주소.startswith(('http://', 'https://', 'data:')):
                continue
            깨끗 = 주소.split('?')[0].split('#')[0]
            실제 = os.path.normpath(os.path.join(뿌리,
                                                 깨끗.replace('/', os.sep)))
            if 실제 in 본것:
                continue
            본것.add(실제)
            if not os.path.isfile(실제):
                없는파일.append('%s — %s' % (이름, 주소))
    print('      본 그림 %d갈래 · 없는 것 %d갈래'
          % (len(본것), len(없는파일)))
    if 없는파일:
        막음.append('없는 그림을 가리키는 곳 %d갈래' % len(없는파일))
        print('  ✗ %d갈래가 없는 파일을 가리킵니다' % len(없는파일))
        for x in 없는파일[:8]:
            print('      %s' % x)
        print('      → 주소를 짐작해 만들지 마세요. 자료에서 읽습니다.')
    else:
        print('  · 가리키는 그림이 모두 있습니다')
    print('')

    # ── 3·4·6. 설명을 제대로 적었는가
    print('[3] 사진 설명을 제대로 적었는가 (규칙 5·6)')
    촬영자없음, 허락적음, 설명없음 = [], [], []
    for 이름, (_, s) in 모든그림.items():
        for m in re.finditer(r'<figure[^>]*class="([^"]*)"[^>]*>(.*?)</figure>',
                             s, re.S):
            반, 안 = m.group(1), m.group(2)
            설명 = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', 안, re.S)
            글 = re.sub(r'<[^>]+>', '', 설명.group(1)).strip() if 설명 else ''
            if not 글:
                설명없음.append(이름)
                continue
            if 이용허락말.search(글):
                허락적음.append('%s — %s' % (이름, 글[:40]))
            # ★ **사진과 직접 그린 그림을 가릅니다** (2026-09-29)
            #
            #   규칙 5·6 이 촬영자를 요구하는 까닭은 **남의 사진**을
            #   쓰기 때문입니다. 직접 그린 그림에는 촬영자가 없고,
            #   지어내서도 안 됩니다(규칙 5).
            #
            #   사진이란 <img> 로 넣은 것입니다. <svg> 만 있으면
            #   우리가 그린 것입니다.
            #
            #   겪은 일: 어종 쪽에 삽화 246개를 되살리자 사진
            #   검사가 「촬영자가 빠진 곳 246개」라 했습니다.
            #   그림에 촬영자를 적을 수는 없습니다.
            사진인가 = '<img' in 안
            그린것 = ('photo--drawn' in 반) or (not 사진인가)
            if not 사진인가 and 'ls-card' in 반:
                # 배우는 차례 카드의 글은 사진 설명이 아니라
                # 가르치는 본문입니다. 설명 규칙을 대지 않습니다.
                continue
            if 그린것:
                # 그림은 「그림 · …」으로 적어야 합니다
                if not 글.startswith('그림'):
                    촬영자없음.append('%s — 그림인데 「그림」이라 안 적었습니다'
                                      % 이름)
            else:
                # 사진은 「사진 · 제목 · 촬영자」
                if not 글.startswith('사진'):
                    촬영자없음.append('%s — 사진인데 「사진」이라 안 적었습니다'
                                      % 이름)
                elif 글.count('·') < 2:
                    촬영자없음.append('%s — 촬영자가 없습니다: %s'
                                      % (이름, 글[:40]))
    print('      설명이 없는 쪽 %d · 촬영자가 빠진 곳 %d · '
          '이용허락 종류를 적은 곳 %d'
          % (len(설명없음), len(촬영자없음), len(허락적음)))
    if 설명없음:
        막음.append('사진 설명이 없는 곳 %d개' % len(설명없음))
        for x in 설명없음[:4]:
            print('  ✗ %s' % x)
    if 촬영자없음:
        막음.append('촬영자가 빠진 곳 %d개' % len(촬영자없음))
        for x in 촬영자없음[:5]:
            print('  ✗ %s' % x)
        print('      → 촬영자는 자료가 준 값만 적습니다 (규칙 5).')
        print('        지어내지 말고, 없으면 그림으로 밝히세요.')
    if 허락적음:
        막음.append('쪽에 이용허락 종류를 적은 곳 %d개' % len(허락적음))
        for x in 허락적음[:5]:
            print('  ✗ %s' % x)
        print('      → 「공공누리 제1유형」 같은 종류는 photos.html 에만')
        print('        둡니다 (규칙 6).')
    if not (설명없음 or 촬영자없음 or 허락적음):
        print('  · 설명을 규칙대로 적었습니다')
    print('')

    # ── 5. og:image
    # ── [4] 대표 사진이 **그 권역 것**인가
    #
    #   ★ 2026-09-29 바깥 검수 12차
    #
    #     「신안 페이지에 다른 지역 사진이 들어가도 파일 자체는
    #       정상적인 이미지이기 때문에 일반적인 이미지 검사는
    #       통과할 수 있습니다. 사진의 **존재** 검사와 사진의
    #       **의미적 매칭** 검사는 별개로 생각해야 합니다.」
    #
    #     재 보니 57권역이 다 맞았습니다. 그러나 **맞는지 재는
    #     검사가 없었습니다.** 우연히 맞은 것일 수도 있습니다.
    #
    #   첫 화면은 전국 쪽이라 어느 권역 사진이든 들어갑니다.
    print('[4] 대표 사진이 그 권역 것인가')
    사진표 = {}
    for x in 자료사진들():
        if x.get('파일'):
            사진표[x['파일']] = x
    첫화면들 = {'index'}
    어긋난것, 원장에없는것, 본쪽 = [], [], 0
    for 길 in 쪽들():
        이름 = os.path.basename(길)[:-5]
        if 이름 in 첫화면들 or os.sep in os.path.relpath(길, NEW):
            continue                       # 권역 쪽만 봅니다
        글 = io.read(길, default='')
        m = re.search(r'<img[^>]*src="([^"]*img/[^"]+)"', 글)
        if not m:
            continue
        본쪽 += 1
        사진길 = re.sub(r'^\.\./', '', m.group(1)).lstrip('./')
        한장 = 사진표.get(사진길)
        if 한장 is None:
            원장에없는것.append('%s → %s' % (이름, 사진길))
        elif 한장.get('권역') and 한장['권역'] != 이름:
            어긋난것.append('%s 쪽인데 사진은 %s 것 (%s)'
                            % (이름, 한장['권역'], 사진길))
    if not 본쪽:
        print('  ~ 권역 쪽이 없습니다 — 잴 것이 없습니다.')
    else:
        if 원장에없는것:
            막음.append('사진 원장에 없는 대표 사진 %d장' % len(원장에없는것))
            print('  ✗ 원장(photos.json)에 없는 대표 사진 %d장'
                  % len(원장에없는것))
            for x in 원장에없는것[:5]:
                print('      %s' % x)
        if 어긋난것:
            막음.append('다른 권역 사진을 쓴 쪽 %d개' % len(어긋난것))
            print('  ✗ 다른 권역 사진을 쓴 쪽 %d개' % len(어긋난것))
            for x in 어긋난것[:5]:
                print('      %s' % x)
            print('      → 파일은 멀쩡해도 **그 고장 바다가 아닙니다.**')
        if not 원장에없는것 and not 어긋난것:
            print('  · 권역 쪽 %d개의 대표 사진이 모두 그 고장 것입니다'
                  % 본쪽)
    print('')

    print('[5] 공유 미리보기 그림이 제대로인가 (규칙 28)')
    사진표 = io.read_json(os.path.join(DATA, 'raw', 'photos.json'),
                          default={}) or {}
    크기표 = dict((x.get('파일'), (x.get('가로'), x.get('세로')))
                  for x in (사진표.get('사진') or []) if x.get('파일'))
    og없음, og깨짐, og비율 = [], [], []
    같은것 = {}
    for 이름, (_, s) in 모든그림.items():
        m = re.search(r'og:image"\s+content="([^"]+)"', s)
        if not m:
            og없음.append(이름)
            continue
        주소 = m.group(1)
        상대 = re.sub(r'^https?://[^/]+/', '', 주소)
        같은것.setdefault(상대, []).append(이름)
        실제 = os.path.join(NEW, 상대.replace('/', os.sep))
        if not os.path.isfile(실제):
            og깨짐.append('%s — %s' % (이름, 주소))
        넓, 높 = 크기표.get(상대, (None, None))
        if 넓 and 높:
            if 넓 < 150 or 높 < 150 or 넓 / float(높) > 3 or 높 / float(넓) > 3:
                og비율.append('%s — %dx%d' % (상대, 넓, 높))
    print('      og:image 가 없는 쪽 %d · 없는 파일을 가리키는 쪽 %d '
          '· 가이드를 어긴 그림 %d'
          % (len(og없음), len(og깨짐), len(set(og비율))))
    if og없음:
        막음.append('og:image 가 없는 쪽 %d개' % len(og없음))
        for x in og없음[:4]:
            print('  ✗ %s' % x)
    if og깨짐:
        막음.append('og:image 가 없는 파일을 가리키는 쪽 %d개' % len(og깨짐))
        for x in og깨짐[:5]:
            print('  ✗ %s' % x)
        print('      → 이것이 2026-09-27 에 52갈래 깨져 있던 그 탈입니다.')
    if og비율:
        막음.append('og:image 가이드를 어긴 그림 %d개' % len(set(og비율)))
        for x in sorted(set(og비율))[:5]:
            print('  ✗ %s' % x)
    # 쪽마다 다른 사진이어야 합니다 (규칙 28)
    많이겹침 = [(k, v) for k, v in 같은것.items() if len(v) > 60]
    if 많이겹침:
        알림.append('여러 쪽이 같은 og:image 를 씁니다 %d갈래' % len(많이겹침))
        print('  ~ 여러 쪽이 같은 그림을 씁니다')
        for k, v in sorted(많이겹침, key=lambda x: -len(x[1]))[:4]:
            print('      %-42s %d쪽' % (k, len(v)))
        print('      가이드는 **쪽마다 다른 사진**을 권합니다 (규칙 28).')
    if not (og없음 or og깨짐 or og비율):
        print('  · 공유 미리보기가 모두 제대로입니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 사람은 눈으로 봅니다. 글만 있는 쪽은 아무리 내용이')
        print('    옳아도 손님이 머물지 않습니다 (주인 규칙 6-1).')
        return 1 if '--strict' in sys.argv else 0

    print('쪽 %d개에 모두 보이는 것이 있고, 설명도 규칙대로입니다.'
          % len(것들))
    return 0


if __name__ == '__main__':
    sys.exit(main())
