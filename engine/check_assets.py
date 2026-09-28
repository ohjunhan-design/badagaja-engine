# -*- coding: utf-8 -*-
"""쪽이 **요구하는 것**이 모두 있는지 봅니다. (검수 지시 6·7·17)

★ 왜 링크 검사만으로는 모자란가 (2026-09-27 바깥 검수 지시)

    「현재 favicon 관련 실제 버그가 발견됐으므로
      단순 HTML 링크 검사만 하지 않는다」

    맞습니다. check_links.py 는 `href` 만 봅니다. 그런데 쪽이
    요구하는 것은 그보다 많습니다.

        <img src>              사진
        srcset                 화면 크기별 사진
        CSS background-image   차림표 속 사진
        <link rel="icon">      아이콘
        <script src>           움직임
        <link href>            차림표·글꼴

    실제로 favicon 세 개가 **416쪽 전부에서 깨져** 있었는데,
    href 가 아니라 `<link rel="icon" href>` 라 알림에 섞여 지나갔습니다.

무엇을 보나
    1. 쪽이 요구하는 자산이 모두 있는가 (404 가 하나라도 있으면 막음)
    2. 선언한 아이콘이 실제로 있는가 (파일만 있고 선언이 없어도 안 됩니다)
    3. **아직 없는 쪽**을 손님이 누를 수 있게 두지 않았는가
       — 사이트맵·차림표·꼬리·구조화자료까지 봅니다

★ 17번은 「쪽이 없는 것」이 탈이 아닙니다
    없는 쪽을 **손님이 누를 수 있게 만들어 둔 것**이 탈입니다.

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_assets.py
    python engine/check_assets.py --list
    python engine/check_assets.py --strict
"""
import os
import re
import sys
import glob
import posixpath
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io    # noqa: E402
from engine import net   # noqa: E402  주소 가르기는 net.py 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

보일것 = '--list' in sys.argv

# 검사 등급 (계약-21)
#   막음 — 손님이 깨진 것을 보게 됩니다
#   알림 — 살펴볼 만한 것
막음, 알림 = [], []

# 바깥으로 나가는 것은 안 봅니다 (여기서 인터넷을 안 씁니다)
바깥 = re.compile(r'^(https?:|//|data:|mailto:|tel:|javascript:|#)')

# 아이콘 — 선언과 파일이 **둘 다** 있어야 합니다
아이콘들 = [
    ('icon', 'favicon.ico'),
    ('icon', 'favicon.svg'),
    ('apple-touch-icon', 'apple-touch-icon.png'),
]


def 있는것():
    나옴 = set()
    for p in glob.glob(os.path.join(NEW, '**', '*'), recursive=True):
        if os.path.isfile(p):
            나옴.add(os.path.relpath(p, NEW).replace(os.sep, '/'))
    return 나옴


def 풀기(여기, 길, 있는):
    """쪽에서 본 상대 주소를 사이트 안 길로."""
    길 = (길 or '').strip().split('?')[0].split('#')[0]
    if not 길:
        return None

    # ★ `https://badagaja.com/tide/` 도 **우리 자리**입니다 (2026-09-27)
    #   전에는 http 로 시작하면 무조건 바깥으로 보고 건너뛰었습니다.
    #   그래서 우리 주소를 통째로 적은 링크는 **깨져도 못 잡았습니다.**
    #   og:url·canonical·구조화 자료는 늘 통째 주소로 적습니다.
    if net.갈래(길) == net.우리것 and 길.lower().startswith('http'):
        남은 = 길.split('//', 1)[1]
        길 = '/' + (남은.split('/', 1)[1] if '/' in 남은 else '')
    elif 바깥.match(길):
        return None
    if 길.startswith('/'):
        간곳 = 길.lstrip('/')
    else:
        간곳 = posixpath.normpath(
            posixpath.join(posixpath.dirname(여기), 길))
    if 길.endswith('/') or 길 in ('.', './'):
        간곳 = posixpath.join(간곳.rstrip('/.'), 'index.html').lstrip('/')
    elif 간곳 not in 있는 and (간곳 + '/index.html') in 있는:
        간곳 = 간곳 + '/index.html'
    return 간곳


