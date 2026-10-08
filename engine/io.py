# -*- coding: utf-8 -*-
"""파일을 읽고 쓰는 단 하나의 통로.  (계약-13)

왜 이 파일이 있나
    지난 사이트에서 **배포가 하루 멈췄고, 사이트가 두 번 500 오류로 죽었습니다.**
    둘 다 눈에 보이지 않는 글자 때문이었습니다.

      · YAML 파일에 제어문자 \x01 한 글자
        → 깃허브가 파일 전체를 읽지 못함 → 배포가 하루 멈춤
      · .htaccess 에 BOM
        → 아파치가 맨 앞 BOM 을 명령으로 읽음 → 사이트 전체 500

    파일마다 규칙이 다릅니다.
      .ps1        BOM 이 있어야 합니다 (없으면 한글이 깨집니다)
      .htaccess   BOM 이 있으면 안 됩니다 (있으면 500)
      .yml .json  BOM 없음, 제어문자 금지

    이것을 사람이나 AI 가 매번 기억하게 두면 반드시 또 틀립니다.
    **그래서 여기 한 곳에서만 정합니다.**

규칙
    · 파일을 쓸 때는 반드시 write() 를 씁니다. open(...,'w') 를 직접 쓰지 않습니다
    · 확장자를 보고 BOM 과 줄바꿈을 알아서 정합니다
    · 쓰기 전에 제어문자를 검사해, 있으면 **쓰지 않고 멈춥니다**
"""
import io as _io
import os
import re
import json
import hashlib

# 임시 파일이 작업 폴더와 같은 드라이브로 가게 합니다 (2026-09-27)
# io 는 검사기·시험이 모두 불러오므로, 여기 한 줄이면 전부에 닿습니다.
# 까닭은 engine/tmp.py 맨 위에 적어 두었습니다 — C: 가 꽉 차 판정이 멈췄습니다.
try:
    from . import tmp as _tmp          # noqa: F401
except ImportError:                    # 홑파일로 부를 때
    import tmp as _tmp                 # noqa: F401

# ── 확장자별 규칙 ───────────────────────────────────────────────
# BOM 이 있어야 하는 것 — PowerShell 은 BOM 이 없으면 한글이 깨집니다
_NEEDS_BOM = ('.ps1',)

# BOM 이 있으면 안 되는 것 — 하나라도 있으면 사이트가 죽거나 배포가 멈춥니다
_NO_BOM = ('.htaccess', '.yml', '.yaml', '.json', '.txt', '.html', '.css',
           '.js', '.xml', '.md', '.py', '.csv')

# 줄바꿈 — 웹에 올라가는 것은 전부 \n 으로 통일합니다
_CRLF = ()     # 지금은 없음. 필요해지면 여기 적습니다

# 제어문자 — 줄바꿈과 탭만 허용합니다
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')

BOM = '﻿'


class 파일오류(Exception):
    """쓰기를 멈춰야 하는 상황. 조용히 넘어가지 않습니다."""


def _ext(path):
    b = os.path.basename(path)
    if b.startswith('.'):          # .htaccess 처럼 점으로 시작하는 것
        return b
    return os.path.splitext(b)[1].lower()


def _check(path, text):
    """쓰기 전 검사. 걸리면 쓰지 않고 멈춥니다. (계약-13)"""
    m = _CTRL.search(text)
    if m:
        n = text.count('\n', 0, m.start()) + 1
        raise 파일오류(
            '%s 의 %d번째 줄에 보이지 않는 제어문자(\\x%02x)가 있습니다.\n'
            '  지난번에 이것 때문에 배포가 하루 멈췄습니다 (계약-13).\n'
            '  sed 의 역참조 \\1 을 쓰려다 진짜 제어문자가 들어간 적이 있습니다.'
            % (path, n, ord(m.group()))
        )


def write(path, text, *, mkdir=True):
    """파일을 씁니다. **모든 쓰기는 이 함수를 지납니다.** (계약-13)

    확장자를 보고 BOM·줄바꿈을 정하고, 제어문자를 검사합니다.
    """
    if not isinstance(text, str):
        raise 파일오류('%s — 글자가 아닌 것을 쓰려 합니다 (%s)' % (path, type(text).__name__))

    _check(path, text)

    ext = _ext(path)
    text = text.replace('\r\n', '\n').replace('\r', '\n')   # 줄바꿈 통일
    if ext in _CRLF:
        text = text.replace('\n', '\r\n')

    text = text.lstrip(BOM)                                  # 이미 붙은 BOM 은 떼고
    if ext in _NEEDS_BOM:
        text = BOM + text                                    # 필요한 것만 다시 붙임

    if mkdir:
        d = os.path.dirname(os.path.abspath(path))
        if d and not os.path.isdir(d):
            os.makedirs(d)

    with _io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
    return len(text)


