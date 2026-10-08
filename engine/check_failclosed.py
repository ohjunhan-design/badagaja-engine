# -*- coding: utf-8 -*-
"""**검사기가 못 쟀을 때 조용히 통과하지 않는가** (2026-10-08)

왜 이 검사가 있나 — 바깥 검수가 못박았습니다

    「모든 validator/checker 를 fail-open 전수조사하세요.
      ImportError/ModuleNotFoundError 뿐 아니라 Exception, 외부
      binary 부재, 파일 부재, 네트워크/API 실패, timeout, parse 실패가
      **검사를 수행할 수 없으면 PASS 가 아니라 UNAVAILABLE(4) 또는
      ERROR(3) 로 종료**해야 합니다. …
      배포가 실패한 것이 아니라, 지금까지 믿었던 녹색 체크 일부의
      신뢰성이 깨졌다는 사실을 보아야 합니다」

    실제로 겪은 일 — `check_workflow.py` 가 이렇게 쓰여 있었습니다.

        try:
            import yaml
        except ImportError:
            알림.append('yaml 이 없어 짜임을 못 봤습니다')
        ...
        return 0          # ← 짜임을 **하나도 안 보고** 통과

    우분투 러너에는 PyYAML 이 없습니다. 그래서 클라우드에서 이 검사가
    **한 줄도 안 돌면서 ✅ 를 찍고** 있었습니다. 제 윈도우에는 PyYAML 이
    있어 멀쩡히 돌았으므로 오래 몰랐을 수 있습니다.

무엇을 보나

    검사기의 코드를 **글이 아니라 짜임(AST)으로** 읽어, 「예외를 삼키고
    통과로 이어지는 길」을 찾습니다.

      ① `except ...:` 안에서 **곧바로 0 을 돌려주는** 곳
      ② `except ...:` 안이 `pass` 뿐이고, 그 try 가 **검사에 꼭 필요한
         것**(import · subprocess · 파일 열기 · 네트워크)을 하던 곳
      ③ 검사기 꼭대기에서 `import` 를 감싸 삼키고, 그 모듈이 없으면
         검사를 건너뛰는 꼴

    ★ **이 메타검사 하나를 유일한 보증으로 삼지 않습니다.** 바깥 검수가
      그렇게 못박았습니다. 검사기마다 「꾸러미를 없앤 환경에서 돌려도
      통과를 내지 않는가」를 실제로 재는 시험이 따로 있습니다
      (`tests/test_failclosed.py`).

끝난값
    0 통과 · 1 어김 (거짓 통과가 있음)
"""
import ast
import io
import os
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

검사기터 = os.environ.get('BADAGAJA_CHECKERS', HERE)

# 검사를 **수행하는 데 꼭 필요한 것**들. 이것이 실패했는데 통과를
# 내면 「안 재고 통과」입니다.
꼭필요한것 = ('import', 'subprocess', 'open', 'urlopen', 'request',
              'run', 'check_output', 'Popen', 'loads', 'load', 'parse')

기준길 = os.path.join(ROOT, 'tests', 'golden', '거짓통과.json')

# ★ **기준선을 둡니다** (2026-10-08)
#
#   짜임(AST)으로만 보면 「예외를 삼키는 곳」이 28곳 나옵니다. 그중
#   상당수는 **거짓 양성**입니다 — 작은 도우미가 빈 값을 돌려주는 것과,
#   검사기 전체가 통과를 내는 것은 다릅니다.
#
#   실제로 못 재는 환경에 놓고 돌려 본 것(`tests/test_failclosed.py`)이
#   **증거**이고, 이것은 **새로 느는 것을 막는 그물**입니다.
#   구별하지 못하는 검사는 두지 않습니다 — 대신 늘지 않게 합니다.


def 통과를내나(본문):
    """이 `except` 본문이 **통과**로 이어지는가."""
    for n in 본문:
        if isinstance(n, ast.Return):
            v = n.value
            if v is None:
                return True, 'return (빈 값)'
            if isinstance(v, ast.Constant) and v.value in (0, True):
                return True, 'return %r' % (v.value,)
            if isinstance(v, ast.List) and not v.elts:
                return True, 'return []'
            if isinstance(v, ast.Dict) and not v.keys:
                return True, 'return {}'
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            # 안쪽까지 봅니다
            속 = []
            for 칸 in ('body', 'orelse', 'finalbody'):
                속 += getattr(n, 칸, []) or []
            난것 = 통과를내나(속)
            if 난것[0]:
                return 난것
    return False, ''


def 그냥넘기나(본문):
    """`pass` 나 `continue` 뿐이어서 **아무 일도 없이 넘어가는가**."""
    쓸모있는것 = [n for n in 본문
                  if not isinstance(n, (ast.Pass, ast.Continue))]
    return not 쓸모있는것


