# -*- coding: utf-8 -*-
"""틀(템플릿) 엔진 — 아주 작습니다. 바깥 것에 기대지 않습니다.

왜 직접 만드나
    바깥 라이브러리(jinja2 등)를 쓰면 설치가 어긋날 때 배포가 멈춥니다.
    이 사이트가 쓰는 것은 「값 끼우기」와 「되풀이」뿐입니다. 표준 파이썬
    만으로 충분하고, 그만큼 고장날 곳이 적습니다.

문법 — 셋뿐입니다

    {{키}}        값을 넣습니다. **HTML 로 안전하게 바꿔서** 넣습니다
    {{{키}}}      이미 HTML 인 것을 그대로 넣습니다 (조심)
    {{#조각}}     다른 틀 파일을 여기에 넣습니다

    되풀이는 틀에 두지 않습니다. 파이썬에서 조각을 만들어 {{{ }}} 로 넣습니다.
    틀에 논리를 넣기 시작하면 다시 읽기 어려워집니다.

★ 없는 키는 조용히 넘어가지 않고 **실패합니다**
    옛 사이트는 값이 없으면 빈칸이 되어, 광고가 15곳에서 빠진 것을
    한 달 넘게 몰랐습니다. 빈칸보다 실패가 낫습니다.

★ 안 쓴 값도 알립니다
    자료를 넣었는데 틀에 자리가 없으면, 그 자료는 화면에 안 나옵니다.
"""
import os
import re
import html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
틀자리 = os.environ.get('BADAGAJA_TEMPLATE', os.path.join(ROOT, 'template'))

_조각 = re.compile(r'\{\{#([\w\-./]+)\}\}')
_그대로 = re.compile(r'\{\{\{\s*([\w\-.]+)\s*\}\}\}')
_안전 = re.compile(r'\{\{\s*([\w\-.]+)\s*\}\}')

_읽은것 = {}


class 틀오류(Exception):
    pass


def 읽기(이름):
    """틀 파일 하나. 한 번 읽으면 기억해 둡니다"""
    if 이름 in _읽은것:
        return _읽은것[이름]
    길 = os.path.join(틀자리, 이름)
    if not os.path.exists(길):
        raise 틀오류('틀을 찾지 못했습니다: %s' % 길)
    with open(길, encoding='utf-8') as f:
        s = f.read()
    _읽은것[이름] = s
    return s


def 비우기():
    """틀을 고친 뒤 다시 읽게 합니다 (시험이 씁니다)"""
    _읽은것.clear()


def _찾기(값들, 키):
    """'권역.이름' 처럼 점으로 파고듭니다"""
    지금 = 값들
    for 조각 in 키.split('.'):
        if isinstance(지금, dict) and 조각 in 지금:
            지금 = 지금[조각]
        else:
            raise 틀오류('틀이 찾는 값이 없습니다: {{%s}}' % 키)
    return 지금


def _글자(v):
    if v is None:
        return ''
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    return str(v)


# ── 그래프 차림표를 **저절로** 붙입니다 ─────────────────────
#
#   ★ 2026-10-02 주인이 화면으로 잡아 주셨습니다
#     간·만조 점이 검은 동그라미였습니다. `tidegraph.css` 가
#     안 실린 쪽이 **10쪽** 있었습니다(첫 쪽·묶음 쪽 아홉).
#
#   까닭은 **쪽마다 손으로 적는 짜임**이었습니다. 쪽을 새로 지을
#   때마다 또 빠집니다. 그래서 **여기 한 곳에서** 봅니다
#   (주인 규칙 26 — 쪽이 아니라 엔진을 고칩니다).
# ★ **글자가 아니라 실제 쓰임을 봅니다** (2026-10-02 바깥 검수)
#   처음에는 `tidegraph\.css` 라는 **글자만** 찾았습니다. 그러면
#   주석이나 스크립트 안에 그 이름이 있어도 「실렸다」고 넘어갑니다.
#   「문구만 있고 기능은 없는」 것을 잡으려는 코드가 **또** 그 덫에
#   걸린 셈입니다 — 오늘 세 번째입니다.
#   따옴표·공백·대소문자에도 흔들리지 않게 합니다.
_그래프칸 = re.compile(r'\bid\s*=\s*["\']tideGraph["\']', re.I)
_그래프css = re.compile(
    r'<link\b[^>]*\bhref\s*=\s*["\'][^"\']*tidegraph\.css'
    r'(?:\?[^"\']*)?["\'][^>]*>', re.I)