# 「기본값을 안 줬다」와 「기본값이 None 이다」를 가려야 합니다.
# default=None 으로 두면 둘이 같아져, 없는 파일에서 None 을 받고 싶어도
# 그대로 예외가 납니다 (2026-09-26에 걸렸습니다)
_없음 = object()


def read(path, *, default=_없음):
    """파일을 읽습니다. BOM 은 떼고 줄바꿈은 \\n 으로 맞춰 돌려줍니다."""
    try:
        with _io.open(path, encoding='utf-8-sig', newline='') as f:
            return f.read().replace('\r\n', '\n').replace('\r', '\n')
    except OSError:
        if default is not _없음:
            return default
        raise


def read_json(path, *, default=_없음):
    try:
        return json.loads(read(path))
    except (OSError, ValueError):
        if default is not _없음:
            return default
        raise


# ── 필수 파일은 **없음과 빈 것을 가려** 읽습니다 ─────────────
#
# ★ 왜 (2026-09-28 바깥 검수 9차 숙제 2)
#
#   검사기가 이렇게 읽고 있었습니다.
#
#       사이트맵 = io.read(os.path.join(NEW, 'sitemap.xml'), default='')
#
#   그러면 이 둘이 **똑같아집니다.**
#
#       파일이 아예 없음            → ''
#       파일은 있는데 0바이트        → ''
#
#   실제로 sitemap.xml 이 통째로 없었는데 `<loc>` 이 하나도 없으니
#   「사이트맵이 가리키는 쪽이 모두 있습니다」로 넘어갔습니다.
#   **없는 것을 「다 맞다」고 세는 검사**였습니다.
#
#   바깥 검수의 말: 「모름 → PASS가 아님. 파일 없음 → PASS가 아님.」
#   그래서 필수 파일은 상태를 네 갈래로 나눠 읽습니다.
#
#       MISSING   파일이 없습니다
#       EMPTY     파일은 있으나 0바이트입니다
#       INVALID   있으나 모양이 틀립니다 (json 이 안 풀리는 등)
#       VALID     괜찮습니다
#
#   ※ 「없어도 되는 것」에는 쓰지 마세요. default= 를 그대로 쓰십시오.
#     이것은 **반드시 있어야 하는 것**을 읽는 길입니다.

MISSING, EMPTY, INVALID, VALID = 'MISSING', 'EMPTY', 'INVALID', 'VALID'


def 파일상태(path, *, json도볼까=False, 가장작게=1):
    """(상태, 글, 한마디) 를 돌려줍니다. **예외를 던지지 않습니다.**

    가장작게 — 이보다 작으면 EMPTY 로 봅니다. robots.txt 가 한 글자만
               남아도 「있다」고 하면 안 되기 때문입니다.
    """
    if not os.path.exists(path):
        return MISSING, None, '파일이 없습니다'
    try:
        크기 = os.path.getsize(path)
    except OSError as e:
        return INVALID, None, '크기를 못 읽었습니다: %s' % str(e)[:40]
    if 크기 < 가장작게:
        return EMPTY, None, '%d바이트입니다' % 크기
    try:
        글 = read(path)
    except OSError as e:
        return INVALID, None, '못 읽었습니다: %s' % str(e)[:40]
    if not 글.strip():
        return EMPTY, 글, '속이 비었습니다 (%d바이트)' % 크기
    if json도볼까:
        try:
            json.loads(글)
        except ValueError as e:
            return INVALID, 글, 'json 이 안 풀립니다: %s' % str(e)[:40]
    return VALID, 글, '%d바이트' % 크기


def 꼭있어야함(path, *, json도볼까=False, 가장작게=1):
    """없거나 비었으면 **그 자리에서 멈춥니다.** 빈 것으로 바꿔 읽지 않습니다."""
    상태, 글, 말 = 파일상태(path, json도볼까=json도볼까, 가장작게=가장작게)
    if 상태 != VALID:
        raise 없거나틀림('%s — %s (%s)' % (path, 상태, 말))
    return 글


