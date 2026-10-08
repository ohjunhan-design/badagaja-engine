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

장부길 = os.path.join(여기, 'tests', 'golden', '그림자장부.json')
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
