# -*- coding: utf-8 -*-
"""검색엔진 눈에 어떻게 보이는지 봅니다. (주인 규칙 28)

왜 따로 보나
    다른 검사는 「자료와 링크가 성한가」를 봅니다.
    이것은 **검색엔진이 이 쪽을 어떻게 읽는가**를 봅니다.
    쪽이 멀쩡해도 제목이 겹치거나 설명이 없으면 검색에 안 뜹니다.

    주인 규칙 28 — 「검색에 관한 일은 언제나 네이버·구글 공식
    가이드에 맞춥니다. 짐작으로 하지 않습니다. 가이드에서 확인한
    것은 검사로 옮겨 둡니다 — 한 번 읽고 마는 것이 아니라,
    앞으로도 저절로 지켜지게 합니다」

가이드에서 확인해 지키는 것 (옛 사이트 tools/check-seo.py 에서 옮김)
    · 제목·설명에 **같은 말을 3회 이상 되풀이하지 않습니다** (반복은 불이익)
    · 설명은 제목과 같게 쓰지 않습니다
    · og:image 는 **쪽마다 다른 사진**이어야 합니다
    · 트위터 카드 태그도 함께 넣습니다 (가이드 권장)
    · 제목·설명은 쪽마다 고유해야 합니다
    · h1 은 쪽마다 하나입니다

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_seo.py
    python engine/check_seo.py --list     어느 쪽인지도 보여 줍니다
    python engine/check_seo.py --strict
"""
import os
import re
import sys
import glob
import html as _h
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 네이버 웹마스터 가이드 기준
제목최대 = 60          # 검색 결과에서 잘리지 않는 선
설명최대 = 80          # 네이버 가이드

보일것 = '--list' in sys.argv

# 검사 등급 (계약-21)
#   막음 — 검색에 해로운 것. 고쳐야 합니다
#   알림 — 살펴볼 만한 것. 막지 않습니다
막음, 알림 = [], []
탈 = collections.defaultdict(list)


def 적기(이름, 어디, 막는가=True):
    탈[이름].append(어디)
    (막음 if 막는가 else 알림).append(이름)