def 꼭읽기(path, *, 가장작게=1):
    """꼭 있어야 하는 **글** 파일. 없거나 비면 멈춥니다."""
    return 꼭있어야함(path, 가장작게=가장작게)


def 꼭읽기json(path):
    """꼭 있어야 하는 **자료** 파일. 없거나 비거나 안 풀리면 멈춥니다.

    ★ keep.json · url-map.json 을 `default={}` 로 읽던 자리를
      이것으로 바꿨습니다 (2026-09-28 바깥 검수 9차).

      없으면 빈 사전이 되고, 빈 사전이면 「남길 것이 하나도 없다」가
      됩니다. 그러면 검사기는 **조용히 틀린 답**을 냅니다 —
      「옛 쪽을 다 지워도 괜찮다」고 하는 셈입니다.

      자료가 없으면 **검사기는 멈춰야 합니다.** 판정이 그것을
      ERROR 로 읽습니다. 모르면서 괜찮다고 하지 않습니다.
    """
    return json.loads(꼭있어야함(path, json도볼까=True))


class 없거나틀림(Exception):
    """꼭 있어야 할 파일이 없거나, 비었거나, 모양이 틀립니다."""


def write_json(path, obj):
    """자료를 씁니다.

    ensure_ascii=False — 한글을 \\uXXXX 로 바꾸지 않습니다. 사람이 읽어야 합니다
    sort_keys=True     — 열쇠 차례를 고정합니다. 안 그러면 돌릴 때마다
                         파일이 바뀌어 보입니다 (계약-07)
    """
    return write(path, json.dumps(obj, ensure_ascii=False, indent=2,
                                  sort_keys=True) + '\n')


def write_binary(path, 내용, *, mkdir=True):
    """인터넷에서 받아 온 그림처럼 **바이트를 그대로** 씁니다.

    ★ 2026-09-29 — 계약-13 이 제 실수를 잡았습니다.
      명소 사진을 받는 도구에서 `open(갈곳,'wb')` 를 직접 썼습니다.
      **파일 쓰기는 이 파일만 한다**는 계약을 제가 어긴 것입니다.

      copy_binary() 는 있는 파일을 옮기는 것이고, 이것은
      메모리에 있는 바이트를 쓰는 것이라 따로 둡니다.

    같은 내용이면 손대지 않습니다 (계약-07 — 다시 만들어도 같아야).
    """
    if os.path.exists(path):
        with _io.open(path, 'rb') as f:
            if f.read() == 내용:
                return False
    if mkdir:
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
    with _io.open(path, 'wb') as f:
        f.write(내용)
    return True


def copy_binary(src, dst, *, mkdir=True):
    """그림·아이콘처럼 글이 아닌 파일을 **그대로** 옮깁니다.

    write() 는 글을 다루므로 줄바꿈을 손보고 BOM 을 따집니다.
    그림에 그 짓을 하면 파일이 깨집니다. 그래서 따로 둡니다.

    파일 쓰기는 이 파일만 한다는 규칙(계약-02)은 그대로입니다 —
    다른 곳에서 shutil.copy 를 부르지 않고 이것을 부릅니다.

    같은 내용이면 손대지 않습니다. 돌릴 때마다 시각이 바뀌어
    「고쳐졌다」고 보이면 재현성 검사가 헛돕니다 (계약-07).
    """
    with _io.open(src, 'rb') as f:
        내용 = f.read()
    if os.path.exists(dst):
        with _io.open(dst, 'rb') as f:
            if f.read() == 내용:
                return False
    if mkdir:
        d = os.path.dirname(dst)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
    with _io.open(dst, 'wb') as f:
        f.write(내용)
    return True


# 글자 파일 — 줄바꿈을 맞춰 셈합니다
_글자확장자 = ('.css', '.js', '.mjs', '.json', '.html', '.xml',
               '.txt', '.svg', '.md', '.yml', '.yaml')


