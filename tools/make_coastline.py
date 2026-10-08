# -*- coding: utf-8 -*-
"""해안선 자료를 **저장소 안으로** 솎아 옮깁니다 (2026-10-08).

★ 왜 필요한가

  주인이 화면에서 잡으셨습니다 — 「지도핀 위치가 해안가로 나와야
  하는데 내륙으로 나오고 있어」. 그런데 **좌표를 재는 검사기가 한
  개도 없었습니다.** 재려면 해안선이 있어야 합니다.

  원본은 `D:\\바다가자\\_geo\\coast_all*` 에 있습니다 —
  OpenStreetMap `natural=coastline` 을 Overpass 로 받아 둔 것,
  way 2,959개 · 점 619,787개.

★ 그런데 그것은 **저장소 밖**입니다

  판정은 깃허브에서 돕니다(규칙 15 — 「저장소에 없으면 없는
  것입니다」). 러너에는 `D:\\바다가자` 가 없습니다. 그러니 검사에
  쓸 만큼만 **저장소 안으로** 옮겨야 합니다.

★ 얼마나 솎는가

  0.002도(약 220m) 격자에 하나씩만 남깁니다 — 619,787점이
  62,481점이 됩니다. 문턱이 1km·3km 이므로 220m 해상도면
  넉넉합니다.

★ 이 도구는 **자주 돌리지 않습니다.** 해안선은 거의 안 바뀝니다.
  원본이 없는 자리에서는 그냥 건너뜁니다 — 만들어 둔 결과를 씁니다.
"""
import glob
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

원본자리 = os.environ.get('BADAGAJA_GEO', r'D:\바다가자\_geo')
낼곳 = os.path.join(여기, 'data', 'geo', 'coastline.json')
눈금 = 500          # 1/500 도 = 0.002도 = 약 220m


def main():
    # ★ `coast_gap` — **구멍을 메운 조각**입니다 (2026-10-08)
    #   옛 조각들의 범위가 위도 33.87~38.71 · 경도 125.08~130.94
    #   뿐이라 제주 남부·백령도·대청도·독도가 통째로 빠져 있었습니다.
    #   그래서 백령도 포인트 14곳이 「바다까지 105km」로 나와
    #   멀쩡한 좌표가 「먼저 볼 것」에 쌓였습니다.
    #   `tools/fetch_coast_gaps.py` 가 그 자리만 받아 둡니다.
    폴더들 = [d for d in ('coast_all', 'coast_all2', 'coast_all3',
                           'coast_gap')
               if os.path.isdir(os.path.join(원본자리, d))]
    if not 폴더들:
        print('□ 원본 해안선을 못 찾았습니다 — %s' % 원본자리)
        print('  **틀린 것이 아니라 못 만든 것입니다.** 이미 만들어 둔')
        print('  data/geo/coastline.json 이 있으면 그대로 씁니다.')
        return 0 if os.path.isfile(낼곳) else 1

    본 = set()
    읽은점 = 0
    for 폴더 in 폴더들:
        for f in sorted(glob.glob(os.path.join(원본자리, 폴더, '*.json'))):
            try:
                d = json.load(io.open(f, encoding='utf-8'))
            except Exception as e:
                print('  ~ 못 읽음 %s (%s)' % (os.path.basename(f), e))
                continue
            for el in d.get('elements', []):
                for g in (el.get('geometry') or []):
                    if not g:
                        continue
                    la, lo = g.get('lat'), g.get('lon')
                    if la is None or lo is None:
                        continue
                    읽은점 += 1
                    본.add((int(round(la * 눈금)), int(round(lo * 눈금))))

    if not 본:
        print('✗ 해안선 점이 하나도 없습니다')
        return 1

    # ★ **차례를 정해 둡니다** — 안 그러면 돌릴 때마다 파일이 달라져
    #   「자료를 안 고쳤으면 결과가 같아야 한다」가 깨집니다 (규칙 26)
    점들 = sorted(본)
    난것 = {
        '_무엇인가': ('해안선 점 — 포인트 좌표가 바다에서 얼마나 먼지 '
                      '재는 데 씁니다. tools/make_coastline.py 가 만듭니다.'),
        '_어디서': ('OpenStreetMap natural=coastline (Overpass API). '
                    'ODbL 라이선스. 원본은 _geo/coast_all*.'),
        '_눈금': '위도·경도에 %d 을 곱한 정수입니다 (약 220m 격자)' % 눈금,
        '눈금': 눈금,
        '점들': 점들,
    }
    os.makedirs(os.path.dirname(낼곳), exist_ok=True)
    io.open(낼곳, 'w', encoding='utf-8').write(
        json.dumps(난것, ensure_ascii=False, separators=(',', ':')))
    크기 = os.path.getsize(낼곳)
    print('  · 원본 %d점 → 솎아서 %d점 (%.1fMB)'
          % (읽은점, len(점들), 크기 / 1024.0 / 1024.0))
    print('  · %s' % os.path.relpath(낼곳, 여기))
    return 0


if __name__ == '__main__':
    sys.exit(main())
