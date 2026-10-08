# -*- coding: utf-8 -*-
"""포인트 좌표가 **바다에 붙어 있는가** (2026-10-08 주인 지적).

★ 왜 생겼나

  주인이 공개 화면에서 잡으셨습니다 —
      「지도핀 위치가 해안가로 나와야 하는데 내륙으로 나오고 있어」

  여수 쪽 1번 「개도 모전리 마을 방파제」가 북위 34.7731 로 **여수
  육지 쪽**에 찍혀 있었습니다. 개도는 34.57 쯤이고, 같은 쪽
  「개도 별촌방파제」가 34.5699 — **23.3km** 떨어져 있었습니다.

  그런데 검사기 36개 가운데 **좌표를 재는 것이 하나도 없었습니다.**
  그래서 아무도 못 잡고 있었습니다. 포인트 이름·사진·물때가 아무리
  좋아도 **핀이 엉뚱한 육지에 꽂혀 있으면 사이트 신뢰가 한 번에
  무너집니다.**

★ 두 축으로 봅니다 (바깥 검수 2026-10-08)

  ① **바다까지 거리** — 물리적으로 말이 안 되는 좌표를 잡습니다.
  ② **같은 지명끼리 거리** — 「해안에는 붙어 있지만 엉뚱한 섬」을
     잡습니다. ①만으로는 개도 사례를 못 잡습니다.

★ 상태를 **넷**으로 나눕니다 — 이것이 이 검사기의 뼈대입니다

      PASS        정상으로 확인
      REVIEW      의심스러움. **배포는 막지 않고** 수정 큐에 쌓음
      UNVERIFIED  해안선 자료가 안 닿아 **못 잼**. 오류가 아님
      FAIL        **새로 들어오거나 바뀐** 좌표가 강한 규칙 위반

  ★ **UNVERIFIED ≠ FAIL** 을 반드시 지킵니다.
    조사하다 제가 바로 이것을 어겼습니다 — 못 잰 것을 999km 로
    넣었더니 「가장 먼 곳」 목록이 통째로 제주로 찼습니다.
    제주·옹진은 해안선 자료가 안 닿는 곳이지 틀린 곳이 아닙니다.
    (끝난값 계약 — 통과·어김·안올림·못잼 과 같은 정신)

★ 기존 자료와 새 자료를 **갈라서** 다룹니다

  지금 105곳이 1km 를 넘습니다. 이것으로 모든 배포를 영원히 막으면
  아무것도 못 합니다. 그래서
      기존에 있던 것  → REVIEW (쌓아 두고 차차 고침)
      오늘 이후 바뀐 것 → FAIL (바로 막음)
  기준선은 `tests/golden/좌표.json` 입니다.

★ 자동으로 고치지 않습니다

  「이름에서 섬 이름을 읽어 그 섬 둘레로 당기는」 보정은 **금지**
  입니다 — 틀린 좌표를 **그럴듯한 다른 틀린 좌표**로 바꿉니다.
  이 검사기는 **후보를 추려 줄 뿐**이고, 고치는 것은 다시 찾아보고
  사람이 확인합니다.
"""
import io as _io
import json
import math
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import io   # noqa: E402

ROOT = 여기
해안길 = os.path.join(ROOT, 'data', 'geo', 'coastline.json')
자료길 = os.path.join(ROOT, 'data', 'raw', 'points')
기준길 = os.path.join(ROOT, 'tests', 'golden', '좌표.json')

# ── 문턱 (바깥 검수가 정한 값)
검토선 = 1.0        # km — 「검토 후보」
경고선 = 3.0        # km — 「강한 경고」
지명선 = 8.0        # km — 같은 지명인데 이만큼 멀면 의심

