# -*- coding: utf-8 -*-
"""fetch_spot_photos.py 가 찾아 놓은 명소 사진을 내려받습니다.

★ 왜 따로 만드나 (계약-19 — 규모를 먼저 잽니다)

  찾는 일과 내려받는 일을 나눕니다.
  찾기만 하면 인터넷 호출 57번이지만, 내려받기는 125번에
  수십 MB 를 씁니다. 되돌리기도 다릅니다.

★ 어디에 두나

  `assets/photo/img/coast/…` — **저장소 안**입니다.
  옛 저장소에서 가져오면 깃허브 액션에서 사진이 통째로 빠지는데
  아무 말이 없었습니다. 주인 규칙 15 — 저장소에 없으면 없는 것입니다.

쓰는 법
    python engine/download_spot_photos.py           # 재 보기만
    python engine/download_spot_photos.py --write   # 실제로 받습니다
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import io                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
ASSETS = os.path.join(ROOT, 'assets')


def 갈이름(한줄):
    """파일 이름 — 관광지 고유번호를 씁니다.

    한글 이름을 로마자로 바꾸면 규칙이 흔들려 다시 만들 때마다
    이름이 달라질 수 있습니다(계약-07). 관광공사 고유번호는
    바뀌지 않고, 나중에 원본을 되짚을 수도 있습니다.
    """
    return 'img/coast/%s-tour-%s.jpg' % (한줄['권역'], 한줄['관광지id'])


def main():
    씀 = '--write' in sys.argv
    길 = os.path.join(DATA, 'raw', 'spot-photos-new.json')
    자료 = io.read_json(길, default={}) or {}
    것들 = 자료.get('사진') or []
    if not 것들:
        print('  받을 것이 없습니다. 먼저 fetch_spot_photos.py --write 를 도세요.')
        return 1

    받음 = 이미 = 실패 = 0
    크기합 = 0
    나온것 = []
    for x in 것들:
        상대 = 갈이름(x)
        갈곳 = os.path.join(ASSETS, 'photo', 상대.replace('/', os.sep))
        if os.path.isfile(갈곳) and os.path.getsize(갈곳) > 1000:
            이미 += 1
            크기합 += os.path.getsize(갈곳)
            나온것.append(dict(x, 파일=상대, 크기=os.path.getsize(갈곳)))
            continue
        if not 씀:
            받음 += 1
            continue
        try:
            # ★ **원본을 먼저 받습니다** (2026-09-29)
            #   서버 api/tour.php 는 목록 카드용이라 가벼운
            #   썸네일(firstimage2 · _image3_)을 내줍니다. 12KB 라
            #   명소 카드에 크게 쓰면 흐립니다.
            #   같은 주소의 `_image3_` 를 `_image2_` 로 바꾸면
            #   원본입니다(10배쯤 큽니다). 없으면 썸네일을 씁니다.
            덩이 = None
            for 후보 in (x['사진주소'].replace('_image3_', '_image2_'),
                         x['사진주소']):
                try:
                    r = urllib.request.Request(
                        후보, headers={'User-Agent': 'badagaja-photo/1.0'})
                    덩이 = urllib.request.urlopen(r, timeout=40).read()
                    if len(덩이) >= 1000:
                        break
                    덩이 = None
                except Exception:
                    덩이 = None
            if not 덩이:
                raise ValueError('원본도 썸네일도 못 받았습니다')
            # ★ 파일 쓰기는 io 만 합니다 (계약-13)
            io.write_binary(갈곳, 덩이)
            받음 += 1
            크기합 += len(덩이)
            나온것.append(dict(x, 파일=상대, 크기=len(덩이)))
        except Exception as e:
            실패 += 1
            print('  x %-18s %s' % (x['명소'], str(e)[:50]))

    print('')
    print('  받은 것 %d · 이미 있던 것 %d · 못 받은 것 %d'
          % (받음, 이미, 실패))
    print('  모두 %.1fMB' % (크기합 / 1024.0 / 1024.0))
    if not 씀:
        print('')
        print('  ※ 재 보기만 했습니다. 받으려면 --write 를 붙이세요.')
        return 0

    # 받은 것만 자료에 남깁니다 — 없는 파일을 가리키지 않습니다
    자료['사진'] = 나온것
    io.write(길, json.dumps(자료, ensure_ascii=False, indent=1) + '\n')
    print('  · %s 를 실제 받은 %d장으로 다시 적었습니다.'
          % (os.path.relpath(길, ROOT), len(나온것)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
