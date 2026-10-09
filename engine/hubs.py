# -*- coding: utf-8 -*-
"""새 사이트에 **없던 네 쪽**을 짓습니다.

★ 2026-10-01 — 434쪽이 없는 곳을 가리키고 있었습니다

  새 사이트 쪽들이 아래 네 곳으로 링크를 겁니다.

      rule.html   494곳
      gear.html   492곳
      tide/       438곳
      guide/      434곳

  그런데 **새 사이트에 그 쪽이 없습니다.** 서버가 200 을 내는 것은
  **옛 사이트 파일이 남아 있어서**입니다. 손님이 새 디자인 쪽을
  보다가 「금어기」를 누르면 **옛 디자인으로 떨어집니다.**

  검사기는 「일부러 남긴 옛 쪽」으로 보고 통과시키고 있었습니다.
  서버가 200 을 낸다고 **내부 링크가 성하다고 보면 안 됩니다.**

★ 오늘 밤의 목표는 「다 채우는 것」이 아닙니다 (바깥 검수 의견)
  **「새 디자인과 옛 디자인의 끊김을 없애고, 손님이 갈 곳을 잃지
  않게 하는 것」** 입니다. 글을 길게 쓰지 않아도 됩니다.

★ gear 와 rig 는 다릅니다 — 링크를 rig 로 돌리지 않습니다
  gear 는 「무엇을 준비하나」, rig 는 「어떻게 묶나」입니다.
  492곳의 뜻을 한꺼번에 바꾸면 404 는 없어져도 **짜임이 틀어집니다.**
"""
import os

from engine import art
from engine import rules
from engine import template
from engine import url
from engine.korean import 조사      # noqa: E402

ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}


def 말(값, 언어='ko'):
    """그 언어의 값. 없으면 한국어로 떨어집니다.

    자료의 이름·한줄은 `{'ko': …, 'zh': …}` 꼴입니다. **꺼내 쓰지 않고
    그대로 넣으면 사전이 글자로 나갑니다** — 2026-10-02 에 두 쪽
    32군데가 그랬습니다.
    """
    if not isinstance(값, dict):
        return 값 or ''
    return 값.get(언어) or 값.get('ko') or ''


def esc(s):
    """화면에 낼 글자로 바꿉니다.

    ★ **사전·목록은 받지 않습니다** (2026-10-02 바깥 검수 13차)
      전에는 `str(s)` 로 무엇이든 받았습니다. 그래서 자료의
      `{'ko': '백합', 'zh': None}` 이 **그 모양 그대로** 손님에게
      나갔습니다. 오류도 안 났습니다 — 조용히 샜습니다.
      이제는 그 자리에서 **죽습니다.** 부르는 쪽에서 `말()` 로
      꺼내 넣으라는 뜻입니다.
    """
    if isinstance(s, (dict, list, tuple, set)):
        raise TypeError(
            'esc() 에 %s 가 들어왔습니다 — 말(값, 언어) 로 꺼내 주십시오: %r'
            % (type(s).__name__, s))
    s = '' if s is None else str(s)
    for a, b in ESC.items():
        s = s.replace(a, b)
    return s


def 칸(제목, 꼬리말, 속, 흰=True):
    """쪽 안 한 칸 — 부품 쪽과 같은 차림을 씁니다."""
    # ★ 큰 제목이 비면 **작은 라벨만** 냅니다 (2026-10-06 바깥 검수)
    #   「지도가 보이면 고르는 곳인 줄 압니다」 — 도구 쪽에서는
    #   설명 블록이 고를 자리를 아래로 밀어냅니다.
    머리 = ('<div class="section-head section-head--slim">'
            '<p class="kicker">%s</p></div>' % esc(꼬리말)) if not 제목 else (
        '<div class="section-head"><p class="kicker">%s</p>'
        '<h2 class="serif">%s</h2></div>' % (esc(꼬리말), esc(제목)))
    return ('<section class="section section--%s"><div class="wrap">'
            '%s%s</div></section>'
            % ('white' if 흰 else 'soft', 머리, 속))


