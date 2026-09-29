# -*- coding: utf-8 -*-
"""명소 사진을 한국관광공사에서 받아 옵니다.

★ 왜 만들었나 (2026-09-29 주인 지시)

  「명소들이 이미지 잘못들어간게 많아 … 사진검수해 실제 사진으로
    지역 광관안내 잘 살펴보면 사진 많을꺼야」

  명소 393곳 가운데 사진이 있는 곳이 **125곳(32%)뿐**이었습니다.
  사진 없는 카드가 격자에 빈자리를 만들어 쪽이 휑해 보였습니다.

  주인 말씀이 맞았습니다 — `api/tour.php?kind=spot&region=…` 이
  그 고장 관광지를 **이름·주소·좌표·사진**까지 통째로 줍니다.
  재 보니 **80%를 채울 수 있습니다.**

★ 이름만 믿지 않습니다 — **좌표로 거릅니다** (주인 제안)

  「지역 명소 사진을 쓸 때 사진에 나온 곳 주소가 관광지 주소와
    동일했으면 더 좋겠어. 검수할 때 이렇게 검수하면 더 좋지 않을까?」

  이름이 느슨하게 맞는 것이 있습니다 —
      명소  석모도 보문사
      관광  석모도            ← 이름은 겹치는데 다른 곳일 수 있습니다
  그래서 **명소 좌표와 1km 안**인 것만 받습니다.
  이것이 「다대포해수욕장」 자리에 「다대포해수욕장역」이 들어가는
  일을 막는 길입니다.

쓰는 법
    python engine/fetch_spot_photos.py              # 재 보기만 (안 씁니다)
    python engine/fetch_spot_photos.py --write      # 자료에 적습니다

  ★ 받아 오기만 하고 **파일은 안 내려받습니다.** 주소만 적습니다.
    내려받기는 build.py 의 사진 옮기기가 합니다 (계약-19 — 규모를 먼저 잽니다).
"""
import json
import math
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import io                                        # noqa: E402
from engine.data import 자료                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
API = 'https://badagaja.com/api/tour.php?kind=spot&region=%s'

# ★ **1km** 안이어야 같은 곳으로 봅니다.
#   해수욕장·섬은 넓으니 조금 넉넉히 두되, 2km 를 넘으면 다른 곳입니다.
가까움km = 1.0
살핌km = 2.0


def 거리km(위1, 경1, 위2, 경2):
    R = 6371.0
    p1, p2 = math.radians(위1), math.radians(위2)
    dp = math.radians(위2 - 위1)
    dl = math.radians(경2 - 경1)
    h = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def 받기(권역):
    try:
        r = urllib.request.Request(API % 권역,
                                   headers={'User-Agent': 'badagaja-spot/1.0'})
        j = json.loads(urllib.request.urlopen(r, timeout=30).read()
                       .decode('utf-8'))
        return j.get('items') or []
    except Exception:
        return None


def main():
    씀 = '--write' in sys.argv
    d = 자료()
    이미있음 = set()
    for x in d.사진들:
        if x.get('명소'):
            이미있음.add((x.get('권역'), x['명소']))

    나옴, 멀다, 좌표없음, 못받음 = [], [], [], []
    이용허락없음 = []
    for r in d.권역들:
        관 = 받기(r['id'])
        if 관 is None:
            못받음.append(r['id'])
            continue
        가진것 = [x for x in 관 if x.get('img') and x.get('lat')]
        for m in d.여행(r['id'])['명소']:
            이 = (m['이름'] or {}).get('ko') or ''
            if not 이 or (r['id'], 이) in 이미있음:
                continue
            좌 = m.get('좌표') or {}
            if not 좌.get('위도'):
                좌표없음.append((r['id'], 이))
                continue
            # 이름이 겹치는 것 가운데 **가장 가까운 것**을 고릅니다
            뽑 = None
            납작 = 이.replace(' ', '')
            for x in 가진것:
                이름2 = (x.get('name') or '').replace(' ', '')
                if not 이름2:
                    continue
                if not (납작 in 이름2 or 이름2 in 납작):
                    continue
                km = 거리km(좌['위도'], 좌['경도'], x['lat'], x['lng'])
                if 뽑 is None or km < 뽑[1]:
                    뽑 = (x, km)
            if 뽑 is None:
                continue
            x, km = 뽑
            # ★ **이용허락을 안 주면 쓰지 않습니다** (주인 규칙 5)
            #   촬영자·이용허락범위는 API 가 준 값만 적습니다.
            #   2026-09-29 에 서버 api/tour.php 가 `lic` 을 함께
            #   내주도록 고쳤습니다. 그 전에는 유형을 알 길이 없어
            #   153곳을 찾아 놓고도 쓰지 못했습니다.
            허락 = x.get('lic') or ''
            if not 허락:
                이용허락없음.append((r['id'], 이))
                continue
            한줄 = {'권역': r['id'], '명소': 이, '제목': x['name'],
                    '주소': x.get('addr') or '', '거리km': round(km, 3),
                    '사진주소': x['img'], '관광지id': x.get('id'),
                    '촬영자': '한국관광공사', '이용허락': 허락}
            if km <= 가까움km:
                나옴.append(한줄)
            else:
                멀다.append(한줄)
        time.sleep(0.15)

    print('')
    print('  ── 명소 사진 받아 오기 ─────────────────────────')
    print('')
    print('  · 새로 채울 수 있는 곳  %d곳 (명소 좌표에서 %.1fkm 안)'
          % (len(나옴), 가까움km))
    print('  ~ 이름은 맞는데 **먼 것**  %d곳 — 버립니다' % len(멀다))
    for x in sorted(멀다, key=lambda v: -v['거리km'])[:5]:
        print('      %5.1fkm  %-18s ↔ %s' % (x['거리km'], x['명소'], x['제목']))
    if 이용허락없음:
        print('  x **이용허락을 안 줘서 버린 것** %d곳 (주인 규칙 5)'
              % len(이용허락없음))
    if 좌표없음:
        print('  ? 명소에 좌표가 없어 못 잰 곳 %d곳' % len(좌표없음))
    if 못받음:
        print('  ✗ 관광 자료를 못 받은 권역 %d곳: %s'
              % (len(못받음), ' · '.join(못받음[:5])))
    print('')

    if not 씀:
        print('  ※ 재 보기만 했습니다. 자료에 적으려면 --write 를 붙이세요.')
        print('')
        return 0

    길 = os.path.join(DATA, 'raw', 'spot-photos-new.json')
    io.write(길, json.dumps({
        '_설명': '한국관광공사에서 받은 명소 사진 — 좌표로 거른 것만',
        '_왜': '2026-09-29 주인 지시 — 「지역 광관안내 잘 살펴보면 사진 많을꺼야」',
        '_어떻게': 'engine/fetch_spot_photos.py --write 가 만듭니다',
        '_거른기준': '명소 좌표에서 %.1fkm 안' % 가까움km,
        '_받은날': time.strftime('%Y-%m-%d'),
        '사진': 나옴,
    }, ensure_ascii=False, indent=1) + '\n')
    print('  · data/raw/spot-photos-new.json 에 %d곳을 적었습니다.' % len(나옴))
    print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
