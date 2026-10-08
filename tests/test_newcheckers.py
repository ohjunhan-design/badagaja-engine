# -*- coding: utf-8 -*-
"""**새로 만든 검사기도 잘못을 잡는지** 봅니다 (2026-10-08).

★ 왜 따로 만드나 — 바깥 검수가 못박았습니다

    「각 checker 별 good fixture → PASS, broken fixture → FAIL,
      missing dependency → UNAVAILABLE 회귀시험을 추가하세요」

    세 짝 가운데 둘은 이미 자동으로 돕니다 —
      · good      그대로 돌려 끝난값 0 이면 됩니다
      · missing   `tests/test_failclosed.py` 가 **전수로** 봅니다
    남은 **broken** 은 검사기마다 달라 손으로 써야 합니다. 여기입니다.

    `tests/test_checkers.py` 가 이미 1000줄이 넘어, 새로 만든 것은
    여기 모읍니다. 계약-28 은 `tests/test_*.py` 를 **모두** 봅니다.

★ 다루는 검사기 (계약-28 이 이 이름들을 셉니다)
    'check_build_stamp.py' · 'check_coast.py' · 'check_failclosed.py'
    'check_overlay.py' · 'check_panel.py' · 'check_rigref.py'
    'check_search.py' · 'check_nocoord.py' · 'check_backup.py'
    'check_cssdup.py' · 'check_cover.py' · 'check_rigpage.py'
    'check_interact.py' · 'check_visual.py'

★ **정말 망가뜨려야 합니다** (기억 「뮤테이션은 정말 망가뜨려야」)
    살짝 건드려 놓고 「잡았다」 하면 헛돕니다. 검사기가 보는 바로
    그것을 없애거나 어긋나게 합니다.

쓰는 법
    python tests/test_newcheckers.py
"""
import io as _io
import os
import re
import sys
import json
import shutil
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io          # noqa: E402
from engine import isolate     # noqa: E402

통과, 실패 = 0, []


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s   %s' % (이름, (덧 or '')[-300:]))


class 결과(str):
    끝난값 = None


def 돌리기(도구, 뿌리=None, 인자=(), 시간=900):
    """검사기를 **사본에 대고** 돌립니다. 진짜 트리는 안 건드립니다."""
    환 = dict(os.environ)
    환['PYTHONIOENCODING'] = 'utf-8'
    환['PYTHONUTF8'] = '1'
    자리 = 뿌리 or ROOT
    try:
        r = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(자리, 'engine', 도구)] + list(인자),
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', env=환, cwd=자리, timeout=시간)
        글 = 결과((r.stdout or '') + (r.stderr or ''))
        글.끝난값 = r.returncode
        return 글
    except subprocess.TimeoutExpired:
        글 = 결과('시간이 넘었습니다')
        글.끝난값 = None
        return 글