def 꼭필요한일인가(try_노드, 글줄):
    """그 `try` 가 **검사에 꼭 필요한 일**을 하고 있었는가."""
    for n in ast.walk(try_노드):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            return True, 'import'
        if isinstance(n, ast.Call):
            이름 = ''
            if isinstance(n.func, ast.Name):
                이름 = n.func.id
            elif isinstance(n.func, ast.Attribute):
                이름 = n.func.attr
            if 이름 in 꼭필요한것:
                return True, 이름
    return False, ''


def 한파일(길):
    """그 검사기 한 장에서 거짓 통과로 가는 길을 찾습니다."""
    글 = io.open(길, encoding='utf-8', errors='replace').read()
    줄들 = 글.splitlines()
    try:
        나무 = ast.parse(글)
    except SyntaxError as e:
        return [('문법', e.lineno or 0, '읽지 못했습니다 (%s)' % e.msg)]

    난것 = []
    for n in ast.walk(나무):
        if not isinstance(n, ast.Try):
            continue
        꼭, 무엇 = 꼭필요한일인가(n, 줄들)
        for h in n.handlers:
            줄 = h.lineno
            통과, 어떻게 = 통과를내나(h.body)
            if 통과:
                난것.append(('통과', 줄,
                             '`except` 안에서 %s — 못 쟀는데 통과입니다'
                             % 어떻게))
            elif 꼭 and 그냥넘기나(h.body):
                난것.append(('넘김', 줄,
                             '`except` 가 %s 실패를 그냥 넘깁니다 '
                             '— 안 재고 이어집니다' % 무엇))
    return 난것


def main():
    자세히 = '--자세히' in sys.argv
    print()
    print('  검사기가 못 쟀을 때 조용히 통과하지 않는가')
    print('  (바깥 검수 2026-10-08 — fail-open 전수조사)')
    print()

    길들 = sorted(glob.glob(os.path.join(검사기터, 'check_*.py')))
    # 자기 자신은 뺍니다
    길들 = [p for p in 길들
            if os.path.basename(p) != os.path.basename(__file__)]
    if not 길들:
        print('  ? 검사기를 못 찾았습니다 — %s' % 검사기터)
        print('    **통과가 아닙니다.**')
        return 4

    받아들이기 = '--받아들이기' in sys.argv
    기준 = {}
    try:
        import json
        기준 = json.loads(io.open(기준길, encoding='utf-8').read())
    except Exception:                                 # noqa: BLE001
        기준 = {}
    알던것 = set(기준.get('알던것') or [])

    모두, 탈 = [], []
    본것 = 0
    for p in 길들:
        본것 += 1
        짧 = os.path.basename(p)
        for 갈래, 줄, 말 in 한파일(p):
            열쇠 = '%s:%d' % (짧, 줄)
            모두.append(열쇠)
            if 열쇠 in 알던것:
                continue
            탈.append((짧, 줄, 갈래, 말))

    if 받아들이기:
        import json
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        io.open(기준길, 'w', encoding='utf-8').write(json.dumps({
            '_무엇인가': ('짜임(AST)으로 본 「예외를 삼키는 곳」의 '
                          '기준선입니다. 여기 있는 것은 **새로 생긴 것이 '
                          '아니라는 뜻**일 뿐, 안전하다는 뜻이 아닙니다.'),
            '_진짜증거는': ('tests/test_failclosed.py — 검사기를 **못 재는 '
                            '환경에 놓고 실제로 돌려** 통과를 내는지 봅니다. '
                            '2026-10-08 에 9장을 잡아 모두 고쳤습니다.'),
            '_어떻게줄이나': '고친 뒤 여기서 그 줄을 지우면 다시 생길 때 막습니다.',
            '알던것': sorted(set(모두)),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(set(모두)), os.path.relpath(기준길, ROOT)))
        return 0

    사라진것 = 알던것 - set(모두)
    if 사라진것:
        print('  · 고쳐진 곳 %d곳 — `--받아들이기` 로 기준을 조이세요'
              % len(사라진것))
        print('')

    print('  검사기 %d장을 짜임으로 읽었습니다' % 본것)
    print()
    if 탈:
        파일별 = {}
        for 짧, 줄, 갈래, 말 in 탈:
            파일별.setdefault(짧, []).append((줄, 갈래, 말))
        print('  **새로 생긴** 거짓 통과 %d곳 · 검사기 %d장'
              % (len(탈), len(파일별)))
        print('  ' + '─' * 68)
        for 짧 in sorted(파일별):
            for 줄, 갈래, 말 in sorted(파일별[짧]):
                print('  ✗ %-26s %4d줄  %s' % (짧, 줄, 말))
        print()
        print('  못 잰 것은 **통과가 아닙니다.** 끝난값 4(못잼)를 냅니다.')
        print('  (끝난값 계약 — 통과 0 · 어김 1 · 안올림 3 · 못잼 4)')
        return 1

    print('  · 새로 생긴 거짓 통과가 없습니다 (쌓인 것 %d곳)' % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
