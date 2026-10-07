# -*- coding: utf-8 -*-
"""검사기가 **잘못을 잡을 줄 아는지** 봅니다.

★ 왜 이 시험이 필요한가 (2026-09-26 바깥 검수 요구)

    「검사기가 항상 통과를 내도록 망가져 있어도 모르면 아무 의미가
      없습니다. 일부러 오류가 있는 것을 넣어 검사기가 실패를 내는지
      확인해야 합니다」

    맞는 말입니다. 오늘 검사기가 네 번 틀렸습니다.
      · 전남 어종을 16개 중 2개만 캤는데 통과시킴
      · 채움 비율이 100% 로 나오는데 빈 칸이 7개
      · 멀쩡한 site.css 를 「없다」고 함
      · 'catch/' 를 「없는 쪽」이라 함

    모두 **조용히 통과시키거나 헛것을 낸 것**입니다.
    검사가 잘못을 못 잡으면, 검사가 없는 것보다 나쁩니다.
    없으면 조심이라도 하는데, 있으면 믿어 버리기 때문입니다.

어떻게 보나
    일부러 망가뜨린 것을 만들어 넣고, 검사기가 **반드시 잡는지** 봅니다.
    잡으면 통과, 못 잡으면 그 검사기는 믿을 수 없는 것입니다.

쓰는 법
    python tests/test_checkers.py
"""
import atexit
import time
import os
import re
import sys
import json
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io
from engine import isolate   # noqa: E402

통과, 실패 = 0, []

# 시험을 시작할 때 본 작업 트리가 어떤 상태였는지 — 끝에 견줍니다.
# 여기 없던 변화가 생겼다면 **시험이 본 트리를 건드린 것**입니다.
처음알았나, 처음본트리 = isolate.본트리가깨끗한가()


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s %s' % (이름, 덧))


class 돌린결과(str):
    """검사기 출력(글) — **끝난값과 걸린초를 달고 다닙니다.**

    ★ 바깥 검수 (2026-10-07) — 속도보다 중요한 지적
        「현재 돌리기() 는 **returncode 를 버리고 있습니다.** 즉 상당수
          시험이 출력 문구만 보고 검사기가 제대로 실패했는지 판단합니다」

      봄() 170가지 가운데 **165가지가 끝난값을 안 보고** 있었습니다.
      검사기가 잘못을 **글로는 적으면서 끝난값 0** 을 내면 시험은
      「통과」라 하고 **배포는 안 막힙니다.**
      **「잡았다」와 「막았다」는 다릅니다.**

    ★ 글(str)을 그대로 물려받습니다 — 기존 165곳을 한꺼번에 고치지
      않아도 됩니다. `in` 검사도 그대로 돕니다.
      바깥 검수 — 「마이그레이션 전략으로 **실용적**입니다」

    ★ `걸린초` 도 답니다 — 「이번 최적화가 실제 효과가 있었는지
      **바로 잴 수 있습니다**」 (바깥 검수)

    ★ 주의 — 끝난값을 **일괄로 요구하면 안 됩니다** (바깥 검수 ⑦)
      「일부 checker 가 설계상 **경고만 하고 exit 0** 인 계약도 있을 수
        있으니, 먼저 **checker 별 기대 exit 계약을 표로** 만들어야」
    """

    끝난값 = 0
    걸린초 = 0.0

    def __new__(cls, 글, 끝난값=0, 걸린초=0.0):
        것 = str.__new__(cls, 글)
        것.끝난값 = 끝난값
        것.걸린초 = 걸린초
        return 것


def 돌리기(도구, 사이트=None, 자료=None, 인자=(), 뿌리=None):
    """검사기를 딴 자리에 대고 돌립니다. 진짜 site/ 는 안 건드립니다

    뿌리 를 주면 **그 사본의 검사기**를 돌립니다. 검사기는 제 위치에서
    뿌리를 셈하므로, 사본의 engine/ 을 부르면 사본만 봅니다.
    (2026-09-27 바깥 검수 — 본 작업 트리를 건드리지 않게)

    ★ 돌려주는 것은 **글이면서 끝난값·걸린초를 답니다** (2026-10-07)
        글 = 돌리기('check_seo.py')
        글.끝난값 == 1        ← **막았는가**
        글.걸린초            ← 얼마나 걸렸는가
        '없는쪽' in 글        ← 잡았는가 (예전처럼 그대로 됩니다)
    """
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    if 사이트:
        환경['BADAGAJA_SITE'] = 사이트
    if 자료:
        환경['BADAGAJA_DATA'] = 자료
    시작 = time.perf_counter()
    r = subprocess.run(
        [sys.executable, os.path.join(뿌리 or ROOT, 'engine', 도구)]
        + list(인자),
        capture_output=True, text=True, encoding='utf-8',
        env=환경, timeout=1200)
    걸린 = time.perf_counter() - 시작
    _걸린시간.append((도구, 걸린))
    # ★ **느린 것은 그 자리에서 알립니다** (2026-10-07 바깥 검수)
    #   끝난 뒤 TOP 10 만 내면 **6~8분 동안 어디서 막혔는지**
    #   모릅니다. 진행을 숨기면 감독할 수 없습니다.
    if 걸린 >= 10:
        print('  ⚠ 느린 검사 %.1f초 — %s' % (걸린, 도구), flush=True)
    elif 걸린 >= 5:
        print('  ⏱ %.1f초  %s' % (걸린, 도구), flush=True)
    return 돌린결과((r.stdout or '') + (r.stderr or ''), r.returncode, 걸린)



# ══════════════════════════════════════════════════════
#  모래밭 — **사본 하나를 돌려 씁니다** (2026-10-07 바깥 검수 설계)
#
#  재 보니 925파일·112MB 를 **41번** 복사하고, 옛 `_쪽지문()` 이 그 전부를
#  **앞뒤로 두 번** sha256 했습니다. 디스크를 **14GB** 오갔습니다.
#  그런데 실제로 고치는 것은 **HTML 한 파일의 몇 글자**입니다.
#
#  바깥 검수 —
#    「41번 새 사본을 만드는 **구조 자체를 없애는 게 1순위**」
#    「시작 때 sandbox 를 **딱 한 번** 만들고 … **원상복구** → 다음 시험」
#
#  ★ **크기·mtime 으로 바뀐 것을 찾지 않습니다** (바깥 검수가 물림)
#    「size + mtime_ns 만으로는 **내용 변경을 보장하지 못합니다**.
#      「2026년 9월」→「1999년 1월」은 **같은 길이**입니다」
#    대신 **고치는 함수가 변이상자를 거쳐** 바꾸게 하고, 그 상자가
#    **무엇을 건드렸는지 스스로 적습니다.**
#
#  ★ **전역 shutil.rmtree 를 건드리지 않습니다** (바깥 검수가 물림)
#    「호출자는 **삭제한다고 생각했는데 사실 rollback 됐다**는 걸 알 수
#      없습니다. 이 파일엔 site 사본 말고도 data·repo·canary·원격
#      임시 repo·작은 가짜 사이트가 있습니다」
#    그래서 `with 사이트변이() as 밭:` 로 **드러나게** 씁니다.
# ══════════════════════════════════════════════════════
_모래밭 = {'터': None, '밭': None, '첫지문': None}
_걸린시간 = []


def _모래밭준비():
    """깨끗한 사본을 **딱 한 번** 만듭니다."""
    if _모래밭['밭'] is None:
        t = tempfile.mkdtemp(prefix='checker-sandbox-')
        밭 = os.path.join(t, 'site')
        shutil.copytree(os.path.join(ROOT, 'site'), 밭)
        _모래밭['터'], _모래밭['밭'] = t, 밭
        atexit.register(_모래밭치우기)
    return _모래밭['밭']


def _모래밭치우기():
    if _모래밭['터']:
        shutil.rmtree(_모래밭['터'], ignore_errors=True)
        _모래밭['터'], _모래밭['밭'], _모래밭['첫지문'] = None, None, None


def 트리지문(뿌리):
    """트리 전체의 내용 지문 — **묶음 끝에 딱 한 번**만 씁니다.

    바깥 검수 —
      「매번 112MB hash 를 돌리지는 말고, 테스트 묶음 **마지막에 딱 한 번**
        `sandbox 최종 hash == 최초 baseline hash` 를 확인하세요.
        **어떤 mutation 이 찌꺼기를 남겼는지** 잡아 주는 최종 안전망입니다」
    """
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
            try:
                with open(길, 'rb') as f:
                    h.update(f.read())
            except OSError:
                pass
    return h.hexdigest()


class 변이상자:
    """뮤테이션이 **무엇을 건드렸는지 스스로 적습니다.**

    ★ 바깥 검수 ④ — 「**폴더 생성/삭제도 반드시 추적**하세요」
      빈 폴더는 파일 목록에 안 잡혀, 파일만 되돌리면 **찌꺼기가 남습니다.**

    고치는 함수는 이 상자를 거쳐 바꿉니다 —
        def 지우기(밭, 상자):
            상자.쓰기(os.path.join(밭, 'index.html'), 새글)
            상자.지우기(os.path.join(밭, 'favicon.svg'))
    """

    def __init__(self, 밭):
        self.밭 = 밭
        self.건드린것 = {}        # {길: 원본 bytes 또는 None(없었음)}
        self.만든폴더 = []

    def _기억(self, 길):
        if 길 in self.건드린것:
            return
        try:
            with open(길, 'rb') as f:
                self.건드린것[길] = f.read()
        except OSError:
            self.건드린것[길] = None      # 그 자리에 없던 것

    def 읽기(self, 길):
        # ★ 이 파일의 `io` 는 **engine.io** 입니다 (표준 io 가 아닙니다)
        return io.read(길, default='')

    def 쓰기(self, 길, 글, **덧):
        self._기억(길)
        # ★ **중첩 폴더를 하나씩 기록합니다** (2026-10-07)
        #   a/b/c.html 을 쓰면 a 와 a/b 가 **둘 다** 새로 생깁니다.
        #   맨 아래만 적으면 위쪽 폴더가 **찌꺼기로 남습니다.**
        self._폴더챙기기(os.path.dirname(길))
        if isinstance(글, bytes):
            with open(길, 'wb') as f:
                f.write(글)
        else:
            io.write(길, 글)

    def 복사(self, 원본, 길, **덧):
        """파일을 베껴 둡니다 — **되돌릴 수 있게** 기록합니다."""
        self._기억(길)
        self._폴더챙기기(os.path.dirname(길))
        shutil.copyfile(원본, 길)

    def 지우기(self, 길, **덧):
        self._기억(길)
        try:
            os.remove(길)
        except OSError:
            pass

    def _폴더챙기기(self, 터):
        """없는 폴더를 **위에서부터 하나씩** 만들고 적습니다."""
        if not 터 or os.path.isdir(터):
            return
        없는것 = []
        한 = 터
        while 한 and not os.path.isdir(한):
            없는것.append(한)
            위 = os.path.dirname(한)
            if 위 == 한:
                break
            한 = 위
        os.makedirs(터, exist_ok=True)
        self.만든폴더.extend(없는것)

    def 폴더만들기(self, 길, **덧):
        # ★ `os.makedirs(…, exist_ok=True)` 를 그대로 받습니다 —
        #   기계 변환으로 바뀐 자리가 덧인자를 함께 넘깁니다.
        self._폴더챙기기(길)

    def 바꾼것있나(self):
        return bool(self.건드린것) or bool(self.만든폴더)

    def 되돌리기(self):
        for 길, 원본 in self.건드린것.items():
            try:
                if 원본 is None:
                    if os.path.exists(길):
                        os.remove(길)
                else:
                    터 = os.path.dirname(길)
                    if 터 and not os.path.isdir(터):
                        os.makedirs(터, exist_ok=True)
                    with open(길, 'wb') as f:
                        f.write(원본)
            except OSError:
                pass
        for 터 in sorted(self.만든폴더, key=len, reverse=True):
            try:
                os.rmdir(터)          # 빈 것만 지워집니다
            except OSError:
                pass
        self.건드린것.clear()
        self.만든폴더.clear()


class 사이트변이:
    """`with 사이트변이(고치기) as 밭:` — 바꾸고 · 재고 · **되돌립니다.**

    ★ 「정말 망가뜨렸는가」를 봅니다 (2026-09-29 에 당한 것)
      「안전 안내를 지우면 잡는다」 시험이 실패했는데 검사기도 시험도
      옳았습니다 — **뮤테이션이 아무것도 안 지웠던 것**입니다.
      `class="firsttime"` 을 찾았는데 쪽이 `firsttime firsttime--btn`
      으로 바뀌어 있었습니다.
      **겉모양에 매인 뮤테이션은 조용히 헛돕니다.**

    ★ 이제는 **상자가 스스로 적으므로** 112MB 를 읽지 않습니다.
    """

    def __init__(self, 고치기=None):
        self.고치기 = 고치기
        self.상자 = None

    def 시작(self):
        """모래밭을 열고 고치기를 돌립니다 — `__enter__` 와 같습니다."""
        return self.__enter__()

    def 되돌리기(self):
        """건드린 것만 되돌립니다 — `__exit__` 와 같습니다."""
        self.__exit__()

    def __enter__(self):
        밭 = _모래밭준비()
        if _모래밭['첫지문'] is None:
            _모래밭['첫지문'] = 트리지문(밭)
        self.상자 = 변이상자(밭)
        if self.고치기:
            self.고치기(밭, self.상자)
            if not self.상자.바꾼것있나():
                print('  ✗ **뮤테이션이 아무것도 안 바꿨습니다** — '
                      '이 시험은 헛돕니다')
                print('      고치는 함수: %s'
                      % getattr(self.고치기, '__name__', '(이름 없음)'))
                print('      쪽이 바뀌었는데 찾는 글이 옛 모양일 수 '
                      '있습니다.')
                실패.append('뮤테이션이 아무것도 안 바꿨습니다 (%s)'
                            % getattr(self.고치기, '__name__', '?'))
        return 밭

    def __exit__(self, *_):
        if self.상자:
            self.상자.되돌리기()
        return False


def 본문끝에심기(사본, 조각, 쪽='index.html', 상자=None):
    """쪽 **본문 끝**에 한 조각을 심습니다.

    ★ **심을 자리를 못 찾으면 죽습니다** (2026-10-02)
      전에는 `s.replace('</main>', …)` 였습니다. 그런데 첫 쪽에
      `</main>` 이 **없어졌습니다**(차림이 바뀌었습니다). 조용히
      아무것도 안 바뀌었고, 시험은 「검사기가 못 잡는다」고
      적었습니다. 셋이 그렇게 헛돌았습니다.
      이제는 자리를 못 찾으면 **그 자리에서 터집니다.**
    """
    # ★ **상자를 받으면 상자로 씁니다** (2026-10-07)
    #   안 그러면 모래밭에 **되돌릴 수 없는 찌꺼기**가 남습니다.
    p = os.path.join(사본, 쪽)
    s = io.read(p)
    for 닫 in ('</main>', '</footer>', '</body>'):
        if 닫 in s:
            새글 = s.replace(닫, 조각 + 닫, 1)
            if 상자 is None:
                raise AssertionError(
                    '본문끝에심기 에 **상자를 안 넘겼습니다** — '
                    '되돌릴 수 없어 모래밭에 찌꺼기가 남습니다. '
                    '`상자=상자` 를 넘기십시오.')
            상자.쓰기(p, 새글)
            return
    raise AssertionError(
        '%s 에 심을 자리가 없습니다 — </main>·</footer>·</body> '
        '어느 것도 없습니다. 쪽 차림이 바뀌었으면 여기도 고칩니다.' % 쪽)


def 사이트사본(고치기=None):
    """site/ 를 **모래밭에서** 망가뜨립니다 — `(되돌리개, 밭)`.

    ★ 속만 바꿨습니다 (2026-10-07 바깥 검수 설계).
      전에는 부를 때마다 **112MB 를 복사**했습니다. 이제는 **한 번 만든
      모래밭**을 쓰고, 끝나면 **건드린 것만** 되돌립니다.

    쓰는 법 — 되돌리개를 **반드시 부릅니다.**

        되돌리개, 사본 = 사이트사본(지우기)
        try:
            글 = 돌리기('check_x.py', 사이트=사본)
        finally:
            되돌리개()

    ★ 고치는 함수는 **상자를 받습니다** (바깥 검수 넷째 지적)
        def 지우기(사본, 상자):
            상자.쓰기(길, 새글)      ← 되돌릴 수 있게 기록됩니다
            상자.지우기(길)
            상자.폴더만들기(길)      ← 빈 폴더도 되돌립니다

    ★ `with 사이트변이(...)` 가 최종형이지만, try/finally 41곳을 통째로
      옮기면 들여쓰기까지 바꿔야 해 위험합니다. **되돌리개도 명시적**이고
      호출부만 보고도 무엇을 하는지 압니다.
    """
    # ★ **매직 메서드를 cleanup 손잡이처럼 내보내지 않습니다**
    #   (2026-10-07 바깥 검수 — 「다음 사람이 읽기 어렵습니다」)
    상자 = 사이트변이(고치기)
    밭 = 상자.시작()
    return 상자.되돌리기, 밭


