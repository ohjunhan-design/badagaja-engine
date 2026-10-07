# -*- coding: utf-8 -*-
"""**바다에 갔다가 무엇을 함께 즐길까** — travel/ (2026-10-01).

★ 아홉 번째로 끊겨 있던 쪽입니다
  첫 화면의 「06 무엇을 즐길까? 관광·맛집·숙소」가 가리키는데
  build 가 안 만들어, 서버의 옛 파일이 응답했습니다.
  `engine/check_manifest.py` 가 찾아냈습니다.

★ 바깥 검수가 정해 준 설계 (2026-10-01)
  「**(가) 새 틀로 다시 짓습니다.**
    (나) 는 반대합니다 — 관광·맛집·숙소를 눌렀는데 축제나 전체
    권역으로 보내면 **단추의 약속과 도착지가 다릅니다.**
    (다) 도 반대합니다 — 홈의 여섯 단계가 잘 만들어졌고
    「어디로 갈까 → 무엇을 할까 → 어디서 할까 → 오늘 괜찮을까 →
     무엇을 준비할까 → **무엇을 즐길까**」라는 여행 준비 흐름에서
    마지막 단계가 자연스럽습니다」

  「다만 기존 57개 권역의 관광·맛집·숙소를 그대로 복사해 길게
    늘어놓는 쪽은 만들지 않습니다. 그건 **중복 쪽**이 됩니다」

★ 이 쪽이 답하는 질문 — **「바다에 갔다가 무엇을 함께 즐길까?」**
  전국 관광정보 사전이 아니라 **바다 일정의 '두 번째 목적'을
  고르는 묶음**입니다.

      travel/   「어떤 지역·어떤 갈래를 볼까?」
      권역 쪽    「그 지역에는 실제로 무엇이 있나?」

★ **쉽게 낡는 것을 여기에 또 복제하지 않습니다.**
  맛집 영업시간·숙박 가격 같은 것은 권역 쪽이 맡습니다.
  이 쪽은 **고르고 옮겨 가는 일**만 합니다.
  「허브 쪽은 **탐색 기능 자체가 가치**입니다. 광고 때문에
   억지 장문은 넣지 마세요」 (바깥 검수)

══════════════════════════════════════════════════════════
★ **2026-10-07 — 새로 짰습니다** (바깥 검수 시안)

  두 가지가 잘못돼 있었습니다.

  ① **사진이 한 장도 없었습니다.** `rig-parts.html`(글만 있는
     히어로)을 빌려 쓰고 있었습니다.
     주인 규칙 6-1 — 「사람은 눈으로 봅니다. 쪽에는 보이는 것이
     있어야 합니다. **바다 사이트에서 바다 사진이 없으면
     첫인상이 통째로 달라집니다**」

  ② **권역 57개 목록이 세 번 되풀이됐습니다.** 갈래마다 한 벌씩.
     쪽 24.2KB 가운데 상당 부분이 같은 목록 셋이었고, 손님은
     내려가다 「또 그거네」 하게 됩니다.

  바깥 검수 시안 — 「**갈래 3개는 탭, 권역 선택은 단 한 벌**」
    「핵심은 탭을 바꿔도 **권역 목록 DOM 을 다시 만들지 않는
      것**입니다」
    「JS 는 '57개 목록을 갈래마다 다시 그리지 말고 **링크 목적만
      바꾸는 정도**'로 제한」

      [히어로 사진]
      [볼거리 393][먹거리 277][코스 171]   ← 갈래 탭
      [전체][제주][인천·경기]…             ← 광역으로 좁히기
      [제주시내][애월·한림]…               ← 57권역 **한 벌만**
      [추천 사진 카드]

★ **자바스크립트가 없어도 쓸 수 있습니다** (계약-23)
  탭 기본값이 「볼거리」이고 권역 링크도 그때 명소 칸으로 갑니다.
  JS 는 **해시만 갈아끼우고 광역을 걸러 보일 뿐**입니다.

★ **추천 카드에 명소 사진만 쓰는 까닭**
  자료에 있는 사진은 **명소 사진뿐**입니다(먹거리·코스 사진 없음).
  먹거리 탭에 명소 사진을 붙이면 **단추의 약속과 도착지가
  달라집니다** — 바깥 검수가 (나)안을 반대한 바로 그 까닭입니다.
  그래서 추천 카드는 **갈래 탭과 묶지 않고** 「먼저 눈으로 보는
  바다」로 두고, 누르면 그 권역의 **명소 칸**으로 보냅니다.
  사진이 명소 사진이고 도착지도 명소 칸이니 약속이 맞습니다.
"""
import os

