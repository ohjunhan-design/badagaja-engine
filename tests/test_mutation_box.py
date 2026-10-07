# -*- coding: utf-8 -*-
"""`변이상자` 가 **정말 되돌리는가** — 작은 가짜 폴더로 (2026-10-07).

★ 왜 따로 있나 (바깥 검수 지시)
    「MutationContext 자체를 **작은 가짜 폴더에서 독립 시험**하는 게
      훨씬 빠르고 정확합니다. **최소 7가지만** 보세요」

  전체 뮤테이션(166가지·8분)을 돌려 「모래밭이 깨끗한가」로 재면
  **무엇이 샜는지**를 알 수 없습니다. 여기서는 **한 가지씩** 봅니다.
  몇 초면 끝납니다.

★ 함께 보는 것 — **금지 패턴 정적 감사**
    「사이트 변이 함수 안에서 **직접 호출 = FAIL**」
  `def X(사본, 상자)` 안에서 `io.write`·`os.remove`·`os.makedirs`·
  `shutil.copy*` 를 **직접** 부르면 되돌릴 수 없습니다.

쓰는 법
    python tests/test_mutation_box.py
"""
import ast
import io as _io
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))

통과, 실패 = 0, []


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s %s' % (이름, 덧))


def 지문(뿌리):
    """작은 폴더의 **내용 지문** — 폴더까지 셉니다."""
    import hashlib
    h = hashlib.sha256()
    for 터, 폴더들, 것들 in os.walk(뿌리):
        폴더들.sort()
        for 이름 in sorted(폴더들):
            h.update(('D:' + os.path.relpath(os.path.join(터, 이름), 뿌리)
                      .replace(os.sep, '/')).encode('utf-8'))
        for 이름 in sorted(것들):
            길 = os.path.join(터, 이름)
            h.update(os.path.relpath(길, 뿌리).replace(os.sep, '/')
                     .encode('utf-8'))
            with open(길, 'rb') as f:
                h.update(f.read())
    return h.hexdigest()


def 가짜밭():
    """작은 가짜 site — 112MB 가 아니라 몇 KB 입니다."""
    t = tempfile.mkdtemp(prefix='상자시험-')
    밭 = os.path.join(t, 'site')
    os.makedirs(os.path.join(밭, 'fish'))
    _io.open(os.path.join(밭, 'index.html'), 'w', encoding='utf-8').write(
        '<html><body><p>2026년 9월</p></body></html>')
    _io.open(os.path.join(밭, 'fish', 'bollak.html'), 'w',
             encoding='utf-8').write('<html><body>볼락</body></html>')
    with open(os.path.join(밭, 'favicon.ico'), 'wb') as f:
        f.write(b'\x00\x01\x02\x03')
    return t, 밭


def 한판(이름, 고치기, 상자꾸러미):
    """바꾸고 · 감지되는지 보고 · 되돌린 뒤 **완전히 같은지** 봅니다."""
    t, 밭 = 가짜밭()
    try:
        처음 = 지문(밭)
        상자 = 상자꾸러미.변이상자(밭)
        터짐 = None
        try:
            고치기(밭, 상자)
        except Exception as e:          # 7번 — 시험 중 예외
            터짐 = e
        감지 = 상자.바꾼것있나()
        상자.되돌리기()
        뒤 = 지문(밭)
        봄('%s — 바뀐 것을 안다' % 이름, 감지,
           '(터짐: %s)' % 터짐 if 터짐 else '')
        봄('%s — 되돌리면 처음과 같다' % 이름, 뒤 == 처음,
           '처음 %s / 뒤 %s' % (처음[:12], 뒤[:12]))
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 시험_상자():
    print('[1] 변이상자 — 일곱 가지를 **정말 되돌리는가**')
    import test_checkers as T

    # 1. 같은 크기 문자열 변경 — mtime·크기로는 못 잡는 것
    def 같은크기(밭, 상자):
        p = os.path.join(밭, 'index.html')
        상자.쓰기(p, 상자.읽기(p).replace('2026년 9월', '1999년 1월'))
    한판('① 같은 크기 글자 바꿈', 같은크기, T)

    # 2. 기존 파일 삭제
    def 지움(밭, 상자):
        상자.지우기(os.path.join(밭, 'favicon.ico'))
    한판('② 파일 삭제', 지움, T)

    # 3. 새 파일 생성
    def 새것(밭, 상자):
        상자.쓰기(os.path.join(밭, '새쪽.html'), '<p>새로</p>')
    한판('③ 새 파일 생성', 새것, T)

    # 4. 바이너리 파일 변경
    def 바이너리(밭, 상자):
        상자.쓰기(os.path.join(밭, 'favicon.ico'), b'\xff\xfe\xfd\xfc')
    한판('④ 바이너리 바꿈', 바이너리, T)

    # 5. 빈 폴더 생성 — **파일 목록으로는 안 잡힙니다**
    def 빈폴더(밭, 상자):
        상자.폴더만들기(os.path.join(밭, '빈칸'))
    한판('⑤ 빈 폴더 생성', 빈폴더, T)

    # 6. 중첩 폴더 + 파일
    def 깊게(밭, 상자):
        상자.쓰기(os.path.join(밭, 'a', 'b', 'c.html'), '<p>깊이</p>')
    한판('⑥ 중첩 폴더+파일', 깊게, T)

    # 7. 시험 중 예외 — 바꾸다 터져도 되돌아와야 합니다
    def 터지기(밭, 상자):
        상자.쓰기(os.path.join(밭, 'index.html'), '<p>망가뜨리고</p>')
        raise RuntimeError('일부러 터뜨립니다')
    한판('⑦ 중간에 터져도', 터지기, T)


