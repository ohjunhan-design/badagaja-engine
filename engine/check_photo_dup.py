# -*- coding: utf-8 -*-
"""**한 쪽에서 같은 사진이 두 번 나오는가** (2026-10-02 바깥 검수 13차).

★ 바깥 검수가 잡은 것
  「SHA 로 전수 비교했더니 **같은 사진을 다른 이름으로** 쓰는 곳이
    있습니다. `changwon-hero.jpg` = `changwon-udo.jpg`,
    `gangneung-hero.jpg` = `gangneung-tour-128757.jpg`,
    `sokcho-hero.jpg` = `sokcho-yeonggeumjeong.jpg` …
    **문제는 파일 중복 자체가 아니라 한 페이지에서 같은 사진이
    Hero 와 관광카드에 다시 나오는 경우입니다.**
    그렇게 되면 사용자는 「사진이 많은 사이트」가 아니라
    **같은 사진을 돌려 쓰는 사이트**처럼 느낍니다.
    페이지 단위 중복 검사도 넣어야 합니다」

  맞습니다. 파일이 둘인 것은 자리만 더 쓸 뿐 손님은 모릅니다.
  그러나 **한 쪽 안에서 같은 그림이 두 번 보이면** 바로 느낍니다 —
  위에 큰 사진으로 한 번, 아래 카드에 또 한 번.

★ 이름이 아니라 **알맹이**를 봅니다
  `changwon-hero.jpg` 와 `changwon-udo.jpg` 는 이름이 다릅니다.
  이름만 보면 다른 사진입니다. **내용(sha1)** 을 보아야 압니다.
  [[photo-check-by-distance]] — 「이름은 못 믿습니다」

★ 두 가지를 냅니다
    [1] **한 쪽 안에서 같은 그림이 두 번** — 손님이 느낍니다
    [2] 같은 알맹이인데 이름이 여럿 — 알림입니다(자리만 더 씁니다)
"""
import collections
import hashlib
import io
import os
import re
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

막음, 알림 = [], []

_img = re.compile(r'<img\b([^>]*)>', re.I)
_attr = re.compile(r'([\w-]+)\s*=\s*["\']([^"\']*)["\']')
_bg = re.compile(r'url\(\s*["\']?([^"\')]+\.(?:jpg|jpeg|png|webp))', re.I)
_og = re.compile(
    r'<meta\b[^>]*\bproperty\s*=\s*["\']og:image["\'][^>]*'
    r'\bcontent\s*=\s*["\']([^"\']+)["\']', re.I)


def 말(s=''):
    print(s)


def _사이트():
    return os.environ.get('BADAGAJA_SITE') or os.path.join(뿌리, 'site')


_지문기억 = {}


def _지문(길):
    if 길 in _지문기억:
        return _지문기억[길]
    try:
        with io.open(길, 'rb') as f:
            h = hashlib.sha1(f.read()).hexdigest()
    except OSError:
        h = None
    _지문기억[길] = h
    return h


def _실제자리(주소, 쪽길, 밑):
    """쪽이 가리키는 주소를 실제 파일 자리로 바꿉니다."""
    if not 주소 or 주소.startswith(('http://', 'https://', '//', 'data:')):
        return None
    깨끗 = 주소.split('?')[0].split('#')[0]
    if 깨끗.startswith('/'):
        p = os.path.join(밑, 깨끗.lstrip('/'))
    else:
        p = os.path.normpath(os.path.join(os.path.dirname(쪽길), 깨끗))
    return p if os.path.exists(p) else None


def _쪽그림들(글, 쪽길, 밑):
    """그 쪽이 **손님에게 보이는** 그림들. 아이콘은 뺍니다.

    28×28 아이콘이 여러 번 나오는 것은 중복이 아닙니다 — 카드마다
    같은 아이콘을 다는 것이 정상입니다. **사진**만 봅니다.
    """
    것들 = []
    for m in _img.finditer(글):
        속 = dict(_attr.findall(m.group(1)))
        주소 = (속.get('src') or 속.get('data-src') or '').strip()
        if not 주소:
            continue
        반 = 속.get('class') or ''
        if 'card-ico' in 반 or '/assets/icon/' in 주소 or 주소.endswith('.svg'):
            continue
        # ★ **갈아끼우는 자리는 빼야 합니다** (2026-10-02)
        #   `rp-img` 는 지도에서 포인트를 고르면 그 포인트 사진으로
        #   바뀝니다(`region-map.js`). 쪽을 열었을 때 보이는 것은
        #   **기본값**이고, 자료에 「포인트에 사진이 없으면 권역
        #   대표사진」이라고 적혀 있습니다. 그러니 처음에 히어로와
        #   같아 보이는 것은 **잘못이 아닙니다.**
        #   처음 이것을 안 빼서 네 쪽을 거짓으로 잡았습니다.
        if 'rp-img' in 반:
            continue
        p = _실제자리(주소, 쪽길, 밑)
        if p:
            것들.append((주소, p))
    for m in _bg.finditer(글):
        p = _실제자리(m.group(1), 쪽길, 밑)
        if p:
            것들.append((m.group(1), p))
    return 것들