def 쪽이요구하는것(여기, s, 있는):
    """그 쪽이 실제로 받아 와야 하는 것들."""
    나옴 = []
    본꼴 = [
        (r'<img[^>]+src="([^"]+)"', '사진'),
        (r'<source[^>]+srcset="([^"]+)"', '사진(srcset)'),
        (r'<img[^>]+srcset="([^"]+)"', '사진(srcset)'),
        (r'<script[^>]+src="([^"]+)"', '움직임'),
        (r'<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"', '차림표'),
        (r'<link[^>]+rel="(?:icon|apple-touch-icon|shortcut icon)"'
         r'[^>]*href="([^"]+)"', '아이콘'),
        (r'<link[^>]+rel="manifest"[^>]*href="([^"]+)"', '앱 설정'),
        (r'url\((["\']?)([^)"\']+)\1\)', '차림표 속 사진'),
    ]
    for 꼴, 갈래 in 본꼴:
        for m in re.finditer(꼴, s):
            값 = m.group(m.lastindex or 1)
            # srcset 은 「주소 1x, 주소 2x」 꼴입니다
            for 한개 in re.split(r'\s*,\s*', 값):
                한개 = 한개.strip().split(' ')[0]
                간곳 = 풀기(여기, 한개, 있는)
                if 간곳:
                    나옴.append((간곳, 갈래))
    return 나옴


def 남기기로한것():
    """data/raw/keep.json 의 「남길것」 — **일부러 서버에 두는 옛 파일**.

    ★ 「아직 안 만듦」과 다릅니다 (2026-09-27)
        아직 안 만듦   나중에 만들 쪽. 지금은 갈 곳이 없습니다
        남길 것       **옛 쪽이 서버에 그대로 있습니다** — 404 가 안 납니다

      배포가 파일을 안 지우므로 옛 쪽이 남는 것은 사실입니다.
      다만 그것은 **우연히 안전한 것**이라, 일부러 남긴다고
      적어 둔 것만 봐줍니다. 안 적었으면 탈입니다.
    """
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
    나옴 = set()
    for k in (d.get('남길것') or {}):
        if k.startswith('_'):
            continue
        나옴.add(k)
        if k.endswith('/index.html'):
            나옴.add(k[:-len('/index.html')])
        if k.endswith('/'):
            나옴.add(k.rstrip('/'))
    return 나옴


def 아직안만든쪽():
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    쪽 = set((d.get('아직_안_만듦') or {}).get('쪽') or [])
    for x in list(쪽):
        if x.endswith('/index.html'):
            쪽.add(x[:-len('/index.html')])
    return 쪽


