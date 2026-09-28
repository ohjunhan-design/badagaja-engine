# -*- coding: utf-8 -*-
"""대표 주소가 **실제로** 하나인지 봅니다. (검수 지시 12·14)

★ 왜 HTML 만 보면 모자란가 (2026-09-27 바깥 검수 지시)

    「단순히 HTML 의 canonical 만 / 으로 넣어놓았다고 끝내면 안 됩니다.
      반드시 실제 HTTP 응답을 확인하세요.

        https://badagaja.com/
        https://badagaja.com/index.html
        https://www.badagaja.com/
        https://www.badagaja.com/index.html

      각각이 최종적으로 어느 URL 을 대표 주소로 삼는지 확인해야 합니다」

    맞습니다. 쪽 안에 `canonical` 을 잘 적어 두어도, 서버가
    `/index.html` 을 200 으로 그대로 내주면 검색엔진은 **두 쪽**으로
    볼 수 있습니다. 실제로 첫 화면 canonical 이 `/index.html` 로
    나오던 것을 고친 적이 있습니다.

무엇을 보나
    1. 쪽 안의 canonical 이 제 주소를 가리키는가 (416쪽 전수)
    2. 첫 화면 대표 주소가 `https://badagaja.com/` 인가
    3. **실제 HTTP 응답** — / · /index.html · www · 비www
       (--net 을 붙일 때만. 바깥에 나가는 일이라 일부러 안 합니다)
    4. 첫 화면 제목이 정해 둔 것과 같은가 (검수 지시 14)

★ 14번 — 첫 배포에서는 **옛 제목을 유지**합니다
    「기존 검색 노출 제목을 유지한다. 새 디자인/HTML 구조와
      검색 title 변경을 동시에 진행하지 않는다」 (바깥 검수)

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_canonical.py
    python engine/check_canonical.py --net      실제 서버에 물어봅니다
    python engine/check_canonical.py --strict
"""
import os
import re
import sys
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, url   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []

# 첫 화면 대표 주소 — 네이버에 이미 색인된 것
대표주소 = 'https://badagaja.com/'