def 카드들(것들):
    """{제목, 글, 주소} 목록을 카드 칸으로."""
    쪽 = []
    for 것 in 것들:
        단추 = ''
        if 것.get('주소'):
            단추 = '<p class="pt-in"><a href="%s">%s</a></p>' % (
                esc(것['주소']), esc(것.get('단추') or '보러 가기'))
        쪽.append(
            '<article class="pt"><div class="pt-body">'
            '<h3 class="pt-name">%s</h3><p class="pt-use">%s</p>%s'
            '</div></article>'
            % (esc(것['제목']), esc(것.get('글') or ''), 단추))
    return '<div class="pt-grid pt-grid--wide">%s</div>' % ''.join(쪽)


def _바탕값(d, 쪽길, 언어, 제목, 짧은제목, 설명, 머리말,
            큰제목, 소개글, 한줄, 갈래칸, 꼬리안내,
            돌아갈주소=None, 돌아갈글=None, 이름표글=None,
            _og갈래=None, 안내띠켜기=True):
    """네 쪽이 함께 쓰는 틀 값."""
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets', 'css', 'site.css')
    이름 = d.사이트['이름'].get(언어) or d.사이트['이름']['ko']
    from engine import build as B
    return {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': 제목,
        '짧은제목': 짧은제목,
        '설명': 설명,
        '정식주소': url.full(쪽길),
        '사이트이름': 이름,
        # ★ 쪽길을 함께 넘깁니다 — **쪽마다 다른 그림** (규칙 28)
        '대표사진': B.갈래사진(d, _og갈래,
                              B.사진주소(d, B.대표사진(d)), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길,
                                 B.판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': '',
        '구조화자료': '',
        '머리말': 머리말,
        '기준일조각': B.기준일조각(),
        '머리이름표': (B.이름표(이름표글, 'badge--orange')
                       if 이름표글 else ''),
        '돌아갈주소': esc(돌아갈주소 or url.rel(쪽길, url.home(언어))),
        '돌아갈글': 돌아갈글 or '첫 쪽으로',
        '권역이름': 머리말,
        '메일': d.사이트['메일'],
        '로고': B.로고(뿌리, 이름),
        '꼬리로고': B.꼬리로고(뿌리, 이름),
        # ★ 쪽 갈래를 body 에 실어 **그 쪽에만** 듣는 규칙을 씁니다
        '쪽갈래': _og갈래 or '',
        '한줄': 한줄,
        '큰제목': 큰제목,
        '소개글': 소개글,
        # ★ 주인만 보는 쪽에는 **손님 안내를 달지 않습니다.**
        #   방문 기록 쪽에 「낚시가 처음이라면…」이 떠 있었습니다.
        '안내띠': B.안내띠(쪽길, '낚시') if 안내띠켜기 else '',
        '갈래칸': 갈래칸,
        '기준일안내': 꼬리안내,
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': B.꼬리메뉴(d, 쪽길, 언어),
        '알림글': ('본 자료는 참고용입니다. 금어기·포획 금지 체장은 '
                   '해양수산부 고시를 따릅니다.'),
        '쪽스크립트': '',
    }


# ══════════════════════════════════════════════════════
#  ① rule.html — 금어기와 잡으면 안 되는 크기
# ══════════════════════════════════════════════════════
def 금어기쪽(d, 언어='ko'):
    """494곳이 거는 쪽입니다.

    ★ 손님은 법을 공부하러 오지 않습니다 (합의 R-016)
      「오늘 이거 잡아도 되나」를 보러 옵니다. 그 답이 맨 위에
      있어야 합니다.

    ★ **연중 금지를 계절 금어기와 섞지 않습니다** (바깥 검수 지적)
      명태는 연중 금지인데 오늘 금어기 카드에 섞이면 손님은
      「10월이라 금지」로 받아들입니다. 따로 둡니다.
    """
    import datetime
    자료 = rules.자료()
    쪽길 = url.rule(언어)
    오늘 = datetime.date.today()

    if not 자료:
        return None

    # ── 오늘 걸린 것 — 연중과 계절을 **가릅니다** ────
    연중, 계절 = [], []
    for 것, st, 걸린 in rules.오늘금지(자료, 오늘):
        온해 = any(기['시작'] == '01-01' and 기['끝'] == '12-31'
                   for 기 in 걸린)
        (연중 if 온해 else 계절).append((것, st, 걸린))

    def 금지카드(묶음, 온해):
        쪽 = []
        for 것, st, 걸린 in 묶음:
            크 = ' · '.join(rules.크기글(c) for c in 것.get('크기제한', []))
            기간 = ('연중 금지' if 온해
                    else ' / '.join(rules.기간글(기) for 기 in 걸린))
            메모 = ''
            for 기 in 걸린:
                if 기.get('메모'):
                    메모 = ('<p class="rl-memo">%s</p>' % esc(기['메모']))
                    break
            쪽.append(
                '<article class="rl-card rl-%s">'
                '<p class="rl-tag">%s</p>'
                '<h3 class="rl-name">%s</h3>'
                '<p class="rl-when">%s</p>%s%s</article>'
                % ('always' if 온해 else 'now',
                   '연중 금지' if 온해 else '지금 금어기',
                   esc(것['법령명']), esc(기간),
                   ('<p class="rl-size">%s</p>' % esc(크)) if 크 else '',
                   메모))
        return '<div class="rl-grid">%s</div>' % ''.join(쪽)

    칸들 = []
    if 계절:
        칸들.append(칸(
            '지금 잡으면 안 됩니다',
            '%d월 %d일 기준' % (오늘.month, 오늘.day),
            금지카드(계절, False) +
            '<p class="notice">금어기가 아닌 어종도 <b>크기 제한</b>과 '
            '<b>지역 규정</b>이 있습니다. 아래 전체 목록에서 확인하세요.</p>',
            흰=False))
    else:
        칸들.append(칸(
            '%d월 %d일' % (오늘.month, 오늘.day), '오늘 기준',
            '<p class="notice">오늘 <b>전국 기본 금어기</b>에 걸리는 '
            '어종은 없습니다. 다만 <b>크기 제한</b>과 <b>지역 규정</b>은 '
            '그대로입니다.</p>', 흰=False))

    # ── 전체 표 ──────────────────────────────────────
    줄들 = []
    for 것 in sorted(자료['어종'], key=lambda x: (x.get('갈래') or '', x['법령명'])):
        st, 걸린, 크기들 = rules.상태(것, 오늘)
        기간 = ' / '.join(rules.기간글(기) for 기 in 것.get('금어기간', []))
        크 = ' · '.join(rules.크기글(c) for c in 크기들)
        메모 = ' '.join(기.get('메모') or '' for 기 in 것.get('금어기간', []))
        별칭 = (' <span class="rl-alias">%s</span>'
                % esc(' · '.join(것['별칭']))) if 것.get('별칭') else ''
        줄들.append(
            '<tr class="rl-row rl-%s" data-q="%s">'
            '<th scope="row">%s%s</th>'
            '<td><span class="rl-chip rl-chip--%s">%s</span></td>'
            '<td>%s</td><td>%s</td><td class="rl-note">%s</td></tr>'
            % (rules.상태색[st],
               esc((것['법령명'] + ' ' + ' '.join(것.get('별칭') or [])).strip()),
               esc(것['법령명']), 별칭,
               rules.상태색[st], esc(rules.상태말[st]),
               esc(기간) or '—', esc(크) or '—', esc(메모)))

    표 = ('<div class="rl-tablewrap"><table class="rl-table">'
          '<thead><tr><th scope="col">어종</th><th scope="col">지금</th>'
          '<th scope="col">금어기간</th><th scope="col">크기 제한</th>'
          '<th scope="col">덧붙임</th></tr></thead>'
          '<tbody>%s</tbody></table></div>' % ''.join(줄들))

    찾기 = ('<p class="rl-find">'
            '<label class="sr-only" for="ruleQ">어종 이름으로 찾기</label>'
            '<input id="ruleQ" type="search" '
            'placeholder="어종 이름으로 찾기 — 우럭 · 주꾸미 · 소라" '
            'autocomplete="off" inputmode="search"></p>'
            '<p class="rl-none" id="ruleNone" hidden>'
            '찾는 어종이 목록에 없습니다. 규정이 없다는 뜻은 아닙니다 — '
            '출조 전 관할 지자체 고시를 확인해 주세요.</p>')

    # ★ 찾기칸을 **맨 앞**으로 (2026-10-01 바깥 검수)
    #   「어종 검색」이 긴 표 안에 묻혀 있으면 찾을 수가 없습니다.
    # ★ 찾기칸에 제목을 달지 않습니다 (2026-10-01)
    #   「어종으로 찾기」를 큰 제목으로 달았더니 머리와 겹쳐
    #   첫 화면이 제목 셋으로 꽉 찼습니다. 입력칸의 안내글이
    #   이미 「어종 이름으로 찾기」라고 말합니다.
    칸들.insert(0, '<section class="section section--white">'
                   '<div class="wrap">%s</div></section>' % 찾기)
    칸들.append(칸('법으로 정해진 %d종' % len(자료['어종']),
                   '전체 목록', 표))

    # ── 연중 금지 ────────────────────────────────────
    연중글 = ''.join('<li>%s</li>' % esc(것['설명'])
                     for 것 in 자료.get('포획제한', []))
    if 연중:
        연중글 += ''.join('<li>%s 연중 금지</li>'
                          % esc(조사(것['법령명'], '는'))
                          for 것, _, _ in 연중)
    칸들.append(칸('철과 상관없이 늘 금지', '연중 금지',
                   '<ul class="rl-always">%s</ul>' % 연중글))

    # ── 출처 ─────────────────────────────────────────
    근 = 자료.get('근거') or {}
    출처줄 = ''.join(
        '<li><b>%s</b> — %s %s%s</li>'
        % (esc(k), esc(v.get('법령') or ''), esc(v.get('조항') or ''),
           (' ' + esc(v.get('별표'))) if v.get('별표') else '')
        for k, v in 근.items())
    칸들.append(칸('어디서 가져왔나', '출처',
                   '<ul class="rl-src">%s</ul>'
                   '<p class="notice">기준일 <b>%s</b> · 확인일 <b>%s</b></p>'
                   '<p class="notice">%s</p>'
                   % (출처줄, esc(자료.get('기준일') or '—'),
                      esc(자료.get('확인일') or '—'),
                      esc(자료.get('주의') or ''))))

    값 = _바탕값(
        d, 쪽길, 언어,
        제목='금어기와 잡으면 안 되는 크기 — 법으로 정해진 %d종 | %s'
             % (len(자료['어종']), d.사이트['이름']['ko']),
        짧은제목='금어기·크기 제한',
        설명='수산자원관리법이 정한 금어기와 포획 금지 체장입니다. '
             '오늘 기준으로 지금 잡으면 안 되는 어종을 먼저 보여 줍니다.',
        머리말='금어기·크기 제한',
        # ★ 머리를 **결과**로 바꿉니다 (2026-10-01 바깥 검수)
        #   손님이 이 쪽에 오는 까닭은 법 공부가 아니라
        #   「오늘 이거 잡아도 되는가」를 빨리 보려는 것입니다.
        #   설명을 먼저 깔면 답이 화면 아래로 밀립니다.
        큰제목=('오늘 금어기인 어종 %d종' % len(계절)
                if 계절 else '오늘 전국 금어기인 어종은 없습니다'),
        소개글=('출조 전에 한 번 보고 가세요. '
               '금어기가 아니어도 크기 제한과 지역 규정은 그대로입니다.'),
        한줄='%d월 %d일 기준 · 법으로 정해진 %d종'
             % (오늘.month, 오늘.day, len(자료['어종'])),
        갈래칸=''.join(칸들),
        꼬리안내='시·도지사 고시로 기간이 지역마다 다른 어종이 있고, '
                 '어업 방식에 따른 예외도 많습니다. '
                 '출조 전 관할 지자체 고시를 확인해 주세요.',
        이름표글='%d종' % len(자료['어종']),
        _og갈래='rule')
    값['쪽스크립트'] = (
        '<script>(function(){'
        'var q=document.getElementById("ruleQ"),'
        'n=document.getElementById("ruleNone");'
        'if(!q)return;'
        'var rows=[].slice.call(document.querySelectorAll(".rl-row"));'
        'q.addEventListener("input",function(){'
        'var v=q.value.trim(),c=0;'
        'rows.forEach(function(r){'
        'var on=!v||r.getAttribute("data-q").indexOf(v)>=0;'
        'r.hidden=!on;if(on)c++;});'
        'n.hidden=!!c;});})();</script>')
    # ★ 겉틀이 body 클래스로 쓰는 값 — 안 주면 틀이 멈춥니다
    값.setdefault('쪽갈래', '')
    return 쪽길, template.그리기('rig-parts.html', 값)
