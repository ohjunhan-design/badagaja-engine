# -*- coding: utf-8 -*-
"""올릴 물때를 **서버 것과 합칩니다** — 배포가 서버를 되돌리지 않게.

★ 왜 만들었나 (2026-10-14)

  서버는 스스로 물때를 채웁니다. 저장소의 `data/tide/` 는
  **씨앗**일 뿐이라 금세 낡습니다. 그런데 `build.py` 가 그 씨앗을
  `site/assets/tide/` 로 복사하고, 배포는 그것을 FTP 로 올립니다.

  그래서 **배포할 때마다 서버가 되돌아갑니다.**
  실측(2026-10-14): 올라갈 것 **30일** ← 서버 지금 **50일**.
  표본 10곳 중 6곳이 20일씩 줄어들 참이었습니다.

  잃는 것은 정부 API 호출 몇 시간치입니다. 다시 채우려면 또
  그만큼 두드려야 하고 하루 한도가 있습니다.

  뿌리는 **같은 사실이 두 곳에** 있는 것입니다 —
      저장소 `data/tide/`  (씨앗 · 낡음)
      서버  `assets/tide/` (진짜 · 자람)
  서버가 진짜인데 배포가 저장소 것으로 덮습니다.

★ 그래서 올리기 전에 **합칩니다.**

  조석은 천문 계산값이라 변하지 않습니다. 10/19 의 간조는
  어제 받든 오늘 받든 같은 값입니다. 그래서 **합쳐도 됩니다** —
  `fetch_tide.합치기()` 를 그대로 씁니다.

  · 서버가 더 많으면 서버 것이 남습니다 (되돌림 없음)
  · 저장소에만 있는 날은 그대로 남습니다 (잃는 것 없음)
  · 빈 날은 **채워진 쪽**이 이깁니다
  · 서버를 못 읽으면 **저장소 것 그대로** 둡니다 (안전)

★ 왜 `build.py` 안에 넣지 않았나 — **멱등성 계약** (주인 규칙 26)

  「자료를 안 고쳤으면 다시 만들어도 결과가 같아야 합니다.」
  그런데 서버는 **계속 채웁니다.** 빌드가 네트워크에서 받아 합치면
  두 번 돌릴 때 결과가 달라져 `check_build` 가 막습니다.

  그래서 **빌드 밖**에 둡니다. 배포 직전에 한 번 돌립니다.
  대신 바꾼 것이 있으면 **판 지문을 다시 찍습니다** — 지문은
  `site/` 아래 **모든 파일**을 세므로, 안 찍으면 「올린 것이 내가
  만든 그것인가」 검증이 거짓 경보를 냅니다.

★ 두 곳을 모두 합칩니다
    `site/assets/tide/`  올라갈 것     — 안 합치면 서버가 되돌아갑니다
    `data/tide/`         씨앗         — 안 합치면 다음 빌드가 또 되돌립니다

쓰는 법
    python -m engine.merge_live_tide            # 합칩니다 (배포 직전)
    python -m engine.merge_live_tide --재보기    # 바꾸지 않고 봅니다
    python -m engine.merge_live_tide --strict   # 한 곳이라도 줄면 막습니다
    python -m engine.merge_live_tide --씨앗만    # data/tide 만
"""
import argparse
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
낼것 = os.path.join(ROOT, 'site', 'assets', 'tide')
씨앗 = os.path.join(ROOT, 'data', 'tide')
서버앞 = 'https://badagaja.com/assets/tide/'

sys.path.insert(0, ROOT)
from engine import fetch_tide as ft   # noqa: E402


def 오늘키():
    t = datetime.datetime.now()
    return '%d/%d' % (t.month, t.day)


def 남은날(자료, 오늘):
    """오늘부터 **이어지는** 날이 며칠인가."""
    날들 = (자료 or {}).get('days') or []
    키들 = [ft.날짜키(x) for x in 날들]
    if 오늘 not in 키들:
        return 0
    return len(날들) - 키들.index(오늘)


def 빈날(자료):
    return sum(1 for x in ((자료 or {}).get('days') or [])
               if not x.get('events'))


