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
