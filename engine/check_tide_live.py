# -*- coding: utf-8 -*-
"""운영에 올라간 물때가 **아직 쓸 만한지** 봅니다 (2026-10-14 주인 지시)

★ 왜 필요한가
  미리 받은 파일은 **날이 지나면 줄어듭니다.** 남은 날이 7일보다
  적어지면 화면이 **지금까지 쓰던 길(정부 API)로 되돌아갑니다.**
  손님에게 나빠지진 않지만, 그때부터 다시 느려질 수 있습니다.
  그래서 **언제 갈아 줘야 하는지**를 미리 알려 줍니다.

★ 내는 것
  권역마다  응답 · 남은 날 · 만료 예정일 · 로컬과 같은지
  그리고    **갱신 필요**(남은 날 14일 미만) / **폴백 임박**(7일 미만)

★ 쓰는 법
    python -m engine.check_tide_live
    python -m engine.check_tide_live --빠르게   (대표 5곳만)
"""
import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
로컬 = os.path.join(뿌리, 'data', 'tide')
운영 = 'https://badagaja.com/assets/tide/'

갱신경고 = 14      # 남은 날이 이보다 적으면 갈아 줄 때입니다
폴백임박 = 7       # 이보다 적으면 화면이 되돌아갑니다
대표 = ['ganghwa', 'taean', 'sinan', 'jejusi', 'pohang']


def 권역목록():
    sys.path.insert(0, 뿌리)
    from engine import build
    d = build.자료()
    return [(r['id'], (r.get('이름') or {}).get('ko') or r['id'])
            for r in d.권역들]


def 오늘엠디():
    t = datetime.now()
    return '%d/%d' % (t.month, t.day)


def 받기(권역):
    t0 = time.time()
    try:
        q = urllib.request.Request(
            운영 + 권역 + '.json',
            headers={'User-Agent': 'badagaja-live'})
        r = urllib.request.urlopen(q, timeout=25)
        몸 = r.read()
        return r.getcode(), 몸, time.time() - t0, None
    except Exception as e:
        return None, b'', time.time() - t0, type(e).__name__


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--빠르게', action='store_true')
    a = p.parse_args()

    오늘 = 오늘엠디()
    것 = 권역목록()
    if a.빠르게:
        것 = [x for x in 것 if x[0] in 대표]

    print('운영 물때를 봅니다 — 오늘 %s · %d곳' % (오늘, len(것)))
    print(운영)
    print('-' * 68)
    print('%-12s %4s %6s %5s %-9s %6s %s'
          % ('권역', '응답', '걸린s', '남은날', '만료', '같은가', '상태'))

    갱신 = []
    임박 = []
    못받음 = []
    다름 = []
    가장적은남은 = None
    가장빠른만료 = None

    for 권역, 이름 in 것:
        코드, 몸, 초, 탈 = 받기(권역)
        if 코드 != 200:
            print('%-12s %4s %6.2f   —        —      —    **못 받았습니다(%s)**'
                  % (이름, 코드 or '-', 초, 탈 or ''))
            못받음.append(이름)
            continue
        try:
            d = json.loads(몸.decode('utf-8', 'replace'))
        except Exception:
            print('%-12s  200 %6.2f   —        —      —    **글이 깨졌습니다**'
                  % (이름, 초))
            못받음.append(이름)
            continue

        날 = d.get('days') or []
        몇째 = -1
        for i, x in enumerate(날):
            if str(x.get('date')) == 오늘:
                몇째 = i
                break
        남은 = len(날) - 몇째 if 몇째 >= 0 else 0
        만료 = 날[-1].get('date') if 날 else '-'

        같은가 = '—'
        q = os.path.join(로컬, '%s.json' % 권역)
        if os.path.isfile(q):
            로컬해시 = hashlib.sha256(
                io.open(q, 'rb').read()).hexdigest()
            운영해시 = hashlib.sha256(몸).hexdigest()
            같 = (로컬해시 == 운영해시)
            같은가 = '같음' if 같 else '**다름**'
            if not 같:
                다름.append(이름)

        상태 = '넉넉합니다'
        if 몇째 < 0:
            상태 = '**오늘이 없습니다 — 폴백 중**'
            임박.append(이름)
        elif 남은 < 폴백임박:
            상태 = '**폴백 임박**'
            임박.append(이름)
        elif 남은 < 갱신경고:
            상태 = '갈아 줄 때입니다'
            갱신.append(이름)

        if 가장적은남은 is None or 남은 < 가장적은남은:
            가장적은남은 = 남은
            가장빠른만료 = 만료

        print('%-12s  200 %6.2f %5d %-9s %6s  %s'
              % (이름, 초, 남은, 만료, 같은가, 상태))

    print('-' * 68)
    if 가장적은남은 is not None:
        t = datetime.now()
        폴백날 = t + timedelta(days=max(0, 가장적은남은 - 폴백임박 + 1))
        print('가장 적게 남은 곳 **%d일** (만료 %s)'
              % (가장적은남은, 가장빠른만료))
        print('→ 아무것도 안 하면 **%d/%d 무렵부터 폴백**입니다'
              % (폴백날.month, 폴백날.day))

    if 못받음:
        print('\n✗ 못 받은 곳 %d곳: %s' % (len(못받음), ' · '.join(못받음)))
    if 다름:
        print('\n~ 운영과 내 것이 다른 곳 %d곳: %s'
              % (len(다름), ' · '.join(다름[:8])))
        print('  (내가 새로 받아 두고 아직 안 올렸다면 당연합니다)')
    if 임박:
        print('\n★ **폴백 임박 %d곳** — %s'
              % (len(임박), ' · '.join(임박[:8])))
        print('  지금 갈아 주십시오. 그대로 두면 정부 API 를 다시 거칩니다.')
    elif 갱신:
        print('\n~ 갈아 줄 때가 된 곳 %d곳 — %s'
              % (len(갱신), ' · '.join(갱신[:8])))

    if not 못받음 and not 임박:
        print('\n★ 운영 물때가 **멀쩡합니다.**')

    return 1 if (못받음 or 임박) else 0


if __name__ == '__main__':
    sys.exit(main())