def main():
    있는 = 있는것()
    쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('쪽이 요구하는 것이 모두 있는가 (검수 지시 6·7·17)')
    print('  쪽 %d개 · 사이트 안 파일 %d개' % (len(쪽들), len(있는)))
    print('')

    # ── 1. 자산 전수
    print('[1] 쪽이 요구하는 자산')
    없는것 = collections.Counter()
    갈래별 = {}
    어디서 = {}
    센것 = 0
    for p in 쪽들:
        여기 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        for 간곳, 갈래 in 쪽이요구하는것(여기, s, 있는):
            센것 += 1
            if 간곳 not in 있는:
                없는것[간곳] += 1
                갈래별[간곳] = 갈래
                어디서.setdefault(간곳, 여기)
    print('      요구한 자산 %d번 · 갈래 %d가지'
          % (센것, len(set(갈래별.values())) if 갈래별 else 0))
    if 없는것:
        막음.append('없는 자산을 요구하는 곳 %d갈래' % len(없는것))
        print('  ✗ 사이트에 없는 자산 %d갈래' % len(없는것))
        for 간곳, 수 in 없는것.most_common(8 if not 보일것 else 99):
            print('      %-42s %-12s %4d곳   보기: %s'
                  % (간곳, 갈래별[간곳], 수, 어디서[간곳]))
    else:
        print('  · 요구하는 자산이 모두 있습니다')
    print('')

    # ── 2. 아이콘 — 선언과 파일이 둘 다
    print('[2] 아이콘 — 선언과 파일이 둘 다 있는가')
    첫쪽 = io.꼭읽기(os.path.join(NEW, 'index.html'))
    탈 = []
    for rel, 파일 in 아이콘들:
        선언 = re.search(r'<link[^>]+rel="[^"]*%s[^"]*"[^>]*href="([^"]+)"'
                         % re.escape(rel), 첫쪽)
        있나 = 파일 in 있는
        if not 선언:
            탈.append('%s — 첫 화면에 선언이 없습니다' % 파일)
        elif not 있나:
            탈.append('%s — 선언은 있는데 파일이 없습니다' % 파일)
        else:
            print('      · %-24s 선언 있음 · 파일 있음' % 파일)
    # 모든 쪽에 선언이 있는가
    선언없는쪽 = [os.path.relpath(p, NEW).replace(os.sep, '/')
                  for p in 쪽들
                  if 'rel="icon"' not in io.read(p, default='')]
    if 선언없는쪽:
        탈.append('아이콘 선언이 없는 쪽 %d개' % len(선언없는쪽))
    if 탈:
        막음.append('아이콘 %d건' % len(탈))
        for x in 탈:
            print('  ✗ %s' % x)
    else:
        print('  · 쪽 %d개가 모두 아이콘을 선언하고, 파일도 있습니다'
              % len(쪽들))
    print('')

    # ── 3. 아직 없는 쪽을 누를 수 있게 두지 않았는가
    print('[3] 아직 없는 쪽을 손님이 누를 수 있는가')
    아직 = 아직안만든쪽()
    남길것 = 남기기로한것()
    print('      아직 안 만들기로 적어 둔 쪽 %d개 · '
          '옛 쪽을 일부러 남기기로 한 것 %d갈래' % (len(아직), len(남길것)))
    누를수있음 = collections.Counter()
    지켜진것 = collections.Counter()
    어느쪽에 = {}
    for p in 쪽들:
        여기 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        for m in re.finditer(r'href="([^"]+)"', s):
            간곳 = 풀기(여기, m.group(1), 있는)
            if 간곳 and 간곳 not in 있는:
                # 옛 쪽을 일부러 남기기로 했으면 404 가 안 납니다
                if 간곳 in 남길것:
                    지켜진것[간곳] += 1
                    continue
                누를수있음[간곳] += 1
                어느쪽에.setdefault(간곳, 여기)
    # 사이트맵·구조화자료도 봅니다
    사이트맵 = io.꼭읽기(os.path.join(NEW, 'sitemap.xml'))
    맵에든것 = []
    for m in re.finditer(r'<loc>([^<]+)</loc>', 사이트맵):
        길 = m.group(1).split('badagaja.com/')[-1] or 'index.html'
        길 = 길 if 길.endswith('.html') else (길.rstrip('/') + '/index.html'
                                             if 길.strip('/') else 'index.html')
        # ★ 옛 사이트에 남기기로 한 쪽은 **서버에 살아 있습니다** (2026-09-28)
        #   about.html·photos.html 처럼 새 틀이 아직 안 만드는 쪽입니다.
        #   사이트맵에 넣는 것이 맞습니다 — 빼면 검색에서 사라집니다.
        #   링크 검사는 이미 남길것을 보는데 여기만 안 봐서,
        #   사이트맵을 만들자마자 10개가 헛 FAIL 로 걸렸습니다.
        if 길 not in 있는 and 길 not in 남길것:
            맵에든것.append(길)
    if 누를수있음:
        막음.append('없는 쪽으로 가는 링크 %d갈래' % len(누를수있음))
        print('  ✗ 손님이 누르면 404 가 되는 링크 %d갈래' % len(누를수있음))
        for 간곳, 수 in 누를수있음.most_common(8 if not 보일것 else 99):
            적힘 = '(아직 안 만들기로 적어 둠)' if 간곳 in 아직 else ''
            print('      %-40s %4d곳   %s %s'
                  % (간곳, 수, 어느쪽에[간곳], 적힘))
        print('      → 아직 안 만든 쪽이라도 **누를 수 있게 두면 안 됩니다.**')
        print('        만들거나, 링크를 빼거나, 「준비 중」으로 표시하세요.')
    else:
        print('  · 손님이 누르면 404 가 되는 링크가 없습니다')
    if 지켜진것:
        print('  ~ 새 틀이 안 만들지만 **옛 쪽을 남기기로 한 것** %d갈래'
              % len(지켜진것))
        for 간곳, 수 in 지켜진것.most_common(4):
            print('      %-40s %4d곳' % (간곳, 수))
        print('      (data/raw/keep.json 에 적혀 있습니다.')
        print('       새 틀로 만들면 거기서 빼세요)')
    if 맵에든것:
        막음.append('사이트맵에 없는 쪽 %d개' % len(맵에든것))
        print('  ✗ 사이트맵이 없는 쪽을 가리킵니다 %d개: %s'
              % (len(맵에든것), ' · '.join(맵에든것[:4])))
    elif 사이트맵:
        print('  · 사이트맵이 가리키는 쪽이 모두 있습니다')
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
        if not 보일것:
            print('')
            print('  다 보려면 --list 를 붙이세요.')
        return 1 if '--strict' in sys.argv else 0
    print('쪽이 요구하는 것이 모두 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
