# -*- coding: utf-8 -*-
"""**네이버 지식백과에서 낚시 자료를 모읍니다** (2026-09-30 주인 지시)

주인 말씀 — 「좋은 자료를 찾았어 네이버 지식백과니까 기준점일 이걸로 잡고 가자」
           「어종별 채비법과 잡는방법 미끼 등등 많은 자료가 있어
             전수해서 데이터 확보해」

★ 모으는 것과 싣는 것은 다릅니다 — 이것이 가장 중요합니다

    지식백과 글은 『바다낚시 첫걸음』 같은 **책의 저작물**입니다.
    그대로 사이트에 옮기면 안 됩니다.

      · 모으기 — `data-private/지식백과/` 에만 둡니다.
        이 폴더는 **배포에서 빠집니다** (주인 규칙 11).
      · 싣기  — 값(호수·길이·시기 같은 **사실**)만 씁니다.
        **사실은 저작물이 아닙니다.** 문장은 우리 말로 다시 씁니다.

    그래서 이 도구는 `data-private/` 바깥에 아무것도 쓰지 않습니다.

★ 예의를 지킵니다

    한 쪽을 받을 때마다 쉬었다 갑니다. 남의 서버를 두드리는 일이니
    빠르게 긁지 않습니다. `--쉬는시간` 으로 늘릴 수 있습니다.

쓰는 법
    python engine/fetch_terms.py --목록           찾을 말로 항목만 모읍니다
    python engine/fetch_terms.py --받기           본문까지 받습니다
    python engine/fetch_terms.py --받기 --더      이미 받은 것도 다시 받습니다
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)
sys.path.insert(0, ROOT)

from engine import io                                     # noqa: E402

모을곳 = os.path.join(ROOT, 'data-private', '지식백과')
뿌리 = 'https://terms.naver.com'
차림 = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# ★ 찾을 말 — **갯바위·방파제 낚시**에 쓰는 것만 모읍니다 (주인 규칙 10)
#   민물·선상 것도 검색에 걸리지만, 쓰기 전에 갈라냅니다.
찾을말 = [
    '낚시 채비', '바다낚시 채비', '찌낚시', '원투낚시', '루어낚시',
    '감성돔', '벵에돔', '참돔', '농어', '우럭', '볼락', '광어',
    '숭어', '학꽁치', '전갱이', '고등어', '삼치', '갈치',
    '무늬오징어', '갑오징어', '주꾸미', '문어',
    '낚싯줄', '낚싯바늘', '봉돌', '찌', '도래', '미끼',
    '갯바위낚시', '방파제낚시', '민장대', '에기', '지그헤드',
]


def 주소다듬기(주소):
    """주소에 든 **한글을 부호로 바꿉니다.**

    지식백과 주소에는 한글이 그대로 들어 있습니다
    (`/낚시-등산-레포츠/카드-채비-낚시-67J6…`).
    그대로 보내면 「'ascii' codec can't encode」로 죽습니다.
    """
    쪼갬 = urllib.parse.urlsplit(주소)
    return urllib.parse.urlunsplit((
        쪼갬.scheme, 쪼갬.netloc,
        urllib.parse.quote(쪼갬.path, safe='/-_.~'),
        urllib.parse.quote(쪼갬.query, safe='=&%'),
        쪼갬.fragment))


def 받아오기(주소, 쉬는시간=1.2):
    """한 쪽을 받아 옵니다. 실패하면 빈 글자를 돌려줍니다."""
    주소 = 주소다듬기(주소)
    무리 = urllib.request.Request(주소, headers={
        'User-Agent': 차림,
        'Accept-Language': 'ko-KR,ko;q=0.9',
    })
    try:
        with urllib.request.urlopen(무리, timeout=25) as 답:
            글 = 답.read().decode('utf-8', errors='replace')
    except Exception as e:
        print('  ✗ 못 받았습니다 — %s' % str(e)[:60])
        글 = ''
    time.sleep(쉬는시간)           # 남의 서버에 예의를 지킵니다
    return 글


def 항목찾기(말, 쉬는시간=1.2):
    """찾을 말 하나로 항목 목록을 모읍니다."""
    주소 = ('%s/search?query=%s'
            % (뿌리, urllib.parse.quote(말)))
    글 = 받아오기(주소, 쉬는시간)
    끝 = []
    for m in re.finditer(r'class="card_title"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                         글, re.S):
        길, 안 = m.group(1), re.sub(r'<[^>]+>', '', m.group(2))
        이름 = html.unescape(안).strip()
        if 이름 and 길.startswith('/'):
            끝.append({'이름': 이름, '길': 길, '찾은말': 말})
    return 끝


def 본문뽑기(글):
    """받은 쪽에서 **본문만** 꺼냅니다.

    지식백과는 머리글·메뉴·광고가 앞뒤로 붙습니다.
    본문은 제목이 두 번째로 나오는 자리부터입니다.
    """
    출처 = ''
    m = re.search(r'"content_source_name":"([^"]*)"', 글)
    if m:
        출처 = m.group(1)
    제목 = ''
    m = re.search(r'"content_title":"([^"]*)"', 글)
    if m:
        제목 = m.group(1)

    몸 = 글
    # 머리글 덩이를 걷어 냅니다
    표 = 'ⓒ NAVER Corp.'
    if 표 in 몸:
        몸 = 몸[몸.index(표) + len(표):]
    몸 = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', 몸, flags=re.S)
    몸 = re.sub(r'<br\s*/?>', '\n', 몸)
    몸 = re.sub(r'</(p|div|li|h\d|tr|td)>', '\n', 몸)
    몸 = re.sub(r'<[^>]+>', '', 몸)
    몸 = html.unescape(몸)
    몸 = re.sub(r'[ \t]+', ' ', 몸)
    몸 = re.sub(r'\n\s*\n+', '\n', 몸).strip()
    # 꼬리(관련 항목·저작권 안내)를 자릅니다
    for 끝표 in ('관련 이미지', '출처', '위 이미지', '[네이버 지식백과]'):
        if 끝표 in 몸[200:]:
            몸 = 몸[:200 + 몸[200:].index(끝표)]
            break
    return 제목, 출처, 몸.strip()


def 파일이름(이름):
    s = re.sub(r'[^0-9A-Za-z가-힣 ]+', '', 이름).strip()
    return (s or '이름없음')[:50]


def main():
    보 = argparse.ArgumentParser()
    보.add_argument('--목록', action='store_true')
    보.add_argument('--받기', action='store_true')
    보.add_argument('--더', action='store_true', help='이미 받은 것도 다시')
    보.add_argument('--쉬는시간', type=float, default=1.2)
    보.add_argument('--말', default='', help='이 말 하나만 찾습니다')
    자 = 보.parse_args()

    # io.write 가 폴더를 알아서 만듭니다 (계약-13)
    색인길 = os.path.join(모을곳, '_색인.json')

    말들 = [자.말] if 자.말 else 찾을말

    if 자.목록 or not os.path.exists(색인길):
        print('항목을 모읍니다 — 찾을 말 %d개' % len(말들))
        모은것, 본길 = [], set()
        for i, 말 in enumerate(말들, 1):
            것들 = 항목찾기(말, 자.쉬는시간)
            새것 = [x for x in 것들 if x['길'] not in 본길]
            for x in 새것:
                본길.add(x['길'])
            모은것 += 새것
            print('  %2d/%d  %-14s %2d개 (새것 %d)'
                  % (i, len(말들), 말, len(것들), len(새것)))
        io.write(색인길, json.dumps(모은것, ensure_ascii=False, indent=2))
        print('')
        print('  항목 %d개를 모았습니다 — %s' % (len(모은것), 색인길))

    if not 자.받기:
        return 0

    목록 = json.loads(io.read(색인길, default='[]'))
    print('')
    print('본문을 받습니다 — %d개' % len(목록))
    받은것, 건너뛴것, 못받은것 = 0, 0, 0
    for i, 것 in enumerate(목록, 1):
        갈곳 = os.path.join(모을곳, 파일이름(것['이름']) + '.txt')
        if os.path.exists(갈곳) and not 자.더:
            건너뛴것 += 1
            continue
        글 = 받아오기(뿌리 + 것['길'], 자.쉬는시간)
        if not 글:
            못받은것 += 1
            continue
        제목, 출처, 몸 = 본문뽑기(글)
        if len(몸) < 120:
            print('  ~ %s — 본문이 너무 짧습니다' % 것['이름'])
            못받은것 += 1
            continue
        io.write(갈곳, '제목: %s\n출처: %s\n주소: %s\n찾은말: %s\n%s\n\n%s\n'
                 % (제목 or 것['이름'], 출처, 뿌리 + 것['길'],
                    것['찾은말'], '-' * 60, 몸))
        받은것 += 1
        if 받은것 % 10 == 0:
            print('  %d개째…' % 받은것)
    print('')
    print('  받은 것 %d · 건너뛴 것 %d · 못 받은 것 %d'
          % (받은것, 건너뛴것, 못받은것))
    print('  모은 곳 — %s' % 모을곳)
    print('')
    print('  ★ 이 글은 **남의 저작물**입니다. 사이트에 그대로 옮기지 않습니다.')
    print('    값(호수·길이·시기)만 쓰고 문장은 우리 말로 다시 씁니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