def 정해둔제목():
    """data/raw/site.json 의 「첫화면제목」에 실제 수를 채운 것."""
    from engine.data import 자료
    d = io.read_json(os.path.join(DATA, 'raw', 'site.json'), default={})
    틀 = (d.get('첫화면제목') or {}).get('ko')
    if not 틀:
        return None
    if '{포인트수}' in 틀:
        내림 = (자료().셈() // 500) * 500
        return 틀.replace('{포인트수}', format(내림, ','))
    return 틀


def 말한수가참인가():
    """제목의 「○○곳 이상」이 **거짓이 아닌지** 봅니다.

    ★ 왜 재나 (2026-09-27)
        「3,600곳 이상」은 자료가 늘어도 제목이 안 바뀌게 하는
        좋은 표현입니다. 다만 자료가 **줄면** 거짓이 됩니다.
        포인트를 정리하다 3,600 아래로 내려가면, 제목이
        손님에게 거짓말을 하게 됩니다.

        숫자는 자료에서 세므로 저절로 따라오지만, 사람이 틀을
        손으로 고칠 수도 있으니 여기서 한 번 더 봅니다.
    """
    from engine.data import 자료
    d = io.read_json(os.path.join(DATA, 'raw', 'site.json'), default={})
    틀 = (d.get('첫화면제목') or {}).get('ko') or ''
    참말 = 자료().셈()
    m = re.search(r'([\d,]+)곳 이상', 정해둔제목() or '')
    if not m:
        return None, 참말, None
    말한것 = int(m.group(1).replace(',', ''))
    return 말한것 <= 참말, 참말, 말한것


def 실제응답(주소):
    """그 주소가 실제로 무엇을 내주는지. --net 일 때만 부릅니다."""
    import urllib.request
    import urllib.error

    class 안따라감(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    열기 = urllib.request.build_opener(안따라감)
    요청 = urllib.request.Request(주소, method='GET',
                                  headers={'User-Agent': 'badagaja-check'})
    try:
        with 열기.open(요청, timeout=20) as f:
            글 = f.read(60000).decode('utf-8', 'ignore')
            m = re.search(r'<link rel="canonical" href="([^"]+)"', 글)
            return {'코드': f.status, '간곳': None,
                    'canonical': m.group(1) if m else None}
    except urllib.error.HTTPError as e:
        return {'코드': e.code, '간곳': e.headers.get('Location'),
                'canonical': None}
    except Exception as e:
        return {'코드': None, '간곳': None, 'canonical': None,
                '탈': str(e)[:50]}


def main():
    바깥에물어볼까 = '--net' in sys.argv
    쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('대표 주소가 실제로 하나인가 (검수 지시 12·14)')
    print('  쪽 %d개' % len(쪽들))
    print('')

    # ── 1. 쪽 안의 canonical 전수
    print('[1] 쪽마다 canonical 이 제 주소를 가리키는가')
    없음, 틀림 = [], []
    for p in 쪽들:
        길 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not m:
            없음.append(길)
            continue
        바람 = url.full(길)
        if m.group(1) != 바람:
            틀림.append('%s → %s (있어야 할 것 %s)' % (길, m.group(1), 바람))
    print('      canonical 이 있는 쪽 %d개' % (len(쪽들) - len(없음)))
    if 없음:
        막음.append('canonical 이 없는 쪽 %d개' % len(없음))
        print('  ✗ canonical 이 없는 쪽 %d개: %s'
              % (len(없음), ' · '.join(없음[:4])))
    if 틀림:
        막음.append('canonical 이 제 주소가 아닌 쪽 %d개' % len(틀림))
        print('  ✗ 제 주소가 아닌 쪽 %d개' % len(틀림))
        for x in 틀림[:4]:
            print('      %s' % x)
    if not (없음 or 틀림):
        print('  · 모든 쪽이 제 주소를 가리킵니다')
    print('')

    # ── 2. 첫 화면 대표 주소
    print('[2] 첫 화면 대표 주소')
    첫쪽 = io.꼭읽기(os.path.join(NEW, 'index.html'))
    c = re.search(r'<link rel="canonical" href="([^"]+)"', 첫쪽)
    og = re.search(r'property="og:url" content="([^"]+)"', 첫쪽)
    for 이름, m in (('canonical', c), ('og:url', og)):
        값 = m.group(1) if m else '(없음)'
        맞나 = (값 == 대표주소)
        print('      %-10s %-34s %s' % (이름, 값, '·' if 맞나 else '✗'))
        if not 맞나:
            막음.append('첫 화면 %s 가 %s 가 아닙니다 (%s)'
                        % (이름, 대표주소, 값))
    print('      ※ 네이버에 색인된 주소는 경로 없는 뿌리입니다')
    print('')

    # ── 3. 첫 화면 제목 정책 (검수 지시 14)
    print('[3] 첫 화면 제목 — 첫 배포에서는 옛 제목을 유지합니다')
    t = re.search(r'<title>(.*?)</title>', 첫쪽, re.S)
    지금제목 = t.group(1).strip() if t else ''
    정해둔 = 정해둔제목()
    print('      지금 제목   %s' % 지금제목)
    if 정해둔:
        print('      정해 둔 것  %s' % 정해둔)
        # 「○○곳 이상」이 참인가
        참인가, 참말, 말한것 = 말한수가참인가()
        if 참인가 is not None:
            print('      말한 수 %s곳 이상 · 실제 %s곳  %s'
                  % (format(말한것, ','), format(참말, ','),
                     '·' if 참인가 else '✗ 거짓입니다'))
            if not 참인가:
                막음.append('제목의 「%d곳 이상」이 거짓입니다 (실제 %d곳)'
                            % (말한것, 참말))
        맞나 = (지금제목 == 정해둔)
        if not 맞나:
            막음.append('첫 화면 제목이 정해 둔 것과 다릅니다')
            print('  ✗ 다릅니다 — data/raw/site.json 의 「첫화면제목」을 보세요')
        else:
            print('  · 정해 둔 제목 그대로입니다')
    else:
        막음.append('첫 화면 제목을 자료에 안 정해 두었습니다')
        print('  ✗ 자료에 정해 둔 제목이 없습니다')
        print('      → data/raw/site.json 에 「첫화면제목」을 적어 주세요.')
        print('        바깥 검수: 「기존 검색 노출 제목을 유지한다.')
        print('        새 디자인과 검색 제목 변경을 동시에 하지 않는다」')
    print('')

    # ── 4. 실제 HTTP 응답
    print('[4] 실제 서버가 내주는 것')
    if not 바깥에물어볼까:
        알림.append('실제 HTTP 응답은 --net 을 붙여야 잽니다')
        print('  ~ 안 물어봤습니다 — 바깥에 나가는 일이라 일부러 안 합니다')
        print('      물어보려면: python engine/check_canonical.py --net')
        print('      ※ 이것은 「지킴」이 아닙니다. **안 잰 것**입니다.')
    else:
        볼주소 = [
            'https://badagaja.com/',
            'https://badagaja.com/index.html',
            'https://www.badagaja.com/',
            'https://www.badagaja.com/index.html',
        ]
        탈 = []
        for 주소 in 볼주소:
            # ★ **끝까지 따라갑니다** (2026-09-27)
            #   바깥 검수: 「각각이 **최종적으로** 어느 URL 을 대표
            #   주소로 삼는지 확인해야 합니다」
            #   한 번만 보면 www/index.html → /index.html 에서 멈춰
            #   「다른 곳으로 간다」고 잘못 봅니다.
            길 = [주소]
            지금 = 주소
            것 = None
            for _ in range(4):
                것 = 실제응답(지금)
                if 것.get('간곳'):
                    지금 = 것['간곳']
                    길.append(지금)
                    continue
                break
            코드 = 것.get('코드') if 것 else None
            can = (것 or {}).get('canonical') or ''
            넘김수 = len(길) - 1
            print('      %-42s %s%s%s'
                  % (주소, 코드 or (것 or {}).get('탈', '?'),
                     '  →  %s' % ' → '.join(길[1:]) if 넘김수 else '',
                     '  canonical=%s' % can if can else ''))
            끝 = 길[-1]
            if 코드 == 200 and can and can != 대표주소:
                탈.append('%s 가 200 인데 canonical 이 %s' % (주소, can))
            elif 코드 == 200 and 끝 != 대표주소:
                탈.append('%s 가 %s 에서 멈춥니다 (대표는 %s)'
                          % (주소, 끝, 대표주소))
            if 넘김수 > 1:
                알림.append('%s 가 %d번 넘어갑니다 — 한 번에 가는 편이 낫습니다'
                            % (주소, 넘김수))
            if 코드 is None:
                탈.append('%s — 못 물어봤습니다 (%s)'
                          % (주소, (것 or {}).get('탈', '')))
        if 탈:
            막음.append('실제 응답에 탈 %d건' % len(탈))
            for x in 탈:
                print('  ✗ %s' % x)
        else:
            print('  · 네 주소가 모두 같은 대표 주소를 가리킵니다')
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
        return 1 if '--strict' in sys.argv else 0
    if not 바깥에물어볼까:
        # 실제 응답을 안 쟀으면 **통과라고 말하지 않습니다**
        print('쪽 안의 대표 주소는 맞습니다. '
              '다만 실제 서버 응답은 안 쟀습니다 (--net).')
        return 0
    print('대표 주소가 실제로 하나입니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
