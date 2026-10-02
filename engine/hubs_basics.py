# -*- coding: utf-8 -*-
"""**처음이신가요** — 왕초보 그림 강의 두 쪽 (2026-10-01).

      fish/basics.html   바다낚시, 처음이라면    권역 57쪽이 걸음
      catch/basics.html  해루질, 처음이라면      권역 57쪽이 걸음

★ 권역 쪽마다 있는 「처음이신가요」 칸이 여기로 보냅니다
  그런데 **새 사이트에 파일이 없어** 서버에 남은 옛 디자인
  쪽으로 떨어지고 있었습니다. 초보자가 **가장 먼저 누르는
  링크**입니다. 거기서 사이트가 둘로 갈라져 보였습니다.

★ 글과 그림은 **옛 쪽 그대로**입니다
  낚싯대 이름 · 릴 · 매듭 · 던지기 · 챔질 · 뜰채 · 쓰레기(7장),
  물때표 · 옷차림 · 안전 · 크기 · 해감(5장).
  `engine/import_basics.py` 가 `data/raw/lessons.json` 의
  「기초」 로 옮겨 두었습니다. 새로 쓰면 더 나빠집니다.

★ 이 쪽이 답해야 하는 질문
  「낚시 한 번도 안 해봤는데 뭘 사야 하고 어떻게 하나」
  그 답이 **그림으로** 있어야 합니다 (주인 규칙 6-1 —
  사람은 눈으로 봅니다).
"""
import os

from engine import art
from engine import url
from engine import template
from engine.hubs import esc, 말, 칸, _바탕값

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _굵게(글):
    """자료의 `**…**` 를 굵게. **별표가 글자로 보이면 안 됩니다.**"""
    쪽 = esc(글 or '').split('**')
    나옴 = []
    for i, x in enumerate(쪽):
        나옴.append(('<b>%s</b>' % x) if i % 2 else x)
    return ''.join(나옴)


def _강의칸(것):
    """그림 카드들 — 어종 쪽이 쓰는 `.ls-grid` 차림 그대로."""
    칸들 = []
    for i, 단 in enumerate(것['단계'], 1):
        칸들.append(
            '<figure class="ls-card">\n'
            '<svg viewBox="0 0 320 220" role="img" aria-label="%s 그림"'
            ' xmlns="http://www.w3.org/2000/svg">\n%s\n</svg>\n'
            '<figcaption><b><i class="ls-no">%d</i>%s</b>'
            '<span>%s</span></figcaption>\n</figure>'
            % (esc(단.get('제목')), 단.get('그림') or '', i,
               esc(단.get('제목')), _굵게(단.get('글'))))
    # ★ 네 장이면 두 줄로 — 어종 쪽과 같은 규칙입니다
    모양 = 'ls-grid ls-grid--2' if len(칸들) == 4 else 'ls-grid'
    # ★ 꼬리말을 **여기서 또 쓰지 않습니다** (2026-10-01)
    #   칸 제목 위에 이미 「왕초보 그림 강의 · 그림 7장」이 있습니다.
    #   390px 로 보니 같은 말이 위아래로 두 번 나왔습니다.
    return ('<div class="ls-head"><p class="ls-lede">%s</p></div>'
            '<div class="%s">%s</div>'
            % (_굵게(것.get('소개')), 모양, ''.join(칸들)))


def _기초자료(d, 갈래):
    from engine import io as _io
    길 = os.path.join(여기, 'data', 'raw', 'lessons.json')
    것 = (_io.read_json(길, default={}).get('기초') or {}).get(갈래)
    return 것 if (것 and 것.get('단계')) else None