def sha(path_or_text):
    """내용의 지문. 재현성 검사와 자산 해시에 씁니다. (계약-07)

    ★ **글자 파일은 줄바꿈을 맞춘 뒤 셉니다** (2026-10-09 새벽)
      `write()` 는 쓸 때 줄바꿈을 LF 로 통일합니다. 그런데 여기서는
      원본(CRLF)을 그대로 세어, 쪽에 박히는 판번호가 서버에 올라간
      파일과 **영영 안 맞았습니다.**

          assets/css/site.css        CRLF 5,080개 → 43dae407
          site/assets/css/site.css   CRLF 0개     → 33b70078

      `check_deployed --net` 이 「449쪽 모두 내용이 다릅니다」라고
      했는데 실제로 다른 것은 **차림표 판번호 한 줄**뿐이었습니다.
      사진·글꼴 같은 바이너리는 그대로 셉니다.
    """
    if os.path.exists(path_or_text):
        with _io.open(path_or_text, 'rb') as f:
            덩이 = f.read()
        if os.path.splitext(path_or_text)[1].lower() in _글자확장자:
            덩이 = 덩이.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        return hashlib.sha256(덩이).hexdigest()
    return hashlib.sha256(path_or_text.encode('utf-8')).hexdigest()


def scan(root='site'):
    """만들어진 파일에 제어문자·BOM 이 없는지 확인합니다. (계약-13)

    write() 를 거치면 생길 수 없지만, 누군가 직접 쓴 파일이 섞일 수 있습니다.
    배포 전 마지막 확인입니다.
    """
    bad = []
    for base, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(base, name)
            ext = _ext(p)
            try:
                with _io.open(p, encoding='utf-8', newline='') as f:
                    s = f.read()
            except (OSError, UnicodeDecodeError):
                continue                      # 그림 같은 것은 건너뜁니다
            if _CTRL.search(s):
                bad.append((p, '제어문자'))
            if s.startswith(BOM) and ext in _NO_BOM:
                bad.append((p, 'BOM'))
            if ext in _NEEDS_BOM and not s.startswith(BOM):
                bad.append((p, 'BOM 이 있어야 하는데 없음'))
    return bad


def 쪽들(뿌리='site', *, 상대로=False):
    """**사이트의 쪽을 모으는 한 곳입니다.** (2026-10-06)

    ★ 왜 만들었나 — 같은 일에 **세 번** 당했습니다

      `check_mobile` 은 쪽을 잴 때 가짜 물때를 심은 사본을
      **그 쪽과 같은 폴더에** 잠깐 만듭니다 (`__재기임시.html`).
      차림표·그림이 상대 경로라 딴 데 두면 차림표 없는 쪽을
      재게 되어, 자리를 옮길 수가 없습니다.

      평소에는 `finally` 로 지웁니다. 그런데 **검사기가 밖에서
      죽으면**(시간 초과로 판정이 끊으면) `finally` 도 안 돕니다.
      그 찌꺼기가 남으면 다른 검사기들이 그것을 **진짜 쪽으로**
      세어 헛 FAIL 을 냅니다.

          2026-10-06 ①  7 아이콘 전수 · 17 미작성 쪽 고아 링크
          2026-10-06 ②  `check_assets`
          2026-10-06 ③  `check_seo` — 제목·설명·canonical 넷

      그때마다 그 검사기에 건너뛰기를 **한 줄씩** 넣었습니다.
      일곱 곳에 같은 줄이 생겼고 그래도 또 샜습니다. 쪽을 모으는
      자리가 여섯 군데로 흩어져 있으니 당연한 일입니다.

      **모으는 곳을 하나로 둡니다.** 여기만 지키면 다 지켜집니다.

    ★ 무엇을 빼나
      `__` 로 시작하는 **파일이든 폴더든** 뺍니다. 검사기가 재는
      동안 만드는 자국입니다. 사이트의 진짜 쪽은 이 꼴로 짓지
      않습니다 (`__probe__/` 는 판 지문이라 html 이 아닙니다).

      폴더까지 보는 것은 `check_golden` 에서 배웠습니다 —
      거기만 경로의 **어느 조각이든** 보고 있었습니다.
      가장 꼼꼼한 쪽에 맞춥니다.
    """
    모음 = []
    for base, _dirs, files in os.walk(뿌리):
        상대밭 = os.path.relpath(base, 뿌리).replace(os.sep, '/')
        if any(조각.startswith('__') for 조각 in 상대밭.split('/')):
            continue              # 자국 폴더 안은 통째로 건너뜁니다
        for name in files:
            if not name.endswith('.html'):
                continue
            if name.startswith('__'):
                continue          # 재는 동안 스쳐 간 자국입니다
            p = os.path.join(base, name)
            모음.append(os.path.relpath(p, 뿌리).replace(os.sep, '/')
                       if 상대로 else p)
    return sorted(모음)