# ★ **「자료가 없는 곳」과 「진짜 내륙」을 가릅니다** (2026-10-08)
#
#   처음에 「10km 넘으면 못 잼」으로 두었습니다. 연평도 포인트 둘이
#   22.7km·23.2km 로 잡혔는데, 연평도는 서해 북단이라 **해안선
#   자료에 그 섬이 없어** 본토까지 잰 값이었기 때문입니다.
#
#   그런데 그렇게 하니 **진짜 내륙 좌표까지 흘려보냈습니다.**
#   시험 삼아 갯바위 포인트를 지리산 한복판으로 옮겼더니 바다가
#   40km 라 「못 잼」이 되어 **검사기가 못 잡았습니다.**
#
#   갈래는 거리가 아니라 **권역**입니다.
#     · 연평도(옹진) — 그 권역 포인트가 **거의 다** 멀다
#       → 해안선 자료가 그 지역을 안 덮는 것
#     · 지리산으로 옮긴 전남 포인트 — 그 권역의 **나머지는 다 가깝다**
#       → 그 하나가 틀린 것
멂선 = 10.0          # 이보다 멀면 「아주 멂」으로 셉니다
권역못잼비율 = 0.5   # 권역의 이만큼이 아주 멀면 자료가 안 닿는 권역
# ★ 권역이 **작으면 이 판정을 쓰지 않습니다** (2026-10-08에 겪음)
#   포인트가 두어 곳뿐인 권역은 **하나만 틀려도** 절반을 넘습니다.
#   시험 삼아 갯바위 하나를 지리산으로 옮겼더니, 그 권역이 통째로
#   「자료 없는 권역」이 되어 **검사기가 못 잡았습니다.**
#   자료가 정말 안 닿는 곳(옹진 40곳·제주 각 20~46곳)은 넉넉히 큽니다.
권역최소 = 8

# ★ **해안형 지형** — 이 유형이 바다에서 멀면 거의 반드시 잘못입니다
해안형 = ('방파제', '선착장', '갯바위', '해변', '항포구', '암반', '해안',
          '등대', '테트라', '방조제')

# ★ **예외군** — 실제로 해안선에서 멀 수 있는 유형입니다
#   갯벌·조간대는 간조 때 드러나는 자리라 해안선 바깥일 수 있고,
#   방조제 안쪽 호수(군산 수라갯벌 5.75km · 해남 금호호 4.78km)도
#   사실일 수 있습니다. **자동으로 실패시키지 않습니다.**
예외형 = ('갯벌', '조간대', '모래갯벌', '체험장', '현장 판단 필요', '호')