def 기초쪽(d, 갈래, 언어='ko'):
    """`갈래` 는 '낚시' 또는 '해루질'."""
    것 = _기초자료(d, 갈래)
    if not 것:
        return None
    낚시 = (갈래 == '낚시')
    쪽길 = url.basics(갈래, 언어)

    칸들 = [칸(것['제목'], 것.get('꼬리말') or '그림 강의',
               _강의칸(것), 흰=False)]

    # ── 다음에 갈 곳 — **여기서 끝나면 안 됩니다**
    #   기초를 봤으면 「그래서 어디로 가나」가 바로 있어야 합니다.
    # ★ **이름은 사전입니다 — 꺼내서 넣습니다** (2026-10-02 바깥 검수)
    #   전에는 `esc(x.get('이름'))` 이었습니다. 자료의 이름은
    #   `{'ko': '백합', 'zh': None}` 꼴이라 **그 모양 그대로**
    #   손님 화면에 나갔습니다. 두 쪽 32군데였습니다.
    어종들 = d.안내(갈래) or []
    고를것 = []
    for x in 어종들[:8]:
        이 = 말(x.get('이름'), 언어) or x['id']
        고를것.append(
            '<a class="card card--go" href="%s">'
            '<h3 class="card-name">%s</h3>'
            '<p class="card-body">%s</p></a>'
            % (esc(url.rel(쪽길, url.guide(x['id'], 갈래, 언어))),
               esc(이),
               esc(말(x.get('한줄'), 언어) or ('%s 잡는 법' % 이))))
    if 고를것:
        칸들.append(칸(
            '무엇을 노리시나요', '다음 차례',
            '<p class="long">기초는 어느 %s나 같습니다. 이제 '
            '<b>노리는 것</b>을 고르면 그것만의 채비와 철, 자리를 '
            '볼 수 있습니다.</p><div class="grid">%s</div>'
            '<p class="pt-in"><a href="%s">%s 전체 보기 →</a></p>'
            % ('물고기' if 낚시 else '조개',
               ''.join(고를것),
               esc(url.rel(쪽길, url.guide_list(갈래, 언어))),
               esc('낚시 어종' if 낚시 else '해루질 대상'))))

    더볼것 = [
        ('오늘 물때 보기', url.tide_list(언어),
         '언제 나가야 하는지부터 정합니다'),
        ('금어기와 크기 제한', url.rule(언어),
         '잡아도 되는 것인지 먼저 봅니다'),
        ('무엇을 챙겨 가나', url.gear(언어),
         '장화·장갑·구명조끼부터'),
    ]
    칸들.append(칸(
        '나가기 전에', '함께 보기',
        '<div class="grid">%s</div>'
        % ''.join(
            '<a class="card card--go" href="%s">'
            '<h3 class="card-name">%s</h3>'
            '<p class="card-body">%s</p></a>'
            % (esc(url.rel(쪽길, 주)), esc(이), esc(글))
            for 이, 주, 글 in 더볼것),
        흰=False))

    무엇 = '바다낚시' if 낚시 else '해루질'
    값 = _바탕값(
        d, 쪽길, 언어,
        제목='%s 처음이라면 — 그림 %d장으로 배우는 기초 | %s'
             % (무엇, len(것['단계']), d.사이트['이름']['ko']),
        짧은제목='%s 처음이라면' % 무엇,
        설명=('낚싯대 이름부터 매듭·던지기·챔질까지, 어떤 물고기를 '
              '노리든 똑같은 기초만 그림 %d장에 모았습니다.'
              if 낚시 else
              '물때 보는 법부터 옷차림·안전·해감까지, 무엇을 잡든 '
              '똑같은 기초만 그림 %d장에 모았습니다.')
             % len(것['단계']),
        머리말='%s 기초' % 무엇,
        큰제목='왕초보 %s 기초' % 무엇,
        소개글=('어종마다 채비는 달라도 낚싯대 다루는 법은 모두 '
               '같습니다.' if 낚시 else
               '무엇을 잡든 물때와 안전이 먼저입니다.'),
        한줄='그림 %d장 · 번호 순서대로' % len(것['단계']),
        갈래칸=''.join(칸들),
        꼬리안내=('처음에는 못 잡는 것이 당연합니다. 자리와 물때를 '
                 '익히는 것이 먼저입니다.' if 낚시 else
                 '갯벌은 물이 빨리 들어옵니다. 물때표를 먼저 '
                 '보고 움직이세요.'),
        이름표글='그림 %d장' % len(것['단계']),
        _og갈래=('fish' if 낚시 else 'catch'))
    return 쪽길, template.그리기('rig-parts.html', 값)