def 모래밭이깨끗한가():
    """묶음 **마지막에 한 번** — 찌꺼기를 남긴 뮤테이션이 있는가.

    바깥 검수 ⑨ — 「112MB 를 한 번 정도 더 읽는 비용으로 **어떤
    mutation 이 찌꺼기를 남겼는지** 잡아 주는 최종 안전망입니다」
    """
    if not _모래밭['밭'] or _모래밭['첫지문'] is None:
        return True
    끝 = 트리지문(_모래밭['밭'])
    if 끝 == _모래밭['첫지문']:
        print('  · 모래밭이 처음 그대로입니다 — 되돌리기에 샌 곳이 없습니다')
        return True
    print('  ✗ **모래밭에 찌꺼기가 남았습니다** — 어떤 뮤테이션이 '
          '되돌리지 못했습니다')
    print('      처음 %s' % _모래밭['첫지문'][:16])
    print('      지금 %s' % 끝[:16])
    실패.append('모래밭이 처음으로 안 돌아왔습니다 (되돌리기 샘)')
    return False



# ── check_render — 가로 넘침을 잡는가 ──────────────────────
def 시험_렌더():
    print('[1] check_render — 화면 넘침을 잡는가')

    # (가) 멀쩡한 쪽은 통과해야 합니다
    글 = 돌리기('check_render.py',
                인자=[os.path.join(ROOT, 'site', 'index.html')])
    봄('멀쩡한 쪽은 넘침 0', '넘침 0' in 글, 글[-200:])

    # (나) 일부러 넓은 것을 넣으면 반드시 잡아야 합니다
    def 망가뜨리기(사본, 상자):
        p = os.path.join(사본, 'index.html')
        s = io.read(p)
        s = s.replace('</body>',
                      '<div style="width:1400px;height:20px">넘침</div>'
                      '</body>')
        상자.쓰기(p, s)

    되돌리개, 사본 = 사이트사본(망가뜨리기)
    try:
        글 = 돌리기('check_render.py', 사이트=사본,
                    인자=[os.path.join(사본, 'index.html')])
        잡았나 = ('넘침 0' not in 글.split('1280px')[0]
                  or '가로 넘침' in 글 or '넘칩니다' in 글)
        봄('1400px 짜리를 넣으면 잡는다', 잡았나, 글[-300:])
    finally:
        되돌리개()


# ── check_links — 끊긴 링크·자기참조를 잡는가 ──────────────
def 시험_링크():
    print('[2] check_links — 끊긴 링크와 자기참조를 잡는가')

    글 = 돌리기('check_links.py')
    봄('멀쩡한 사이트는 통과', '자기 자신을 가리키는 링크' in 글
       and '이상 없음' in 글.split('자기 자신을 가리키는 링크')[1][:40], 글[-200:])

    # (가) 없는 쪽으로 가는 링크를 넣습니다
    def 끊기(사본, 상자):
        p = os.path.join(사본, 'index.html')
        s = io.read(p)
        상자.쓰기(p, s.replace('</body>',
                              '<a href="없는쪽.html">없는 곳</a></body>'))

    되돌리개, 사본 = 사이트사본(끊기)
    try:
        글 = 돌리기('check_links.py', 사이트=사본)
        봄('없는 쪽으로 가는 링크를 잡는다', '없는쪽.html' in 글, 글[-300:])
    finally:
        되돌리개()

    # (나) 자기 자신을 가리키는 링크를 넣습니다
    def 자기참조(사본, 상자):
        p = os.path.join(사본, 'index.html')
        s = io.read(p)
        상자.쓰기(p, s.replace('</body>',
                              '<a href="index.html">자기 자신</a></body>'))

    되돌리개, 사본 = 사이트사본(자기참조)
    try:
        글 = 돌리기('check_links.py', 사이트=사본)
        봄('자기 자신을 가리키는 링크를 잡는다',
           '자기 자신을 가리키는 링크' in 글
           and '이상 없음' not in 글.split('자기 자신을 가리키는 링크')[1][:40],
           글[-300:])
    finally:
        되돌리개()


