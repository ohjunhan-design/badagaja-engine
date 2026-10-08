# -*- coding: utf-8 -*-
"""엉뚱한 곳에 찍힌 핀을 **자료 안의 답으로** 고칩니다 (2026-10-08).

★ 주인이 화면에서 잡으셨습니다 — 「지도핀 위치가 해안가로 나와야
  하는데 내륙으로 나오고 있어」. 여수 쪽 「개도 모전리 마을 방파제」가
  개도가 아니라 **여수 육지**에 찍혀 있었습니다.

★ **짐작해 고치지 않습니다** (바깥 검수)

      「이름에서 섬 이름을 읽어 좌표를 그 섬 둘레로 당기는
        자동보정은 **금지**입니다. 틀린 좌표를 **그럴듯한 다른 틀린
        좌표**로 바꿀 위험이 큽니다」

  그래서 이 도구는 **같은 자료 안에 이미 답이 있는 것만** 고칩니다.
      「개도 모전리 마을 방파제」 (34.7731, 127.5981) ← 여수 육지
      「개도 모전리 해안」       (34.5699, 127.6609) ← 개도
  **같은 마을 이름**을 가진 다른 포인트가 올바른 자리를 들고
  있습니다. 그것을 가져옵니다 — 지어내는 것이 아닙니다.

★ 그래도 **정확한 한 점은 아닙니다.** 주인 말씀대로 포인트 좌표는
  대표 진입점이고, 손님은 위성지도로 해안과 들어가는 길을 봅니다.
  여기서 하는 일은 「다른 섬·내륙에 꽂힌 핀을 **그 마을 근처로**
  돌려놓는 것」까지입니다.

★ 고친 것은 **되돌릴 수 있게 적어 둡니다** — data-private/ 에
  무엇을 무엇으로 바꿨는지 남깁니다.
"""
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import check_coast as C   # noqa: E402

자료칸 = os.path.join(여기, 'data', 'raw', 'points')
자국길 = os.path.join(여기, 'data-private', '좌표-고친기록.md')


def 답찾기():
    """같은 자료 안에 답이 있는 것만. `{id: (이름, 바탕이름, 위도, 경도)}`"""
    판길 = os.path.join(여기, 'tests', 'out', '좌표판정.json')
    if not os.path.isfile(판길):
        return None
    판 = json.loads(io.open(판길, encoding='utf-8').read())
    지명 = 판.get('지명이상') or {}
    것들 = C.포인트들()
    표 = dict((x.get('id'), x) for x in 것들)

    난것 = {}
    for 아이디 in 지명:
        x = 표.get(아이디) or {}
        이름 = (x.get('이름') or {}).get('ko') or ''
        낱말 = 이름.split()
        if len(낱말) < 2:
            continue
        앞둘 = ' '.join(낱말[:2])      # 섬 + 마을
        for y in 것들:
            if y.get('id') == 아이디:
                continue
            이2 = (y.get('이름') or {}).get('ko') or ''
            if not 이2.startswith(앞둘):
                continue
            좌 = y.get('좌표') or {}
            if 좌.get('위도') is None:
                continue
            # ★ 바탕이 되는 동료가 **의심 목록에 없어야** 합니다 —
            #   틀린 것을 바탕으로 고치면 둘 다 틀립니다
            if y.get('id') in 지명:
                continue
            난것[아이디] = (이름, 이2, 좌['위도'], 좌['경도'])
            break
    return 난것


def main():
    진짜로 = '--고칩니다' in sys.argv
    답 = 답찾기()
    if 답 is None:
        print('□ 판정이 없습니다 — 먼저 engine/check_coast.py 를 돌리세요')
        return 1
    if not 답:
        print('· 자료 안에 답이 있는 것이 없습니다 — 고칠 것이 없습니다')
        return 0

    print('자료 안에 답이 있는 핀 %d곳' % len(답))
    print('')

    바꾼것 = []
    for f in sorted(os.listdir(자료칸)):
        if not f.endswith('.json'):
            continue
        길 = os.path.join(자료칸, f)
        d = json.loads(io.open(길, encoding='utf-8').read())
        것들 = d if isinstance(d, list) else (d.get('포인트')
                                              or list(d.values())[0])
        손댐 = False
        for x in 것들:
            아이디 = x.get('id')
            if 아이디 not in 답:
                continue
            이름, 바탕, la, lo = 답[아이디]
            좌 = x.get('좌표') or {}
            옛 = (좌.get('위도'), 좌.get('경도'))
            멀기 = C.거리km(옛[0], 옛[1], la, lo) if 옛[0] else None
            print('  %s — %s' % (아이디, 이름))
            print('     %s, %s  →  %s, %s' % (옛[0], 옛[1], la, lo))
            print('     바탕: 「%s」%s' % (바탕,
                                           (' (%.1fkm 옮김)' % 멀기)
                                           if 멀기 else ''))
            바꾼것.append((아이디, 이름, 옛, (la, lo), 바탕, 멀기))
            if 진짜로:
                x['좌표'] = {'위도': la, '경도': lo}
                손댐 = True
        if 손댐:
            io.open(길, 'w', encoding='utf-8').write(
                json.dumps(d, ensure_ascii=False, indent=1))

    print('')
    if not 진짜로:
        print('※ 아직 **안 고쳤습니다.** 정말 고치려면 --고칩니다')
        return 0

    # 고친 자국을 남깁니다 — 되돌릴 수 있어야 합니다
    줄 = ['# 좌표를 고친 기록', '',
          '`tools/fix_point_coords.py` 가 **자료 안에 이미 있던 답**으로',
          '고친 것입니다. 짐작해 당긴 것이 아닙니다 — 같은 마을 이름을',
          '가진 다른 포인트의 좌표를 가져왔습니다.', '',
          '정확한 한 점은 아닙니다. 다른 섬·내륙에 꽂힌 핀을 **그 마을',
          '근처로 돌려놓은 것**이고, 최종 확인은 위성지도에서 합니다.', '']
    for 아이디, 이름, 옛, 새, 바탕, 멀기 in 바꾼것:
        줄.append('- **%s** · `%s`' % (이름, 아이디))
        줄.append('  - `%s, %s` → `%s, %s`%s'
                  % (옛[0], 옛[1], 새[0], 새[1],
                     (' (%.1fkm)' % 멀기) if 멀기 else ''))
        줄.append('  - 바탕: 「%s」' % 바탕)
    줄 += ['', '※ 이 파일은 `data-private/` 에 있습니다 — 웹에 안 냅니다.']
    os.makedirs(os.path.dirname(자국길), exist_ok=True)
    io.open(자국길, 'w', encoding='utf-8').write(chr(10).join(줄))
    print('· %d곳을 고쳤습니다. 기록 — %s'
          % (len(바꾼것), os.path.relpath(자국길, 여기)))
    print('· 이제 engine/check_coast.py --받아들이기 로 기준선을'
          ' 다시 만드세요')
    return 0


if __name__ == '__main__':
    sys.exit(main())