def 거리km(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    h = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def 해안읽기():
    """해안선 격자. 없으면 None — **못 잼**이지 어김이 아닙니다."""
    if not os.path.isfile(해안길):
        return None, 0
    try:
        d = json.loads(io.read(해안길, default='') or '{}')
    except Exception:
        return None, 0
    눈금 = d.get('눈금') or 500
    격자 = {}
    for a, b in (d.get('점들') or []):
        격자.setdefault((a // 10, b // 10), []).append(
            (a / float(눈금), b / float(눈금)))
    return 격자, 눈금


def 바다까지(격자, 눈금, la, lo):
    """가장 가까운 해안선까지 km. 자료가 안 닿으면 None."""
    칸 = 10.0 / 눈금          # 격자 한 칸의 도 크기
    gi, gj = int(la / 칸), int(lo / 칸)
    # ★ **넉넉히 넓혀 봅니다** (2026-10-08에 겪음)
    #   전에는 ±8칸(약 17km)까지만 봤습니다. 그래서 갯바위 하나를
    #   지리산(바다까지 40km)으로 옮겨 시험했더니 **아무것도 못 찾아
    #   None** 이 되었고, 그것이 「못 잼」으로 빠져 **검사기가
    #   못 잡았습니다.** 못 잼과 아주 멂은 다릅니다 — 멀더라도
    #   값이 나와야 「멀다」고 말할 수 있습니다.
    #   64칸이면 약 142km 라 전국 어디서든 바다를 찾습니다.
    for 폭 in (1, 2, 4, 8, 16, 32, 64):
        가장 = None
        for i in range(gi - 폭, gi + 폭 + 1):
            for j in range(gj - 폭, gj + 폭 + 1):
                for (a, b) in 격자.get((i, j), ()):
                    d = 거리km(la, lo, a, b)
                    if 가장 is None or d < 가장:
                        가장 = d
        if 가장 is not None:
            return 가장
    return None


def 포인트들():
    난것 = []
    if not os.path.isdir(자료길):
        return 난것
    for f in sorted(os.listdir(자료길)):
        if not f.endswith('.json'):
            continue
        try:
            d = json.loads(io.read(os.path.join(자료길, f), default='')
                           or '{}')
        except Exception:
            continue
        것들 = d if isinstance(d, list) else (d.get('포인트')
                                              or list(d.values())[0])
        for x in 것들:
            난것.append(x)
    return 난것


def 지명묶기(것들):
    """이름 앞낱말(섬·항 이름)로 묶습니다 — 같은 곳이면 모여 있어야 합니다."""
    묶음 = {}
    for x in 것들:
        좌 = x.get('좌표') or {}
        if 좌.get('위도') is None:
            continue
        이름 = (x.get('이름') or {}).get('ko') or ''
        쪼갠것 = 이름.split()
        앞 = 쪼갠것[0] if 쪼갠것 else ''
        if len(앞) < 2:
            continue
        묶음.setdefault((x.get('권역'), 앞), []).append(x)
    return 묶음


def 외톨이찾기(묶음):
    """같은 이름 무리에서 **혼자 멀리 떨어진 것**을 찾습니다.

    ★ 처음에는 「무리의 가운데에서 먼 것」으로 쟀습니다. 그랬더니
      **영종도처럼 큰 섬**이 통째로 잡혔습니다 — 섬이 20km 가 넘어
      포인트가 고르게 퍼져 있으면 가장자리는 가운데에서 15km 입니다.
      틀린 것이 아닌데 잡힌 것입니다.

    ★ 그래서 **가장 가까운 동료까지의 거리**로 바꿉니다.
        개도 모전리(틀림) — 가장 가까운 동료가 23km (혼자 떨어짐)
        영종도 가장자리   — 가장 가까운 동료가 1~3km (줄지어 있음)
      섬이 아무리 커도 포인트들은 **서로 이어져** 있습니다. 혼자
      뚝 떨어진 것만 의심합니다.

    돌려주는 것 — `{id: (가장가까운동료까지km, 앞낱말, 무리크기)}`
    """
    난것 = {}
    for (권역, 앞), 들 in 묶음.items():
        if len(들) < 2:
            continue
        자리 = [((y.get('좌표') or {})['위도'],
                 (y.get('좌표') or {})['경도']) for y in 들]
        for i, y in enumerate(들):
            가장 = None
            for j in range(len(들)):
                if i == j:
                    continue
                d = 거리km(자리[i][0], 자리[i][1], 자리[j][0], 자리[j][1])
                if 가장 is None or d < 가장:
                    가장 = d
            if 가장 is not None and 가장 > 지명선:
                난것[y['id']] = (가장, 앞, len(들))
    return 난것


def 지형갈래(지형):
    """해안형인가 · 예외형인가. 둘 다 아니면 (False, False)."""
    g = 지형 or ''
    예외 = any(t in g for t in 예외형)
    해안 = (not 예외) and any(t in g for t in 해안형)
    return 해안, 예외


def 기준읽기():
    try:
        return json.loads(io.read(기준길, default='') or '{}')
    except Exception:
        return {}


def main():
    엄격 = '--strict' in sys.argv
    받아들이기 = '--받아들이기' in sys.argv

    print('포인트 좌표가 바다에 붙어 있는가 (2026-10-08 주인 지적)')
    격자, 눈금 = 해안읽기()
    if 격자 is None:
        print('□ 해안선 자료가 없습니다 — %s'
              % os.path.relpath(해안길, ROOT))
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  tools/make_coastline.py 로 만드세요.')
        return 4 if 엄격 else 0
    print('  해안선 %d칸 · 눈금 1/%d도(약 %dm)'
          % (len(격자), 눈금, int(111000.0 / 눈금)))

    것들 = 포인트들()
    if not 것들:
        print('볼 포인트가 없습니다.')
        return 1

    # ── ① 바다까지 거리
    잰것 = {}
    못잼 = []
    좌표없음 = []
    for x in 것들:
        좌 = x.get('좌표') or {}
        la, lo = 좌.get('위도'), 좌.get('경도')
        if la is None or lo is None:
            좌표없음.append(x)
            continue
        km = 바다까지(격자, 눈금, la, lo)
        if km is None:
            못잼.append(x)
        else:
            잰것[x['id']] = km

    # ★ **자료가 안 닿는 권역을 먼저 가립니다** (연평도에서 겪음)
    #   권역의 절반 넘게가 아주 멀면, 그 권역 포인트가 다 틀린 것이
    #   아니라 **그 지역 해안선이 자료에 없는 것**입니다.
    권역셈 = {}
    for x in 것들:
        아이디 = x.get('id')
        if 아이디 not in 잰것:
            continue
        권 = x.get('권역')
        한, 멂 = 권역셈.get(권, (0, 0))
        권역셈[권] = (한 + 1, 멂 + (1 if 잰것[아이디] > 멂선 else 0))
    자료없는권역 = set(k for k, (한, 멂) in 권역셈.items()
                       if 한 >= 권역최소 and 멂 >= 한 * 권역못잼비율)
    for x in 것들:
        아이디 = x.get('id')
        if 아이디 in 잰것 and x.get('권역') in 자료없는권역:
            del 잰것[아이디]
            못잼.append(x)

    # ── ② 같은 지명끼리 거리
    지명이상 = 외톨이찾기(지명묶기(것들))

    # ── 상태를 매깁니다
    기준 = 기준읽기()
    옛것 = set(기준.get('알던것') or [])
    상태 = {}
    for x in 것들:
        아이디 = x.get('id')
        if 아이디 in 잰것:
            km = 잰것[아이디]
            해안, 예외 = 지형갈래(x.get('지형'))
            멀다 = km > 검토선
            아주멀다 = km > 경고선
            # ★ FAIL 은 **복합조건**입니다 (바깥 검수)
            #   「3km 초과 + 해안형 지형인데 예외가 아님」
            #   그리고 **기준선에 없던 것**(새로 들어오거나 바뀐 것)만
            #   막습니다. 기존 것은 REVIEW 로 쌓아 둡니다.
            센잘못 = 아주멀다 and 해안 and not 예외
            # ★ **막는 것은 「새로 생긴 의심」입니다** (2026-10-08)
            #
            #   처음에는 「3km 초과 + 해안형」을 바로 FAIL 로 두었습니다.
            #   그런데 서해 5도(백령·대청·소청·연평)가 해안선 자료에
            #   통째로 없어 100km 넘게 나왔고, 그것들이 전부 FAIL 로
            #   찍혔습니다. **좌표가 틀린 것이 아니라 잴 자료가
            #   없는 것**입니다.
            #
            #   거리 하나로 「틀림/맞음」을 가르는 것은 한계가 분명합니다.
            #   그래서 바깥 검수가 정한 원칙으로 돌아갑니다 —
            #     기존에 있던 것   → REVIEW (쌓아 두고 차차 고침)
            #     오늘 이후 생긴 것 → FAIL (바로 막음)
            #   「3km + 해안형」은 REVIEW 안에서 **먼저 볼 것**을
            #   가리는 데 씁니다.
            if 센잘못 or 멀다 or 아이디 in 지명이상:
                상태[아이디] = ('FAIL' if 아이디 not in 옛것 else 'REVIEW',
                                km)
            else:
                상태[아이디] = ('PASS', km)
        elif 아이디 in 지명이상:
            # 거리는 못 쟀지만 지명이 어긋난 것은 볼 거리가 있습니다
            상태[아이디] = ('FAIL' if 아이디 not in 옛것 else 'REVIEW', None)
        else:
            상태[아이디] = ('UNVERIFIED', None)

    셈 = {'PASS': 0, 'REVIEW': 0, 'UNVERIFIED': 0, 'FAIL': 0}
    for v in 상태.values():
        셈[v[0]] += 1

    print('')
    print('  PASS       %5d  정상으로 확인' % 셈['PASS'])
    print('  REVIEW     %5d  의심 — **배포는 막지 않습니다**' % 셈['REVIEW'])
    print('  UNVERIFIED %5d  해안선 자료가 안 닿아 못 잼 (오류 아님)'
          % 셈['UNVERIFIED'])
    print('  FAIL       %5d  새로 바뀐 좌표가 강한 규칙 위반' % 셈['FAIL'])
    if 좌표없음:
        print('  (좌표 자체가 없는 곳 %d — 이 검사 밖입니다)' % len(좌표없음))

    # ── 기준선 받아들이기
    if 받아들이기:
        알던것 = sorted(k for k, v in 상태.items()
                        if v[0] in ('REVIEW', 'FAIL'))
        난것 = {
            '_무엇인가': ('좌표가 의심스러운 포인트의 기준선입니다. '
                          '여기 있는 것은 REVIEW 로만 셉니다 — '
                          '**새로 생긴 것만 배포를 막습니다.**'),
            '_어떻게줄이나': ('고친 뒤 이 파일에서 그 id 를 지우면 '
                              '다시 생길 때 FAIL 로 잡힙니다.'),
            '알던것': 알던것,
        }
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        _io.open(기준길, 'w', encoding='utf-8').write(
            json.dumps(난것, ensure_ascii=False, indent=1))
        print('')
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(알던것), os.path.relpath(기준길, ROOT)))
        return 0

    # ── 자세히
    막음 = [(k, v[1]) for k, v in 상태.items() if v[0] == 'FAIL']
    볼것 = sorted(((v[1] if v[1] is not None else -1), k)
                  for k, v in 상태.items() if v[0] == 'REVIEW')
    볼것.reverse()

    이름표 = {}
    지형표 = {}
    for x in 것들:
        이름표[x.get('id')] = (x.get('이름') or {}).get('ko') or ''
        지형표[x.get('id')] = x.get('지형') or ''

    if 볼것:
        print('')
        print('  살펴볼 것 %d곳 (막지 않습니다) — 먼 쪽부터 15곳'
              % len(볼것))
        for km, 아이디 in 볼것[:15]:
            덧 = ''
            if 아이디 in 지명이상:
                d, 앞, n = 지명이상[아이디]
                덧 = ' · 「%s」 무리(%d곳)에서 혼자 %.1fkm 떨어짐' % (앞, n, d)
            print('   ~ %-26s %-12s %s%s'
                  % (이름표.get(아이디, '')[:26], 지형표.get(아이디, ''),
                     ('바다까지 %.2fkm' % km) if km >= 0 else '거리 못 잼',
                     덧))

    print('')
    if 막음:
        print('✗ **전에 없던** 의심 좌표가 %d곳 생겼습니다' % len(막음))
        for 아이디, km in 막음[:10]:
            덧 = ''
            if 아이디 in 지명이상:
                d, 앞, n = 지명이상[아이디]
                덧 = ' · 「%s」 무리(%d곳)에서 혼자 %.1fkm 떨어짐' % (앞, n, d)
            print('   ✗ %-26s %-12s %s%s'
                  % (이름표.get(아이디, '')[:26], 지형표.get(아이디, ''),
                     ('바다까지 %.2fkm' % km) if km is not None
                     else '거리 못 잼', 덧))
        print('')
        print('  바다에서 멀거나, 같은 이름 무리에서 혼자 떨어져 있습니다.')
        print('  좌표를 다시 찾아 주세요 — **짐작해 당기지 않습니다.**')
        print('  (자료는 그대로인데 이것이 떴다면 기준선이 낡은 것입니다:')
        print('   python engine/check_coast.py --받아들이기)')
        return 1

    print('좌표가 바다에 제대로 붙어 있습니다.')
    print('  (살펴볼 것 %d곳은 쌓아 두고 차차 고칩니다 — 새로 생기는'
          ' 것만 막습니다)' % len(볼것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