def 서버것(권역, 기다림=20):
    """서버 파일을 받아 옵니다. 못 받으면 None — **막지 않습니다.**

    ★ 못 받는 것은 **잘못이 아닙니다.** 서버가 느리거나, 아직
      그 권역 파일이 없거나(첫 배포), 네트워크가 막혔을 수
      있습니다. 그때는 저장소 것을 그대로 올립니다 — 되돌릴
      것이 없으니 손해도 없습니다.
    """
    주소 = 서버앞 + 권역 + '.json'
    try:
        req = urllib.request.Request(주소, headers={
            'User-Agent': 'badagaja-merge/1.0',
            'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=기다림) as r:
            return json.loads(r.read().decode('utf-8')), None
    except urllib.error.HTTPError as e:
        return None, '%d' % e.code
    except Exception as e:
        return None, type(e).__name__


받아둔것 = {}      # 권역 → (자료, 탈) — 서버를 **한 번만** 두드립니다


def 서버것캐시(권역):
    if 권역 not in 받아둔것:
        받아둔것[권역] = 서버것(권역)
    return 받아둔것[권역]


def 한권역(길, 오늘, 재보기):
    권역 = os.path.basename(길)[:-5]
    try:
        내것 = json.load(io.open(길, encoding='utf-8'))
    except Exception as e:
        return 권역, None, '내 파일을 못 읽습니다 (%s)' % type(e).__name__

    서, 탈 = 서버것캐시(권역)
    before = (남은날(내것, 오늘), 빈날(내것))
    if 서 is None:
        return 권역, (before, before, '서버 %s' % (탈 or '못읽음')), None

    모음, 차례 = ft.합치기(내것, 서)
    # ★ `차례대로` 는 「새자료의 첫 날 = 오늘」을 믿습니다.
    #   여기서는 **오늘을 직접 넣어** 그 믿음에 기대지 않습니다.
    줄 = ft.차례대로(모음, 차례, {'days': [{'date': 오늘}]}, 365)
    합 = dict(내것)
    합['days'] = 줄
    after = (남은날(합, 오늘), 빈날(합))

    if after[0] < before[0]:
        return 권역, None, ('합쳤는데 날이 줄었습니다 %d → %d'
                            % (before[0], after[0]))

    if not 재보기 and (after != before):
        임시 = 길 + '.tmp'
        io.open(임시, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(합, ensure_ascii=False, separators=(',', ':')))
        os.replace(임시, 길)      # 원자적 교체
    return 권역, (before, after, '서버 %d일' % 남은날(서, 오늘)), None


def 한칸(칸, 이름, 오늘, 재보기):
    """칸 하나를 서버 것과 합칩니다. 돌려주는 것은 (바뀐곳, 늘어난날, 탈)."""
    if not os.path.isdir(칸):
        print("  %s — 칸이 없습니다 (할 일 없음)" % 이름)
        return 0, 0, []
    길들 = sorted(x for x in
                  (os.path.join(칸, n) for n in os.listdir(칸))
                  if x.endswith(".json") and
                  not os.path.basename(x).startswith("_"))
    if not 길들:
        print("  %s — 물때 파일이 없습니다" % 이름)
        return 0, 0, []

    늘어난곳, 그대로, 못읽음, 탈난곳 = [], 0, [], []
    늘어난날 = 0
    for 길 in 길들:
        권역, 값, 탈 = 한권역(길, 오늘, 재보기)
        if 탈:
            탈난곳.append("%s — %s" % (권역, 탈))
            continue
        before, after, 메모 = 값
        if not 메모.endswith("일"):
            못읽음.append("%s (%s)" % (권역, 메모))
            continue
        if after[0] > before[0] or after[1] < before[1]:
            늘어난곳.append("%-13s %2d일·빈%d → **%d일·빈%d**"
                            % (권역, before[0], before[1], after[0], after[1]))
            늘어난날 += after[0] - before[0]
        else:
            그대로 += 1

    print("  %s — 파일 %d개" % (이름, len(길들)))
    if 늘어난곳:
        print("     서버 것을 받아 **늘어난 곳 %d곳** (합쳐 %d일)"
              % (len(늘어난곳), 늘어난날))
        for x in 늘어난곳[:5]:
            print("        " + x)
        if len(늘어난곳) > 5:
            print("        … 그 밖 %d곳" % (len(늘어난곳) - 5))
    if 그대로:
        print("     이미 같거나 내 것이 더 많은 곳 %d곳" % 그대로)
    if 못읽음:
        print("     서버를 못 읽은 곳 %d곳 — **내 것 그대로 둡니다**"
              % len(못읽음))
        for x in 못읽음[:3]:
            print("        " + x)
    if 탈난곳:
        print("     ✗ 탈난 곳 %d곳" % len(탈난곳))
        for x in 탈난곳[:3]:
            print("        " + x)
    return len(늘어난곳), 늘어난날, 탈난곳


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--재보기", action="store_true",
                   help="바꾸지 않고 무엇이 달라지는지만 봅니다")
    p.add_argument("--strict", action="store_true",
                   help="한 곳이라도 줄면 막습니다")
    p.add_argument("--씨앗만", action="store_true",
                   help="data/tide 만 합칩니다 (빌드 전에 쓸 때)")
    a = p.parse_args()

    print("물때를 서버 것과 합칩니다"
          + (" (재보기 — 바꾸지 않습니다)" if a.재보기 else ""))
    print("=" * 62)

    오늘 = 오늘키()
    칸들 = [(씨앗, "data/tide (씨앗)")]
    if not a.씨앗만:
        칸들.insert(0, (낼것, "site/assets/tide (올라갈 것)"))

    바뀐곳합, 늘어난날합, 탈전부 = 0, 0, []
    for 칸, 이름 in 칸들:
        c, d, t = 한칸(칸, 이름, 오늘, a.재보기)
        바뀐곳합 += c
        늘어난날합 += d
        탈전부 += t

    # ★ 바꿨으면 **판 지문을 다시 찍습니다** (2026-10-14)
    #   지문은 site/ 아래 모든 파일을 셉니다. 물때를 합쳐 놓고
    #   안 찍으면 「올린 것이 내가 만든 그것인가」 검증이
    #   거짓 경보를 냅니다.
    if 바뀐곳합 and not a.재보기 and not a.씨앗만:
        try:
            from engine import build_id
            판 = build_id.만들기(os.path.join(ROOT, "site"))
            print("  판 지문을 다시 찍었습니다 — 파일 %d개 · %s"
                  % (판.get("파일수", 0), (판.get("통지문") or "")[:16]))
        except Exception as e:
            탈전부.append("판 지문을 다시 못 찍었습니다 (%s)"
                          % type(e).__name__)

    print("-" * 62)
    if 탈전부:
        print("[한 줄 요약] ✗ %d곳이 탈났습니다 — 올리지 마십시오"
              % len(탈전부))
        return 2 if a.strict else 1
    if 바뀐곳합 and a.재보기:
        print("[한 줄 요약] 합치면 **%d일**을 지킵니다 (%d곳)"
              % (늘어난날합, 바뀐곳합))
    elif 바뀐곳합:
        print("[한 줄 요약] 서버 것을 지켰습니다 — %d곳 · %d일"
              % (바뀐곳합, 늘어난날합))
    else:
        print("[한 줄 요약] 되돌아갈 것이 없습니다")
    return 0

if __name__ == '__main__':
    sys.exit(main())
