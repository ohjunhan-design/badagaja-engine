# -*- coding: utf-8 -*-
"""해안선 자료의 **구멍**을 메웁니다 (2026-10-08).

★ 왜 필요한가 — 검사기가 멀쩡한 좌표를 「먼저 볼 것」으로 쌓았습니다

  좌표 검사기를 만들어 돌렸더니 백령도·대청도 포인트가
  **「바다까지 105km」** 로 나왔습니다. 좌표는 맞습니다.
  **해안선 자료에 그 섬이 없었습니다.**

  옛 PowerShell 스크립트들이 Overpass 에서 조각조각 받았는데
  범위가 이랬습니다

      fetch_coast_all   위도 33.8~35.8 · 경도 125.0~128.2
      (그 밖 셋도 각자 범위)

  합쳐 보니 **위도 33.87~38.71 · 경도 125.08~130.94** 였습니다.
  그래서 통째로 빠진 곳

      제주 남부·서부      위도 33.1~33.8   (마라도 84km, 제주 45km)
      백령·대청·소청      경도 124.5~125.1 (108km)
      독도                경도 131.8~132.0 (88km)
      연평도 주변         (20km)

  **좌표가 틀린 것이 아니라 잴 자료가 없었습니다.** 그런데 검사기는
  「멀다」로 세었습니다. 이것이 거짓 양성의 뿌리입니다.

★ 여기서는 **구멍만** 받습니다. 이미 받아 둔 조각은 그대로 둡니다.
  `coast_gap/` 에 따로 담아 `make_coastline.py` 가 함께 읽습니다.

★ 자주 돌리지 않습니다. 해안선은 거의 안 바뀝니다.
  인터넷을 쓰므로 **판정에 넣지 않습니다.**

쓰는 법
    python tools/fetch_coast_gaps.py
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

원본자리 = os.environ.get('BADAGAJA_GEO',
                          os.path.join('D:', os.sep, '바다가자', '_geo'))
낼곳 = os.path.join(원본자리, 'coast_gap')

# ★ 메울 구멍 — (이름, 남, 서, 북, 동)
#   섬은 작아도 조각을 넉넉히 잡습니다. 빈 결과가 나와도 괜찮습니다.
구멍들 = [
    ('제주남서', 33.05, 126.05, 33.62, 126.65),
    ('제주남동', 33.05, 126.65, 33.62, 127.05),
    ('제주북', 33.40, 126.10, 33.75, 126.99),
    ('추자도', 33.85, 126.20, 34.15, 126.45),
    ('백령대청', 37.70, 124.50, 38.15, 125.15),
    ('연평도', 37.50, 125.50, 37.85, 126.10),
    ('독도', 37.15, 131.75, 37.35, 132.00),
    ('가거도흑산', 33.90, 124.95, 34.75, 125.60),
    ('마라가파', 33.05, 126.20, 33.30, 126.45),
]

주소들 = (
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
)


def 받기(물음):
    몸 = urllib.parse.urlencode({'data': 물음}).encode('utf-8')
    마지막 = None
    for 주 in 주소들:
        try:
            req = urllib.request.Request(
                주, data=몸,
                headers={'User-Agent': 'badagaja-coast-gap/1.0'})
            with urllib.request.urlopen(req, timeout=240) as r:
                return r.read().decode('utf-8', 'replace'), None
        except Exception as e:                            # noqa: BLE001
            마지막 = '%s — %s' % (주.split('/')[2], str(e)[:60])
            time.sleep(3)
    return None, 마지막


def main():
    os.makedirs(낼곳, exist_ok=True)
    print('해안선 구멍 %d 조각을 받습니다 → %s' % (len(구멍들), 낼곳))
    print('')
    받은점 = 0
    못받음 = []
    for 이름, 남, 서, 북, 동 in 구멍들:
        길 = os.path.join(낼곳, '%s.json' % 이름)
        if os.path.isfile(길) and os.path.getsize(길) > 30:
            try:
                d = json.loads(io.open(길, encoding='utf-8').read())
                n = sum(len(e.get('geometry') or [])
                        for e in d.get('elements', []))
                print('  · %-10s 이미 있습니다 — 점 %d개' % (이름, n))
                받은점 += n
                continue
            except ValueError:
                pass            # 깨졌으면 다시 받습니다
        물음 = ('[out:json][timeout:180];'
                'way["natural"="coastline"](%s,%s,%s,%s);out geom;'
                % (남, 서, 북, 동))
        글, 왜 = 받기(물음)
        if 글 is None:
            print('  ! %-10s 못 받았습니다 (%s)' % (이름, 왜))
            못받음.append(이름)
            continue
        try:
            d = json.loads(글)
        except ValueError as e:
            print('  ! %-10s 답이 JSON 이 아닙니다 (%s)' % (이름, e))
            못받음.append(이름)
            continue
        n = sum(len(e.get('geometry') or []) for e in d.get('elements', []))
        # BOM 없이 씁니다 (파일마다 다릅니다 — CLAUDE.md)
        io.open(길, 'w', encoding='utf-8').write(글)
        print('  O %-10s way %d개 · 점 %d개'
              % (이름, len(d.get('elements', [])), n))
        받은점 += n
        time.sleep(2)

    print('')
    print('받은 점 %d개' % 받은점)
    if 못받음:
        print('못 받은 조각 %d개: %s' % (len(못받음), ', '.join(못받음)))
        print('  **틀린 것이 아니라 못 받은 것입니다.** 다시 돌리면')
        print('  이미 받은 것은 건너뛰고 못 받은 것만 받습니다.')
        return 4                                      # 계약 — 못 잼
    print('이제 `python tools/make_coastline.py` 로 솎아 넣으세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
