# -*- coding: utf-8 -*-
"""쪽끼리 이어지는 길이 실제로 있는지 봅니다.  (계약-12)

왜
    쪽은 잘 만들어졌는데 **서로 못 가는** 일이 생깁니다.
    옛 사이트에서 포인트 쪽의 「권역으로」 단추가 자기 쪽을 가리키거나,
    없는 쪽으로 이어진 적이 있었습니다.

무엇을 보나
    1. 쪽 안의 링크가 실제 파일을 가리키는가
    2. 자료에 있는 것에 대응하는 쪽이 다 있는가 (계약-12)
    3. 자기 자신을 가리키는 링크는 없는가

쓰는 법
    python engine/check_links.py
    python engine/check_links.py --strict   탈이 있으면 1 로 끝냅니다
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
from engine import io, url   # noqa: E402
from engine import pages     # noqa: E402  주소의 갈래는 pages.py 한 곳에서만
from engine.data import 자료   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))


def 아직안만든쪽():
    """만들기로 했는데 아직 안 만든 쪽 (data/raw/url-map.json).

    ★ 왜 갈라 보나 (2026-09-26, tests/test_checkers.py 가 잡음)

        처음에는 끊긴 링크를 모두 「알림」으로 두었습니다. 아직 안 만든
        쪽이 많으니 막으면 늘 빨간불일 것 같아서였습니다.

        그래서 favicon.ico·favicon.svg·apple-touch-icon.png 가
        **416쪽 전부에서 깨져 있는 것을 놓쳤습니다.** 알림에 섞여
        조용히 지나갔습니다.

        목록에 적힌 것만 봐주고, 나머지는 막습니다.
        「나중에 만들 쪽」과 「빠뜨린 것」은 다른 일입니다.
    """
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    쪽 = set((d.get('아직_안_만듦') or {}).get('쪽') or [])
    # 'guide/index.html' 을 적어 두었으면 'guide' 로 가는 링크도 같은 뜻입니다
    for x in list(쪽):
        if x.endswith('/index.html'):
            쪽.add(x[:-len('/index.html')])
    return 쪽

문제, 알림 = [], []


def 탈(이름, 수, 보기=''):
    if 수:
        문제.append(이름)
        print('  ✗ %-34s %d건 %s' % (이름, 수, 보기))
    else:
        print('  · %-34s 이상 없음' % 이름)


def 참고(이름, 수, 보기=''):
    if 수:
        알림.append(이름)
        print('  ~ %-34s %d건 %s' % (이름, 수, 보기))
    else:
        print('  · %-34s 이상 없음' % 이름)


def main():
    d = 자료()
    쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    # 차림표·그림 같은 것도 링크 대상입니다. html 만 보면 멀쩡한 파일을
    # 「없다」고 알려 검사가 무뎌집니다 (2026-09-26)
    있는쪽 = set()
    for p in glob.glob(os.path.join(NEW, '**', '*'), recursive=True):
        if os.path.isfile(p):
            있는쪽.add(os.path.relpath(p, NEW).replace('\\', '/'))

    print('쪽끼리 이어지는 길 (계약-12)')
    print('  쪽 %d개' % len(쪽들))
    print('')

    # ── 1. 링크가 실제 파일을 가리키는가
    print('[1] 링크')
    못찾음 = collections.Counter()
    나중에 = collections.Counter()
    남긴쪽으로 = collections.Counter()
    자기자신 = []
    센것 = 0
    아직 = 아직안만든쪽()
    # ★ keep.json 의 「남긴 옛 쪽」도 봐야 합니다 (2026-09-27)
    #   travel/index.html 은 「옛 쪽을 일부러 남깁니다」로 적혀
    #   있는데 이 검사기만 그 파일을 안 읽어 FAIL 을 냈습니다.
    #   check_assets 는 읽어서 통과시켰습니다 — 답이 달랐습니다.
    남긴것 = pages.남긴옛쪽들()
    for p in 쪽들:
        여기 = os.path.relpath(p, NEW).replace('\\', '/')
        s = io.read(p, default='')
        for m in re.finditer(r'href="(?!https?:|mailto:|tel:|#|//|data:)([^"#?]*)',
                             s):
            길 = m.group(1).strip()
            if not 길:
                continue
            센것 += 1
            간곳 = posixpath.normpath(
                posixpath.join(posixpath.dirname(여기), 길))
            # 'catch/' 는 normpath 를 거치면 'catch' 가 되어 슬래시가
            # 사라집니다. 원래 길이 슬래시로 끝났는지를 보고 판단합니다.
            if 길.endswith('/') or 길 in ('.', './'):
                간곳 = posixpath.join(간곳.rstrip('/.'), 'index.html').lstrip('/')
            elif 간곳 not in 있는쪽 and (간곳 + '/index.html') in 있는쪽:
                간곳 = 간곳 + '/index.html'
            if 간곳 == 여기:
                자기자신.append('%s → %s' % (여기, 길))
            elif 간곳 not in 있는쪽:
                # 목록에 적어 둔 것만 봐줍니다. 나머지는 빠뜨린 것입니다
                if 간곳 in 남긴것:
                    # 옛 쪽이 서버에 그대로 있습니다 — 404 가 안 납니다
                    남긴쪽으로[간곳] += 1
                else:
                    (나중에 if 간곳 in 아직 else 못찾음)[간곳] += 1
    print('      링크 %d개를 봤습니다' % 센것)
    탈('자기 자신을 가리키는 링크', len(자기자신), ' · '.join(자기자신[:3]))
    탈('없는 곳으로 가는 링크', len(못찾음),
       ' · '.join('%s(%d곳)' % (k, v) for k, v in 못찾음.most_common(6)))
    참고('일부러 남긴 옛 쪽으로 가는 링크', len(남긴쪽으로),
         ' · '.join('%s(%d곳)' % (k, v)
                    for k, v in 남긴쪽으로.most_common(4)))
    참고('아직 안 만든 쪽으로 가는 링크', len(나중에),
         ' · '.join('%s(%d곳)' % (k, v) for k, v in 나중에.most_common(4)))

    # ── 2. 자료에 있는데 쪽이 없는가 (계약-12)
    print('[2] 자료에 있는 것이 모두 쪽이 되었는가')
    쪽만 = set(x for x in 있는쪽 if x.endswith('.html'))
    없는권역 = [r['id'] for r in d.권역들 if url.region(r['id']) not in 쪽만]
    탈('권역 쪽이 없음', len(없는권역), ' · '.join(없는권역[:5]))

    없는포인트쪽 = []
    for r in d.권역들:
        for 갈래 in ('낚시', '해루질'):
            if d.셈(r['id'], 갈래) and url.point_list(r['id'], 갈래) not in 쪽만:
                없는포인트쪽.append('%s %s' % (r['id'], 갈래))
    탈('포인트가 있는데 쪽이 없음', len(없는포인트쪽), ' · '.join(없는포인트쪽[:5]))

    # ── 3. 권역 ↔ 포인트 쪽이 서로 오가는가
    print('[3] 권역 쪽과 포인트 쪽이 서로 오가는가')
    못감 = []
    for r in d.권역들:
        권역길 = url.region(r['id'])
        if 권역길 not in 쪽만:
            continue
        권역글 = io.read(os.path.join(NEW, 권역길), default='')
        for 갈래 in ('낚시', '해루질'):
            if not d.셈(r['id'], 갈래):
                continue
            포인트길 = url.point_list(r['id'], 갈래)
            상대 = url.rel(권역길, 포인트길)
            if 상대 not in 권역글:
                못감.append('%s → %s' % (권역길, 포인트길))
            # 되돌아오는 길
            포인트글 = io.read(os.path.join(NEW, 포인트길), default='')
            되돌아 = url.rel(포인트길, 권역길)
            if 되돌아 not in 포인트글:
                못감.append('%s → %s' % (포인트길, 권역길))
    탈('오가는 길이 끊김', len(못감), ' · '.join(못감[:3]))

    print('')
    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
    if 문제:
        print('손볼 곳 %d가지: %s' % (len(문제), ' · '.join(문제)))
        if '--strict' in sys.argv:
            return 1
    else:
        print('쪽끼리 길이 모두 이어집니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
