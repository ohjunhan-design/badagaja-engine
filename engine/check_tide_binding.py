# -*- coding: utf-8 -*-
"""권역마다 **물때가 정말 다른지** 실제 서버에서 확인합니다 (2026-10-02).

★ 왜 만드나
  바깥 검수가 캡처를 보고 지적했습니다 —
    「태안·신안·고흥·부산 동부·포항·강릉의 간·만조 시각이 캡처상
      **전부 04:54 / 11:38 / 17:26 / 23:52 로 동일**합니다.
      관측소는 서로 다른데 시간은 모두 같습니다. 이게 테스트
      fixture 가 아니라 실제 생성 결과라면 **배포 차단 문제**입니다」

  제 캡처가 `_fake_tide.py` 의 가짜 값이었던 것이 맞습니다.
  하지만 **「가짜였습니다」로 끝내면 안 됩니다.** 실제 서버가
  권역마다 다른 값을 주는지 **재서 보여야** 합니다.

  주인 기억 — 「증거가 완료 조건 — 「내가 맞다고 생각한다」가
  아니라 「재현되고 검사기가 잡는다」」

★ 이 검사는 **인터넷을 씁니다.** 그래서 판정에 넣지 않습니다.
  배포 전에 손으로 돌려 표를 냅니다.

쓰는 법
  python engine/check_tide_binding.py              # 여섯 권역
  python engine/check_tide_binding.py --all        # 57권역
"""
import io
import json
import os
import sys
import time
import urllib.request

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

막음, 알림 = [], []                 # 계약-21

주소 = 'https://badagaja.com/api/tide-cache.php?region=%s'
기본 = ['taean', 'sinan', 'goheung', 'busaneast', 'pohang', 'gangneung']


def 받기(권역):
    try:
        req = urllib.request.Request(
            주소 % 권역, headers={'User-Agent': 'badagaja-check/1.0'})
        with urllib.request.urlopen(req, timeout=70) as r:
            return json.loads(r.read().decode('utf-8')), None
    except Exception as e:                            # noqa: BLE001
        return None, str(e)[:70]


def main():
    from engine.data import 자료
    d = 자료()

    볼것 = ([r['id'] for r in d.권역들] if '--all' in sys.argv else 기본)
    print()
    print('  권역마다 물때가 정말 다른가 — **실제 서버**에서 받습니다')
    print('  %s' % (주소 % '{권역}'))
    print()
    print('  %-12s %-10s %-12s %s'
          % ('권역', '자료의 관측소', '서버 관측소', '오늘 간·만조'))
    print('  ' + '-' * 76)

    본것, 지문들 = [], {}
    for 권역 in 볼것:
        r = d.권역(권역) or {}
        이름 = (r.get('이름') or {}).get('ko') or 권역
        적힌관 = (r.get('물때관측소') or {}).get('이름') or '—'
        j, 탈 = 받기(권역)
        if not j:
            알림.append('%s — 못 받았습니다 (%s)' % (이름, 탈))
            print('  %-12s %-10s %-12s ! %s' % (이름, 적힌관, '—', 탈))
            continue
        서버관 = (j.get('point') or j.get('station') or '—')
        들 = ((j.get('days') or [{}])[0].get('events') or [])
        글 = ' · '.join('%s %s' % (e.get('type', ''), e.get('time', ''))
                        for e in 들[:4]) or '(없음)'
        print('  %-12s %-10s %-12s %s' % (이름, 적힌관, 서버관, 글))
        본것.append((이름, 적힌관, 서버관, 글))
        지문들.setdefault(글, []).append(이름)
        time.sleep(1.2)             # 서버가 처음 받으면 느립니다

    print()
    if not 본것:
        알림.append('한 곳도 못 받았습니다 — 인터넷이나 서버를 확인하세요')
        print('  □ 한 곳도 못 받았습니다. **틀린 것이 아니라 못 잰 것입니다**')
        print('')
        print('NOT_TESTED')
        return 4 if '--strict' in sys.argv else 0

    같은것 = {k: v for k, v in 지문들.items() if len(v) > 1}
    print('  받은 곳 %d · 서로 다른 물때 %d가지'
          % (len(본것), len(지문들)))
    if 같은것:
        for 글, 곳들 in 같은것.items():
            # 바다가 가까우면 실제로 같을 수 있습니다 — 알림입니다
            알림.append('%s 가 같은 물때입니다 (%s)'
                        % (' · '.join(곳들), 글[:30]))
            print('  ! %s — 같은 값입니다' % ' · '.join(곳들))
        print('    가까운 바다는 실제로 같을 수 있습니다. 관측소가')
        print('    **같은 곳**이면 당연하고, 다르면 살펴봐야 합니다.')
    else:
        print('  · 모두 다릅니다 — 권역마다 제 관측소 값을 씁니다')

    # 자료에 적힌 관측소와 서버가 쓰는 관측소가 어긋나는가
    어긋 = [(a, b, c) for a, b, c, _ in 본것
            if b not in ('—', '') and c not in ('—', '') and b != c]
    if 어긋:
        for 이름, 적힌, 서버 in 어긋:
            막음.append('%s — 자료는 %s, 서버는 %s' % (이름, 적힌, 서버))
        print('')
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:10]:
            print('  ✗ %s' % t)
        print('  **자료와 서버가 다른 관측소를 가리킵니다.**')
        print('  쪽에는 자료의 이름이 적히는데 숫자는 서버 것입니다.')
        return 1
    print('  · 자료에 적힌 관측소와 서버가 쓰는 관측소가 같습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
