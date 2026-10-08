# -*- coding: utf-8 -*-
"""그림자 합격을 **코드가 셉니다** (2026-10-08).

★ 바깥 검수가 합격 기준을 못박았습니다

      「shadow 기간의 합격 기준을 저는 명확히 잡겠습니다 —
        **연속 3회 배포에서 새 계획과 기존 계획이 100% 동일**
        + artifact preflight 성공 + rollback drill 성공.
        그 뒤 정상 경로의 full FTP backup 을 조건부 fallback 으로
        내리세요」

★ 사람이 세면 **잊습니다.** 「두 번쯤 봤으니 됐겠지」가 가장
  위험합니다. 그래서 배포마다 결과를 한 줄씩 쌓고, **연속 몇 회
  같았는지**를 코드가 말해 줍니다.

★ 「연속」이 중요합니다 — 한 번이라도 다르면 **거기서 0 으로**
  돌아갑니다. 세 번 중 두 번 같은 것으로는 모자랍니다.
"""
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ★ **장부는 체크아웃 밖에 둡니다** (2026-10-08 에 겪음)
#
#   처음에는 `tests/golden/그림자장부.json` 한 곳에만 썼습니다.
#   그런데 판정·배포는 깃허브 일꾼에서 돌고, 일꾼은 배포마다
#   **저장소를 새로 받습니다.** 그러니 일꾼이 적은 줄은 그 배포가
#   끝나면 **사라집니다.**
#
#   증거 — 배포 #29(b969834)가 성공으로 끝났는데 장부에는 그 줄이
#   없었습니다. 장부에는 제가 제 컴퓨터에서 적은 한 줄(27c8527)뿐.
#   **연속 3회가 영영 안 쌓이는 상태**였습니다.
#
#   「사람이 세면 잊으니 코드가 세게 하겠습니다」라고 해 놓고
#   코드도 못 세고 있었습니다.
#
#   그래서 일꾼이 **체크아웃 밖 고정 자리**에 쌓게 합니다
#   (`BADAGAJA_TALLY`). 잃어도 큰일이 아닙니다 — 되돌리기 밑천이
#   아니라 **세는 것**이라 연속이 0부터 다시 시작될 뿐입니다.
#   밑천은 깃허브 아티팩트가 따로 보관합니다.
_기본장부 = os.path.join(여기, 'tests', 'golden', '그림자장부.json')
장부길 = os.environ.get('BADAGAJA_TALLY') or _기본장부
합격선 = 3


def 읽기():
    try:
        return json.loads(io.open(장부길, encoding='utf-8').read())
    except Exception:
        return {'_무엇인가': ('그림자 단계의 기록입니다. 배포마다 새 셈과 '
                              '기존 계획이 같았는지 한 줄씩 쌓습니다.'),
                '_합격선': '연속 %d회 같아야 합니다' % 합격선,
                '기록': []}


def 적기(판, 같았나, 덧=''):
    장부 = 읽기()
    기록 = 장부.get('기록') or []
    # 같은 판을 두 번 적지 않습니다 — 다시 돌려도 셈이 안 부풀게
    기록 = [x for x in 기록 if x.get('판') != 판]
    기록.append({'판': 판, '같았나': bool(같았나), '덧': 덧})
    기록 = 기록[-20:]
    장부['기록'] = 기록
    os.makedirs(os.path.dirname(장부길), exist_ok=True)
    io.open(장부길, 'w', encoding='utf-8').write(
        json.dumps(장부, ensure_ascii=False, indent=1))
    return 장부


def 사라질자리인가():
    """장부가 **배포마다 지워지는 자리**에 있는가.

    ★ 일꾼(깃허브 액션)은 배포마다 저장소를 새로 받습니다. 장부가
      체크아웃 안에 있으면 적어 봐야 그 배포와 함께 사라지고,
      연속 횟수가 영영 안 쌓입니다. 2026-10-08 에 그 상태였습니다 —
      배포 #29 가 성공했는데 장부에 그 줄이 없었습니다.

      그때는 **아무도 알려 주지 않아** 제가 로그를 뒤져 알았습니다.
      다음부터는 그 자리에서 말하게 합니다.
    """
    if not os.environ.get('GITHUB_ACTIONS'):
        return False            # 내 컴퓨터에서는 안 지워집니다
    일터 = os.environ.get('GITHUB_WORKSPACE')
    if not 일터:
        return False
    try:
        안인가 = os.path.commonpath(
            [os.path.abspath(장부길), os.path.abspath(일터)])
        return 안인가 == os.path.abspath(일터)
    except ValueError:
        return False            # 드라이브가 다르면 바깥입니다


def 연속(장부=None):
    """마지막부터 **연속으로 같았던** 횟수."""
    기록 = (장부 or 읽기()).get('기록') or []
    n = 0
    for x in reversed(기록):
        if x.get('같았나'):
            n += 1
        else:
            break
    return n


def main():
    # 적는 쪽: --적기 <판> <0|1> [덧]
    if '--적기' in sys.argv:
        i = sys.argv.index('--적기')
        판 = sys.argv[i + 1] if len(sys.argv) > i + 1 else '(모름)'
        같 = (sys.argv[i + 2] == '1') if len(sys.argv) > i + 2 else False
        덧 = sys.argv[i + 3] if len(sys.argv) > i + 3 else ''
        장부 = 적기(판, 같, 덧)
    else:
        장부 = 읽기()

    기록 = 장부.get('기록') or []
    n = 연속(장부)
    print('그림자 장부 — 새 셈이 기존 계획과 같았는가')
    for x in 기록[-5:]:
        print('   %s %-10s %s' % ('·' if x.get('같았나') else '✗',
                                  x.get('판'), x.get('덧') or ''))
    print('')
    print('   연속 %d회 같았습니다 (합격선 %d회)' % (n, 합격선))
    if n >= 합격선:
        print('   ★ **합격선을 넘었습니다.** 다음 단계로 갈 수 있습니다 —')
        print('     아티팩트 사전확인을 넣고, 그 다음 전체 백업을')
        print('     조건부로 건너뜁니다. 한꺼번에 둘을 바꾸지 않습니다.')
    else:
        print('   아직입니다. %d회 더 같아야 합니다.' % (합격선 - n))
        print('   (한 번이라도 다르면 **거기서 0 으로** 돌아갑니다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
