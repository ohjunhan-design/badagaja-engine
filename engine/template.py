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


def 그리기(이름, 값들, *, 안쓴값알림=True):
    """틀 하나를 값으로 채웁니다.

    이름  — template/ 안의 파일 이름 (보기: 'point-list.html')
    값들  — 채울 값. 점으로 파고들 수 있습니다 ({'권역': {'이름': '태안'}})
    """
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
