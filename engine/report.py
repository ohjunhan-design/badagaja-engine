# -*- coding: utf-8 -*-
"""**보고할 숫자를 읽어 줍니다** — 손으로 옮겨 적지 않습니다.

★ 왜 만들었나 (2026-09-28 바깥 검수 9차)

    바깥 검수가 제 보고서를 보고 가장 먼저 이것을 짚었습니다.

        TOTAL 20 · PASS 17 · FAIL 0 · NOT_TESTED 1 · ERROR 0 · N.A. 1
        → 17 + 0 + 1 + 0 + 1 = 19

    합이 안 맞는다고요. 확인해 보니 **검사기는 틀리지 않았습니다.**
    검사기가 낸 것은 이랬습니다.

        ✗ 2  검사기 자기검증 (뮤테이션)   FAIL
        검산  17 + 1 + 1 + 0 + 1 = 20 = 20

    **제가 틀렸습니다.** 뮤테이션을 고쳐 88가지를 통과시킨 뒤
    **판정을 다시 돌리지 않고**, 머릿속에서 「그러면 FAIL 0 이겠지」
    하고 문서에 적었습니다. **잰 적 없는 숫자를 잰 것처럼** 적은 것입니다.

    주인 규칙 29 가 못 박은 바로 그 잘못입니다 —
    「사이트에 적는 숫자는 손으로 적지 않습니다. 자료에서 셉니다.」
    기계가 지키던 것을 사람이 깼습니다.

    그리고 캐 보니 뿌리가 더 있었습니다.

      · 판정이 `--json` 을 붙여야만 결과를 남겼습니다.
        아침 것이 파일에 남아 낮 결과와 달랐습니다.
      · 그 파일에 **ERROR 가 통째로 빠져** 있었습니다.
        ERROR 가 0 일 때만 우연히 합이 맞았습니다.

★ 그래서 이 도구가 하는 일

    tests/out/gate.json 에서 **읽어서** 보고할 글을 만듭니다.
    그리고 **낡았으면 낡았다고 말합니다** — 지금 커밋과 견줍니다.
    안 맞으면 숫자를 내주지 않습니다. 낡은 숫자로 보고하느니
    「모른다」고 하는 편이 낫습니다.

쓰는 법
    python engine/report.py            사람이 읽을 요약
    python engine/report.py --md       문서에 붙일 표
    python engine/report.py --strict   낡았거나 안 맞으면 끝난값 1
"""
import os
import sys
import subprocess
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

결과길 = os.path.join(ROOT, 'tests', 'out', 'gate.json')
# ★ 상태 목록은 **engine/gate.py 한 곳에만** 있습니다 (2026-09-28)
#   여기에 따로 적어 두었다가 INFRA_FAIL 을 늘리며 한 곳만 고쳤고,
#   합이 18 인데 TOTAL 이 20 이 됐습니다.
#   바깥 검수 9차가 지적한 바로 그 상황이 실제로 났습니다.
#   ★ 그런데 **검사가 잡아냈습니다** — 「상태 합 18 과 TOTAL 20 이
#     다릅니다 · 판정 자체를 믿을 수 없습니다」. 숙제 1 이 제 몫을 했습니다.
from engine.gate import 상태들   # noqa: E402


def 지금커밋():
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    끝 = (r.stdout or '').strip()
    return 끝 if (r.returncode == 0 and 끝) else None


def 읽기():
    """★ **없으면 없다고 합니다.** 빈 것으로 바꿔 읽지 않습니다.

    바깥 검수 9차가 짚은 그대로입니다 — 필수 파일을
    `default=''` 로 읽으면 「없음」과 「빈 것」이 같아집니다.
    """
    if not os.path.exists(결과길):
        return None, '판정 결과가 없습니다 — python engine/gate.py --full 을 먼저'
    if os.path.getsize(결과길) == 0:
        return None, '판정 결과가 비었습니다 (0바이트)'
    판 = io.read_json(결과길, default=None)
    if not isinstance(판, dict):
        return None, '판정 결과를 읽을 수 없습니다 (모양이 다릅니다)'
    return 판, None


