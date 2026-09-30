# -*- coding: utf-8 -*-
"""**지식백과 채비 그림을 모읍니다** (2026-09-30 주인 지시)

주인 말씀 — 「어종별로 하고 채비이미지 엄청 많아」

★ 왜 그림까지 모으나

    글만으로는 **부품이 어떻게 생겼고 어떤 차례로 붙는지** 알 수 없습니다.
    오늘만 해도 막대찌를 줄에 꿰어 그렸다가 주인이 보내 주신 사진을
    보고서야 고쳤습니다. 그림이 있으면 그런 잘못을 미리 막습니다.

★ 모으는 것과 싣는 것은 다릅니다 — 가장 중요합니다

    지식백과 그림은 **책에 실린 남의 저작물**입니다.
    사이트에 옮기면 안 됩니다.

      · 모으기 — `data-private/지식백과-그림/` 에만 둡니다.
        이 폴더는 **배포에서 빠집니다** (주인 규칙 11).
      · 쓰기  — **보고 우리가 다시 그립니다.** 그림 자체는 안 씁니다.
        사이트에 나가는 채비도는 전부 engine/art.py 가 그린 것입니다.

★ 어종별로 갈라 둡니다

    `data-private/지식백과-그림/감성돔/…` 처럼 찾은 말로 폴더를 나눕니다.
    나중에 「감성돔 채비를 그릴 때 무엇을 봤나」를 되짚을 수 있습니다.

쓰는 법
    python engine/fetch_terms_img.py                    모두
    python engine/fetch_terms_img.py --말 감성돔        하나만
    python engine/fetch_terms_img.py --최대 5           쪽마다 5장까지
"""
import argparse
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

모을곳 = os.path.join(ROOT, 'data-private', '지식백과-그림')
색인길 = os.path.join(ROOT, 'data-private', '지식백과', '_색인.json')
뿌리 = 'https://terms.naver.com'
차림 = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def 주소다듬기(주소):
    쪼갬 = urllib.parse.urlsplit(주소)
    return urllib.parse.urlunsplit((
        쪼갬.scheme, 쪼갬.netloc,
        urllib.parse.quote(쪼갬.path, safe='/-_.~'),
        urllib.parse.quote(쪼갬.query, safe='=&%'),
        쪼갬.fragment))


def 받아오기(주소, 쉬는시간=1.0, 날것=False):
    무리 = urllib.request.Request(주소다듬기(주소), headers={
        'User-Agent': 차림,
        'Accept-Language': 'ko-KR,ko;q=0.9',
        'Referer': 뿌리 + '/',
    })
    try:
        with urllib.request.urlopen(무리, timeout=25) as 답:
            것 = 답.read()
        끝 = 것 if 날것 else 것.decode('utf-8', errors='replace')
    except Exception as e:
        print('  ✗ 못 받았습니다 — %s' % str(e)[:60])
        끝 = b'' if 날것 else ''
    time.sleep(쉬는시간)
    return 끝


def 그림주소들(글):
    """쪽에서 그림 주소를 꺼냅니다.

    ★ 자바스크립트 안에 **역슬래시가 붙은 채** 들어 있는 것이
      섞입니다. 그대로 두면 같은 그림을 두 번 받습니다.
      꼬리의 역슬래시와 물음표 뒤를 잘라 **같은 것을 하나로** 봅니다.
    """
    본것 = []
    for g in re.findall(r'https://nterms-phinf\.pstatic\.net/[^"\'\s\\]+', 글):
        g = g.split('?')[0].rstrip('\\')
        if not re.search(r'\.(jpg|jpeg|png|gif)$', g, re.I):
            continue
        if g not in 본것:
            본것.append(g)
    return 본것


def 이름다듬기(이름):
    s = re.sub(r'[^0-9A-Za-z가-힣 ]+', '', 이름).strip()
    return (s or '이름없음')[:40]


def main():
    보 = argparse.ArgumentParser()
    보.add_argument('--말', default='', help='이 찾은말 것만')
    보.add_argument('--최대', type=int, default=12, help='쪽마다 몇 장까지')
    보.add_argument('--쉬는시간', type=float, default=0.8)
    보.add_argument('--더', action='store_true', help='이미 받은 것도 다시')
    자 = 보.parse_args()

    목록 = json.loads(io.read(색인길, default='[]'))
    if not 목록:
        print('색인이 없습니다 — 먼저 engine/fetch_terms.py --목록 을 돌리세요')
        return 2
    if 자.말:
        목록 = [x for x in 목록 if x['찾은말'] == 자.말]

    print('지식백과 그림을 모읍니다 (data-private/ 에만 둡니다)')
    print('  쪽 %d개 · 쪽마다 최대 %d장' % (len(목록), 자.최대))
    print('')

    받은것, 건너뛴것, 못받은것 = 0, 0, 0
    for i, 것 in enumerate(목록, 1):
        칸 = os.path.join(모을곳, 이름다듬기(것['찾은말']))
        머리 = 이름다듬기(것['이름'])
        # 이미 받은 것이 있으면 건너뜁니다
        있는것 = []
        if os.path.isdir(칸):
            있는것 = [x for x in os.listdir(칸) if x.startswith(머리 + '-')]
        if 있는것 and not 자.더:
            건너뛴것 += 1
            continue
        글 = 받아오기(뿌리 + 것['길'], 자.쉬는시간)
        if not 글:
            못받은것 += 1
            continue
        주소들 = 그림주소들(글)[:자.최대]
        for n, 그림 in enumerate(주소들, 1):
            뒤 = os.path.splitext(그림)[1].lower() or '.jpg'
            갈곳 = os.path.join(칸, '%s-%02d%s' % (머리, n, 뒤))
            if os.path.exists(갈곳) and not 자.더:
                continue
            몸 = 받아오기(그림, 자.쉬는시간 * 0.4, 날것=True)
            if len(몸) < 1500:          # 너무 작으면 아이콘입니다
                continue
            io.write_binary(갈곳, 몸)
            받은것 += 1
        if i % 20 == 0:
            print('  %d/%d 쪽째 · 그림 %d장' % (i, len(목록), 받은것))

    print('')
    print('  받은 그림 %d장 · 건너뛴 쪽 %d · 못 받은 쪽 %d'
          % (받은것, 건너뛴것, 못받은것))
    print('  모은 곳 — %s' % 모을곳)
    print('')
    print('  ★ 이 그림은 **남의 저작물**입니다. 사이트에 옮기지 않습니다.')
    print('    보고 우리가 다시 그립니다 (engine/art.py).')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
