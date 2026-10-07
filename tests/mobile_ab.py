# -*- coding: utf-8 -*-
"""`check_mobile` 을 **쪽 묶음**으로 바꿀 때 쓰는 A/B 자 (2026-10-07).

★ 왜 (바깥 검수 지시)
    「각 단계에서 기존 37회 결과와 아래를 **완전 비교**하세요.
      페이지별 × 폭별 / 화면폭 / 몸폭 / 넘침 목록 / 밀기 여부 /
      그래프 존재·폭 / 접힘 여부 / None·못잼 여부 / 최종 막음·알림 집합
      **한 항목이라도 달라지면 그 배치 크기는 탈락입니다**」

    승인 기준
        batch=3   A/B 259/259 완전 동일 · 못잼 증가 0 · 시간 < 15초
        batch=5   완전 동일 · 시간 < 10초  → 되면 5 채택
        5에서 한 번이라도 흔들리면 **3으로 고정**

★ 「추측해서 최적화 → 효과 없음」을 이미 한 번 겪었습니다.
  그래서 **고치기 전에 기준선을 떠 두고**, 고친 뒤 그것과 견줍니다.

쓰는 법
    python tests/mobile_ab.py --기준          기준선을 뜹니다 (지금 코드)
    python tests/mobile_ab.py --견주기        기준선과 지금 코드를 견줍니다
"""
import io as _io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

기준자리 = os.path.join(ROOT, 'data-private', 'mobile-기준선.json')

# ★ **견줄 항목** — 바깥 검수가 적어 준 그대로입니다.
#   하나라도 빠지면 「같다」가 거짓이 됩니다.
볼것 = ('몸폭', '화면폭', '넘침', '그래프', '그래프폭', '그래프칸', '접힘')


def 한쪽추리기(것):
    """잰 것에서 **견줄 값만** 뽑습니다 — 차례도 고정합니다."""
    if 것 is None:
        return None                      # ★ None(못잼)도 견줍니다
    뽑 = {}
    for k in 볼것:
        뽑[k] = 것.get(k)
    # 넘침은 목록이라 **차례까지** 같아야 합니다
    넘침 = 것.get('넘침') or []
    뽑['넘침'] = sorted(
        [(x.get('t'), x.get('c'), x.get('l'), x.get('r'),
          x.get('w'), bool(x.get('밀기'))) for x in 넘침])
    return 뽑


def 재기():
    """지금 코드로 **37쪽 × 7폭**을 재어 돌려줍니다."""
    from engine import check_mobile as M
    쪽들 = M.볼쪽들('--all' in sys.argv)
    시 = time.perf_counter()
    묶음 = M.묶음크기()
    모은것 = {}
    for i in range(0, len(쪽들), 묶음):
        덩이 = M.재기여러쪽(쪽들[i:i + 묶음], list(M.재볼폭들))
        for p, 잰것 in 덩이.items():
            이름 = os.path.relpath(p, M.NEW).replace(os.sep, '/')
            모은것[이름] = dict((str(폭), 한쪽추리기(잰것.get(폭)))
                                for 폭 in M.재볼폭들)
    걸린 = time.perf_counter() - 시
    return {'쪽수': len(쪽들), '폭수': len(M.재볼폭들),
            '묶음': 묶음,
            '걸린초': round(걸린, 2), '잰것': 모은것}


def 기준뜨기():
    것 = 재기()
    os.makedirs(os.path.dirname(기준자리), exist_ok=True)
    _io.open(기준자리, 'w', encoding='utf-8').write(
        json.dumps(것, ensure_ascii=False, sort_keys=True, indent=1))
    칸 = 것['쪽수'] * 것['폭수']
    못잼 = sum(1 for 쪽 in 것['잰것'].values()
               for v in 쪽.values() if v is None)
    print('기준선을 떴습니다 — %d쪽 × %d폭 = **%d칸**'
          % (것['쪽수'], 것['폭수'], 칸))
    print('  걸린 시간 %.1f초 · 못 잰 칸 %d개' % (것['걸린초'], 못잼))
    print('  자리 %s' % os.path.relpath(기준자리, ROOT))
    print('  ※ 이 자료는 **웹에 내지 않습니다** (주인 규칙 11)')
    return 0


def 견주기():
    if not os.path.exists(기준자리):
        print('기준선이 없습니다. 먼저 --기준 으로 뜨세요.')
        return 2
    옛 = json.loads(_io.open(기준자리, encoding='utf-8').read())
    새 = 재기()

    다름 = []
    모든칸 = set(옛['잰것']) | set(새['잰것'])
    for 이름 in sorted(모든칸):
        ㄱ, ㄴ = 옛['잰것'].get(이름), 새['잰것'].get(이름)
        if ㄱ is None or ㄴ is None:
            다름.append('%s — 한쪽에만 있습니다' % 이름)
            continue
        for 폭 in sorted(set(ㄱ) | set(ㄴ), key=int):
            a, b = ㄱ.get(폭), ㄴ.get(폭)
            if json.dumps(a, sort_keys=True, ensure_ascii=False) != \
               json.dumps(b, sort_keys=True, ensure_ascii=False):
                어디 = '값'
                if (a is None) != (b is None):
                    어디 = '못잼 여부'       # ★ 가장 나쁜 어긋남입니다
                다름.append('%s %spx — %s' % (이름, 폭, 어디))

    칸수 = sum(len(v) for v in 옛['잰것'].values())
    같은수 = 칸수 - len(다름)
    print('옛 %d칸 %.1f초  →  새 %.1f초' % (칸수, 옛['걸린초'], 새['걸린초']))
    print('')
    if not 다름:
        줄어듦 = (1 - 새['걸린초'] / 옛['걸린초']) * 100 if 옛['걸린초'] else 0
        print('  · **%d/%d 완전 동일** — %.0f%% 줄었습니다'
              % (같은수, 칸수, 줄어듦))
        return 0
    print('  ✗ 다른 칸 %d개 / %d개' % (len(다름), 칸수))
    for x in 다름[:10]:
        print('      %s' % x)
    print('')
    print('  ★ **한 항목이라도 달라지면 그 묶음 크기는 탈락입니다.**')
    print('    (바깥 검수 승인 기준 2026-10-07)')
    return 1


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if '--기준' in sys.argv:
        return 기준뜨기()
    if '--견주기' in sys.argv:
        return 견주기()
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
