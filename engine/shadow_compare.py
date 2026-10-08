# -*- coding: utf-8 -*-
"""새 되돌림 셈이 **기존 계획과 집합이 같은가** (2026-10-08).

★ 바깥 검수가 정한 전환 차례의 **1단계(그림자)** 입니다

      「바로 기존 19분33초를 지워버리기보다, 새 0.2초 계산을 먼저
        **그림자 모드**로 몇 번 병행해 증명한 뒤 전환하는 게
        맞습니다. 사람 눈으로 『비슷하다』가 아니라
        **new_plan == old_plan** 이어야 합니다」

★ 견주는 둘
    기존  `rollback-plan.txt` — lftp `mirror --delete --dry-run` 글
    새것  `tests/out/되돌림계획.json` — 공개 판 목록으로 셈한 것

★ **여기서는 막지 않습니다.** 기존 방식이 그대로 일하고 있고,
  이것은 아직 재 보는 중입니다. 몇 번 나란히 돌려 늘 같은 것을
  본 뒤에야 바꿉니다.

★ 다를 수 있는 **올바른 까닭**도 있습니다
  · lftp 는 `_stage/` 를 빼고 봅니다(`--exclude-glob`)
  · lftp 는 **서버 전체**를, 새 셈은 **배포가 가진 파일**만 봅니다.
    그래서 손으로 올린 파일은 lftp 에만 나옵니다 — 그것이 바로
    새 방식으로 바꾸려는 까닭입니다(남의 것을 안 지웁니다).
  그래서 **새것 − 기존** 이 비어 있는 것이 더 중요합니다.
  새 셈이 기존에 없는 것을 지우려 들면 그때가 위험합니다.
"""
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ★ **올리기 전에 잰 것**과 견줍니다 (2026-10-08에 겪음)
#
#   그림자가 **올리기 뒤**에만 돌고 있었습니다. 그런데 새 셈은
#   **공개 `build.json`** 을 읽습니다. 올린 뒤에는 공개 판이 곧
#   이번 판이라 늘 「새로 생김 0 · 바뀜 0 · 사라짐 0」이 나왔습니다.
#   배포 #39 로그에 그대로 찍혀 있었습니다 —
#       공개 판 8ab8271 · 이번 판 8ab8271 · 그대로 926
#   **잴 것이 없는 자리에서 재고 있었습니다.**
#
#   올리기 전에 잰 것이 있으면 그것을 먼저 씁니다. lftp 계획도
#   「새 판 → 옛 판」을 재므로 짝이 맞습니다.
_전 = os.path.join(여기, 'tests', 'out', '되돌림계획-올리기전.json')
새길 = (_전 if os.path.isfile(_전)
        else os.path.join(여기, 'tests', 'out', '되돌림계획.json'))
옛길 = os.path.join(여기, 'rollback-plan.txt')


def lftp가지울것(글):
    """lftp `--dry-run` 글에서 「지우겠다」는 경로만 꺼냅니다."""
    난것 = set()
    for 줄 in (글 or '').splitlines():
        m = re.search(r'rm\s+(?:-r\s+)?(?:-f\s+)?["\']?/www/([^"\'\s]+)',
                      줄)
        if m:
            난것.add(m.group(1).rstrip('/'))
    return 난것