def _그래프차림표끼우기(s):
    """그래프 칸이 있는데 차림표가 없으면 머리에 끼웁니다."""
    if not _그래프칸.search(s) or _그래프css.search(s):
        return s
    # 이미 실린 다른 차림표 **바로 뒤**에 둡니다 — 뒤에 와야
    # 그래프 규칙이 바탕 규칙을 덮습니다
    m = None
    for m in re.finditer(
            r'<link\b[^>]*\bhref\s*=\s*["\'][^"\']*site\.css'
            r'(?:\?[^"\']*)?["\'][^>]*>', s, re.I):
        pass
    if not m:
        m = re.search(r'</title>', s)
        if not m:
            return s
    # ★ **판번호를 붙입니다** — 없으면 브라우저가 옛 차림표를 씁니다
    #   (파일 내용으로 셉니다. build 가 쓰는 것과 같은 셈법)
    뿌리 = _차림표뿌리(s)
    끼울것 = ('<link rel="stylesheet" href="%stidegraph.css%s">'
              % (뿌리, _그래프css판번호()))
    return s[:m.end()] + 끼울것 + s[m.end():]


_그래프css판 = None


def _그래프css판번호():
    """tidegraph.css 의 판번호. 한 번만 셉니다."""
    global _그래프css판
    if _그래프css판 is None:
        길2 = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), 'assets', 'css', 'tidegraph.css')
        try:
            import hashlib
            with open(길2, 'rb') as f:
                # ★ build.판번호() 와 **같은 셈법**이어야 합니다
                #   (sha1 8자리). 다르면 같은 파일에 판번호가
                #   두 갈래로 생겨 브라우저가 두 번 받습니다.
                _그래프css판 = '?v=' + hashlib.sha1(f.read()).hexdigest()[:8]
        except Exception:
            _그래프css판 = ''
    return _그래프css판


def _차림표뿌리(s):
    """이미 실린 site.css 주소에서 폴더 부분만 떼어 냅니다."""
    m = re.search(r'href\s*=\s*["\']([^"\']*?)assets/css/site\.css',
                  s, re.I)
    if m:
        return m.group(1) + 'assets/css/'
    return 'assets/css/'


# 칸 **통째로** 비었을 때 — 그 칸을 지웁니다
_빈안내칸 = re.compile(
    r'<section class="section section--tail"><div class="wrap">\s*'
    r'<p class="notice">\s*</p>\s*'
    r'</div></section>')
# 광고 칸처럼 **다른 것이 함께 있을 때** — 빈 글만 지웁니다.
#   광고 자리는 남겨야 합니다. 광고가 뜨면 거기 들어갑니다.
_빈안내글 = re.compile(r'\s*<p class="notice">\s*</p>')

# 속이 빈 구조화 자료 — 틀이 늘 넣는데 값이 없으면 껍데기만
# 남습니다. 검색엔진에 「자료가 있다」고 해 놓고 안 주는 꼴입니다.
_빈구조화 = re.compile(
    r'\s*<script type="application/ld\+json"[^>]*>\s*</script>')


def _빈칸지우기(s):
    """**글이 하나도 없는 칸을 지웁니다.**

    ★ 2026-10-08 밤 주인 지시 — 「전체적으로 시각적으로 오류가 있는지
      찾아봐. 디자인 오류 …」. 전수로 재니 권역 묶음 쪽 등에서
      `<p class="notice"></p>` 만 든 칸이 **글 없는 76~84px 공백**으로
      남아 있었습니다. 손님에게는 까닭 없는 빈자리입니다.

    ★ 왜 **여기** 인가 — 이 자리는 틀 11곳이 모두 거쳐 가는 길목입니다.
      틀마다 고치면 열두 번째 틀을 만들 때 빠뜨립니다 (규칙 26).
    """
    s = _빈안내칸.sub('', s)
    s = _빈안내글.sub('', s)
    return _빈구조화.sub('', s)


def 머리문의단추(메일):
    """머리띠 오른쪽 메일 단추. 메일이 비면 아무것도 안 냅니다."""
    메일 = (메일 or '').strip()
    if not 메일:
        return ''
    것 = html.escape(메일, quote=True)
    return ('<a href="mailto:%s" class="badge"><svg class="bi"'
            ' viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5.5"'
            ' width="18" height="13" rx="2.5"/><path d="m3.8 7 8.2 6 8.2-6"/>'
            '</svg> %s</a>' % (것, 것))


