# -*- coding: utf-8 -*-
"""**물때표 보는 법** — muldae.html (2026-10-01).

★ `tide/` 와 역할이 다릅니다 (바깥 검수 기준: 왜 이 주소가 있는가)
      tide/    **오늘 물때가 몇 시인가** — 보고 바로 나가는 쪽
      muldae   **물때표를 어떻게 읽는가** — 한 번 배우는 쪽
  합치면 둘 다 나빠집니다. 나가기 직전에 긴 설명을 읽고 싶은
  사람은 없고, 처음 배우는 사람에게 숫자만 보여 주면 못 읽습니다.

★ 글과 그림은 옛 쪽 그대로입니다
  아홉 절·그림 7장. `engine/import_muldae.py` 가
  `data/raw/muldae.json` 으로 옮겨 두었습니다.

★ 차례를 맨 위에 둡니다
  아홉 절이라 깁니다. 「해루질은 언제 나가나」만 보려는 사람이
  스크롤로 찾게 두면 안 됩니다.
"""
import os
import re

from engine import io as _io
from engine import url
from engine import template
from engine.hubs import esc, 칸, _바탕값

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _굵게(글):
    """`**…**` 를 굵게. **별표가 글자로 보이면 안 됩니다.**"""
    쪽 = esc(글 or '').split('**')
    return ''.join(('<b>%s</b>' % x) if i % 2 else x
                   for i, x in enumerate(쪽))


def _자료():
    것 = _io.read_json(os.path.join(여기, 'data', 'raw', 'muldae.json'),
                       default={})
    return 것 if 것.get('절') else None


def 물때보는법쪽(d, 언어='ko'):
    것 = _자료()
    if not 것:
        return None
    쪽길 = url.muldae(언어)

    # ── 차례 — **작게, 세 줄로** (2026-10-01 바깥 검수 지시)
    #
    #   처음에는 세로 카드 아홉 개로 두었습니다. 390px 에서
    #   **첫 화면을 통째로 먹어** 본문이 한 줄도 안 보였습니다.
    #   가로 칩으로 바꿨더니 나아졌지만 아직 세 줄을 넘었습니다.
    #
    #   바깥 검수 —
    #     「가로 스크롤 칩 9개로 바꾸는 것도 권하지 않습니다. 화면
    #       밖에 숨어서 목차를 발견하는 문제를 다른 형태로 옮기는
    #       것뿐입니다. **3×3 작은 텍스트 목차** 정도만 두세요.
    #       높이를 지금의 약 1/3 로 줄이고 바로 「1. 물때란」이
    #       보이게 하세요. **네 장 중 오늘 밤 하나만 고친다면
    #       바로 이것입니다.**」
    #
    #   제목이 길어서(「하루 두 번, 날마다 약 50분씩 늦게」) 그대로
    #   쓰면 3×3 이 안 됩니다. 자료에 **짧은 이름**을 따로 적었습니다.
    차례 = ('<nav class="toc-mini" aria-label="이 쪽 차례">%s</nav>'
            % ''.join(
                '<a href="#%s"><i>%d</i>%s</a>'
                % (esc(x['id']), i,
                   esc(x.get('짧은제목') or x['제목']))
                for i, x in enumerate(것['절'], 1)))

    칸들 = [칸('무엇부터 보나', '이 쪽 차례', 차례, 흰=False)]

    for i, 절 in enumerate(것['절']):
        속 = []
        for 글 in 절['글']:
            속.append('<p class="long">%s</p>' % _굵게(글))
        for 그 in 절['그림']:
            속.append(
                '<figure class="ls-fig">'
                '<svg viewBox="%s" role="img" aria-label="%s"'
                ' xmlns="http://www.w3.org/2000/svg">%s</svg></figure>'
                % (esc(그['보기칸']), esc(그['설명']), 그['속']))
        if 절['표']:
            # ★ 금어기 쪽이 쓰는 차림을 **그대로** 씁니다 (계약-01)
            #   없는 이름을 새로 지으면 조용히 꾸밈이 안 걸립니다.
            # ★ class 를 **합칩니다** (2026-10-01에 겪은 일)
            #   `<table` 뒤에 그냥 붙였더니
            #   `<table class="rl-table" class="mf-names">` 가 되었고,
            #   브라우저는 **두 번째 class 를 버립니다.** 옛 쪽이 쓰던
            #   `mf-names` 꾸밈이 통째로 날아갔습니다.
            표 = re.sub(r'<table class="([^"]*)"',
                        lambda m: '<table class="rl-table %s"' % m.group(1),
                        절['표'], count=1)
            if 'rl-table' not in 표:
                표 = 표.replace('<table', '<table class="rl-table"', 1)
            속.append('<div class="rl-tablewrap">%s</div>' % 표)
        칸들.append(
            '<section class="section section--%s" id="%s"><div class="wrap">'
            '<div class="section-head"><p class="kicker">%d</p>'
            '<h2 class="serif">%s</h2></div>%s</div></section>'
            % ('white' if i % 2 == 0 else 'soft', esc(절['id']),
               i + 1, esc(절['제목']), ''.join(속)))

    # ── 배웠으면 **어디로 가나**
    더 = [('오늘 물때 보기', url.tide_list(언어),
           '전국 관측소의 오늘 간조·만조 시각'),
          ('해루질 대상 고르기', url.guide_list('해루질', 언어),
           '물이 빠질 때 무엇을 찾나'),
          ('낚시 어종 고르기', url.guide_list('낚시', 언어),
           '물이 흐를 때 무엇을 노리나')]
    칸들.append(칸(
        '이제 어디로', '다음 차례',
        '<div class="grid">%s</div>'
        % ''.join(
            '<a class="card card--go" href="%s">'
            '<h3 class="card-name">%s</h3>'
            '<p class="card-body">%s</p></a>'
            % (esc(url.rel(쪽길, 주)), esc(이), esc(글))
            for 이, 주, 글 in 더), 흰=False))

    값 = _바탕값(
        d, 쪽길, 언어,
        제목='물때표 보는 법 — 사리·조금·들물·날물, 간조 시각 읽기 | %s'
             % d.사이트['이름']['ko'],
        짧은제목='물때표 보는 법',
        설명='사리와 조금, 들물과 날물, 간조 시각만 읽을 줄 알면 '
             '언제 가고 언제 나와야 할지 스스로 정할 수 있습니다.',
        머리말='물때 기초',
        큰제목=것['제목'],
        # ★ 소개글은 틀이 **글자 그대로** 내보냅니다 (esc)
        #   별표를 그냥 두면 「날씨보다 **물때**를」 처럼 보입니다.
        #   굵게가 필요한 자리가 아니므로 별표만 뗍니다.
        소개글=것['소개'].replace('**', '')[:160],
        한줄='%d가지로 나눠 봅니다 · 그림 %d장'
             % (len(것['절']), sum(len(x['그림']) for x in 것['절'])),
        갈래칸=''.join(칸들),
        꼬리안내='물때는 바다마다 다릅니다. 나가실 곳의 관측소 값을 '
                 '꼭 확인하세요.',
        이름표글='그림 %d장' % sum(len(x['그림']) for x in 것['절']),
        _og갈래='tide')
    # ★ 겉틀이 body 클래스로 쓰는 값 — 안 주면 틀이 멈춥니다
    값.setdefault('쪽갈래', '')
    return 쪽길, template.그리기('rig-parts.html', 값)
