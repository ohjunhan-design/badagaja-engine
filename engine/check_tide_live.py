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

from engine import kst
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
    # ★ **한국 날짜**로 못 박습니다 (2026-10-14 · engine/kst.py)
    #   판정은 우분투(UTC)에서 돕니다. `now()` 를 그냥 쓰면
    #   한국 새벽에 하루 어긋나 「폴백 임박」을 잘못 알립니다.
    return kst.오늘키()


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


def 서버상태():
    """★ 서버가 적어 둔 `_status.json` 을 읽습니다.

    57번 두드리지 않고 **한 번**에 전체 상태를 봅니다.
    자가 갱신이 켜진 뒤로는 이쪽이 더 정확합니다 — 서버가
    방금 바꾼 것까지 들어 있습니다.
    """
    주소 = 'https://badagaja.com/api/tide-refresh.php?status=1'
    try:
        q = urllib.request.Request(
            주소, headers={'User-Agent': 'badagaja-live'})
        d = json.loads(urllib.request.urlopen(q, timeout=25)
                       .read().decode('utf-8', 'replace'))
    except Exception as e:
        print('서버 상태를 못 읽었습니다 — %s' % type(e).__name__)
        return 1
    if not d:
        print('서버가 아직 아무것도 적지 않았습니다 (한 걸음도 안 돌았습니다)')
        return 0

    목표 = d.get('목표일수') or 60
    권역 = d.get('권역') or {}
    마지막 = d.get('마지막걸음')
    print('서버가 적어 둔 물때 상태 — 목표 %d일 · %d곳'
          % (목표, len(권역)))
    if 마지막:
        지난 = int(time.time()) - int(마지막)
        print('마지막 걸음: %d분 전 · %s'
              % (지난 // 60, d.get('마지막결과') or '-'))
    print('-' * 56)

    줄 = sorted(권역.items(), key=lambda kv: (kv[1].get('남은') or 0,
                                              -(kv[1].get('빈') or 0)))
    가장적은 = None
    빈합 = 0
    모자람합 = 0
    for 이름, v in 줄:
        남 = v.get('남은') or 0
        빈 = v.get('빈') or 0
        빈합 += 빈
        모자람합 += max(0, 목표 - 남)
        if 가장적은 is None or 남 < 가장적은:
            가장적은 = 남
        표 = ''
        if 남 < 폴백임박:
            표 = '  ← **폴백 임박**'
        elif 남 < 갱신경고:
            표 = '  ← 갈아 줄 때'
        print('   %-14s 남은 %2d일 · 빈 %2d%s' % (이름, 남, 빈, 표))

    print('-' * 56)
    print('가장 적게 남은 곳 **%s일** · 빈 날 합계 %d · 모자란 날 합계 %d'
          % (가장적은, 빈합, 모자람합))
    if 가장적은 is not None:
        남을날 = max(0, 가장적은 - 폴백임박 + 1)
        그날 = kst.지금() + timedelta(days=남을날)
        print('→ 아무것도 안 하면 **%d/%d 무렵부터 폴백**입니다'
              % (그날.month, 그날.day))
    # ★ 감독실이 그대로 옮겨 적을 수 있는 한 줄
    print()
    print('[한 줄 요약] 물때 %d곳 · 가장 적은 곳 %s일 · 빈 날 %d개 · %s'
          % (len(권역), 가장적은, 빈합,
             '넉넉합니다' if (가장적은 or 0) >= 갱신경고
             else '**갈아 줄 때입니다**'))
    return 1 if (가장적은 is not None and 가장적은 < 폴백임박) else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--빠르게', action='store_true')
    p.add_argument('--서버', action='store_true',
                   help='서버가 적어 둔 상태(_status.json)만 읽습니다')
    a = p.parse_args()

    if a.서버:
        return 서버상태()

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
        t = kst.지금()
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