def 그리기(이름, 값들, *, 안쓴값알림=True):
    """틀 하나를 값으로 채웁니다.

    이름  — template/ 안의 파일 이름 (보기: 'point-list.html')
    값들  — 채울 값. 점으로 파고들 수 있습니다 ({'권역': {'이름': '태안'}})
    """
    # ★ **모든 쪽에 지금 판을 새깁니다** (2026-10-07 주인 지시)
    #   호출부마다 넣으면 또 빠뜨립니다 — 여기 한 곳에서 채웁니다.
    _짧, _날 = 지금판()
    if isinstance(값들, dict):
        값들 = dict(값들)
        # ★ **머리띠 문의 단추** — 기본은 메일, 쪽이 '' 를 주면 안 냅니다
        #   (2026-10-09 지피티 결정 — 동호회 지원 쪽에서만 숨깁니다.
        #    CSS 로 가리지 않고 아예 내보내지 않습니다)
        값들.setdefault('머리문의', 머리문의단추(값들.get('메일', '')))
        값들.setdefault('판이름', _짧)
        값들.setdefault('판날짜', _날)
        값들.setdefault('판날짜보기', _날.replace('-', '.') if _날 else '')

    s = 읽기(이름)

    # 1) 조각을 먼저 넣습니다 (조각 안에 또 조각이 있어도 됩니다)
    본 = 0
    while _조각.search(s):
        본 += 1
        if 본 > 10:
            raise 틀오류('조각이 서로를 끝없이 부릅니다: %s' % 이름)
        s = _조각.sub(lambda m: 읽기(m.group(1)), s)

    쓴키 = set()

    def 그대로바꾸기(m):
        쓴키.add(m.group(1))
        return _글자(_찾기(값들, m.group(1)))

    def 안전바꾸기(m):
        쓴키.add(m.group(1))
        return html.escape(_글자(_찾기(값들, m.group(1))), quote=True)

    s = _그대로.sub(그대로바꾸기, s)
    s = _안전.sub(안전바꾸기, s)

    # 2) 남은 자리가 있으면 실패 — 빈칸으로 두지 않습니다
    남음 = re.findall(r'\{\{[^}]*\}\}', s)
    if 남음:
        raise 틀오류('틀 %s 에 못 채운 자리가 있습니다: %s'
                     % (이름, ' · '.join(남음[:3])))

    # 3) 안 쓴 값 알림 — 자료를 넣었는데 화면에 안 나오는 것을 잡습니다
    if 안쓴값알림:
        윗키 = set(값들) - set(k.split('.')[0] for k in 쓴키)
        윗키 = set(k for k in 윗키 if not k.startswith('_'))
        if 윗키:
            그리기.안쓴값 = sorted(윗키)
        else:
            그리기.안쓴값 = []
    # ★ 그래프 칸이 있으면 **차림표가 저절로** 따라옵니다
    s = _그래프차림표끼우기(s)
    # ★ **빈 칸을 지웁니다** (2026-10-08 밤 주인 지시 — 시각 점검)
    s = _빈칸지우기(s)
    return s


그리기.안쓴값 = []


def 숫자검사(이름):
    """틀에 세 자리 이상 숫자가 박혀 있으면 알립니다 (계약-04)

    「포인트 110곳」처럼 틀에 숫자를 쓰면 자료가 늘 때마다 틀립니다.
    색(#2B2116)·크기(1120px)·해(2026) 는 숫자가 아니라 디자인이므로 뺍니다.
    """
    s = 읽기(이름)
    # ★ **주석은 봅니다만, 나무라지 않습니다** (2026-09-28)
    #   주석에 「옛 쪽에 6 / 306 / 48 / 19 가 있었습니다」라고
    #   까닭을 적었더니 계약-04 가 306 을 잡았습니다.
    #   계약의 뜻은 「쪽에 나오는 숫자를 틀에 박지 말라」입니다.
    #   주석은 손님에게 안 보이고, 왜 그렇게 했는지를 남기는 자리입니다.
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<link[^>]*fonts\.googleapis[^>]*>', ' ', s)   # 글꼴 굵기(300~900)
    s = re.sub(r'#[0-9A-Fa-f]{3,8}\b', ' ', s)            # 색
    s = re.sub(r'\d+(?:px|rem|em|%|ms|s|vh|vw)\b', ' ', s)  # 크기
    s = re.sub(r'\b(?:19|20)\d\d\b', ' ', s)               # 해
    s = re.sub(r'viewBox="[^"]*"', ' ', s)                 # 그림 좌표
    s = re.sub(r'\bd="[^"]*"', ' ', s)
    return sorted(set(re.findall(r'\b\d{3,}\b', s)))


# ── 지금 판을 밝히는 지문 ────────────────────────────────
#   ★ 2026-10-07 주인 지시 — 「누가 보든 **새 판**을 보고 판단해야 한다」
#     보는 사람이 「기준일 26년 9월」 같은 엉뚱한 단서로 최신 여부를
#     짐작하지 않도록, **쪽 자신이 자기 판을 밝힙니다.**
#   ★ 멱등(계약-07) — 「오늘 날짜」가 아니라 **커밋 날짜**를 씁니다.
#     같은 커밋이면 몇 번을 다시 만들어도 같은 값입니다.
_판 = None


def 지금판():
    """(커밋 짧은이름, 커밋 날짜) — git 에서 읽습니다. 못 읽으면 빈 값."""
    global _판
    if _판 is not None:
        return _판
    import subprocess
    뿌 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%h\t%cs'],
                           cwd=뿌, capture_output=True, text=True,
                           encoding='utf-8', timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            조각 = r.stdout.strip().split('\t')
            _판 = (조각[0], 조각[1] if len(조각) > 1 else '')
            return _판
    except (OSError, subprocess.SubprocessError):
        pass
    _판 = ('', '')
    return _판
