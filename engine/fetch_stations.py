# -*- coding: utf-8 -*-
"""전남 15권역 **물때 관측소를 자료에 적습니다** (2026-10-02).

★ 남은 부채였습니다
  `data/raw/index.json` 의 `물때관측소` 가 **전남 15권역만 비어**
  있었습니다. 바깥 검수도 「전국 물때 쪽에서 제주·충남·전북 등은
  ○○ 관측소 기준으로 표시되는데 **전남 15권역은 괄호명만 있고
  관측소가 없습니다**」라고 지적했습니다.

★ **임의로 잇지 않습니다** (주인 원칙)
  거리만으로 가까운 관측소를 고르면 **물길이 다른 곳**이 섞입니다.
  강화 자료에 그 경고가 적혀 있습니다 — 「염하 물길 쪽이 가장
  가깝지만 석모도·교동도 서쪽 바다는 물 들고 나는 시각이 조금
  다를 수 있습니다」.

★ 그래서 **이미 쓰고 있는 값**을 받아 적습니다
  서버(`api/tide-cache.php`)가 KHOA 에서 받아 **실제로 쪽에
  보여 주고 있는** 관측소가 있습니다. 여수 쪽은 지금도
  「기준 관측소 여수」라고 나옵니다. 즉 **매핑은 이미 있고
  자료에만 안 적혀 있었던 것**입니다.

  짐작이 아니라 **동작하는 값을 기록**하는 일입니다.
  이렇게 적어 두면 쪽을 만들 때도 쓸 수 있고, 서버가 멈춰도
  「어디 기준인가」를 손님께 밝힐 수 있습니다.

★ 한 번만 돌리는 도구입니다. 적은 뒤에는 자료가 대장입니다.
"""
import io
import json
import os
import sys
import time
import urllib.request

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

색인길 = os.path.join(여기, 'data', 'raw', 'index.json')
주소 = 'https://badagaja.com/api/tide-cache.php?region=%s'


def 받기(권역):
    try:
        with urllib.request.urlopen(주소 % 권역, timeout=20) as r:
            d = json.loads(r.read().decode('utf-8'))
    except Exception as e:                       # noqa: BLE001
        return None, str(e)[:60]
    이름 = (d.get('point') or '').strip()
    where = (d.get('source') or '').strip()
    if not 이름:
        return None, '관측소 이름이 비어 있습니다'
    return {'이름': 이름, '출처': where, '받은날': d.get('updated')}, None


def main():
    with io.open(색인길, encoding='utf-8') as f:
        색인 = json.load(f)
    권역들 = 색인['권역']
    빈것 = [r for r in 권역들 if not (r.get('물때관측소') or {}).get('이름')]
    print('관측소가 비어 있는 권역 %d개' % len(빈것))
    if not 빈것:
        return 0

    채움, 못함 = 0, []
    for r in 빈것:
        것, 탈 = 받기(r['id'])
        if not 것:
            못함.append('%s — %s' % (r['id'], 탈))
            print('  ! %-12s %s' % (r['id'], 탈))
            continue
        r['물때관측소'] = {
            '이름': 것['이름'],
            '코드': None,              # ★ 코드는 **모릅니다.** 짓지 않습니다
            '메모': ('물때표는 %s 조위관측소 기준입니다. '
                     '서버가 국립해양조사원에서 받아 쓰는 값을 '
                     '그대로 적었습니다 (%s 확인).'
                     % (것['이름'], (것.get('받은날') or '')[:10])),
        }
        채움 += 1
        print('  · %-12s → %s 관측소' % (r['id'], 것['이름']))
        time.sleep(0.4)          # 서버에 몰아치지 않습니다

    with io.open(색인길, 'w', encoding='utf-8') as f:
        json.dump(색인, f, ensure_ascii=False, indent=1)
    print()
    print('%d곳을 적었습니다 → data/raw/index.json' % 채움)
    if 못함:
        print('못 받은 곳 %d개 — **비워 둡니다.** 지어내지 않습니다'
              % len(못함))
    return 0


if __name__ == '__main__':
    sys.exit(main())