def 검사_쪽안중복():
    말()
    말('[1] 한 쪽에서 같은 사진이 두 번 나오지 않는가')
    밑 = _사이트()
    걸린것, 본쪽, 본그림 = [], 0, 0
    for 뿌, _, 들 in os.walk(밑):
        for n in 들:
            if not n.endswith('.html'):
                continue
            p = os.path.join(뿌, n)
            본쪽 += 1
            글 = io.open(p, encoding='utf-8', errors='replace').read()
            # og:image 도 함께 봅니다 — 공유 미리보기가 본문과 같으면
            # 그건 정상입니다. 그래서 본문 안에서만 셉니다.
            것들 = _쪽그림들(글, p, 밑)
            본그림 += len(것들)
            지문별 = collections.defaultdict(list)
            for 주소, 자리 in 것들:
                h = _지문(자리)
                if h:
                    지문별[h].append(주소)
            for h, 주소들 in 지문별.items():
                if len(주소들) < 2:
                    continue
                # **같은 주소를 두 번** 쓴 것은 흔히 srcset·picture 입니다.
                # 손님에게는 한 장으로 보이므로 중복이 아닙니다.
                다른이름 = sorted(set(os.path.basename(x.split('?')[0])
                                   for x in 주소들))
                if len(다른이름) < 2:
                    continue
                걸린것.append('%s — 같은 사진이 %d번 (%s)' % (
                    os.path.relpath(p, 밑).replace(os.sep, '/'),
                    len(주소들), ' = '.join(다른이름)))
    말('      쪽 %d개 · 사진 자리 %d곳' % (본쪽, 본그림))
    if 걸린것:
        막음.append('한 쪽에 같은 사진이 두 번 나오는 쪽 %d개' % len(걸린것))
        말('  x **한 쪽에서 같은 사진이 두 번 보입니다 %d쪽**' % len(걸린것))
        for x in 걸린것[:10]:
            말('      %s' % x)
        말('      → 손님은 「사진이 많다」가 아니라')
        말('        **「같은 사진을 돌려 쓴다」**로 느낍니다.')
    else:
        말('  · 한 쪽 안에서 같은 사진이 두 번 나오는 곳이 없습니다')


def 검사_같은알맹이():
    """[2] 알맹이가 같은데 이름이 여럿 — 알림입니다."""
    말()
    말('[2] 알맹이가 같은데 이름이 여럿인 사진')
    밑 = _사이트()
    그림칸 = os.path.join(밑, 'img')
    if not os.path.isdir(그림칸):
        알림.append('사진 칸을 못 찾았습니다')
        말('  ~ 사진 칸이 없습니다')
        return
    지문별 = collections.defaultdict(list)
    본것 = 0
    for 뿌, _, 들 in os.walk(그림칸):
        for n in 들:
            if not n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
            p = os.path.join(뿌, n)
            본것 += 1
            h = _지문(p)
            if h:
                지문별[h].append(os.path.relpath(p, 밑).replace(os.sep, '/'))
    겹친것 = {h: v for h, v in 지문별.items() if len(v) > 1}
    말('      사진 %d장 · 알맹이 %d갈래' % (본것, len(지문별)))
    if 겹친것:
        낭비 = sum(len(v) - 1 for v in 겹친것.values())
        알림.append('같은 알맹이인데 이름이 여럿 %d갈래 (%d장 더)'
                   % (len(겹친것), 낭비))
        말('  ~ 알맹이가 같은 사진 %d갈래 — %d장이 겹칩니다'
           % (len(겹친것), 낭비))
        for v in sorted(겹친것.values(), key=lambda x: -len(x))[:8]:
            말('      %s' % ' = '.join(sorted(v)))
        말('      → 자리만 더 쓸 뿐 손님은 모릅니다. [1] 이 진짜 문제입니다.')
    else:
        말('  · 알맹이가 겹치는 사진이 없습니다')


def 하기():
    엄격 = '--strict' in sys.argv
    말()
    말('한 쪽에서 같은 사진이 두 번 나오는가')
    말('=' * 60)
    검사_쪽안중복()
    검사_같은알맹이()
    말()
    말('-' * 60)
    if 알림:
        말('알림 %d (막지 않습니다)' % len(알림))
        for x in 알림:
            말('    %s' % x)
    if 막음:
        말('어김 %d' % len(막음))
        for x in 막음:
            말('    %s' % x)
        return 1 if 엄격 else 0
    말('어김 없습니다')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(하기())