def 글자(s):
    return re.sub(r'\s+', ' ', _h.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def 되풀이(글, 몇번=3):
    """같은 낱말이 몇 번 넘게 나오는가. 반복 키워드는 불이익입니다."""
    낱말 = [w for w in re.findall(r'[가-힣A-Za-z]{2,}', 글) if len(w) >= 2]
    셈 = collections.Counter(낱말)
    return [w for w, n in 셈.items() if n >= 몇번]



def 알림파일(쪽들):
    """★ 검색엔진에게 알리는 파일이 **있는가**부터 봅니다 (2026-09-28)

    겪은 일: sitemap.xml · robots.txt · llms.txt 가 배포본에 통째로
    없었는데 아무 검사도 안 잡았습니다. check_assets.py 가

        사이트맵 = io.read(..., default='')

    로 읽어, 없으면 빈 글자가 되고 `<loc>` 이 하나도 없으니
    「사이트맵이 가리키는 쪽이 모두 있습니다」로 넘어갔습니다.
    **없는 것을 「다 맞다」고 세는 검사**였습니다.

    그대로 올렸으면 서버에는 옛 사이트맵이 남아, 주소가 바뀐 쪽을
    가리키며 검색엔진을 404 로 보냈을 것입니다.
    """
    print('[0] 검색엔진에게 알리는 파일')
    keep = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
    남길것 = set(k for k in (keep.get('남길것') or {})
                 if not k.startswith('_'))

    for 이름 in ('sitemap.xml', 'robots.txt', 'llms.txt'):
        # ★ **없음·빈 것·틀림을 가려 봅니다** (바깥 검수 9차 숙제 2)
        #   default='' 로 읽으면 「없음」과 「빈 것」이 같아집니다.
        상태, 글, 말 = io.파일상태(os.path.join(NEW, 이름), 가장작게=32)
        if 상태 != io.VALID:
            적기('검색 알림 파일이 %s' % 상태, '%s (%s)' % (이름, 말))
            print('  ✗ %-14s **%s** — %s' % (이름, 상태, 말))
            print('       engine/make_sitemap.py 가 만듭니다')
            continue
        if 글.startswith('﻿'):
            적기('BOM 이 붙음', 이름)
            print('  ✗ %-14s 맨 앞에 BOM 이 붙었습니다' % 이름)
            continue
        print('  · %-14s %6d바이트' % (이름, len(글.encode('utf-8'))))

    # ★ 검증판 표시가 남아 있으면 **운영에 나가면 안 됩니다** (2026-09-28)
    #
    #   engine/mark_stage.py 는 site/ 를 그 자리에서 고쳐 쪽마다
    #   noindex 를 박습니다. 검증판(/_stage/)에는 그래야 하지만,
    #   그대로 운영에 올리면 **416쪽이 통째로 검색에서 사라집니다.**
    #   되돌려도 다시 걷히는 데 몇 주가 걸립니다.
    #   실수 한 번이 너무 비싸므로 여기서 막습니다.
    검증판 = [os.path.relpath(p, NEW).replace(os.sep, '/')
              for p in 쪽들
              if 'badagaja:stage' in io.read(p, default='')]
    if 검증판:
        적기('검증판 표시가 남아 있음', '%d쪽' % len(검증판))
        print('  ✗ 검증판(_stage) 표시가 %d쪽에 남아 있습니다' % len(검증판))
        print('      운영에 이대로 올리면 검색에서 통째로 사라집니다.')
        print('      → python engine/build.py 로 다시 만드세요')

    맵 = io.꼭읽기(os.path.join(NEW, 'sitemap.xml'))
    if 맵:
        든것 = set()
        for m in re.finditer(r'<loc>([^<]+)</loc>', 맵):
            길 = m.group(1).split('badagaja.com', 1)[-1].lstrip('/')
            든것.add(길 or 'index.html')
        # 쪽마다 사이트맵에 있는가 — **빠지면 검색에서 사라집니다**
        # ★ **로봇에게 숨긴 쪽은 빼고 셉니다** (2026-10-06)
        #   robots noindex 가 박힌 쪽은 **일부러** 검색에 안
        #   내보내는 쪽입니다. 그런 쪽을 사이트맵에 넣으면
        #   「담지 말라면서 와서 보라」는 꼴이라 오히려 어긋납니다
        #   (네이버·구글 가이드). 방문 기록 쪽(stats.html)이
        #   그렇습니다 — 열쇠말을 넣어야 보이는 주인 전용 쪽입니다.
        빠진 = []
        for p in 쪽들:
            길 = os.path.relpath(p, NEW).replace(os.sep, '/')
            _글 = io.꼭읽기(p) or ''
            if 'noindex' in _글 and 'name="robots"' in _글:
                continue          # 일부러 숨긴 쪽입니다
            후보 = {길}
            if 길 == 'index.html':
                후보.add('index.html')
            elif 길.endswith('/index.html'):
                후보.add(길[:-len('index.html')])
            if not (후보 & 든것):
                빠진.append(길)
        if 빠진:
            적기('사이트맵에서 빠진 쪽', '%d개 (%s …)'
                 % (len(빠진), ' · '.join(빠진[:3])))
            print('  ✗ 사이트맵에 안 든 쪽 %d개 — 검색에서 사라집니다'
                  % len(빠진))
        else:
            print('  · 쪽 %d개가 모두 사이트맵에 있습니다' % len(쪽들))

    로봇 = io.꼭읽기(os.path.join(NEW, 'robots.txt'))
    for m in re.finditer(r'(?im)^\s*Sitemap:\s*(\S+)\s*$', 로봇):
        이름 = m.group(1).rsplit('/', 1)[-1]
        if not os.path.exists(os.path.join(NEW, 이름)) and 이름 not in 남길것:
            적기('robots 가 없는 사이트맵을 가리킴', 이름)
            print('  ✗ robots.txt 의 Sitemap: %s — 그런 파일이 없습니다'
                  % 이름)

    # ── AI 가 우리를 읽고 인용할 수 있는가 (2026-10-01) ──
    #
    #   ★ 바깥 검수가 OpenAI 공식 문서를 확인해 알려 준 것
    #
    #     OAI-SearchBot  챗지피티 **검색 결과에 노출**시키는 크롤러
    #     GPTBot         모델 **학습**용 크롤러
    #
    #   둘은 서로 **다릅니다.** 챗지피티 답에 인용되려면
    #   OAI-SearchBot 을 막지 않아야 합니다. GPTBot 만 열어
    #   두고 「AI 에 열어 두었다」고 여기면 안 됩니다.
    #
    #   주인 규칙 28 — 검색에 관한 일은 공식 가이드에 맞춥니다.
    #   가이드에서 확인한 것은 **검사로 옮겨** 저절로 지켜지게 합니다.
    AI봇 = [
        ('OAI-SearchBot', '챗지피티 검색 결과 노출', True),
        ('GPTBot', '챗지피티 학습', False),
        ('ChatGPT-User', '사람이 챗지피티로 우리 쪽을 열 때', False),
        ('ClaudeBot', '클로드', False),
        ('PerplexityBot', '퍼플렉시티', False),
        ('Google-Extended', '구글 AI', False),
    ]
    print('[5] AI 가 우리를 읽고 인용할 수 있는가')
    for 이름, 무엇, 꼭 in AI봇:
        m = re.search(r'(?im)^\s*User-agent:\s*%s\s*$\s*'
                      r'(Allow|Disallow):\s*(\S*)' % re.escape(이름), 로봇)
        if not m:
            글 = '안 적혀 있습니다 (기본은 모든 쪽 허용)'
            막나 = False
        else:
            막나 = (m.group(1).lower() == 'disallow'
                    and m.group(2).strip() == '/')
            글 = '%s: %s' % (m.group(1), m.group(2) or '/')
        if 꼭 and 막나:
            적기('%s 를 막고 있습니다' % 이름, 무엇)
            print('  ✗ %-16s %s — **%s**' % (이름, 글, 무엇))
            print('      → 막으면 챗지피티 답에 우리 쪽이 안 나옵니다.')
        else:
            print('  %s %-16s %s · %s'
                  % ('·' if not 막나 else '~', 이름, 글, 무엇))
    print('')


def main():
    쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('검색엔진 눈에 어떻게 보이는지 (주인 규칙 28)')
    print('  쪽 %d개' % len(쪽들))
    print('')

    알림파일(쪽들)

    제목별 = collections.defaultdict(list)
    설명별 = collections.defaultdict(list)
    사진별 = collections.defaultdict(list)

    for p in 쪽들:
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')

        # ── 제목
        m = re.search(r'<title>(.*?)</title>', s, re.S)
        제목 = 글자(m.group(1)) if m else ''
        if not 제목:
            적기('제목이 없음', 이름)
        else:
            제목별[제목].append(이름)
            if len(제목) > 제목최대:
                적기('제목이 %d자 넘음' % 제목최대,
                     '%s (%d자)' % (이름, len(제목)), 막는가=False)
            되 = 되풀이(제목)
            if 되:
                적기('제목에 같은 말 3번 이상',
                     '%s (%s)' % (이름, '·'.join(되[:2])))

        # ── 설명
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        설명 = 글자(m.group(1)) if m else ''
        if not 설명:
            적기('설명이 없음', 이름)
        else:
            설명별[설명].append(이름)
            if len(설명) > 설명최대:
                적기('설명이 %d자 넘음' % 설명최대,
                     '%s (%d자)' % (이름, len(설명)), 막는가=False)
            if 설명 == 제목:
                적기('설명이 제목과 같음', 이름)
            되 = 되풀이(설명)
            if 되:
                적기('설명에 같은 말 3번 이상',
                     '%s (%s)' % (이름, '·'.join(되[:2])))

        # ── h1
        h1 = re.findall(r'<h1[^>]*>', s)
        if not h1:
            적기('h1 이 없음', 이름)
        elif len(h1) > 1:
            적기('h1 이 둘 이상', '%s (%d개)' % (이름, len(h1)))

        # ── 공유 태그
        for 태그, 말 in (('og:title', 'og 제목'), ('og:description', 'og 설명'),
                         ('og:image', 'og 사진'), ('og:url', 'og 주소'),
                         ('og:type', 'og 갈래')):
            if not re.search(r'property="%s"' % re.escape(태그), s):
                적기('%s 빠짐' % 말, 이름)
        # 트위터 카드 (가이드 권장)
        if not re.search(r'name="twitter:card"', s):
            적기('트위터 카드 빠짐', 이름)

        m = re.search(r'property="og:image" content="([^"]+)"', s)
        if m:
            사진별[m.group(1)].append(이름)

        # ── 대표 주소
        m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if not m:
            적기('대표 주소 없음', 이름)

        # ── 화면 폭
        if not re.search(r'name="viewport"', s):
            적기('화면 폭 설정 없음', 이름)

        # ── 사진 대체글
        대체글없음 = [x for x in re.findall(r'<img[^>]*>', s)
                      if 'alt=' not in x]
        if 대체글없음:
            적기('대체글 없는 사진',
                 '%s (%d장)' % (이름, len(대체글없음)))

        # ── 구조화 자료
        if not re.search(r'application/ld\+json', s):
            적기('구조화 자료 없음', 이름, 막는가=False)

    # ── 쪽끼리 겹치는가
    for 제목, fs in 제목별.items():
        if len(fs) > 1:
            적기('제목이 겹침', '%s … %d쪽' % (제목[:30], len(fs)))
    for 설명, fs in 설명별.items():
        if len(fs) > 1:
            적기('설명이 겹침', '%s … %d쪽' % (설명[:30], len(fs)))
    for 주소, fs in 사진별.items():
        if len(fs) > 1:
            적기('og 사진이 여러 쪽에 겹침',
                 '%s … %d쪽' % (os.path.basename(주소), len(fs)),
                 막는가=False)

    if not 탈:
        print('쪽 %d개가 검색 기준을 모두 지킵니다.' % len(쪽들))
        return 0

    # 다른 검사기와 같은 꼴로 가릅니다 (계약-21)
    막을것 = [k for k in 탈 if k in 막음]
    알릴것 = [k for k in 탈 if k not in 막음]
    if 알림 and not 알릴것:
        알릴것 = sorted(set(알림))

    for 갈래, 목록 in (('손볼 곳', 막을것), ('살펴볼 것', 알릴것)):
        if not 목록:
            continue
        print('%s' % 갈래)
        for k in sorted(목록, key=lambda x: -len(탈[x])):
            v = 탈[k]
            print('  %s %-30s %4d쪽' % ('✗' if 갈래 == '손볼 곳' else '~',
                                         k, len(v)))
            if 보일것:
                for x in v[:6]:
                    print('        %s' % x)
                if len(v) > 6:
                    print('        … 그 밖 %d쪽' % (len(v) - 6))
        print('')

    if 막을것:
        if not 보일것:
            print('  어느 쪽인지 보려면 --list 를 붙이세요.')
        return 1 if '--strict' in sys.argv else 0
    # ★ 알림만 있을 때도 「지킵니다」라고 말합니다 (2026-09-27)
    #   전에는 아무 말도 안 해서, 판정 도구가 「통과 문구가 없다」며
    #   FAIL 로 셌습니다. **막을 것이 없으면 지킨 것입니다.**
    print('쪽 %d개가 검색 기준을 모두 지킵니다. '
          '(살펴볼 것 %d가지는 막지 않습니다)' % (len(쪽들), len(알릴것)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
