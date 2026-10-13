# -*- coding: utf-8 -*-
"""**어종 아이디가 자료마다 어긋나지 않았나** (2026-10-13)

★ 왜 만들었나

  어종 이름표(`species.json` 104종)와 쪽을 만드는 안내
  (`guide.json` 35종)가 **따로 자랐습니다.** 그러다 같은 어종의
  아이디가 서로 달라졌습니다.

      벵에돔     자료 bengedom     ↔ 쪽 byeongedom
      갑오징어    자료 gabojingeo   ↔ 쪽 gapojingeo
      무늬오징어   자료 muniojingeo  ↔ 쪽 muni

  겉으로는 멀쩡해 보였습니다. 쪽도 잘 나오고 검사도 다 통과했습니다.
  그런데 어종 쪽에서 포인트를 세면 **0곳**이 나왔습니다 —
  실제로는 413·246·258곳인데도. 이름이 다르니 못 찾은 것입니다.

  ★ **0 은 조용합니다.** 「없다」와 「못 찾았다」가 똑같이 0으로
    보입니다. 그래서 사람이 눈으로 보기 전에는 아무도 모릅니다.
    그런 것은 검사기가 잡아야 합니다.

★ 무엇을 보나

  ① 두 자료에 **같은 이름**인데 아이디가 다른 것이 있는가
     (별칭표에 적혀 있으면 봐줍니다 — 이미 아는 것입니다)
  ② 별칭표에 적힌 짝이 **정말 같은 이름**인가
     (잘못 이으면 다른 어종이 섞입니다)
  ③ 별칭표에 **이제 필요 없는 줄**이 남아 있지 않은가

★ 끝난값 — 통과 0 · 어김 1 · 못잼 4

쓰는 법
    python engine/check_species_id.py
    python engine/check_species_id.py --strict    어기면 끝난값 1
"""
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import io as _io          # noqa: E402

DATA = os.path.join(여기, 'data', 'raw')


def 이름of(것):
    """어종 하나의 한국어 이름. 꼴이 자료마다 조금 다릅니다."""
    v = 것.get('이름')
    if isinstance(v, dict):
        return (v.get('ko') or '').strip()
    return str(v or '').strip()


def 읽기(이름):
    길 = os.path.join(DATA, 이름)
    if not os.path.isfile(길):
        return None
    return _io.read_json(길, default=None)


def main():
    엄격 = '--strict' in sys.argv

    종 = 읽기('species.json')
    안내 = 읽기('guide.json')
    별 = 읽기('species-alias.json') or {}

    # ★ 못 읽으면 **통과로 내지 않습니다** (fail-closed)
    if not 종 or not 안내:
        print('어종 아이디 — 자료를 못 읽었습니다. 통과로 내지 않습니다.')
        return 4

    종들 = 종.get('어종') or []
    안내들 = 안내.get('어종') or []
    if not 종들 or not 안내들:
        print('어종 아이디 — 잴 것이 0개입니다. 통과로 내지 않습니다.')
        return 4

    별칭 = dict((별.get('별칭') or {}))         # 자료 id → 쪽 id
    아는짝 = set(별칭.items()) | set((v, k) for k, v in 별칭.items())

    # 이름 → 아이디들
    종이름 = {}
    for g in 종들:
        종이름.setdefault(이름of(g), []).append(g['id'])
    안내이름 = {}
    for g in 안내들:
        안내이름.setdefault(이름of(g), []).append(g['id'])

    # ★ 계약-21 — 막을 것과 알릴 것을 **따로** 모읍니다
    #   막음 : 계약을 어긴 것. 고쳐야 합니다
    #   알림 : 아직 안 한 것·기계가 못 재는 것. 막지 않습니다
    막음, 알림 = [], []

    # ① 같은 이름인데 아이디가 다른 것
    못이은것 = []
    for 이름, 안내ids in sorted(안내이름.items()):
        if not 이름:
            continue
        종ids = 종이름.get(이름) or []
        if not 종ids:
            continue                     # 이름표에 없는 것은 여기서 안 봅니다
        for a in 안내ids:
            if a in 종ids:
                continue                 # 아이디가 같습니다 — 좋습니다
            이은것 = [s for s in 종ids if (s, a) in 아는짝]
            if 이은것:
                continue                 # 별칭표에 적혀 있습니다
            못이은것.append((이름, 종ids, a))

    # ② 별칭표의 짝이 정말 같은 이름인가
    엉뚱한짝 = []
    종의이름 = dict((g['id'], 이름of(g)) for g in 종들)
    안내의이름 = dict((g['id'], 이름of(g)) for g in 안내들)
    쓸모없는줄 = []
    for 자료id, 쪽id in sorted(별칭.items()):
        가 = 종의이름.get(자료id)
        나 = 안내의이름.get(쪽id)
        if 가 is None or 나 is None:
            쓸모없는줄.append((자료id, 쪽id, 가, 나))
            continue
        if 가 != 나:
            엉뚱한짝.append((자료id, 가, 쪽id, 나))

    print('어종 아이디 어긋남 — 이름표 %d종 · 안내 %d종 · 별칭 %d줄'
          % (len(종들), len(안내들), len(별칭)))

    if 못이은것:
        막음.append(('이름은 같은데 아이디가 다릅니다', 못이은것))
        print('  ❌ 이름은 같은데 아이디가 다른 것 %d개' % len(못이은것))
        for 이름, 종ids, a in 못이은것[:10]:
            print('       %-10s 이름표 %s ↔ 안내 %s'
                  % (이름, ' · '.join(종ids), a))
        print('     → data/raw/species-alias.json 에 한 줄 더하세요.')
        print('       안 이으면 그 어종 쪽에서 포인트가 **0곳**으로 나옵니다.')
    else:
        print('  ✓ 이름이 같은데 아이디가 다른 것 0')

    if 엉뚱한짝:
        막음.append(('별칭표의 짝이 다른 어종입니다', 엉뚱한짝))
        print('  ❌ 별칭표에서 **다른 어종끼리** 이어 놓은 것 %d개'
              % len(엉뚱한짝))
        for 자료id, 가, 쪽id, 나 in 엉뚱한짝:
            print('       %s(%s) ↔ %s(%s)' % (자료id, 가, 쪽id, 나))
    elif 별칭:
        print('  ✓ 별칭표의 짝이 모두 같은 이름')

    if 쓸모없는줄:
        알림.append(('자료에 없는 아이디를 가리키는 별칭', 쓸모없는줄))
        print('  ⚠ 자료에 없는 아이디를 가리키는 별칭 %d줄 (막지는 않습니다)'
              % len(쓸모없는줄))
        for 자료id, 쪽id, 가, 나 in 쓸모없는줄:
            print('       %s → %s' % (자료id, 쪽id))

    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        return 1 if 엄격 else 0
    print('  ✓ 어긋남 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