def 시험_안전망():
    """되돌리기를 **일부러 꺼서** 지문이 반드시 어긋나는지."""
    print('')
    print('[2] 되돌리기를 끄면 **반드시** 들통나는가')
    import test_checkers as T
    t, 밭 = 가짜밭()
    try:
        처음 = 지문(밭)
        상자 = T.변이상자(밭)
        상자.쓰기(os.path.join(밭, 'index.html'), '<p>안 되돌립니다</p>')
        # 되돌리기를 **안 부릅니다**
        봄('되돌리지 않으면 지문이 달라진다', 지문(밭) != 처음)
    finally:
        shutil.rmtree(t, ignore_errors=True)


_금지 = {'io.write', 'os.remove', 'os.makedirs', 'os.rmdir',
         'shutil.copy', 'shutil.copy2', 'shutil.copyfile',
         'shutil.rmtree', 'os.rename'}


def _부른이름(마디):
    것 = []
    while isinstance(마디, ast.Attribute):
        것.append(마디.attr)
        마디 = 마디.value
    if isinstance(마디, ast.Name):
        것.append(마디.id)
    return '.'.join(reversed(것))


def 시험_금지패턴():
    """**사이트 변이 함수 안에서 직접 파일 조작 = 어김** (바깥 검수 ㉮).

    「반드시 상자.쓰기 / 상자.지우기 / 상자.폴더만들기 사용」
    되돌릴 수 없는 조작이 섞이면 **모래밭에 찌꺼기가 남습니다.**
    """
    print('')
    print('[3] 변이 함수 안에서 **직접 파일 조작**을 하지 않는가')
    길 = os.path.join(ROOT, 'tests', 'test_checkers.py')
    나무 = ast.parse(_io.open(길, encoding='utf-8').read())
    나쁨 = []
    for 마디 in ast.walk(나무):
        if not isinstance(마디, ast.FunctionDef):
            continue
        이름들 = [a.arg for a in 마디.args.args]
        if '상자' not in 이름들:
            continue                     # 변이 함수가 아닙니다
        for 속 in ast.walk(마디):
            if isinstance(속, ast.Call):
                부른 = _부른이름(속.func)
                if 부른 in _금지:
                    나쁨.append((마디.name, 부른, 속.lineno))
    if 나쁨:
        print('  ✗ %d곳' % len(나쁨))
        for 함, 부, 줄 in 나쁨[:8]:
            print('      %-18s %-16s %d번째 줄' % (함, 부, 줄))
        print('      → 되돌릴 수 없습니다. 상자.쓰기/지우기/폴더만들기 를 쓰십시오.')
    봄('변이 함수가 직접 파일을 건드리지 않는다', not 나쁨)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('변이상자가 **정말 되돌리는가** (바깥 검수 2026-10-07)')
    print('')
    시험_상자()
    시험_안전망()
    시험_금지패턴()
    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **되돌리지 못하는 뮤테이션은 다음 시험을 더럽힙니다.**')
        return 1
    print('%d가지 모두 통과 — 상자가 제대로 되돌립니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