from engine import url
from engine import counts
from engine import template
from engine.hubs import esc, _바탕값

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ 사진 **원본**이 있는 자리 — `site/` 가 아닙니다
#
#   ★ 2026-10-06 에 겪은 일 — `site/img` 로 사진을 세었더니
#     깃허브에서 **0장**이 나와 배포가 두 번 막혔습니다.
#     `site/img` 는 빌드가 **쪽을 다 만든 뒤에** 채우는
#     생성물이고, 깨끗한 체크아웃에서는 비어 있습니다.
#     **내 컴퓨터는 차 있어 영영 안 드러났습니다.**
#   원본은 저장소 안 `assets/photo/` 입니다. 여기를 봅니다.
_사진원본 = os.path.join(여기, 'assets', 'photo')

# ★ 세 갈래 — 바깥 검수가 글까지 정해 주었습니다
#
#   다만 세 번째는 **바꿨습니다.** 검수는 「머물 곳 — 바다 가까운
#   숙소 찾기」를 제안했는데, **숙소 자료가 없습니다.**
#   권역 자료(data/raw/travel/)에 있는 것은 이것뿐입니다 —
#       명소 393 · 먹거리 277 · 코스 171 · 마을 90
#   권역 쪽에도 숙소 칸이 없습니다(id="spot"·"eat"·"course").
#
#   **없는 것을 있는 척 보내면 안 됩니다.** 눌렀는데 숙소가
#   없으면 단추가 거짓말을 한 것입니다 — 검수가 (나)를 반대한
#   까닭과 같습니다(「단추의 약속과 도착지가 다릅니다」).
#   그래서 자료가 있는 **코스**로 바꿨습니다.
갈래들 = (
    ('볼거리', '바다 보고 어디를 더 둘러볼까요?', '명소', 'spot', '명소'),
    ('먹거리', '이 지역에서 무엇을 먹을까요?', '먹거리', 'eat', '먹거리'),
    ('코스', '하루를 어떻게 돌까요?', '코스', 'course', '코스'),
)

# ★ **바다가 주제로 보이는 사진만** 씁니다 (주인 규칙 3·4)
#   「바다·해변·항구·갯바위·등대처럼 바다가 주제로 보이는 사진만」
#   「건물 외관, 도로, 간판, 지질 표본, 관공서, 상가 사진 등은 제외」
_바다말 = ('해수욕장', '해변', '해안', '등대', '포구', '갯벌', '어항',
           '방조제', '선착장', '해상', '바다', '섬', '일출', '낙조', '노을')


def _바다사진인가(한장):
    """제목에 바다가 드러나는가 — **이름으로만 가립니다.**

    ★ 좌표로도 걸러져 있습니다 — `fetch_spot_photos.py` 가 받을 때
      **명소 좌표에서 1km 밖이면 버렸습니다.** 여기서는 그 위에
      「바다가 주제인가」만 한 겹 더 봅니다.
    """
    제목 = (한장.get('제목') or '') + ' ' + (한장.get('명소') or '')
    return any(말 in 제목 for 말 in _바다말)