def main():
    if not os.path.isfile(새길):
        print('   □ 새 계획이 없습니다 — 그림자를 못 쟀습니다')
        return 0
    try:
        새 = json.loads(io.open(새길, encoding='utf-8').read())
    except Exception as e:
        print('   □ 새 계획을 못 읽었습니다 (%s)' % e)
        return 0
    새지울것 = set(새.get('지울것') or [])

    # ★ **잴 것이 없으면 「같았다」고 세지 않습니다** (2026-10-08)
    #   공개 판과 이번 판이 같으면 차이가 0 인 것이 당연합니다.
    #   그것을 「집합이 정확히 같습니다」로 세면 **연속 3회가
    #   거짓으로 채워집니다.** 배포 #39 가 그 상태였습니다.
    바뀜 = 새.get('바뀜') or {}
    움직인것 = (len(새지울것) + len(새.get('되돌릴것') or [])
                + (바뀜.get('생김') or 0) + (바뀜.get('바뀜') or 0)
                + (바뀜.get('사라짐') or 0))
    잴것없음 = (움직인것 == 0)
    if 잴것없음:
        print('   □ **잴 것이 없습니다** — 공개 판과 이번 판이'
              ' 같습니다 (%s)' % (새.get('이번판') or '?'))
        print('     차이 0 은 당연한 것이라 「같았다」로 세지 않습니다.')
        print('     올리기 **전**에 재야 진짜 차이가 나옵니다.')
        return 0

    글 = ''
    if os.path.isfile(옛길):
        try:
            글 = io.open(옛길, encoding='utf-8', errors='replace').read()
        except Exception:
            글 = ''
    옛지울것 = lftp가지울것(글)

    print('   새 셈 %d개 · lftp %d개' % (len(새지울것), len(옛지울것)))

    새것만 = sorted(새지울것 - 옛지울것)
    옛것만 = sorted(옛지울것 - 새지울것)

    if not 새것만 and not 옛것만:
        print('   · **집합이 정확히 같습니다**')
    else:
        if 새것만:
            # ★ 이것이 **위험한 쪽**입니다 — 새 셈이 기존에 없는 것을
            #   지우려 듭니다. 왜 그런지 봐야 합니다.
            print('   ! 새 셈에만 있는 것 %d개 — **눈여겨볼 것**'
                  % len(새것만))
            for x in 새것만[:5]:
                print('       %s' % x)
        if 옛것만:
            # ★ 이것은 **대개 올바릅니다** — lftp 는 서버 전체를 보아
            #   손으로 올린 파일까지 지우려 듭니다. 새 방식이 그것을
            #   안 건드리는 것이 바뀌려는 까닭입니다.
            print('   ~ lftp 에만 있는 것 %d개 (손으로 올린 것 등 —'
                  ' 새 방식은 일부러 안 건드립니다)' % len(옛것만))
            for x in 옛것만[:5]:
                print('       %s' % x)

    # ★ **장부에 적습니다** — 합격 기준은 「연속 3회 100% 동일」이고
    #   사람이 세면 잊습니다 (바깥 검수가 정한 기준)
    #
    #   ★ 「같았다」의 뜻을 좁게 잡습니다 — **새 셈에만 있는 것이
    #     없을 때**입니다. lftp 에만 있는 것은 손으로 올린 파일 등이라
    #     **일부러 다른 것**이고, 그것이 바로 새 방식으로 바꾸려는
    #     까닭입니다. 반대로 새 셈이 기존에 없는 것을 지우려 들면
    #     그것은 위험이므로 「다르다」로 셉니다.
    같았나 = not 새것만
    판 = 새.get('이번판') or '(모름)'
    덧 = ('새것만 %d · lftp만 %d' % (len(새것만), len(옛것만)))
    try:
        sys.path.insert(0, 여기)
        from engine import shadow_tally
        if shadow_tally.사라질자리인가():
            # ★ 적어도 이 배포가 끝나면 사라집니다. 세는 척만 하는
            #   것이라 **말해 주어야** 합니다 (2026-10-08 에 겪음)
            print('   ✗ **장부가 체크아웃 안에 있습니다** — 적어도'
                  ' 이 배포가 끝나면 사라집니다.')
            print('     연속 횟수가 영영 안 쌓입니다.'
                  ' deploy.yml 의 BADAGAJA_TALLY 를 보세요.')
            print('     지금 자리: %s' % shadow_tally.장부길)
        장부 = shadow_tally.적기(판, 같았나, 덧)
        n = shadow_tally.연속(장부)
        print('   장부: 연속 %d회 같았습니다 (합격선 %d회) — %s'
              % (n, shadow_tally.합격선, shadow_tally.장부길))
    except Exception as e:
        print('   ~ 장부에 못 적었습니다 (%s)' % e)

    print('   ※ 재기만 했습니다. 실제 백업·되돌림은 기존 단계가'
          ' 그대로 합니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