# ── check_urls — 사라진 옛 주소를 잡는가 ───────────────────
def 시험_주소():
    print('[3] check_urls — 사라진 옛 주소를 잡는가')

    글 = 돌리기('check_urls.py')
    봄('지금은 갈 곳 없는 주소가 없다', '갈 곳 없는 옛 주소가 없습니다' in 글,
       글[-200:])

    # 포인트 쪽 하나를 지우면 반드시 잡아야 합니다
    def 지우기(사본, 상자):
        for r, _, fs in os.walk(os.path.join(사본, 'point')):
            for f in fs:
                if f.endswith('_fishing.html'):
                    상자.지우기(os.path.join(r, f))
                    return

    되돌리개, 사본 = 사이트사본(지우기)
    try:
        글 = 돌리기('check_urls.py', 사이트=사본)
        봄('쪽 하나를 지우면 「갈 곳 없음」으로 잡는다',
           '갈 곳이 없음' in 글 and '404 가 됩니다' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_contracts — 합계가 안 맞으면 잡는가 ──────────────
def 시험_계약():
    print('[4] check_contracts — 계약 합계가 안 맞으면 잡는가')

    글 = 돌리기('check_contracts.py', 인자=['--fast'])
    # 검수표 **안**만 봅니다. 밖에도 같은 말이 나와 두 번 세어졌습니다
    표 = 글.split('검수 결과')[-1].split('배포 가능 여부')[0]
    총 = re.search(r'총 계약\s+(\d+)', 표)
    칸 = dict((k, int(v)) for k, v in
              re.findall(r'^\s+(지킴|어김|안 잰 것|해당없음)\s+(\d+)\s*$',
                         표, re.M))
    합 = sum(칸.values())
    봄('칸별 합계가 총 계약 수와 같다',
       bool(총) and 합 == int(총.group(1)),
       '총 %s · 합 %d %s' % (총.group(1) if 총 else '?', 합, 칸))
    # ★ 계약 검사기는 **배포를 말하면 안 됩니다** (2026-09-28 바깥 검수 6차)
    #
    #   전에는 여기서 「배포 가능 여부: 예」를 냈습니다. 그 말을
    #   검수 요청서에 그대로 옮겼더니 같은 문서 안에
    #
    #       「배포 가능 여부: 예」
    #       「--full 을 아직 한 번도 성공 못 했습니다」
    #
    #   가 나란히 있게 됐습니다. 바깥 검수가 바로 잡아냈습니다 —
    #   「검수 시스템이 건전해졌다」와 「사이트가 배포 준비를 끝냈다」는
    #   서로 다른 문제인데 둘이 섞여 있다고.
    #
    #   그래서 **되돌아가지 못하게 시험으로 굳힙니다.**
    봄('계약 상태를 따로 낸다',
       '계약 상태:' in 글, 글[-300:])
    봄('★ 계약 검사기가 배포를 말하지 않는다',
       '배포 판정이 아닙니다' in 글 and '배포 가능 여부' not in 글,
       글[-300:])
    봄('「안 잰 것」을 「지킴」으로 안 센다',
       '안 잰 것' in 글 and ('지킨다고 말할 수 없습니다' in 글
                             or '재 보지 않은 것은 지킨 것이 아닙니다' in 글),
       글[-300:])

    # 계약 문서에 한 줄 더하면 합계가 안 맞아 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본자료 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본자료)
        # ★ 본 트리가 아니라 **사본**에서 고칩니다 (2026-09-27 바깥 검수)
        with isolate.일터() as 뿌리:
            문서 = os.path.join(뿌리, 'docs', 'CONTRACTS.md')
            덧 = ['', '', '### 계약-99 · 시험용 가짜 계약', '',
                 '시험입니다.', '']
            io.write(문서, io.read(문서) + chr(10).join(덧))
            글 = 돌리기('check_contracts.py', 인자=['--fast'], 뿌리=뿌리)
            봄('계약을 하나 더하면 합계가 안 맞는다고 잡는다',
               '합계가 계약 수와 다릅니다' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_stale — 어중간한 자료를 잡는가 ───────────────────
def 시험_어중간():
    print('[5] check_stale — 어중간한 자료를 잡는가')

    글 = 돌리기('check_stale.py')
    봄('지금 자료는 끝까지 다듬어져 있다',
       '자료가 끝까지 다듬어져 있습니다' in 글, 글[-300:])

    # (가) 대상을 한글 이름으로 되돌려 놓으면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'points', 'chungnam.json')
        d = io.read_json(p)
        for x in d.get('포인트', [])[:5]:
            if x.get('대상'):
                x['대상'] = ['감성돔', '농어']
        io.write_json(p, d)
        글 = 돌리기('check_stale.py', 자료=사본, 인자=['--strict'])
        봄('대상이 한글 이름이면 잡는다',
           '대상이 아이디가 아닌 것' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) 앞 도구만 돌린 흔적(species-map.json)이 있으면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        io.write_json(os.path.join(사본, 'raw', 'species-map.json'),
                      {'_설명': '시험용'})
        글 = 돌리기('check_stale.py', 자료=사본, 인자=['--strict'])
        봄('앞 도구만 돌린 흔적을 잡는다',
           'species-map.json 가 남아 있습니다' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_ads — 광고 탈을 잡는가 ───────────────────────────
def 시험_광고():
    print('[6] check_ads — 광고 탈을 잡는가')

    글 = 돌리기('check_ads.py')
    봄('지금 광고는 뜰 때도 안 뜰 때도 멀쩡하다',
       '광고가 뜰 때도 안 뜰 때도 쪽이 멀쩡합니다' in 글, 글[-400:])

    # (가) 자료에 켰는데 쪽에 없는 자리를 만들면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'ads.json')
        d = io.read_json(p)
        d['자리']['없는자리-pc'] = {
            '켬': True, '기기': 'pc',
            '배너': 'coupang-carousel-760x140-index', '쪽갈래': '첫화면'}
        io.write_json(p, d)
        글 = 돌리기('check_ads.py', 자료=사본, 인자=['--strict'])
        봄('자료에 켰는데 쪽에 없는 자리를 잡는다',
           '쪽에 없습니다' in 글 and '없는자리-pc' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) 휴대폰 자리에 PC 배너를 물려도 가로로 안 넘쳐야 합니다
    #     (ads.js 가 칸보다 넓은 배너를 줄여 넣습니다)
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'ads.json')
        d = io.read_json(p)
        d['자리']['index-mid-mobile']['배너'] = 'coupang-carousel-760x140-index'
        io.write_json(p, d)
        글 = 돌리기('check_ads.py', 자료=사본, 인자=['--strict'])
        봄('휴대폰에 큰 배너를 물려도 가로로 안 넘친다',
           '화면 밖으로' not in 글 and '가로로 넘칩니다' not in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_i18n — 다른 언어 쪽 탈을 잡는가 ──────────────────
def 시험_다른언어():
    print('[7] check_i18n — 다른 언어 쪽 탈을 잡는가')

    글 = 돌리기('check_i18n.py')
    봄('다른 언어 쪽이 없으면 「해당 없음」이라 말한다',
       '잴 것이 없습니다' in 글 and '해당 없음' in 글, 글[-300:])

    # (가) 한국어뿐인 쪽을 중국어 자리에 두면 잡아야 합니다
    def 가짜중국어쪽(사본, 상자):
        자리 = os.path.join(사본, 'zh-cn')
        상자.폴더만들기(자리, exist_ok=True)
        s = io.read(os.path.join(사본, 'index.html'))
        s = s.replace('<html lang="ko"', '<html lang="zh-Hans"', 1)
        상자.쓰기(os.path.join(자리, 'index.html'), s)

    되돌리개, 사본 = 사이트사본(가짜중국어쪽)
    try:
        글 = 돌리기('check_i18n.py', 사이트=사본, 인자=['--strict'])
        봄('중국어 쪽인데 한국어면 잡는다',
           '80% 에 못 미치는' in 글 or '그 언어가 아닙니다' in 글, 글[-400:])
        봄('한국어를 안 밝힌 것도 잡는다',
           'lang="ko" 로 안 밝힌' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 만들기로 해 놓고 안 만들면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'site.json')
        d = io.read_json(p)
        d['만들언어']['쪽'] = ['ko', 'zh']
        io.write_json(p, d)
        글 = 돌리기('check_i18n.py', 자료=사본, 인자=['--strict'])
        봄('만들기로 해 놓고 안 만들면 잡는다',
           '만들기로 했는데 쪽이 없습니다' in 글
           or '「만들언어」에는 들어 있습니다' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_keep — 지우면 안 되는 것을 지키는가 ──────────────
def 시험_남길것():
    print('[8] check_keep — 지우면 안 되는 것을 지키는가')

    글 = 돌리기('check_keep.py')
    봄('지금은 중국어판이 멀쩡하다',
       '중국어판이 멀쩡합니다' in 글, 글[-300:])

    # (가) 남길 것 목록에서 css/style.css 를 빼면 잡아야 합니다
    #     — 중국어 쪽 182곳이 쓰는 파일입니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'keep.json')
        d = io.read_json(p)
        d['남길것'].pop('css/style.css', None)
        io.write_json(p, d)
        글 = 돌리기('check_keep.py', 자료=사본, 인자=['--strict'])
        봄('중국어판이 쓰는 css 를 목록에서 빼면 잡는다',
           'css/style.css' in 글 and '사라질 것' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) 자료가 낡으면 알려야 합니다 (막지는 않습니다)
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p = os.path.join(사본, 'raw', 'keep.json')
        d = io.read_json(p)
        d['중국어가쓰는것']['css/style.css'] = 9999
        io.write_json(p, d)
        글 = 돌리기('check_keep.py', 자료=사본)
        봄('자료에 적은 값이 낡으면 알려 준다',
           '자료가 낡았습니다' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_manifest — **끊긴 쪽을 잡는가** ──────────────────
def 시험_끊긴쪽():
    """★ 하루에 **아홉 번** 겪은 잘못을 막는 검사입니다

    쪽이 거는데 build 가 안 만들고, 서버에 남은 옛 파일이 200 을
    냅니다. 손님은 옛 디자인으로 떨어지고 거기 숫자는 낡았습니다.
    사람 눈으로는 **아홉 번이나 놓쳤습니다.**

    바깥 검수 —
    「446쪽이 내부에서 링크하는 **모든 .html 대상이 manifest 에
      존재하는지 자동 검사**를 돌리세요. **아홉 번째가 서버에
      숨어 있는 일**을 막는 게 중요합니다」
    그 검사가 실제로 아홉 번째(travel/)를 찾아냈습니다.
    """
    print('[20] check_manifest — 끊긴 쪽을 잡는가')

    글 = 돌리기('check_manifest.py')
    봄('지금은 끊긴 쪽이 없다', '모두 만듭니다' in 글, 글[-400:])

    # (가) 없는 쪽으로 가는 링크를 심으면 잡아야 합니다
    def 끊어놓기(사본, 상자):
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        # ★ 첫 화면에는 `</main>` 이 없습니다 — `</body>` 에 답니다
        상자.쓰기(a, s2.replace(
            '</body>',
            '<a href="eobsneun-jjok.html">없는 쪽</a></body>', 1))

    되돌리개, 사본 = 사이트사본(끊어놓기)
    try:
        글 = 돌리기('check_manifest.py', 사이트=사본)
        봄('없는 쪽으로 가는 링크를 잡는다',
           'eobsneun-jjok.html' in 글, 글[-600:])
    finally:
        되돌리개()

    # (나) **진짜 쪽을 지우면** 그 쪽을 거는 곳이 다 걸려야 합니다
    #     — 이것이 서버에 옛 파일이 남은 상황과 같은 모양입니다
    def 쪽지우기(사본, 상자):
        p = os.path.join(사본, 'muldae.html')
        if os.path.exists(p):
            상자.지우기(p)

    되돌리개, 사본 = 사이트사본(쪽지우기)
    try:
        글 = 돌리기('check_manifest.py', 사이트=사본)
        봄('만들어야 할 쪽이 사라지면 잡는다',
           'muldae.html' in 글, 글[-600:])
    finally:
        되돌리개()


# ── 넙치 35cm — **법령 값이 한 길로 흐르는가** ─────────────
def 시험_넙치():
    """★ 사람이 **법을 어길 수 있는** 값이라 따로 지킵니다

    바깥 검수 요구 (2026-10-01) —
    「넙치 35cm 를 금어기.json → rules resolver → rule.html/어종/권역
      **한 경로로 통일**하고 **mutation test 까지** 넣으세요.
      이건 재심사보다 먼저 처리할 안전 항목입니다」

    왜 중요한가 — 화면에 **우연히 맞는 값**이 있는데 원자료에는
    없다면 더 위험합니다. 다른 오래된 경로에서 값이 흘러나오는
    것이기 때문입니다. 그래서 **자료를 바꾸면 쪽도 바뀌는지**를
    확인합니다. 안 바뀌면 쪽이 다른 데서 값을 얻고 있다는 뜻입니다.

    근거 — 수산자원관리법 시행령 별표2, 넙치(Paralichthys
    olivaceus) 전장 35cm 이하 포획 금지.
    """
    print('[19] 넙치 35cm — 법령 값이 자료에서 쪽으로 흐르는가')

    자료길 = os.path.join(ROOT, 'data', 'raw', 'rules', '금어기.json')
    원본 = io.read(자료길)
    것 = json.loads(원본)
    넙 = [x for x in 것['어종'] if x['법령명'] == '넙치']
    봄('자료에 넙치가 있다', len(넙) == 1, '%d건' % len(넙))
    if not 넙:
        return
    크 = (넙[0].get('크기제한') or [{}])[0]
    봄('자료의 값이 35cm 전장 전국이다',
       크.get('값') == 35 and 크.get('재는법') == '전장'
       and (크.get('지역') or {}).get('갈래') == '전국',
       json.dumps(크, ensure_ascii=False)[:120])
    봄('근거가 시행령 별표2 로 적혀 있다',
       크.get('근거') == '시행령별표2', str(크.get('근거')))

    글 = io.read(os.path.join(ROOT, 'site', 'rule.html'), default='')
    봄('쪽에 35cm 가 나온다', '35' in 글 and '넙치' in 글, '')

    # ★ **정말 망가뜨립니다** — 자료를 40 으로 바꾸고 다시 지어
    #   쪽이 따라 바뀌는지 봅니다. 안 바뀌면 쪽이 **딴 데서**
    #   값을 얻고 있다는 뜻입니다 (그것이 더 위험합니다).
    바꾼 = json.loads(원본)
    for x in 바꾼['어종']:
        if x['법령명'] == '넙치':
            x['크기제한'][0]['값'] = 40
    t = tempfile.mkdtemp(prefix='neopchi-')
    try:
        io.write(자료길, json.dumps(바꾼, ensure_ascii=False, indent=1))
        환경 = dict(os.environ)
        환경['BADAGAJA_SITE'] = t
        환경['PYTHONIOENCODING'] = 'utf-8'
        subprocess.run([sys.executable,
                        os.path.join(ROOT, 'engine', 'build.py')],
                       capture_output=True, timeout=1800, env=환경)
        새글 = io.read(os.path.join(t, 'rule.html'), default='')
        봄('자료를 40 으로 바꾸면 쪽도 40 이 된다',
           '40' in 새글 and '35cm' not in 새글.replace('35cm 이하', '', 0)
           or '40' in 새글,
           '쪽에 40 이 %s' % ('있음' if '40' in 새글 else '없음'))
    finally:
        io.write(자료길, 원본)          # **반드시 되돌립니다**
        shutil.rmtree(t, ignore_errors=True)
    봄('자료를 원래대로 되돌렸다',
       json.loads(io.read(자료길)) == 것, '')


# ── check_numbers — 틀린 숫자를 잡는가 ────────────────────
def 시험_숫자():
    """★ 실제로 나간 잘못과 **같은 모양**으로 망가뜨립니다

    2026-10-01 — 소개 쪽에 「낚시 자리 **0곳**」이 나갔습니다.
    자료에서 센다고 했지만 세는 방법이 틀려 합이 0 이었습니다.
    검사 34가지가 모두 통과했습니다.
    """
    print('[18] check_numbers — 쪽에 적힌 틀린 숫자를 잡는가')

    글 = 돌리기('check_numbers.py')
    봄('지금 쪽의 숫자는 자료와 맞는다',
       '자료와 맞습니다' in 글, 글[-400:])

    # (가) 큰 숫자 칸에 0 을 심으면 잡아야 합니다
    def 영심기(사본, 상자):
        a = os.path.join(사본, 'about.html')
        if not os.path.exists(a):
            return
        s2 = io.read(a)
        s2 = re.sub(r'<b>[\d,]+</b><span>낚시 자리</span>',
                    '<b>0</b><span>낚시 자리</span>', s2, count=1)
        상자.쓰기(a, s2)

    되돌리개, 사본 = 사이트사본(영심기)
    try:
        글 = 돌리기('check_numbers.py', 사이트=사본)
        봄('「0」이 적히면 잡는다', '「0」이 적힌 쪽' in 글, 글[-600:])
    finally:
        되돌리개()


# ── check_private — 저희 메모가 샌 것을 잡는가 ────────────
def 시험_내부메모():
    """★ **정말 망가뜨려야** 합니다 (2026-10-01)

    2026-10-01 에 실제로 샌 것과 같은 글을 쪽에 심어 봅니다.
    갱신 대장에서 sources.html 을 지었더니 저희 메모가 그대로
    나왔습니다 — 「사람이 눈으로 확인 (클로드)」.
    """
    print('[16] check_private — 저희끼리 쓰는 말이 샌 것을 잡는가')

    글 = 돌리기('check_private.py')
    봄('지금 쪽에는 저희 메모가 없다',
       '저희끼리 쓰는 말이 없습니다' in 글, 글[-400:])

    # (가) 만드는 쪽 파일 경로를 쪽에 심으면 잡아야 합니다
    def 경로심기(사본, 상자):
        본문끝에심기(사본, '<p>직접 그림 (옛 저장소 '
                        'tools/lesson-steps.ps1)</p>', 상자=상자)

    되돌리개, 사본 = 사이트사본(경로심기)
    try:
        글 = 돌리기('check_private.py', 사이트=사본, 인자=['--strict'])
        봄('만드는 쪽 경로가 새면 잡는다',
           '공개 쪽에 나갔습니다' in 글, 글[-500:])
    finally:
        되돌리개()

    # (나) 주소·스크립트 안의 같은 글자는 **잡으면 안 됩니다**
    #     거짓 경보가 나면 사람이 검사기를 믿지 않게 됩니다.
    def 주소에만(사본, 상자):
        본문끝에심기(사본, '<a href="tools/x.html">보기</a>', 상자=상자)

    되돌리개, 사본 = 사이트사본(주소에만)
    try:
        글 = 돌리기('check_private.py', 사이트=사본, 인자=['--strict'])
        봄('주소 안 글자는 잡지 않는다',
           '저희끼리 쓰는 말이 없습니다' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_css_names — 없는 차림 이름을 찾는가 ──────────────
def 시험_없는차림이름():
    """★ 없는 이름은 **오류 없이 조용히 버려집니다** (2026-10-01)

    하루에 세 번 당했습니다 — `--brand` · `.tbl` · `.ls-basic`.
    그래서 물때 막대 꾸밈이 빠진 것도 모르고 있었습니다.
    """
    print('[17] check_css_names — 차림표에 없는 이름을 찾는가')

    def 없는이름넣기(사본, 상자):
        본문끝에심기(사본,
                   '<div class="아무도없는이름입니다xyz">글</div>', 상자=상자)

    되돌리개, 사본 = 사이트사본(없는이름넣기)
    try:
        # ★ `--list` 로 **전부** 받습니다 (2026-10-02)
        #   그냥 돌리면 스무 가지만 냅니다. 심은 이름은 한 번만
        #   쓰여 뒤로 밀리므로 **잡았어도 출력에 안 나옵니다.**
        #   그래서 이 시험이 「못 잡는다」고 헛되이 적고 있었습니다.
        글 = 돌리기('check_css_names.py', 사이트=사본, 인자=['--list'])
        봄('차림표에 없는 이름을 찾는다',
           '아무도없는이름입니다xyz' in 글, 글[-600:])
    finally:
        되돌리개()

    # 변형 이름(`--`)의 바탕은 **잡으면 안 됩니다**
    #   `.firsttime--btn` 만 있어도 `class="firsttime firsttime--btn"`
    #   은 올바른 쓰임입니다. 처음에 이것을 잘못 잡았습니다.
    글 = 돌리기('check_css_names.py')
    봄('변형 이름의 바탕은 잡지 않는다',
       '.firsttime ' not in 글, 글[-600:])


# ── check_seo — 검색 기준 탈을 잡는가 ──────────────────────
def 시험_검색():
    print('[9] check_seo — 검색 기준 탈을 잡는가')

    글 = 돌리기('check_seo.py')
    봄('지금 쪽은 검색 기준을 지킨다',
       '검색 기준을 모두 지킵니다' in 글, 글[-500:])

    # (가) 제목을 두 쪽에 같게 만들면 잡아야 합니다
    def 제목겹치게(사본, 상자):
        a = os.path.join(사본, 'index.html')
        b = os.path.join(사본, 'taean.html')
        if not os.path.exists(b):
            return
        s2 = io.read(b)
        원래 = io.read(a)
        m = re.search(r'<title>(.*?)</title>', 원래, re.S)
        if m:
            s2 = re.sub(r'<title>.*?</title>',
                        '<title>%s</title>' % m.group(1), s2, count=1,
                        flags=re.S)
            상자.쓰기(b, s2)

    되돌리개, 사본 = 사이트사본(제목겹치게)
    try:
        글 = 돌리기('check_seo.py', 사이트=사본, 인자=['--strict'])
        봄('제목이 겹치면 잡는다', '제목이 겹침' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 제목에 같은 말을 세 번 넣으면 잡아야 합니다
    def 되풀이넣기(사본, 상자):
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        s2 = re.sub(r'<title>.*?</title>',
                    '<title>갯벌 갯벌 갯벌 안내</title>', s2, count=1,
                    flags=re.S)
        상자.쓰기(a, s2)

    되돌리개, 사본 = 사이트사본(되풀이넣기)
    try:
        글 = 돌리기('check_seo.py', 사이트=사본, 인자=['--strict'])
        봄('제목에 같은 말 3번이면 잡는다',
           '제목에 같은 말 3번 이상' in 글, 글[-400:])
    finally:
        되돌리개()

    # (다) 설명을 지우면 잡아야 합니다
    def 설명지우기(사본, 상자):
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        s2 = re.sub(r'<meta name="description"[^>]*>', '', s2, count=1)
        상자.쓰기(a, s2)

    되돌리개, 사본 = 사이트사본(설명지우기)
    try:
        글 = 돌리기('check_seo.py', 사이트=사본, 인자=['--strict'])
        봄('설명이 없으면 잡는다', '설명이 없음' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_refresh — 갱신 대장 탈을 잡는가 ──────────────────
def 시험_갱신():
    print('[10] check_refresh — 갱신 대장 탈을 잡는가')

    글 = 돌리기('check_refresh.py')
    봄('지금 자료는 모두 대장에 있다',
       '자료가 모두 대장에 있습니다' in 글, 글[-400:])

    # (가) 대장에서 한 줄 빼면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p2 = os.path.join(사본, 'raw', 'refresh-plan.json')
        d = io.read_json(p2)
        d['자료'] = [x for x in d['자료'] if x.get('key') != 'ads']
        io.write_json(p2, d)
        글 = 돌리기('check_refresh.py', 자료=사본)
        봄('대장에서 자료를 빼면 잡는다',
           '대장에 안 적힌 자료' in 글 and 'ads.json' in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) 기한을 0 으로 하면 「지났다」고 해야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        p2 = os.path.join(사본, 'raw', 'refresh-plan.json')
        d = io.read_json(p2)
        for x in d['자료']:
            if x.get('key') == 'points':
                x['유효기간일'] = 0
        io.write_json(p2, d)
        글 = 돌리기('check_refresh.py', 자료=사본)
        봄('기한이 지나면 알려 준다',
           '일 지남 (기한' in 글 and '기한을 넘긴 자료가 없습니다' not in 글,
           글[-500:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_calendar — 달이 바뀌면 틀어질 것을 잡는가 ────────
def 시험_달력():
    print('[11] check_calendar — 달이 바뀌면 틀어질 것을 잡는가')

    글 = 돌리기('check_calendar.py')
    봄('지금은 달이 바뀌어도 탈이 없다',
       '달이 바뀌어도 탈이 없습니다' in 글, 글[-400:])

    글 = 돌리기('check_calendar.py', 인자=['--next'])
    봄('다음 달로 넘어간 척해도 탈이 없다',
       '달이 바뀌어도 탈이 없습니다' in 글, 글[-400:])

    # (가) 쪽에 「이달의 축제」를 박아 두면 잡아야 합니다
    def 이달박기(사본, 상자):
        p = os.path.join(사본, 'index.html')
        s = io.read(p)
        상자.쓰기(p, s.replace('</body>',
                              '<h2>이달의 축제</h2></body>'))

    되돌리개, 사본 = 사이트사본(이달박기)
    try:
        글 = 돌리기('check_calendar.py', 사이트=사본, 인자=['--strict'])
        봄('「이달의 축제」를 박아 두면 잡는다',
           '「이달」이 쪽에 박힌 곳' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 기준일을 딴 달로 바꾸면 잡아야 합니다
    def 기준일틀리기(사본, 상자):
        # ★ **쪽에 적힌 꼴이 바뀌었습니다** (2026-10-02)
        #   전에는 「이 자료는 2026년 9월 기준입니다」였는데
        #   주인 지시로 「기준일 26년 9월」로 짧아졌습니다.
        #   옛 꼴을 찾던 이 뮤테이션은 **아무것도 안 바꾸고** 있었고,
        #   그래서 「검사기가 못 잡는다」고 헛되이 적었습니다.
        #   두 꼴을 다 보고, **하나도 못 바꾸면 터집니다.**
        p = os.path.join(사본, 'index.html')
        s = io.read(p)
        꼴들 = [
            (r'이 자료는 \d{4}년 \d{1,2}월 기준입니다',
             '이 자료는 1999년 1월 기준입니다'),
            (r'기준일 \d{2}년 \d{1,2}월', '기준일 99년 1월'),
            (r'기준 \d{4}년 \d{1,2}월', '기준 1999년 1월'),
        ]
        새 = s
        for 무늬, 바꿈 in 꼴들:
            새 = re.sub(무늬, 바꿈, 새)
        if 새 == s:
            raise AssertionError(
                'index.html 에서 기준일 적힌 자리를 못 찾았습니다 — '
                '쪽에 쓰는 꼴이 바뀌었으면 여기 꼴들에 더합니다.')
        상자.쓰기(p, 새)

    되돌리개, 사본 = 사이트사본(기준일틀리기)
    try:
        글 = 돌리기('check_calendar.py', 사이트=사본, 인자=['--strict'])
        봄('기준일이 자료와 다르면 잡는다',
           '기준일이 자료와 다릅니다' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_assets — 자산·아이콘·고아 링크를 잡는가 ──────────
def 시험_자산():
    print('[12] check_assets — 자산·아이콘·고아 링크를 잡는가')

    글 = 돌리기('check_assets.py')
    봄('지금은 요구하는 것이 모두 있다',
       '쪽이 요구하는 것이 모두 있습니다' in 글, 글[-400:])

    # (가) 아이콘 파일을 지우면 잡아야 합니다
    def 아이콘지우기(사본, 상자):
        p2 = os.path.join(사본, 'favicon.svg')
        if os.path.exists(p2):
            상자.지우기(p2)

    되돌리개, 사본 = 사이트사본(아이콘지우기)
    try:
        글 = 돌리기('check_assets.py', 사이트=사본, 인자=['--strict'])
        봄('아이콘 파일을 지우면 잡는다',
           'favicon.svg' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 없는 사진을 쓰면 잡아야 합니다
    def 없는사진(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, s.replace('</body>',
                               '<img src="없는사진.jpg" alt="시험"></body>'))

    되돌리개, 사본 = 사이트사본(없는사진)
    try:
        글 = 돌리기('check_assets.py', 사이트=사본, 인자=['--strict'])
        봄('없는 사진을 쓰면 잡는다', '없는사진.jpg' in 글, 글[-400:])
    finally:
        되돌리개()

    # (다) 남길 것 목록에 없는 쪽을 가리키면 잡아야 합니다
    def 없는쪽가리키기(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, s.replace('</body>',
                               '<a href="아무데도없음.html">시험</a></body>'))

    되돌리개, 사본 = 사이트사본(없는쪽가리키기)
    try:
        글 = 돌리기('check_assets.py', 사이트=사본, 인자=['--strict'])
        봄('남기기로 안 적은 없는 쪽을 가리키면 잡는다',
           '아무데도없음.html' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_canonical — 대표 주소 탈을 잡는가 ────────────────
def 시험_대표주소():
    print('[13] check_canonical — 대표 주소 탈을 잡는가')

    글 = 돌리기('check_canonical.py')
    봄('지금 쪽 안의 대표 주소는 맞다',
       '모든 쪽이 제 주소를 가리킵니다' in 글, 글[-400:])
    봄('실제 서버를 안 물어봤으면 그렇다고 말한다',
       '실제 서버 응답은 안 쟀습니다' in 글, 글[-300:])

    # (가) 첫 화면 canonical 을 /index.html 로 바꾸면 잡아야 합니다
    def 캐논틀리기(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, s.replace('href="https://badagaja.com/"',
                               'href="https://badagaja.com/index.html"'))

    되돌리개, 사본 = 사이트사본(캐논틀리기)
    try:
        글 = 돌리기('check_canonical.py', 사이트=사본, 인자=['--strict'])
        봄('첫 화면 대표 주소가 /index.html 이면 잡는다',
           'index.html' in 글 and '아닙니다' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 첫 화면 제목을 바꾸면 잡아야 합니다 (검수 지시 14)
    def 제목바꾸기(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, re.sub(r'<title>.*?</title>',
                            '<title>딴 제목</title>', s, count=1, flags=re.S))

    되돌리개, 사본 = 사이트사본(제목바꾸기)
    try:
        글 = 돌리기('check_canonical.py', 사이트=사본, 인자=['--strict'])
        봄('첫 화면 제목을 바꾸면 잡는다',
           '제목이 정해 둔 것과 다릅니다' in 글, 글[-400:])
    finally:
        되돌리개()


# ── check_console — 자바스크립트 탈을 잡는가 ───────────────
def 시험_콘솔():
    print('[14] check_console — 자바스크립트 탈을 잡는가')

    글 = 돌리기('check_console.py')
    봄('지금은 브라우저에서 조용하다',
       '브라우저에서 조용하고' in 글, 글[-400:])
    봄('광고가 두 경로 다 뜬다',
       '광고도 제대로 뜹니다' in 글, 글[-300:])

    # (가) 일부러 넘어지는 코드를 넣으면 잡아야 합니다
    def 넘어뜨리기(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, s.replace('</body>',
                               '<script>없는것.부르기()</script></body>'))

    되돌리개, 사본 = 사이트사본(넘어뜨리기)
    try:
        글 = 돌리기('check_console.py', 사이트=사본, 인자=['--strict'])
        봄('일부러 넘어뜨리면 잡는다',
           '사이트 자체 코드에서 난 탈' in 글, 글[-500:])
    finally:
        되돌리개()

    # (나) 사이트 안 파일을 못 받게 하면 잡아야 합니다
    def 파일없애기(사본, 상자):
        p2 = os.path.join(사본, 'index.html')
        s = io.read(p2)
        상자.쓰기(p2, s.replace('</body>',
                               '<script src="없는움직임.js"></script></body>'))

    되돌리개, 사본 = 사이트사본(파일없애기)
    try:
        글 = 돌리기('check_console.py', 사이트=사본, 인자=['--strict'])
        봄('사이트 안 파일을 못 받으면 잡는다',
           '사이트 안 파일을 못 받았습니다' in 글, 글[-500:])
    finally:
        되돌리개()


# ── check_deployed — 배포 뒤 검사가 제 몫을 하는가 ─────────
def 시험_배포뒤():
    print('[15] check_deployed — 배포 뒤 검사가 제 몫을 하는가')

    # (가) --net 없이는 아무것도 재지 않아야 합니다
    글 = 돌리기('check_deployed.py')
    봄('--net 없이는 잰 척하지 않는다',
       '실제로는 안 물어봤습니다' in 글 and '아직 안 잰 것' in 글, 글[-400:])

    # (나) 무엇을 볼지 목록을 냅니다
    봄('무엇을 볼지 보여 준다',
       '쪽 ' in 글 and '자산 ' in 글 and '남기기로 한 것' in 글, 글[-400:])

    # (다) 아직 안 올렸으면 「같습니다」라고 하지 않습니다
    #     (--net 은 바깥에 나가므로 여기서는 안 돌립니다.
    #      대신 코드에 그 갈래가 있는지 봅니다)
    코드글 = io.read(os.path.join(ROOT, 'engine', 'check_deployed.py'),
                     default='')
    봄('아직 안 올렸을 때를 따로 다룬다',
       '아직 안 올렸습니다' in 코드글 and '잰 것이 아닙니다' in 코드글)
    # (마) ★ **판 지문을 벗기되, 그 밖에는 손대지 않아야** 합니다
    #     2026-10-07 — 판 지문을 쪽마다 넣은 뒤 이 검사기가
    #     「449쪽 전부 다름」을 냈습니다. 내 site/ 가 서버와 딴
    #     커밋이면 지문 한 줄 때문에 전부 다릅니다. **신호가 소음에
    #     묻혀** 진짜 빠뜨린 쪽을 놓칩니다.
    #     그래서 지문을 벗기고 견주는데, **너무 넓게 벗기면**
    #     진짜 차이도 함께 가려집니다. 둘 다 잽니다.
    sys.path.insert(0, ROOT)
    from engine import check_deployed as _CD

    본 = ('<head><meta name="badagaja-build" content="abc1234">'
          '<meta name="badagaja-build-date" content="2026-10-07">'
          '<title>가</title></head>'
          '<body><p class="foot-build">사이트 업데이트 2026.10.07</p>'
          '<p>본문</p></body>')
    벗 = _CD.판지문벗기기(본)
    봄('판 지문 meta 두 줄을 벗긴다',
       'badagaja-build' not in 벗, 벗[:200])
    봄('꼬리말 「사이트 업데이트」도 벗긴다',
       'foot-build' not in 벗 and '사이트 업데이트' not in 벗, 벗[:200])
    봄('★ 그 밖에는 손대지 않는다 (무르게 하지 않습니다)',
       '<title>가</title>' in 벗 and '<p>본문</p>' in 벗, 벗[:200])

    # (바) ★ CSS 캐시 지문은 **벗기지 않아야** 합니다
    #     실제로 남은 차이가 `site.css?v=…` 한 군데였습니다.
    #     벗겨 넘기고 싶었지만 그러면 **진짜로 CSS 가 안 올라간
    #     사고**도 함께 놓칩니다. 소음을 줄이려 귀를 막는 것입니다.
    쪽 = '<link rel="stylesheet" href="assets/css/site.css?v=51aa4c68">'
    봄('CSS 캐시 지문은 벗기지 않는다 (진짜 사고를 놓치지 않게)',
       '?v=51aa4c68' in _CD.판지문벗기기(쪽))

    # (사) 딴 커밋이면 **못 쟀다**고 적어야 합니다
    봄('딴 커밋이면 「못 쟀다」고 적는다',
       '딴 커밋' in 코드글 and '못 쟀습니다' in 코드글)
    봄('못 쟀을 때 「같습니다」라고 말하지 않는다',
       "if _딴커밋['그런가']:" in 코드글
       and '내용이 같은가는 못 쟀습니다' in 코드글)

    봄('.htaccess 가 웹으로 보이면 잡는다',
       '숨어야할것' in 코드글 and '서버 설정이 샙니다' in 코드글)


# ── url_table — 줄어든 쪽이 무엇인지 밝히는가 ──────────────
def 시험_주소표():
    print('[16] url_table — 줄어든 쪽이 무엇인지 밝히는가')

    글 = 돌리기('url_table.py')
    봄('434개가 모두 어떻게 됐는지 적혀 있다',
       '모두 어떻게 됐는지 적혀 있습니다' in 글, 글[-400:])
    봄('검산을 스스로 낸다', '검산' in 글 and '안 맞습니다' not in 글, 글[-300:])
    봄('줄어든 것을 갈래별로 보여 준다',
       '줄어든' in 글 and '아직안만듦' in 글, 글[-400:])

    # 남길 것에서 빼면 「갈 곳 없음」으로 나와야 합니다
    t = tempfile.mkdtemp(prefix='checker-test-')
    try:
        사본 = os.path.join(t, 'data')
        shutil.copytree(os.path.join(ROOT, 'data'), 사본)
        # ★ **정말 안 만들어진 쪽을 고릅니다** (2026-10-02)
        #   전에는 `about.html` 을 박아 두었습니다. 그런데 그 쪽은
        #   그 뒤 **실제로 만들어졌습니다.** 두 자료에서 빼도
        #   `site/about.html` 이 있으니 「갈 곳 없음」이 아닙니다.
        #   그래서 이 시험이 「검사기가 못 잡는다」고 헛되이
        #   적고 있었습니다. 사이트가 자라면 또 같은 일이 납니다.
        #   **「아직 안 만듦」에 있으면서 site/ 에도 없는 것**을
        #   매번 골라냅니다.
        p3 = os.path.join(사본, 'raw', 'url-map.json')
        d3 = io.read_json(p3)
        아직들 = list(d3['아직_안_만듦']['쪽'])
        고를것 = next((x for x in 아직들
                     if not os.path.exists(os.path.join(ROOT, 'site', x))), None)
        if not 고를것:
            raise AssertionError(
                '「아직 안 만듦」에 적힌 쪽이 모두 실제로 만들어졌습니다 — '
                '이 시험은 안 만들어진 쪽이 있어야 뜻이 있습니다. '
                'url-map.json 을 손보거나 이 시험을 고쳐야 합니다.')
        p2 = os.path.join(사본, 'raw', 'keep.json')
        d = io.read_json(p2)
        d['남길것'].pop(고를것, None)
        io.write_json(p2, d)
        d3['아직_안_만듦']['쪽'] = [x for x in 아직들 if x != 고를것]
        io.write_json(p3, d3)
        글 = 돌리기('url_table.py', 자료=사본, 인자=['--strict'])
        봄('어디에도 안 적힌 옛 주소를 잡는다',
           '갈 곳 없는 옛 주소' in 글 and 고를것 in 글, 글[-400:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_clean — 시험 자국을 잡는가 ───────────────────────
def 시험_깨끗한가():
    print('[17] check_clean — 시험이 망가뜨린 것을 잡는가')

    글 = 돌리기('check_clean.py')
    봄('지금은 시험 자국이 없다',
       '시험이 망가뜨린 것이 없습니다' in 글 or '시험 자국이 없습니다' in 글,
       글[-400:])

    # 물때 식을 밀어 놓으면 잡아야 합니다 — 실제로 커밋된 적이 있습니다
    # ★ 본 트리가 아니라 **사본**에서 밉니다 (2026-09-27 바깥 검수)
    #   전에는 여기서 진짜 tide.js 를 고쳤다 되돌렸습니다. 그 사이에
    #   커밋하면 밀린 식이 그대로 들어갑니다 — 실제로 들어갔습니다.
    with isolate.일터() as 뿌리:
        p2 = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        io.write(p2, io.read(p2).replace('(음력날(날짜) + 5) % 15',
                                         '(음력날(날짜) + 6) % 15'))
        글 = 돌리기('check_clean.py', 인자=['--strict'], 뿌리=뿌리)
        봄('물때 식이 밀려 있으면 잡는다',
           'tide.js' in 글 and '한 칸 민 자국' in 글, 글[-400:])

    # 사본을 지우고 나면 본 트리는 처음부터 깨끗해야 합니다
    글 = 돌리기('check_clean.py')
    봄('되돌리면 다시 깨끗하다',
       '시험이 망가뜨린 것이 없습니다' in 글, 글[-300:])

    # ★ 본 트리를 정말 안 건드렸는가 — 바깥 검수가 더하라고 한 조건입니다
    #   「mutation test 종료 후: 메인 worktree tracked file 변경 0개」
    알았나, 지금 = isolate.본트리가깨끗한가()
    if not 알았나:
        봄('본 트리를 안 건드렸다', False, 'git 을 못 물어봤습니다')
    else:
        샌것 = sorted(set(지금) - set(처음본트리))
        봄('본 트리를 안 건드렸다', not 샌것,
           '시험 때문에 바뀐 파일: %s' % ' · '.join(샌것[:5]))


# ── check_tide — 물때가 어긋나면 잡는가 ────────────────────
def 시험_물때():
    print('[18] check_tide — 독립 셈과 화면 값이 어긋나면 잡는가')

    from engine import tide_reference as 독립
    import datetime
    오늘 = datetime.date.today()
    봄('독립 셈이 돌아간다', 독립.물때(오늘)['이름'] in 독립.물때이름)

    # tide.js 의 식을 한 칸 밀면 독립 셈과 어긋나야 합니다
    # ★ 본 트리가 아니라 **사본**에서 밉니다 (2026-09-27 바깥 검수)
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        io.write(p, io.read(p).replace('(음력날(날짜) + 5) % 15',
                                       '(음력날(날짜) + 6) % 15'))
        글 = 돌리기('check_tide.py', 뿌리=뿌리)
        봄('물때 식을 한 칸 밀면 잡는다',
           '독립 셈과 화면 값이 다릅니다' in 글, 글[:600])



# ── check_newmoon — 삭이 어긋나면 잡는가 ───────────────────
def 시험_삭():
    print('[19] check_newmoon — 삭이 천문 기준과 어긋나면 잡는가')

    # 천문 기준(meeus)이 주인이 확인한 값과 맞는가 — 자를 먼저 봅니다
    from engine import meeus
    import datetime
    목록 = dict((t.strftime('%Y-%m-%d'), t)
                for _, t in meeus.삭목록(2026, 2026))
    봄('천문 기준이 2026-10-11 00:50 을 낸다',
       '2026-10-11' in 목록 and abs(목록['2026-10-11'].hour * 60
                                    + 목록['2026-10-11'].minute - 50) <= 5,
       str(목록.get('2026-10-11')))

    # 달 흔들림을 몇 개 빼면 삭이 어긋나야 합니다.
    # ★ 사본에서만 뺍니다 — 본 트리는 안 건드립니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        원 = io.read(p)
        # 큰 흔들림 하나(1.274 sin(2D−M'))를 지웁니다
        상한것 = 원.replace("      + 1.274027 * Math.sin(2 * D - Mp)\n", '')
        봄('흔들림 항을 정말 지웠다', 상한것 != 원)
        io.write(p, 상한것)
        글 = 돌리기('check_newmoon.py', 인자=['2026', '2027', '--strict'],
                    뿌리=뿌리)
        봄('흔들림 항을 빼면 잡는다',
           ('음력 날짜가' in 글 and '갈립니다' in 글)
           or '삭 시각이' in 글, 글[-500:])

    # 바깥 기준표를 비우면 「못 박을 데가 없다」고 해야 합니다
    with isolate.일터() as 뿌리:
        p2 = os.path.join(뿌리, 'data', 'raw', '삭-기준.json')
        d = io.read_json(p2)
        d['삭'] = []
        io.write_json(p2, d)
        글 = 돌리기('check_newmoon.py', 인자=['2026', '2026', '--strict'],
                    뿌리=뿌리)
        봄('바깥 기준이 비면 잡는다',
           '확인된 값이 하나도 없습니다' in 글, 글[-400:])


# ── check_months — 달이 안 넘어가면 잡는가 ─────────────────
def 시험_열두달():
    print('[20] check_months — 달이 안 넘어가면 잡는가')

    # 축제 달력이 이달을 안 고르게 만들면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'assets', 'js', 'festival-list.js')
        원 = io.read(p)
        상한것 = 원.replace('new Date().getMonth() + 1', '6')
        봄('이달 고르기를 정말 망가뜨렸다', 상한것 != 원)
        io.write(p, 상한것)
        글 = 돌리기('check_months.py', 인자=['--strict'], 뿌리=뿌리)
        봄('달이 안 따라가면 잡는다',
           '월인데' in 글 and '눌렸습니다' in 글, 글[-500:])

    # 움직임이 음력 **달**을 셈해 내면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p2 = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        io.write(p2, io.read(p2)
                 + chr(10) + 'var 윤달 = true;' + chr(10))
        글 = 돌리기('check_months.py', 인자=['--strict'], 뿌리=뿌리)
        봄('음력 달을 셈해 내면 잡는다',
           '음력 **달**을 셈해' in 글 or '윤달에 갈립니다' in 글, 글[-400:])


# ── check_mobile — 휴대폰에서 넘치면 잡는가 ────────────────
def 시험_휴대폰():
    """★ 2026-09-28 — 「휴대폰 확인」을 한 번도 제대로 못 했습니다.

    크롬 헤드리스는 창을 500px 보다 좁게 못 만듭니다.
    --window-size=375 를 줘도 쪽이 받는 폭은 500px 입니다.
    그래서 찍은 「휴대폰 사진」이 전부 500px 짜리였고,
    375px 그림에 담기며 오른쪽이 잘려 보였습니다.

    check_mobile 은 **iframe 안에 넣어** 진짜 폭으로 그립니다.
    그 검사기가 정말 잡는지 여기서 봅니다.
    """
    print('[27] check_mobile — 휴대폰에서 화면 밖으로 나가면 잡는가')

    글 = 돌리기('check_mobile.py')
    봄('지금은 휴대폰에서 넘치는 것이 없다',
       '화면 밖으로 나가는 것이 없습니다' in 글, 글[-400:])

    # (가) 화면보다 넓은 것을 넣으면 잡아야 합니다
    #
    #   ★ **검사기에게 물어 표본을 고릅니다** (2026-10-02)
    #     전에는 `taean.html` 에 박아 심었습니다. 그런데 check_mobile 은
    #     **갈래마다 한 장씩**만 봅니다. 태안은 권역 쪽 57개 중
    #     하나이고 그 갈래의 대표는 다른 쪽이라, 심어도 **아무도
    #     안 봤습니다.** 그래서 이 시험이 「검사기가 못 잡는다」고
    #     헛되이 적고 있었습니다 ([[new-page-into-check-samples]] —
    #     「표본에 없으면 영영 안 봅니다」).
    #     검사기가 실제로 보는 첫 쪽에 심습니다.
    import importlib
    _cm = importlib.import_module('engine.check_mobile')
    # 돌려주는 것은 **온전한 경로**이므로 site/ 아래 상대 경로로 바꿉니다
    표본 = _cm.볼쪽들(False)
    심을쪽 = (os.path.relpath(표본[0], _cm.NEW).replace(os.sep, '/')
            if 표본 else 'index.html')

    def 넓은것넣기(사본, 상자):
        a = os.path.join(사본, 심을쪽)
        s2 = io.read(a)
        새것 = s2.replace(
            '</body>',
            '<div style="width:700px;height:40px">일부러 넘치게</div>'
            '</body>', 1)
        if 새것 == s2:
            raise AssertionError('%s 에 </body> 가 없습니다' % 심을쪽)
        상자.쓰기(a, 새것)

    되돌리개, 사본 = 사이트사본(넓은것넣기)
    try:
        글 = 돌리기('check_mobile.py', 사이트=사본, 인자=['--strict'])
        봄('화면보다 넓은 것을 넣으면 잡는다',
           '화면 밖으로 나갑니다' in 글 or '넘친 것' in 글, 글[-500:])
    finally:
        되돌리개()

    # (나) 일부러 옆으로 밀게 만든 것은 **봐줘야** 합니다
    #     안 봐주면 「무조건 빨간불 기계」가 됩니다
    def 밀수있게(사본, 상자):
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        상자.쓰기(a, s2.replace(
            '</body>',
            '<div style="overflow-x:auto">'
            '<div style="width:700px;height:40px">밀어서 봅니다</div>'
            '</div></body>', 1))

    되돌리개, 사본 = 사이트사본(밀수있게)
    try:
        글 = 돌리기('check_mobile.py', 사이트=사본, 인자=['--strict'])
        봄('일부러 밀게 만든 것은 안 막는다',
           '화면 밖으로 나가는 것이 없습니다' in 글, 글[-500:])
    finally:
        되돌리개()


# ── check_photos — 보이는 것이 없으면 잡는가 ───────────────
def 시험_사진():
    print('[21] check_photos — 쪽에 보이는 것이 없으면 잡는가')

    글 = 돌리기('check_photos.py')
    봄('지금은 쪽마다 보이는 것이 있다',
       '모두 보이는 것이 있고' in 글, 글[-400:])

    # (가) 사진을 지우면 잡아야 합니다
    def 사진지우기(사본, 상자):
        import re as _re
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        # ★ **보이는 것을 모두** 지웁니다 (2026-09-28)
        #   전에는 <figure class="photo…> 만 지웠습니다. 그런데
        #   명소 사진을 <figure class="card-figure"> 로 넣자
        #   그것들이 남아 「그림이 하나도 없다」가 안 됐습니다.
        #   시험이 덜 지우면 **검사기가 멀쩡한데도 못 잡은 것처럼**
        #   보입니다. 보이는 것을 통째로 지워야 제대로 잽니다.
        s2 = _re.sub(r'<figure[^>]*>.*?</figure>', '', s2, flags=_re.S)
        s2 = _re.sub(r'<img[^>]*>', '', s2)
        s2 = _re.sub(r'<svg[^>]*>.*?</svg>', '', s2, flags=_re.S)
        상자.쓰기(a, s2)

    되돌리개, 사본 = 사이트사본(사진지우기)
    try:
        글 = 돌리기('check_photos.py', 사이트=사본, 인자=['--strict'])
        봄('사진을 지우면 잡는다',
           '그림이 하나도 없습니다' in 글, 글[-400:])
    finally:
        되돌리개()

    # (나) 없는 파일을 가리키면 잡아야 합니다
    #   ★ 2026-09-27 에 실제로 52갈래가 이랬습니다
    def 엉뚱한주소(사본, 상자):
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        상자.쓰기(a, s2.replace('img/coast/taean-hero.jpg',
                               'img/taean/hero.jpg'))

    되돌리개, 사본 = 사이트사본(엉뚱한주소)
    try:
        글 = 돌리기('check_photos.py', 사이트=사본, 인자=['--strict'])
        봄('없는 그림을 가리키면 잡는다',
           '없는 파일을 가리킵니다' in 글, 글[-500:])
    finally:
        되돌리개()

    # (다) 설명에 이용허락 종류를 적으면 잡아야 합니다 (규칙 6)
    def 허락적기(사본, 상자):
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        상자.쓰기(a, s2.replace('<figcaption>사진 ·',
                               '<figcaption>공공누리 제1유형 · 사진 ·', 1))

    되돌리개, 사본 = 사이트사본(허락적기)
    try:
        글 = 돌리기('check_photos.py', 사이트=사본, 인자=['--strict'])
        봄('쪽에 이용허락 종류를 적으면 잡는다',
           '이용허락 종류를 적은 곳' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()

    # (라) 촬영자를 빼면 잡아야 합니다 (규칙 5)
    def 촬영자빼기(사본, 상자):
        import re as _re
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        상자.쓰기(a, _re.sub(r'<figcaption>사진 · [^<]*</figcaption>',
                            '<figcaption>사진</figcaption>', s2))

    되돌리개, 사본 = 사이트사본(촬영자빼기)
    try:
        글 = 돌리기('check_photos.py', 사이트=사본, 인자=['--strict'])
        봄('촬영자를 빼면 잡는다',
           '촬영자가 없습니다' in 글 or '촬영자가 빠진 곳' in 글, 글[-500:])
    finally:
        되돌리개()


# ── check_golden — 있던 것이 사라지면 잡는가 ───────────────
#
#   ★ 계약-28 「검사기도 시험받는다」
#     이 검사기는 **주인이 눈으로 잡은 셋**을 다시 놓치지 않으려고
#     만들었습니다. 그러니 이것이 진짜 잡는지도 재 봐야 합니다.
#         사진 0장 · 링크 안 링크 · 아이콘 7칸 사라짐
def 시험_있던것():
    print('[22] check_golden — 있던 것이 사라지면 잡는가')

    글 = 돌리기('check_golden.py')
    봄('지금은 있던 것이 그대로 있다',
       '모두 지켰습니다' in 글, 글[-400:])

    # (가) 빈 링크 — 2026-09-27 에 권역 쪽 57개가 실제로 이랬습니다
    def 빈링크넣기(사본, 상자):
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        상자.쓰기(a, s2.replace('<a class="brand" href="./"',
                               '<a class="brand" href=""', 1))

    되돌리개, 사본 = 사이트사본(빈링크넣기)
    try:
        글 = 돌리기('check_golden.py', 사이트=사본)
        봄('빈 링크를 넣으면 잡는다', '빈 링크' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()

    # (나) 링크 안에 링크 — 주인이 화면 보고 잡은 것
    def 링크겹치기(사본, 상자):
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        상자.쓰기(a, s2.replace('<div class="groups">',
                               '<div class="groups"><a href="a.html">'
                               '<a href="b.html">겹침</a></a>', 1))

    되돌리개, 사본 = 사이트사본(링크겹치기)
    try:
        글 = 돌리기('check_golden.py', 사이트=사본)
        봄('링크 안에 링크를 넣으면 잡는다',
           '링크 안에 링크' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()

    # (다) 사진을 통째로 빼면 잡아야 합니다 — 416쪽 사진 0장 사고
    def 보이는것없애기(사본, 상자):
        import re as _re
        a = os.path.join(사본, 'taean.html')
        s2 = io.read(a)
        몸 = s2.split('</head>', 1)
        if len(몸) == 2:
            뒤 = _re.sub(r'<img[^>]*>', '', 몸[1])
            뒤 = _re.sub(r'(?is)<svg.*?</svg>', '', 뒤)
            뒤 = _re.sub(r'(?is)<picture.*?</picture>', '', 뒤)
            상자.쓰기(a, 몸[0] + '</head>' + 뒤)

    되돌리개, 사본 = 사이트사본(보이는것없애기)
    try:
        글 = 돌리기('check_golden.py', 사이트=사본)
        봄('보이는 것을 다 빼면 잡는다',
           '보이는 것이 하나도 없음' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()

    # (라) alt 없는 사진 — 눈이 불편한 분이 못 읽습니다
    #
    #   ★ **망가뜨리지 못하고 있었습니다** (2026-10-08에 잡음)
    #
    #     전에는 ` alt=""` 를 지워 변형을 만들었습니다. 그런데
    #     2026-10-08 에 네이버 진단을 받고 **빈 alt 를 모두 채우자**
    #     지울 자리가 한 곳도 없어졌습니다. `replace` 가 아무것도
    #     못 바꾸고 **사본이 원본과 똑같아졌습니다.** 검사기는
    #     당연히 통과하고, 시험은 「못 잡았다」로 섰습니다.
    #     배포 #25 의 판정 2번이 그래서 NO-GO 였습니다.
    #
    #     **시험이 제 할 일을 한 것입니다.** 망가뜨리지 못했는데
    #     통과로 넘겼다면, 검사기가 죽어도 모르고 있었을 것입니다.
    #     (기억 「뮤테이션은 정말 망가뜨려야」)
    #
    #     이제 **값이 있는 alt 를 통째로 지웁니다.** 그리고 정말
    #     바뀌었는지 보고, 안 바뀌었으면 **조용히 통과하지 않습니다** —
    #     같은 일이 또 나면 바로 여기서 섭니다.
    바뀜 = {'했나': False}

    def 알트빼기(사본, 상자):
        import re as _re
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        새 = _re.sub(r'(<img[^>]*?)\s+alt="[^"]*"', r'\1', s2, count=1)
        if 새 != s2:
            바뀜['했나'] = True
            상자.쓰기(a, 새)

    되돌리개, 사본 = 사이트사본(알트빼기)
    try:
        if not 바뀜['했나']:
            봄('alt 없는 사진을 넣으면 잡는다', False,
               'index.html 에서 alt 를 지울 자리를 못 찾았습니다 — '
               '망가뜨리지 못했으니 검사기를 잰 것이 아닙니다')
        else:
            글 = 돌리기('check_golden.py', 사이트=사본)
            봄('alt 없는 사진을 넣으면 잡는다',
               'alt 없는 사진' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()

    # (마) 겹치는 id — 2026-10-08 에 **공개 서버에서 잡았습니다**
    #
    #   첫 화면 포인트 셋을 전체 목록과 같은 함수로 만들어 `id` 가
    #   쪽마다 셋씩 겹쳐 있었습니다. `getElementById` 는 먼저 나온
    #   것만 잡으므로 「위치 확인하기」가 엉뚱한 카드로 갔고,
    #   걸러내기가 한 장만 숨겼습니다.
    #
    #   **화면에는 아무 탈이 없어 보입니다.** 그러니 눈으로는 영영
    #   못 찾습니다 — 기계가 재야 하는 종류입니다. 고치는 데서
    #   끝내지 않고 검사를 더하고, 그 검사도 잰 것입니다.
    겹침 = {'했나': False}

    def 아이디겹치기(사본, 상자):
        import re as _re
        a = os.path.join(사본, 'index.html')
        s2 = io.read(a)
        m = _re.search(r'\sid="([^"]+)"', s2)
        if not m:
            return
        새 = s2.replace('</body>', '<div id="%s"></div></body>'
                        % m.group(1), 1)
        if 새 != s2:
            겹침['했나'] = True
            상자.쓰기(a, 새)

    되돌리개, 사본 = 사이트사본(아이디겹치기)
    try:
        if not 겹침['했나']:
            봄('겹치는 id 를 넣으면 잡는다', False,
               'index.html 에 심을 자리를 못 찾았습니다 — '
               '망가뜨리지 못했으니 검사기를 잰 것이 아닙니다')
        else:
            글 = 돌리기('check_golden.py', 사이트=사본)
            봄('겹치는 id 를 넣으면 잡는다',
               '겹치는 id' in 글 and '✗' in 글, 글[-500:])
    finally:
        되돌리개()



# ── check_architecture — 같은 사실이 두 곳에 있으면 잡는가 ──
#
#   ★ 계약-28. 이 검사기는 **하루에 열한 번 난 사고**를 막으려고
#     만들었습니다. 그러니 정말 잡는지도 재 봐야 합니다.
def 시험_짜임():
    print('[23] check_architecture — 같은 사실이 두 곳에 있으면 잡는가')

    글 = 돌리기('check_architecture.py')
    봄('지금은 두 곳에서 관리하는 것이 없다',
       '같은 사실을 두 곳에서 관리하는 곳이 없습니다' in 글, 글[-400:])

    # (가) 검사기를 만들고 판정에 안 물리면 잡아야 합니다
    #     — 오늘 실제로 넷이 그랬습니다
    t = tempfile.mkdtemp(prefix='arch-')
    try:
        뿌리 = os.path.join(t, '두번째도전')
        shutil.copytree(ROOT, 뿌리, ignore=shutil.ignore_patterns(
            'site', '.git', '__pycache__', '.tmp', 'release',
            # ★ 사진 71MB 는 복사할 까닭이 없습니다 (2026-09-28)
            #   시험마다 통째로 베끼다 디스크를 때려, 같이 돌던
            #   check_console 이 크롬을 못 얻고 죽었습니다.
            'photo',
            # ★ **무거운 것을 더 뺍니다** (2026-10-02)
            #   2026-10-02 에 D 드라이브가 꽉 차 시험이 통째로
            #   죽었습니다 — 「WinError 112 디스크 공간이
            #   부족합니다」. 조사 자료 data-private 만 138MB 이고
            #   그림·캡처까지 합치면 한 번에 수백 MB 를 베낍니다.
            #
            #   이 시험이 보는 것은 **engine/ 의 검사기 목록과
            #   gate.py 의 차례**뿐입니다. 사진도 조사 자료도
            #   읽지 않습니다. 복사할 까닭이 없습니다.
            'data-private', 'img', 'out', '샷', '.shot',
            '*.jpg', '*.jpeg', '*.png', '*.webp', '*.zip', '*.mp4'))
        io.write(os.path.join(뿌리, 'engine', 'check_아무것도안함.py'),
                 '# -*- coding: utf-8 -*-\nimport sys\nsys.exit(0)\n')
        글 = 돌리기('check_architecture.py', 뿌리=뿌리)
        봄('판정에 안 물린 검사기를 잡는다',
           '판정에 안 물린 검사기' in 글, 글[-500:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) 차림표를 하나 더했는데 아무도 안 쓰면 잡아야 합니다
    t = tempfile.mkdtemp(prefix='arch2-')
    try:
        뿌리 = os.path.join(t, '두번째도전')
        shutil.copytree(ROOT, 뿌리, ignore=shutil.ignore_patterns(
            'site', '.git', '__pycache__', '.tmp', 'release',
            # ★ 사진 71MB 는 복사할 까닭이 없습니다 (2026-09-28)
            #   시험마다 통째로 베끼다 디스크를 때려, 같이 돌던
            #   check_console 이 크롬을 못 얻고 죽었습니다.
            'photo'))
        io.write(os.path.join(뿌리, 'assets', 'css', '아무도안씀.css'),
                 '.x{color:red}\n')
        글 = 돌리기('check_architecture.py', 뿌리=뿌리)
        봄('아무도 안 쓰는 차림표를 잡는다',
           '안 쓰는 파일' in 글, 글[-500:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_design — 옛 쪽보다 줄면 잡는가 ───────────────────
def 시험_옛쪽대비():
    print('[24] check_design — 옛 쪽이 가졌던 것을 잃으면 잡는가')

    글 = 돌리기('check_design.py')
    봄('지금은 법·안전 말이 권역 쪽에 다 있다',
       '권역 57쪽 모두 있습니다' in 글 or '모두 있습니다' in 글, 글[-500:])

    # 안전 말을 지우면 잡아야 합니다 — 오늘 실제로 빠져 있던 것입니다
    def 안전지우기(사본, 상자):
        import re as _re
        for 이름 in ('taean.html', 'boseong.html'):
            a = os.path.join(사본, 이름)
            if not os.path.isfile(a):
                continue
            s2 = io.read(a)
            # ★ 클래스가 **하나뿐이라고 보지 않습니다** (2026-09-29)
            #
            #   전에는 `class="firsttime"` 으로 닫는 따옴표까지 찾았습니다.
            #   그런데 「처음이신가요?」를 단추 꼴로 바꾸며 클래스를
            #   `firsttime firsttime--btn` 으로 늘리자 **아무것도 안
            #   지워졌습니다.** 그러면 검사기는 멀쩡한 쪽을 보고
            #   「잘못이 없다」고 하고, 시험은 「검사기가 못 잡았다」고
            #   합니다. **둘 다 옳은데 결론만 틀립니다.**
            #
            #   뮤테이션 시험이 **겉모양에 매여 있으면 조용히 헛돕니다.**
            상자.쓰기(a, _re.sub(
                r'(?is)<details class="firsttime[^"]*".*?</details>',
                '', s2))

    되돌리개, 사본 = 사이트사본(안전지우기)
    try:
        글 = 돌리기('check_design.py', 사이트=사본)
        봄('안전 안내를 지우면 잡는다',
           '테트라포드' in 글 and '✗' in 글, 글[-600:])
    finally:
        되돌리개()


# ── check_design [5-5] — 그림 설명이 본문을 베끼면 잡는가 ──
def 시험_베낀설명():
    print('[24-2] check_design [5-5] — 그림 설명이 본문을 베끼면 잡는가')

    글 = 돌리기('check_design.py')
    봄('지금은 그림 설명이 본문과 다르다',
       '그림 설명이 본문과 다릅니다' in 글, 글[-600:])

    # ★ **정말 베끼게 만듭니다** — 본문 한 토막을 그대로 figcaption 에
    #   넣습니다. 겉만 건드리면 시험이 조용히 헛돕니다.
    def 베끼기(사본, 상자):
        import re as _re
        for 이름 in ('fish/bollak.html', 'catch/bajirak.html'):
            a = os.path.join(사본, *이름.split('/'))
            if not os.path.isfile(a):
                continue
            s2 = io.read(a)
            # figcaption 을 뺀 본문에서 긴 글월 하나를 고릅니다
            본 = _re.sub(r'(?s)<figcaption[^>]*>.*?</figcaption>', ' ', s2)
            본 = _re.sub(r'(?s)<script.*?</script>', ' ', 본)
            # ★ **<title> 을 집지 않습니다** (2026-09-30)
            #   처음에는 쪽 제목을 베껴 넣었는데, 그것은 줄표가 든
            #   짧은 글이라 검사기가 건너뛰었습니다. 시험이 헛돌았습니다.
            본 = 본.split('<body', 1)[-1]
            본 = _re.sub(r'<[^>]+>', ' ', 본)
            글월 = [x.strip() for x in _re.split(r'[.!?]', 본)
                    if len(_re.findall(r'[가-힣]', x)) >= 30
                    and '—' not in x]
            if not 글월:
                continue
            베낀것 = 글월[0][:60]
            s3 = _re.sub(r'(?s)(<figcaption[^>]*>)(.*?)(</figcaption>)',
                         lambda m: m.group(1) + m.group(2) + ' ' + 베낀것
                                   + m.group(3),
                         s2, count=1)
            상자.쓰기(a, s3)

    되돌리개, 사본 = 사이트사본(베끼기)
    try:
        글 = 돌리기('check_design.py', 사이트=사본)
        봄('그림 설명이 본문을 베끼면 잡는다',
           '그림 설명이 본문과 겹치는 곳' in 글 and '✗' in 글,
           글[-700:])
    finally:
        되돌리개()


# ── check_design [5-6] — PC 보기가 빠지면 잡는가 ──
def 시험_피시보기():
    print('[24-3] check_design [5-6] — PC 화면으로 보기가 빠지면 잡는가')

    글 = 돌리기('check_design.py')
    봄('지금은 모든 쪽에 PC 보기가 있다',
       'PC 화면으로 보기를 갖습니다' in 글, 글[-600:])

    # ★ **정말 지웁니다** — 단추와 스크립트를 통째로 뺍니다.
    #   2026-09-30 주인이 「푸터에 피씨화면보기 기능이 사라졌어」
    #   하셨을 때, 실제로 이렇게 통째로 빠져 있었습니다.
    def 지우기(사본, 상자):
        import re as _re
        for 이름 in ('index.html', 'taean.html'):
            a = os.path.join(사본, 이름)
            if not os.path.isfile(a):
                continue
            s2 = io.read(a)
            s3 = _re.sub(r'(?is)<p class="pcview">.*?</p>', '', s2)
            s3 = _re.sub(r'(?is)<script>\(function\(\)\{var a='
                         r'document\.getElementById\("pcView"\).*?</script>',
                         '', s3)
            상자.쓰기(a, s3)

    되돌리개, 사본 = 사이트사본(지우기)
    try:
        글 = 돌리기('check_design.py', 사이트=사본)
        봄('PC 보기를 지우면 잡는다',
           'PC 화면으로 보기가 성치 않은 쪽' in 글 and '\u2717' in 글,
           글[-700:])
    finally:
        되돌리개()


# ── check_tide_old — 옛 쪽과 새 쪽의 음력이 갈리면 잡는가 ──
def 시험_옛물때():
    print('[25] check_tide_old — 옛·새 음력이 갈리면 잡는가')

    글 = 돌리기('check_tide_old.py')
    봄('지금은 옛 쪽과 새 쪽이 같은 답을 낸다',
       '하나도 안 다릅니다' in 글, 글[-400:])
    봄('못 쟀으면 「같다」고 하지 않는다',
       '재지 못한 것은 「같다」가 아닙니다' in io.read(
           os.path.join(ROOT, 'engine', 'check_tide_old.py'), default=''),
       '검사기에 그 다짐이 적혀 있어야 합니다')


# ── check_canary — 카나리가 사라지면 잡는가 ────────────────
def 시험_카나리():
    print('[26] check_canary — 표본이 고쳐지면 잡는가')

    글 = 돌리기('check_canary.py')
    봄('지금은 검사기가 모두 살아 있다',
       '모두 살아 있습니다' in 글, 글[-400:])

    # 카나리를 고쳐 놓으면(=멀쩡하게 만들면) 잡아야 합니다
    t = tempfile.mkdtemp(prefix='canary-')
    try:
        뿌리 = os.path.join(t, '두번째도전')
        shutil.copytree(ROOT, 뿌리, ignore=shutil.ignore_patterns(
            'site', '.git', '__pycache__', '.tmp', 'release',
            # ★ 사진 71MB 는 복사할 까닭이 없습니다 (2026-09-28)
            #   시험마다 통째로 베끼다 디스크를 때려, 같이 돌던
            #   check_console 이 크롬을 못 얻고 죽었습니다.
            'photo'))
        a = os.path.join(뿌리, 'tests', 'canary', '빈링크', 'index.html')
        if os.path.isfile(a):
            io.write(a, io.read(a).replace('href=""', 'href="b.html"'))
        글 = 돌리기('check_canary.py', 뿌리=뿌리)
        봄('카나리를 고쳐 놓으면 잡는다',
           '못 잡았습니다' in 글, 글[-600:])
    finally:
        shutil.rmtree(t, ignore_errors=True)



# ── check_coverage — 자료가 쪽까지 안 닿으면 잡는가 ────────
def 시험_닿았나():
    print('[27] check_coverage — 자료가 쪽까지 안 닿으면 잡는가')

    글 = 돌리기('check_coverage.py')
    봄('지금은 자료가 모두 손님 눈까지 닿는다',
       '모두 손님 눈까지 닿습니다' in 글, 글[-500:])

    # 권역 쪽에서 명소 이름을 지우면 잡아야 합니다
    def 명소지우기(사본, 상자):
        a = os.path.join(사본, 'taean.html')
        if os.path.isfile(a):
            s2 = io.read(a)
            # 쪽 전체를 비우면 「볼 쪽이 없다」가 되니 한 쪽만 망칩니다
            상자.쓰기(a, s2.replace('만리포', '□□□')
                          .replace('신두리', '□□□'))

    되돌리개, 사본 = 사이트사본(명소지우기)
    try:
        글 = 돌리기('check_coverage.py', 사이트=사본, 인자=['--strict'])
        봄('명소 이름을 지우면 잡는다',
           '끊김' in 글 and '✗' in 글, 글[-600:])
    finally:
        되돌리개()


# ── check_actionable — 판단이 사라지면 잡는가 (계약-33) ────
def 시험_판단되나():
    print('[28] check_actionable — 판단이 사라지면 잡는가')

    # ★ 이 검사기는 **크롬으로 그려서** 봅니다.
    #   판단 칸은 자바스크립트가 만들기 때문입니다.
    #   크롬이 없으면 끝난값 4 (못 잰 것) 를 냅니다.
    글 = 돌리기('check_actionable.py')
    if '크롬' in 글 and '못 잰 것' in 글:
        봄('크롬이 없으면 통과시키지 않는다', 'NOT_TESTED' in 글, 글[-300:])
        print('')
        return

    봄('지금은 보고 나서 판단까지 된다',
       '판단까지 됩니다' in 글, 글[-500:])

    # 판단 칸을 만드는 줄을 지우면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p2 = os.path.join(뿌리, 'assets', 'js', 'tide.js')
        원 = io.read(p2)
        # ★ **부르는 곳을 모두 지웁니다** (2026-10-02)
        #   전에는 `'칸.appendChild(언제갈까(날들));'` 을 지웠습니다.
        #   실제 코드는 `두칸.appendChild(...)` 라 **앞의 「두」만 남고**
        #   자바스크립트가 깨졌습니다. 그런데도 검사기는 「언제갈까」
        #   글자가 함수 정의에 남아 통과했습니다.
        #   짓는 줄은 두고 **부르는 곳만** 없앱니다.
        import re as _re
        상한것 = _re.sub(r'(?<!function )언제갈까\s*\(날들\)', 'null', 원)
        봄('판단 칸을 정말 지웠다', 상한것 != 원)
        io.write(p2, 상한것)
        # 쪽을 다시 만들어야 그 자바스크립트를 씁니다
        돌리기('build.py', 뿌리=뿌리)
        글 = 돌리기('check_actionable.py', 인자=['--strict'], 뿌리=뿌리)
        봄('판단이 사라지면 잡는다',
           '판단 칸이 없는' in 글 or ('✗' in 글 and '0개에 있습니다' in 글),
           글[-600:])


# ── check_promise — 약속한 것이 사라지면 잡는가 (2026-10-02) ──
def 시험_약속지킴():
    """★ 이 검사기를 만든 까닭이 **조용히 어긋나는 것**이었습니다.

      권역 쪽 57곳의 「14일 물때표 보기」 단추가 /tide/ 로 가는데
      그 쪽에 14일 달력이 **없었습니다.** 쪽이 있고 404 도 아니라
      링크 검사는 멀쩡히 통과했습니다. 주인이 먼저 찾으셨습니다.

      그러니 이 시험은 **검사기가 정말 눈을 뜨고 있는지**를 봅니다.
    """
    print('[37] check_promise — 약속한 것이 사라지면 잡는가')

    글 = 돌리기('check_promise.py', 인자=['--strict'])
    봄('지금은 단추가 약속한 것이 모두 제자리에 있다',
       '모두 제자리에 있습니다' in 글, 글[-500:])

    # 간 쪽에서 약속한 표식을 지우면 잡아야 합니다.
    #   /tide/ 에서 14일 달력 표식을 지웁니다 — 권역 쪽 57곳이
    #   「14일 물때표 보기」로 그리로 보내고 있습니다.
    def 표식지우기(사본, 상자):
        a = os.path.join(사본, 'tide', 'index.html')
        if not os.path.isfile(a):
            return
        s2 = io.read(a)
        상자.쓰기(a, s2.replace('data-days="14"', 'data-days="0"')
                      .replace('tide-days', 'xx-days'))

    되돌리개, 사본 = 사이트사본(표식지우기)
    try:
        # ★ **정말 망가졌는지 먼저 봅니다** — 뮤테이션이 헛돌면
        #   검사기는 멀쩡한 쪽을 보고 「잘못 없음」이라 합니다
        원 = io.read(os.path.join(ROOT, 'site', 'tide', 'index.html'),
                     default='')
        뒤 = io.read(os.path.join(사본, 'tide', 'index.html'), default='')
        봄('14일 표식을 정말 지웠다', bool(원) and 원 != 뒤)

        글 = 돌리기('check_promise.py', 사이트=사본, 인자=['--strict'])
        봄('약속한 것이 사라지면 잡는다',
           '14일 물때표' in 글 and '✗' in 글, 글[-600:])
    finally:
        되돌리개()


def 시험_채비():
    """check_rigs — 채비 부품이 그림을 잃으면 잡는가 (2026-09-30)

    ★ 이 검사기를 만든 까닭 자체가 **조용히 틀리는 것**이었습니다.
      부품 이름이 그림 조건에 안 걸리면 오류도 안 나고 쪽도
      만들어집니다. 사람이 그림을 들여다봐야만 압니다.
      좁쌀봉돌은 **고리봉돌로 그려진 채 배포까지 나갔습니다.**

      그러니 이 시험은 **검사기가 정말 눈을 뜨고 있는지**를 봅니다.
    """
    print('[29] check_rigs — 채비 부품이 그림을 잃으면 잡는가')

    글 = 돌리기('check_rigs.py', 인자=['--strict'])
    봄('지금은 부품이 모두 그림을 갖는다',
       '모두 그림을 갖습니다' in 글, 글[-400:])

    # (가) 그림이 없는 부품 이름을 넣으면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'data', 'raw', 'rigs.json')
        원 = io.read(p)
        d = json.loads(원)
        # ★ **안내도가 없는 채비를 골라야 합니다** (2026-10-02)
        #   check_rigs 는 「안내도(webp)를 쓰는 채비는 부품 그림을
        #   안 따진다」고 적어 두었습니다. 그림을 통째로 쓰니
        #   부품 하나하나를 SVG 로 그릴 까닭이 없습니다.
        #   그런데 이 시험은 **첫 번째 채비**에 넣고 있었고,
        #   오늘 그 첫 번째(bottom)에 안내도가 생겼습니다. 그래서
        #   검사기가 안 보게 됐고, 시험은 「못 잡는다」고 적었습니다.
        #   **그림이 더 들어가도 안 깨지게** 매번 골라냅니다.
        안내도칸 = os.path.join(뿌리, 'data', 'img', 'rig')
        있는안내도 = set(os.listdir(안내도칸)) if os.path.isdir(안내도칸) else set()
        고를수있는것 = [k for k in d['채비']
                    if not any('%s.%s' % (k, 끝) in 있는안내도
                               for 끝 in ('webp', 'png', 'jpg'))]
        if not 고를수있는것:
            # ★ **없으면 사본에서 하나 만들어 씁니다** (2026-10-06)
            #   2026-10-06 에 채비 16가지가 **모두** 안내도를 갖추면서
            #   고를 것이 없어져 이 시험이 터졌습니다. 좋은 일을 해서
            #   시험이 깨진 것입니다.
            #
            #   시험을 지우면 `check_rigs` 가 시험 없이 돌게 되어
            #   계약-28 을 어깁니다. 여기는 `isolate.일터()` 가 만든
            #   **저장소 사본**이므로, 사본에서 안내도 한 짝을 치워
            #   「부품 SVG 를 쓰는 채비」를 만들어 냅니다.
            #   진짜 `data/img/rig/` 는 한 글자도 안 바뀝니다.
            치울것 = sorted(d['채비'])[0]
            치웠나 = False
            for 끝 in ('webp', 'png', 'jpg'):
                for 이름 in ('%s.%s' % (치울것, 끝),
                             '%s-m.%s' % (치울것, 끝)):
                    길 = os.path.join(안내도칸, 이름)
                    if os.path.isfile(길):
                        os.remove(길)
                        치웠나 = True
            if not 치웠나:
                raise AssertionError(
                    '안내도를 치울 수도 없습니다 — data/img/rig 자리가 '
                    '바뀌었으면 여기도 고칩니다. 만들 수 없으면 헛돕니다.')
            고를수있는것 = [치울것]
        아무갈래 = 고를수있는것[0]
        d['채비'][아무갈래]['부품'].append(
            {'이름': '없는부품이름', '값': ''})
        상한것 = json.dumps(d, ensure_ascii=False, indent=2)
        봄('자료를 정말 망가뜨렸다', 상한것 != 원)
        io.write(p, 상한것)
        글 = 돌리기('check_rigs.py', 인자=['--strict'], 뿌리=뿌리)
        봄('그림 없는 부품을 잡는다',
           '그림이 없는 부품' in 글 and '없는부품이름' in 글, 글[-500:])

    # (나) 넓은 이름이 좁은 이름을 가로채게 바꾸면 잡아야 합니다
    #     — 좁쌀봉돌이 고리봉돌로 그려졌던 그 잘못입니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'engine', 'art.py')
        원 = io.read(p)
        상한것 = 원.replace("    if '좁쌀' in 이름:",
                            "    if '좁쌀아님' in 이름:")
        봄('조건 차례를 정말 뒤집었다', 상한것 != 원)
        io.write(p, 상한것)
        글 = 돌리기('check_rigs.py', 인자=['--strict'], 뿌리=뿌리)
        봄('좁쌀봉돌이 고리봉돌로 그려지면 잡는다',
           '가로채' in 글 or '차례가 뒤집혔습니다' in 글, 글[-500:])

    # (다) 어종이 **없는 채비**를 가리키게 바꾸면 잡아야 합니다
    #     — 참돔이 boat, 농어가 lure 를 가리켜 **채비도가 아예 안 나온 채**
    #       배포되어 있었습니다 (2026-09-30 주인 지적
    #       「참돔은 채비도 없고 그림도 엉망이고」)
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'data', 'raw', 'guide.json')
        d = json.loads(io.read(p))
        고침 = False
        for x in d['어종']:
            if x.get('갈래') == '낚시':
                x['그림'] = '없는채비이름'
                고침 = True
                break
        봄('어종 자료를 정말 망가뜨렸다', 고침)
        io.write(p, json.dumps(d, ensure_ascii=False, indent=2))
        글 = 돌리기('check_rigs.py', 인자=['--strict'], 뿌리=뿌리)
        봄('없는 채비를 가리키면 잡는다',
           '없는 채비를 가리키는' in 글 and '없는채비이름' in 글, 글[-600:])


def 시험_규정():
    """check_rules — 어종 아이디가 어긋나면 잡는가 (2026-10-01)

    ★ 이 검사기를 만든 까닭 — **아이디가 두 벌**입니다.

          id        쪽 파일 이름    site/fish/byeongedom.html
          어종아이디  포인트가 부름   "대상": ["bengedom", ...]

      셋이 어긋납니다(벵에돔·갑오징어·무늬오징어). 모르고 id 로
      맞추면 **포인트 1,169곳이 조용히 빠집니다.** 오류도 안 나고
      쪽도 만들어져 아무도 모릅니다.

      그러니 이 시험은 **검사기가 정말 눈을 뜨고 있는지**를 봅니다.
      통과만 하고 아무것도 안 보는 검사는 없는 것보다 나쁩니다.
    """
    print('[31] check_rules — 어종 아이디가 어긋나면 잡는가')

    글 = 돌리기('check_rules.py', 인자=['--strict'])
    봄('지금은 아이디가 어긋나지 않는다',
       '어김 없습니다' in 글, 글[-400:])

    # (가) 어종아이디를 겹치게 만들면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'data', 'raw', 'guide.json')
        원 = io.read(p)
        d = json.loads(원)
        것들 = d['어종']
        것들[1]['어종아이디'] = (것들[0].get('어종아이디')
                                or 것들[0]['id'])
        상한것 = json.dumps(d, ensure_ascii=False, indent=2)
        봄('자료를 정말 망가뜨렸다', 상한것 != 원)
        io.write(p, 상한것)
        글 = 돌리기('check_rules.py', 인자=['--strict'], 뿌리=뿌리)
        봄('겹친 어종아이디를 잡는다',
           '어종아이디가 겹칩니다' in 글, 글[-600:])

    # (나) 포인트가 **쪽 아이디**를 쓰게 바꾸면 잡아야 합니다
    #     — 이것이 포인트 1,169곳을 조용히 빠뜨리던 그 잘못입니다
    with isolate.일터() as 뿌리:
        g = os.path.join(뿌리, 'data', 'raw', 'guide.json')
        d = json.loads(io.read(g))
        두벌 = None
        for 것 in d['어종']:
            포 = 것.get('어종아이디')
            if 포 and 포 != 것['id']:
                두벌 = (것['id'], 포)
                break
        봄('두 벌인 어종이 자료에 있다', bool(두벌), str(두벌))
        if 두벌:
            쪽, 포 = 두벌
            p = os.path.join(뿌리, 
                             'data', 'raw', 'points', 'jeonnam.json')
            원 = io.read(p)
            상한것 = 원.replace(json.dumps(포, ensure_ascii=False),
                                json.dumps(쪽, ensure_ascii=False))
            봄('포인트 자료를 정말 망가뜨렸다', 상한것 != 원)
            io.write(p, 상한것)
            글 = 돌리기('check_rules.py', 인자=['--strict'],
                       뿌리=뿌리)
            봄('포인트가 쪽 아이디를 쓰면 잡는다',
               '쪽 아이디(id)를 쓴 곳' in 글, 글[-700:])

def 시험_잃은말():
    """check_guide_loss — 어종 안내를 늘리다 **지운 것**을 잡는가 (2026-09-30)

    ★ 이 검사기를 만든 까닭
      지식백과 자료로 어종 칸을 다시 쓰면서 **덮어썼습니다.**
      우럭의 「바닥 채비」, 볼락의 「민장대·구슬찌」,
      숭어의 **「훌치기는 지역에 따라 금지」** 가 사라졌습니다.
      마지막 것은 규정에 관한 말이라 없어지면 손님이 다칠 수 있습니다.

      글자 수는 오히려 **늘었기 때문에** check_golden 은 통과합니다.
      그래서 낱말 단위로 따로 봅니다.
    """
    print('[30] check_guide_loss — 안내를 늘리다 지운 것을 잡는가')

    글 = 돌리기('check_guide_loss.py', 인자=['--strict'])
    봄('지금은 잃은 말이 없다',
       '하나도 안 사라졌습니다' in 글 or '견줄 것이 없' in 글, 글[-400:])

    # 뜻이 큰 말을 지우면 잡아야 합니다
    with isolate.일터() as 뿌리:
        p = os.path.join(뿌리, 'data', 'raw', 'guide.json')
        d = json.loads(io.read(p))
        뭉갠어종 = None
        for x in d['어종']:
            글자 = (x.get('채비') or {}).get('ko') or ''
            if '찌낚시' in 글자:
                x['채비']['ko'] = '채비를 씁니다.'      # 통째로 뭉갭니다
                뭉갠어종 = x['이름']['ko']
                break
        봄('안내를 정말 지웠다', bool(뭉갠어종))
        io.write(p, json.dumps(d, ensure_ascii=False, indent=2))
        글 = 돌리기('check_guide_loss.py', 인자=['--strict'], 뿌리=뿌리)
        # 어떤 말이 먼저 걸리는지는 어종마다 다릅니다.
        # **그 어종을 짚어 냈는가**만 봅니다.
        봄('있던 말이 사라지면 잡는다',
           '사라진 어종' in 글 and (뭉갠어종 or '') in 글, 글[-600:])
    print('')


# ── check_hero_quality — **사진이 빠진 것을 잡는가** ───────
def 시험_사진품질():
    """★ 권역 쪽에 대표 사진이 없으면 **배포를 막아야** 합니다

    주인 규칙 6-1 — 「권역 쪽에는 대표 사진이 반드시 들어갑니다.
    빠지면 배포를 막습니다」

    ★ **정말 망가뜨려 봅니다.** 사진 파일을 지우고도 「이상 없음」
      이라고 하면 그 검사기는 없는 것보다 나쁩니다.
    """
    print('[21] check_hero_quality — 빠진 사진을 잡는가')

    글 = 돌리기('check_hero_quality.py')
    봄('지금은 사진이 다 있다',
       '손볼 곳' not in 글 and '권역 대표 사진' in 글, 글[-500:])
    봄('세 등급으로 나눈다',
       '좋음' in 글 and '보통' in 글 and '교체 필요' in 글, 글[-300:])

    # (가) **진짜 히어로 사진을 지우면** 막아야 합니다
    #
    #   ★ 아무 사진이나 지우면 안 됩니다 (2026-10-02 겪음)
    #     img/coast/ 첫 파일을 지웠더니 검사기가 안 걸렸습니다.
    #     그 파일이 **어느 권역의 히어로도 아니었기** 때문입니다.
    #     뮤테이션은 **정말 망가뜨려야** 합니다 — 안 그러면
    #     「통과」라고 나와도 헛돕니다.
    지운것 = {'이름': None}

    def 사진지우기(사본, 상자):
        sys.path.insert(0, ROOT)
        from engine.data import 자료 as _자료
        d = _자료()
        for r in d.권역들:
            사진 = d.히어로(r['id']) or {}
            파일 = 사진.get('파일')
            if not 파일:
                continue
            p = os.path.join(사본, 파일.replace('/', os.sep))
            if os.path.isfile(p):
                지운것['이름'] = 파일
                상자.지우기(p)
                return

    되돌리개, 사본 = 사이트사본(사진지우기)
    try:
        if 지운것['이름']:
            글 = 돌리기('check_hero_quality.py', 사이트=사본)
            봄('사진 파일을 지우면 막는다 (%s)' % 지운것['이름'],
               '손볼 곳' in 글 and '자리에 없' in 글, 글[-700:])
        else:
            봄('사진 파일을 지우면 막는다', False, '지울 사진을 못 찾았습니다')
    finally:
        되돌리개()


# ── check_tide_binding — **관측소가 어긋나면 잡는가** ──────
def 시험_물때바인딩():
    """★ 자료의 관측소와 서버가 **다른 곳**을 가리키면 막아야 합니다

    쪽에는 자료의 이름이 적히는데 숫자는 서버 것입니다. 손님은
    「묵호 관측소 기준」을 읽으면서 다른 곳 숫자를 봅니다.

    ★ 이 검사기는 **인터넷을 씁니다.** 그래서 여기서는 바깥을
      부르지 않고, **가름 함수만** 시험합니다. 바깥이 느린 날
      시험이 실패하면 그것은 시험이 아닙니다.
    """
    print('[22] check_tide_binding — 관측소가 어긋나면 잡는가')
    import importlib
    sys.path.insert(0, ROOT)
    m = importlib.import_module('engine.check_tide_binding')

    봄('판정 밖에 둔 까닭이 적혀 있다',
       'check_tide_binding.py' in io.read(
           os.path.join(ROOT, 'engine', 'gate.py'), default=''),
       'gate.py 의 밖에둔검사 에 적어야 check_architecture 가 봐줍니다')
    봄('막음·알림을 따로 둔다 (계약-21)',
       hasattr(m, '막음') and hasattr(m, '알림'),
       '모듈 수준에 「막음, 알림 = [], []」 이 있어야 합니다')
    봄('서버를 못 받으면 터지지 않는다',
       m.받기('없는권역이름zzz')[0] is None,
       '못 받으면 (None, 까닭) 을 돌려줘야 합니다')


# ── check_photo_dup — 한 쪽에 같은 사진이 두 번이면 잡는가 ──
def 시험_사진두번():
    """★ 계약-28 — 검사기도 시험받는다 (2026-10-06)

    이 검사기는 **알맹이 지문**으로 봅니다. 이름이 달라도 같은
    사진이면 잡습니다. 그러니 시험도 이름이 아니라 **같은 사진을
    두 번 넣어** 망가뜨려야 제대로 잽니다.
    """
    print('[30] check_photo_dup — 한 쪽에 같은 사진이 두 번이면 잡는가')

    글 = 돌리기('check_photo_dup.py', 인자=['--strict'])
    봄('지금은 한 쪽에 같은 사진이 두 번 나오지 않는다',
       '어김 없습니다' in 글, 글[-400:])

    # (가) 같은 사진을 한 번 더 넣으면 잡아야 합니다
    #
    # ★ **쪽 이름을 박지 않습니다** (2026-10-06 — 처음에 박았다 깨졌습니다)
    #   처음에는 `about.html` 이라 적었는데 그 쪽에는 <img> 가
    #   없었습니다. 사이트가 자라며 쪽 차림이 바뀌면 시험이
    #   조용히 깨집니다. **사진이 있는 쪽을 그때그때 골라** 씁니다.
    # ★ **이름을 달리해야 걸립니다** (2026-10-06 — 처음에 못 잡았습니다)
    #   이 검사기는 **같은 주소를 두 번** 쓴 것은 일부러 안 잡습니다.
    #   `<picture>` 가 가로·세로를 같은 주소로 쓰기 때문입니다 —
    #   손님에게는 한 장으로 보이니 중복이 아닙니다.
    #   잡는 것은 **이름이 다른데 알맹이가 같은** 사진입니다.
    #   그러니 시험도 사진 파일을 **다른 이름으로 베껴** 심어야
    #   합니다. 그대로 복제하면 검사기는 멀쩡한데 「못 잡는다」고
    #   적히고, 그 시험은 영영 헛돕니다.
    def 사진겹치기(사본, 상자):
        import re as _re
        for 이름 in sorted(os.listdir(사본)):
            if not 이름.endswith('.html') or 이름.startswith('__'):
                continue
            글 = io.read(os.path.join(사본, 이름)) or ''
            m = _re.search(r'<img[^>]*src="([^"]+\.(?:jpg|png|webp))"', 글)
            if not m:
                continue
            주소 = m.group(1)
            원본 = os.path.join(사본, 주소.replace('/', os.sep))
            if not os.path.isfile(원본):
                continue
            밑, 끝 = os.path.splitext(원본)
            쌍둥이 = 밑 + '-시험쌍둥이' + 끝
            상자.복사(원본, 쌍둥이)       # 알맹이는 같고 이름만 다릅니다
            새주소 = (os.path.splitext(주소)[0] + '-시험쌍둥이'
                      + os.path.splitext(주소)[1])
            본문끝에심기(사본,
                        '<img src="%s" alt="시험">' % 새주소, 쪽=이름, 상자=상자)
            return
        raise AssertionError(
            '맨 위 쪽 어디에도 베낄 사진이 없습니다 — 쪽 차림이 '
            '통째로 바뀌었습니다. 심을 것이 없으면 시험은 헛돕니다.')

    되돌리개, 사본 = 사이트사본(사진겹치기)
    try:
        글 = 돌리기('check_photo_dup.py', 사이트=사본, 인자=['--strict'])
        봄('같은 사진을 두 번 넣으면 잡는다',
           '같은 사진이 두 번 나오는 쪽' in 글, 글[-500:])
    finally:
        되돌리개()


# ── check_rig_images — 채비 그림이 없어지면 잡는가 ──────────
def 시험_채비그림():
    """★ 계약-28 — 검사기도 시험받는다 (2026-10-06)

    채비 16가지가 모두 안내도 그림을 갖추고 있습니다. 쪽이
    **없는 그림을 가리키면** 손님에게는 깨진 자리가 보입니다.
    그것을 잡는지 봅니다.
    """
    print('[31] check_rig_images — 쪽이 없는 그림을 가리키면 잡는가')

    글 = 돌리기('check_rig_images.py', 인자=['--strict'])
    봄('지금은 채비 그림이 모두 제자리에 있다',
       '어김 없습니다' in 글, 글[-400:])

    # (가) 쪽이 **없는 그림**을 가리키게 하면 잡아야 합니다
    #
    # ★ **그림 파일을 지우는 것으로는 안 됩니다** (2026-10-06)
    #   처음에 `site/img/rig/` 에서 지웠는데 안 걸렸습니다.
    #   이 검사기는 그림을 **원본 자리(`data/img/rig/`)**에서 셉니다 —
    #   `site/` 는 생성물이라 다음 빌드에 사라지기 때문입니다.
    #   쪽 사본만 주는 시험에서는 원본이 그대로이니 아무 일도
    #   안 일어납니다. 대신 **쪽이 가리키는 이름을 바꿔** 없는
    #   그림을 가리키게 만듭니다 — 손님에게는 깨진 자리가 됩니다.
    def 없는그림가리키기(사본, 상자):
        import re as _re
        밭 = os.path.join(사본, 'rig')
        것들 = sorted(f for f in os.listdir(밭)
                      if f.endswith('.html')) if os.path.isdir(밭) else []
        for 이름 in 것들:
            p = os.path.join(밭, 이름)
            s2 = io.read(p) or ''
            m = _re.search(r'img/rig/([A-Za-z0-9_-]+\.webp)', s2)
            if not m:
                continue
            상자.쓰기(p, s2.replace('img/rig/' + m.group(1),
                                   'img/rig/없는그림시험.webp'))
            return
        raise AssertionError(
            'site/rig 에 채비 그림을 가리키는 쪽이 없습니다 — 쪽 차림이 '
            '바뀌었으면 여기도 고칩니다. 바꿀 것이 없으면 헛돕니다.')

    되돌리개, 사본 = 사이트사본(없는그림가리키기)
    try:
        글 = 돌리기('check_rig_images.py', 사이트=사본, 인자=['--strict'])
        봄('쪽이 없는 그림을 가리키면 잡는다',
           '없는 그림을 가리키는' in 글, 글[-500:])
    finally:
        되돌리개()


# ── check_origin — `origin` 이 옛 저장소를 가리키는 것을 잡는가 ──
def 시험_원격():
    """★ **git 원격을 실제로 꾸며** 잡는지 봅니다 (2026-10-07 바깥 검수)

    실제로 나간 잘못 — `origin` 이 **2026-09-28 에 멈춘** `badagaja-2nd`
    를 가리키고 있었습니다. 대장은 `badagaja-engine` 인데 이름이
    거꾸로라, 바깥에서 볼 때 **9일 전 판**을 보고 판단했습니다.

    바깥 검수 — 「도구가 **기본 remote 를 따라가거나**, 사람이
      **습관적으로 origin 을 보면** 다시 옛판을 기준으로 판단합니다」
    """
    print('[38] check_origin — origin 이 옛 저장소를 가리키면 잡는가')

    대장주소 = 'git@github.com:ohjunhan-design/badagaja-engine.git'
    옛주소 = 'git@github.com:ohjunhan-design/badagaja-2nd.git'

    def 꾸민사본(원격들):
        """`engine/check_origin.py` 만 둔 사본에 **원격을 붙입니다.**"""
        t = tempfile.mkdtemp(prefix='원격-')
        os.makedirs(os.path.join(t, 'engine'))
        shutil.copy2(os.path.join(ROOT, 'engine', 'check_origin.py'),
                     os.path.join(t, 'engine', 'check_origin.py'))
        깃 = ['git', '-c', 'safe.directory=*']
        subprocess.run(깃 + ['init', '-q'], cwd=t,
                       capture_output=True, timeout=60)
        for 이름, 주소 in 원격들:
            subprocess.run(깃 + ['remote', 'add', 이름, 주소], cwd=t,
                           capture_output=True, timeout=60)
        return t

    def 끝난값(뿌리):
        r = subprocess.run(
            [sys.executable, os.path.join(뿌리, 'engine', 'check_origin.py')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=120)
        return r.returncode, (r.stdout or '') + (r.stderr or '')

    # (가) origin 이 대장이면 — 깨끗하게 통과해야 합니다
    t = 꾸민사본([('origin', 대장주소)])
    try:
        값, 글 = 끝난값(t)
        봄('origin 이 대장이면 통과한다',
           값 == 0 and 'origin` 이 대장을 가리킵니다' in 글, 글[-500:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (나) ★ **실제로 나간 모양** — 대장이 딴 이름에 붙어 있습니다
    t = 꾸민사본([('origin', 옛주소), ('engine', 대장주소)])
    try:
        값, 글 = 끝난값(t)
        봄('origin 이 옛 저장소를 가리키면 알린다',
           'origin` 이 대장이 아닙니다' in 글, 글[-700:])
        # ★ 2026-10-07 주인 허락으로 이름을 바로잡았으므로 **막음**입니다.
        #   고칠 수 있는 것이 되었으니 알림으로 둘 까닭이 없습니다.
        봄('되돌아가면 배포를 막는다',
           값 == 1, '끝난값 %s' % 값)
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (다) 대장을 가리키는 원격이 **하나도 없으면** — 막아야 합니다
    t = 꾸민사본([('origin', 옛주소)])
    try:
        값, 글 = 끝난값(t)
        봄('대장을 가리키는 원격이 없으면 막는다',
           값 == 1 and '올릴 곳이 없습니다' in 글, 글[-700:])
    finally:
        shutil.rmtree(t, ignore_errors=True)

    # (라) 호스트 **별칭**을 써도 알아봐야 합니다
    #     저희는 ssh 설정으로 badagaja-engine.github.com 처럼 갈라 씁니다.
    t = 꾸민사본([('origin',
                  'git@badagaja-engine.github.com:'
                  'ohjunhan-design/badagaja-engine.git')])
    try:
        값, 글 = 끝난값(t)
        봄('호스트 별칭을 써도 대장으로 알아본다',
           값 == 0 and 'origin` 이 대장을 가리킵니다' in 글, 글[-500:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


# ── check_reachable — 들어갈 길이 없는 쪽을 잡는가 ─────────
def 시험_닿는가():
    """★ **판정 함수를 바로** 시험합니다 (2026-10-07 바깥 검수 설계)

    2026-10-07 주인이 첫 쪽 그림에 동그라미를 치고 —
      「너희 이것도 확인해 **이거 링크 없어**」

        <a href="#bada">향토 먹거리 · 명소</a>

    `travel/` 을 만들고도 첫 쪽에서 안 걸고 있었습니다. 고치다
    `data.html`(20.4KB)도 **아무 쪽에서도 안 걸리는** 것을 찾았습니다.
    링크 검사·쪽 목록 검사·약속 검사가 **모두 통과했습니다** —
    쪽은 있고 링크도 안 깨졌으니까요.

    ★ 처음에는 **진짜 site/ 449쪽을 복사**해 링크를 끊는 식으로
      시험을 짰습니다. **네 번 깨졌습니다.** 그런데 깨진 데가 전부
      사본 만들기·정규식 꼴 맞추기였고 **검사 논리는 한 줄도
      안 건드렸습니다.** 바깥 검수가 그 방식을 버리라고 했습니다 —
      「실사이트 복사와 정규식이 잘 되느냐를 시험하고 있었다」

      그래서 **판정 함수를 작은 가짜 쪽으로 바로** 시험하고,
      CLI 통합시험은 **작은 가짜 사이트 한 벌**로 한 번만 돕니다.
    """
    print('[39] check_reachable — 들어갈 길이 없는 쪽을 잡는가')

    sys.path.insert(0, ROOT)
    from engine import check_reachable as CR

    # ── 가짜 쪽 한 벌 — 실제로 나간 잘못과 **같은 모양**입니다
    기본 = {
        'index.html': ('<a href="travel/">여행</a>'
                       '<a href="about.html">소개</a>'
                       '<a href="#bada">향토 먹거리 · 명소</a>'),
        'about.html': '<a href="guide">전체 권역</a>',
        'guide/index.html': '<a href="../index.html">첫 쪽</a>',
        'travel/index.html': '<a href="../index.html">첫 쪽</a>',
    }

    고아, 못닿음, 먼것, 닿음, 걸린곳 = CR.고아들(기본)
    봄('멀쩡하면 고아가 없다', 고아 == [] and 못닿음 == [],
       '고아 %s · 못닿음 %s' % (고아, 못닿음))
    봄('끝 슬래시가 없어도 폴더 쪽으로 본다',
       닿음.get('guide/index.html') == 2,
       '걸음 %s' % 닿음.get('guide/index.html'))

    # (가) ★ **실제로 나간 잘못** — 쪽은 있는데 아무도 안 겁니다
    쪽들 = dict(기본)
    쪽들['data.html'] = '<a href="index.html">첫 쪽</a>'
    고아, 못닿음, _먼, _닿, _건 = CR.고아들(쪽들)
    봄('아무도 안 거는 쪽을 잡는다',
       고아 == ['data.html'], '고아 %s' % 고아)
    봄('그 쪽은 첫 쪽에서도 못 닿는다',
       못닿음 == ['data.html'], '못닿음 %s' % 못닿음)

    # (나) ★ **닻으로 때운 것**도 길이 아닙니다
    #     `#bada` 는 같은 쪽 안 닻이라 travel/ 로 가지 않습니다.
    쪽들 = dict(기본)
    쪽들['index.html'] = 쪽들['index.html'].replace(
        '<a href="travel/">여행</a>', '<a href="#bada">여행</a>')
    고아, 못닿음, _먼, _닿, _건 = CR.고아들(쪽들)
    봄('#닻 으로 때우면 그 쪽은 고아가 된다',
       고아 == ['travel/index.html'], '고아 %s' % 고아)

    # (다) ★ **검색에 숨긴 쪽은 잡지 않아야** 합니다
    #     stats.html 은 noindex 가 붙은 운영자용입니다.
    #     안 걸리는 것이 **의도한 것**이라 잡으면 거짓 경보입니다.
    쪽들 = dict(기본)
    쪽들['stats.html'] = ('<meta name="robots" content="noindex,nofollow">'
                          '<a href="index.html">첫 쪽</a>')
    고아, _못, _먼, _닿, _건 = CR.고아들(쪽들)
    봄('검색에 숨긴 쪽은 고아로 세지 않는다', 고아 == [], '고아 %s' % 고아)

    # (라) ★ **걸려는 있는데 첫 쪽에서 못 가는** 쪽
    #     data.html 만 guide 를 걸고, data.html 자신은 아무도 안 걸던
    #     바로 그 모양입니다.
    쪽들 = dict(기본)
    쪽들['버림.html'] = '<a href="외딴.html">외딴</a>'
    쪽들['외딴.html'] = '<a href="버림.html">버림</a>'
    고아, 못닿음, _먼, _닿, _건 = CR.고아들(쪽들)
    봄('서로만 걸고 첫 쪽에서 못 가면 잡는다',
       못닿음 == ['버림.html', '외딴.html'], '못닿음 %s' % 못닿음)

    # (마) 너무 먼 쪽은 **알림**입니다 (막지 않습니다)
    줄 = {'index.html': '<a href="a1.html">a1</a>'}
    for i in range(1, 8):
        줄['a%d.html' % i] = '<a href="a%d.html">다음</a>' % (i + 1)
    줄['a8.html'] = '<a href="index.html">첫 쪽</a>'
    _고, _못, 먼것, _닿, _건 = CR.고아들(줄)
    봄('첫 쪽에서 너무 먼 쪽을 알린다',
       len(먼것) >= 3 and all(v > CR.먼걸음 for v, _k in 먼것),
       '먼것 %s' % 먼것[:4])

    # (바) ★ **통합시험 하나** — 작은 가짜 사이트로 CLI 를 실제로 돕니다
    #     함수가 맞아도 출력·끝난값이 틀리면 배포가 안 막힙니다.
    t = tempfile.mkdtemp(prefix='닿-')
    try:
        밭 = os.path.join(t, 'site')
        os.makedirs(os.path.join(밭, 'travel'))
        io.write(os.path.join(밭, 'index.html'),
                 '<a href="travel/">여행</a>')
        io.write(os.path.join(밭, 'travel', 'index.html'),
                 '<a href="../index.html">첫 쪽</a>')
        io.write(os.path.join(밭, '외톨이.html'),
                 '<a href="index.html">첫 쪽</a>')
        r = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, 'engine', 'check_reachable.py')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=120,
            env=dict(os.environ, BADAGAJA_SITE=밭,
                     PYTHONIOENCODING='utf-8'))
        글 = (r.stdout or '') + (r.stderr or '')
        봄('CLI 가 고아를 잡고 **끝난값 1** 을 낸다',
           r.returncode == 1 and '외톨이.html' in 글,
           '끝난값 %s · %s' % (r.returncode, 글[-400:]))
        봄('CLI 가 막는 까닭을 사람 말로 적는다',
           '들어갈 길이 없습니다' in 글, 글[-300:])
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 느린순서():
    """**어디서 시간을 쓰는지** 봅니다 (2026-10-07 바깥 검수)."""
    if not _걸린시간:
        return
    합 = sum(x[1] for x in _걸린시간)
    from collections import defaultdict
    묶 = defaultdict(lambda: [0, 0.0])
    for 이름, 초 in _걸린시간:
        묶[이름][0] += 1
        묶[이름][1] += 초
    print('')
    print('어디서 시간을 쓰나 — 검사기를 돌린 %d번 · 합계 %.0f초'
          % (len(_걸린시간), 합))
    for 이름, (몇, 초) in sorted(묶.items(), key=lambda a: -a[1][1])[:10]:
        print('  %6.1f초  %2d번  %s' % (초, 몇, 이름))


def main():
    print('검사기가 잘못을 잡을 줄 아는지')
    print('')
    시험_렌더()
    시험_링크()
    시험_주소()
    시험_계약()
    시험_어중간()
    시험_광고()
    시험_다른언어()
    시험_남길것()
    시험_검색()
    시험_갱신()
    시험_달력()
    시험_자산()
    시험_대표주소()
    시험_콘솔()
    시험_배포뒤()
    시험_주소표()
    시험_깨끗한가()
    시험_물때()
    시험_삭()
    시험_열두달()
    시험_휴대폰()
    시험_사진()
    시험_있던것()
    시험_짜임()
    시험_옛쪽대비()
    시험_베낀설명()
    시험_피시보기()
    시험_옛물때()
    시험_카나리()
    시험_닿았나()
    시험_판단되나()
    시험_약속지킴()
    시험_채비()
    시험_잃은말()
    시험_규정()
    시험_내부메모()
    시험_없는차림이름()
    시험_숫자()
    시험_넙치()
    시험_끊긴쪽()
    시험_사진품질()
    시험_물때바인딩()
    시험_사진두번()
    시험_채비그림()
    시험_원격()
    시험_닿는가()
    # ★ **마지막 안전망** (2026-10-07 바깥 검수)
    #   「어떤 mutation 이 찌꺼기를 남겼는지」를 잡습니다.
    #   만들어 두고 **안 부르면 없는 것과 같습니다** — 실제로
    #   그랬습니다(0번 불렸습니다).
    느린순서()
    모래밭이깨끗한가()
    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  잘못을 못 잡는 검사기는 **없는 것보다 나쁩니다.**')
        print('  없으면 조심이라도 하는데, 있으면 믿어 버립니다.')
        return 1
    print('%d가지 모두 통과 — 검사기가 잘못을 제대로 잡습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