def _실물있나(한장):
    """사진 **원본이 저장소에 실제로 있는가** (주인 규칙 6-1).

    「사진 주소는 자료에서 읽습니다. **짐작해 만들지 않습니다**」
    자료에 적혀 있어도 파일이 없으면 깨진 그림이 나갑니다.
    """
    길 = (한장.get('파일') or '').lstrip('/')
    return bool(길) and os.path.exists(os.path.join(_사진원본, 길))


def _쓸사진들(d):
    """여행 쪽이 쓸 수 있는 사진 — **차례를 못 박아** 돌려줍니다.

    ★ 계약-07(멱등) — 차례가 정해지지 않으면 다시 만들 때마다
      다른 사진이 걸립니다. `파일` 이름으로 정렬해 못 박습니다.
    """
    것 = [x for x in d.사진들
          if x.get('촬영자') and x.get('이용허락')
          and _바다사진인가(x) and _실물있나(x)]
    return sorted(것, key=lambda x: x.get('파일') or '')


def _사진한덩이(d, 한장, 쪽길, 앞장서나=True):
    """사진 한 덩이 — `build.사진자리` 와 **같은 모양**입니다.

    ★ 설명에는 **촬영자만** 적습니다 (주인 규칙 6).
      「공공누리 제1유형」 같은 이용허락 종류는 photos.html 에만 둡니다.
    """
    from engine import build as B
    return B.사진자리(d, 한장, 쪽길, 앞장서나=앞장서나)


