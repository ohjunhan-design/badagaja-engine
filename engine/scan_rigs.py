# -*- coding: utf-8 -*-
"""**모은 자료에서 채비 값을 뽑습니다** (2026-09-30 주인 지시)

주인 말씀 — 「우리 사이트에 디비로 사용하자」
           「설명은 너가 재가공해서 알기쉽게 요약해주고
             낚시 채비그림은 최대한 활용을 하자」

★ 이름이 `scan_` 인 까닭 (2026-09-30)

    처음에 `extract_rigs.py` 로 지었더니 check_contracts 가
    **「옮기는 도구」로 보고** 계약-26·27 어김을 냈습니다
    (`extract_*.py` 는 자료를 `data/` 로 옮기는 도구라는 약속입니다).

    이것은 **조사 도구**입니다. `data-private/` 바깥에 아무것도
    쓰지 않고, 정기 갱신 차례에도 들어가지 않습니다.
    그래서 이름을 `scan_` 으로 바꿨습니다.

★ 무엇을 뽑고 무엇을 안 뽑나

    뽑습니다 — **값(사실)**
      「원줄 3~4호」 「목줄 플로로카본 2~3호 1m」 「감성돔바늘 4~6호」
      이런 것은 **사실**이라 저작물이 아닙니다. 누가 적어도 같습니다.

    안 뽑습니다 — **문장**
      설명 글은 남의 저작물입니다. 값만 가져오고
      **설명은 제가 처음부터 다시 씁니다.**

★ 뽑은 것은 어디로 가나

    `data-private/뽑은채비.json` 에 **먼저 쌓습니다.**
    바로 `data/raw/rigs.json` 에 넣지 않습니다 —
    사람이 보고 고른 것만 옮깁니다. 기계가 잘못 읽을 수 있으니까요.

쓰는 법
    python engine/scan_rigs.py               모두 훑습니다
    python engine/scan_rigs.py --말 감성돔   하나만
"""
import argparse
import glob
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(여기)
sys.path.insert(0, ROOT)

from engine import io                                     # noqa: E402

읽을곳 = os.path.join(ROOT, 'data-private', '지식백과')
갈곳 = os.path.join(ROOT, 'data-private', '뽑은채비.json')

# ── 값을 알아보는 자 ──────────────────────────────────────
#
#   채비도와 본문에 이런 꼴로 적혀 있습니다.
#     「원줄 : 3~4호」 「목줄 : 플로로카본 2~3호 1m」
#     「감성돔바늘 4~6호」 「구멍봉돌 10~20호」
#
#   ★ **너무 넓게 잡지 않습니다.** 「3호」 하나만 보고 무엇의 3호인지
#     모르면 값이 아닙니다. 부품 이름이 바로 앞에 있을 때만 뽑습니다.
부품말 = [
    '낚싯대', '낚시대', '릴',
    '원줄', '목줄', '쇼크리더',
    '구멍찌', '막대찌', '수중찌', '찌',
    '면사매듭', '반달구슬', '반원구슬', '구슬',
    '쿠션고무', '완충고무', '찌멈춤', '엉킴방지',
    '맨도래', '도래', '핀도래',
    '봉돌', '구멍봉돌', '좁쌀봉돌', '고리봉돌', '지그헤드',
    '바늘', '묶음바늘', '가지바늘',
    '에기', '웜', '미끼',
]
# 호수·길이·무게를 적는 꼴
값꼴 = (r'(?:[0-9]+(?:\.[0-9]+)?\s*(?:~|-|∼)\s*)?'
        r'[0-9]+(?:\.[0-9]+)?\s*(?:호|g|cm|mm|m|B|파운드|lb|번)')


def 값뽑기(글):
    """부품 이름 바로 뒤에 붙은 값을 뽑습니다."""
    끝 = []
    for 말 in 부품말:
        차림 = (r'%s\s*[:：]?\s*((?:[가-힣A-Za-z]+\s*)?%s(?:\s*[~\-∼]\s*%s)?)'
                % (re.escape(말), 값꼴, 값꼴))
        for m in re.finditer(차림, 글):
            값 = re.sub(r'\s+', ' ', m.group(1)).strip()
            if (말, 값) not in 끝:
                끝.append((말, 값))
    return 끝


def 갈래알기(이름, 글):
    """선상인지 갯바위·방파제인지 가립니다 (주인 규칙 10).

    선상낚시는 **싣지 않습니다.** 뽑아 두되 표시해 둡니다.
    """
    섞 = 이름 + ' ' + 글[:600]
    if re.search(r'선상|배낚시|지깅|외수질|심해|보트', 섞):
        return '선상'
    if re.search(r'민물|붕어|배스|쏘가리|메기|가물치|떡밥|계류|송어|향어',
                 섞):
        return '민물'
    return '바다'


def main():
    보 = argparse.ArgumentParser()
    보.add_argument('--말', default='')
    자 = 보.parse_args()

    파일들 = sorted(glob.glob(os.path.join(읽을곳, '*.txt')))
    파일들 = [p for p in 파일들
              if not os.path.basename(p).startswith('_')]
    if not 파일들:
        print('모은 글이 없습니다 — 먼저 engine/fetch_terms.py --받기')
        return 2

    끝 = []
    for p in 파일들:
        글 = io.read(p, default='')
        이름 = os.path.splitext(os.path.basename(p))[0]
        찾은말 = ''
        m = re.search(r'^찾은말: (.*)$', 글, re.M)
        if m:
            찾은말 = m.group(1).strip()
        if 자.말 and 찾은말 != 자.말:
            continue
        출처 = ''
        m = re.search(r'^출처: (.*)$', 글, re.M)
        if m:
            출처 = m.group(1).strip()
        값들 = 값뽑기(글)
        if not 값들:
            continue
        끝.append({
            '이름': 이름,
            '찾은말': 찾은말,
            '출처': 출처,
            '갈래': 갈래알기(이름, 글),
            '값': [{'부품': a, '값': b} for a, b in 값들],
        })

    io.write(갈곳, json.dumps(끝, ensure_ascii=False, indent=2))

    셈 = {}
    for 것 in 끝:
        셈[것['갈래']] = 셈.get(것['갈래'], 0) + 1
    print('값이 있는 글 %d편' % len(끝))
    for 갈, n in sorted(셈.items()):
        print('  %-4s %d편' % (갈, n))
    print('  모두 값 %d개' % sum(len(x['값']) for x in 끝))
    print('')
    print('  %s 에 쌓았습니다.' % 갈곳)
    print('  ★ 바로 쓰지 않습니다. 사람이 보고 고른 것만 rigs.json 으로 옮깁니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