def 재보기(판):
    """★ 읽은 숫자를 **다시 셉니다.** 파일이 적어 준 합을 안 믿습니다."""
    탈 = []
    총 = 판.get('TOTAL')
    항목 = 판.get('항목') or []

    셈 = {}
    for k in 상태들:
        v = 판.get(k)
        if v is None:
            탈.append('%s 가 결과에 없습니다' % k)
            v = 0
        셈[k] = v
    합 = sum(셈.values())

    if 총 is None:
        탈.append('TOTAL 이 없습니다')
    elif 합 != 총:
        탈.append('상태 합 %d 과 TOTAL %d 이 다릅니다' % (합, 총))

    # 항목을 직접 세어 봅니다 — 요약 숫자와 맞아야 합니다
    if 항목:
        직접 = {}
        for x in 항목:
            직접[x.get('상태')] = 직접.get(x.get('상태'), 0) + 1
        for k in 상태들:
            if 직접.get(k, 0) != 셈[k]:
                탈.append('%s: 요약 %d · 항목을 세면 %d'
                          % (k, 셈[k], 직접.get(k, 0)))
        if 총 is not None and len(항목) != 총:
            탈.append('TOTAL %d · 항목 수 %d' % (총, len(항목)))
    else:
        탈.append('항목이 하나도 없습니다')

    return 셈, 합, 탈


def 낡았나(판):
    """이 판정이 **지금 코드**를 잰 것인가."""
    잰커밋 = 판.get('커밋')
    이제 = 지금커밋()
    if not 잰커밋 or 잰커밋 == '(모름)':
        return '이 판정이 어느 판을 잰 것인지 안 적혀 있습니다'
    if 이제 and 잰커밋 != 이제:
        return ('판정은 %s 를 쟀는데 지금은 %s 입니다 — **다시 재세요**'
                % (잰커밋, 이제))
    return None


def 나이(판):
    때 = 판.get('잰때')
    if not 때:
        return None
    try:
        t = datetime.datetime.fromisoformat(때)
    except ValueError:
        return None
    return (datetime.datetime.now() - t).total_seconds() / 3600.0


def main():
    엄하게 = '--strict' in sys.argv
    마크다운 = '--md' in sys.argv

    판, 탈 = 읽기()
    if 판 is None:
        print('✗ %s' % 탈)
        return 1

    셈, 합, 탈들 = 재보기(판)
    낡음 = 낡았나(판)
    시간 = 나이(판)

    if 마크다운:
        print('| 상태 | 수 |')
        print('|---|---|')
        for k in 상태들:
            print('| %s | %d |' % (k, 셈[k]))
        print('| **합** | **%d** |' % 합)
        print('')
        print('- 잰 때: %s' % 판.get('잰때', '(모름)'))
        print('- 잰 판: %s' % 판.get('커밋', '(모름)'))
        print('- 판정: **%s**' % 판.get('FINAL', '(모름)'))
        if 판.get('빠른검사'):
            print('- ※ `--smoke` 로 잰 것이라 **배포 판정이 아닙니다**')
    else:
        print('판정 결과를 읽었습니다 (손으로 옮겨 적지 않습니다)')
        print('  잰 때  %s%s'
              % (판.get('잰때', '(모름)'),
                 '  (%.1f시간 전)' % 시간 if 시간 is not None else ''))
        print('  잰 판  %s' % 판.get('커밋', '(모름)'))
        print('')
        print('  TOTAL  %d' % (판.get('TOTAL') or 0))
        for k in 상태들:
            print('  %-11s%d' % (k, 셈[k]))
        print('  ─────────────')
        print('  상태 합  %d' % 합)
        print('')
        print('  FINAL  %s' % 판.get('FINAL', '(모름)'))

    나쁨 = []
    if 탈들:
        print('')
        print('✗ 숫자가 안 맞습니다 %d가지' % len(탈들))
        for x in 탈들:
            print('    %s' % x)
        print('  **판정 자체를 믿을 수 없습니다.** 다시 재세요.')
        나쁨.append('숫자')
    if 낡음:
        print('')
        print('✗ %s' % 낡음)
        나쁨.append('낡음')
    if 시간 is not None and 시간 > 6:
        print('')
        print('~ 잰 지 %.1f시간 지났습니다 — 그 사이 무엇이 바뀌었는지 보세요'
              % 시간)

    if 나쁨:
        print('')
        print('  이 숫자를 보고서에 적지 마세요.')
        print('  낡은 숫자로 보고하느니 「모른다」고 하는 편이 낫습니다.')
        return 1 if 엄하게 else 0
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