# ──────────────────────────────────────────────────────────
def 시험_판지문():
    """'check_build_stamp.py' — 쪽마다 판이 갈리면 잡는가"""
    print('[1] check_build_stamp — 판이 갈리면 잡는가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, 'site')
        쪽들 = []
        for 뿌, _, 들 in os.walk(밭):
            for 이름 in 들:
                if 이름.endswith('.html'):
                    쪽들.append(os.path.join(뿌, 이름))
        if not 쪽들:
            봄('쪽이 있어야 잽니다', False, 'site/ 가 비었습니다')
            return
        # ★ **정말 망가뜨립니다** — 한 쪽의 판 지문만 딴 값으로
        길 = 쪽들[0]
        글 = io.read(길)
        새 = re.sub(r'(name="badagaja-build"\s+content=")[^"]*(")',
                    r'\g<1>deadbee\g<2>', 글, count=1)
        봄('지문을 바꿀 수 있다', 새 != 글, '지문 태그를 못 찾았습니다')
        io.write(길, 새)
        난것 = 돌리기('check_build_stamp.py', 뿌리=뿌리)
        봄('한 쪽만 판이 다르면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)


def 시험_좌표():
    """'check_coast.py' — 바다에서 먼 좌표를 잡는가"""
    print('[2] check_coast — 뭍 한복판 좌표를 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'data', 'raw', 'points', 'jeonnam.json')
        d = json.loads(io.read(길))
        것들 = d.get('포인트') or d.get('points') or d
        옮긴것 = 0
        for x in 것들:
            좌 = x.get('좌표') or {}
            if 좌.get('위도') is not None:
                # ★ 서울 한복판으로 옮깁니다 — 바다에서 30km 넘습니다
                좌['위도'], 좌['경도'] = 37.5665, 126.9780
                옮긴것 += 1
            if 옮긴것 >= 3:
                break
        봄('좌표를 옮길 수 있다', 옮긴것 >= 3)
        io.write(길, json.dumps(d, ensure_ascii=False))
        난것 = 돌리기('check_coast.py', 뿌리=뿌리, 인자=['--strict'])
        봄('뭍 한복판으로 옮기면 FAIL 로 잡는다',
           ('FAIL' in 난것 and 'FAIL           0' not in 난것)
           or 난것.끝난값 == 1, 난것)


def 시험_덧그림():
    """'check_overlay.py' — 사진 위 덧그림을 잡는가"""
    print('[3] check_overlay — 사진 위에 덧그린 것을 잡는가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, 'site')
        골랐나 = None
        for 뿌, _, 들 in os.walk(밭):
            for 이름 in 들:
                if 이름.endswith('.html'):
                    p = os.path.join(뿌, 이름)
                    if '<svg' in io.read(p, default=''):
                        골랐나 = p
                        break
            if 골랐나:
                break
        if not 골랐나:
            봄('svg 가 든 쪽이 있어야 잽니다', False)
            return
        글 = io.read(골랐나)
        # ★ 사진을 깔고 그 위에 그림을 얹습니다 — 검사기가 막는 꼴
        # ★ **실제 덧그림처럼** — 사진 위에 「서는 자리」를 찍습니다
        #   (검사기가 막는 조건: 사진이 깔린 그림 안에 자리를 주장하는 말)
        덧 = ('<figure class="rig-guide" style="position:relative">'
              '<img src="img/a.jpg" alt="a">'
              '<svg viewBox="0 0 10 10" style="position:absolute;'
              'left:0;top:0"><circle cx="5" cy="5" r="2"/>'
              '<text x="5" y="8">서는 자리</text></svg>'
              '</figure>')
        io.write(골랐나, 글.replace('</body>', 덧 + '</body>', 1))
        난것 = 돌리기('check_overlay.py', 뿌리=뿌리, 인자=['--strict'])
        봄('사진 위에 그림을 얹으면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)


def 시험_상세패널():
    """'check_panel.py' — 패널 스크립트가 빠지면 잡는가"""
    print('[4] check_panel — 패널에 필요한 것이 빠지면 잡는가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, 'site', 'point')
        골랐나 = None
        for 뿌, _, 들 in os.walk(밭):
            for 이름 in 들:
                if 이름.endswith('.html'):
                    p = os.path.join(뿌, 이름)
                    if 'point-panel.js' in io.read(p, default=''):
                        골랐나 = p
                        break
            if 골랐나:
                break
        if not 골랐나:
            봄('패널을 켠 쪽이 있어야 잽니다', False)
            return
        글 = io.read(골랐나)
        # ★ 패널 스크립트를 **통째로 뺍니다**
        새 = re.sub(r'<script[^>]*point-panel\.js[^>]*>\s*</script>', '',
                    글, count=1)
        봄('패널 스크립트를 뺄 수 있다', 새 != 글)
        io.write(골랐나, 새)
        난것 = 돌리기('check_panel.py', 뿌리=뿌리, 인자=['--strict'])
        봄('패널 스크립트가 빠지면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)


def 시험_채비자산():
    """'check_rigref.py' — 채비 사진이 없어지면 잡는가"""
    print('[5] check_rigref — 채비 사진이 없어지면 잡는가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, 'data', 'img', 'rig')
        것들 = sorted(f for f in os.listdir(밭)) if os.path.isdir(밭) else []
        if not 것들:
            봄('채비 사진이 있어야 잽니다', False)
            return
        # ★ **정말 지웁니다** — 이름만 바꾸면 검사기가 다른 길로 찾습니다
        지움 = 0
        for f in 것들:
            os.remove(os.path.join(밭, f))
            지움 += 1
        봄('채비 사진을 지울 수 있다 (%d장)' % 지움, 지움 > 0)
        난것 = 돌리기('check_rigref.py', 뿌리=뿌리, 인자=['--strict'])
        봄('채비 사진이 없으면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)


def 시험_찾기():
    """'check_search.py' — 거짓 검색창을 잡는가"""
    print('[6] check_search — 동작하지 않는 검색창을 잡는가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, 'site')
        길 = os.path.join(밭, 'index.html')
        if not os.path.exists(길):
            봄('첫 쪽이 있어야 잽니다', False)
            return
        글 = io.read(길)
        # ★ 아무 데도 안 걸린 **가짜 검색창**을 넣습니다
        가짜 = ('<form action="/nowhere-search"><input type="search" '
                'name="q" placeholder="포인트 검색"></form>')
        io.write(길, 글.replace('</body>', 가짜 + '</body>', 1))
        난것 = 돌리기('check_search.py', 뿌리=뿌리, 인자=['--strict'])
        봄('아무 데도 안 걸린 검색창을 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)


def 시험_거짓통과():
    """'check_failclosed.py' — 새 거짓 통과를 잡는가"""
    print('[7] check_failclosed — 새로 생긴 거짓 통과를 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'engine', 'check_zz시험용.py')
        io.write(길, '\n'.join([
            '# -*- coding: utf-8 -*-',
            '"""시험이 만든 가짜 검사기입니다."""',
            'import sys',
            '',
            '',
            'def main():',
            '    try:',
            '        import 없는꾸러미',
            '    except ImportError:',
            '        return 0          # ← 못 쟀는데 통과',
            '    return 0',
            '',
            '',
            "if __name__ == '__main__':",
            '    sys.exit(main())',
            '']))
        난것 = 돌리기('check_failclosed.py', 뿌리=뿌리, 인자=['--strict'])
        봄('새 검사기가 못 쟀는데 통과하면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)
        봄('어느 줄인지 말해 준다', 'check_zz시험용.py' in 난것, 난것)


def 시험_되돌릴것():
    """'check_backup.py' — 받아 둔 것이 없으면 못잼을 내는가"""
    print('[8] check_backup — 받아 둔 것이 없으면 못잼(4)인가')
    with isolate.일터() as 뿌리:
        밭 = os.path.join(뿌리, '_before')
        if os.path.isdir(밭):
            shutil.rmtree(밭, ignore_errors=True)
        난것 = 돌리기('check_backup.py', 뿌리=뿌리, 시간=300)
        봄('받아 둔 것이 없으면 **통과가 아니다** (끝난값 4)',
           난것.끝난값 == 4, 난것)
        봄('--strict 없이도 똑같이 못잼이다',
           돌리기('check_backup.py', 뿌리=뿌리, 시간=300).끝난값 == 4)


def 시험_이름겹침():
    """'check_cssdup.py' — 같은 이름을 두 뜻으로 쓰면 잡는가

    ★ 2026-10-08 실제로 사이트를 망가뜨린 그 줄을 **그대로** 되살립니다.
      `.rig-zoom` 은 「크게 보는 칸」(평소 display:none)이었는데
      「크게 보기 단추」에 같은 이름을 썼고, 뒤쪽 규칙이 그 숨김을
      덮어 1372x980 확대 그림이 채비 16쪽에서 늘 펼쳐졌습니다.
    """
    print('[9] check_cssdup — 같은 이름을 두 뜻으로 쓰면 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'assets', 'css', 'site.css')
        글 = io.read(길)
        # ★ **정말 그때처럼** — 단추 이름을 확대 칸과 같게 되돌립니다
        옛 = '.fish-rig-zoom{position:absolute;right:10px;bottom:10px;'
        봄('그때의 줄을 되살릴 수 있다', 옛 in 글, '앵커를 못 찾았습니다')
        io.write(길, 글.replace(
            옛, '.rig-zoom{position:absolute;right:10px;bottom:10px;', 1))
        난것 = 돌리기('check_cssdup.py', 뿌리=뿌리, 인자=['--strict'],
                      시간=180)
        봄('`display` 가 none / inline-flex 로 갈리면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)
        봄('어느 이름인지 말해 준다', 'rig-zoom' in 난것, 난것)

    # 손대지 않은 판은 통과해야 합니다 — 거짓 양성이 없어야 둘 수 있습니다
    봄('지금 차림표는 통과한다',
       돌리기('check_cssdup.py', 인자=['--strict'], 시간=180).끝난값 == 0)


def 시험_덮는것():
    """'check_cover.py' — 본문을 덮는 것을 잡는가

    ★ 2026-10-08 — 확대 그림이 채비 16쪽을 덮었는데 **기존 검사기
      어느 것도 못 잡았습니다.** 그때의 차림표를 그대로 되살립니다.
    """
    print('[10] check_cover — 본문을 덮는 것을 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'assets', 'css', 'site.css')
        글 = io.read(길)
        옛 = '.fish-rig-zoom{position:absolute;right:10px;bottom:10px;'
        봄('그때의 줄을 되살릴 수 있다', 옛 in 글)
        io.write(길, 글.replace(
            옛, '.rig-zoom{position:absolute;right:10px;bottom:10px;', 1))
        # ★ **쪽을 다시 만들어야** 차림표가 site/ 로 갑니다.
        #   안 만들고 재면 옛 차림표를 재어 「탈 없음」이 나옵니다 —
        #   2026-10-08에 제가 그렇게 두 번 속았습니다.
        만들기 = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(뿌리, 'engine', 'build.py')],
            cwd=뿌리, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=900)
        봄('사본에서 다시 만들 수 있다', 만들기.returncode == 0,
           (만들기.stderr or '')[-200:])
        난것 = 돌리기('check_cover.py', 뿌리=뿌리, 시간=900)
        봄('본문을 덮으면 막는다 (끝난값 1)', 난것.끝난값 == 1, 난것)
        봄('어느 쪽·무엇인지 말해 준다',
           'rig-zoom' in 난것 and '덮습니다' in 난것, 난것)


def 시험_채비쪽그림():
    """'check_rigpage.py' — 바깥 검수가 정한 네 가지를 잡는가

      초기 overlay 숨김 · 확대 CTA · 가로 넘침 · 1100px 초과 그림
    """
    print('[11] check_rigpage — 채비 쪽 네 가지를 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'assets', 'css', 'site.css')
        글 = io.read(길)
        옛 = '.fish-rig-zoom{position:absolute;right:10px;bottom:10px;'
        봄('그때의 줄을 되살릴 수 있다', 옛 in 글)
        io.write(길, 글.replace(
            옛, '.rig-zoom{position:absolute;right:10px;bottom:10px;', 1))
        만들기 = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(뿌리, 'engine', 'build.py')],
            cwd=뿌리, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=900)
        봄('사본에서 다시 만들 수 있다', 만들기.returncode == 0)
        난것 = 돌리기('check_rigpage.py', 뿌리=뿌리, 시간=1500)
        봄('확대 칸이 펼쳐져 있으면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)
        봄('「처음부터 펼쳐져」라고 말해 준다',
           '처음부터 펼쳐져' in 난것, 난것)
        봄('1100px 넘는 그림도 함께 잡는다',
           '1100 넘음' in 난것, 난것)


def 시험_눌러보기():
    """'check_interact.py' — 덮개가 안 닫히면 잡는가

    손님이 확대 그림에 **갇히는** 것이 가장 나쁩니다.
    닫는 길을 없애 보고 잡는지 봅니다.
    """
    print('[12] check_interact — 덮개가 안 닫히면 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'assets', 'css', 'site.css')
        글 = io.read(길)
        # ★ **정말 못 닫게** — 닫기 단추와 배경을 모두 숨깁니다
        옛 = '.rig-zoom-bg{position:absolute;inset:0}'
        봄('닫는 길을 없앨 수 있다', 옛 in 글)
        io.write(길, 글.replace(
            옛, '.rig-zoom-bg{display:none}' + chr(10)
            + '.rig-zoom-x{display:none}', 1))
        만들기 = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(뿌리, 'engine', 'build.py')],
            cwd=뿌리, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=900)
        봄('사본에서 다시 만들 수 있다', 만들기.returncode == 0)
        난것 = 돌리기('check_interact.py', 뿌리=뿌리, 시간=2400)
        봄('닫는 길이 없으면 막는다 (끝난값 1)', 난것.끝난값 == 1, 난것)
        봄('「닫는 길이 없습니다」라고 말해 준다',
           '닫는 길이 없습니다' in 난것, 난것)


def 시험_눈으로볼때():
    """'check_visual.py' — 빈 칸을 잡는가"""
    print('[13] check_visual — 글 없는 빈 칸을 잡는가')
    with isolate.일터() as 뿌리:
        길 = os.path.join(뿌리, 'engine', 'template.py')
        글 = io.read(길)
        옛 = "    s = _빈칸지우기(s)"
        봄('빈 칸 지우기를 끌 수 있다', 옛 in 글)
        io.write(길, 글.replace(옛, "    pass  # 일부러 끔", 1))
        만들기 = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(뿌리, 'engine', 'build.py')],
            cwd=뿌리, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=900)
        봄('사본에서 다시 만들 수 있다', 만들기.returncode == 0)
        난것 = 돌리기('check_visual.py', 뿌리=뿌리, 시간=2400)
        봄('글 없는 빈 칸이 생기면 막는다 (끝난값 1)',
           난것.끝난값 == 1, 난것)
        봄('「비어 있습니다」라고 말해 준다', '비어 있습니다' in 난것, 난것)


def main():
    print('새로 만든 검사기도 잘못을 잡는지 봅니다 (2026-10-08)')
    print('  바깥 검수 — 「broken fixture → FAIL 회귀시험을 추가하세요」')
    print('')
    시험_판지문()
    시험_좌표()
    시험_덧그림()
    시험_상세패널()
    시험_채비자산()
    시험_찾기()
    시험_거짓통과()
    시험_되돌릴것()
    시험_이름겹침()
    시험_덮는것()
    시험_채비쪽그림()
    시험_눌러보기()
    시험_눈으로볼때()
    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  잘못을 못 잡는 검사기는 **없는 것보다 나쁩니다.**')
        return 1
    print('%d가지 모두 통과 — 새 검사기도 잘못을 제대로 잡습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