def 여행쪽(d, 언어='ko'):
    쪽길 = url.travel(언어)
    수 = counts.모두(d)
    권역수글 = counts.글(수, '권역')

    # ── 갈래마다 **실제 수를 셉니다** (주인 규칙 29)
    #    「명소 393곳」처럼 보이면 눌러 볼 까닭이 생깁니다.
    def _셈(자료칸):
        n = 0
        for r in (d.여행들 or {}).values():   # 여행들 은 **꾸러미**입니다
            v = r.get(자료칸)
            if v:
                n += len(v) if hasattr(v, '__len__') else 1
        return n

    셈들 = {아이디: _셈(자료칸)
            for _이름, _물음, _속, 아이디, 자료칸 in 갈래들}

    # ── ① 히어로 사진 — 바다가 주제인 것 가운데 첫 장
    쓸것 = _쓸사진들(d)
    히어로 = 쓸것[0] if 쓸것 else None
    대표사진자리 = (_사진한덩이(d, 히어로, 쪽길, 앞장서나=True)
                    if 히어로 else '')

    # ── ② 갈래 탭 — 누르면 권역 링크의 **해시만** 바뀝니다
    탭들 = []
    for i, (이름, 물음, _속, 아이디, _칸) in enumerate(갈래들):
        탭들.append(
            '<button type="button" class="tv-tab%s" role="tab"'
            ' id="tvTab-%s" data-goal="%s" data-ask="%s"'
            ' aria-selected="%s" aria-controls="tvRegions">'
            '<span class="tv-tab-name">%s</span>'
            '<span class="tv-tab-n">%s곳</span></button>'
            % (' is-on' if i == 0 else '', esc(아이디), esc(아이디),
               esc(물음), 'true' if i == 0 else 'false',
               esc(이름), esc(format(셈들[아이디], ','))))
    갈래탭 = ''.join(탭들)

    # ── ③ 광역으로 먼저 좁힙니다 — 57개를 한꺼번에 보면 고르기 어렵습니다
    #     ★ 차례는 **사이트가 쓰는 차례 그대로**입니다
    #       (주인이 정한 것 — 제주를 첫 번째로. 바깥 검수도
    #        「기존 사이트가 사용하는 고정 권역 순서를 그대로」)
    광역 = ['<button type="button" class="tv-prov is-on"'
            ' data-prov="all">전체</button>']
    for 묶 in d.색인['묶음차례']:
        것들 = [r for r in d.권역들 if r['묶음'] == 묶]
        if not 것들:
            continue
        묶음이름 = (d.색인['묶음이름'][묶].get(언어)
                    or d.색인['묶음이름'][묶]['ko'])
        광역.append('<button type="button" class="tv-prov"'
                    ' data-prov="%s">%s</button>'
                    % (esc(묶), esc(묶음이름)))
    광역단추 = ''.join(광역)

    # ── ④ 권역 **한 벌** — 쪽에 단 한 번만 있습니다
    #     `data-to` 에 권역 쪽 주소만 두고, 해시는 JS 가 붙입니다.
    #     JS 가 없으면 `href` 에 이미 **첫 갈래 해시**가 있습니다.
    첫갈래 = 갈래들[0][3]
    한벌 = []
    for 묶 in d.색인['묶음차례']:
        것들 = [r for r in d.권역들 if r['묶음'] == 묶]
        if not 것들:
            continue
        for r in 것들:
            이름값 = r.get('이름')
            보일이름 = (이름값.get(언어) or 이름값.get('ko')
                        if isinstance(이름값, dict) else 이름값) or r['id']
            권역주소 = url.rel(쪽길, url.region(r['id'], 언어))
            한벌.append(
                '<a class="tv-region" href="%s#%s" data-to="%s"'
                ' data-prov="%s">%s</a>'
                % (esc(권역주소), esc(첫갈래), esc(권역주소),
                   esc(묶), esc(보일이름)))
    권역한벌 = ''.join(한벌)

    # ── ⑤ 추천 사진 카드 — 「먼저 눈으로 보는 바다」
    #     ★ 갈래 탭과 **묶지 않습니다.** 자료에 있는 사진은
    #       명소 사진뿐이라, 먹거리 탭에 붙이면 **단추의 약속과
    #       도착지가 달라집니다**(검수가 (나)안을 반대한 까닭).
    #       누르면 그 권역의 **명소 칸**으로 보냅니다 — 사진도
    #       명소 사진이고 도착지도 명소 칸이니 약속이 맞습니다.
    #
    #     ★ 권역이 겹치지 않게 골라 **여러 바다**를 보입니다.
    카드들, 쓴권역 = [], set()
    for x in 쓸것[1:]:
        권 = x.get('권역')
        if not 권 or 권 in 쓴권역:
            continue
        쓴권역.add(권)
        이름값 = next((r.get('이름') for r in d.권역들 if r['id'] == 권), None)
        권역이름 = (이름값.get(언어) or 이름값.get('ko')
                    if isinstance(이름값, dict) else 이름값) or 권
        카드들.append(
            '<a class="tv-card" href="%s#%s">%s'
            '<span class="tv-card-copy">'
            '<b class="tv-card-name">%s</b>'
            '<span class="tv-card-where">%s</span></span></a>'
            % (esc(url.rel(쪽길, url.region(권, 언어))), esc(첫갈래),
               _사진한덩이(d, x, 쪽길, 앞장서나=False),
               esc(x.get('제목') or ''), esc(권역이름)))
        if len(카드들) >= 6:
            break

    갈래칸 = ''
    if 카드들:
        갈래칸 = (
            '<section class="section tv-shots" id="shots"><div class="wrap">'
            '<div class="section-head"><p class="kicker">먼저 눈으로</p>'
            '<h2 class="serif">이런 바다가 기다립니다</h2>'
            '<p class="lead">누르면 그 권역의 명소 칸으로 갑니다.</p></div>'
            '<div class="tv-shot-grid">%s</div>'
            '</div></section>' % ''.join(카드들))

    # ── ⑥ 탭·필터를 움직이는 스크립트
    #     ★ 바깥 검수 — 「57개 목록을 갈래마다 **다시 그리지 말고**
    #       링크 목적만 바꾸는 정도로 제한」
    쪽스크립트 = (
        '<script>(function(){'
        'var 묶="tvRegions",목=document.getElementById(묶);'
        'if(!목)return;'
        'var 것들=목.querySelectorAll(".tv-region");'
        'var 물음=document.getElementById("tvGoal");'
        'var 더2=document.getElementById("tvMore");'
        # 갈래 탭 — **해시만** 갈아끼웁니다
        'Array.prototype.forEach.call('
        'document.querySelectorAll(".tv-tab"),function(단){'
        '단.addEventListener("click",function(){'
        'Array.prototype.forEach.call('
        'document.querySelectorAll(".tv-tab"),function(x){'
        'x.classList.remove("is-on");x.setAttribute("aria-selected","false");'
        '});'
        '단.classList.add("is-on");단.setAttribute("aria-selected","true");'
        'var 끝="#"+단.getAttribute("data-goal");'
        'Array.prototype.forEach.call(것들,function(a){'
        'a.setAttribute("href",a.getAttribute("data-to")+끝);});'
        'if(물음)물음.textContent=단.getAttribute("data-ask")||"";'
        '});});'
        # 광역 필터 — 보이고 감추기만 합니다
        'Array.prototype.forEach.call('
        'document.querySelectorAll(".tv-prov"),function(단){'
        '단.addEventListener("click",function(){'
        'Array.prototype.forEach.call('
        'document.querySelectorAll(".tv-prov"),function(x){'
        'x.classList.remove("is-on");});'
        '단.classList.add("is-on");'
        'var 골=단.getAttribute("data-prov");'
        'Array.prototype.forEach.call(것들,function(a){'
        'a.hidden=(골!=="all"&&a.getAttribute("data-prov")!==골);});'
        # 지역을 고르면 그 지역은 수가 적으므로 **전부** 보입니다
        'if(골!=="all"){목.classList.add("is-open");}'
        'if(더2&&골!=="all"){더2.hidden=true;}'
        'else if(더2){더2.hidden=false;}'
        '});});'
        # ★ **모두 보기** — 첫 화면에서만 접습니다 (2026-10-07)
        #   광역을 고르면 그 지역은 수가 적으므로 **전부** 보입니다.
        'var 더=document.getElementById("tvMore");'
        'if(더){더.addEventListener("click",function(){'
        'var 펼=목.classList.toggle("is-open");'
        '더.setAttribute("aria-expanded",펼?"true":"false");'
        # ★ 숫자를 **박지 않습니다** — 틀의 data-all 을 되돌려 씁니다
        '더.textContent=펼?"접기":(더.getAttribute("data-all")||"모두 보기");'
        '});}'
        '})();</script>')

    값 = _바탕값(
        d, 쪽길, 언어,
        제목='바다 여행 — 볼거리·먹거리·코스 | %s'
             % d.사이트['이름']['ko'],
        짧은제목='바다 여행',
        설명='바다에 갔다가 무엇을 함께 즐길지 고릅니다. 전국 %s개 '
             '권역의 명소·지역 음식·하루 코스로 이어집니다.' % 권역수글,
        머리말='바다 여행',
        큰제목='바다에 갔다가 무엇을 함께 즐길까',
        소개글='볼거리 · 먹거리 · 코스 가운데 고르고, 권역을 '
               '누르면 그곳에 실제로 무엇이 있는지 보여 드립니다.',
        한줄='전국 %s개 권역' % 권역수글,
        갈래칸=갈래칸,
        꼬리안내='영업시간·가격처럼 자주 바뀌는 것은 가시기 전에 '
                 '한 번 더 확인해 주세요.',
        이름표글='%s개 권역' % 권역수글,
        _og갈래='travel')
    값.update({
        '대표사진자리': 대표사진자리,
        '갈래탭': 갈래탭,
        '광역단추': 광역단추,
        '권역한벌': 권역한벌,
        '첫갈래물음': 갈래들[0][1],
        '권역수글': '%s권역' % 권역수글,
        '고르기안내': '가고 싶은 바다를 먼저 골라 보세요. '
                      '위에서 갈래를 바꾸면 같은 목록이 그 갈래로 갑니다.',
        '쪽스크립트': 쪽스크립트,
    })
    return 쪽길, template.그리기('travel.html', 값)
