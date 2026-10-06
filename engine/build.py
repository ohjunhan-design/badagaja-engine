# -*- coding: utf-8 -*-
"""쪽을 만드는 **단 하나의 곳**입니다.  (계약-01)

왜
    옛 사이트는 생성기 28개·후처리 16개였습니다. 새 기능을 넣을 때마다
    한 곳을 빠뜨렸고, 권역 쪽 광고가 42곳에만 들어가고 15곳이 빠졌습니다.
    여기 말고 다른 데서 HTML 을 쓰지 않습니다.

무엇을 만들지는 **자료가 정합니다** (계약-11)
    만들 쪽 목록을 손으로 적지 않습니다. 자료를 읽어 스스로 정합니다.
    그래서 권역이 늘면 쪽도 저절로 늡니다.

숫자는 **셉니다** (계약-04·06)
    「110곳」을 어디에도 적지 않습니다. 자료를 세어 넣습니다.

쓰는 법
    python engine/build.py                  전부 만듭니다
    python engine/build.py --only taean     한 권역만 (수직 슬라이스)
    python engine/build.py --list           무엇을 만들지 보여만 줍니다
"""
import os
import re
import sys
import json
import html
import hashlib
import datetime
import subprocess
import posixpath
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, url, template, art, hubs   # noqa: E402
from engine import hubs_more   # noqa: E402
from engine import hubs_site   # noqa: E402
from engine import hubs_basics   # noqa: E402
from engine import hubs_gear     # noqa: E402
from engine import hubs_muldae   # noqa: E402
from engine import hubs_data   # noqa: E402
from engine import hubs_travel   # noqa: E402
from engine.korean import 조사      # noqa: E402
from engine.data import 자료            # noqa: E402

나갈곳 = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
ASSETS = os.path.join(ROOT, 'assets')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

지형코드 = {
    '방파제': 'breakwater', '갯바위': 'rock', '선착장': 'pier', '항구': 'port',
    '해변': 'beach', '갯벌': 'mudflat', '해안': 'shore',
}



# ── 사진 ───────────────────────────────────────────────────
#
# ★ 주소를 **짐작하지 않습니다** (2026-09-27)
#   전에는 '%s/img/%s/hero.jpg' % (주소, 권역) 처럼 만들어 썼습니다.
#   권역 57곳 가운데 15곳만 그 자리에 파일이 있었고, 나머지 52곳은
#   img/coast/{권역}-hero.jpg 였습니다. 그래서 공유 미리보기가
#   52갈래나 깨져 있었습니다. 이제 자료에서만 읽습니다.
_사진지문기억 = {}


def _사진지문(파일):
    """사진 **알맹이**의 지문. 이름이 달라도 같은 사진을 알아봅니다.

    2026-10-02 — 히어로와 명소 카드가 같은 사진을 쓰는 곳이 네 권역
    있었습니다. 이름은 달랐습니다(`changwon-hero` 와 `changwon-udo`).
    이름만 보면 영영 못 찾습니다.
    """
    if not 파일:
        return None
    if 파일 in _사진지문기억:
        return _사진지문기억[파일]
    import hashlib
    # ★ **원본 자리에서도 찾습니다** (2026-10-06 — 계약-07 이 깨졌습니다)
    #
    #   전에는 `나갈곳`(site/)만 봤습니다. 쌓인 자리에서는 사진이
    #   이미 옮겨져 있어 지문이 나오는데, **빈 자리에 처음 지으면**
    #   아직 없어 `OSError` → 지문 None → 「중복 아님」이 됩니다.
    #
    #   그래서 창원·강릉·서귀포 세 쪽이 **지을 때마다 달라졌습니다** —
    #   쌓인 자리는 사진 5장, 빈 자리는 6장. 계약-07(두 번 만들어도
    #   결과가 같아야 한다)이 그것을 잡았습니다.
    #
    #   사진의 알맹이는 옮기기 전후가 같습니다. 원본을 보면
    #   **자리 형편과 상관없이** 같은 답이 나옵니다.
    후보 = []
    if os.path.isabs(파일):
        후보.append(파일)
    else:
        후보.append(os.path.join(나갈곳, 파일))
        후보.append(os.path.join(ROOT, 'assets', 'photo', 파일))
        후보.append(os.path.join(DATA, 파일))
    지문 = None
    for 길 in 후보:
        try:
            with open(길, 'rb') as f:
                지문 = hashlib.sha1(f.read()).hexdigest()
            break
        except OSError:
            continue
    _사진지문기억[파일] = 지문
    return 지문


def 대표사진(d, 권역=None, 묶음=None):
    """그 쪽의 대표 사진 한 장. 없으면 None — 지어내지 않습니다."""
    if 권역:
        한장 = d.히어로(권역)
        if 한장:
            return 한장
    if 묶음:
        # 묶음 쪽은 그 묶음에 든 첫 권역의 사진을 씁니다
        for x in d.권역들:
            if x.get('묶음') == 묶음:
                한장 = d.히어로(x['id'])
                if 한장:
                    return 한장
    for x in d.사진들:
        if x.get('쓰임') == 'home':
            return x
    return None


def 사진주소(d, 한장):
    """공유 미리보기(og:image)에 쓸 **온전한 주소**."""
    if not 한장 or not 한장.get('파일'):
        return ''
    return '%s/%s' % (d.사이트['주소'], 한장['파일'])


def 공유그림(d, 갈래, 아이디, 기본):
    """공유 미리보기 그림을 **쪽 갈래와 아이디로 스스로 고릅니다.**

    ★ 왜 만들었나 (2026-10-01 합의 D-003·D-004)
      채비 쪽 18곳의 공유 그림이 **모두 home-hero.jpg** 였습니다.
      카카오톡에 어느 채비를 나눠도 같은 바다 사진이 떴습니다.
      네이버·구글 가이드는 **쪽마다 다른 그림**을 요구합니다.

      까닭은 쪽마다 손으로 적는 짜임이었기 때문입니다.
      그래서 **틀이 스스로 고르게** 바꿉니다 —

          assets/og/{갈래}/{아이디}.webp  가 있으면 그것
          없으면 지금까지 쓰던 것

      그림이 생기면 **코드를 한 줄도 안 고치고** 바뀝니다.
      바깥 검수가 그림을 주면 그 자리에 넣기만 하면 됩니다.

    ★ 짐작으로 주소를 만들지 않습니다 (주인 규칙 6-1)
      겪은 일 — img/{권역}/hero.jpg 로 지어냈는데 57곳 중
      15곳만 그 자리에 있었습니다. **파일이 실제로 있는지**
      보고 나서 씁니다.
    """
    if not 갈래 or not 아이디:
        return 기본
    # ① 따로 지은 공유 그림이 있으면 **그것이 먼저**입니다
    for 끝 in ('.webp', '.jpg', '.png'):
        상대 = 'assets/og/%s/%s%s' % (갈래, 아이디, 끝)
        if os.path.isfile(os.path.join(ROOT, 상대.replace('/', os.sep))):
            return '%s/%s' % (d.사이트['주소'], 상대)
    # ② 채비 쪽은 **그 채비 안내도**를 씁니다 (2026-10-01)
    #    바깥 검수는 「안내도를 그대로 OG 로 쓰면 글자가 잘린다」
    #    했습니다. 맞습니다. 다만 17쪽이 모두 같은 바다 사진인
    #    지금보다는 **그 채비 그림이 뜨는 쪽**이 낫습니다.
    #    따로 지은 그림이 오면 ①이 이깁니다.
    if 갈래 == 'rig':
        상대 = 'img/rig/%s.webp' % 아이디
        if os.path.isfile(os.path.join(ROOT, 'data',
                                       상대.replace('/', os.sep))):
            return '%s/%s' % (d.사이트['주소'], 상대)
    return 기본


# ★ 쪽마다 **다른 바다 사진**을 줍니다 (2026-10-01)
#
#   공유 그림이 27쪽에서 같았습니다 — 첫 쪽·금어기·장비·물때·
#   어종 목록·채비 목록이 모두 같은 제주 사진이었습니다.
#   카카오톡에 무엇을 나눠도 같은 그림이 떴습니다.
#   네이버·구글 가이드는 **쪽마다 다른 그림**을 요구합니다.
#
#   따로 지은 OG 그림이 오면 그것이 이깁니다(공유그림 ①).
#   그때까지는 **있는 사진 가운데 어울리는 것**을 씁니다.
#   짐작으로 주소를 만들지 않습니다 — 자료에 있는 것만 씁니다.
쪽마다사진 = {
    'rule': ('어종', None),        # 금어기 — 어종 사진
    'gear': ('채비', None),        # 장비 — 채비 그림
    'tide': ('바다', 'taean'),     # 물때 — 갯벌이 드러난 바다
    'guide': ('어종', None),
    'fish': ('어종', None),
    'catch': ('바다', 'sinan'),
    'festival': ('바다', 'boryeong'),
    'rig': ('채비', None),
}


def 갈래사진(d, 갈래, 기본):
    """쪽 갈래에 어울리는 사진 하나. 없으면 기본."""
    것 = 쪽마다사진.get(갈래)
    if not 것:
        return 기본
    무엇, 권역 = 것
    if 무엇 == '어종':
        for 안내 in (d.안내('낚시') or []):
            한장 = d.어종사진(안내['id'])
            if 한장 and 한장.get('파일'):
                return 사진주소(d, 한장)
    elif 무엇 == '바다' and 권역:
        한장 = d.히어로(권역)
        if 한장 and 한장.get('파일'):
            return 사진주소(d, 한장)
    return 기본


def 돌려쓸사진(d, 권역, 몇번째, 기본):
    """같은 권역 쪽이 여럿일 때 **사진을 돌려 씁니다**.

    ★ 2026-10-01 — 공유 그림이 58가지나 겹쳐 있었습니다.
      신안 축제 10쪽이 모두 같은 신안 히어로를 썼습니다.
      카카오톡에 어느 축제를 나눠도 같은 사진이 떴습니다.
      네이버·구글 가이드는 **쪽마다 다른 그림**을 요구합니다.

      축제 자료에는 사진이 없습니다(197개 모두). 그러나
      **권역에는 명소 사진이 여러 장** 있습니다. 차례대로
      돌려 쓰면 적어도 같은 사진이 줄줄이 나오지는 않습니다.

    ★ 사진이 모자라면 그냥 기본을 씁니다 — 지어내지 않습니다.
    """
    것들 = [x for x in (d.명소사진(권역) or []) if x.get('파일')]
    히 = d.히어로(권역)
    if 히 and 히.get('파일'):
        것들 = [히] + [x for x in 것들
                       if x['파일'] != 히['파일']]
    if not 것들:
        return 기본
    return 사진주소(d, 것들[몇번째 % len(것들)])


def 사진자리(d, 한장, 쪽길, 앞장서나=True):
    """쪽에 보일 사진 한 덩이.

    ★ 설명에는 **촬영자만** 적습니다 (주인 규칙 6).
      「공공누리 제1유형」 같은 이용허락 종류는 photos.html 에만 둡니다.

    ★ 가로·세로를 적어 둡니다 (계약-14)
      사진이 내려오기 전에도 자리를 잡아, 글이 밀렸다 올라갔다
      하지 않습니다.
    """
    if not 한장 or not 한장.get('파일'):
        return ''
    주소 = url.rel(쪽길, 한장['파일'])
    제목 = (한장.get('제목') or '').strip()
    찍은이 = (한장.get('촬영자') or '').strip()
    넓, 높 = 한장.get('가로'), 한장.get('세로')
    크기글 = (' width="%d" height="%d"' % (넓, 높)) if (넓 and 높) else ''
    # 맨 위 사진은 곧바로, 아래쪽 사진은 늦게 내려받습니다
    늦게 = '' if 앞장서나 else ' loading="lazy" decoding="async"'
    빠르게 = ' fetchpriority="high"' if 앞장서나 else ''
    설명 = ('사진 · %s · %s' % (제목, 찍은이)) if 찍은이 else ('사진 · %s' % 제목)
    return ('<figure class="photo%s">'
            '<img src="%s" alt="%s"%s%s%s>'
            '<figcaption>%s</figcaption>'
            '</figure>'
            % (' photo--hero' if 앞장서나 else '',
               주소, html.escape(제목), 크기글, 늦게, 빠르게,
               html.escape(설명)))



# ── 빠른이동 아이콘 ────────────────────────────────────────
#
# ★ 2026-09-27 주인 지적 「너무 많이 줄었어」
#   옛 쪽에는 이 아이콘 7개가 있었는데 새 틀에서 통째로 빠졌습니다.
#   글자만 든 알약 단추가 되어 한눈에 안 들어왔습니다.
#
#   ★ 모양은 **옛 사이트에서 그대로 가져왔습니다.** 새로 그리지
#     않았습니다. 손님이 보던 그림이 그대로여야 낯설지 않습니다.
#     (옛 badagaja-site/taean.html 의 qn-item)
_빠른이동아이콘 = {
    'points': '<path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z"/>'
              '<circle cx="12" cy="9" r="2.4"/>',
    'tide': '<path d="M2 15c1.5-1.5 3-1.5 4.5 0s3 1.5 4.5 0 3-1.5 4.5 0 '
            '3 1.5 4.5 0"/>'
            '<path d="M2 19c1.5-1.5 3-1.5 4.5 0s3 1.5 4.5 0 3-1.5 4.5 0 '
            '3 1.5 4.5 0"/>'
            '<path d="M12 3v9"/><path d="M9 8l3-3 3 3"/>',
    'catch': '<path d="M6.5 12c0-3 4-6.5 9-6.5 3 0 4.5 2 4.5 2s-1.5 3.5-1.5 '
             '4.5 1.5 4.5 1.5 4.5-1.5 2-4.5 2c-5 0-9-3.5-9-6.5z"/>'
             '<path d="M6.5 12L2 9v6l4.5-3z"/>'
             '<circle cx="15.5" cy="10" r=".8" fill="currentColor"/>',
    'stay': '<path d="M3 19V8"/><path d="M3 19h18"/>'
            '<path d="M21 19v-6a2 2 0 00-2-2h-8v8"/>'
            '<circle cx="7" cy="11" r="1.6"/><path d="M3 11h5"/>',
    'eat': '<path d="M6 3v7a2 2 0 002 2 2 2 0 002-2V3"/><path d="M8 12v9"/>'
           '<path d="M17 3c-1.5 0-3 1.5-3 4s.5 3 1.5 3.5V21"/>',
    'spot': '<path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z"/>'
            '<circle cx="12" cy="9" r="2.4"/>',
    'festival': '<rect x="3" y="5" width="18" height="16" rx="2"/>'
                '<path d="M3 10h18"/><path d="M8 3v4"/><path d="M16 3v4"/>'
                '<circle cx="8" cy="14.5" r="1"/>'
                '<circle cx="12" cy="14.5" r="1"/>'
                '<circle cx="16" cy="14.5" r="1"/>',
    'course': '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="18" r="2"/>'
              '<path d="M5 8v3a2 2 0 002 2h6a2 2 0 012 2v3"/>',
}



_남길것 = None


def 남기기로한것():
    """옛 사이트에 그대로 두는 것 — **keep.json 한 곳에서** 읽습니다."""
    global _남길것
    if _남길것 is None:
        d = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
        _남길것 = set(k for k in (d.get('남길것') or {})
                      if not k.startswith('_'))
    return _남길것


def 빠른이동칸(칸들, 칩=False):
    """아이콘 + 글자로 된 빠른이동. 내용이 있는 칸만 냅니다 (계약-11).

    ★ `칩=True` 면 **가로로 미는 칩 한 줄**을 냅니다
      (2026-10-02 지피티 시안 v3 · 권역 쪽)

      전에는 7칸이 **세로로** 쌓여 머리말을 길게 만들었습니다.
      지피티 — 「7칸 세로 목록은 없앱니다. 이게 스크롤을 잡아먹는
      큰 원인입니다. 가로 스크롤 칩 한 줄로 바꿉니다」
      칩에는 아이콘을 넣지 않습니다 — 한 줄에 더 많이 들어갑니다.
    """
    나옴 = []
    for 어디, 이름, 수 in 칸들:
        if not 수:
            continue
        if 칩:
            나옴.append('<a href="#%s">%s</a>' % (어디, esc(이름)))
            continue
        길 = _빠른이동아이콘.get(어디, '')
        그림 = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                'stroke-width="1.6" aria-hidden="true">%s</svg>' % 길) if 길 else ''
        나옴.append('<a class="qn-item" href="#%s">%s<span>%s</span></a>'
                    % (어디, 그림, esc(이름)))
    return ''.join(나옴)


def 숫자칸(d, 권역, 언어='ko'):
    """머리말 오른쪽 **숫자 2×2** (2026-10-02 지피티 시안 v3).

    지피티가 정한 넷 — 포인트 수 · 많이 찾는 대상 종수 ·
    오늘 물때 · 지금 확인할 금어기.

    ★ 숫자는 **자료에서 셉니다. 손으로 적지 않습니다** (주인 규칙 29).
    ★ 「오늘 물때」는 계산이라 자바스크립트가 채웁니다. 못 돌아도
      칸은 남고 「—」 로 보입니다 (계약-23).
    """
    낚, 해 = d.셈(권역, '낚시'), d.셈(권역, '해루질')
    어종셈 = set()
    for 갈 in ('낚시', '해루질'):
        for x in (d.포인트(권역, 갈) or []):
            어종셈.update(x.get('대상') or [])
    관 = ((d.권역(권역) or {}).get('물때관측소') or {}).get('이름') or ''

    # 금어기 — 답 묶음과 **같은 셈**을 씁니다 (계약-01)
    금 = 0
    try:
        from engine import rules as _규정
        for 것, _st, 기들 in _규정.오늘금지():
            if set(것.get('사이트어종') or []) & 어종셈:
                금 += 1
    except Exception:
        pass

    것들 = [
        ('%d' % (낚 + 해), '낚시·해루질 포인트'),
        ('%d종' % len(어종셈), '많이 찾는 대상어종'),
        ('<b id="tsMuldaeNum">—</b>',
         '오늘 물때%s' % (' · %s 관측소' % 관 if 관 else '')),
        ('%d건' % 금, '지금 확인할 금어기'),
    ]
    return ''.join(
        '<div class="hc-stat"><b>%s</b><span>%s</span></div>'
        % (값 if 값.startswith('<') else esc(값), esc(글))
        for 값, 글 in 것들)



# ── 그린 그림 ──────────────────────────────────────────────
#
# ★ 2026-09-27 주인 지시 「정보가 없다면 너가 어울리게 사진으로 만들어」
#   목록 쪽 셋은 사진 자료가 없습니다. engine/make_cover.py 가
#   그린 그림을 씁니다.
#
# ★ **사진인 척하지 않습니다** (주인 규칙 5)
#   설명에 「그림 · 바다가자닷컴」이라 적습니다. 촬영자를 지어내면
#   없는 사진을 쓰는 것보다 나쁩니다.
_그린그림 = {
    'catch': ('assets/cover/catch-cover.svg', '갯벌과 조개'),
    'fish': ('assets/cover/fish-cover.svg', '바다와 물고기'),
    'festival': ('assets/cover/festival-cover.svg', '바닷가 축제'),
}



def 달별막대(달별, 쪽길):
    """★ **달마다 축제가 몇인지** 막대로 보여 줍니다 (2026-09-29)

    주인이 표지 삽화를 빼라 하셨습니다 —
    「정보전달도 없고 칸도 너무 많이 차지해」.

    그런데 빼고 나니 이 쪽에 **보이는 것이 하나도 없어져**
    check_photos 검사 1이 잡았습니다 (주인 규칙 6-1).

    ★ 그래서 **장식 대신 알려 주는 그림**을 넣습니다.
      규칙 6-1 그대로입니다 —
      「숫자를 글로만 적지 말고 길이·색으로도 보이게 합니다」

    ★ 숫자는 **자료에서 셉니다** (주인 규칙 29). 손으로 안 적습니다.
    """
    수들 = [len(달별.get(m) or []) for m in range(1, 13)]
    최대 = max(수들) or 1
    칸, 틈, 높 = 34, 10, 96
    너비 = 12 * 칸 + 11 * 틈
    조각 = []
    for i, 수 in enumerate(수들):
        x = i * (칸 + 틈)
        길이 = max(3, round(수 / 최대 * (높 - 34)))
        y = 높 - 22 - 길이
        진함 = '.35' if 수 == 0 else ('1' if 수 >= 최대 * .7 else '.66')
        조각.append(
            '<rect x="%d" y="%d" width="%d" height="%d" rx="5" '
            'fill="#2F5D57" fill-opacity="%s"/>' % (x, y, 칸, 길이, 진함))
        if 수:
            조각.append('<text x="%d" y="%d" font-size="11" font-weight="700" '
                        'text-anchor="middle" fill="#2B2116">%d</text>'
                        % (x + 칸 // 2, y - 5, 수))
        조각.append('<text x="%d" y="%d" font-size="11" text-anchor="middle" '
                    'fill="#6B5E4F">%d</text>' % (x + 칸 // 2, 높 - 6, i + 1))
    많은달 = 수들.index(최대) + 1
    return ('<figure class="fest-bar">'
            '<svg viewBox="0 0 %d %d" role="img" '
            'aria-label="달마다 축제 수 — 가장 많은 달은 %d월 %d개">'
            '<title>달마다 축제 수</title>%s</svg>'
            # ★ 설명은 **「그림」으로 시작**해야 합니다 (2026-09-29)
            #   check_photos --strict 가 잡습니다 — 그림인데 사진인 척
            #   하면 안 됩니다 (주인 규칙 5).
            #   처음에는 「그림 · 바다가자닷컴」을 **끝**에 적어
            #   판정에서 걸렸습니다.
            '<figcaption>그림 · 바다가자닷컴 — 막대가 길수록 그 달에 '
            '축제가 많습니다. 가장 많은 달은 <b>%d월(%d개)</b>입니다.'
            '</figcaption></figure>'
            % (너비, 높, 많은달, 최대, ''.join(조각), 많은달, 최대))

def 그림자리(무엇, 쪽길):
    """사진 자료가 없는 쪽에 쓸 그림 한 덩이."""
    것 = _그린그림.get(무엇)
    if not 것:
        return ''
    상대, 제목 = 것
    바탕 = os.path.join(ASSETS, os.path.basename(os.path.dirname(상대)),
                        os.path.basename(상대))
    if not os.path.exists(바탕):
        return ''                      # 없는 것을 가리키지 않습니다
    return ('<figure class="photo photo--hero photo--drawn">'
            '<img src="%s" alt="%s" width="1200" height="800" '
            'fetchpriority="high">'
            '<figcaption>그림 · %s</figcaption>'
            '</figure>'
            % (url.rel(쪽길, 상대), html.escape(제목),
               html.escape('바다가자닷컴')))



def 히어로사진(d, 한장, 쪽길):
    """첫 화면 배경 사진. 맨 먼저 보이므로 곧바로 내려받습니다."""
    if not 한장 or not 한장.get('파일'):
        return ''
    return ('<img class="hero-bg" src="%s" alt="%s" width="%d" height="%d" '
            'fetchpriority="high" decoding="async">'
            % (url.rel(쪽길, 한장['파일']),
               html.escape(한장.get('제목') or ''),
               한장.get('가로') or 1800, 한장.get('세로') or 1200))



def 히어로설명(한장):
    """배경 사진의 촬영자. 규칙 6 — 이용허락 종류는 안 적습니다."""
    if not 한장:
        return ''
    제목 = (한장.get('제목') or '').strip()
    찍은이 = (한장.get('촬영자') or '').strip()
    글 = ('사진 · %s · %s' % (제목, 찍은이)) if 찍은이 else ('사진 · %s' % 제목)
    return '<p class="hero-credit">%s</p>' % html.escape(글)



# ── 전국 바다지도 ──────────────────────────────────────────
#
# ★ 2026-09-27 주인 지시 「이건 예전 지도로 권역선택하게 하고」
#   옛 첫 화면에 있던 지도입니다. 묶음 아홉 곳이 눌러지는 땅 모양으로
#   그려져 있고, 누르면 그 묶음 쪽으로 갑니다.
#
#   사진 카드보다 지도가 나은 까닭 — **바닷가는 자리가 곧 정보**입니다.
#   「인천·경기」라는 글자를 읽는 것보다 지도 위 그 자리가 빠릅니다.
#
#   좌표는 data/raw/map.json 에서 읽습니다. 손으로 안 적습니다.
def 동호회칸(d):
    """첫 화면 동호회 칸 — 바다가자 클라우드로 보냅니다.

    ★ 2026-09-27 주인 지시 「바다가자 클라우드로 링크걸어서 만들어」

      규칙 12(개인 사이트로 연결하지 않습니다)는 **남의** 개인
      사이트를 말합니다. badagaja.cloud 는 주인 소유 도메인이고,
      저장소 cloud/ 에 그 쪽이 함께 있습니다.

      글과 주소는 data/raw/site.json 에 있습니다. 여기 안 박습니다.
    """
    것 = d.사이트.get('동호회') or {}
    주소 = 것.get('주소')
    if not 주소:
        return ''                # 자료가 없으면 안 만듭니다
    제목 = 것.get('제목') or []
    줄 = ''.join('<li>%s</li>' % esc(x) for x in (것.get('줄') or []))
    return (
        '<section class="g-panel g-clubpanel"><div class="gcp-in">'
        '<span class="gc-tag">%s</span>'
        '<h2>%s</h2><p>%s</p><ul>%s</ul>'
        '<a class="gcp-btn" href="%s" rel="noopener">%s</a>'
        '<small>%s</small>'
        '</div></section>'
        % (esc(것.get('이름표', '')),
           '<br>'.join(esc(x) for x in 제목),
           esc(것.get('소개', '')), 줄,
           esc(주소), esc(것.get('단추', '')),
           esc(것.get('작은글', ''))))

def 브랜드각인(d, 언어='ko'):
    """첫 화면 오른쪽 빈자리에 **이름을 새깁니다** (2026-09-29 주인 지시).

    ★ 「이곳에 바다가자닷컴의 이름이 각인되도록 뭔가 베너나
      홍보같은게 필요할거 같아 **사람들이 이름을 잊어버리지 않도록**」

    ★ 히어로 사진의 오른쪽은 글이 없어 **비어 있었습니다.**
      쓰지 않는 자리에 이름을 두면, 자리도 살고 이름도 남습니다.

    ★ 광고가 아닙니다. 누르는 것도 아닙니다 — **장식**입니다.
      그래서 읽어 주기(aria)에서는 뺍니다. 머리에 이미 같은
      이름이 있어 두 번 읽으면 거슬립니다.

    ★ 적는 값은 **모두 자료에서 읽습니다** (주인 규칙 29).
      이름·한줄·주소를 손으로 박지 않습니다.

    ★ 크기 (주인 규칙 23 — PC·모바일 둘 다 밝힙니다)
        PC(1280·1920)  300×210px  히어로 오른쪽
        휴대폰(360·375) **안 보입니다** — 글이 밀립니다.
                        휴대폰은 머리 로고가 그 일을 합니다.
    """
    이름 = d.사이트['이름'].get(언어) or d.사이트['이름']['ko']
    한줄 = d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko']
    주소 = (d.사이트.get('주소') or '').replace('https://', '')
    # ★ 숫자는 **자료에서 셉니다** (주인 규칙 29)
    권역수 = len(d.권역들)
    포인트수 = sum(d.셈(r['id']) for r in d.권역들)
    # 카드 안에 깔 **파도** — 바다 사이트다운 느낌을 줍니다
    파도 = ('<svg class="gb-wave" viewBox="0 0 340 90" aria-hidden="true" '
            'preserveAspectRatio="none">'
            '<path d="M0 54q28-16 57 0t57 0t57 0t57 0t57 0t57 0V90H0Z" '
            'fill="#F0C173" fill-opacity=".13"/>'
            '<path d="M0 66q28-15 57 0t57 0t57 0t57 0t57 0t57 0V90H0Z" '
            'fill="#F0C173" fill-opacity=".09"/></svg>')
    return ('<aside class="g-brand" aria-hidden="true">'
            '%s'
            '<span class="gb-in">'
            '%s'
            '<b class="gb-name">%s</b>'
            '<span class="gb-url">%s</span>'
            '<span class="gb-line">%s</span>'
            '</span></aside>'
            % (파도, LOGO_BIG, esc(이름), esc(주소), esc(한줄)))


def _곧은길(쪽길, 길):
    """상대 주소. **끝 빗금을 지킵니다.**

    url.rel 은 'fish/' 를 'fish' 로 줄입니다. 그러면 서버가 한 번 더
    넘겨야 하고(301), 옛 쪽과도 달라집니다.
    """
    if 길.startswith('#'):
        return 길
    나온것 = url.rel(쪽길, 길)
    if 길.endswith('/') and not 나온것.endswith('/'):
        나온것 += '/'
    return 나온것


def 바다지도(d, 쪽길, 언어='ko'):
    것 = d.지도
    if not 것 or not 것.get('묶음'):
        return ''            # 자료가 없으면 안 그립니다 — 지어내지 않습니다
    조각 = []
    조각.append('<svg class="hm-svg" viewBox="%s" role="img" '
                'aria-label="전국 바다 지역 지도 — 지역을 누르면 그 지역으로 '
                '갑니다" xmlns="http://www.w3.org/2000/svg">'
                % esc(것.get('보임칸') or '0 0 255 353'))
    for x in (것.get('내륙') or []):
        조각.append('<polygon class="hm-inland" points="%s"/>'
                    % esc(x.get('점', '')))
    for x in (것.get('내륙글자') or []):
        조각.append('<text class="hm-inl" x="%s" y="%s">%s</text>'
                    % (x.get('x'), x.get('y'), esc(x.get('글', ''))))
    for x in (것.get('묶음') or []):
        묶 = x.get('묶음')
        조각.append('<a href="%s" class="hm-r" style="--c:%s" '
                    'aria-label="%s">'
                    % (esc(url.rel(쪽길, url.group(묶, 언어))),
                       esc(x.get('색') or '#4A6FA5'),
                       esc(x.get('읽는이름') or '')))
        for 점 in (x.get('땅') or []):
            조각.append('<polygon points="%s"/>' % esc(점))
        알 = x.get('이름표')
        if 알:
            조각.append('<rect class="hm-pill" x="%s" y="%s" width="%s" '
                        'height="%s" rx="%s"/>'
                        % (알.get('x'), 알.get('y'), 알.get('w'),
                           알.get('h'), 알.get('r')))
        글 = x.get('글')
        if 글:
            조각.append('<text class="hm-lb" x="%s" y="%s">%s</text>'
                        % (글.get('x'), 글.get('y'), esc(글.get('글', ''))))
        조각.append('</a>')
    조각.append('</svg>')
    return ''.join(조각)


def 지도차림표(d, 쪽길, 언어='ko'):
    """지도 옆 차림표. **숫자는 자료에서 셉니다** (주인 규칙 29).

    옛 쪽에는 「해루질 대상 17」·「바다 축제 190」이 박혀 있었습니다.
    지금 자료는 17·197 입니다. 축제는 이미 어긋나 있었습니다.
    """
    것 = d.지도
    줄들 = 것.get('차림표') or []
    if not 줄들:
        return ''
    채울값 = {
        '해루질수': len(d.안내('해루질')),
        '낚시수': len(d.안내('낚시')),
        '포인트수': '{:,}'.format(d.셈()),
        '축제수': len(d.축제들),
    }
    조각 = ['<div class="hm-menu">',
            '<p class="hm-menu-t">바다가자닷컴에서 볼 수 있는 것</p>']
    for 묶 in 줄들:
        조각.append('<div class="hm-g"><b>%s</b><div class="hm-b">'
                    % esc(묶.get('머리', '')))
        for 줄 in (묶.get('줄') or []):
            글 = 줄.get('글', '')
            for k, v in 채울값.items():
                글 = 글.replace('{%s}' % k, str(v))
            길 = 줄.get('길', '#')
            조각.append('<a href="%s">%s</a>'
                        % (esc(url.rel(쪽길, 길)), esc(글)))
        조각.append('</div></div>')
    조각.append('</div>')
    return ''.join(조각)


def 판번호(길):
    """파일 내용에서 판 번호를 만듭니다.

    시각을 넣으면 안 고쳐도 결과가 달라져 재현성이 깨집니다 (계약-08).
    내용이 같으면 판 번호도 같습니다.
    """
    if not os.path.exists(길):
        return '0'
    with open(길, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def esc(s):
    return html.escape(s or '', quote=True)


def 이름표(글, 꾸밈=''):
    끝 = ' ' + 꾸밈 if 꾸밈 else ''
    return '<span class="badge badge--sm%s">%s</span>' % (끝, esc(글))


def 지도주소(위도, 경도, 이름):
    """카카오맵 — 좌표가 있으면 좌표로, 없으면 이름으로 찾습니다"""
    if 위도 is not None and 경도 is not None:
        return 'https://map.kakao.com/link/map/%s,%s,%s' % (
            esc(이름), 위도, 경도)
    from urllib.parse import quote
    return 'https://map.kakao.com/?q=%s' % quote(이름 or '')


# ★ 출입 상태를 **사람 말로** — 한 곳에서만 정합니다 (계약-01)
#   2026-10-01 — 카드에서 「들어갈 수 없음」으로 고쳤는데
#   답 묶음에서 「금지」가 되살아났습니다. 두 곳에서 따로
#   적으면 언젠가 또 어긋납니다.
출입말표 = {
    '금지': '들어갈 수 없음',
    '허가필요': '허가가 있어야 함',
    '확인필요': '가기 전 확인',
    '배로만': '배로만',
    '자유': '자유',
}


def 출입말(값):
    return 출입말표.get(값, 값)


def 답묶음(d, 권역, 갈래, 포인트들, 언어='ko'):
    """**한 질문에 대한 완결된 답**을 한 덩이로 적습니다.

    ★ 2026-10-01 바깥 검수 제안 (AEO-001)

      누가 「부안에서 광어 낚시할 곳 있어?」 하고 물었을 때,
      한 쪽 안에 답이 **다 들어 있어야** 검색엔진도 AI 도
      그 쪽을 답으로 꺼냅니다.

      지금 머리에는 **풍경 설명**만 있었습니다. 아름답지만
      「광어가 몇 곳인가」에는 답하지 않습니다.

    ★ AI 용 숨김 글이 아닙니다
      **사람이 화면에서 읽는 답 = 검색엔진이 읽는 답**입니다.
      숨겨 두면 속이는 것이고, 검색엔진도 싫어합니다.

    ★ 숫자는 모두 **셉니다** (주인 규칙 29)
    """
    if not 포인트들:
        return ''
    어종셈 = {}
    지형셈 = {}
    출입셈 = {}
    for x in 포인트들:
        for 어 in (x.get('대상') or []):
            어종셈[어] = 어종셈.get(어, 0) + 1
        if x.get('지형'):
            지형셈[x['지형']] = 지형셈.get(x['지형'], 0) + 1
        출 = x.get('출입') or '자유'
        출입셈[출] = 출입셈.get(출, 0) + 1

    줄 = []
    앞선어종 = sorted(어종셈.items(), key=lambda kv: (-kv[1], kv[0]))[:4]
    if 앞선어종:
        줄.append('<li><b>많이 나오는 대상</b> %s</li>'
                  % ' · '.join('%s %d곳' % (d.어종이름(어, 언어), 수)
                               for 어, 수 in 앞선어종))
    앞선지형 = sorted(지형셈.items(), key=lambda kv: (-kv[1], kv[0]))[:4]
    if 앞선지형:
        줄.append('<li><b>자리</b> %s</li>'
                  % ' · '.join('%s %d곳' % (esc(a), b)
                               for a, b in 앞선지형))
    # ★ 못 들어가는 곳을 **먼저** 밝힙니다
    #   가서 알면 늦습니다.
    # ★ 카드에서 고친 말이 **여기서 되살아났습니다** (2026-10-01)
    #   카드는 「들어갈 수 없음」으로 고쳤는데 이 칸은 자료의
    #   「금지」를 그대로 썼습니다. 한 곳에서 고치고 다른 곳을
    #   잊은 것입니다. **말을 한 곳에 모읍니다** (계약-01).
    막힘 = [(a, b) for a, b in 출입셈.items() if a != '자유']
    if 막힘:
        줄.append('<li><b>출입</b> 자유 %d곳 · %s</li>'
                  % (출입셈.get('자유', 0),
                     ' · '.join('%s %d곳' % (esc(출입말(a)), b)
                                for a, b in sorted(막힘,
                                                   key=lambda t: -t[1]))))
    if not 줄:
        return ''
    # ★ 제목을 짧게 (2026-10-01 바깥 검수)
    #   위에 이미 「포인트 43곳」 이름표가 있고 「전체 목록 보기
    #   · 43곳」 단추도 있습니다. 또 되풀이하면 군더더기입니다.
    return ('<div class="answer"><p class="answer-h">%s</p>'
            '<ul>%s</ul></div>'
            % (esc('%d곳 한눈에 보기' % len(포인트들)), ''.join(줄)))


def 권역답묶음(d, 권역, 언어='ko'):
    """권역 쪽의 **한 질문에 대한 답** (2026-10-01 · AEO-001).

    포인트 쪽은 「부안 낚시 포인트」 하나에 답하지만, 권역 쪽은
    **「부안 바다에 가면 무엇을 할 수 있나」**에 답해야 합니다.

      낚시 43곳 · 해루질 15곳
      많이 나오는 것 — 우럭 35곳 · 감성돔 28곳 …
      물때는 위도 관측소 기준
      지금 금어기 — 전복류 · 대게 …

    ★ 금어기를 **권역 쪽에서** 보여 주는 것이 핵심입니다.
      손님은 금어기 쪽을 따로 찾아가지 않습니다. 가려는 바다를
      보다가 「아, 지금 전복은 안 되는구나」를 알아야 합니다.
    """
    셈 = {}
    어종셈 = {}
    for 갈 in ('낚시', '해루질'):
        것들 = d.포인트(권역, 갈) or []
        if 것들:
            셈[갈] = len(것들)
        for x in 것들:
            for 어 in (x.get('대상') or []):
                어종셈[어] = 어종셈.get(어, 0) + 1
    if not 셈:
        return ''

    줄 = []
    줄.append('<li><b>포인트</b> %s</li>'
              % ' · '.join('%s %d곳' % (a, b) for a, b in 셈.items()))
    앞선 = sorted(어종셈.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    if 앞선:
        줄.append('<li><b>많이 나오는 것</b> %s</li>'
                  % ' · '.join('%s %d곳' % (d.어종이름(어, 언어), 수)
                               for 어, 수 in 앞선))
    관 = ((d.권역(권역) or {}).get('물때관측소') or {}).get('이름')
    if 관:
        줄.append('<li><b>물때</b> %s 관측소 기준</li>' % esc(관))

    # ★ **그 권역에 나오는 것 가운데** 지금 금어기인 것
    #   (2026-10-01)
    #
    #   처음에는 전국 금어기를 그대로 보여 줬습니다. 그랬더니
    #   태안 쪽에 「넓미역·톳」이 떴습니다 — 제주 해조류입니다.
    #   손님에게는 쓸모없는 글자이고, 정작 태안에서 잡는 것 중
    #   무엇이 금어기인지는 안 보입니다.
    #
    #   ★ 연중 금지(명태)는 **빼고 따로** 말합니다. 섞으면
    #     「10월이라 금지」로 읽힙니다.
    걸린, 연중 = [], []
    try:
        from engine import rules as _규정
        여기어종 = set(어종셈)
        for 것, _st, 기들 in _규정.오늘금지():
            # 이 권역에서 실제로 잡는 것인가
            붙은것 = set(것.get('사이트어종') or [])
            if not (붙은것 & 여기어종):
                continue
            온해 = any(기['시작'] == '01-01' and 기['끝'] == '12-31'
                       for 기 in 기들)
            (연중 if 온해 else 걸린).append(것['법령명'])
    except Exception:
        pass
    규정길 = url.rel(url.region(권역, 언어), url.rule(언어))
    if 걸린:
        줄.append('<li><b>지금 금어기</b> %s'
                  ' <a href="%s">모두 보기</a></li>'
                  % (esc(' · '.join(걸린[:6])), esc(규정길)))
    else:
        # ★ **빈 칸을 「규정 없음」으로 보여 주지 않습니다**
        #   (합의 R-005) 아무 말도 없으면 손님은 「금어기가
        #   없구나」로 읽습니다. 금어기가 아니어도 크기 제한과
        #   지역 규정은 그대로입니다.
        # ★ 말을 법에 맞게 (2026-10-01 바깥 검수)
        #   「전국 금어기에 걸리는 것은 없습니다」는 「잡아도
        #   된다」로 읽힐 수 있습니다. **전국 공통 금어기 없음
        #   ≠ 포획 가능**입니다 (합의 R-004).
        # ★ **요약 띠는 「한눈에」 자리입니다** (2026-10-06 주인 확정 — ③안)
        #   긴 문장이 띠를 124px 로 키우고 있었습니다. 86px 로 줄였습니다.
        #   ★ **합의 R-004 는 그대로 지킵니다** — 「전국 공통 금어기 없음
        #     ≠ 포획 가능」. 그래서 「크기·지역 제한은 **남습니다**」를
        #     반드시 남깁니다. 자세한 것은 「규정 보기」가 맡습니다.
        줄.append('<li><b>금어기</b> <b>전국 공통 금어기</b> 해당 없음 ·'
                  ' 크기·지역 제한은 남습니다'
                  ' <a href="%s">규정 보기</a></li>'
                  % esc(규정길))
    if 연중:
        줄.append('<li><b>연중 금지</b> %s</li>'
                  % esc(' · '.join(연중[:4])))
    # ★ **네 칸 가로 띠로 눕힙니다** (2026-10-02 지피티 시안 v3)
    #
    #   전에는 세로로 긴 상자였습니다. 지피티 —
    #     「검색/AEO 때문에 필요한 정보는 **유지하되**, 별도의 긴
    #       박스가 아니라 2×2/4열 압축 스트립으로 넣습니다.
    #       검색엔진이 읽을 텍스트는 그대로 있고, 사람이 보는
    #       화면에서는 작고 빠르게 읽히는 대시보드가 됩니다」
    #
    #   ★ **내용은 하나도 빼지 않았습니다.** `<li>` 가 `<div>` 로
    #     바뀌었을 뿐이고 글자는 그대로입니다. 검색이 읽는 것도
    #     그대로입니다.
    칸 = []
    for 한줄 in 줄:
        속 = 한줄[len('<li>'):-len('</li>')]
        # <b>이름</b> 값  →  이름 / 값 으로 가릅니다
        m = re.match(r'<b>(.*?)</b>\s*(.*)$', 속, re.S)
        이름, 값 = (m.group(1), m.group(2)) if m else ('', 속)
        칸.append('<div class="ans-i"><div class="ans-k">%s</div>'
                  '<div class="ans-v">%s</div></div>' % (이름, 값))
    return ('<section class="answer" aria-label="%s">%s</section>'
            % (esc('이 바다에서 무엇을 할 수 있나'), ''.join(칸)))


def 축제때상태(축제):
    """축제가 **지금 어느 때인가**. 자료에 근거가 있을 때만 (2026-10-01).

    ★ 바깥 검수 지적
      「행사 종료 페이지는 반드시 상태가 보여야 합니다.
        진행 예정 / 진행 중 / 종료 / 일정 확인 필요를 **자료 근거가
        있을 때** 표시하세요. 197쪽에 기계적으로 '2026'을 붙이는
        일은 절대 하지 마십시오」

    ★ 지금 자료에는 **달만 있고 날짜·연도가 없습니다.**
      197개 가운데 68개에만 「지난해」가 있습니다. 그래서
      「2026년 10월 3일」처럼 **지어낼 수 없습니다.** 달까지만
      적고, 날짜·연도는 **주최 측 공지로 넘깁니다.**

    ★ 「이번 달」을 **쪽에 박지 않습니다** — 거짓말이 됩니다
      처음에는 만들 때 날짜와 견주어 「이번 달」을 박았습니다.
      그러면 **10월에 지어 올린 쪽이 11월에도 「이번 달」**이라고
      말합니다. 쪽은 한번 올리면 그대로 있고 날은 갑니다.
      그래서 쪽에는 **변하지 않는 「보통 N월」**만 두고,
      이번 달·다음 달은 `assets/js/fest-when.js` 가 **보는 그날**
      기준으로 더합니다. 자바스크립트가 없어도 「보통 4월」은
      그대로 읽힙니다 (계약-07 멱등성도 지킵니다).
    """
    달 = 축제.get('달')
    if not 달:
        return '일정 확인 필요', '열리는 달이 해마다 달라집니다'
    return '보통 %d월' % 달, '보통 %d월에 엽니다' % 달


def 축제바다묶음(d, 축제, 권역이름, 쪽길, 언어='ko'):
    """**축제만 보고 돌아가지 않게** 바다로 잇습니다 (2026-10-01).

    ★ 답 묶음을 쪽마다 또 만들지 않습니다
      바깥 검수 마지막 원칙 —
      「AEO 때문에 사이트 전체가 똑같은 **'답 묶음 카드 공장'**처럼
        보이지 않게 하는 것도 중요한 디자인 원칙으로 잡겠습니다」

      맞습니다. 축제 쪽의 **언제·어디·무엇을**은 이미 머리 바로 아래
      핵심정보 칸(`fest-facts`)이 답합니다. 그러니 여기서 또
      키-값 카드를 찍어내지 않고, **이 칸이 답하는 질문 하나**만
      맡습니다 — 「축제 보러 간 김에 바다에서 무엇을 할 수 있나」.

    ★ 숫자는 셉니다 (주인 규칙 29). 없으면 **없다고 적습니다.**
    """
    줄 = []
    낚시수, 해루질수 = d.셈(축제['권역'], '낚시'), d.셈(축제['권역'], '해루질')
    바다 = []
    if 낚시수:
        바다.append('<a href="%s">낚시 자리 %d곳</a>'
                    % (esc(url.rel(쪽길,
                                   url.point_list(축제['권역'], '낚시', 언어))),
                       낚시수))
    if 해루질수:
        바다.append('<a href="%s">해루질터 %d곳</a>'
                    % (esc(url.rel(쪽길,
                                   url.point_list(축제['권역'], '해루질',
                                                  언어))),
                       해루질수))
    if 바다:
        줄.append('<li><b>%s 바다</b> %s</li>'
                  % (esc(권역이름), ' · '.join(바다)))
    else:
        # ★ **없는 것도 밝힙니다.** 가서 알면 늦습니다.
        줄.append('<li><b>%s 바다</b> 저희가 확인한 낚시 자리·해루질터가 '
                  '없습니다</li>' % esc(권역이름))
    가까이 = 축제.get('가까운곳') or []
    if 가까이:
        줄.append('<li><b>축제장 가까이</b> %s</li>'
                  % ' · '.join(esc(x.split(' — ')[0]) for x in 가까이[:3]))
    다른 = [x for x in d.축제(축제['권역']) if x['id'] != 축제['id']]
    if 다른:
        달들 = sorted({x['달'] for x in 다른 if x.get('달')})
        줄.append('<li><b>같은 권역 다른 축제</b> %d개%s</li>'
                  % (len(다른),
                     ' (%s)' % ' · '.join('%d월' % m for m in 달들[:5])
                     if 달들 else ''))
    if len(줄) < 2:
        return ''
    # ★ 섹션 제목과 **같은 말을 쓰지 않습니다** (2026-10-01)
    #   위 칸 꼬리말이 이미 「축제 보러 간 김에」입니다. 답 묶음에도
    #   같은 말을 쓰니 390px 화면에 두 번 겹쳐 보였습니다.
    return ('<div class="answer"><p class="answer-h">%s</p>'
            '<ul>%s</ul></div>'
            % (esc('%s 둘레에서 할 수 있는 것' % 권역이름), ''.join(줄)))


def 카드하나(d, 차례, x, 언어='ko'):
    등급 = x.get('등급')
    등급표 = ''
    if 등급:
        # ★ 이모지를 **CSS 로 그린 점**으로 바꿉니다 (2026-10-01)
        #   🟢🟡⚪ 는 기계마다 모양도 색도 다릅니다. 안드로이드와
        #   아이폰이 다르게 그리고, 어떤 기계는 네모로 보입니다.
        #   사이트가 쓰는 색으로 직접 그리면 어디서나 같습니다.
        #   (주인 명령 — 현란하지 않게, 정보전달력이 좋게)
        글 = {'A': '확인됨', 'B': '제보 확인 중',
              'C': '미확인'}.get(등급, 등급)
        등급표 = ('<span class="badge badge--sm grade-%s">'
                  '<i class="dot" aria-hidden="true"></i>%s</span>'
                  % (등급, esc(글)))

    표들 = []
    if x.get('지형'):
        표들.append(이름표(x['지형'], 'badge--plain'))
    # ★ **못 들어가는 자리를 또렷하게** (2026-10-01 바깥 검수)
    #
    #   금지 63곳 · 허가필요 62곳 · 확인필요 56곳이 있습니다.
    #   모르고 갔다가 그냥 돌아와야 하는 자리입니다. 그런데
    #   지금은 「배로만」과 똑같은 주황 이름표 하나였습니다.
    #
    #   무게가 다릅니다 —
    #     금지·허가필요  가면 안 되거나 미리 받아야 합니다
    #     확인필요       가기 전에 전화해 봐야 합니다
    #     배로만         갈 수는 있는데 배를 타야 합니다
    if x.get('출입') and x['출입'] != '자유':
        꾸밈 = {'금지': 'badge--stop',
                '허가필요': 'badge--stop',
                '확인필요': 'badge--warn'}.get(x['출입'],
                                               'badge--orange')
        표들.append(이름표(출입말(x['출입']), 꾸밈))
    if x.get('배로가나'):
        표들.append(이름표('배로 들어감', 'badge--plain'))

    항목 = []
    if x.get('대상'):
        이름들 = ' · '.join(d.어종이름(s, 언어) for s in x['대상'])
        항목.append('<div><b>대상:</b> %s</div>' % esc(이름들))
    if x.get('철'):
        항목.append('<div><b>철:</b> %s</div>' % esc(x['철']))
    if x.get('방법'):
        항목.append('<div><b>방법:</b> %s</div>' % esc(x['방법']))

    메모 = ''
    if x.get('메모'):
        메모 = '<p class="card-note">%s</p>' % esc(x['메모'])

    좌 = x.get('좌표') or {}
    return template.그리기('_card.html', {
        '아이디': x['id'],
        '차례': 차례,
        '이름': (x['이름'].get(언어) or x['이름']['ko']),
        '위도': 좌.get('위도') if 좌.get('위도') is not None else '',
        '경도': 좌.get('경도') if 좌.get('경도') is not None else '',
        '지형코드': 지형코드.get(x.get('지형') or '', 'etc'),
        '등급표': 등급표,
        '이름표들': ''.join(표들),
        '항목들': ''.join(항목),
        '메모': 메모,
        '지도주소': 지도주소(좌.get('위도'), 좌.get('경도'),
                             x['이름'].get(언어) or x['이름']['ko']),
    }, 안쓴값알림=False)


def 구조화자료(d, 권역, 갈래, 포인트들, 쪽길):
    """검색이 읽는 자료. 숫자는 여기서도 **셉니다** (계약-04)"""
    r = d.권역(권역)
    이름 = r['이름']['ko']
    제목 = '%s %s 포인트' % (이름, 갈래)
    자리 = []
    for i, x in enumerate(포인트들, 1):
        좌 = x.get('좌표') or {}
        곳 = {'@type': 'Place', 'name': x['이름']['ko']}
        if 좌.get('위도') is not None:
            곳['geo'] = {'@type': 'GeoCoordinates',
                         'latitude': 좌['위도'], 'longitude': 좌['경도']}
        자리.append({'@type': 'ListItem', 'position': i, 'item': 곳})
    그래프 = [
        {'@type': 'WebPage', 'name': 제목,
         'url': url.full(쪽길), 'inLanguage': 'ko',
         'isPartOf': {'@type': 'WebSite', 'name': d.사이트['이름']['ko'],
                      'url': d.사이트['주소'] + '/'},
         'about': {'@type': 'AdministrativeArea', 'name': 이름}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': d.사이트['이름']['ko'],
             'item': d.사이트['주소'] + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 이름,
             'item': url.full(url.region(권역))},
            {'@type': 'ListItem', 'position': 3, 'name': 제목,
             'item': url.full(쪽길)}]},
        # numberOfItems 는 목록 길이에서 나옵니다 — 따로 세지 않습니다
        {'@type': 'ItemList', 'name': 제목,
         'numberOfItems': len(자리), 'itemListElement': 자리},
    ]
    return json.dumps({'@context': 'https://schema.org', '@graph': 그래프},
                      ensure_ascii=False, separators=(',', ':'))


def 쪽자료만들기(d, 권역, 갈래, 포인트들, 언어='ko'):
    """쪽이 쓸 자료를 JSON 으로 싣습니다.

    ★ 왜 이렇게 하나 (2026-09-26)
      옛 사이트의 지도는 HTML 을 **긁어서** 이름을 찾았습니다.

          c.querySelector('div[style*="font-weight:800"]')

      9월 20일 글자 모양을 다듬자 이 줄이 아무것도 못 찾게 되었고,
      지도 풍선에 이름 대신 "point-0" 이 6일 동안 떴습니다.

      디자인은 앞으로도 계속 바뀝니다. 그러니 **화면에서 자료를 긁지
      않습니다.** 자료를 자료로 싣고, 화면은 화면대로 둡니다.
    """
    자리 = []
    for i, x in enumerate(포인트들, 1):
        좌 = x.get('좌표') or {}
        자리.append({
            'id': x['id'],
            '차례': i,
            '이름': x['이름'].get(언어) or x['이름']['ko'],
            '위도': 좌.get('위도'),
            '경도': 좌.get('경도'),
            '지형': x.get('지형'),
            '등급': x.get('등급') or 'C',
            '대상': [d.어종이름(s, 언어) for s in (x.get('대상') or [])],
            '어림': bool(x.get('배로가나')) or x.get('출입') == '배로만',
        })
    r = d.권역(권역)
    return json.dumps({
        '권역': 권역,
        '권역이름': r['이름'].get(언어) or r['이름']['ko'],
        '갈래': 갈래,
        '지도키': (d.사이트.get('지도') or {}).get('카카오키') or '',
        '가운데': {'위도': (r.get('좌표') or {}).get('위도'),
                   '경도': (r.get('좌표') or {}).get('경도')},
        '포인트': 자리,
    }, ensure_ascii=False, separators=(',', ':'))


# ★ **남의 상표를 쓰지 않습니다** (2026-09-29 주인 지시)
#
#   전에는 여기에 이런 것이 있었습니다.
#
#       <span class="nv-n">   ← nv = naver
#       <path d="M4 3h5.3l5.1 7.6V3H20v18h-5.3L9.6 13.4V21H4z"/>
#
#   **네이버의 N 자 모양**을 그대로 쓰고 있었습니다. 검색창
#   생김새를 참고한 것까지는 좋으나, 남의 글자는 안 됩니다.
#
#   바다가자의 것으로 바꿉니다 — **물방울에 해가 뜬 모양**입니다.
#   바다로 떠나는 일을 한 눈에 보이게 한 것이고, 꼬리 로고와
#   같은 그림이라 어디서 봐도 같은 곳임을 압니다.
# ★ 머리 로고 — **「네이버에서 바다가자닷컴 검색」 안내**
#   (2026-09-29 주인 결정)
#
#   제가 「남의 상표라 못 씁니다」고 여러 번 말씀드렸고,
#   주인께서 까닭을 들어 거듭 정하셨습니다 —
#     「이건 회사 로고가 아니야 상단에 바다가자닷컴을
#       검색하라고 알려주는 로고니까」
#     「회사 정식로고는 푸터에 나오니까 상관없다고」
#
#   그래서 주인이 주신 그림 그대로 둡니다.
#   바다가자닷컴의 **정식 로고는 꼬리에 있는 물방울**입니다.
#   engine/_trademark.py 는 **이 한 자리만** 봐줍니다 —
#   다른 곳에 번지면 그것은 여전히 잡습니다.
LOGO_SVG = ('<span class="logo-mark"><svg viewBox="0 0 28 28" '
            'aria-hidden="true"><rect width="28" height="28" rx="7" '
            'fill="#03C75A"/><path d="M8.6 7.4h4.3l4.1 6.1V7.4h3.4v13.2'
            'h-4.3L12 14.5v6.1H8.6z" fill="#fff"/></svg></span>')
LOGO_GO = ('<span class="logo-go"><svg viewBox="0 0 24 24" aria-hidden="true">'
           '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5" '
           'stroke-linecap="round"/></svg></span>')
LOGO_BIG = ('<svg class="logo" width="36" height="36" viewBox="0 0 48 48" '
            'aria-hidden="true"><rect width="48" height="48" rx="13" '
            'fill="#2F5D57"/><path d="M24 43C24 43 10.5 29 10.5 19.5a13.5 '
            '13.5 0 0 1 27 0C37.5 29 24 43 24 43Z" fill="#FFFBF3"/><circle '
            'cx="24" cy="15" r="3.6" fill="#E5A94F"/><path d="M15.5 23q2.1-2.4 '
            '4.25 0t4.25 0t4.25 0t4.25 0" stroke="#2F5D57" stroke-width="2.6" '
            'fill="none" stroke-linecap="round"/></svg>')


def 사진바탕(상대):
    """사진 파일의 **실제 자리.** 못 찾으면 None — 짐작하지 않습니다.

    ★ 왜 바꿨나 (2026-09-28 — 클라우드 판정을 붙이다 드러났습니다)

        전에는 사진을 **옛 저장소**에서 가져왔습니다.

            바탕 = os.path.join(옛뿌리, 상대)
            if not os.path.isfile(바탕):
                continue          ← 조용히 넘어갑니다

        내 컴퓨터에는 옛 저장소가 있으니 잘 돌았습니다. 그런데
        깃허브 액션 러너에는 없습니다. 거기서는 **264장이 통째로
        빠지는데 아무 말이 없습니다.** 주인이 화면을 보고서야
        「사진이 한 장도 안 들어가 있다」고 잡으셨던 그 사고가,
        클라우드에서 그대로 다시 납니다.

        주인 규칙 15 그대로입니다 —
        **「저장소에 없으면 없는 것입니다」**

        그래서 사진 264장 + 걸음 카드 6장을 `assets/photo/` 안으로
        들였습니다(71MB). 이제 저장소 하나로 온전합니다.

    ★ 옛 저장소는 **뒷길**로만 둡니다
        아직 안 옮긴 사진이 있을 때를 위해서입니다.
        `BADAGAJA_OLD` 가 가리키는 자리에 있으면 그것도 씁니다.
    """
    안쪽 = os.path.join(ASSETS, 'photo', 상대.replace('/', os.sep))
    if os.path.isfile(안쪽):
        return 안쪽
    옛뿌리 = os.environ.get('BADAGAJA_OLD')
    if 옛뿌리:
        뒷길 = os.path.join(옛뿌리, 상대.replace('/', os.sep))
        if os.path.isfile(뒷길):
            return 뒷길
    return None


def 로고(뿌리, 이름, 첫쪽인가=False):
    """★ **검색창 꼴 로고** (2026-09-29 주인 지시)

    「상단 네이버박스를 로고로 만들고 인덱스페이지이동 링크까지 붙여야지」
    「이런식으로 만들어 그래야 네이버에서 검색하지」
    「마이크버튼이랑 엑스표는 지우고」

    ★ **네이버 N 자는 쓰지 않습니다.** 남의 상표입니다.
      검색창 **생김새**는 흔한 꼴이라 써도 되지만, 그 안의
      글자·로고는 그쪽 것입니다. 네모 안은 **바다가자 물방울**입니다.
      engine/_trademark.py 가 다시 새지 않게 봅니다.

    ★ 마이크·지움(X) 단추는 넣지 않습니다 — 주인 지시.
      우리 것은 **누르면 첫 화면으로 가는 로고**이지
      진짜 검색창이 아닙니다. 없는 기능을 그려 두면 속입니다.

    ★ 첫 화면에서도 **누르면 맨 위로** 갑니다.
      자기 쪽을 그대로 가리키면 눌러도 아무 일이 없어
      check_links.py 가 잡습니다. 맨 위로 보내면
      눌리는 느낌도 살고 하는 일도 있습니다.
    """
    속 = '%s<span class="mark">%s</span>%s' % (LOGO_SVG, esc(이름), LOGO_GO)
    길 = '#top' if 첫쪽인가 else 뿌리
    잡 = ('%s 맨 위로' % 이름) if 첫쪽인가 else ('%s 홈' % 이름)
    return ('<a class="brand" href="%s" aria-label="%s">%s</a>'
            % (esc(길), esc(잡), 속))


def 꼬리로고(뿌리, 이름, 첫쪽인가=False):
    """★ **꼬리에는 정식 로고**가 나옵니다 (2026-09-29 주인 말씀)

    「회사 정식로고는 푸터에 나오니까 상관없다고」

    ★ 머리와 **다른 차림표(class)** 를 씁니다.
      전에는 둘 다 `brand` 라, 머리를 검색창 꼴로 바꾸자
      **꼬리 정식 로고에도 초록 알약이 붙었습니다.**
      머리는 「네이버에서 검색하세요」 안내,
      꼬리는 바다가자닷컴 **그 자체**입니다. 달라야 합니다.
    """
    속 = '%s<span class="mark">%s</span>' % (LOGO_BIG, esc(이름))
    if 첫쪽인가:
        return '<span class="brand brand--foot">%s</span>' % 속
    return ('<a class="brand brand--foot" href="%s" aria-label="%s 홈">%s</a>'
            % (esc(뿌리), esc(이름), 속))


# ── 언어 고르기 ────────────────────────────────────────────
#
# ★ 떨어진 것을 **조용히 두지 않습니다** (2026-09-26 바깥 검수 지적)
#
#     「중국어 데이터가 없는 경우 한국어가 조용히 출력되는지,
#       아니면 의도한 fallback 이 작동하는지를 명확히 해야 합니다」
#
#   맞는 지적입니다. 지금 자료는 이렇습니다.
#       권역 이름 57개    중국어 있음 100%
#       포인트 이름 3,603개  중국어 **0%**
#
#   그래서 중국어 포인트 쪽을 만들면 이름이 전부 한국어로 나옵니다.
#   그것 자체는 나쁘지 않습니다 — 지명은 현지에서 물어볼 때 한국어가
#   필요하고, 옛 사이트도 그렇게 했습니다. 문제는 **밝히지 않는 것**입니다.
#
#   그래서 둘을 합니다.
#     · lang="ko" 를 달아 브라우저·검색엔진·읽어 주는 장치가 알게 합니다
#     · 몇 번 떨어졌는지 세어 check_i18n.py 가 잽니다
떨어짐 = collections.Counter()


def 말(값, 언어='ko'):
    """그 언어의 값. 없으면 한국어로 떨어집니다 (세어 둡니다)."""
    if not isinstance(값, dict):
        return 값 or ''
    v = 값.get(언어)
    if v:
        return v
    if 언어 != 'ko':
        떨어짐[언어] += 1
    return 값.get('ko') or ''


def 말표시(값, 언어='ko'):
    """화면에 낼 값. 떨어졌으면 lang="ko" 로 감싸 **밝힙니다.**"""
    if not isinstance(값, dict):
        return esc(값 or '')
    v = 값.get(언어)
    if v:
        return esc(v)
    ko = 값.get('ko') or ''
    if 언어 == 'ko' or not ko:
        return esc(ko)
    떨어짐[언어] += 1
    return '<span lang="ko">%s</span>' % esc(ko)


def 낱말(d, 한국말, 언어='ko'):
    """낱말표(data/raw/zh.json)에서 옮긴 말을 찾습니다.

    어종·지형처럼 **정해진 낱말**에 씁니다. 표에 없으면 한국어
    그대로 두고 셉니다 — 지어내면 틀린 중국어가 조용히 섞입니다.
    """
    if 언어 == 'ko' or not 한국말:
        return 한국말 or ''
    표 = d.중국어낱말 if hasattr(d, '중국어낱말') else {}
    v = (표.get('어종표') or {}).get(한국말)
    if not v:
        v = ((표.get('표') or {}).get('낱말') or {}).get(한국말)
    if v:
        return v
    떨어짐[언어] += 1
    return 한국말


_기준일캐시 = {}


def 기준일조각(갈래='포인트'):
    """머리에 붙는 **짧은** 기준일 이름표.

    ★ 2026-10-01 주인 지시 — 「기준일 26년 9월 이렇게만 적어」
      전에는 쪽 맨 아래에 긴 문장으로 있었습니다. 거기까지
      내려간 사람만 보았고, 뒷말은 위쪽 띠와 겹쳤습니다.
      **읽기 전에** 언제 것인지 알아야 값이 있습니다.
    """
    때 = 자료기준일(갈래)          # 「2026년 9월」
    m = re.match(r'(\d{4})년\s*(\d{1,2})월', 때 or '')
    if m:
        return '기준일 %s년 %s월' % (m.group(1)[2:], m.group(2))
    return '기준일 %s' % (때 or '')


def 자료기준일(갈래='포인트'):
    """그 자료를 **마지막으로 고친 달**. git 기록에서 읽습니다.

    ★ 손으로 적지 않습니다 (주인 규칙 30 · 2026-09-27 주인 지시)

        전에는 「2026년 9월」이 코드에 박혀 있었습니다.
        10월이 되면 97쪽이 한꺼번에 거짓말을 합니다.
        누가 고쳐 주기를 기다리는 값은 언젠가 반드시 낡습니다.

        「3,603곳을 매달 다시 확인할 수는 없습니다. 그러나
          **언제 것인지 밝히면 최신이 아니어도 정직합니다.**」

    ★ 계약-08(결과물에 시각을 넣지 않는다)과 어긋나지 않습니다
        넣는 것은 **만든 시각**이 아니라 **자료를 고친 달**입니다.
        자료가 안 바뀌면 이 값도 안 바뀝니다 — 재현성이 지켜집니다.
    """
    if 갈래 in _기준일캐시:
        return _기준일캐시[갈래]
    무늬 = {'포인트': 'data/raw/points',
            '축제': 'data/raw/festivals',
            '어종': 'data/raw/guide.json',
            '여행': 'data/raw/travel'}.get(갈래, 'data/raw/points')
    값 = None
    try:
        r = subprocess.run(
            ['git', 'log', '-1', '--format=%cI', '--', 무늬],
            cwd=ROOT, capture_output=True, text=True, timeout=30)
        s = (r.stdout or '').strip()
        if s:
            값 = '%s년 %d월' % (s[:4], int(s[5:7]))
    except (OSError, ValueError):
        값 = None
    if not 값:
        # git 을 못 읽으면 **오늘**로 둡니다. 박아 둔 값보다 낫습니다
        이제 = datetime.date.today()
        값 = '%d년 %d월' % (이제.year, 이제.month)
    _기준일캐시[갈래] = 값
    return 값


def 첫화면제목(d, 언어='ko'):
    """첫 화면 제목 — 자료의 틀에 **자료에서 센 수**를 채웁니다.

    ★ 「이상」으로 적습니다 (2026-09-27 주인 뜻)

        포인트 수는 이 사이트의 핵심 강점이라 제목에 넣습니다.
        다만 「3,603곳」이라고 적으면 자료가 늘 때마다 제목이
        바뀌고, 검색 제목을 자주 바꾸면 불이익입니다.

        「3,600곳 이상」이면 3,650 이 되든 3,699 가 되든 그대로입니다.
        강점은 살리고, 자주 바꾸는 문제는 없앱니다.

    ★ 숫자는 **자료에서 셉니다** (주인 규칙 29)
        **500단위**로 내려 채웁니다. 손으로 적지 않습니다.

        100단위로 내리면 3,603 → 3,600 이라 여유가 3곳뿐입니다.
        포인트를 몇 개만 정리해도 「3,600곳 이상」이 거짓이 되고,
        그때 제목을 또 고쳐야 합니다. 500단위면 3,500 이라
        100곳 넘게 줄어도 참입니다 (2026-09-27 주인 지시).
    """
    틀 = 말(d.사이트.get('첫화면제목'), 언어)
    if not 틀:
        return '%s — 물때·해루질·낚시 포인트' % d.사이트['이름']['ko']
    내림 = (d.셈() // 500) * 500
    return 틀.replace('{포인트수}', format(내림, ','))


def 축제설명(이름, 권역이름, 한줄):
    """축제 쪽 설명 — **쪽마다 달라야** 하고, **같은 말이 3번 넘으면 안 됩니다.**

    ★ 두 가지를 한꺼번에 지켜야 합니다 (2026-09-27 check_seo 가 잡음)

        (1) 자료의 「한줄」이 여러 축제에 같은 값인 경우가 있습니다
            「해수욕 · 해양레저 성수기 시작」이 보성·여수 두 쪽에 있었습니다.
            → 축제 이름을 넣어 가릅니다.

        (2) 그렇다고 무턱대고 권역을 붙이면 되풀이가 생깁니다
            「동해 무릉제(동해) — 동해 시민이 …」 — 「동해」가 세 번.
            네이버 가이드는 되풀이에 불이익을 줍니다.
            → 이름이나 한줄에 권역이 이미 있으면 안 붙입니다.
    """
    한줄 = (한줄 or '').strip()
    있는말 = '%s %s' % (이름, 한줄)
    머리 = 이름 if 권역이름 in 있는말 else '%s(%s)' % (이름, 권역이름)
    if not 한줄:
        return ('%s 일정과 가는 길을 안내합니다.' % 머리)[:110]
    # 한줄이 이름으로 시작하면 이름을 또 안 붙입니다
    if 한줄.startswith(이름):
        return 한줄[:110]
    return ('%s — %s' % (머리, 한줄))[:110]



def 포인트설명(이름, 갈래, 수, 포인트들, 언어, 한도=80):
    """포인트 쪽 설명. **80자를 안 넘습니다.**

    ★ 왜 (2026-09-28 — check_seo 가 25쪽을 잡았습니다)

      자리 이름을 늘 셋씩 늘어놓다 보니 이름이 긴 권역에서
      81~84자로 넘쳤습니다.

          보령 해루질포인트 20곳. 군헌 갯벌체험장(대천) ·
          무창포 신비의 바닷길(석대도) · 독산(홀뫼)해수욕장 등 …   84자

      주인 규칙 28 — 검색 가이드에 맞춥니다. 설명이 길면 잘립니다.

    ★ **글을 자르지 않습니다.** 말이 중간에 끊기면 검색에서도
      손님에게도 나쁩니다. 대신 **늘어놓을 이름을 하나씩 덜어 냅니다.**
      이름이 하나도 안 들어가면 그 구절을 통째로 뺍니다.
    """
    바탕 = '%s %s포인트 %d곳.' % (이름, 갈래, 수)
    꼬리 = '자리와 채비, 물때·금어기를 안내합니다.'
    for 몇 in (3, 2, 1):
        앞선곳 = 겹치지않는이름(포인트들, 몇, 언어)
        if not 앞선곳:
            break
        글 = '%s %s 등 %s' % (바탕, 앞선곳, 꼬리)
        if len(글) <= 한도:
            return 글
    return '%s %s' % (바탕, 꼬리)


def 겹치지않는이름(포인트들, 몇개, 언어='ko'):
    """제목에 넣을 대표 포인트 이름 — **같은 낱말이 겹치지 않게** 고릅니다.

    ★ 왜 고르나 (2026-09-27 engine/check_seo.py 가 잡음)
        전에는 앞 세 곳을 그대로 이어 붙였습니다. 그랬더니

            신안 해루질포인트 34곳 — 고이도 **갯벌** · 도초도 시목해변
            **갯벌** · 매화도 **갯벌**

        「갯벌」이 세 번입니다. 네이버 가이드는 제목·설명에 같은 말을
        되풀이하면 **불이익**을 준다고 합니다 (주인 규칙 28).
        22쪽이 이 모양이었습니다.

        차례는 자료 차례를 따릅니다 — 앞에서부터 보되, 이미 쓴 낱말이
        들어간 이름은 건너뜁니다. 그래야 늘 같은 결과가 나옵니다 (계약-07).
    """
    쓴낱말 = set()
    고른것 = []
    남은것 = []
    for x in 포인트들:
        이름 = 말(x.get('이름'), 언어)
        if not 이름:
            continue
        낱말 = set(w for w in re.findall(r'[가-힣A-Za-z]{2,}', 이름))
        if 낱말 & 쓴낱말:
            남은것.append(이름)
            continue
        고른것.append(이름)
        쓴낱말 |= 낱말
        if len(고른것) >= 몇개:
            break
    # 겹치지 않는 것이 모자라면 남은 것으로 채웁니다
    for 이름 in 남은것:
        if len(고른것) >= 몇개:
            break
        고른것.append(이름)
    return ' · '.join(고른것)


def 언어연결(d, 주소내기):
    """hreflang — **실제로 만드는 언어만** 냅니다.

    ★ 왜 자료에서 보나 (2026-09-26)
        중국어 쪽을 하나도 안 만들었는데 416쪽 전부가
        hreflang="zh-Hans" 로 **없는 쪽**을 가리키고 있었습니다.
        구글에 「중국어판이 여기 있다」고 알려 놓고 404 를 내면
        검색에 해롭습니다. 만든 언어만 냅니다.

        만들 언어는 data/raw/site.json 의 「만들언어」 한 곳에서
        정합니다. 중국어를 만들기 시작하면 거기에 한 줄 더합니다.

    주소내기 — 언어 코드를 받아 그 언어 쪽 주소를 돌려주는 함수
    """
    코드표 = {'ko': 'ko', 'zh': 'zh-Hans'}
    만들것 = ((d.사이트.get('만들언어') or {}).get('쪽')) or ['ko']
    만들것 = [x for x in 만들것 if x in 코드표]
    if len(만들것) < 2:
        return ''          # 한 언어뿐이면 hreflang 이 필요 없습니다
    return '\n'.join(
        '<link rel="alternate" hreflang="%s" href="%s">'
        % (코드표[언], url.full(주소내기(언)))
        for 언 in 만들것)


def _광고자료():
    """data/raw/ads.json. 없으면 광고 없는 것으로 봅니다."""
    return io.read_json(os.path.join(DATA, 'raw', 'ads.json'), default={})


def 광고칸(쪽갈래, 권역=None):
    """그 갈래 쪽에 들어갈 광고 자리.

    ★ **권역별 광고** (2026-09-30 주인 지시 — 제주패스)
      자리에 `권역` 목록이 있으면 **그 권역에서만** 넣습니다.
      같은 쪽갈래·기기에 여럿이 맞으면 **권역을 집은 것이 이깁니다** —
      제주에서는 제주패스, 나머지는 쿠팡. 둘 다 넣으면 어지럽습니다.

    ★ 자리만 만들고 **내용은 안 넣습니다.** 실제 광고는 assets/js/ads.js
      가 화면에서 그립니다. 쪽 안에 광고 코드를 박으면, 광고를 끄거나
      바꿀 때 500여 쪽을 다시 만들어야 합니다.

    ★ hidden 으로 시작합니다 — 광고가 실제로 들어왔을 때만 폅니다.
      광고는 바깥 것이라 언제든 안 올 수 있습니다. 안 왔을 때 빈 상자가
      남으면 쪽이 어색합니다 (계약-23).

    ★ PC 와 휴대폰 자리를 따로 둡니다 (주인 규칙 23)
      크기가 다른 배너를 각각 싣습니다. CSS 가 기기에 맞는 것만 보입니다.
    """
    a = _광고자료()
    if not a.get('켬'):
        return ''
    # ★ **권역을 집은 자리가 있으면 그것만** 씁니다 (2026-09-30)
    #   기기마다 따로 봅니다 — PC 는 제주패스인데 휴대폰은 쿠팡,
    #   같은 일이 생기면 안 됩니다.
    쓸것 = {}
    for 이름 in sorted((a.get('자리') or {})):
        if 이름.startswith('_'):
            continue
        자리 = a['자리'][이름]
        if not 자리.get('켬') or 자리.get('쪽갈래') != 쪽갈래:
            continue
        집은것 = 자리.get('권역')
        if 집은것 and 권역 not in 집은것:
            continue                      # 이 권역 것이 아닙니다
        기기 = 자리.get('기기') or 'all'
        앞 = 쓸것.get(기기)
        if 앞 and not 집은것:
            continue                      # 이미 딱 집은 것이 있습니다
        if 앞 and 집은것 and 앞[1].get('권역'):
            continue                      # 집은 것끼리는 먼저 온 것
        쓸것[기기] = (이름, 자리)

    나옴 = []
    for 기기 in sorted(쓸것):
        이름, 자리 = 쓸것[기기]
        # ★ hidden 을 쓰지 않습니다 (2026-09-26 check_ads.py 가 잡음)
        #   hidden 은 display:none 이라 IntersectionObserver 가
        #   **영영 못 봅니다.** 광고가 한 번도 안 떴습니다.
        #   대신 CSS 가 높이를 0 으로 두었다가, 들어오면 폅니다.
        # ★ 카드 자리는 **격자 칸 안**에 들어갑니다 (2026-10-01)
        #   바깥 여백과 `height:0` 이 격자를 밀어내므로 따로 둡니다.
        덧 = ' ad-slot--card' if 쪽갈래 == '묶음카드' else ''
        나옴.append('<aside class="ad-slot%s" data-ad-slot="%s" '
                    'data-ad-device="%s"></aside>'
                    % (덧, esc(이름), esc(자리.get('기기') or 'all')))
    return ''.join(나옴)


def 광고자료쓰기():
    """assets/js/ads-data.js 를 만듭니다 — 화면이 읽는 광고 자료.

    ★ 왜 자료를 따로 내보내나
      쪽마다 광고 코드를 박으면, 배너 하나를 바꿀 때 500여 쪽을
      다시 만들어야 합니다. 자료를 한 파일로 내보내면 그 파일만
      바뀝니다 (옛 사이트가 겪은 일입니다).

    ★ 밖으로 내는 것은 **화면에 필요한 것만**입니다.
      메모·근거 같은 것은 안 냅니다 (주인 규칙 11 — 근거 자료는
      웹에 내지 않습니다).
    """
    a = _광고자료()
    낼것 = {'켬': bool(a.get('켬')), '표시': {}, '배너': {}, '자리': {}}
    표시 = a.get('표시') or {}
    # ★ 제휴문구는 **반드시** 나가야 합니다 (2026-09-30 주인 지시)
    #   안 나가면 대가를 받고도 밝히지 않은 것이 됩니다.
    for k in ('배지', '배지_zh', '글', '글_zh',
              '제휴문구', '제휴문구_zh'):
        if 표시.get(k):
            낼것['표시'][k] = 표시[k]
    for 이름, b in sorted((a.get('배너') or {}).items()):
        if 이름.startswith('_'):
            continue
        낼것['배너'][이름] = {
            '제공': b.get('제공'), 'id': b.get('id'), '틀': b.get('틀'),
            '추적': b.get('추적'), '가로': b.get('가로'), '세로': b.get('세로'),
        }
        # ★ 링크 배너에 필요한 것 (2026-09-30)
        #   메모·근거는 그대로 안 냅니다 (주인 규칙 11)
        for k in ('주소', '제휴', '이름', '한줄', '풀이', '단추'):
            if b.get(k) is not None:
                낼것['배너'][이름][k] = b[k]
    for 이름, s in sorted((a.get('자리') or {}).items()):
        if 이름.startswith('_'):
            continue
        낼것['자리'][이름] = {'켬': bool(s.get('켬')), '기기': s.get('기기'),
                              '배너': s.get('배너')}
    글 = ('/* 광고 자료 — engine/build.py 가 data/raw/ads.json 에서 만듭니다.\n'
          '   손으로 고치지 마세요. 고칠 곳은 data/raw/ads.json 입니다. */\n'
          'window.바다가자광고 = %s;\n'
          % json.dumps(낼것, ensure_ascii=False, indent=2, sort_keys=True))
    io.write(os.path.join(ASSETS, 'js', 'ads-data.js'), 글)
    켠자리 = sum(1 for v in 낼것['자리'].values() if v['켬'])
    print('  광고 자료 — 배너 %d개 · 켠 자리 %d개%s'
          % (len(낼것['배너']), 켠자리, '' if 낼것['켬'] else '  (광고 꺼짐)'))


def 광고움직임(쪽길, 쪽갈래, 권역=None):
    """그 쪽에 광고 자리가 있을 때만 광고 움직임을 부릅니다.

    자리가 없는 쪽에 스크립트를 부르면 쓸데없이 내려받게 됩니다.

    ★ **권역을 함께 물어야 합니다** (2026-10-01)
      권역을 집은 자리(제주패스)는 권역 없이 물으면 안 걸립니다.
      그러면 자리는 쪽에 들어갔는데 그리는 코드가 안 실려
      **영영 빈 칸**이 됩니다. `광고칸()` 과 똑같이 묻습니다.
    """
    if not 광고칸(쪽갈래, 권역):
        return ''
    return ('\n  <script src="%s" defer></script>'
            '\n  <script src="%s" defer></script>'
            % (url.asset('assets/js/ads-data.js', 쪽길,
                         판번호(os.path.join(ASSETS, 'js', 'ads-data.js'))),
               url.asset('assets/js/ads.js', 쪽길,
                         판번호(os.path.join(ASSETS, 'js', 'ads.js')))))


def 꼬리메뉴(d, 쪽길, 언어='ko'):
    """꼬리 메뉴.

    ★ 지금 보고 있는 쪽은 링크로 두지 않습니다 (2026-09-26).
      눌러도 아무 일이 없어 혼란스럽습니다.
      engine/check_links.py 가 「자기 자신을 가리키는 링크」로 잡습니다.
    """
    여기 = 쪽길.replace(os.sep, '/')
    칸들 = []
    for 칸 in d.사이트['꼬리메뉴']:
        토막 = []
        for x in 칸['고리']:
            글 = esc(x['글'].get(언어) or x['글']['ko'])
            간곳 = x['길'].rstrip('/')
            자기쪽 = (여기 == x['길']
                      or 여기 == 간곳 + '/index.html'
                      or 여기 == 간곳)
            if 자기쪽:
                토막.append('<span class="here" aria-current="page">%s</span>'
                            % 글)
            else:
                토막.append('<a href="%s">%s</a>'
                            % (esc(url.rel(쪽길, x['길'])), 글))
        고리 = ''.join(토막)
        칸들.append('<div class="fn-col"><h2>%s</h2>%s</div>'
                    % (esc(칸['제목'].get(언어) or 칸['제목']['ko']), 고리))
    return ''.join(칸들)


def 포인트쪽(d, 권역, 갈래, 언어='ko'):
    """포인트 목록 쪽 하나를 만듭니다"""
    r = d.권역(권역)
    이름 = r['이름'].get(언어) or r['이름']['ko']
    포인트들 = d.포인트(권역, 갈래)
    수 = len(포인트들)          # ★ 셉니다 (계약-06)
    쪽길 = url.point_list(권역, 갈래, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')

    # 제목에 들어갈 대표 포인트 세 곳
    앞선곳 = 겹치지않는이름(포인트들, 3, 언어)
    바다 = d.바다안내(권역, 언어)

    머리표 = ''.join([
        이름표('%s %d권역' % (d.색인['묶음이름'][r['묶음']]['ko'],
                              sum(1 for y in d.권역들 if y['묶음'] == r['묶음'])),
               'badge--orange'),
        이름표('포인트 %d곳' % 수),
        이름표('현장 확인 필수', 'badge--green'),
    ])

    카드들 = '\n'.join(카드하나(d, i, x, 언어)
                       for i, x in enumerate(포인트들, 1))

    걸러내기 = ''.join(
        '<button type="button" aria-pressed="%s" data-filter="%s">%s</button>'
        % ('true' if 값 == '전체' else 'false', esc(값), esc(값))
        for 값 in ['전체'] + sorted(set(x['지형'] for x in 포인트들 if x.get('지형'))))

    # ★ **어종으로 거르기** (2026-10-01 주인 확정 — 104종 다 넣기)
    #
    #   손님은 「갯바위냐 방파제냐」보다 **「우럭이 나오느냐」**를
    #   먼저 묻습니다. 자료에 대상어종이 이미 있는데 거르개가
    #   지형뿐이라 그 물음에 답할 수 없었습니다.
    #
    #   ★ 단추를 다 펼치지 않습니다 (바깥 검수 의견)
    #     104종을 같은 무게로 늘어놓으면 전화번호부가 됩니다.
    #     **많이 나오는 여섯**만 보이고 나머지는 접어 둡니다.
    #     찾는 어종이 없으면 위 찾기칸에 이름을 치면 됩니다.
    어종셈 = {}
    for x in 포인트들:
        for 어 in (x.get('대상') or []):
            어종셈[어] = 어종셈.get(어, 0) + 1
    어종거르개 = ''
    if 어종셈:
        차례 = sorted(어종셈.items(), key=lambda kv: (-kv[1], kv[0]))
        앞선것, 남은것 = 차례[:6], 차례[6:]

        def _단추(어, 수, 숨김=False):
            return ('<button type="button" aria-pressed="false"'
                    ' data-fish="%s"%s>%s <i>%d</i></button>'
                    % (esc(어), ' hidden' if 숨김 else '',
                       esc(d.어종이름(어, 언어)), 수))
        단추들 = ('<button type="button" aria-pressed="true"'
                  ' data-fish="전체">전체</button>')
        단추들 += ''.join(_단추(어, 수) for 어, 수 in 앞선것)
        단추들 += ''.join(_단추(어, 수, True) for 어, 수 in 남은것)
        더보기 = ''
        if 남은것:
            더보기 = ('<button type="button" class="fish-more"'
                      ' data-more>어종 %d가지 더 보기</button>'
                      % len(남은것))
        어종거르개 = ('<div class="filters filters--fish" id="fishFilter"'
                      ' role="group" aria-label="어종으로 거르기">'
                      '%s%s</div>' % (단추들, 더보기))

    쪽자료 = 쪽자료만들기(d, 권역, 갈래, 포인트들, 언어)

    값 = {
        # ── 머리말
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s %s포인트 %d곳 — %s | %s'
                % (이름, 갈래, 수, 앞선곳, d.사이트['이름']['ko']),
        '짧은제목': '%s %s포인트 %d곳 — %s' % (이름, 갈래, 수, 앞선곳),
        # ★ 80자를 안 넘게 **자리 이름 수를 줄입니다** (2026-09-28)
        #   자르지 않습니다 — 말이 중간에 끊기면 검색에서도 손님에게도
        #   나쁩니다. 대신 늘어놓을 이름을 하나씩 덜어 냅니다.
        '설명': 포인트설명(이름, 갈래, 수, 포인트들, 언어),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 사진주소(d, 대표사진(d, 권역=권역)),
        '대표사진자리': 사진자리(d, 대표사진(d, 권역=권역), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.point_list(권역, 갈래, 언)),
        '구조화자료': 구조화자료(d, 권역, 갈래, 포인트들, 쪽길),
        # ── 머리
        '머리말': '%s %s 안내' % (이름, 갈래),
        '기준일조각': 기준일조각(),
        '머리이름표': 머리표,
        '돌아갈주소': url.rel(쪽길, url.region(권역, 언어)),
        '돌아갈글': '%s 권역으로' % 이름,
        '권역이름': 이름,
        '메일': d.사이트['메일'],
        # ── 첫 화면
        # ★ **「현장 기록」이라 하지 않습니다** (2026-10-07 바깥 전수감사)
        #   「가서 하나씩 적어 왔다」로 읽힙니다. 저희는 공개 자료를
        #   **정리**합니다 — About 쪽도 그렇게 적혀 있습니다.
        #   두 쪽이 서로 다른 말을 하면 사이트 전체를 못 믿게 됩니다.
        '머리이름표글': '%s 직접 정리한 %s %s 포인트 안내' % (
            조사(d.사이트['이름']['ko'], '이'), 이름, 갈래),
        '큰제목': '%s %s포인트' % (이름, 갈래),
        '큰제목뒷줄': '물때를 읽다',
        '소개글': (r.get('안내') or r.get('소개') or
                   '%s의 %s 자리를 한눈에 모았습니다.' % (이름, 갈래)),
        '포인트수': 수,
        # ── 바다 안내
        '바다제목': 바다['제목'],
        '바다글': 바다['글'],
        '바다조심': 바다['조심'],
        # ── 목록
        '권역': 권역,
        '갈래': 갈래,
        '갈래코드': url.갈래주소[갈래],
        '안내글': (r.get('포인트안내') or
                   '자리마다 어촌계·지자체 규정이 다릅니다. 가기 전에 반드시 확인하세요.'),
        '답묶음': 답묶음(d, 권역, 갈래, 포인트들, 언어),
        '걸러내기': 걸러내기,
        '어종거르개': 어종거르개,
        '카드들': 카드들,
        '광고칸': 광고칸('포인트목록'),
        # ★ 기준일은 머리로 올렸습니다 (2026-10-01 주인 지시)
        '기준일안내': '',
        # ── 꼬리
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': (
            '<script type="application/json" id="쪽자료">%s</script>\n'
            # ★ map-type.js 를 **먼저** 실어야 합니다 (2026-09-29)
            #   point-list.js 가 window.BADAGAJA_MAPTYPE 를 찾습니다.
            '<script src="%s" defer></script>'
            '<script src="%s" defer></script>'
            # ★ **카카오내비 길안내** (2026-09-30 — 옛 사이트에서 되살림)
            #   포인트 카드에서 곧장 출발합니다. 휴대폰에서만 보입니다.
            '<script src="%s" defer></script>'
            % (쪽자료.replace('</', '<\\/'),
               url.asset('assets/js/map-type.js', 쪽길,
                         판번호(os.path.join(ASSETS, 'js', 'map-type.js'))),
               url.asset('assets/js/point-list.js', 쪽길,
                         판번호(os.path.join(ASSETS, 'js', 'point-list.js'))),
               url.asset('assets/js/navi.js', 쪽길,
                         판번호(os.path.join(ASSETS, 'js', 'navi.js'))))
            + 광고움직임(쪽길, '포인트목록')),
    }
    return 쪽길, template.그리기('point-list.html', 값)


def 권역쪽(d, 권역, 언어='ko'):
    """권역 첫 쪽 — 그 권역으로 들어오는 문입니다"""
    r = d.권역(권역)
    v = d.여행(권역)
    이름 = r['이름'].get(언어) or r['이름']['ko']
    쪽길 = url.region(권역, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')

    낚시수, 해루질수 = d.셈(권역, '낚시'), d.셈(권역, '해루질')
    모두 = 낚시수 + 해루질수

    # ── 빠른 이동: 내용이 있는 칸만 (계약-11)
    칸들 = [('points', '포인트', 모두),
            # 물때는 늘 있습니다 — 옛 쪽에도 있던 칸입니다 (2026-09-27)
            ('tide', '물때', 1),
            ('catch', '제철 어종', len(v['어종'])),
            ('eat', '먹거리', len(v['먹거리'])),
            ('spot', '해안 명소', len(v['명소'])),
            ('festival', '축제', len(v['축제'])),
            ('course', '여행 코스', len(v['코스']))]
    # ★ 권역 쪽은 **칩 한 줄**입니다 (2026-10-02 지피티 시안 v3)
    빠른이동 = 빠른이동칸(칸들, 칩=True)

    # ── 포인트 칸 — ★ **배너로 돌려놓습니다** (2026-09-29 주인 지시)
    #
    #   「이것도 전처럼 베너효과를 좀 주자 둘이 색을 달리해서」
    #   「첫번째 도전을 참고해」
    #
    #   옛 쪽(css/style.css `.sinan-banner`)은 두 칸이 **색이 달랐습니다.**
    #       낚시    짙은 초록  #163F3B → #2E7A70
    #       해루질  주황       #A9621F → #E0922F
    #   숫자를 큼직한 상자에 넣고, 오른쪽에 「더보기」 단추를 두었습니다.
    #
    #   새 쪽은 둘 다 흰 카드라 **어느 쪽이 무엇인지 한눈에 안 보였습니다.**
    #   색은 글보다 빨리 읽힙니다 (규칙 6-1 — 사람은 눈으로 봅니다).
    포인트칸 = []
    for 갈래, 수, 반, 뭐하는 in (
            ('낚시', 낚시수, 'fish', '방파제·갯바위·선착장'),
            ('해루질', 해루질수, 'gleaning', '갯벌·갯바위·체험마을')):
        if not 수:
            continue
        포인트칸.append(
            '<a class="pbn pbn--%s" href="%s">'
            '<span class="pbn-n"><b>%d</b><i>%s 포인트</i></span>'
            '<span class="pbn-mid"><b>%s · %s %s</b>'
            '<i>%s에서 %s 할 수 있는 자리를 지도와 목록으로 안내합니다.</i>'
            '</span>'
            '<span class="pbn-go">포인트 보기 <i>→</i></span></a>'
            % (반, esc(url.rel(쪽길, url.point_list(권역, 갈래, 언어))),
               수, esc(갈래), esc(갈래), esc(이름), esc(뭐하는),
               esc(이름), esc(갈래)))
    if not 포인트칸:
        포인트칸.append('<p class="notice">이 권역은 아직 포인트를 '
                        '정리하는 중입니다.</p>')

    # ★ **지도를 배너 위에** 둡니다 (2026-10-02 지피티 시안)
    #   「주인이 특히 원하는 것은 지도 + 사진카드 + 짧은 스크롤입니다」
    #   배너 둘은 그대로 둡니다 — 지도가 안 떠도 고를 수 있어야
    #   합니다 (계약-23). 지피티도 못 박았습니다 —
    #   「지도 실패 시 기존 낚시/해루질 링크는 반드시 남겨」
    #
    #   ★ **`.two-up` 안에 넣으면 안 됩니다** (2026-10-02 겪음)
    #     포인트칸은 틀에서 `<div class="two-up">` 에 들어갑니다.
    #     지도를 거기 끼웠더니 격자가 자식 **셋**을 3열로 쪼개
    #     PC 에서 지도가 손가락만큼 좁아지고 배너 글자가 세로로
    #     쌓였습니다. 틀에 `{{{포인트지도}}}` 자리를 따로 뒀습니다.
    포인트지도 = 권역지도(d, 권역, 쪽길, 언어)

    # ── 통제구역 — 있으면 눈에 띄게
    통제 = ''
    if v['통제']:
        줄 = ''.join('<li><b>%s</b> %s</li>'
                     % (esc(x['곳']), esc((x['내용'] or {}).get('ko')))
                     for x in v['통제'])
        통제 = ('<div class="warn-box"><h3>못 들어가는 곳 · 조심할 곳</h3>'
                '<ul>%s</ul>'
                '<p class="warn-small">해경이 지정한 출입통제 장소에 '
                '들어가면 과태료 대상입니다.</p></div>' % 줄)

    # ★ 안전 안내 — **권역 57곳 모두**에 붙입니다 (2026-09-28 주인 지적)
    #
    #   옛 쪽에 있던 것이 새 쪽에서 통째로 빠져 있었습니다.
    #   전수 검사(engine/check_design.py)가 잡았습니다.
    #
    #       테트라포드  4 → 0
    #       구명조끼    2 → 0
    #       기상특보    5 → 0
    #
    #   **이건 디자인이 아닙니다.** 사람이 다치고 과태료를 뭅니다.
    #   갯바위는 물이끼와 따개비로 미끄럽고, 테트라포드 사이에
    #   빠지면 혼자 못 올라옵니다.
    #
    #   권역마다 다른 내용이 아니므로 자료에 넣지 않고 여기 둡니다.
    #   (자료에 57번 같은 글을 적으면 한 곳을 고치고 나머지를
    #    잊습니다 — 주인 규칙 29 와 같은 뜻입니다)
    통제 += 안전안내(쪽길)

    # ── 제철 어종 — 낚시와 해루질로 나눕니다
    어종칸 = []
    for 갈래, 설명 in (('해루질', '물 빠진 갯벌에서 손·호미로 직접 잡는 것들'),
                       ('낚시', '갯바위·방파제에서 낚싯대로 노리는 것들')):
        것들 = [x for x in v['어종'] if x['갈래'] == 갈래]
        if not 것들:
            continue
        카드 = ''.join(
            '<div class="catch-card">%s<h3 class="serif">%s</h3>%s</div>'
            % ('<div class="season">%s</div>' % esc(x['철']) if x['철'] else '',
               esc(x['이름'].get(언어) or x['이름']['ko']),
               '<p>%s</p>' % esc((x['설명'] or {}).get(언어)
                                 or (x['설명'] or {}).get('ko')) if x.get('설명') else '')
            for x in 것들)
        어종칸.append(
            '<div class="catch-group"><div class="catch-group-head">'
            '<span class="badge badge--green">%s</span>'
            '<span class="sub">%s</span></div>'
            '<div class="grid grid--tight">%s</div></div>'
            % (esc(갈래), esc(설명), 카드))

    # ── 먹거리 · 명소 · 코스 · 축제
    먹거리칸 = ''.join(
        '<div class="card"><h3 class="card-name">%s</h3>%s%s</div>'
        % (esc(x['이름'].get(언어) or x['이름']['ko']),
           '<p class="card-body">%s</p>'
           % esc((x['설명'] or {}).get(언어) or (x['설명'] or {}).get('ko'))
           if x.get('설명') else '',
           '<p class="card-note">철: %s</p>' % esc(x['철']) if x.get('철') else '')
        for x in v['먹거리'])

    # ★ 명소 카드에 **사진**을 붙입니다 (2026-09-28 주인 지적)
    #
    #   옛 권역 쪽에는 명소 사진 넷(학암포·만리포·가의도·몽산포)이
    #   있었습니다. 새 쪽은 대표 사진 하나뿐이라
    #   check_design.py 가 「사진 4 → 1」로 잡았습니다.
    #
    #   ★ 자료에 **명소 사진 142장**이 촬영자까지 적힌 채로 있는데
    #     쪽이 하나도 안 쓰고 있었습니다. 오늘 어종 설명 534개를
    #     찾았을 때와 같은 갈래입니다 — **자료에 있는데 안 쓰는 것.**
    #
    #   ★ 촬영자는 **자료에 적힌 것만** 적습니다 (주인 규칙 5).
    #     이용허락 종류는 photos.html 에만 둡니다 (규칙 6).
    #   ★ 짝은 **「명소」 칸으로** 짓습니다 (2026-09-28)
    #     처음에는 「제목」으로 이었습니다. 그런데 제목은 원본
    #     출처 이름 그대로라 체코어·영어인 것도 있습니다.
    #         제목  Seopori pine forest promenade
    #         명소  덕적도 서포리해수욕장
    #     그래서 142장 중 72장만 붙고 70장이 끊겼습니다.
    #     check_coverage.py 가 만들자마자 이것을 잡았습니다.
    _명소사진 = {}
    for _사 in (d.명소사진(권역) or []):
        열 = _사.get('명소') or _사.get('제목')
        if 열 and _사.get('파일'):
            _명소사진.setdefault(열, _사)

    _쓴사진 = set()

    # ★ **히어로와 같은 사진은 명소 카드에 안 씁니다** (2026-10-02 바깥 검수)
    #
    #   바깥 검수가 SHA 로 전수 비교해 잡았습니다 —
    #       changwon-hero.jpg = changwon-udo.jpg
    #       gangneung-hero.jpg = gangneung-tour-128757.jpg
    #       sokcho-hero.jpg = sokcho-yeonggeumjeong.jpg
    #       seogwipo-hero.jpg = seogwipo-oedolgae.jpg
    #   「파일 중복 자체가 아니라 **한 페이지에서 같은 사진이 Hero 와
    #     관광카드에 다시 나오는 경우**가 문제입니다. 그러면 사용자는
    #     「사진이 많은 사이트」가 아니라 **같은 사진을 돌려 쓰는
    #     사이트**처럼 느낍니다」
    #
    #   **이름이 아니라 알맹이**를 봅니다 — 이름이 달라도 같은 사진입니다
    #   ([[photo-check-by-distance]] 「이름은 못 믿습니다」).
    #   겹치면 그 명소는 **사진 없이 글 카드로** 나갑니다. 같은 것을
    #   두 번 보여 주느니 한 번만 보여 주는 편이 낫습니다.
    _히어로 = 대표사진(d, 권역=권역) or {}
    _히어로지문 = _사진지문(_히어로.get('파일'))

    def _명소그림(이름):
        사 = _명소사진.get(이름)
        if not 사 and 이름:
            # ★ 이름이 조금 다를 때도 잇습니다 (2026-09-28)
            #   제주는 「명소」 칸이 비고 제목만 있는데, 그 제목이
            #   명소 이름과 조금씩 다릅니다.
            #       제목  도두봉 키세스존
            #       명소  도두봉
            #   한쪽이 다른 쪽에 들어 있으면 같은 곳으로 봅니다.
            for 열, 후보 in _명소사진.items():
                if 열 and (이름 in 열 or 열 in 이름):
                    사 = 후보
                    break
        if not 사:
            return ''
        if _히어로지문 and _사진지문(사.get('파일')) == _히어로지문:
            # 히어로와 **같은 사진**입니다. 쪽 맨 위에 이미 크게
            # 있으니 여기서 또 보여 주지 않습니다.
            #
            #   ★ **「썼다」고 표시하고 비웁니다.** 그냥 비우기만 하면
            #     아래 「남는 사진」 칸이 「아직 안 쓴 사진」으로 보고
            #     **거기에 또 붙입니다.** 처음에 그렇게 해서 고친 뒤에도
            #     네 쪽이 그대로였습니다 — 재 보지 않았으면
            #     「고쳤습니다」라고 할 뻔했습니다
            #     ([[verify-each-fix]]).
            _쓴사진.add(사['파일'])
            return ''
        _쓴사진.add(사['파일'])
        찍은이 = 사.get('촬영자') or ''
        # ★ **출처를 사진 안에 겹쳐 둡니다** (2026-09-29 주인 지시)
        #   「사진출처도 사진안으로 집어넣자 그게 공간을 덜 잡아먹으니
        #     출처는 최대한 작게 표시하자」
        #   밖에 두면 두 줄까지 차지해 카드가 길어졌습니다.
        #   규칙 6 은 **촬영자를 밝히라**는 것이지 크게 쓰라는 것이
        #   아닙니다. 사진 안 아래에 작게 겹쳐도 밝힌 것입니다.
        return ('<figure class="card-figure">'
                '<img src="%s" alt="%s" loading="lazy" '
                'width="%s" height="%s">%s</figure>'
                % (esc(url.rel(쪽길, 사['파일'])), esc(이름),
                   사.get('가로') or 960, 사.get('세로') or 640,
                   # ★ 「사진 · 제목 · 촬영자」 꼴입니다 (주인 규칙 6)
                   #   처음에는 「사진 · 촬영자」로만 적었다가
                   #   check_photos 가 72곳을 잡았습니다.
                   #   검사기가 옳았습니다 — 제목이 있어야
                   #   어느 사진인지 알 수 있습니다.
                   '<figcaption>사진 · %s · %s</figcaption>'
                   % (esc(사.get('제목') or 이름), esc(찍은이))
                   if 찍은이 else ''))

    # ★ **주소를 뺍니다** (2026-09-29 주인 지시)
    #   「명소에서 주소칸을 지워버려 어짜피 명소라서 네비에 쉽게 나와
    #     굳이 안내 필요없어」
    #   맞는 말씀입니다. 「해운대해수욕장」을 찾는 데 지번은 필요 없습니다.
    #   한 줄이 빠지면 카드 57×평균 7곳 = 400줄이 줄어듭니다.
    명소칸 = ''.join(
        '<div class="card%s">%s<div class="card-head">'
        '<h3 class="card-name">%s</h3>%s</div>%s</div>'
        % (' card--photo' if _명소그림(x['이름'].get('ko')) else '',
           _명소그림(x['이름'].get('ko')),
           esc(x['이름'].get(언어) or x['이름']['ko']),
           이름표(x['갈래']) if x.get('갈래') else '',
           '<p class="card-body">%s</p>'
           % esc((x['설명'] or {}).get(언어) or (x['설명'] or {}).get('ko'))
           if x.get('설명') else '')
        for x in v['명소'])

    # ★ **남는 사진을 버리지 않습니다** (2026-09-28)
    #
    #   check_coverage 가 「자료에 142장인데 쪽에 129장」이라고
    #   했습니다. 남은 13장은 모두 제주였고, 까닭이 둘이었습니다.
    #
    #     (가) 같은 명소에 사진이 두 장
    #          성산에 「성산일출봉」이 두 장인데 첫 장만 쓰였습니다.
    #     (나) 명소 목록에 없는 곳
    #          대정의 「사계해변」은 명소 일곱 곳에 없습니다.
    #
    #   짝짓기 규칙을 더 촘촘히 만들 수도 있었지만, 그러면 자료가
    #   늘 때마다 또 손봐야 합니다. **남는 것을 모아 보여주는** 쪽이
    #   튼튼합니다 — 사진이 늘어도 저절로 나옵니다.
    #
    #   그리고 이것은 규칙 6-1 이기도 합니다.
    #   **사람은 눈으로 봅니다.** 좋은 바다 사진을 자료에 쌓아 두고
    #   안 보여 주면 없는 것과 같습니다.
    남은사진 = [x for x in (d.명소사진(권역) or [])
                if x.get('파일') and x['파일'] not in _쓴사진]
    풍경칸 = ''
    if 남은사진:
        칸들 = ''
        for 사 in 남은사진:
            찍은이 = 사.get('촬영자') or ''
            제목 = 사.get('제목') or ''
            칸들 += ('<figure class="shot">'
                     '<img src="%s" alt="%s" loading="lazy" '
                     'width="%s" height="%s">'
                     '<figcaption>사진 · %s%s</figcaption></figure>'
                     % (esc(url.rel(쪽길, 사['파일'])), esc(제목),
                        사.get('가로') or 960, 사.get('세로') or 640,
                        esc(제목),
                        ' · %s' % esc(찍은이) if 찍은이 else ''))
        풍경칸 = ('<section class="section" id="scenery"><div class="wrap">'
                  '<div class="section-head">'
                  '<p class="kicker">%s</p>'
                  '<h2 class="serif">%s</h2></div>'
                  '<div class="shots">%s</div>'
                  '</div></section>'
                  % ('이 고장의 다른 풍경' if 언어 == 'ko' else '当地其他风景',
                     '사진 %d장' % len(남은사진) if 언어 == 'ko'
                     else '照片 %d 张' % len(남은사진), 칸들))

    코스칸 = ''.join(
        '<div class="card"><div class="card-head">'
        '<h3 class="card-name">%s</h3>%s</div><ol class="steps">%s</ol></div>'
        % (esc(x['이름'].get(언어) or x['이름']['ko']),
           이름표(x['누구와'], 'badge--orange') if x.get('누구와') else '',
           ''.join('<li>%s</li>' % esc(s) for s in (x.get('차례') or [])))
        for x in v['코스'])

    # ★ **한 곳에서 만듭니다** (2026-09-29 · 규칙 26)
    #   전에는 권역 쪽과 묶음 쪽이 같은 코드를 따로 들고 있었습니다.
    축제칸, 축제목록 = 달력칸(v['축제'], 쪽길, 언어,
                          _축제쪽찾기(d))
    마을칸 = ''
    if v['마을']:
        줄 = ''.join(
            '<li><b>%s</b> %s%s</li>'
            % (esc(x['이름'].get(언어) or x['이름']['ko']),
               esc((x['무엇을'] or {}).get(언어) or (x['무엇을'] or {}).get('ko') or ''),
               ' · %s' % esc(x['주소']) if x.get('주소') else '')
            for x in v['마을'])
        마을칸 = ('<div class="note-box"><h3>어촌체험휴양마을</h3>'
                  '<p>마을이 정한 구역·도구로만 체험합니다. 예약과 요금은 '
                  '마을에 직접 확인하세요.</p><ul>%s</ul></div>' % 줄)

    물때 = r.get('물때관측소') or {}
    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s 물때표·해루질·낚시 — 포인트 %d곳 | %s'
                % (이름, 모두, d.사이트['이름']['ko']),
        '짧은제목': '%s 물때표·해루질·낚시 — 포인트 %d곳' % (이름, 모두),
        '설명': (r.get('설명') or
                 '%s 바다여행. 포인트 %d곳과 오늘 물때, 제철 어종·먹거리·축제를 '
                 '안내합니다.' % (이름, 모두)),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 사진주소(d, 대표사진(d, 권역=권역)),
        '대표사진자리': 사진자리(d, 대표사진(d, 권역=권역), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        # ★ 시간별 물높이 그래프 차림표 (2026-09-28 주인 지적)
        '집차림표': 그래프차림표(쪽길),
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.region(권역, 언)),
        '구조화자료': 권역구조화(d, 권역, 쪽길, 모두),
        '머리말': '%s 바다 안내' % 이름,
        '기준일조각': 기준일조각(),
        '머리이름표': ''.join([
            이름표('%s %d권역' % (d.색인['묶음이름'][r['묶음']]['ko'],
                                  sum(1 for y in d.권역들 if y['묶음'] == r['묶음'])),
                   'badge--orange'),
            이름표('포인트 %d곳' % 모두),
            이름표(r.get('바다') or '', 'badge--green'),
        ]),
        # 권역 쪽에서는 '전국 바다' 로 나갑니다.
        # 자기 쪽으로 가는 링크를 두면 안 됩니다 (주인 규칙 9)
        # ★ 누르면 **권역 사진 목록**으로 갑니다 (2026-09-29 주인 지시)
        #   첫 화면 맨 위로 보내면 다시 내려야 합니다.
        #   나가는 사람은 「다른 바다를 고르려고」 누릅니다.
        '돌아갈주소': (뿌리 or './') + '#bada-cards',
        '돌아갈글': '전국 바다',
        '권역이름': 이름,
        '메일': d.사이트['메일'],
        '권역': 권역,
        '한줄': (r.get('한줄') or '%s 바다 안내' % 이름),
        '큰제목': '%s 바다' % 이름,
        '큰제목뒷줄': (r.get('한줄') or '물때에 맞춰'),
        '소개글': (r.get('안내') or r.get('소개') or
                   '%s의 포인트와 제철 어종, 먹거리와 축제를 한곳에 모았습니다.' % 이름),
        '답묶음': 권역답묶음(d, 권역, 언어),
        '숫자칸': 숫자칸(d, 권역, 언어),
        '포인트수': 모두,
        '빠른이동': 빠른이동,
        '물때안내': ('물때 번호와 사리·조금은 늘 자동으로 나옵니다. '
                     '간조·만조 시각은 공공데이터를 불러옵니다.'
                     + (' 기준 관측소는 %s 입니다.' % 물때.get('이름')
                        if 물때.get('이름') else '')),
        # ★ 물때 띠 **아래에 시간별 물높이 그래프** 자리를 둡니다
        #   (2026-09-28 주인 지적 「물때표도 이 그림이 더 좋은거 같아
        #    그래프가 빠져있어」)
        #
        #   숫자만 있는 것과 곡선으로 보는 것은 다릅니다.
        #   **「지금 물이 차고 있나 빠지고 있나」는 곡선이라야
        #   한눈에 보입니다.** (주인 규칙 6-1 — 사람은 눈으로 봅니다)
        #
        #   그리는 것은 assets/js/tide-graph.js 가 합니다.
        #   자료는 서버의 api/marine.php (국립해양조사원 조석예보).
        #
        # ★ 2026-10-02 — **10일 달력을 권역 쪽에서 뺐습니다** (지피티 검수)
        #
        #   재 보니 권역 쪽이 모바일 390px 에서 **9,971px · 화면 14.6개**
        #   였고, 그중 물때 둘이 2,557px 로 **26%** 를 먹었습니다.
        #   그 탓에 이 사이트의 핵심인 **낚시 포인트가 6.2번째 화면**
        #   에서야 나왔습니다.
        #
        #   지피티 — 「권역 페이지에서 10일 물때 달력을 통째로 보여주지
        #     마세요. 권역 페이지는 오늘 물때 + 오늘 그래프만 보여주고,
        #     10일 전체 물때표는 전용 tide 페이지로 이동시킵니다」
        #
        #   ★ **달력을 지우는 것이 아닙니다.** 자료도 코드도 그대로고
        #     `/tide/` 에서 14일을 다 봅니다. 권역 쪽에서 **안 그릴** 뿐입니다.
        #     쪽에 「14일 물때표 보기」 단추를 두어 길을 잇습니다.
        #
        #   왼쪽 요약 + 오른쪽 그래프를 **한 줄에** 둡니다 (`.tide-compact`).
        '물때자리': ('<div class="tide-compact">'
                     '<div class="tide-strip" id="tideStrip" '
                     'data-region="%s" data-station="%s" data-days="14" '
                     'data-view="today" data-tide-url="%s" '
                     'data-muldae-url="%s"></div>'
                     # ★ data-events="off" — 바로 옆 요약칸에 간·만조가
                     #   있어 **똑같은 네 시각이 두 번** 나왔습니다.
                     #   그래프는 곡선·점·「지금」과 색 범례만 둡니다.
                     '<div class="tide-graph" id="tideGraph" '
                     'data-events="off"></div>'
                     '</div>'
                     # ★ **고른 권역을 들고 갑니다** (2026-10-02 지피티 결정)
                     #   「선택 상태까지 넘겨야 합니다. 단순 #부안보다
                     #     query 가 낫습니다 — /tide/?region=buan#tide-detail」
                     #   그러면 /tide/ 가 그 권역을 고르고 2주 상세를
                     #   **저절로 폅니다.** 「14일 물때표 보기」를 누른
                     #   분은 무엇을 보러 왔는지 분명하기 때문입니다.
                     % (esc(권역), esc(물때.get('이름') or ''),
                        esc(url.rel(쪽길, 'tide/index.html')
                            + '?region=' + 권역 + '#tide-detail'),
                        esc(url.rel(쪽길, 'muldae.html')))),
        '포인트안내': (r.get('포인트안내') or
                       '자리마다 어촌계·지자체 규정이 다릅니다. '
                       '가기 전에 반드시 확인하세요.'),
        '포인트지도': 포인트지도,
        '포인트칸': ''.join(포인트칸),
        '통제': 통제,
        '어종칸': ''.join(어종칸) or '<p class="notice">제철 어종을 정리하는 중입니다.</p>',
        '먹거리칸': 먹거리칸,
        '명소칸': 명소칸,
        '풍경칸': 풍경칸,
        '축제칸': 축제칸,
        '코스칸': 코스칸,
        '마을칸': 마을칸,
        # ★ 권역을 넘깁니다 — 제주에서는 제주패스가 뜹니다
        '광고칸': 광고칸('권역', 권역),
        # ★ 기준일은 머리로 올렸습니다 (2026-10-01 주인 지시)
        '기준일안내': '',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '쪽스크립트': ('<script src="%s" defer></script>'
                       % url.asset('assets/js/tide.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js', 'tide.js')))
                       + 물높이그래프(쪽길, 권역)
                       # ★ 축제 팝업 (2026-09-29 주인 지적)
                       + 축제팝업(축제목록, 쪽길)
                       # ★ 요즘 많이 찾아가는 곳 (2026-09-29 주인 지적)
                       + 찾아가는곳(권역, 이름, 쪽길)
                       + 광고움직임(쪽길, '권역')),
    }
    return 쪽길, template.그리기('region.html', 값)



def 찾아가는곳(권역, 이름, 쪽길):
    """★ **요즘 많이 찾아가는 곳** (2026-09-29 주인 지적)

    「맛집정보에 예전 티맵데이터기반 추천이 있었는데 그게 사라졌어」

    옛 쪽에는 `#tmapRank` 가 있었고 자료(api/places.php)도 그대로
    살아 있었습니다. 새 쪽에만 **아예 없었습니다.**

    ★ **맛 평가가 아닙니다.** 내비게이션 목적지 순위입니다.
      그대로 밝힙니다 — 「맛집 순위」라 하면 거짓이 됩니다.

    ★ 개인 가게로 연결하지 않습니다 (주인 규칙 12).
      누르면 지도 검색으로 갑니다.
    """
    길 = os.path.join(ASSETS, 'js', 'tmap-rank.js')
    if not os.path.isfile(길):
        return ''
    # api 주소는 **쪽 자리에 맞춰 셉니다** — 묶음 쪽은 폴더라
    # 'api/...' 로 고정하면 한 칸 아래를 가리킵니다 (그래프에서 겪음)
    자료 = {'권역': 권역, '이름': 이름, 'api': url.rel(쪽길, 'api/_')[:-1]}
    return ('<script>window.BADAGAJA_TMAP=%s;</script>'
            '<script src="%s" defer></script>'
            % (json.dumps(자료, ensure_ascii=False),
               esc(url.asset('assets/js/tmap-rank.js', 쪽길, 판번호(길)))))

def 첫물때권역(d):
    """첫 화면이 보여 줄 물때의 기준 권역 (data/raw/site.json).

    옛 사이트도 같은 자리에 보성을 기본으로 두었습니다
    (js/app.js — `COORDS[REGION] || COORDS.boseong`).
    """
    것 = (d.사이트.get('첫화면물때') or {}).get('권역')
    if 것 and any(r['id'] == 것 for r in d.권역들):
        return 것
    return d.권역들[0]['id'] if d.권역들 else ''


def 물높이그래프(쪽길, 권역):
    """시간별 물높이 그래프를 싣고 붙입니다 (2026-09-28 주인 지적).

    ★ 옛 쪽은 `js/region-extra.js` 가 `#tideStrip` 바로 아래에 칸을
      만들어 붙였습니다. 새 틀은 칸을 **미리 만들어 두고**
      거기에 붙입니다 — 자리가 자료에서 정해지는 편이 낫습니다.

    ★ 그래프가 못 뜨면 **칸을 숨깁니다.**
      빈 네모가 남아 있으면 「뭔가 깨졌나」 싶습니다.
      바깥(국립해양조사원)이 안 오는 것은 우리 탈이 아니지만,
      손님 눈에 빈 자리를 보이면 안 됩니다.
    """
    p = os.path.join(ASSETS, 'js', 'tide-graph.js')
    if not os.path.isfile(p):
        return ''
    주소 = url.asset('assets/js/tide-graph.js', 쪽길, 판번호(p))
    # ★ api 주소는 **쪽 자리에 맞춰 셉니다** (2026-09-29)
    #   묶음 쪽은 주소가 폴더(/chungnam/)라 'api/marine.php' 가
    #   /chungnam/api/marine.php 를 가리켜 404 였습니다.
    #   그 404 가 「물높이 예보를 불러오지 못했어요」로 보였습니다.
    api뿌리 = url.rel(쪽길, 'api/_')[:-1]
    return ('<script src="%s" defer></script>'
            '<script>window.addEventListener("load",function(){'
            'var 칸=document.getElementById("tideGraph");'
            'if(!칸||!window.BADAGAJA_TIDEGRAPH)return;'
            'var T=window.BADAGAJA_TIDE;'
            'window.BADAGAJA_TIDEGRAPH.mount(칸,%s,'
            '{api:%s,coords:(T&&T.coords)?T.coords[%s]:null});'
            'setTimeout(function(){'
            'if(!칸.querySelector(".tg-plot"))칸.style.display="none";'
            '},6000);});</script>'
            % (esc(주소), _js문자열(권역), _js문자열(api뿌리),
               _js문자열(권역)))



def 대상아이콘(이름, 쪽길):
    """어종·해루질 대상의 작은 그림 (2026-09-28 주인 규칙 6-1).

    ★ 없으면 **빈 네모를 두지 않습니다.** 그냥 안 넣습니다.
      깨진 그림 자리가 남으면 「뭔가 잘못됐나」 싶습니다.
    """
    if not 이름:
        return ''
    상대 = 'assets/icon/%s.svg' % 이름
    p = os.path.join(ASSETS, 'icon', '%s.svg' % 이름)
    if not os.path.isfile(p):
        return ''
    return ('<img class="card-ico" src="%s" alt="" width="28" height="28" '
            'loading="lazy" decoding="async">'
            % esc(url.asset(상대, 쪽길, 판번호(p))))



_나오는권역_기억 = {}


def 나오는권역들(d, 안내, 언어='ko'):
    """이 어종이 **나오는 권역 목록** — 한 곳에서 셉니다 (계약-01).

    ★ 2026-10-02 바깥 감사가 잡았습니다

      같은 쪽 안에서 숫자가 달랐습니다 —
        볼락 36↔39 · 우럭 45↔48 · 감성돔 51↔52 · 바지락 36↔38

      위 「나오는 권역」은 **손으로 적은 목록만** 세고,
      아래 「전국에서 잡히는 곳」은 거기에 **권역별 설명이 있는
      곳을 더해** 세고 있었습니다. **계산 경로가 둘이었습니다.**

      바깥 감사 — 「단순 문구 문제가 아니라 두 계산 경로가
      아직 살아 있다는 증거입니다」. 맞는 말입니다.

    ★ 셈법은 **아래쪽 것**을 그대로 씁니다. 그것이 옳습니다 —
      손으로 적은 목록은 빠진 것이 있습니다. 서천은 권역별
      설명에 백합이 있는데 목록에 없어 쪽에서 통째로 빠졌던
      적이 있습니다 (바깥 검수 8차).
    """
    열쇠 = (안내.get('id') or 안내.get('이름', {}).get('ko'), 언어)
    if 열쇠 in _나오는권역_기억:
        return list(_나오는권역_기억[열쇠])
    권역들 = list(안내.get('나오는권역') or [])
    있는것 = set(권역들)
    for _r in d.권역들:
        if _r['id'] in 있는것:
            continue
        if 권역별어종(d, _r['id'], 안내, 언어).get('설명'):
            권역들.append(_r['id'])
            있는것.add(_r['id'])
    _나오는권역_기억[열쇠] = list(권역들)
    return 권역들


def 권역별어종(d, 권역, 안내, 언어='ko'):
    """그 권역에서 이 어종을 어떻게 잡는가 (2026-09-28 되살림).

    ★ 자료(`data/raw/travel/`)의 권역별 어종 설명입니다.
      권역 쪽에는 나오는데 **어종 쪽에서 빠져** 있었습니다.
      갯벌마다 지켜야 할 것이 다르므로, 어종 쪽에서도 보여야 합니다.

    ★ 이름이 딱 안 맞을 수 있습니다
      자료에 「바지락·동죽」처럼 묶여 적힌 곳이 있습니다.
      그래서 **들어 있는지**로 봅니다. 없으면 빈 것을 돌려줍니다 —
      지어내지 않습니다.
    """
    찾을이름 = 안내['이름'].get('ko') or ''
    # ★ 한 권역에 **여러 항목**일 수 있습니다 (2026-09-28)
    #   화성에는 「바지락」과 「고온리 바지락 체험」이 따로 있습니다.
    #   먼저 만난 하나만 쓰면 나머지가 버려집니다.
    #   둘 다 그곳 사정을 담고 있으니 **모아서** 냅니다.
    설명들, 철 = [], ''
    for x in d.여행(권역)['어종']:
        그이름 = (x['이름'] or {}).get('ko') or ''
        if not 그이름 or x.get('갈래') != 안내['갈래']:
            continue
        if not (찾을이름 == 그이름 or 찾을이름 in 그이름):
            continue
        설명 = (x.get('설명') or {}).get(언어)                or (x.get('설명') or {}).get('ko') or ''
        if 설명 and 설명 not in 설명들:
            설명들.append(설명)
        if not 철:
            철 = x.get('철') or ''
    if not 설명들:
        return {}
    return {'설명': ' '.join(설명들), '철': 철}


def 안전안내(쪽길):
    """갯바위·방파제에서 지킬 것 (2026-09-28 주인 지적으로 되살림).

    ★ 옛 쪽 글 그대로입니다. 지어내지 않았습니다.
    ★ 펼쳐 보기로 둡니다 — 늘 펴 두면 쪽이 길어져 정작 찾던 것이
      아래로 밀립니다. 다만 **테트라포드·기상특보는 제목에 넣어**
      접혀 있어도 눈에 걸리게 합니다.
    """
    def 길(x):
        """★ **남기기로 한 옛 쪽도 갈 수 있는 곳입니다** (2026-09-28)

        전에는 site/ 안에 파일이 있는지만 봤습니다. 그런데
        gear.html·rule.html 은 새 틀이 안 만들고 **옛 사이트에
        남기는 쪽**입니다. 서버에는 살아 있는데 site/ 에는 없습니다.

        그래서 「처음이신가요」 칸 안의 네 링크가

            왕초보 해루질 기초 →
            장비와 안전 준비 →
            금어기·크기 제한 →

        **하나도 안 나오고 있었습니다.** 코드는 넣으려 했는데
        조건이 막고 있었습니다. 처음 오신 분께 가장 필요한 길인데요.

        keep.json 한 곳을 함께 봅니다 (SSOT).
        """
        그곳 = os.path.join(나갈곳, x.replace('/', os.sep))
        if os.path.isfile(그곳):
            return url.rel(쪽길, x)
        if x in 남기기로한것():
            return url.rel(쪽길, x)
        return None

    더보기 = []
    for 주소, 글 in (('fish/basics.html', '왕초보 바다낚시 기초 →'),
                     ('catch/basics.html', '왕초보 해루질 기초 →'),
                     ('gear.html', '장비와 안전 준비 →'),
                     ('rule.html', '금어기·크기 제한 →')):
        r = 길(주소)
        if r:
            더보기.append('<a href="%s">%s</a>' % (esc(r), esc(글)))

    return (
        # ★ **단추처럼 보이게 합니다** (2026-09-29 주인 지시 — 「이것도 버튼으로」)
        #   전에는 작은 ▶ 삼각형 하나뿐이라 **누를 수 있는 것으로 안 보였습니다.**
        #   처음 오신 분께 가장 필요한 안전 안내인데 아무도 안 눌렀을 것입니다.
        '<details class="firsttime firsttime--btn">'
        '<summary><span class="ft-ico" aria-hidden="true">'
        '<svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 4.6-3.2 8-8 9'
        '-4.8-1-8-4.4-8-9V7l8-4z"/><path d="M12 8v5M12 16v.6"/></svg>'
        '</span><b>처음이신가요?</b>'
        '<em>갯바위·방파제·테트라포드에서 지킬 것</em>'
        '<span class="ft-arrow" aria-hidden="true">▾</span>'
        '</summary><div class="ft-body">'
        '<p><b>구명조끼와 미끄럼 방지 신발</b>이 기본입니다. 갯바위는 '
        '물이끼와 따개비로 몹시 미끄럽고, 한 번 넘어지면 크게 다칩니다.</p>'
        '<p><b>기상특보 때는 들어가지 않습니다.</b> 너울은 맑은 날에도 '
        '예고 없이 옵니다. 파도가 발밑까지 올라오면 그 자리를 떠나세요.</p>'
        '<p><b>방파제 테트라포드</b>는 추락 사고가 잦습니다. 올라가지 '
        '마세요. 사이에 빠지면 혼자 올라오기 어렵습니다. 혼자 가지 말고, '
        '밤에는 헤드랜턴을 챙기세요.</p>'
        '<p><b>갯벌 대부분은 어촌계가 가꾸는 마을어장</b>입니다. 체험장이나 '
        '허용 구역이 아닌 곳에서 조개·낙지를 캐면 처벌받거나 분쟁이 생길 '
        '수 있습니다. 비어업인이 쓸 수 있는 도구도 손·호미·집게·갈고리 '
        '정도로 정해져 있습니다.</p>'
        '<p><b>어종마다 금어기와 잡으면 안 되는 크기</b>가 다릅니다. '
        '작은 것은 놓아 주세요.</p>'
        '<p><b>위급하면 119</b>로 신고하세요. 해상 사고는 122 도 '
        '119 로 이어집니다.</p>'
        + ('<p class="ft-more">%s</p>' % ' '.join(더보기) if 더보기 else '')
        + '</div></details>')


def 그래프차림표(쪽길):
    """시간별 물높이 그래프의 모양. 파일이 없으면 안 싣습니다.

    ★ engine/migrate_tidegraph.py 가 옛 css 에서 그래프 규칙만
      골라 만듭니다. 통째로 베끼면 새 틀 차림표와 부딪힙니다.
    """
    p = os.path.join(ASSETS, 'css', 'tidegraph.css')
    if not os.path.isfile(p):
        return ''
    return ('<link rel="stylesheet" href="%s">'
            % esc(url.asset('assets/css/tidegraph.css', 쪽길, 판번호(p))))


def _js문자열(s):
    """자바스크립트 문자열로 안전하게 적습니다."""
    return json.dumps(s or '', ensure_ascii=False)


def 권역구조화(d, 권역, 쪽길, 포인트수):
    r = d.권역(권역)
    이름 = r['이름']['ko']
    그래프 = [
        {'@type': 'WebPage', 'name': '%s 바다여행' % 이름,
         'url': url.full(쪽길), 'inLanguage': 'ko',
         'isPartOf': {'@type': 'WebSite', 'name': d.사이트['이름']['ko'],
                      'url': d.사이트['주소'] + '/'},
         'about': {'@type': 'AdministrativeArea', 'name': 이름}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': d.사이트['이름']['ko'],
             'item': d.사이트['주소'] + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 이름,
             'item': url.full(쪽길)}]},
    ]
    좌 = r.get('좌표') or {}
    if 좌.get('위도') is not None:
        그래프[0]['about']['geo'] = {
            '@type': 'GeoCoordinates',
            'latitude': 좌['위도'], 'longitude': 좌['경도']}
    return json.dumps({'@context': 'https://schema.org', '@graph': 그래프},
                      ensure_ascii=False, separators=(',', ':'))



def _축제주소(x, 쪽찾기, 쪽길, 언어):
    """축제 하나의 상세 쪽 주소. 없으면 빈 글."""
    아이디 = None
    if 쪽찾기:
        이 = (x.get('이름') or {}).get('ko')
        아이디 = 쪽찾기.get((이 or '').strip())
    if not 아이디:
        return ''
    return url.rel(쪽길, url.festival(아이디, 언어))


def _축제쪽찾기(d):
    """★ **축제 쪽 주소를 이름으로 찾습니다** (2026-09-29 주인 지적)

    주인이 「자세히 보기를 누르면 비어있는 페이지로 연결되」 하셨습니다.

    까닭: **자료가 둘인데 아이디 체계가 다릅니다.**

        권역 달력   data/raw/travel/*.json     busanwest-fest-01
        축제 상세   data/raw/festivals/*.json  busanwest-1

    달력은 travel 의 아이디로 `festival/busanwest-fest-01.html` 을
    가리켰는데, 그런 파일은 **없습니다.** 198쪽이 모두 어긋났습니다.

    ★ 아이디를 맞추려 자료를 고치지 않습니다 — 축제 쪽 주소는
      옛 사이트와 같아야 검색이 안 끊깁니다(url.festival 주석).
      대신 **이름으로 잇습니다.** 자료가 늘어도 저절로 이어집니다.
    """
    표 = {}
    for x in d.축제들:
        이 = (x.get('이름') or {}).get('ko')
        if 이 and x.get('id'):
            표.setdefault(이.strip(), x['id'])
    return 표


def 달력칸(축제들, 쪽길, 언어='ko', 쪽찾기=None):
    """★ **달마다 한 칸 · 누르면 팝업** (2026-09-29 주인 지적)

    「달마다 다른 얼굴의 행사에 전에 있던 팝업 설명창이 사라졌어」

    ★ 옛 쪽에는 `.ip-overlay` 팝업이 있었습니다. 새 쪽은 설명을
      카드에 **그대로 펼쳐** 놓아 칸이 길어지고, 일정·가는 길처럼
      더 적을 것을 넣을 자리가 없었습니다.

    ★ **한 곳에서 만듭니다** (규칙 26). 전에는 권역 쪽과 묶음 쪽이
      각각 같은 코드를 들고 있었습니다. 한쪽만 고치면 갈라집니다.

    돌려주는 것: (칸 HTML, 팝업이 읽을 목록)
    """
    달표 = {}
    for x in 축제들:
        달표.setdefault(x.get('달') or 0, []).append(x)

    목록 = []

    def 한개(x):
        이름 = x['이름'].get(언어) or x['이름']['ko']
        설명 = ((x.get('설명') or {}).get(언어)
                or (x.get('설명') or {}).get('ko') or '')
        번호 = len(목록)
        목록.append({
            '이름': 이름, '설명': 설명,
            '곳': x.get('곳') or '',
            '때': ('%d월' % x['달']) if x.get('달') else '',
            '누구와': x.get('누구와') or '',
            # ★ 못 찾으면 **주소를 안 넣습니다.**
            #   깨진 링크보다 단추가 없는 편이 낫습니다.
            '주소': _축제주소(x, 쪽찾기, 쪽길, 언어),
        })
        return ('<button type="button" class="month-item" data-fest="%d">'
                '<span class="month-name">%s</span>%s</button>'
                % (번호, esc(이름),
                   '<span class="month-desc">%s</span>' % esc(설명)
                   if 설명 else ''))

    나옴 = ''
    for 달 in range(1, 13):
        것들 = 달표.get(달) or []
        나옴 += ('<div class="month%s"><div class="month-num">%d월</div>%s</div>'
                 % (' month--on' if 것들 else '', 달,
                    ''.join(한개(x) for x in 것들)))
    남은 = 달표.get(0) or []
    if 남은:
        나옴 += ('<div class="month month--on">'
                 '<div class="month-num">그 밖</div>%s</div>'
                 % ''.join(한개(x) for x in 남은))
    return 나옴, 목록


def 축제팝업(목록, 쪽길):
    """팝업이 읽을 자료와 스크립트를 함께 냅니다."""
    if not 목록:
        return ''
    길 = os.path.join(ASSETS, 'js', 'fest-pop.js')
    if not os.path.isfile(길):
        return ''
    return ('<script>window.BADAGAJA_FEST=%s;</script>'
            '<script src="%s" defer></script>'
            % (json.dumps(목록, ensure_ascii=False),
               esc(url.asset('assets/js/fest-pop.js', 쪽길, 판번호(길)))))

def 달표만들기(축제들, 언어='ko'):
    """달마다 한 칸. 축제가 있는 달만 밝게 보입니다"""
    달표 = {}
    for x in 축제들:
        달표.setdefault(x.get('달') or 0, []).append(x)
    나옴 = ''
    for 달 in range(1, 13):
        것들 = 달표.get(달) or []
        나옴 += ('<div class="month%s"><div class="month-num">%d월</div>%s</div>'
                 % (' month--on' if 것들 else '', 달,
                    ''.join('<div class="month-name">%s</div>%s'
                            % (esc(x['이름'].get(언어) or x['이름']['ko']),
                               '<div class="month-desc">%s</div>'
                               % esc((x['설명'] or {}).get(언어)
                                     or (x['설명'] or {}).get('ko'))
                               if x.get('설명') else '')
                            for x in 것들[:3])))
    남은것 = 달표.get(0) or []
    if 남은것:
        나옴 += ('<div class="month month--on"><div class="month-num">그 밖</div>%s</div>'
                 % ''.join('<div class="month-name">%s</div>'
                           % esc(x['이름'].get(언어) or x['이름']['ko'])
                           for x in 남은것[:3]))
    return 나옴



def 묶음검색자료(d, 묶음, 권역들, 쪽길, 언어='ko'):
    """★ 이 묶음 안에서 찾을 수 있는 것들 (2026-09-28)

    옛 묶음 쪽에 「충남 권역·포인트·제철 해산물·축제·명소 검색」
    칸이 있었습니다. 새 쪽에서 빠져 check_design.py 가
    「입력칸 1 → 0」으로 잡았습니다.

    ★ 목록을 **손으로 적지 않습니다.** 자료에서 모읍니다 (규칙 29).
      나중에 권역이 늘거나 어종이 바뀌어도 저절로 따라옵니다.

    ★ 포인트는 **이름만** 담습니다.
      한 묶음에 300곳이 넘는데 설명까지 담으면 쪽이 무거워집니다.
      손님은 이름으로 찾고, 눌러서 그 쪽으로 갑니다.
    """
    나옴 = []

    def 말(값):
        """이름은 모두 {'ko': …, 'zh': …} 꼴입니다. 한 군데서 풉니다."""
        if isinstance(값, dict):
            return 값.get(언어) or 값.get('ko') or ''
        return 값 or ''

    def 넣기(갈래, 이름, 곁말, 갈곳):
        이름 = 말(이름)
        if not 이름 or not 갈곳:
            return
        것 = {'t': 갈래, 'n': 이름, 'u': url.rel(쪽길, 갈곳)}
        if 곁말:
            것['k'] = 곁말
        나옴.append(것)

    for r in 권역들:
        r이름 = r['이름'].get(언어) or r['이름']['ko']
        넣기('region', r이름, r.get('한줄') or '',
             url.region(r['id'], 언어))

        여행 = d.여행(r['id'])
        for x in 여행['어종']:
            넣기('catch', x['이름'].get(언어) or x['이름']['ko'],
                 '%s · %s' % (r이름, x.get('철') or ''),
                 url.region(r['id'], 언어))
        for x in 여행['축제']:
            넣기('fest', x.get('이름'), r이름,
                 url.region(r['id'], 언어))
        for x in 여행['명소']:
            넣기('spot', x.get('이름'), r이름,
                 url.region(r['id'], 언어))
        for x in (여행.get('코스') or []):
            넣기('course', x.get('이름'), r이름,
                 url.region(r['id'], 언어))

        # 포인트 — 이름만. 그 갈래 목록 쪽으로 보냅니다.
        for 갈래, 이름갈래 in (('낚시', 'fishing'), ('해루질', 'gleaning')):
            목록 = d.포인트(r['id'], 갈래) or []
            if not 목록:
                continue
            갈곳 = url.point_list(r['id'], 갈래, 언어)
            for 곳 in 목록:
                넣기('point', 곳.get('이름'),
                     '%s · %s' % (r이름, 갈래), 갈곳)

    # 같은 것이 여러 번 나오면 하나만 (어종은 권역마다 나옵니다)
    본것 = set()
    끝 = []
    for 것 in 나옴:
        열쇠 = (것['t'], 것['n'], 것['u'])
        if 열쇠 in 본것:
            continue
        본것.add(열쇠)
        끝.append(것)
    return 끝


def 많이찾는말(d, 권역들, 언어='ko'):
    """많이 찾는 말 — **자료에서 고릅니다.** 손으로 적지 않습니다.

    이 묶음 권역들이 제철로 가장 많이 꼽는 어종 다섯을 냅니다.
    """
    센것 = {}
    for r in 권역들:
        for x in d.여행(r['id'])['어종']:
            이름 = x['이름'].get(언어) or x['이름']['ko']
            센것[이름] = 센것.get(이름, 0) + 1
    많은것 = sorted(센것.items(), key=lambda v: (-v[1], v[0]))
    return [이름 for 이름, _ in 많은것[:5]] + ['축제']



def 권역지도(d, 권역, 쪽길, 언어='ko'):
    """권역 쪽 **포인트 지도 + 사진카드** (2026-10-02 지피티 시안)

    ★ 왜 넣었나
      재 보니 모바일 390px 에서 **낚시 포인트가 6.2번째 화면**에서야
      나왔습니다. 이 사이트에서 손님이 가장 알고 싶은 것인데
      네 화면 반을 넘겨야 닿았습니다.

      지피티 — 「43개 포인트를 처음부터 다 노출할 이유가 없습니다.
        지도에서 하나 선택 → 선택한 카드 1개 크게. 화면 하나에서
        해결됩니다」

    ★ 자리는 지피티가 확정했습니다 (`region-point-map-controls-v2.html`)
        지도 **밖** 위 : 전체 / 낚시 / 해루질 거르기
        좌상단        : 일반 / 위성
        우상단        : ＋ / －
        좌하단        : 색 범례
        하단 가운데   : 「지도 이동 켜기」 — 모바일만

      네 모서리를 지도 조작에 내주려고 거르기를 **밖으로** 뺐습니다.
      모바일 360px 에서 한 줄에 몰면 서로 가립니다.

    ★ 지도가 안 떠도 쪽은 그대로 씁니다 (계약-23).
      아래 낚시·해루질 배너가 그대로 있어 고르는 데 지장이 없습니다.

    ★ 그리는 것은 `assets/js/region-map.js`,
      카카오 전용 코드는 `assets/js/map-provider.js` 에 가둡니다.
    """
    열쇠 = (d.사이트.get('지도') or {}).get('카카오키') or ''
    if not 열쇠:
        return ''

    r = d.권역(권역)
    이름 = r['이름'].get(언어) or r['이름']['ko']
    것들 = []
    for 갈래 in ('낚시', '해루질'):
        for x in (d.포인트(권역, 갈래) or []):
            좌 = x.get('좌표') or {}
            if not (좌.get('위도') and 좌.get('경도')):
                continue
            것들.append({
                'id': x['id'],
                '이름': x['이름'].get(언어) or x['이름']['ko'],
                '위도': 좌['위도'], '경도': 좌['경도'],
                '지형': x.get('지형') or '',
                '갈래': 갈래,
                '어림': bool(x.get('배로가나')) or x.get('출입') == '배로만',
                '주소': url.rel(쪽길, url.point_list(권역, 갈래, 언어))
                        + '#' + x['id'],
            })
    if not 것들:
        return ''

    낚 = sum(1 for x in 것들 if x['갈래'] == '낚시')
    해 = sum(1 for x in 것들 if x['갈래'] == '해루질')

    # ★ **지도에 안 뜨는 곳을 밝힙니다** (2026-10-02 바깥 검수가 잡음)
    #
    #   「신안: 제목은 포인트 110곳인데 지도 필터는 전체 108.
    #     고흥: 제목은 109곳인데 지도는 102. 7곳 차이가 납니다」
    #
    #   자료가 틀린 것이 아닙니다. **좌표를 아직 못 잡은 곳**이
    #   지도에서 빠진 것입니다. 그런데 그 사실을 **안 밝히고
    #   있었습니다.** 손님은 「숫자가 왜 다르지」 할 뿐입니다.
    #
    #   포인트 쪽 지도는 이미 밝히고 있습니다 — 「지도에 N곳 ·
    #   위치를 아직 못 잡은 곳 M」. 같은 말을 여기도 둡니다.
    #   ★ 숨기지 않습니다. 모르는 것은 모른다고 적습니다.
    온전 = d.셈(권역, '낚시') + d.셈(권역, '해루질')
    없는수 = 온전 - (낚 + 해)

    # 사진 주소는 **자료에서 읽습니다. 짐작해 만들지 않습니다** (규칙 6-1)
    사진 = d.히어로(권역) or {}
    대표 = (url.rel(쪽길, 사진['파일']) if 사진.get('파일') else '')

    자료 = {
        '지도키': 열쇠,
        '권역': 권역,
        '한줄': (r.get('한줄') or ''),
        '대표사진': 대표,
        '포인트': 것들,
    }

    거르기 = ['<nav class="rm-filter" id="regionMapFilter" '
              'aria-label="포인트 갈래">']
    for 값, 글, 수 in (('전체', '전체', 낚 + 해),
                       ('낚시', '낚시', 낚), ('해루질', '해루질', 해)):
        if not 수:
            continue
        켜 = (값 == '전체')
        거르기.append('<button type="button" data-kind="%s"%s '
                      'aria-pressed="%s">%s %d</button>'
                      % (esc(값), ' class="on"' if 켜 else '',
                         'true' if 켜 else 'false', esc(글), 수))
    거르기.append('</nav>')
    if 없는수 > 0:
        거르기.append(
            '<p class="rm-note">지도에 %d곳을 표시했습니다. '
            '위치를 아직 못 잡은 %d곳은 아래 목록에서 보실 수 있습니다.</p>'
            % (낚 + 해, 없는수))

    낚주소 = url.rel(쪽길, url.point_list(권역, '낚시', 언어))
    해주소 = url.rel(쪽길, url.point_list(권역, '해루질', 언어))
    단추 = ''
    if 낚:
        단추 += '<a class="on" href="%s">낚시 포인트</a>' % esc(낚주소)
    if 해:
        단추 += '<a href="%s">해루질 포인트</a>' % esc(해주소)

    카드 = ('<article class="rm-pick" id="regionPickCard">'
            '<img class="rp-img" src="%s" alt="%s 바다" '
            'loading="lazy" width="900" height="600">'
            '<a class="rp-arrow" href="%s" aria-label="포인트 목록 보기">→</a>'
            # ★ 차례는 **제목 → 설명 → 배지 → 단추** 입니다
            #   (2026-10-02 지피티 (나) 선택)
            #   「포인트 제목 최대 2줄 · 설명 최대 1줄 · 배지는 제목
            #     오른쪽이 아니라 제목 아래 또는 설명 옆.
            #     카드 높이는 늘리지 말고 오버레이 안 배치만 바꿉니다」
            #   실제 이름이 「라마다호텔 앞 해안도로 좌측」처럼 길어
            #   제목 오른쪽에 배지를 두면 겹칩니다.
            '<div class="rp-copy">'
            '<h3 class="rp-name">%s</h3>'
            '<p class="rp-desc"></p>'
            '<span class="rp-count">포인트</span>'
            '<div class="rp-acts">%s</div>'
            '</div></article>'
            % (esc(대표), esc(이름), esc(낚주소 if 낚 else 해주소),
               esc(이름), 단추))

    실을것 = ''
    for 자리, 파일 in (('assets/js/map-provider.js', 'map-provider.js'),
                       ('assets/js/region-map.js', 'region-map.js')):
        길 = os.path.join(ASSETS, 'js', 파일)
        if os.path.isfile(길):
            실을것 += ('<script src="%s" defer></script>'
                       % esc(url.asset(자리, 쪽길, 판번호(길))))

    return ('%s<div class="region-points">'
            '<div class="rm-shell" id="regionPointMap" '
            'aria-label="%s 포인트 지도"></div>%s</div>'
            '<script type="application/json" id="권역지도자료">%s</script>%s'
            % (''.join(거르기), esc(이름), 카드,
               json.dumps(자료, ensure_ascii=False, separators=(',', ':')),
               실을것))


def 묶음지도(d, 권역들, 쪽길, 언어='ko'):
    """★ **실제 지도**로 권역을 보여 줍니다 (2026-09-29 주인 지시)

    「이런 지도 말고 실제 지도로해줘」 · 「위성지도도 볼 수 있게 만들고」

    ★ 전에는 직접 그린 **그림 지도**였습니다. 땅 모양 다각형에
      점을 찍었습니다. 가볍고 열쇠도 필요 없었지만
      **섬이 어디인지 · 길이 어떤지 · 얼마나 먼지**를 알 수 없었습니다.

    ★ 위성이 왜 필요한가 — 갯바위·갯벌은 **길 이름이 없습니다.**
      일반 지도에서는 빈 바다로만 보입니다.

    ★ 지도가 안 떠도 쪽은 그대로 씁니다 (계약-23).
      옆에 권역 카드가 그대로 있습니다.
    """
    점들 = [(r, (r.get('좌표') or {})) for r in 권역들]
    점들 = [(r, c) for r, c in 점들 if c.get('위도') and c.get('경도')]
    if not 점들:
        return ''

    묶음이름 = (d.색인['묶음이름'][권역들[0]['묶음']].get(언어)
                or d.색인['묶음이름'][권역들[0]['묶음']]['ko'])
    것들 = [{
        '이름': r['이름'].get(언어) or r['이름']['ko'],
        '위도': c['위도'], '경도': c['경도'],
        '주소': url.rel(쪽길, url.region(r['id'], 언어)),
        '수': d.셈(r['id']),
    } for r, c in 점들]

    자료 = {'지도키': (d.사이트.get('지도') or {}).get('카카오키') or '',
            '권역들': 것들}
    # ★ 파일 이름을 **또렷하게** 적습니다 (2026-09-29)
    #   처음에는 경로만 적고 쪼개 썼더니, check_architecture 검사 1이
    #   「build.py 가 group-map.js 를 모른다」고 잡았습니다.
    #   그 검사는 따옴표 안의 **파일 이름**을 봅니다 — 다른 곳과
    #   같은 꼴로 적어야 사람도 검사기도 찾습니다.
    실을것 = ''
    for 자리, 이름 in (('assets/js/map-type.js', 'map-type.js'),
                       ('assets/js/group-map.js', 'group-map.js')):
        길 = os.path.join(ASSETS, 'js', 이름)
        if os.path.isfile(길):
            실을것 += ('<script src="%s" defer></script>'
                       % esc(url.asset(자리, 쪽길, 판번호(길))))

    return ('<div class="gm"><p class="gm-title">권역 위치 안내</p>'
            '<div id="groupMap" class="gm-map" '
            'aria-label="%s 권역 지도"></div>'
            '<p class="gm-note">권역이 서로 어디쯤 있는지 보여 줍니다. '
            '누르면 그 권역으로 가고, 포인트 지도는 그곳에 있습니다.'
            '</p></div>'
            '<script>window.BADAGAJA_GROUPMAP=%s;</script>%s'
            % (esc(묶음이름), json.dumps(자료, ensure_ascii=False), 실을것))

def 묶음쪽(d, 묶음, 언어='ko'):
    """묶음 쪽 — 충남·전남처럼 여러 권역을 묶은 문입니다"""
    이름 = d.색인['묶음이름'][묶음].get(언어) or d.색인['묶음이름'][묶음]['ko']
    권역들 = [r for r in d.권역들 if r['묶음'] == 묶음]
    쪽길 = url.group(묶음, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    수 = d.셈(묶음=묶음)          # ★ 셉니다 (계약-05)

    # ★ 권역 카드에 **사진**을 붙입니다 (2026-09-28 주인 지적)
    #
    #   옛 묶음 쪽에는 카드마다 그 권역 바다 사진이 있었습니다.
    #   새 쪽은 글만 있어 사진이 6장 → 1장으로 줄었습니다.
    #   주인 규칙 6-1 — 「사람은 눈으로 봅니다. 쪽에는 보이는 것이
    #   있어야 합니다」 — 와 곧장 맞닿습니다.
    #
    #   ★ 사진 주소는 **자료에서 읽습니다. 짐작해 만들지 않습니다.**
    #     (규칙 6-1 — 전에 img/{권역}/hero.jpg 로 지어냈다가
    #      57곳 중 15곳만 맞고 52곳이 깨진 적이 있습니다)
    권역칸 = []
    for r in 권역들:
        r수 = d.셈(r['id'])
        사진 = d.히어로(r['id']) or {}
        그림 = ''
        if 사진.get('파일'):
            그림 = ('<img class="card-photo" src="%s" alt="%s 바다" '
                    'loading="lazy" width="480" height="320">'
                    % (esc(url.rel(쪽길, 사진['파일'])),
                       esc(r['이름'].get(언어) or r['이름']['ko'])))
        권역칸.append(
            '<a class="card card--go card--photo" href="%s">%s'
            '<div class="card-head"><h3 class="card-name">%s</h3>%s</div>'
            # ★ 카드 자체가 링크입니다 — 안에 또 단추를
            #   두면 「그것만 눌러야 하나」 싶어집니다
            #   (2026-09-30 주인 지시)
            '<p class="card-body">%s</p></a>'
            % (esc(url.rel(쪽길, url.region(r['id'], 언어))), 그림,
               esc(r['이름'].get(언어) or r['이름']['ko']),
               이름표('포인트 %d곳' % r수) if r수 else '',
               esc(r.get('한줄') or r.get('소개') or '')))

    # ★ **남는 칸에 광고 카드를 넣습니다** (2026-10-01 주인 지시)
    #
    #   「여기에 제주패스 광고 올릴꺼야 예쁘게 만들어서 넣어줘」
    #
    #   제주는 권역이 7곳입니다. 격자가 PC 에서 2열이라 여덟째 칸이
    #   늘 빕니다. 빈 칸은 「덜 만든 쪽」처럼 보입니다 — 채우면
    #   광고도 되고 모양도 삽니다.
    #
    #   ★ 자리만 둡니다. 무엇을 넣을지는 `data/raw/ads.json` 이
    #     정합니다 (계약-11). 광고를 끄면 이 칸도 사라집니다.
    권역칸.append(광고칸('묶음카드', 묶음))

    # ★ 권역 고르기 — **누르면 그 권역 쪽으로 갑니다** (2026-09-28)
    #
    #   옛 쪽에는 태안·서산·당진… 여섯 단추가 물때 칸 위에 있었고,
    #   누르면 **그 자리에서** 물때가 바뀌었습니다.
    #
    #   여기서는 **그 권역 쪽으로 보냅니다.** 까닭이 있습니다.
    #     · tide.js 는 한 번 그리고 끝나는 짜임입니다. 그 자리에서
    #       바꾸려면 여섯 권역 물때를 미리 다 불러오거나, 누를 때마다
    #       바깥에 물어봐야 합니다. 둘 다 무겁고 깨지기 쉽습니다.
    #     · 권역 쪽에는 물때가 **더 온전히** 있습니다 — 2주 표,
    #       시간별 물높이, 포인트, 안전 안내까지.
    #     · 손님이 진짜 원하는 것은 「서산 물때」가 아니라
    #       「서산에 갈까」입니다. 그러면 권역 쪽이 맞습니다.
    #
    #   단추가 아니라 **링크**라야 합니다. 눌러서 옮겨 가는 것이니
    #   가운데 클릭·새 탭이 되어야 하고, 읽어 주는 기계도 그렇게 압니다.
    권역단추 = ''.join(
        '<a class="tide-region%s" href="%s"%s>%s</a>'
        % (' is-on' if i == 0 else '',
           esc(url.rel(쪽길, url.region(r['id'], 언어)) + '#tide'),
           ' aria-current="page"' if i == 0 else '',
           esc(r['이름'].get(언어) or r['이름']['ko']))
        for i, r in enumerate(권역들))

    첫 = 권역들[0] if 권역들 else None

    지도 = 묶음지도(d, 권역들, 쪽길, 언어)

    # ★ 검색 — 이 묶음 안의 것을 이름으로 찾습니다 (2026-09-28)
    찾을것 = 묶음검색자료(d, 묶음, 권역들, 쪽길, 언어)
    빠른말 = 많이찾는말(d, 권역들, 언어)
    검색칸 = (
        '<div class="gs"><label class="sr-only" for="groupSearch">'
        '%s 권역·포인트·제철 해산물·축제·명소를 찾을 수 있습니다</label>'
        '<div class="gs-box">'
        '<svg class="gs-ic" viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4.2-4.2"/></svg>'
        '<input id="groupSearch" type="search" autocomplete="off" '
        'placeholder="%s 권역·포인트·제철 해산물·축제·명소 찾기"></div>'
        '<div class="gs-quick" id="groupQuick"><span>많이 찾는</span>%s</div>'
        '<div class="gs-out" id="groupSearchOut" hidden></div></div>'
        % (esc(이름), esc(이름),
           ''.join('<button type="button" data-q="%s">%s</button>'
                   % (esc(말), esc(말)) for 말 in 빠른말)))

    # ★ 숫자 요약 — **자료에서 셉니다** (주인 규칙 29)
    _명소 = sum(len(d.여행(r['id'])['명소']) for r in 권역들)
    _축제수 = sum(len(d.여행(r['id'])['축제']) for r in 권역들)
    숫자요약 = ('<div class="hero-stats">'
                + ''.join('<div class="hs"><b>%s</b><span>%s</span></div>'
                          % ('{:,}'.format(값), esc(말))
                          for 값, 말 in (
                              (len(권역들), '%s 시·군' % 이름),
                              (수, '해루질·낚시 포인트'),
                              (_명소, '바닷가 명소'),
                              (_축제수, '지역 축제')) if 값)
                + '</div>')

    # 제철 어종 — 이 묶음 권역들에서 여러 번 꼽히는 것부터
    센것 = {}
    for r in 권역들:
        for x in d.여행(r['id'])['어종']:
            키 = x['이름']['ko']
            센것.setdefault(키, {'것': x, '수': 0})
            센것[키]['수'] += 1
    많은것 = sorted(센것.values(), key=lambda v: (-v['수'], v['것']['이름']['ko']))
    어종칸 = ''.join(
        '<div class="catch-card">%s<h3 class="serif">%s</h3>'
        '<p>%d권역에서 제철로 꼽습니다</p></div>'
        % ('<div class="season">%s</div>' % esc(v['것']['철'])
           if v['것'].get('철') else '',
           esc(v['것']['이름'].get(언어) or v['것']['이름']['ko']), v['수'])
        for v in 많은것[:12])

    축제들 = []
    for r in 권역들:
        축제들 += d.여행(r['id'])['축제']
    # ★ 팔업이 뛰도록 권역 쪽과 **같은 함수**를 씁니다
    묶음축제칸, 묶음축제목록 = 달력칸(축제들, 쪽길, 언어,
                                  _축제쪽찾기(d))

    # ── 여행 코스 — **이 묶음 안 권역들의 코스를 모읍니다**
    #
    #   ★ 2026-09-28 주인 지적으로 되살렸습니다.
    #     옛 묶음 쪽에는 「학암포에서 만리포까지 해변 잇기」처럼
    #     코스가 18개 있었는데 새 쪽에서 통째로 빠져 있었습니다.
    #     engine/check_design.py 가 잡았습니다(빠진 칸 27개 중 18개).
    #
    #   ★ 코스는 **권역 쪽에도 있습니다.** 여기서는 어느 권역
    #     것인지 밝혀, 묶음에서 한눈에 고르고 그 권역으로 가게 합니다.
    코스칸 = []
    for r in 권역들:
        r이름 = r['이름'].get(언어) or r['이름']['ko']
        for x in d.여행(r['id'])['코스']:
            차례 = [z for z in (x.get('차례') or []) if z]
            코스칸.append(
                '<div class="card course-card">'
                '<div class="card-head">'
                '<h3 class="card-name">%s</h3>%s</div>'
                '<p class="course-where">'
                '<a href="%s">%s</a></p>'
                '<ol class="steps">%s</ol></div>'
                % (esc(x['이름'].get(언어) or x['이름']['ko']),
                   이름표(x['누구와'], 'badge--orange')
                   if x.get('누구와') else '',
                   esc(url.rel(쪽길, url.region(r['id'], 언어))),
                   esc(r이름),
                   ''.join('<li>%s</li>' % esc(z) for z in 차례)))

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s 바다 여행 — 물때·낚시·해루질 포인트 %d곳 | %s'
                % (이름, 수, d.사이트['이름']['ko']),
        '짧은제목': '%s 바다 여행 — 포인트 %d곳' % (이름, 수),
        '설명': '%s 해안 %d권역의 물때와 낚시·해루질 포인트 %d곳, 제철 해산물과 '
                '축제를 한곳에.' % (이름, len(권역들), 수),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 사진주소(d, 대표사진(d, 묶음=묶음)),
        '대표사진자리': 사진자리(d, 대표사진(d, 묶음=묶음), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.group(묶음, 언)),
        '구조화자료': 묶음구조화(d, 묶음, 쪽길, 수, len(권역들)),
        '머리말': '%s 바다 안내' % 이름,
        '기준일조각': 기준일조각(),
        '머리이름표': ''.join([
            이름표('%d권역' % len(권역들), 'badge--orange'),
            이름표('포인트 %d곳' % 수),
        ]),
        # ★ 누르면 **권역 사진 목록**으로 갑니다 (2026-09-29 주인 지시)
        #   첫 화면 맨 위로 보내면 다시 내려야 합니다.
        #   나가는 사람은 「다른 바다를 고르려고」 누릅니다.
        '돌아갈주소': (뿌리 or './') + '#bada-cards',
        '돌아갈글': '전국 바다',
        '권역이름': 이름,
        '메일': d.사이트['메일'],
        '묶음': 묶음,
        '묶음이름': 이름,
        '한줄': '%s 바다 안내' % 이름,
        '큰제목': '%s 바다' % 이름,
        '큰제목뒷줄': '%d권역을 한눈에' % len(권역들),
        '소개글': '%s 해안 %d권역의 포인트 %d곳과 제철 어종, 축제를 모았습니다. '
                  '권역을 고르면 그곳의 물때와 자세한 안내가 나옵니다.'
                  % (이름, len(권역들), 수),
        '권역수': len(권역들),
        '전국주소': 뿌리 or './',
        '권역안내': '권역마다 물때 기준 관측소와 규정이 다릅니다. '
                    '가시려는 곳을 골라 주세요.',
        '권역칸': ''.join(권역칸),
        # ★ 2026-09-28 주인 지적으로 되살린 것들
        '숫자요약': 숫자요약,
        '검색칸': 검색칸,
        '지도': 지도,
        '권역단추': 권역단추,
        '첫권역': (첫 or {}).get('id', ''),
        '첫권역이름': ((첫 or {}).get('이름') or {}).get(언어)
                      or ((첫 or {}).get('이름') or {}).get('ko') or '',
        '첫관측소': ((첫 or {}).get('물때관측소') or {}).get('이름', ''),
        '첫권역주소': (url.rel(쪽길, url.region(첫['id'], 언어))
                       if 첫 else './'),
        '어종칸': 어종칸 or '<p class="notice">제철 어종을 정리하는 중입니다.</p>',
        '코스칸': ''.join(코스칸),
        '코스수': len(코스칸),
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        # ★ 팔업이 뛰도록 같은 함수를 씁니다 (2026-09-29)
        '축제칸': 묶음축제칸,
        # ★ 기준일은 머리로 올렸습니다 (2026-10-01 주인 지시)
        '기준일안내': '',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        # ★ 묶음 쪽에도 물때를 놓았으니 tide.js 를 부릅니다 (2026-09-28)
        #   자리만 만들고 스크립트를 안 부르면 막대가 영영 비어 있습니다.
        #   (권역 쪽에서 한 번 겪은 일입니다 — 2024줄 주석 참고)
        '쪽스크립트': ('<script src="%s" defer></script>'
                       % url.asset('assets/js/tide.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js',
                                                       'tide.js')))
                       + (물높이그래프(쪽길, 첫['id']) if 첫 else '')
                       # ★ **긴 목록을 접습니다** — more.js (2026-09-30)
                       #   주인 지시 「하루코스 너무많아 더보기버튼으로
                       #   축소해」. 전남은 코스가 45개였습니다.
                       + ('<script src="%s" defer></script>'
                          % url.asset('assets/js/more.js', 쪽길,
                                      판번호(os.path.join(
                                          ASSETS, 'js', 'more.js'))))
                       # ★ **광고** — 권역 카드 격자의 빈 칸
                       #   (2026-10-01 주인 지시 「제주패스 광고
                       #   올릴꺼야 예쁘게 만들어서 넣어줘」)
                       + 광고움직임(쪽길, '묶음카드', 묶음)
                       # ★ 축제 팝업 — 권역 쪽과 같은 것을 씁니다
                       + 축제팝업(묶음축제목록, 쪽길)
                       # ★ 검색 자료는 **쪽에 심습니다** — 바깥에 안 물어봅니다.
                       #   인터넷이 느려도 검색은 바로 됩니다.
                       + ('<script>window.BADAGAJA_GROUP_SEARCH=%s;</script>'
                          % json.dumps(찾을것, ensure_ascii=False,
                                       separators=(',', ':')))
                       + '<script src="%s" defer></script>'
                       % url.asset('assets/js/group-search.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js',
                                                       'group-search.js')))),
    }
    return 쪽길, template.그리기('group.html', 값)


def 묶음구조화(d, 묶음, 쪽길, 포인트수, 권역수):
    이름 = d.색인['묶음이름'][묶음]['ko']
    그래프 = [
        {'@type': 'CollectionPage', 'name': '%s 바다 여행' % 이름,
         'url': url.full(쪽길), 'inLanguage': 'ko',
         'description': '%s 해안 %d권역의 포인트 %d곳'
                        % (이름, 권역수, 포인트수),
         'isPartOf': {'@type': 'WebSite', 'name': d.사이트['이름']['ko'],
                      'url': d.사이트['주소'] + '/'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': d.사이트['이름']['ko'],
             'item': d.사이트['주소'] + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 이름,
             'item': url.full(쪽길)}]},
    ]
    return json.dumps({'@context': 'https://schema.org', '@graph': 그래프},
                      ensure_ascii=False, separators=(',', ':'))


def 첫쪽(d, 언어='ko'):
    """전국 첫 화면 — 사이트로 들어오는 문입니다"""
    쪽길 = url.home(언어)
    뿌리 = './'
    # ★ 옛 저장소를 더 안 봅니다 — 사진은 사진바탕() 이 찾습니다
    #   (2026-09-28. 옛 저장소가 없는 컴퓨터에서 사진이 통째로
    #    빠지는데도 아무 말이 없었습니다)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    모두 = d.셈()                     # ★ 셉니다 (계약-04·06)
    묶음별 = d.묶음별셈()

    묶음칸 = []
    for 묶음 in d.색인['묶음차례']:
        권역들 = [r for r in d.권역들 if r['묶음'] == 묶음]
        if not 권역들:
            continue
        이름 = d.색인['묶음이름'][묶음].get(언어) or d.색인['묶음이름'][묶음]['ko']
        # ★ 사진을 얹습니다 (2026-09-27 주인 지적 — 글자만으로는
        #   고르기 어렵습니다. 휴대폰에서는 더욱 그렇습니다)
        한장 = 대표사진(d, 묶음=묶음)
        그림 = ''
        if 한장 and 한장.get('파일'):
            그림 = ('<img class="gc-photo" src="%s" alt="" '
                    'width="%d" height="%d" loading="lazy" decoding="async">'
                    % (esc(url.rel(쪽길, 한장['파일'])),
                       한장.get('가로') or 1200, 한장.get('세로') or 800))
        묶음칸.append(
            '<a class="group-card" href="%s">%s'
            '<span class="gc-text">'
            '<span class="gc-name">%s</span>'
            '<span class="gc-sub">%d권역 · 포인트 %d곳</span></span></a>'
            % (esc(url.rel(쪽길, url.group(묶음, 언어))), 그림, esc(이름),
               len(권역들), 묶음별.get(묶음, 0)))

    # ★ 찾기 카드에도 그림을 얹습니다 (2026-09-27 주인 지적)
    #   글자만 있으면 읽어야 압니다. 휴대폰에서는 읽지 않고 넘깁니다.
    def _찾기그림(무엇):
        상대 = {'물때': 'assets/cover/fish-cover.svg',
                '축제': 'assets/cover/festival-cover.svg',
                '해루질': 'assets/cover/catch-cover.svg',
                '낚시': 'assets/cover/fish-cover.svg'}.get(무엇)
        if not 상대 or not os.path.exists(
                os.path.join(ASSETS, 'cover', os.path.basename(상대))):
            return ''
        return ('<img class="gc-photo" src="%s" alt="" width="1200" '
                'height="800" loading="lazy" decoding="async">'
                % esc(url.rel(쪽길, 상대)))

    # ── 숫자 칸 — 모두 **셉니다** (주인 규칙 29)
    #   ★ 옛 쪽은 축제 190·어종 35 가 손으로 박혀 있었습니다.
    #     지금 자료는 197·104 입니다. 이미 어긋나 있었습니다.
    #
    #   ★ **다섯에서 셋으로 줄였습니다** (2026-10-01 바깥 검수)
    #
    #     「첫 화면에서 사용자의 행동보다 사이트 통계를 앞세우지
    #       않습니다. 축제 197과 먹거리 277까지 첫 화면에서 같은
    #       무게로 자랑할 필요 없습니다」
    #
    #     맞습니다. 손님이 첫 화면에서 할 일은 **어디로 갈지
    #     고르는 것**이지 이 사이트가 얼마나 큰지 읽는 것이
    #     아닙니다. 축제와 먹거리는 권역 쪽에서 만납니다.
    # ★ **숫자는 한 곳에서 셉니다** (2026-10-01 · engine/counts.py)
    #   전에는 `len(d.어종['어종'])` = **104** 를 적고
    #   「제철 어종·해루질 **안내**」라 불렀습니다. 그런데 104 는
    #   포인트에 적힌 **이름표 가짓수**이고, **안내 쪽이 있는 것은
    #   35개**뿐입니다. 손님이 104개 안내를 기대하고 눌렀다가
    #   35개를 봅니다. 「안내」라고 썼으면 안내가 있는 수를 적습니다.
    #
    #   바깥 검수가 공개판에서 찾았습니다 —
    #   「About 숫자는 바로잡았지만 사이트 전체 숫자 source-of-truth 는
    #     아직 하나가 아닙니다. **의미가 같은 통계끼리 같은 계산
    #     함수를 쓰게** 해야 합니다」
    from engine import counts as _counts
    _수 = _counts.모두(d)
    숫자칸 = ''.join(
        '<a href="%s"><b>%s</b><span>%s</span></a>'
        % (esc(url.rel(쪽길, 길)), esc(값), esc(이름))
        for 값, 이름, 길 in [
            ('%d' % _수['권역'], '전국 바다 권역', '#bada'),
            ('{:,}'.format(_수['포인트']), '해루질·낚시 포인트', '#bada'),
            ('%d' % _수['어종모두'], '제철 어종·해루질 안내', 'catch/'),
        ])

    # ── 찾기 폼과 빠른 꼬리표 (옛 쪽 그대로)
    #   ★ 옛 쪽은 guide/?q= 로 보냈습니다. 새 틀엔 그 쪽이 없어
    #     지금은 **있는 쪽으로 곧장** 보냅니다. 찾기 쪽을 만들면
    #     여기만 고치면 됩니다.
    찾기폼 = (
        '<form class="g-search" action="%s" method="get" role="search">'
        '<label class="sr-only" for="gq">권역·어종·축제·포인트 찾기</label>'
        '<svg class="g-search-ico" viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" '
        'stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round"/></svg>'
        '<input id="gq" name="q" type="search" '
        'placeholder="지금, 바다에 갈 준비 되셨나요?" autocomplete="off">'
        '<button type="submit">찾아보기</button></form>'
        % esc(url.rel(쪽길, url.festival_list(언어))))

    빠른꼬리표 = ''.join(
        '<a href="%s">%s</a>' % (esc(url.rel(쪽길, 길)), esc(이름))
        for 이름, 길 in [
            ('해루질 대상', 'catch/'),
            ('낚시 어종', 'fish/'),
            ('바다 축제', url.festival_list(언어)),
            ('오늘 물때', 'tide/'),
            ('금어기', 'rule.html'),
        ])

    # ── 01~06 걸음 카드 — **옛 쪽 그대로** (2026-09-27 주인 지시)
    #
    #   ★ 02 칸만 <div> 입니다 (2026-09-27 주인 지적으로 고침)
    #     그 칸 안에는 「낚시」·「해루질」 알약 **링크**가 들어갑니다.
    #     <a> 안에 <a> 는 넣을 수 없어, 브라우저가 안쪽을 밖으로
    #     풀어내 알약이 거대한 세로 막대가 됐습니다.
    #     옛 쪽은 그래서 02 만 <div> 로 두고 카드 전체를 덮는
    #     <a class="sc-cover"> 를 따로 깔았습니다. 그대로 따릅니다.
    #
    #   ★ 그림의 크기·대체글은 **옛 쪽 값 그대로**입니다.
    #     06 칸 270x103 은 「아이콘이 두 벌로 겹쳐 보이던 것」을
    #     그림을 잘라 고친 값입니다 (2026-09-25 주인 지적).
    #     대체글은 「빈 대체글 14곳」을 채운 것입니다 (2026-09-25,
    #     네이버 '색인 상태 확인' 이 짚어 줌). 되돌리면 안 됩니다.
    _아이콘 = {
        '낚시': '<path d="M3 12c4-4.6 10-4.6 14 0-4 4.6-10 4.6-14 0Z"/>'
                '<path d="M17 12l4-2.8v5.6L17 12Z"/><circle cx="8" cy="12" r="1"/>',
        '해루질': '<path d="M12 4c4.4 0 8 3.6 8 8v4H4v-4c0-4.4 3.6-8 8-8Z"/>'
                  '<path d="M12 4v12M8.4 4.8 6 16M15.6 4.8 18 16"/>',
        '물때': '<path d="M2 13c3 0 3-3 6-3s3 3 6 3 3-3 6-3 2 1.6 2 1.6"/>'
                '<path d="M2 18c3 0 3-3 6-3s3 3 6 3 3-3 6-3 2 1.6 2 1.6"/>',
        '날씨': '<circle cx="9" cy="9" r="3.4"/>'
                '<path d="M9 2.6v1.8M9 13.6v1.8M2.6 9h1.8M13.6 9h1.8'
                'M4.5 4.5l1.3 1.3M12.2 12.2l1.3 1.3M13.5 4.5l-1.3 1.3'
                'M5.8 12.2l-1.3 1.3"/>'
                '<path d="M11 19a3.4 3.4 0 0 1 6.5-1.4A3 3 0 1 1 18 22h-7'
                'a1.6 1.6 0 0 1 0-3Z"/>',
        '파고': '<path d="M2 10c3 0 3-3 6-3s3 3 6 3 3-3 6-3 2 1.6 2 1.6"/>'
                '<path d="M2 15c3 0 3-3 6-3s3 3 6 3 3-3 6-3 2 1.6 2 1.6"/>'
                '<path d="M2 20c3 0 3-3 6-3s3 3 6 3 3-3 6-3 2 1.6 2 1.6"/>',
        '관광': '<path d="M3 8h4l1.6-2h6.8L17 8h4v11H3V8Z"/>'
                '<circle cx="12" cy="13" r="3.4"/>',
        '맛집': '<path d="M6 3v7a2 2 0 0 0 4 0V3M8 10v11"/>'
                '<path d="M17 3c-1.4 1.6-2 3.4-2 5.4 0 1.4.8 2.6 2 2.6v10"/>',
        # ★ 「숙박」(침대)을 **「코스」(길 따라 도는 점선)**로 바꿉니다
        #   (2026-10-01 바깥 검수 지시) — 숙소 자료가 없으므로
        #   침대 그림은 **있지도 않은 것을 약속**합니다.
        #   「침대 아이콘이 있다면 여행코스를 나타내는 것으로
        #     교체해야 합니다. 이것은 새 디자인 작업이 아니라
        #     **단추의 약속을 실제 데이터와 맞추는 수정**입니다」
        '코스': '<path d="M5 19c0-4 4-4 4-7s-4-3-4-7"'
                ' stroke-dasharray="3 3"/>'
                '<circle cx="5" cy="5" r="2"/>'
                '<path d="M19 19c-3 0-5-1.5-5-4"/>'
                '<circle cx="19" cy="19" r="2"/>',
    }

    def _그림표(이름):
        return ('<svg viewBox="0 0 24 24" aria-hidden="true">%s</svg>'
                % _아이콘.get(이름, ''))

    # 그림 — 이름 · 대체글 · 가로 · 세로 (옛 쪽 값 그대로)
    _걸음그림 = {
        1: ('img/ui/step/1.webp', '전국 바다 권역을 나눈 지도', 269, 130),
        2: ('img/ui/step/2.webp', '갯바위 낚시와 갯벌 해루질', 268, 87),
        3: ('img/ui/step/3.webp', '갯바위가 늘어선 바닷가', 269, 112),
        5: ('img/ui/step/5.webp', '낚싯대와 채비함, 장화', 268, 117),
        6: ('img/ui/step/6.webp', '해산물 밥상과 바닷가 풍경', 270, 103),
    }

    def _사진(번호):
        것 = _걸음그림.get(번호)
        if not 것:
            return ''
        상대, 대체글, 넓, 높 = 것
        if 사진바탕(상대) is None:
            return ''
        return ('<img src="%s" alt="%s" loading="lazy" width="%d" '
                'height="%d">'
                % (esc(url.rel(쪽길, 상대)), esc(대체글), 넓, 높))

    # 02 — 낚시 / 해루질 알약 둘
    알약 = ''.join(
        '<a class="sc-pill %s" href="%s">%s%s</a>'
        % (반, esc(_곧은길(쪽길, 길)), _그림표(이름), esc(이름))
        for 이름, 반, 길 in (('낚시', 'pf', 'fish/'),
                             ('해루질', 'pc', 'catch/')))
    둘째속 = ('<span class="sc-ph sc-stack">%s<span class="sc-pills">%s'
              '</span></span>' % (_사진(2), 알약))

    # 04 — 물때 · 날씨 · 파고 세 줄 (사진이 없는 카드입니다)
    세줄 = ''.join(
        '<span class="si">%s<b>%s</b><em id="%s">%s</em></span>'
        % (_그림표(이름), esc(이름), 아이디, esc(값))
        for 이름, 아이디, 값 in (('물때', 'stTide', '오늘 물때'),
                                 ('날씨', 'stSky', '오늘 날씨'),
                                 ('파고', 'stWave', '바다 상태')))
    넷째속 = '<span class="sc-ph sc-info">%s</span>' % 세줄

    # 06 — 관광 · 먹거리 · 코스 셋
    셋 = ''.join(
        '<span class="sc-one">%s%s</span>' % (_그림표(이름), esc(이름))
        for 이름 in ('관광', '맛집', '코스'))
    여섯째속 = ('<span class="sc-ph sc-stack">%s<span class="sc-trio">%s'
                '</span></span>' % (_사진(6), 셋))

    걸음들 = [
        ('01', '어디로 갈까?', '%d개 바다 권역' % len(d.권역들),
         '전남 · 제주 · 경남 · 강원 등', '#1F6FB2', '#EAF3FB',
         '<span class="sc-ph">%s</span>' % _사진(1), '#bada', False),
        ('02', '무엇을 할까?', '낚시 · 해루질', '낚시 / 해루질 선택',
         '#1E8A5F', '#E9F6F0', 둘째속, 'catch/', True),
        ('03', '어디서 할까?', '{:,}개 포인트'.format(모두),
         '갯벌 · 갯바위 · 방파제 · 선착장', '#E08A1E', '#FDF4E6',
         '<span class="sc-ph">%s</span>' % _사진(3), '#bada', False),
        # ★ 옛 쪽처럼 전국 물때표(tide/)로 보냅니다 (2026-09-27 주인 확인)
        #   제가 같은 쪽 안 물때 칸(#tide)으로 바꿔 놨었습니다.
        ('04', '오늘 괜찮을까?', '물때 · 날씨 · 파고',
         '간조 · 만조 · 바람 · 파고', '#7A4FC0', '#F2EDFB', 넷째속,
         'tide/', False),
        # ★ **채비법 쪽으로 보냅니다** (2026-09-30 주인 지시)
        #   「그 자료를 홈에서도 활용하게」
        #   전에는 옛 사이트의 `gear.html` 로 보냈습니다. 새 사이트는
        #   그 쪽을 만들지 않으니 **우리가 만든 쪽**으로 보냅니다.
        ('05', '무엇을 준비할까?', '채비 · 장비 · 미끼',
         '원투 · 찌낚시 · 카드채비 · 에기', '#0F9A9A', '#E5F6F5',
         '<span class="sc-ph">%s</span>' % _사진(5), 'rig/', False),
        ('06', '무엇을 즐길까?', '관광 · 먹거리 · 여행코스',
         '명소 · 지역 음식 · 하루 코스', '#D9558A', '#FCECF3',
         여섯째속, 'travel/', False),
    ]
    걸음칸 = []
    for 차례, (번호, 제목, 작은, 아래, 색, 바탕, 속, 길,
               안에링크있나) in enumerate(걸음들):
        몸 = ('<span class="sc-h"><b class="sc-no">%s</b>'
              '<span class="sc-t">%s</span></span>'
              '<span class="sc-s">%s</span>%s'
              '<span class="sc-d">%s</span>'
              % (번호, esc(제목), esc(작은), 속, esc(아래)))
        if 안에링크있나:
            # ★ 안에 링크가 있으면 카드를 <div> 로 둡니다 — <a> 안에
            #   <a> 를 넣으면 브라우저가 풀어 헤칩니다 (2026-09-27)
            걸음칸.append(
                '<div class="sc sc-two" style="--c:%s;--bg:%s">'
                '<a class="sc-cover" href="%s" aria-label="%s"></a>'
                '%s</div>'
                % (색, 바탕, esc(_곧은길(쪽길, 길)),
                   esc('%s 보기' % 제목.rstrip('?')), 몸))
        else:
            걸음칸.append(
                '<a class="sc" style="--c:%s;--bg:%s" href="%s">%s</a>'
                % (색, 바탕, esc(_곧은길(쪽길, 길)), 몸))
        if 차례 < len(걸음들) - 1:
            걸음칸.append('<span class="st-ar" aria-hidden="true">&rsaquo;</span>')

    # ── 물때 칸 사진
    물때한장 = 대표사진(d, 권역='sinan') or 대표사진(d)
    물때사진 = ''
    if 물때한장 and 물때한장.get('파일'):
        # ★ **어디 물때인지 사진 위에 밝힙니다** (2026-09-30 주인 지적)
        #   「현재 어디를 보여주고 있는지도 안나오고 있어」
        #
        #   옛 첫 쪽에는 사진 위에 「전남 신안」 같은 이름표가
        #   있었습니다(index.html 의 `<span class="gt-tag" id="gtTag">`).
        #   제 쪽에는 그것이 없어 **어느 바다 물때인지 알 수 없었습니다.**
        #   첫 쪽은 권역이 없으니 기준 관측소를 밝혀야 정직합니다.
        _기준권역 = d.권역(첫물때권역(d))
        _기준이름 = ((_기준권역 or {}).get('이름') or {}).get(언어)             or ((_기준권역 or {}).get('이름') or {}).get('ko') or ''
        물때사진 = (
            '<a class="gt-ph" href="%s">'
            '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy">'
            '%s'
            '<span class="gt-cap">오늘 물때와 날씨를 확인하고 출발하세요</span>'
            '</a>'
            % (esc(url.rel(쪽길, 'tide/')),
               esc(url.rel(쪽길, 물때한장['파일'])),
               esc(물때한장.get('제목') or ''),
               물때한장.get('가로') or 1200, 물때한장.get('세로') or 800,
               ('<span class="gt-tag" id="gtTag">%s 기준</span>'
                % esc(_기준이름)) if _기준이름 else ''))

    # ── 초보자 가이드 — 어종 사진을 씁니다
    가이드들 = [
        # ★ **준비물은 따로 쪽이 있습니다** (2026-10-02 주인 지적)
        #   「이거 두개가 같은 링크를 가르키고 있어」 — 준비물과
        #   대상 17가지가 둘 다 catch/ 로 갔습니다. 역할이 다릅니다.
        ('bajirak', '초보자를 위한 해루질 준비물',
         '장화·장갑·망부터, 무엇을 왜 챙기는지', 'catch/gear.html'),
        ('matjogae', '해루질 대상 %d가지' % len(d.안내('해루질')),
         '바지락·맛조개·낙지까지, 대상별 시기와 잡는 법', 'catch/'),
        ('ureok', '낚시 어종 %d가지' % len(d.안내('낚시')),
         # ★ 「기타 준비물 안내」를 뺐습니다 (2026-10-02)
         #   fish/ 에는 준비물이 **없습니다.** 적어 놓고 보내면
         #   손님이 찾다가 못 찾습니다. 글은 간 쪽에 있는 것만 적습니다.
         '어종별 채비법과 입질이 오는 자리', 'fish/'),
        ('nakji', '금어기·크기·마을어장',
         '잡으면 안 되는 철과 크기, 들어가면 안 되는 구역', 'rule.html'),
    ]
    가이드칸 = []
    for 어종, 제목, 작은, 길 in 가이드들:
        한장 = d.어종사진(어종)
        그림 = ''
        if 한장 and 한장.get('파일'):
            그림 = ('<span class="gb-th"><img src="%s" alt="" '
                    'loading="lazy" decoding="async"></span>'
                    % esc(url.rel(쪽길, 한장['파일'])))
        가이드칸.append(
            '<a class="gb" href="%s">%s<span class="gb-tx">'
            '<b>%s</b><small>%s</small></span></a>'
            % (esc(url.rel(쪽길, 길)), 그림, esc(제목), esc(작은)))

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        # ★ 첫 화면 제목은 **자료가 정합니다** (2026-09-27 바깥 검수 지시 14)
        #
        #   「기존 검색 노출 제목을 유지한다. 새 디자인/HTML 구조와
        #     검색 title 변경을 동시에 진행하지 않는다. 특히 3603곳
        #     숫자가 자동으로 갱신되지 않는다면 title 에 쓰지 않는다」
        #
        #   전에는 「… 포인트 %d곳」처럼 숫자를 넣었는데, 자료가 늘면
        #   제목이 바뀝니다. 검색 제목을 자주 바꾸면 불이익입니다.
        #   지금 네이버에 뜨는 제목을 그대로 씁니다.
        '제목': 첫화면제목(d, 언어),
        '짧은제목': '%s — 물때에 맞춰 떠나는 바다 여행' % d.사이트['이름']['ko'],
        # ★ **설명은 제목이 안 하는 말을 합니다** (2026-09-28)
        #
        #   전에는 이랬습니다.
        #
        #     제목  … 전국 물때표와 3,500곳 이상의 해루질·낚시 포인트
        #     설명  전국 57권역의 물때와 해루질·낚시 포인트 3603곳, …
        #
        #   같은 말을 두 번 합니다. 네이버 가이드는 되풀이에
        #   불이익을 줍니다(주인 규칙 28). 게다가 손님이 검색 결과에서
        #   **두 줄을 읽고도 새로 아는 것이 없습니다.**
        #
        #   그래서 제목은 「규모」를, 설명은 「무엇을 더 볼 수 있는지」를
        #   맡습니다. 숫자는 제목에 이미 있으니 여기서는 뺍니다.
        '설명': '어느 물때에 어디로 가야 하는지. 전국 %d개 권역을 '
                '지역별로 나눠 제철 어종·금어기·축제까지 '
                '한곳에 모았습니다.' % len(d.권역들),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 사진주소(d, 대표사진(d)),
        # ★ 첫 화면은 사진을 **배경으로 깔고** 그 위에 글자를 얹습니다
        #   (2026-09-27 주인 지적 — 옛 쪽이 그랬고, 그게 더 좋습니다)
        '히어로사진': 히어로사진(d, 대표사진(d), 쪽길),
        '히어로설명': 히어로설명(대표사진(d)),
        '브랜드각인': 브랜드각인(d, 언어),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.home(언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': d.사이트['이름']['ko'],
            'url': d.사이트['주소'] + '/',
            'inLanguage': 'ko',
            'description': '전국 %d권역의 물때와 해루질·낚시 포인트 %d곳'
                           % (len(d.권역들), 모두),
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '물때에 맞춰 떠나는 바다 여행',
        '기준일조각': 기준일조각(),
        '머리이름표': ''.join([
            이름표('%d권역' % len(d.권역들), 'badge--orange'),
            이름표('현장 확인 필수', 'badge--green'),
        ]),
        '돌아갈주소': '#bada',
        '돌아갈글': '어느 바다로 갈까요',
        '권역이름': '전국',
        '메일': d.사이트['메일'],
        '한줄': '%s 직접 정리한 전국 바다 안내' % 조사(d.사이트['이름']['ko'], '이'),
        '큰제목': '바다를 알고 가면',
        '큰제목뒷줄': '즐겁습니다',
        '소개글': '첫 갯벌에서 무엇을 찾아야 하는지, 어느 물때에 어디로 가야 '
                  '하는지 — 전국 바다의 포인트를 물때와 함께 '
                  '안내합니다.',
        '묶음안내': '묶음을 먼저 고르고, 그 안에서 권역을 고르시면 됩니다.',
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko'], True),
        '꼬리로고': 꼬리로고(뿌리, d.사이트['이름'].get(언어)
                             or d.사이트['이름']['ko'], True),
        '큰제목앞': '바다가 더',
        '찾기폼': 찾기폼,
        '빠른꼬리표': 빠른꼬리표,
        '걸음칸': ''.join(걸음칸),
        '물때쪽': esc(url.rel(쪽길, 'tide/')),
        '물때사진': 물때사진,
        '물때안내': '오늘 물때를 부르는 중입니다.',
        # ★ 첫 쪽은 권역이 없으니 **기준 관측소를 자료에서** 읽습니다.
        #   틀에 박지 않습니다 (계약-04). 쪽에는 「기준 관측소 ○○」이
        #   함께 나와 어느 바다인지 숨기지 않습니다.
        '물때기준권역': esc(첫물때권역(d)),
        '가이드칸': ''.join(가이드칸),
        '동호회칸': 동호회칸(d),
        # ★ 첫 화면만 옛 짜임 차림표를 함께 싣습니다
        '집차림표': ('<link rel="stylesheet" href="%s">'
                     % url.asset('assets/css/home.css', 쪽길,
                                 판번호(os.path.join(ASSETS, 'css',
                                                     'home.css')))),
        '바다지도': 바다지도(d, 쪽길, 언어),
        '지도차림표': 지도차림표(d, 쪽길, 언어),
        '묶음칸': ''.join(묶음칸),
        '숫자칸': 숫자칸,
        '광고칸': 광고칸('첫화면'),
        # ★ 기준일은 머리로 올렸습니다 (2026-10-01 주인 지시)
        '기준일안내': '',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        # ★ 첫 화면에도 물때 움직임을 싣습니다 (2026-09-27)
        #   물때 칸을 넣었는데 tide.js 가 없어 「계산 중」에서 멈췄습니다.
        #
        #   ★ **물높이 그래프도 함께 싣습니다** (2026-09-29 주인 지적)
        #     「전에 있었던 그래프 축소판도 안보이고」
        #
        #     까닭: tidegraph.css 에
        #         .g-today .gt-graph:not(:has(.tg-plot)){display:none}
        #     이 있어 **곡선이 없으면 칸을 통째로 숨깁니다.**
        #     그런데 첫 쪽에는 tide-graph.js 를 안 실어서 곡선이
        #     영영 안 생기고, 칸이 늘 숨어 있었습니다.
        #     빈 칸을 접는 것은 옳은데, **실을 것을 안 실은 것**이 탈입니다.
        '쪽스크립트': ('<script src="%s" defer></script>'
                       % url.asset('assets/js/tide.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js',
                                                       'tide.js')))
                       + 물높이그래프(쪽길, 첫물때권역(d))
                       + 광고움직임(쪽길, '첫화면')),
    }
    return 쪽길, template.그리기('home.html', 값)


달이름 = ['1월', '2월', '3월', '4월', '5월', '6월',
          '7월', '8월', '9월', '10월', '11월', '12월']
철이름 = {12: '겨울', 1: '겨울', 2: '겨울', 3: '봄', 4: '봄', 5: '봄',
          6: '여름', 7: '여름', 8: '여름', 9: '가을', 10: '가을', 11: '가을'}


def 축제쪽(d, 축제, 언어='ko'):
    """축제 쪽 하나 — 소개글·프로그램·가는 법·주변까지"""
    권역 = d.권역(축제['권역'])
    권역이름 = 권역['이름'].get(언어) or 권역['이름']['ko']
    이름 = 축제['이름'].get(언어) or 축제['이름']['ko']
    쪽길 = url.festival(축제['id'], 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    묶음 = 권역['묶음']
    묶음이름 = d.색인['묶음이름'][묶음].get(언어) or d.색인['묶음이름'][묶음]['ko']
    달 = 축제.get('달')

    def 글꾸러미(v):
        """{'ko':…} 에서 글을 꺼냅니다. 없으면 None"""
        if not isinstance(v, dict):
            return v or None
        return v.get(언어) or v.get('ko') or None

    # ── 길찾기 (빵부스러기)
    길찾기 = ''.join([
        '<a href="%s">%s</a>' % (esc(url.rel(쪽길, url.home(언어))),
                                 esc(d.사이트['이름']['ko'])),
        '<span>›</span>',
        '<a href="%s">%s 축제</a>' % (esc(url.rel(쪽길, url.group(묶음, 언어))),
                                      esc(묶음이름)),
        '<span>›</span>',
        '<a href="%s">%s</a>' % (esc(url.rel(쪽길, url.region(축제['권역'], 언어))),
                                 esc(권역이름)),
    ])

    # ── 한눈에 보기 — **행사 핵심정보**
    # ★ 바깥 검수가 고쳐 준 차례 (2026-10-01)
    #   「넣는다면 소개글 다음이 아니라 **H1 직후의 행사 핵심정보
    #     영역**이 좋습니다. 다만 부안처럼 통계 카드 형태를 그대로
    #     복제하지 마세요. 축제 사용자가 원하는 답은 완전히 다릅니다 —
    #     언제 / 어디서 / **무엇을** / **가기 전에** / 공식 안내」
    #
    #   그 말이 맞습니다. 전에는 「열리는 시기·장소·지역」만 있어
    #   **「가서 무엇을 하나」에 답하지 않았습니다.** 축제를 찾는 사람이
    #   가장 먼저 알고 싶은 것이 그것인데도요.
    _때, _때설명 = 축제때상태(축제)
    칸들 = [('언제', _때설명),
            ('어디서', 축제.get('곳') or '%s 일원' % 권역이름)]
    # ★ **무엇을** — 프로그램에서 **셉니다.** 지어내지 않습니다.
    _프 = 축제.get('프로그램') or []
    if _프:
        _앞 = ' · '.join(x.split('와 ')[0].split(',')[0].strip()
                         for x in _프[:3])
        칸들.append(('무엇을', '%s%s'
                     % (_앞, ' 등 %d가지' % len(_프) if len(_프) > 3 else '')))
    if 축제.get('지난해'):
        칸들.append(('지난 개최', 축제['지난해']))
    # ★ **입장료·문의**를 함께 냅니다 (2026-10-01 주인 지시)
    #   「정확한 일정이나 행사관련 링크가 나왔다면 …페이지에 기록해」
    if 축제.get('입장료'):
        칸들.append(('입장료', 축제['입장료']))
    if 축제.get('문의'):
        칸들.append(('문의', 축제['문의']))
    # ★ **알아둘 것** — 자료 첫 줄을 머리로 올립니다 (2026-10-01 바깥 검수)
    #   「가기 전에 주차/운영시간/변경 가능 여부」를 핵심정보에 두라는
    #   지적입니다. 자료의 `알아둘것` 에 바로 그런 것이 많은데
    #   (「첫날에는 한 개 차로와 공영주차장을 통제합니다」
    #    「불꽃쇼는 저녁 7시부터입니다. 자리를 잡으려면 일찍 가야」
    #    「명선도는 물때에 맞춰서만 건널 수 있습니다」)
    #   쪽 한참 아래에만 있어 **못 보고 출발하던** 것입니다.
    #
    # ★ 칸 이름을 「가기 전에」로 **안 씁니다**
    #   190개 첫 줄을 보니 시각·주차·물때 같은 것이 많지만
    #   「멸치회는 뼈째 썰어 냅니다」처럼 **먹는 법**도 섞여 있습니다.
    #   말만 보고 가릴 수 없으니, 자료의 칸 이름을 그대로 씁니다.
    #   일정이 바뀔 수 있다는 경고는 **머리 이름표**가 맡습니다.
    _알 = 축제.get('알아둘것') or []
    칸들.append(('알아둘 것',
                 _알[0] if _알 else
                 '날짜·시간은 해마다 바뀝니다. 주최 측 공지를 확인하세요'))
    # ★ **글이 긴 칸은 한 줄을 통째로** 씁니다 (2026-10-01)
    #   390px 에서 보니 「무엇을」이 두 줄로 꺾이는데 옆 칸은 한 줄이라
    #   들쭉날쭉했습니다. 긴 칸만 넓게 둡니다 (`.fact--wide`).
    _넓게 = ('무엇을', '알아둘 것', '공식 안내')
    한눈에 = ''.join(
        '<div class="fact%s"><span class="f-k">%s</span>'
        '<span class="f-v">%s</span></div>'
        % (' fact--wide' if k in _넓게 else '', esc(k), esc(v))
        for k, v in 칸들 if v)

    # ★ **공식 누리집** — 공공기관 쪽만 (주인 규칙 12)
    #   자료에 개인 사이트를 적어도 쪽에는 안 나갑니다.
    #   막는 곳을 **여기 한 곳**에 두어야 다음에도 새지 않습니다.
    공식 = (축제.get('공식쪽') or '').strip()
    if 공식:
        _터 = 공식.split('//', 1)[-1].split('/', 1)[0].lower()
        if not (_터.endswith('.go.kr') or _터.endswith('.or.kr')):
            공식 = ''          # 개인·회사 쪽은 안내하지 않습니다
    if 공식:
        한눈에 += ('<div class="fact"><span class="f-k">공식 안내</span>'
                   '<span class="f-v"><a href="%s" target="_blank" '
                   'rel="noopener">주최 측 누리집 →</a></span></div>'
                   % esc(공식))

    # ── 소개글 · 프로그램
    소개글 = 글꾸러미(축제.get('소개'))
    소개 = ('<p class="long">%s</p>' % esc(소개글) if 소개글 else
            '<p class="notice">이 축제의 자세한 안내를 준비하고 있습니다. '
            '아래 일정과 장소를 먼저 참고해 주세요.</p>')
    프로그램 = ''
    if 축제.get('프로그램'):
        # ★ 오른쪽 칸으로 갑니다 (template/festival.html `.two-col`)
        프로그램 = ('<aside class="two-col-b">'
                    '<h3 class="sub-head">주요 프로그램</h3>'
                    '<ul class="dots">%s</ul></aside>'
                    % ''.join('<li>%s</li>' % esc(x) for x in 축제['프로그램']))

    # ── 가는 법 · 알아둘 것 · 가까운 곳
    가는글 = 글꾸러미(축제.get('가는법'))
    가는법 = ('<p class="long">%s</p>' % esc(가는글) if 가는글 else
              '<p class="notice">가시는 길은 주최 측 공지를 확인해 주세요.</p>')
    # ★ **첫 줄은 빼고 냅니다** — 머리 핵심정보에 이미 올렸습니다
    #   (2026-10-01 390px 로 보니 같은 글이 위아래에 두 번 나왔습니다)
    #   한 줄뿐이면 이 상자를 아예 내지 않습니다.
    알아둘것 = ''
    _남은알 = (축제.get('알아둘것') or [])[1:]
    if _남은알:
        알아둘것 = ('<div class="note-box"><h3>더 알아둘 것</h3>'
                    '<ul>%s</ul></div>'
                    % ''.join('<li>%s</li>' % esc(x) for x in _남은알))
    가까운곳 = ''
    if 축제.get('가까운곳'):
        가까운곳 = ('<h3 class="sub-head">축제장 가까이 볼 곳</h3>'
                    '<ul class="dots">%s</ul>'
                    % ''.join('<li>%s</li>' % esc(x) for x in 축제['가까운곳']))

    # ── 바다 이야기 + 그 권역으로 가는 길
    바다글 = 글꾸러미(축제.get('바다이야기'))
    바다이야기 = ('<p class="long">%s</p>' % esc(바다글) if 바다글 else '')

    권역칸 = []
    낚시수, 해루질수 = d.셈(축제['권역'], '낚시'), d.셈(축제['권역'], '해루질')
    권역칸.append(
        '<a class="card card--go" href="%s">'
        '<h3 class="card-name">%s 바다 안내</h3>'
        '<p class="card-body">오늘 물때와 제철 어종, 먹거리와 명소를 '
        '한곳에 모았습니다.</p></a>'
        % (esc(url.rel(쪽길, url.region(축제['권역'], 언어))),
           esc(권역이름)))
    for 갈래, 수 in (('낚시', 낚시수), ('해루질', 해루질수)):
        if not 수:
            continue
        권역칸.append(
            '<a class="card card--go" href="%s">'
            '<h3 class="card-name">%s %s 포인트</h3>'
            '<p class="card-body">%s에서 %s 할 수 있는 자리 <b>%d곳</b>.</p></a>'
            % (esc(url.rel(쪽길, url.point_list(축제['권역'], 갈래, 언어))),
               esc(권역이름), esc(갈래), esc(권역이름), esc(갈래), 수))

    # ── 같은 권역의 다른 축제
    다른것 = [x for x in d.축제(축제['권역']) if x['id'] != 축제['id']]
    다른축제 = ''.join(
        '<a class="card card--go" href="%s">'
        '<div class="card-head"><h3 class="card-name">%s</h3>%s</div>'
        '<p class="card-body">%s</p></a>'
        % (esc(url.rel(쪽길, url.festival(x['id'], 언어))),
           esc(x['이름'].get(언어) or x['이름']['ko']),
           이름표('%s' % 달이름[x['달'] - 1]) if x.get('달') else '',
           esc(x.get('한줄') or ''))
        for x in 다른것)
    if not 다른축제:
        다른축제 = ('<p class="notice">%s에서 저희가 아는 축제는 이것 '
                    '하나입니다.</p>' % esc(권역이름))

    언제어디 = '%s · %s%s' % (
        권역이름,
        '%s · ' % 달이름[달 - 1] if 달 else '',
        '%s 축제' % 철이름.get(달, '') if 달 else '축제')

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        # ★ 권역을 넣습니다 (2026-09-27 engine/check_seo.py 가 잡음)
        #   명량대첩축제처럼 **두 권역에 걸친 축제**가 있습니다.
        #   해남 쪽과 진도 쪽의 제목이 똑같아 검색엔진이 한 쪽을
        #   겹친 것으로 봅니다. 권역을 넣으면 갈립니다.
        '제목': '%s %s일정·가는 길 — %s | %s'
                % (이름, '%s ' % 달이름[달 - 1] if 달 else '',
                   권역이름, d.사이트['이름']['ko']),
        '짧은제목': '%s — %s%s' % (이름, 권역이름,
                                   ' %s' % 달이름[달 - 1] if 달 else ''),
        # ★ 설명에도 권역·축제 이름을 넣습니다 (2026-09-27 check_seo 가 잡음)
        #   자료의 「한줄」이 여러 축제에 같은 값인 경우가 있습니다
        #   (「해수욕 · 해양레저 성수기 시작」이 보성·여수 두 쪽에).
        #   검색엔진은 설명이 같으면 한 쪽을 겹친 것으로 봅니다.
        '설명': 축제설명(이름, 권역이름,
                         축제.get('한줄') or 소개글),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        # ★ 같은 권역 축제가 여럿이면 **사진을 돌려 씁니다**
        #   (2026-10-01) 신안 축제 10쪽이 모두 같은 사진이라
        #   카카오톡에 어느 축제를 나눠도 같은 그림이 떴습니다.
        '대표사진': 돌려쓸사진(
            d, 축제['권역'],
            [x['id'] for x in d.축제들
             if x['권역'] == 축제['권역']].index(축제['id']) + 1,
            사진주소(d, 대표사진(d, 권역=축제['권역']))),
        '대표사진자리': 사진자리(d, 대표사진(d, 권역=축제['권역']), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.festival(축제['id'], 언)),
        '구조화자료': 축제구조화(d, 축제, 쪽길, 권역이름),
        '머리말': '%s 축제 안내' % 권역이름,
        '기준일조각': 기준일조각(),
        # ★ **지금 어느 때인가**를 밝힙니다 (2026-10-01 바깥 검수)
        #   「행사 종료 페이지는 반드시 상태가 보여야 합니다」
        #   전에는 197쪽 모두 「일정 확인 필수」로 똑같았습니다.
        #   이제 자료의 달과 오늘을 견주어 **이번 달·다음 달·지난 N월**
        #   을 가립니다. 날짜·연도는 **짓지 않습니다** — 자료에 없습니다.
        '머리이름표': ''.join([
            이름표(권역이름, 'badge--orange'),
            이름표(_때, 'badge--green' if _때 in ('이번 달', '다음 달')
                   else ''),
            이름표('올해 일정 확인 필요'),
        ]),
        '돌아갈주소': url.rel(쪽길, url.region(축제['권역'], 언어)),
        '돌아갈글': '%s 권역으로' % 권역이름,
        '권역이름': 권역이름,
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '축제': 축제['id'],
        '축제이름': 이름,
        '언제어디': 언제어디,
        '한줄': 축제.get('한줄') or '%s에서 열리는 축제입니다.' % 권역이름,
        '길찾기': 길찾기,
        '한눈에': 한눈에,
        '소개': 소개,
        '프로그램': 프로그램,
        '가는법': 가는법,
        '알아둘것': 알아둘것,
        '가까운곳': 가까운곳,
        '바다이야기': 바다이야기,
        '바다묶음': 축제바다묶음(d, 축제, 권역이름, 쪽길, 언어),
        '권역칸': ''.join(권역칸),
        '다른축제': 다른축제,
        '기준일안내': '일정과 프로그램은 해마다 바뀝니다. 가시기 전에 주최 측 '
                      '공지를 꼭 확인해 주세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        # ★ 이번 달·다음 달은 **보는 그날** 기준으로 (2026-10-01)
        #   쪽에는 「보통 4월」만 박고, 여기서 더합니다. 자세한 까닭은
        #   `축제때상태()` 와 `assets/js/fest-when.js` 머리글.
        '달숫자': str(달) if 달 else '',
        '쪽스크립트': ('<script src="%s" defer></script>'
                       % url.asset('assets/js/fest-when.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js',
                                                       'fest-when.js')))),
    }
    return 쪽길, template.그리기('festival.html', 값)


def 축제구조화(d, 축제, 쪽길, 권역이름):
    이름 = 축제['이름']['ko']
    것 = {'@type': 'Event', 'name': 이름,
          'url': url.full(쪽길),
          'eventStatus': 'https://schema.org/EventScheduled',
          'location': {'@type': 'Place', 'name': 축제.get('곳') or 권역이름,
                       'address': {'@type': 'PostalAddress',
                                   'addressLocality': 권역이름,
                                   'addressCountry': 'KR'}}}
    소개 = (축제.get('소개') or {}).get('ko')
    if 소개:
        것['description'] = 소개[:300]
    그래프 = [것, {
        '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': d.사이트['이름']['ko'],
             'item': d.사이트['주소'] + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 권역이름,
             'item': url.full(url.region(축제['권역']))},
            {'@type': 'ListItem', 'position': 3, 'name': 이름,
             'item': url.full(쪽길)}]}]
    return json.dumps({'@context': 'https://schema.org', '@graph': 그래프},
                      ensure_ascii=False, separators=(',', ':'))


def 축제달력(d, 언어='ko'):
    """전국 축제 달력 — 197쪽으로 들어가는 문입니다.

    ★ **시각형으로 다시 지었습니다** (2026-10-02 지피티 시안 v1)

      전에는 큰 제목 · 막대 그림 · 단추 두 줄 · 글자 카드 197개
      였습니다. 바다 사이트인데 **첫 화면에 바다가 한 장도
      없었습니다**(주인 규칙 6-1).

      바꾼 것 넷 —
        ① 머리를 **큰 바다 사진**으로
        ② 12달을 **막대 단추**로 (그 달 축제 수가 길이로 보입니다)
        ③ 달마다 **사진 카드 셋**을 앞세웁니다
        ④ 197개 링크는 **하나도 안 없앴습니다** — 달 묶음
           `<details>` 안에 그대로 있습니다 (지피티 지시)

    ★ 축제 자료에는 **사진이 없습니다.** 그래서 그 축제가 열리는
      **권역의 대표 사진**을 씁니다 (지피티가 정한 차례 —
      실제 축제 사진 → 권역 히어로 → 그래도 없으면 GPT 에 목록).
      **짐작해 주소를 만들지 않습니다** (주인 규칙 6-1).

    ★ 숫자는 **자료에서 셉니다** (주인 규칙 29).
    """
    쪽길 = url.festival_list(언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    모두 = d.축제들
    수 = len(모두)                      # ★ 셉니다 (계약-04·06)

    권역묶음 = dict((r['id'], r['묶음']) for r in d.권역들)
    권역이름 = dict((r['id'], r['이름'].get(언어) or r['이름']['ko'])
                    for r in d.권역들)

    # ── 달별로 가릅니다 (한 번만 — 계약-01)
    달별 = collections.defaultdict(list)
    for x in 모두:
        달별[x.get('달') or 0].append(x)
    달센것 = dict((m, len(달별.get(m) or [])) for m in range(1, 13))
    최대달 = max(달센것.values()) or 1

    # ★ **쪽에는 「이달」을 박지 않습니다** (2026-10-02 check_calendar)
    #   처음에는 쪽을 만든 때의 달을 찍고 자바스크립트로 고치게
    #   했습니다. 검사기가 막았고, 검사기가 옳았습니다 —
    #     · 달이 바뀌면 **캐시에 남은 쪽**이 틀립니다
    #     · **검색엔진이 읽는 HTML** 은 자바스크립트를 안 돌립니다
    #     · 달마다 500여 쪽을 다시 만들라면 언젠가 잊습니다
    #   그래서 이 쪽은 **한 해 전체**로 만들고, 자바스크립트가
    #   보는 날의 달을 골라 줍니다. 자바스크립트가 죽어도 축제
    #   197개는 다 보입니다 — 달 묶음을 펼친 채로 만듭니다.

    # ── 묶음 단추 — 축제가 있는 묶음만 (계약-11)
    묶음센것 = collections.Counter(권역묶음.get(x['권역']) for x in 모두)
    묶음단추 = ['<button type="button" aria-pressed="true" '
                'data-group="전체">전체 <b>%d</b></button>' % 수]
    for 묶음 in d.색인['묶음차례']:
        n = 묶음센것.get(묶음, 0)
        if not n:
            continue
        이름 = d.색인['묶음이름'][묶음].get(언어) or d.색인['묶음이름'][묶음]['ko']
        묶음단추.append(
            '<button type="button" aria-pressed="false" data-group="%s">'
            '%s <b>%d</b></button>' % (esc(묶음), esc(이름), n))

    # ★ 축제가 가장 많은 지역 — **자료에서 셉니다** (주인 규칙 29)
    많은묶음 = max(묶음센것, key=lambda g: 묶음센것[g])
    많은묶음수 = 묶음센것[많은묶음]
    많은묶음이름 = (d.색인['묶음이름'][많은묶음].get(언어)
                    or d.색인['묶음이름'][많은묶음]['ko'])

    # ── 달 단추 — ★ **막대 길이가 그 달 축제 수**입니다
    #   주인 규칙 6-1 — 「숫자를 글로만 적지 말고 길이·색으로도」
    # ★ **「한 해 전체」를 되살립니다** (2026-10-02 골든이 알려 줌)
    #   옛 쪽에는 「한 해 내내」 단추가 있었는데 새 짜임에서
    #   빠졌습니다. 그러면 12달을 한 번에 보려고 묶음을 **손으로
    #   열두 번** 펴야 합니다. 지피티 지시의 뜻은 「이번 달만
    #   펼치고 나머지는 접는다」이지 「전체 보기를 없앤다」가
    #   아닙니다. 골든이 「단추 221 → 220」으로 알려 주었습니다.
    달단추 = ['<button type="button" class="month-btn month-btn--all" '
              'data-month="전체" aria-pressed="false">'
              '<b>한 해</b><span>%d개</span></button>' % 수]
    for m in range(1, 13):
        n = 달센것.get(m, 0)
        길이 = max(6, round(n / 최대달 * 100))
        달단추.append(
            '<button type="button" class="month-btn" '
            'style="--w:%d%%" data-month="%d" aria-pressed="false"%s>'
            '<b>%d월</b><span>%s</span><i></i></button>'
            % (길이, m, ' disabled' if not n else '',
               m, ('%d개' % n) if n else '없음'))

    # ── 사진 카드 — 달마다 셋씩. 고른 달만 보입니다
    카드들 = []
    for m in range(1, 13):
        것들 = 달별.get(m) or []
        if not 것들:
            continue
        쓴권역, 뽑은것 = set(), []
        for 차례 in (0, 1):
            for x in 것들:
                if len(뽑은것) >= 3:
                    break
                if 차례 == 0 and x['권역'] in 쓴권역:
                    continue    # 첫 바퀴는 **서로 다른 권역**으로
                if x in 뽑은것:
                    continue
                한장 = d.히어로(x['권역'])
                if not (한장 and 한장.get('파일')):
                    continue
                쓴권역.add(x['권역'])
                뽑은것.append(x)
        for x in 뽑은것:
            카드들.append(_축제사진카드(d, x, 쪽길, m,
                                       권역묶음, 권역이름, 언어))

    # ── 달별 목록 — ★ **197개를 하나도 안 없앱니다**
    #   `<details>` 를 **펼친 채로** 만듭니다. 자바스크립트가
    #   이번 달만 남기고 접습니다. 거꾸로 하면 자바스크립트가
    #   죽을 때 축제가 한 줄도 안 보입니다 (계약-23).
    덩이들 = []
    for m in list(range(1, 13)) + [0]:
        것들 = 달별.get(m) or []
        if not 것들:
            continue
        머리 = 달이름[m - 1] if m else '달을 아직 모르는 축제'
        카드 = ''.join(
            '<a class="month-link fest-item" href="%s" '
            'data-group="%s" data-month="%s">'
            '<b>%s</b><span>%s%s</span></a>'
            % (esc(url.rel(쪽길, url.festival(x['id'], 언어))),
               esc(권역묶음.get(x['권역']) or ''),
               m or '',
               esc(x['이름'].get(언어) or x['이름']['ko']),
               esc(권역이름.get(x['권역']) or x['권역']),
               (' · ' + esc(x.get('곳') or '')) if x.get('곳') else '')
            for x in 것들)
        덩이들.append(
            # ★ 달 이름은 **중제목(h2)** 으로 둡니다 (2026-10-02)
            #   `<details>` 로 바꾸면서 제목 표식이 통째로 사라져
            #   check_design 이 「중제목 15 → 4」로 알렸습니다.
            #   접었다 폈다 하는 것과 **문서 짜임**은 다른 일입니다 —
            #   검색과 읽기 보조는 제목 표식을 보고 차례를 읽습니다.
            #   「달마다 모두 보기」 칸 머리(h2) 아래이므로 h3 입니다.
            '<details class="month-group" data-month="%s" open>'
            '<summary><h3 class="month-title"><strong>%s</strong>'
            '<span>축제 %d개</span></h3></summary>'
            '<div class="month-list">%s</div></details>'
            % (m or '', esc(머리), len(것들), 카드))

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '전국 바다 축제 달력 — 축제 %d개 | %s'
                % (수, d.사이트['이름']['ko']),
        '짧은제목': '전국 바다 축제 달력 — 축제 %d개' % 수,
        '설명': '바닷가에서 열리는 축제 %d개를 달마다 모았습니다. 축제를 누르면 '
                '일정과 가는 길, 그 시기 물때와 제철 먹거리까지 봅니다.' % 수,
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 갈래사진(d, 'festival', 사진주소(d, 대표사진(d))),
        # ★ **큰 바다 사진을 머리에 둡니다** (2026-10-02 지피티 시안 v1)
        #   전에는 막대 그림만 있었습니다. 바다 사이트인데 첫 화면에
        #   바다가 한 장도 없었습니다 (주인 규칙 6-1).
        #   공유 그림(og:image)과 **같은 권역**을 씁니다 — 카카오톡에
        #   뜨는 사진과 쪽을 열었을 때 사진이 같아야 덜 낯섭니다.
        '대표사진자리': 사진자리(
            d, 대표사진(d, 권역=쪽마다사진.get('festival', (None, None))[1]),
            쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.festival_list(언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org',
            '@type': 'CollectionPage',
            'name': '전국 바다 축제 달력',
            'url': url.full(쪽길), 'inLanguage': 'ko',
            'description': '바닷가 축제 %d개' % 수,
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '전국 바다 축제',
        '기준일조각': 기준일조각(),
        # ★ 위 띠에 붙는 이름표 (틀 _header.html 이 씁니다)
        '머리이름표': ''.join([
            이름표('축제 %d개' % 수, 'badge--orange'),
            이름표('%d권역' % len(set(x['권역'] for x in 모두))),
            이름표('일정 확인 필수', 'badge--green'),
        ]),
        # ★ 사진 안 칩 — **위 띠와 다른 것**을 보입니다 (2026-10-02)
        #   처음에는 같은 변수를 썼다가 「10월·25개 / 축제 197개 /
        #   57권역」이 띠와 사진에 **두 번** 나왔습니다.
        # ★ 달 이름을 **안 적습니다** — 자바스크립트가 채웁니다
        '머리칩': ''.join([
            '<span class="hero-chip hero-chip--on" id="festNowChip">'
            '달마다 골라 보기</span>',
            '<span class="hero-chip">%s가 %d개로 가장 많아요</span>'
            % (esc(많은묶음이름), 많은묶음수),
        ]),
        # ★ 누르면 **권역 사진 목록**으로 갑니다 (2026-09-29 주인 지시)
        '돌아갈주소': (뿌리 or './') + '#bada-cards',
        '돌아갈글': '전국 바다',
        '권역이름': '전국',
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '한줄': '전국 바다 축제 %d개' % 수,
        '큰제목': '이번 달, 바다에서 뭐가 열릴까요?',
        '큰제목뒷줄': '',
        '소개글': '달과 지역을 먼저 고르고, 마음에 드는 축제를 눌러 일정과 '
                  '가는 길, 그 시기 물때까지 이어서 보세요.',
        '묶음단추': ''.join(묶음단추),
        '달단추': ''.join(달단추),
        # ★ 달을 **안 적습니다** — 자바스크립트가 채웁니다
        '고른달제목': '한 해 축제 %d개' % 수,
        '셈안내': '사진이 있는 축제를 먼저 보여 주고, 아래에서 모두 볼 수 '
                  '있습니다.',
        '사진카드': ''.join(카드들),
        '달별목록': ''.join(덩이들),
        '기준일안내': '일정과 프로그램은 해마다 바뀝니다. 가시기 전에 주최 측 '
                      '공지를 꼭 확인해 주세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': ('<script src="%s" defer></script>'
                       % url.asset('assets/js/festival-list.js', 쪽길,
                                   판번호(os.path.join(ASSETS, 'js',
                                                       'festival-list.js')))),
    }
    return 쪽길, template.그리기('festival-list.html', 값)


def _축제사진카드(d, 축제, 쪽길, 달, 권역묶음, 권역이름, 언어):
    """축제 하나를 **큰 사진 카드**로.

    ★ 축제 자료에는 사진이 없습니다. 그 축제가 열리는 **권역의
      대표 사진**을 씁니다 (지피티가 정한 차례).
    ★ 촬영자를 반드시 적습니다 — 남의 사진입니다 (주인 규칙 5·6).
      CC BY 사진은 저작자 표시가 **지켜야 할 조건**입니다.
    """
    한장 = d.히어로(축제['권역'])
    제목 = (한장.get('제목') or '').strip()
    찍은이 = (한장.get('촬영자') or '').strip()
    설명 = ('사진 · %s · %s' % (제목, 찍은이)) if 찍은이 else ('사진 · %s' % 제목)
    넓, 높 = 한장.get('가로'), 한장.get('세로')
    크기글 = (' width="%d" height="%d"' % (넓, 높)) if (넓 and 높) else ''
    한줄 = (축제.get('한줄') or '').strip()
    return ('<a class="f-card fest-pick" href="%s" data-month="%d" '
            'data-group="%s">'
            '<figure class="photo f-card__photo">'
            '<img src="%s" alt="%s"%s loading="lazy" decoding="async">'
            '<figcaption>%s</figcaption></figure>'
            '<div class="f-card__body">'
            '<span class="f-card__meta">%s · %d월</span>'
            '<h3>%s</h3>%s</div></a>'
            % (esc(url.rel(쪽길, url.festival(축제['id'], 언어))), 달,
               esc(권역묶음.get(축제['권역']) or ''),
               esc(url.rel(쪽길, 한장['파일'])), esc(제목), 크기글,
               esc(설명),
               esc(권역이름.get(축제['권역']) or 축제['권역']), 달,
               esc(축제['이름'].get(언어) or 축제['이름']['ko']),
               ('<p>%s</p>' % esc(한줄)) if 한줄 else ''))


def _펼칠것정해서(덩이):
    """★ **모두 접어 둡니다** (2026-09-29 주인 지시)

    「어떤곳은 펼처저있고 어떤곳은 접혀있어 일관성있게 모두 접어줘」

    ★ 처음에는 「가장 많은 묶음 하나만」 펼쳐 두었습니다.
      손님이 「어디가 제일 많나」를 먼저 볼 것이라 여겼습니다.

      그런데 화면에서 보면 **어떤 줄은 펼쳐지고 어떤 줄은 접혀**
      까닭을 알 수 없습니다. 「왜 전남만 펼쳐져 있지?」 하고
      손님이 묻게 됩니다. **규칙이 안 보이면 어지럽습니다.**

      그리고 전남은 14권역이라 펼치면 그것만으로 쪽이 길어집니다.
      주인이 줄곧 말씀하신 「스크롤이 길면 지루하다」와 어긋납니다.

    ★ 접어도 자료는 쪽 안에 그대로 있습니다 —
      <details> 안 글은 검색 로봇도 읽습니다.
      요약 줄에 권역 수와 포인트 수가 있어 펼치지 않아도
      규모를 압니다.
    """
    if not 덩이:
        return ''
    return ''.join(틀 % '' for _묶음, _합, 틀 in 덩이)

def 어종쪽(d, 안내, 언어='ko'):
    """어종 안내 쪽 하나 — 어디서·언제·채비·순서·금어기까지"""
    이름 = 안내['이름'].get(언어) or 안내['이름']['ko']
    갈래 = 안내['갈래']
    쪽길 = url.guide(안내['id'], 갈래, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')

    def 글꾸(v):
        if not isinstance(v, dict):
            return v or None
        return v.get(언어) or v.get('ko') or None

    목록이름 = '낚시 어종' if 갈래 == '낚시' else '해루질 대상'
    길찾기 = ''.join([
        '<a href="%s">%s</a>' % (esc(url.rel(쪽길, url.home(언어))),
                                 esc(d.사이트['이름']['ko'])),
        '<span>›</span>',
        '<a href="%s">%s</a>' % (esc(url.rel(쪽길, url.guide_list(갈래, 언어))),
                                 esc(목록이름)),
    ])

    딴이름 = ''
    if 안내.get('딴이름'):
        딴이름 = ('<p class="alias">다른 이름: %s</p>'
                  % esc(' · '.join(안내['딴이름'])))

    # ── 한눈에
    철글 = ''
    if 안내.get('철'):
        달들 = sorted(안내['철'])
        if len(달들) >= 12:
            철글 = '연중'
        elif len(달들) >= 3 and 달들 == list(range(달들[0], 달들[-1] + 1)):
            # 이어진 달은 「4~11월」처럼 묶습니다. 열두 개를 늘어놓으면
            # 한눈에 안 들어옵니다 (2026-09-26)
            철글 = '%d~%d월' % (달들[0], 달들[-1])
        else:
            철글 = ' · '.join('%d월' % m for m in 달들)
    칸들 = [('주로 잡는 때', 철글),
            ('어려움', 안내.get('어려움')),
            ('무리', 안내.get('무리'))]
    if 안내.get('깊이cm'):
        칸들.append(('파는 깊이', '%dcm 안팎' % 안내['깊이cm']))
    # ★ **아래 「전국에서 잡히는 곳」과 같은 수**여야 합니다 (계약-01)
    #   2026-10-02 바깥 감사가 잡았습니다 — 같은 쪽 안에서
    #   볼락 36↔39 · 우럭 45↔48 · 감성돔 51↔52 · 바지락 36↔38.
    #   위는 **손으로 적은 목록만** 세고, 아래는 거기에 **권역별
    #   설명이 있는 곳을 더해** 세고 있었습니다. 계산 경로가 둘이면
    #   언젠가 반드시 어긋납니다. 이제 한 함수가 셉니다.
    _나오는곳 = 나오는권역들(d, 안내, 언어)
    if _나오는곳:
        칸들.append(('나오는 권역', '%d곳' % len(_나오는곳)))
    한눈에 = ''.join(
        '<div class="fact"><span class="f-k">%s</span>'
        '<span class="f-v">%s</span></div>' % (esc(k), esc(v))
        for k, v in 칸들 if v)

    # ── 어디서·언제
    줄들 = []
    for 머리, 값 in (('어디서', 글꾸(안내.get('어디서'))),
                     ('언제', 글꾸(안내.get('언제'))),
                     ('찾는 흔적', 글꾸(안내.get('흔적')))):
        if 값:
            # ★ 자료의 `**…**` 를 굵게 냅니다 (2026-09-30 · 화면에서 잡음)
            #   참돔 채비 글에 **별표가 그대로 보였습니다** —
            #   「갯바위·방파제에서는 **찌낚시**나 …」
            #   채비·부품 쪽은 _굵게() 를 쓰는데 어종 쪽 이 칸들만
            #   esc() 라 그랬습니다. 4쪽 8곳이 그랬습니다.
            줄들.append('<h3 class="sub-head">%s</h3><p class="long">%s</p>'
                        % (esc(머리), _굵게(값)))
    어디서언제 = ''.join(줄들) or '<p class="notice">안내를 준비하고 있습니다.</p>'

    # ── 삽화 — **눈으로 보이는 것** (주인 규칙 6-1)
    #
    #   ★ 2026-09-29 — 옛 쪽과 견주다 **삽화 245개가 사라진 것**을
    #     찾았습니다. 해루질 17쪽 · 낚시 18쪽이 7개씩 잃었습니다.
    #     자료(`그림`·`깊이cm`·`흔적`)는 멀쩡했고, 엔진이 그리지
    #     않았을 뿐이었습니다.
    #
    #   바지락 쪽에서 「숨구멍 두 개가 나란히」를 글로만 읽는 것과
    #   그려서 보여 주는 것은 다릅니다. 깊이 그림은 `깊이cm` 에
    #   **비례해 자리가 바뀝니다** — 칠게 5cm 는 얕게, 낙지 40cm 는
    #   깊게 그립니다.
    #
    #   그림 속 글씨가 한글이라 지금은 한국어 쪽에만 넣습니다.
    #   중국어판은 글씨를 옮긴 뒤에 넣습니다(2차 과제).
    어디그림, 채비그림, 배우는차례 = '', '', ''
    if 언어 == 'ko':
        if 갈래 == '해루질':
            어디그림 = art.흔적그림(안내) + art.단면그림(안내)
        else:
            어디그림 = art.자리그림(안내)
            # ★ **채비도를 함께 넣습니다** (2026-09-30 주인 지시)
            #   「반유동 찌낚시 채비 홈페이지에 적용」
            #
            #   채비도()는 **부품마다 이름과 호수**를 적은 설명 그림입니다.
            #   낚시점 채비도(머털낚시)의 구조를 따라 낚싯대·릴부터 적습니다.
            #   값은 모두 data/raw/rigs.json 에서 읽습니다 (규칙 29).
            #
            #   ★ 간단 그림(art.채비그림)은 **뺐습니다** (2026-09-30 주인 지시)
            #     「이건 필요 없잖아 이제」 — 자세한 채비도가 바로 아래
            #     있는데 찌·봉돌·바늘만 있는 그림을 또 그리고 있었습니다.
            채비그림 = art.채비도(안내, d.채비자료)
            # ★ **채비법 쪽으로 가는 길** (2026-09-30 주인 지시)
            #   「그 자료를 홈에서도 활용하게」 — 어종 쪽에서도 잇습니다.
            #   같은 자료를 두 곳에서 보여 주되, 자세한 것은 한 곳에만
            #   둡니다. 갈래가 자료에 없으면 길도 안 놓습니다.
            _갈 = 안내.get('그림')
            _것 = ((d.채비자료 or {}).get('채비') or {}).get(_갈)
            if _것:
                채비그림 += (
                    '<p class="rig-go"><a class="rig-go-btn" href="%s">'
                    '%s 자세히 보기 &rsaquo;</a></p>'
                    % (esc(url.rel(쪽길, url.rig(_갈, 언어))),
                       esc(_것.get('이름') or '채비')))
        어디그림 += art.물때그림(갈래)
        # 그림 넉 장으로 가르치는 배우는 차례 (35갈래에만 있습니다)
        배우는차례 = art.배우는차례(안내, d.배우는차례)

    # ── 이 어종이 나오는 권역 — **자료에서 셉니다** (계약-06)
    권역칸 = ''
    # ★ **자료에서 셉니다** — 손으로 적은 목록을 안 믿습니다 (2026-09-28)
    #
    #   같은 사실이 세 곳에 있었고 서로 어긋났습니다.
    #       ① 어종 자료의 「나오는권역」 목록   ← 손으로 적은 것
    #       ② 포인트의 「대상」 (3,603곳)
    #       ③ 권역별 어종 설명 (534개)
    #
    #   서천은 ③에 백합이 있는데 ①에 없어 쪽에서 통째로 빠졌습니다.
    #   바깥 검수 8차가 「콘텐츠 유실인지 가리라」 해서 찾았습니다.
    #
    #   ①을 바탕에 두되 ③을 **더합니다.** 주인 규칙 29 —
    #   숫자도 목록도 자료에서 셉니다.
    권역들 = 나오는권역들(d, 안내, 언어)
    if 권역들:
        # ★ **묶음(도)으로 묶어** 냅니다 (2026-09-28 주인 지적)
        #
        #   전에는 권역을 평평하게 줄줄이 늘어놓았습니다.
        #   감성돔은 **권역 51곳**에 걸칩니다 — 51개가 한 줄로
        #   이어지면 전국 그림이 안 보이고 고르기도 어렵습니다.
        #
        #   옛 쪽은 「전국에서 나오는 곳 — 전남 14곳 · 충남 6곳」처럼
        #   도별로 묶어 두었습니다. 그 편이 한눈에 들어옵니다.
        #   숫자는 **자료에서 셉니다** (계약-06 · 주인 규칙 29).
        아는권역 = dict((r['id'], r) for r in d.권역들)
        묶음별 = {}
        전체포인트, 전체권역 = 0, 0
        for 권역 in 권역들:
            r = 아는권역.get(권역)
            if not r:
                continue
            n = d.셈(권역, 갈래)
            # ★ 포인트가 0이어도 **그곳 사정이 적혀 있으면** 냅니다
            #   (체험장만 있고 포인트를 아직 안 정리한 권역이 있습니다)
            if not n and not 권역별어종(d, 권역, 안내, 언어).get('설명'):
                continue
            전체포인트 += n
            전체권역 += 1
            묶음별.setdefault(r['묶음'], []).append((r, n))

        덩이 = []
        for 묶음 in d.색인['묶음차례']:
            것들 = 묶음별.get(묶음)
            if not 것들:
                continue
            # ★ `이름` 은 **어종 이름**입니다 — 덮어쓰면 안 됩니다 (2026-09-28)
            #   여기서 묶음 이름을 `이름` 에 넣었다가, 쪽 제목이
            #   어종마다 다르지 않고 **마지막 묶음 이름(강원)** 으로
            #   바뀌었습니다. 어종 13쪽의 제목이 전부 같아졌습니다.
            #   (check_seo 가 「제목이 겹침 8쪽」으로 잡았습니다)
            묶음이름 = (d.색인['묶음이름'][묶음].get(언어)
                        or d.색인['묶음이름'][묶음]['ko'])
            합 = sum(n for _r, n in 것들)
            # ★ **권역마다 그곳 사정을 적습니다** (2026-09-28 바깥 검수 8차)
            #
            #   전에는 이름과 숫자만 냈습니다. 그런데 자료에는
            #   권역×어종 설명이 **534개 · 23,062자** 들어 있고,
            #   그 안에 **법·안전 이야기**가 있습니다.
            #
            #       「마을어장이라 체험 프로그램 밖 채취는 하면 안 됩니다」
            #       「마을 체험장을 통해서만 캘 수 있습니다」
            #
            #   옛 쪽에는 이것이 다 나왔습니다. 새 쪽에서 빠진 것을
            #   바깥 검수가 「축약인가 유실인가 가리라」 해서 재 보니
            #   **유실**이었습니다. 자료는 그대로 있었습니다.
            #
            #   갯벌마다 지켜야 할 것이 다릅니다. 「바지락 34곳」만
            #   보고 가면 체험장 밖에서 캐다 탈이 납니다.
            # ★ **자리를 너무 많이 먹었습니다** (2026-09-29 주인 지적)
            #
            #   「하부 상세가 너무 많아 좀 줄이자 … 공간효율이 작아
            #     모바일에서도 창 길이가 너무 길고」
            #
            #   재 보니 소라 쪽 이 칸 하나가 **2,369px** 였습니다.
            #     묶음 머리 7개  322px
            #     권역 줄 37개  1,739px   ← 거의 전부
            #     설명 7개       308px
            #
            #   그런데 **설명이 붙은 것은 전체의 37%** 뿐인데,
            #   나머지 63%도 한 줄씩 자리를 다 먹고 있었습니다.
            #
            #   ★ 그래서 **둘로 가릅니다.**
            #     · 설명 없는 권역 → **칩 격자**로 촘촘히 (한 줄에 서넛)
            #     · 설명 있는 권역 → 그대로 펼칩니다
            #
            #   ★ 설명을 숨기지 않습니다. 그 안에 **법·안전 이야기**가
            #     있습니다 — 「마을어장이라 체험 프로그램 밖 채취는
            #     하면 안 됩니다」. 「바지락 34곳」만 보고 가면 탈이 납니다.
            칩들, 줄들 = [], []
            for r, n in 것들:
                r이름 = r['이름'].get(언어) or r['이름']['ko']
                그곳 = 권역별어종(d, r['id'], 안내, 언어)
                주소 = esc(url.rel(쪽길,
                                   url.point_list(r['id'], 갈래, 언어)))
                철 = (' · %s' % esc(그곳['철'])) if 그곳.get('철') else ''
                if 그곳.get('설명'):
                    줄들.append(
                        '<li class="area-row">'
                        '<a class="area-go" href="%s">%s</a>'
                        '<span class="area-n2">%s포인트 %d곳%s</span>'
                        '<p class="area-say">%s</p></li>'
                        % (주소, esc(r이름), esc(갈래), n, 철,
                           esc(그곳['설명'])))
                else:
                    칩들.append(
                        '<li class="area-chip">'
                        '<a href="%s"><b>%s</b><i>%d곳</i></a></li>'
                        % (주소, esc(r이름), n))
            속 = ''
            if 칩들:
                속 += '<ul class="area-chips">%s</ul>' % ''.join(칩들)
            if 줄들:
                속 += '<ul class="area-list">%s</ul>' % ''.join(줄들)
            # ★ **묶음별로 접습니다** (2026-09-29 주인 지적)
            #
            #   칩 격자로 43% 줄였지만 휴대폰에서 아직 1,863px 였습니다.
            #   그래서 묶음을 접고, **포인트가 가장 많은 묶음 하나만**
            #   펼쳐 둡니다. 손님은 대개 「어디가 제일 많나」를 먼저 봅니다.
            #
            #   ★ 접어도 **자료는 쪽 안에 그대로** 있습니다.
            #     <details> 안 글은 검색 로봇도 읽습니다.
            #     요약 줄에 **권역 수와 포인트 수**를 적어,
            #     펼치지 않아도 규모를 알 수 있게 합니다.
            덩이.append(
                (묶음, 합,
                 # ★ **접힌 줄이 단추로 보이게** 합니다 (2026-09-29 주인 지시)
                 #   「권역별로 표시를 하고 더보기 버튼으로 더 보고 싶은
                 #     사람은 볼 수 있게 하자」
                 #   전에는 작은 ▶ 삼각형뿐이라 **누를 수 있는 줄 몰랐습니다.**
                 #   접어서 쪽을 줄여 놓고 아무도 못 펴면 자료를 숨긴 것과
                 #   같습니다.
                 '<details class="area-group"%%s>'
                 '<summary class="area-name">%s '
                 '<span class="area-n">%d권역 · 포인트 %d곳</span>'
                 '<span class="area-more">권역 보기<i>▾</i></span>'
                 '</summary>%s</details>'
                 % (esc(묶음이름), len(것들), 합, 속)))

        if 덩이:
            권역칸 = ('<h3 class="sub-head">전국에서 %s 곳</h3>'
                      '<p class="lead">권역 <b>%d곳</b>·포인트 <b>%d곳</b>에 '
                      '이 %s이 있습니다. 권역을 누르면 그곳 포인트 목록으로 '
                      '갑니다.</p>'
                      '<div class="area-groups">%s</div>'
                      % ('잡히는' if 갈래 == '낚시' else '나오는',
                         전체권역, 전체포인트,
                         esc('어종' if 갈래 == '낚시' else '대상'),
                         _펼칠것정해서(덩이)))

    # ── 채비·미끼
    채비줄 = []
    for 머리, 값 in (('채비', 글꾸(안내.get('채비'))),
                     ('미끼', 글꾸(안내.get('미끼')))):
        if 값:
            채비줄.append('<h3 class="sub-head">%s</h3><p class="long">%s</p>'
                          % (esc(머리), _굵게(값)))
    채비미끼 = ''.join(채비줄)

    # ── 차례대로
    차례 = ''
    걸음 = [글꾸(x) for x in (안내.get('이렇게') or [])]
    걸음 = [x for x in 걸음 if x]
    if 걸음:
        # ★ **여기도 `**…**` 를 굵게 냅니다** (2026-09-30)
        #   채비·부품 쪽은 `_굵게()` 를 쓰는데 어종 쪽만 `esc()` 라
        #   자료에 굵게 적어도 **별표가 그대로 보였습니다.**
        #   잡는 법은 핵심 한마디가 눈에 들어와야 합니다.
        #   (`_굵게` 가 이스케이프까지 하므로 esc 를 따로 쓰지 않습니다)
        차례 = ('<ol class="steps-big">%s</ol>'
                % ''.join('<li><span class="step-no">%d</span>'
                          '<span class="step-text">%s</span></li>'
                          % (i, _굵게(x)) for i, x in enumerate(걸음, 1)))

    귀띔글 = 글꾸(안내.get('귀띔'))
    # ★ 어종 쪽의 **긴 글 칸은 모두** 굵게를 처리합니다 (2026-09-30)
    #   칸마다 약속이 다르면 자료를 쓰는 사람이 외울 수 없습니다.
    #   check_design [5-4] 가 별표째 나오는 것을 잡습니다.
    귀띔 = ('<div class="note-box"><h3>귀띔</h3><p>%s</p></div>' % _굵게(귀띔글)
            if 귀띔글 else '')

    # ── 금어기·크기 — 지켜야 할 것이라 눈에 띄게
    금어기줄 = []
    if 안내.get('금어기'):
        금어기줄.append('<li><b>금어기</b> %s</li>' % esc(안내['금어기']))
    if 안내.get('크기제한'):
        금어기줄.append('<li><b>잡으면 안 되는 크기</b> %s</li>'
                        % esc(안내['크기제한']))
    if 금어기줄:
        금어기칸 = ('<div class="warn-box"><h3>이것만은 지켜 주세요</h3>'
                    '<ul>%s</ul>'
                    '<p>어기면 수산자원관리법에 따라 처벌받을 수 있습니다. '
                    '해마다 고시가 바뀌니 출발 전에 다시 확인해 주세요.</p>'
                    '</div>' % ''.join(금어기줄))
    else:
        금어기칸 = ('<p class="notice">이 %s에는 따로 정해진 금어기나 크기 '
                    '제한이 없습니다. 다만 어촌계가 정한 마을어장 규정은 '
                    '따로 있으니 현장 표지를 꼭 보세요.</p>'
                    % esc('어종' if 갈래 == '낚시' else '대상'))

    # ★ 「손질·먹는 법」은 **안 냅니다** (2026-10-01 주인 지시)
    #   「그냥 손질과 먹는법은 지워버려」 「이런정보 필요없어」
    #   자료는 그대로 두되 쪽에 내지 않습니다.
    # ── 같은 시기에 함께 나오는 것 — **자료에서 셉니다** (규칙 29)
    #
    #   ★ 2026-09-29 — 옛 쪽에 있던 칸을 되살립니다.
    #     「바지락 캐러 간 김에 뭘 더 볼 수 있나」를 알려 줍니다.
    #
    #   철만 겹쳐서는 안 됩니다. 전복은 바지락과 철이 같아도
    #   **바위에 살아 갈 곳이 다릅니다.** 그래서 철과
    #   **나오는 권역**이 함께 겹치는 것만 고릅니다.
    #   손으로 적지 않고 자료에서 셉니다.
    함께칸 = ''
    if 언어 == 'ko':
        내철 = set(안내.get('철') or [])
        내권 = set(안내.get('나오는권역') or [])
        나란히 = []
        for 딴것 in d.안내(갈래):
            if 딴것['id'] == 안내['id']:
                continue
            철겹 = 내철 & set(딴것.get('철') or [])
            권겹 = 내권 & set(딴것.get('나오는권역') or [])
            if 철겹 and 권겹:
                나란히.append((len(권겹), len(철겹), 딴것))
        나란히.sort(key=lambda x: (-x[0], -x[1], x[2]['id']))
        줄 = []
        for _권, _철, 딴것 in 나란히[:6]:
            # ★ **`딴이름` 이라 이름 짓지 않습니다** (2026-09-30 · 화면에서 잡음)
            #   저 위(3137줄)에서 만든 `딴이름`(= 이 어종의 다른 이름을
            #   담은 <p class="alias">)을 **여기서 덮어썼습니다.**
            #   그래서 쪽 제목 바로 밑에, 틀의 {{{딴이름}}} 자리에
            #   **마지막으로 돌던 딴 어종의 이름**이 태그도 없이
            #   맨 글자로 떠 있었습니다 —
            #   볼락 쪽에 「학꽁치」, 감성돔 쪽에 「볼락」, 돌돔 쪽에 「붕장어」.
            #   **34쪽 전부**가 그랬고 그대로 배포되어 있었습니다.
            딴것이름 = 딴것['이름'].get(언어) or 딴것['이름']['ko']
            줄.append('<a class="side-item" href="%s"><b>%s</b>'
                      '<span>%s</span></a>'
                      % (esc(url.rel(쪽길, url.guide(딴것['id'], 갈래, 언어))),
                         esc(딴것이름), esc(딴것.get('무리') or 갈래)))
        if 줄:
            함께칸 = ('<h3 class="sub-head">같은 시기에 함께 나오는 것</h3>'
                      '<div class="side-grid">%s</div>' % ''.join(줄))


    한줄글 = 글꾸(안내.get('한줄')) or '%s 안내입니다.' % 이름
    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s %s — 시기·자리·%s | %s'
                % (이름, 갈래, '채비' if 갈래 == '낚시' else '잡는 법',
                   d.사이트['이름']['ko']),
        '짧은제목': '%s %s — 시기·자리·잡는 법' % (이름, 갈래),
        '설명': 한줄글[:110],
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 공유그림(d, '어종' if 갈래 == '낚시' else '해루질', 안내['id'],
                              사진주소(d, d.어종사진(안내['id'])
                                        or 대표사진(d))),
        '대표사진자리': 사진자리(
            d, d.어종사진(안내['id']) or 대표사진(d), 쪽길),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.guide(안내['id'], 갈래, 언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org', '@type': 'Article',
            'headline': '%s %s' % (이름, 갈래),
            'description': 한줄글[:200],
            'url': url.full(쪽길), 'inLanguage': 'ko',
            'author': {'@type': 'Organization', 'name': d.사이트['이름']['ko']},
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '%s 안내' % 목록이름,
        '기준일조각': 기준일조각(),
        '머리이름표': ''.join([
            이름표(갈래, 'badge--orange'),
            이름표(안내.get('어려움') or '') if 안내.get('어려움') else '',
            이름표('금어기 확인', 'badge--green'),
        ]),
        '돌아갈주소': url.rel(쪽길, url.guide_list(갈래, 언어)),
        '돌아갈글': '%s 전체' % 목록이름,
        '권역이름': 목록이름,
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '어종': 안내['id'],
        '이름': 이름,
        '큰제목': '%s %s' % (이름, 갈래),
        '무리와난이도': '%s%s' % (안내.get('무리') or 갈래,
                                  ' · 난이도 %s' % 안내['어려움']
                                  if 안내.get('어려움') else ''),
        '한줄': 한줄글,
        '길찾기': 길찾기,
        '딴이름': 딴이름,
        '한눈에': 한눈에,
        '어디서언제': 어디서언제,
        '어디그림': 어디그림,
        '채비그림': 채비그림,
        '배우는차례': 배우는차례,
        '권역칸': 권역칸,
        '채비미끼': 채비미끼,
        '차례': 차례,
        '귀띔': 귀띔,
        '금어기칸': 금어기칸,
        '함께칸': 함께칸,
        '광고칸': 광고칸('어종'),
        '기준일안내': '금어기와 크기 제한은 해마다 고시가 바뀝니다. '
                      '출발 전에 해양수산부 고시를 다시 확인해 주세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': 광고움직임(쪽길, '어종'),
    }
    return 쪽길, template.그리기('guide.html', 값)


def 철묶기(달들):
    """이어진 달은 「4~11월」처럼 묶습니다"""
    달들 = sorted(달들 or [])
    if not 달들:
        return ''
    if len(달들) >= 12:
        return '연중'
    if len(달들) >= 3 and 달들 == list(range(달들[0], 달들[-1] + 1)):
        return '%d~%d월' % (달들[0], 달들[-1])
    return ' · '.join('%d월' % m for m in 달들)


def 어종목록(d, 갈래, 언어='ko'):
    """낚시 어종 / 해루질 대상 목록"""
    것들 = d.안내(갈래)
    수 = len(것들)
    쪽길 = url.guide_list(갈래, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    목록이름 = '낚시 어종' if 갈래 == '낚시' else '해루질 대상'

    # ★ 카드마다 **작은 그림**을 넣습니다 (2026-09-28 주인 규칙 6-1)
    #
    #   맨 위 큰 덮개 그림을 뺐더니 check_photos 가 바로 잡았습니다.
    #       ✗ 2쪽에 그림이 하나도 없습니다 (catch/ · fish/)
    #   **큰 그림을 빼는 것과 아무것도 안 보이는 것은 다릅니다.**
    #   옛 쪽도 카드마다 작은 그림이 있었습니다.
    #
    #   자료에 `그림` 칸이 있습니다(shell · float · egi …).
    #   그 이름의 svg 를 engine/make_icons.py 가 그려 둡니다.
    카드 = ''.join(
        '<a class="card card--go" href="%s">'
        '<div class="card-head">%s<h3 class="card-name">%s</h3>%s</div>'
        '<p class="card-body">%s</p>%s</a>'
        % (esc(url.rel(쪽길, url.guide(x['id'], 갈래, 언어))),
           대상아이콘(x.get('그림'), 쪽길),
           esc(x['이름'].get(언어) or x['이름']['ko']),
           이름표(x['어려움'], 'badge--orange') if x.get('어려움') else '',
           esc((x['한줄'] or {}).get(언어) or (x['한줄'] or {}).get('ko') or ''),
           '<p class="card-note">%s</p>' % esc(철묶기(x['철']))
           if x.get('철') else '')
        for x in 것들)

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s %d가지 — 시기·자리·잡는 법 | %s'
                % (목록이름, 수, d.사이트['이름']['ko']),
        '짧은제목': '%s %d가지' % (목록이름, 수),
        '설명': '%s %d가지를 시기와 자리, 잡는 법까지 정리했습니다.'
                % (목록이름, 수),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 갈래사진(d, 'fish' if 갈래 == '낚시' else 'catch',
                              사진주소(d, 대표사진(d))),
        # ★ 표지 삽화를 뺐습니다 (2026-09-29 주인 지시)
        #   「정보전달도 없고 칸도 너무 많이 차지해」
        #   620px 을 쓰면서 알려 주는 것이 없었습니다.
        #   제목 바로 아래 달력·목록이 오게 합니다.
        #   그린 그림 자체는 남겨 둡니다(engine/make_cover.py) —
        #   나중에 다른 자리에 쓸 수 있습니다.
        '대표사진자리': '',
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.guide_list(갈래, 언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org', '@type': 'CollectionPage',
            'name': 목록이름, 'url': url.full(쪽길), 'inLanguage': 'ko',
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '%s 안내' % 목록이름,
        '기준일조각': 기준일조각(),
        '머리이름표': ''.join([
            이름표('%d가지' % 수, 'badge--orange'),
            이름표('금어기 확인', 'badge--green'),
        ]),
        # ★ 누르면 **권역 사진 목록**으로 갑니다 (2026-09-29 주인 지시)
        #   첫 화면 맨 위로 보내면 다시 내려야 합니다.
        #   나가는 사람은 「다른 바다를 고르려고」 누릅니다.
        '돌아갈주소': (뿌리 or './') + '#bada-cards',
        '돌아갈글': '전국 바다',
        '권역이름': 목록이름,
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        # ★ 맨 위는 **글로** 엽니다 (2026-09-28 주인 지적)
        #   「해루질대상도 상단에 이미지보다는 이게 더 좋고」
        #   옛 쪽 짜임 그대로 — 작은 머리말 · 큰 제목 · 긴 설명 · 안내 띠.
        #   숫자는 자료에서 셉니다 (주인 규칙 29).
        '한줄': 목록이름,
        '큰제목': '무엇을, 언제, 어떻게 잡나' if 갈래 == '해루질'
                   else '무엇을, 언제, 어디서 낚나',
        '큰제목뒷줄': '',
        '소개글': (
            '전국 갯바위·방파제에서 노리는 어종 %d가지를 정리했습니다. '
            '어종마다 제철과 자리, 채비와 미끼, 금어기와 크기 제한을 '
            '볼 수 있고, 그 어종이 나는 권역마다 지켜야 할 것을 따로 '
            '적었습니다.' % 수
            if 갈래 == '낚시' else
            '전국 갯벌에서 잡는 대상 %d가지를 정리했습니다. 대상마다 '
            '잡는 시기와 갯벌 종류, 방법, 금어기와 크기 제한을 볼 수 '
            '있고, 그 대상이 나는 권역마다 지켜야 할 것을 따로 '
            '적었습니다. 어촌계 마을어장에서는 체험 프로그램으로만 '
            '참여할 수 있는 곳이 많습니다.' % 수),
        '안내띠': 안내띠(쪽길, 갈래),
        '묶음안내': '하나를 고르면 시기와 자리, 잡는 법, 금어기까지 봅니다.',
        '묶음칸': 카드,
        '찾기칸': '',
        '숫자칸': '',
        '기준일안내': '금어기와 크기 제한은 해마다 바뀝니다. '
                      '출발 전에 해양수산부 고시를 확인해 주세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': '',
    }
    # ★ 쪽 갈래를 겉틀로 내려보냅니다 — 그 쪽에만 듣는 규칙을 쓰려고
    값['쪽갈래'] = 'catch' if 갈래 == '해루질' else 'fish'
    return 쪽길, template.그리기('guide-list.html', 값)


# ── 채비법 쪽 ────────────────────────────────────────────────
#
#   ★ 2026-09-30 주인 지시 —
#     「낚시 채비법에 관한 별도 페이지가 있었으면 좋겠어
#       원투법 찌낙시법 등 채비에 관한 별도 페이지가 있으면 좋겠어
#       그 자료를 홈에서도 활용하게」
#
#   채비도는 이미 있었지만 **어종 쪽 안에만** 있었습니다.
#   「찌낚시가 뭔지」 알고 싶은 사람이 먼저 어종을 골라야 했습니다.
#   순서가 거꾸로였습니다.
#
#   값은 모두 `data/raw/rigs.json` 에서 읽습니다. 손으로 안 적습니다
#   (주인 규칙 29). 갈래 차례도 자료가 정합니다 (계약-11).

def 채비갈래들(d):
    """자료가 정한 차례 그대로 돌려줍니다 (계약-11 · 계약-07)"""
    return list(((d.채비자료 or {}).get('채비') or {}).items())


def _채비어종꼴(갈래, 것):
    """art.채비도()·art.채비그림()은 **어종 꼴**을 받습니다.

    그 둘은 원래 어종 쪽에서 불렀습니다. 채비 쪽에서도 같은 그림을
    쓰려고 자료를 어종 꼴로 감쌉니다 — 그림 코드를 복붙하지 않습니다
    (계약-01 의 뜻 · 한 곳에서만 만듭니다).
    """
    return {'그림': 갈래, '이름': {'ko': 것.get('이름') or 갈래}}


def 채비카드(d, 쪽길, 언어='ko'):
    """모음 쪽의 카드들"""
    칸 = []
    for 갈래, 것 in 채비갈래들(d):
        칸.append(
            '<a class="card card--go" href="%s">'
            '<div class="card-head">%s<h3 class="card-name">%s</h3></div>'
            '<p class="card-body">%s</p>'
            '<p class="card-note">%s</p></a>'
            % (esc(url.rel(쪽길, url.rig(갈래, 언어))),
               대상아이콘(갈래, 쪽길),
               esc(것.get('이름') or 갈래),
               # ★ **카드에서는 굵게 표시를 지웁니다** (2026-09-30)
               #   목록 카드는 두어 줄만 보이는 짧은 소개입니다.
               #   여기서 굵게까지 쓰면 오히려 어지럽고, 자료에 적힌
               #   `**…**` 가 그대로 보이면 더 나쁩니다. 그래서 **떼어 냅니다.**
               esc(_별표뗌(것.get('왜') or '')),
               esc('노리는 것 — %s' % (것.get('대상') or ''))))
    return ''.join(칸)


def 챙길것칸(것):
    """낚싯대·릴과 부품을 **한 표**로 보여 줍니다.

    ★ 글로 죽 늘어놓지 않습니다 (주인 규칙 6-1 — 눈으로 읽히게).
      값이 빈 부품(이름만 있는 것)은 값 칸을 비우고 귀띔만 답니다.
    """
    줄 = []
    for 묶음이름, 열쇠 in (('장비', '장비'), ('부품', '부품')):
        것들 = 것.get(열쇠) or []
        if not 것들:
            continue
        줄.append('<p class="rig-th">%s</p>' % esc(묶음이름))
        줄.append('<dl class="rig-dl">')
        for 한개 in 것들:
            값 = (한개.get('값') or '').strip()
            귀띔 = (한개.get('귀띔') or '').strip()
            줄.append('<dt>%s</dt><dd>%s%s</dd>'
                      % (esc(한개.get('이름') or ''),
                         esc(값) if 값 else '<span class="rig-none">—</span>',
                         # ★ **부품 귀띔도 굵게** (2026-09-30)
                         #   esc() 면 별표가 글자로 보입니다.
                         '<span class="rig-tip">%s</span>' % _굵게(귀띔)
                         if 귀띔 else ''))
        줄.append('</dl>')
    return ''.join(줄)


def 요령칸(것):
    """안내도의 **요령과 준비물**을 쪽에 냅니다 (2026-10-01).

    ★ 주인 지시 — 「내가 제시한 자료를 사용해」
      주인이 주신 안내도의 「초보자를 위한 TIP」과
      「추천 준비물」입니다.

    ★ 왜 글로도 두나
      휴대폰에서 안내도 글씨는 작습니다. 글로 두면 확대 없이
      읽힙니다. 준비물은 **낚시점에서 그대로 보여 주고 살 수
      있는 목록**이라 더욱 그렇습니다.

    자료가 없으면 칸도 안 만듭니다 — 빈 제목만 남기느니
    없는 편이 낫습니다 (㉕ 에서 배운 것).
    """
    요령 = [x for x in (것.get('요령') or []) if str(x).strip()]
    준비물 = [x for x in (것.get('준비물') or []) if str(x).strip()]
    if not 요령 and not 준비물:
        return ''
    덩이 = []
    if 요령:
        덩이.append(
            '<div class="rig-tip">'
            '<h3 class="rig-tip-h">이렇게 하면 더 잘 잡힙니다</h3>'
            '<ul class="rig-tip-list">%s</ul></div>'
            % ''.join('<li>%s</li>' % _굵게(str(x)) for x in 요령))
    if 준비물:
        덩이.append(
            '<div class="rig-kit">'
            '<h3 class="rig-tip-h">이것만 챙기면 됩니다</h3>'
            '<ul class="rig-kit-list">%s</ul>'
            '<p class="rig-kit-note">낚시점에서 이 목록을 '
            '그대로 보여 주셔도 됩니다.</p></div>'
            % ''.join('<li>%s</li>' % esc(str(x)) for x in 준비물))
    return ('<section class="section"><div class="wrap">'
            '<div class="section-head">'
            '<p class="kicker">나가기 전에</p>'
            '<h2 class="serif">이것만 알고 가세요</h2></div>'
            '<div class="rig-tips">%s</div></div></section>'
            % ''.join(덩이))


def 안내도(d, 갈래, 쪽길, 이름, 밭='rig'):
    """주인이 주신 안내도 그림. 없으면 빈 글.

    ★ 2026-10-01 주인 지시 — 「그림은 그대로 사용해」
      `data/img/<밭>/<갈래>.webp` 를 찾습니다.

    ★ **채비만의 것이 아닙니다** (2026-10-06)
      해루질 준비물 안내도도 똑같이 생겼고 똑같이 쓰입니다 —
      가로·세로 두 장, 눌러서 크게 보기, 만든 곳 밝히기까지.
      함수를 하나 더 만들면 **같은 일을 하는 곳이 둘**이 되어
      한쪽만 고치면 갈라집니다. `밭` 만 받아 둘 다 맡습니다.

          밭='rig'     data/img/rig/<갈래>.webp
          밭='catch'   data/img/catch/<갈래>.webp

    ★ 크기를 적어 둡니다 — 안 적으면 쪽이 **덜컹** 합니다
      그림이 늦게 오면 자리가 0 이었다가 갑자기 벌어집니다.
      width·height 를 적으면 브라우저가 미리 자리를 잡습니다.
    """
    import shutil
    원본 = os.path.join(DATA, 'img', 밭, 갈래 + '.webp')
    if not os.path.isfile(원본):
        return ''
    쪽아래 = 'img/%s/%s.webp' % (밭, 갈래)
    낼곳 = os.path.join(나갈곳, 'img', 밭)
    os.makedirs(낼곳, exist_ok=True)
    목적 = os.path.join(낼곳, 갈래 + '.webp')
    if (not os.path.isfile(목적)
            or os.path.getmtime(원본) > os.path.getmtime(목적)):
        shutil.copy2(원본, 목적)
    가로, 세로 = 1479, 1063
    try:
        from PIL import Image
        with Image.open(원본) as im:
            가로, 세로 = im.size
    except Exception:
        pass
    # ★ **눌러서 크게 보기** (2026-10-01)
    #   재 보니 휴대폰에서 안내도 글씨가 4px 쯤이라 못 읽습니다
    #   (1480px → 321px, 4.6배 축소). 누르면 화면 가득 펼쳐집니다.
    #   자바스크립트 없이 `:target` 만 씁니다 — 스크립트가 못
    #   돌아도 그림은 그대로 보입니다 (계약-23).
    자리 = 'guide-' + 갈래
    주소 = esc(url.rel(쪽길, 쪽아래))
    # ★ **휴대폰용 세로판** (2026-10-01 주인이 만들어 주심)
    #   재 보니 가로판은 휴대폰에서 4.6배 축소라 글씨가
    #   4.3px 이 되어 못 읽습니다. 세로판은 3.2배라 11px —
    #   줄여서 눈으로 견주니 부품 이름과 TIP 이 다 읽힙니다.
    #   `<picture>` 로 **브라우저가 고릅니다** — 맞는 것
    #   하나만 받으므로 쪽이 안 무거워집니다.
    세로원본 = os.path.join(DATA, 'img', 밭, 갈래 + '-m.webp')
    세로조각 = ''
    if os.path.isfile(세로원본):
        세로아래 = 'img/%s/%s-m.webp' % (밭, 갈래)
        세로목적 = os.path.join(낼곳, 갈래 + '-m.webp')
        if (not os.path.isfile(세로목적)
                or os.path.getmtime(세로원본) >
                os.path.getmtime(세로목적)):
            shutil.copy2(세로원본, 세로목적)
        세로조각 = ('<source media="(max-width:767px)" srcset="%s">'
                     % esc(url.rel(쪽길, 세로아래)))
    return ('<figure class="rig-guide">'
            '<a class="rig-guide-open" href="#%s"'
            ' aria-label="%s 안내도 크게 보기">'
            '<picture>%s'
            '<img src="%s" alt="%s 안내도" width="%d"'
            ' height="%d" loading="lazy" decoding="async">'
            '</picture>'
            '<span class="rig-guide-hint">눌러서 크게 보기</span>'
            '</a>'
            # ★ 설명을 답니다 (주인 규칙 5·6 · check_photos [3])
            #   **우리가 만든 안내도**라는 것을 밝힙니다.
            #   남의 사진이 아니므로 촬영자 대신 만든 곳을 적습니다.
            '<figcaption>그림 · %s 안내도 · 바다가자닷컴</figcaption>'
            '</figure>'
            # 크게 보는 칸 — 누르기 전에는 안 보입니다
            '<div class="rig-zoom" id="%s">'
            '<a class="rig-zoom-bg" href="#" aria-label="닫기">'
            '</a>'
            '<picture>%s'
            '<img src="%s" alt="%s 안내도" width="%d" height="%d">'
            '</picture>'
            '<a class="rig-zoom-x" href="#">닫기</a></div>'
            % (esc(자리), esc(이름), 세로조각, 주소, esc(이름),
               가로, 세로,
               esc(이름),
               esc(자리), 세로조각, 주소, esc(이름), 가로, 세로))


def 채비쪽(d, 갈래, 언어='ko'):
    """채비법 한 갈래 — rig/float.html 등"""
    것 = (((d.채비자료 or {}).get('채비') or {}).get(갈래)) or {}
    쪽길 = url.rig(갈래, 언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    이름 = 것.get('이름') or 갈래
    대상 = 것.get('대상') or ''
    미끼 = 것.get('미끼') or ''

    # ★ **간단 그림은 안 씁니다** (2026-09-30 주인 지시)
    #   「이건 필요 없잖아 이제」
    #   바로 아래에 **부품마다 이름과 호수를 적은 채비도**가 있습니다.
    #   찌·봉돌·바늘만 있는 간단 그림은 같은 것을 두 번 말하면서
    #   자리만 차지했습니다. 함수(art.채비그림)는 남겨 둡니다 —
    #   「배우는 차례」 묶음이 아직 씁니다.
    # ★ **주인이 주신 안내도가 있으면 그것을 씁니다** (2026-10-01)
    #   주인 지시 — 「그림은 그대로 사용해」
    #
    #   안내도에는 제가 SVG 로 못 담는 것이 들어 있습니다 —
    #   실제 제품 사진, 바다 배경, 어종 사진, 초보자 TIP.
    #   **제가 그린 것보다 손님에게 훨씬 잘 읽힙니다.**
    #   없는 채비는 그대로 SVG 채비도를 그립니다.
    # ★ 변수 이름을 함수와 다르게 둡니다 (2026-10-06)
    #   `채비안내도` 를 `안내도` 로 넓히면서 이 줄이
    #   `안내도 = 안내도(...)` 가 되어 **지역 변수가 함수를
    #   가렸습니다** — UnboundLocalError 로 빌드가 통째로
    #   멈췄습니다. 고친 자리에서 바로 돌려 봐 잡았습니다.
    안내도글 = 안내도(d, 갈래, 쪽길, 이름)
    if 안내도글:
        채비그림 = 안내도글
    else:
        꼴 = _채비어종꼴(갈래, 것)
        채비그림 = art.채비도(꼴, d.채비자료)
    # ★ **부력과 수심 그림** (2026-09-30 주인 지시 — 「이런 시각적인 정보도 좋아」)
    #   「얕으면 3B~5B · 깊으면 0.8~1.5호」처럼 값이 둘로 갈린 채비에만
    #   붙습니다. 왜 호수를 나누는지 글보다 그림이 빠릅니다.
    if not 안내도글:
        채비그림 += art.수심그림(갈래, d.채비자료)

    # ★ 이름표는 **무엇인지 밝혀서** 답니다 (2026-09-30)
    #   처음에 미끼 이름만 달았더니 「크릴·게·홍합·깐새우」가
    #   무엇을 뜻하는지 알 수 없었습니다. 이름표는 짧아서
    #   **앞에 무엇인지 붙여야** 읽힙니다.
    이름표줄 = ''.join(
        ([이름표('미끼 — %s' % 미끼, 'badge--green')] if 미끼 else [])
        + ([이름표('노리는 것 — %s' % 대상, 'badge--orange')] if 대상 else []))

    # ★ 「왜 이렇게 매나」는 **제목이 아니라 설명**입니다 (2026-09-30)
    #   처음에 문장을 통째로 h2 에 넣었더니 두 줄짜리 거대한 제목이
    #   됐습니다. 제목은 짧게 두고 문장은 본문 크기로 둡니다.
    왜 = (것.get('왜') or '').strip()
    왜이렇게 = ('<section class="section section--soft"><div class="wrap">'
                '<div class="section-head"><p class="kicker">채비 읽기</p>'
                '<h2 class="serif">왜 이렇게 매나</h2></div>'
                # ★ 여기도 `**…**` 를 굵게 냅니다 (2026-09-30)
                #   에기 채비 설명에 별표가 그대로 보였습니다.
                '<p class="rig-why">%s</p></div></section>' % _굵게(왜)
                ) if 왜 else ''

    # 이 채비로 노리는 어종 — **자료끼리 이어 줍니다.**
    #
    #   ① 어종 안내(guide)의 `그림` 값이 채비 갈래와 같은 것
    #   ② ①로 하나도 못 찾으면 **「대상」에 적힌 이름으로** 찾습니다
    #
    #   ★ 2026-09-30 — ①만 있을 때 **전유동 쪽에 어종 칸이 통째로
    #     안 나왔습니다.** 어종 자료의 `그림` 값은 `float`·`bottom`
    #     처럼 **채비 갈래가 아니라 그림 이름**이라, 새 갈래
    #     (`float_free`)를 가진 어종이 하나도 없었기 때문입니다.
    #     어종 자료에 손대지 않고 이름으로도 잇습니다.
    이어진것 = [x for x in d.안내('낚시') if x.get('그림') == 갈래]
    if not 이어진것 and 대상:
        _이름들 = [y.strip() for y in 대상.split('·') if y.strip()]
        이어진것 = [x for x in d.안내('낚시')
                    if (x['이름'].get('ko') or '') in _이름들]
    어종칸 = ''
    if 이어진것:
        칸 = ''.join(
            '<a class="card card--go" href="%s">'
            '<div class="card-head">%s<h3 class="card-name">%s</h3></div>'
            '<p class="card-body">%s</p></a>'
            % (esc(url.rel(쪽길, url.guide(x['id'], '낚시', 언어))),
               대상아이콘(x.get('그림'), 쪽길),
               esc(x['이름'].get(언어) or x['이름']['ko']),
               esc((x['한줄'] or {}).get(언어) or (x['한줄'] or {}).get('ko') or ''))
            for x in 이어진것)
        어종칸 = ('<section class="section section--white"><div class="wrap">'
                  '<div class="section-head"><p class="kicker">이 채비로</p>'
                  '<h2 class="serif">무엇을 낚나</h2>'
                  '<p class="lead">어종을 고르면 제철과 자리, 금어기까지 봅니다.</p>'
                  '</div><div class="grid">%s</div></div></section>' % 칸)

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '%s — 무엇을 챙기고 어떻게 매나 | %s'
                % (이름, d.사이트['이름']['ko']),
        '짧은제목': 이름,
        '설명': '%s 를 부품마다 이름과 호수까지 그림으로 풀었습니다.%s'
                % (이름, (' 노리는 것 — %s.' % 대상) if 대상 else ''),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 공유그림(d, 'rig', 갈래, 사진주소(d, 대표사진(d))),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.rig(갈래, 언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org', '@type': 'HowTo',
            'name': 이름, 'url': url.full(쪽길), 'inLanguage': 'ko',
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '낚시 채비법',
        '기준일조각': 기준일조각(),
        '머리이름표': 이름표(이름, 'badge--green'),
        '돌아갈주소': esc(url.rel(쪽길, url.rig_list(언어))),
        '돌아갈글': '채비법 모두 보기',
        '권역이름': 이름,
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '한줄': '낚시 채비법',
        '큰제목': 이름,
        '소개글': ('%s 로 노립니다. 미끼는 %s 를 씁니다.'
                   % (대상, 미끼) if 대상 and 미끼
                   else (것.get('왜') or '')),
        '이름표줄': (이름표줄 + 부품바로가기(d, 쪽길, 언어)),
        '채비그림': 채비그림,
        '챙길것': 챙길것칸(것),
        '요령칸': 요령칸(것),
        '왜이렇게': 왜이렇게,
        '어종칸': 어종칸,
        '광고칸': 광고칸('안내'),
        '기준일안내': '호수와 굵기는 자리와 물때에 따라 달라집니다. '
                      '낚시점에서 그날 상황을 한 번 더 물어보세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': '',
    }
    return 쪽길, template.그리기('rig.html', 값)


def 부품바로가기(d, 쪽길, 언어='ko'):
    """부품 쪽으로 보내는 띠 (2026-09-30 주인 지시).

    주인 말씀 — 「낚시 채비법 페이지에 부품별 명칭 및 사용법
                  바로가기 이렇게 페이지하나만들면 더 좋을거 같아」

    채비도에 나오는 이름(맨도래·좁쌀봉돌·O형 고무…)은 처음 오신 분께
    낯섭니다. **그 자리에서 바로 물어볼 곳**을 둡니다.
    자료가 없으면 띠도 안 답니다 — 빈 단추를 보이지 않습니다.
    """
    것들 = 부품사전(d)
    if not 것들:
        return ''
    return ('<p class="pt-go"><span>부품 이름이 낯서신가요? '
            '<b>%d가지</b>를 크기와 쓰는 법까지 풀어 두었습니다.</span>'
            '<a class="pt-go-btn" href="%s">부품 이름과 쓰는 법 &rsaquo;</a></p>'
            % (len(것들), esc(url.rel(쪽길, url.rig_parts(언어)))))


def 부품사전(d):
    """자료의 부품 사전 (계약-11 — 차례도 자료가 정합니다)"""
    return list(((d.채비자료 or {}).get('부품') or {}).items())


def _부품어디쓰나(d):
    """부품마다 **어느 채비에 나오는지**를 자료에서 셉니다.

    손으로 적지 않습니다. 채비를 하나 더하면 여기도 저절로 늡니다.
    """
    어디 = {}
    for 갈, 것 in 채비갈래들(d):
        for 한개 in (것.get('부품') or []):
            이름 = (한개.get('이름') or '').strip()
            if not 이름:
                continue
            # 「소형 맨도래」도 「맨도래」로 셉니다
            열쇠 = 이름
            for 사전이름 in ((d.채비자료 or {}).get('부품') or {}):
                if 사전이름 == 이름 or 사전이름 in 이름:
                    열쇠 = 사전이름
                    break
            어디.setdefault(열쇠, [])
            if 갈 not in 어디[열쇠]:
                어디[열쇠].append(갈)
    return 어디


def 부품쪽(d, 언어='ko'):
    """부품별 이름과 쓰는 법 — rig/parts.html

    ★ 2026-09-30 주인 지시 —
      「각 부품별 크기 사용용도, 종류 이렇게 별도의 한 페이지를
        만들면 어떨까?」 「부품별 사용법 및 상세설명」

    같은 부품이 여러 채비에 되풀이됩니다. 설명을 쪽마다 적으면
    **한 곳을 고치고 다른 곳을 잊습니다.** 여기 한 번만 적습니다.
    """
    것들 = 부품사전(d)
    쪽길 = url.rig_parts(언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')
    어디쓰나 = _부품어디쓰나(d)
    채비이름 = {갈: (것.get('이름') or 갈) for 갈, 것 in 채비갈래들(d)}

    # 갈래로 묶습니다 — 자료에 나온 차례를 지킵니다
    묶음 = []
    for 이름, 것 in 것들:
        갈래 = 것.get('갈래') or '그 밖'
        if not 묶음 or 묶음[-1][0] != 갈래:
            묶음.append((갈래, []))
        묶음[-1][1].append((이름, 것))

    칸들 = []
    for 갈래, 것들묶음 in 묶음:
        카드 = []
        for 이름, 것 in 것들묶음:
            그림 = art.부품그림(이름)
            크기 = ('<span class="pt-mm">%dmm 안팎</span>' % 것['크기mm']
                    if 것.get('크기mm') else '')
            종류 = ''
            if 것.get('종류'):
                종류 = ('<p class="pt-h">종류</p><ul class="pt-ul">%s</ul>'
                        % ''.join('<li>%s</li>' % esc(x) for x in 것['종류']))
            조심 = ('<p class="pt-care">%s</p>' % _굵게(것['조심'])
                    if 것.get('조심') else '')
            # ★ 2026-09-30 주인 지시 — 「찌가 어디에 걸리고 이런것들도」
            걸림 = ('<p class="pt-h">어디에 걸리나</p>'
                    '<p class="pt-pick">%s</p>' % _굵게(것['걸림'])
                    if 것.get('걸림') else '')
            나오는곳 = ''
            갈래들 = 어디쓰나.get(이름) or []
            if 갈래들:
                나오는곳 = ('<p class="pt-in">%s</p>' % ' · '.join(
                    '<a href="%s">%s</a>'
                    % (esc(url.rel(쪽길, url.rig(g, 언어))),
                       esc(채비이름.get(g, g)))
                    for g in 갈래들))
            카드.append(
                '<article class="pt" id="%s">'
                '<div class="pt-art">%s</div>'
                '<div class="pt-body">'
                '<h3 class="pt-name">%s%s</h3>'
                '<p class="pt-use">%s</p>'
                '<p class="pt-h">고르는 법</p><p class="pt-pick">%s</p>'
                '%s%s%s%s</div></article>'
                % (esc(_부품고리(이름)), 그림, esc(이름), 크기,
                   _굵게(것.get('쓰임') or ''), _굵게(것.get('고르기') or ''),
                   걸림, 종류, 조심, 나오는곳))
        칸들.append(
            '<section class="section section--white"><div class="wrap">'
            '<div class="section-head"><p class="kicker">%s</p>'
            '<h2 class="serif">%s</h2></div>'
            '<div class="pt-grid">%s</div></div></section>'
            % (esc(갈래), esc(_갈래제목(갈래)), ''.join(카드)))

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '낚시 부품 %d가지 — 이름·크기·쓰는 법 | %s'
                % (len(것들), d.사이트['이름']['ko']),
        '짧은제목': '낚시 부품 %d가지' % len(것들),
        '설명': '원줄·찌·도래·봉돌·바늘까지 %d가지를 크기와 쓰는 법, '
                '고르는 요령까지 그림으로 풀었습니다.' % len(것들),
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 갈래사진(d, 'rig', 사진주소(d, 대표사진(d))),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.rig_parts(언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org', '@type': 'DefinedTermSet',
            'name': '낚시 부품', 'url': url.full(쪽길), 'inLanguage': 'ko',
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '낚시 부품',
        '기준일조각': 기준일조각(),
        '머리이름표': 이름표('%d가지' % len(것들), 'badge--orange'),
        '돌아갈주소': esc(url.rel(쪽길, url.rig_list(언어))),
        '돌아갈글': '채비법 모두 보기',
        '권역이름': '낚시 부품',
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '한줄': '부품별 이름과 쓰는 법',
        '큰제목': '이게 무슨 부품인가요',
        '소개글': '채비도에 나오는 부품 %d가지입니다. 실제 크기와 '
                  '무엇에 쓰는지, 어떻게 고르는지를 그림과 함께 '
                  '적었습니다. 낚시점에서 이름을 몰라 못 사는 일이 '
                  '없게 합니다.' % len(것들),
        '안내띠': 안내띠(쪽길, '낚시'),
        '갈래칸': ''.join(칸들),
        '기준일안내': '호수와 굵기는 자리와 물때에 따라 달라집니다. '
                      '낚시점에서 그날 상황을 한 번 더 물어보세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': '',
    }
    # ★ 겉틀이 body 클래스로 쓰는 값 — 안 주면 틀이 멈춥니다
    값.setdefault('쪽갈래', '')
    return 쪽길, template.그리기('rig-parts.html', 값)


def _갈래제목(갈래):
    return {
        '줄': '줄 — 원줄과 목줄',
        '찌': '찌 — 입질을 보여 주는 것',
        '채비소품': '채비소품 — 이어 주고 막아 주는 것',
        '봉돌': '봉돌 — 가라앉히는 것',
        '바늘': '바늘 — 무는 자리',
        '미끼': '미끼 — 꾀는 것',
    }.get(갈래, 갈래)


def _부품고리(이름):
    """부품 이름을 쪽 안 고리(id)로 바꿉니다 — 바로가기에 씁니다"""
    return 'pt-' + re.sub(r'[^0-9A-Za-z가-힣]+', '-', 이름).strip('-')


def _별표뗌(글):
    """짧은 카드용 — 자료의 `**…**` 에서 **별표만 떼어 냅니다.**

    긴 글에는 `_굵게()` 로 굵게 내지만, 목록 카드처럼 두어 줄만
    보이는 자리에는 굵은 글씨가 오히려 어지럽습니다.
    그렇다고 그대로 두면 별표가 글자로 보입니다.
    """
    return re.sub(r'\*\*(.+?)\*\*', r'\g<1>', 글 or '')


def _굵게(글):
    """자료에 적은 `**…**` 를 굵은 글씨로 바꿉니다.

    자료를 쓰는 사람이 HTML 을 몰라도 되게 합니다.
    글은 먼저 **이스케이프**하고, 그 뒤에 별표만 태그로 바꿉니다.
    """
    s = esc(글)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)


def 채비목록(d, 언어='ko'):
    """채비법 모음 — rig/"""
    갈래들 = 채비갈래들(d)
    수 = len(갈래들)
    쪽길 = url.rig_list(언어)
    뿌리 = url.뿌리로(쪽길)
    차림표 = os.path.join(ASSETS, 'css', 'site.css')

    값 = {
        '언어코드': 'ko' if 언어 == 'ko' else 'zh-Hans',
        '제목': '낚시 채비법 %d가지 — 원투·찌낚시·카드채비 | %s'
                % (수, d.사이트['이름']['ko']),
        '짧은제목': '낚시 채비법 %d가지' % 수,
        '설명': '원투·찌낚시·카드채비 등 %d가지를 부품마다 이름과 '
                '호수까지 그림으로 풀었습니다.' % 수,
        '정식주소': url.full(쪽길),
        '사이트이름': d.사이트['이름'].get(언어) or d.사이트['이름']['ko'],
        '대표사진': 갈래사진(d, 'rig', 사진주소(d, 대표사진(d))),
        '차림표주소': url.asset('assets/css/site.css', 쪽길, 판번호(차림표)),
        '집차림표': '',
        '뿌리': 뿌리,
        '언어연결': 언어연결(d, lambda 언: url.rig_list(언)),
        '구조화자료': json.dumps({
            '@context': 'https://schema.org', '@type': 'CollectionPage',
            'name': '낚시 채비법', 'url': url.full(쪽길), 'inLanguage': 'ko',
        }, ensure_ascii=False, separators=(',', ':')),
        '머리말': '낚시 채비법',
        '기준일조각': 기준일조각(),
        '머리이름표': 이름표('%d가지' % 수, 'badge--orange'),
        '돌아갈주소': (뿌리 or './') + '#bada-cards',
        '돌아갈글': '전국 바다',
        '권역이름': '낚시 채비법',
        '메일': d.사이트['메일'],
        '로고': 로고(뿌리, d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '꼬리로고': 꼬리로고(뿌리,
                             d.사이트['이름'].get(언어) or d.사이트['이름']['ko']),
        '한줄': '낚시 채비법',
        '큰제목': '무엇을 챙기고, 어떻게 매나',
        '소개글': '갯바위와 방파제에서 쓰는 채비 %d가지입니다. '
                  '낚싯대·릴부터 원줄·찌·봉돌·바늘까지, 부품마다 '
                  '이름과 호수를 그림으로 적었습니다. 낚시점에서 '
                  '무엇을 달라고 해야 할지 그대로 보고 가시면 됩니다.' % 수,
        # ★ 부품 쪽 바로가기 (2026-09-30 주인 지시)
        #   「낚시 채비법 페이지에 부품별 명칭 및 사용법 바로가기
        #     이렇게 페이지하나만들면 더 좋을거 같아」
        '안내띠': (안내띠(쪽길, '낚시') + 부품바로가기(d, 쪽길, 언어)),
        '묶음안내': '하나를 고르면 채비도와 챙길 것, 노리는 어종까지 봅니다.',
        '묶음칸': 채비카드(d, 쪽길, 언어),
        '기준일안내': '호수와 굵기는 자리와 물때에 따라 달라집니다. '
                      '낚시점에서 그날 상황을 한 번 더 물어보세요.',
        '사이트한줄': d.사이트['한줄'].get(언어) or d.사이트['한줄']['ko'],
        '운영책임자': d.사이트['운영책임자'],
        '꼬리메뉴': 꼬리메뉴(d, 쪽길, 언어),
        '알림글': '본 자료는 참고용입니다. 금어기·포획 금지 체장은 해양수산부 고시를 따릅니다.',
        '쪽스크립트': '',
    }
    return 쪽길, template.그리기('rig-list.html', 값)


def 안내띠(쪽길, 갈래):
    """처음 오신 분을 기초 쪽으로 보내는 띠 (2026-09-28 주인 지적).

    ★ 옛 쪽에 있던 것입니다. 큰 그림 대신 **바로 쓸 수 있는 길**을
      둡니다. 해루질은 물때·옷차림·안전을 모르면 위험합니다.

    ★ 갈 곳이 없으면 띠도 안 답니다 — 빈 단추를 보이지 않습니다.
    """
    갈곳, 말, 단추 = None, '', ''
    if 갈래 == '해루질':
        갈곳 = url.guide('basics', '해루질')
        말 = '해루질이 처음이라면 물때·옷차림·안전부터 보세요.'
        단추 = '왕초보 해루질 기초 바로가기 →'
    else:
        갈곳 = url.guide('basics', '낚시')
        말 = '낚시가 처음이라면 채비·미끼·안전부터 보세요.'
        단추 = '왕초보 낚시 기초 바로가기 →'
    if not 갈곳:
        return ''
    # ★ **파일이 있는지로 정하면 안 됩니다** (2026-10-01 계약-07 어김)
    #
    #   전에는 `os.path.isfile(나갈곳/갈곳)` 으로 보았습니다. 그러면
    #   **만드는 차례에 따라 결과가 달라집니다** — 기초 쪽보다 먼저
    #   만들어진 쪽에는 띠가 안 붙고, 나중 쪽에는 붙습니다.
    #   같은 자료로 두 번 지어도 결과가 달라져 계약-07 을 어겼습니다
    #   (about.html · catch/index.html · fish/basics.html).
    #
    #   이제 기초 쪽은 **저희가 만듭니다.** 그러니 파일을 찾아볼
    #   까닭이 없습니다. **자료가 있으면 만들어질 쪽**입니다.
    if not hubs_basics._기초자료(None, 갈래):
        return ''          # 자료가 없으면 그 쪽을 안 만듭니다
    return ('<p class="ls-basic"><span>%s</span>'
            '<a class="ls-basic-btn" href="%s">%s</a></p>'
            % (esc(말), esc(url.rel(쪽길, 갈곳)), esc(단추)))


def 쪽주소(갈, 권역, 갈래, 언어='ko'):
    """무엇을 만들든 주소는 url.py 한 곳에서 나옵니다 (계약-03)"""
    if 갈 == '첫쪽':
        return url.home(언어)
    if 갈 == '묶음':
        return url.group(권역, 언어)
    if 갈 == '권역':
        return url.region(권역, 언어)
    if 갈 == '축제':
        return url.festival(권역, 언어)
    if 갈 == '축제달력':
        return url.festival_list(언어)
    if 갈 == '어종':
        return url.guide(권역, 갈래, 언어)
    if 갈 == '어종목록':
        return url.guide_list(갈래, 언어)
    if 갈 == '채비':
        return url.rig(권역, 언어)
    if 갈 == '채비목록':
        return url.rig_list(언어)
    if 갈 == '채비부품':
        return url.rig_parts(언어)
    if 갈 == '금어기':
        return url.rule(언어)
    if 갈 == '물때허브':
        return url.tide_list(언어)
    if 갈 == '안내허브':
        return url.guide_hub(언어)
    if 갈 == '장비':
        return url.gear(언어)
    # ★ 사이트를 밝히는 네 쪽 (2026-10-01)
    #   438쪽 모두가 꼬리에서 겁니다. 자세한 까닭은 engine/hubs_site.py
    if 갈 == '기초':
        return url.basics(권역, 언어)
    if 갈 == '준비물':
        return 'catch/gear.html'
    if 갈 == '물때보는법':
        return url.muldae(언어)
    if 갈 == '가진자료':
        return url.data(언어)
    if 갈 == '여행':
        return url.travel(언어)
    if 갈 == '소개':
        return url.about(언어)
    if 갈 == '출처':
        return url.sources(언어)
    if 갈 == '개인정보':
        return url.privacy(언어)
    if 갈 == '사진출처':
        return url.photos(언어)
    if 갈 == '방문기록':
        return url.stats(언어)
    return url.point_list(권역, 갈래, 언어)


def _자기링크없애기(글, 쪽길):
    """**지금 보는 쪽을 가리키는 링크**를 눌리지 않게 합니다.

    ★ 2026-10-01 — 아래 차림표를 달면서 드러났습니다.
      catch/index.html 에서 차림표의 「해루질」이 자기
      자신을 가리켰습니다. 누르면 같은 쪽이 다시 떠
      손님이 「눌렀는데 안 바뀐다」고 느낍니다.

      차림표만의 일이 아닙니다 — index.html 의 로고가
      ./index.html 을 가리키는 것도 전부터 있었습니다.
      **쪽을 쓰기 직전에 한 번 훑어 모두** 없앱니다.

    ★ 링크를 지우지 않고 **href 만 뗍니다.**
      글자와 모양은 그대로 두어야 차림표 칸이 안 무너집니다.
      aria-current 를 붙여 읽어 주는 기계도 알게 합니다.
    """
    여기 = posixpath.basename(쪽길)
    후보 = {'./' + 여기, 여기}
    if 여기 == 'index.html':
        후보 |= {'./', '.', ''}
        밑 = posixpath.dirname(쪽길)
        if 밑:
            후보 |= {'../' + posixpath.basename(밑) + '/',
                     posixpath.basename(밑) + '/'}

    def 바꾸기(m):
        주소 = m.group(2)
        if 주소 not in 후보:
            return m.group(0)
        앞 = m.group(1).replace(' href=', ' data-here=')
        뒤 = m.group(3)
        if 'aria-current' not in 앞 + 뒤:
            뒤 = ' aria-current="page"' + 뒤
        return 앞 + '"' + 주소 + '"' + 뒤

    return re.sub(r'(<a[^>]*?\shref=)"([^"]*)"([^>]*>)', 바꾸기, 글)


def 만들목록(d, 만=None):
    """무엇을 만들지 **자료가 정합니다** (계약-11)"""
    할것 = []
    if not 만:
        할것.append(('첫쪽', None, None))
        if d.축제들:
            할것.append(('축제달력', None, None))
        for 갈래 in ('낚시', '해루질'):
            if d.안내(갈래):
                할것.append(('어종목록', None, 갈래))
                for x in d.안내(갈래):
                    할것.append(('어종', x['id'], 갈래))
        # ★ 채비법 쪽 (2026-09-30 주인 지시) — 자료가 있는 만큼만 만듭니다
        if 채비갈래들(d):
            할것.append(('채비목록', None, None))
            # ★ 부품 쪽 (2026-09-30 주인 지시) — 자료가 있으면 만듭니다
            if ((d.채비자료 or {}).get('부품')):
                할것.append(('채비부품', None, None))
            for 갈, _것 in 채비갈래들(d):
                할것.append(('채비', 갈, None))
        # ★ 금어기 쪽 (2026-10-01) — 434쪽이 rule.html 로 링크를 거는데
        #   새 사이트에 쪽이 없었습니다. 서버가 200 을 내는 것은
        #   **옛 사이트 파일이 남아 있어서**였습니다.
        if os.path.isfile(os.path.join(
                ROOT, 'data', 'raw', 'rules', '금어기.json')):
            할것.append(('금어기', None, None))
        할것.append(('물때허브', None, None))
        할것.append(('안내허브', None, None))
        할것.append(('장비', None, None))
        # ★ 사이트를 밝히는 네 쪽 (2026-10-01) — rule.html 과 **같은 구멍**
        #   438쪽 모두가 꼬리에서 about·sources·privacy·photos 를 거는데
        #   새 사이트에 파일이 없었습니다. 서버가 200 을 낸 것은
        #   옛 사이트 파일이 남아 있어서였습니다. 광고 심사가 반드시
        #   보는 쪽이기도 합니다 (주인 확인 — 애드센스 두 번 거절).
        # ★ **방문기록 (2026-10-06 주인 지시)**
        #   새 사이트 448쪽이 방문을 하나도 안 세고 있었습니다.
        #   세는 줄은 template/_footer.html 에 넣었고, 이 쪽은
        #   그 숫자를 봅니다. 열쇠말을 넣어야 보이는 주인 전용
        #   쪽이라 차림표에는 안 겁니다.
        for _것 in ('소개', '출처', '개인정보', '사진출처', '방문기록'):
            할것.append((_것, None, None))
        # ★ 왕초보 그림 강의 (2026-10-01) — **권역 57쪽이 각각 겁니다**
        #   「처음이신가요」 칸이 fish/basics.html · catch/basics.html 로
        #   보내는데 새 사이트에 쪽이 없어 옛 디자인으로 떨어졌습니다.
        for _갈 in ('낚시', '해루질'):
            할것.append(('기초', _갈, None))
        # ★ 물때표 보는 법 (2026-10-01) — 사이트의 **전제**를 설명하는 쪽
        #   tide/ 는 「오늘 몇 시인가」, 이 쪽은 「어떻게 읽는가」입니다.
        할것.append(('물때보는법', None, None))
        # ★ 해루질 준비물 (2026-10-02 주인 지시)
        #   「준비물에서는 페이지를 만들더라도 준비물만 보이게」
        할것.append(('준비물', None, None))
        # ★ 가진 자료 (2026-10-01) — **여덟 번째 끊긴 쪽**
        #   서버의 옛 파일이 「사진 264장 · 축제 190개」라는 낡은
        #   숫자를 내고 있었습니다. 이제 engine/counts.py 한 곳에서
        #   센 값만 적습니다.
        할것.append(('가진자료', None, None))
        # ★ 바다 여행 (2026-10-01) — **아홉 번째 끊긴 쪽**
        #   첫 화면 「06 무엇을 즐길까?」가 가리키는 곳입니다.
        할것.append(('여행', None, None))
        for 묶음 in d.색인['묶음차례']:
            if any(r['묶음'] == 묶음 for r in d.권역들):
                할것.append(('묶음', 묶음, None))
    for r in d.권역들:
        if 만 and r['id'] != 만:
            continue
        할것.append(('권역', r['id'], None))
        for x in d.축제(r['id']):
            할것.append(('축제', x['id'], None))
        for 갈래 in ('낚시', '해루질'):
            if d.셈(r['id'], 갈래):      # 포인트가 있는 것만
                할것.append(('포인트목록', r['id'], 갈래))
    return 할것


def main():
    만 = None
    if '--only' in sys.argv:
        i = sys.argv.index('--only')
        if i + 1 < len(sys.argv):
            만 = sys.argv[i + 1]

    # ★ 어느 언어로 만들지 (2026-09-26)
    #   자료(site.json 의 「만들언어」)가 정하는 것이 원칙입니다.
    #   --lang 은 시험용으로 한 언어만 만들어 볼 때 씁니다.
    언어 = 'ko'
    if '--lang' in sys.argv:
        i = sys.argv.index('--lang')
        if i + 1 < len(sys.argv):
            언어 = sys.argv[i + 1]

    d = 자료()
    # ★ 부품 크기를 **자료에서** art 에 넘깁니다 (2026-09-30)
    #   같은 값을 art.py 와 rigs.json 두 곳에 두면 언젠가 어긋납니다.
    art.크기표넣기(d.채비자료)
    할것 = 만들목록(d, 만)
    떨어짐.clear()

    print('쪽 만들기 (계약-01 — 여기 말고 다른 데서 안 만듭니다)')
    print('  나갈 곳: %s' % 나갈곳)
    if 언어 != 'ko':
        print('  언어: %s' % 언어)
    print('  만들 쪽 %d개' % len(할것))
    if '--list' in sys.argv:
        for 갈, 권역, 갈래 in 할것:
            print('    %-34s %s' % (쪽주소(갈, 권역, 갈래), 갈))
        return 0
    print('')

    # ★ 광고 자료를 **쪽보다 먼저** 만듭니다.
    #   쪽이 ads-data.js 의 판 번호를 쓰기 때문입니다. 나중에 만들면
    #   쪽에 박힌 판 번호가 낡아, 광고를 고쳐도 브라우저가 옛것을 씁니다.
    광고자료쓰기()

    쓴것 = []
    for 갈, 권역, 갈래 in 할것:
        if 갈 == '첫쪽':
            쪽길, 글 = 첫쪽(d, 언어)
            수 = d.셈()
        elif 갈 == '묶음':
            쪽길, 글 = 묶음쪽(d, 권역, 언어)
            수 = d.셈(묶음=권역)
        elif 갈 == '축제달력':
            쪽길, 글 = 축제달력(d, 언어)
            수 = len(d.축제들)
        elif 갈 == '어종목록':
            쪽길, 글 = 어종목록(d, 갈래, 언어)
            수 = len(d.안내(갈래))
        elif 갈 == '어종':
            것 = [x for x in d.안내(갈래) if x['id'] == 권역][0]
            쪽길, 글 = 어종쪽(d, 것, 언어)
            수 = 0
        elif 갈 == '채비목록':
            쪽길, 글 = 채비목록(d, 언어)
            수 = len(채비갈래들(d))
        elif 갈 == '금어기':
            것 = hubs.금어기쪽(d, 언어)
            if not 것:
                continue
            쪽길, 글 = 것
            수 = 0
        elif 갈 == '물때허브':
            쪽길, 글 = hubs_more.물때쪽(d, 언어)
            수 = 0
        elif 갈 == '안내허브':
            쪽길, 글 = hubs_more.안내쪽(d, 언어)
            수 = 0
        elif 갈 == '장비':
            쪽길, 글 = hubs_more.장비쪽(d, 언어)
            수 = 0
        elif 갈 == '기초':
            것 = hubs_basics.기초쪽(d, 권역, 언어)
            if not 것:
                continue
            쪽길, 글 = 것
            수 = 0
        elif 갈 == '물때보는법':
            것 = hubs_muldae.물때보는법쪽(d, 언어)
            if not 것:
                continue
            쪽길, 글 = 것
            수 = 0
        elif 갈 == '준비물':
            # ★ 해루질 준비물 — **catch/ 와 역할이 다릅니다** (2026-10-02)
            #   주인 지적 — 첫 쪽에서 「준비물」과 「대상 17가지」가
            #   같은 곳으로 갔습니다. 셋을 가릅니다 —
            #     gear 무엇을 챙길까 · basics 어떻게 시작할까 ·
            #     catch 무엇을 대상으로 하나
            # ★ **큰 안내도를 만들어 넘깁니다** (2026-10-06)
            #   채비 16장과 **같은 함수**가 만듭니다 (계약-01).
            #   `밭='catch'` 만 다릅니다 — data/img/catch/gear.webp
            _안내도 = 안내도(d, 'gear', url.catch_gear(언어),
                             '해루질 준비물', 밭='catch')
            # ★ **폭을 맞춥니다** (2026-10-06 — 찍어 보고 잡았습니다)
            #   채비 쪽에서는 `section > wrap` 안에 들어가 양옆
            #   여백을 받습니다. 해루질 쪽은 갈래칸에 바로 넣었더니
            #   **안내도만 화면 끝에서 끝까지** 뻗어, 위의 제목·
            #   설명과 왼쪽 선이 안 맞았습니다.
            #   같은 틀로 감싸 같은 자리에 섭니다.
            if _안내도:
                _안내도 = ('<section class="section section--white">'
                           '<div class="wrap">%s</div></section>' % _안내도)
            것 = hubs_gear.준비물쪽(d, 언어, 안내도글=_안내도)
            if not 것 or not 것[0]:
                continue
            쪽길, 글 = 것
            수 = 0
        elif 갈 == '가진자료':
            쪽길, 글 = hubs_data.가진자료쪽(d, 언어)
            수 = 0
        elif 갈 == '여행':
            쪽길, 글 = hubs_travel.여행쪽(d, 언어)
            수 = 0
        elif 갈 == '소개':
            쪽길, 글 = hubs_site.소개쪽(d, 언어)
            수 = 0
        elif 갈 == '출처':
            쪽길, 글 = hubs_site.출처쪽(d, 언어)
            수 = 0
        elif 갈 == '개인정보':
            쪽길, 글 = hubs_site.개인정보쪽(d, 언어)
            수 = 0
        elif 갈 == '사진출처':
            쪽길, 글 = hubs_site.사진출처쪽(d, 언어)
            수 = 0
        elif 갈 == '방문기록':
            쪽길, 글 = hubs_site.방문기록쪽(d, 언어)
            수 = 0
        elif 갈 == '채비부품':
            쪽길, 글 = 부품쪽(d, 언어)
            수 = len(부품사전(d))
        elif 갈 == '채비':
            쪽길, 글 = 채비쪽(d, 권역, 언어)
            수 = 0
        elif 갈 == '축제':
            것 = [x for x in d.축제들 if x['id'] == 권역][0]
            쪽길, 글 = 축제쪽(d, 것, 언어)
            수 = 0
        elif 갈 == '권역':
            쪽길, 글 = 권역쪽(d, 권역, 언어)
            수 = d.셈(권역)
        else:
            쪽길, 글 = 포인트쪽(d, 권역, 갈래, 언어)
            수 = d.셈(권역, 갈래)
        글 = _자기링크없애기(글, 쪽길)
        io.write(os.path.join(나갈곳, 쪽길), 글)
        쓴것.append((쪽길, len(글), 수))

    # 함께 쓰는 것 — 차림표와 움직임.
    # 자료를 안 고쳤으면 여기도 그대로여야 합니다 (계약-07)
    #
    # ★ **목록을 손으로 적지 않습니다** (2026-09-28)
    #
    #   전에는 (('css','site.css'), ('css','home.css'), …) 처럼
    #   이름을 하나하나 적어 두었습니다. 그래서 `tidegraph.css` 를
    #   새로 만들어 쪽에 싣고도 **목록에 안 적어 배포본에서 빠졌습니다.**
    #   쪽 57개가 없는 차림표를 불렀습니다 (check_links 가 잡음).
    #
    #   오늘만 일곱 번째로 난 같은 병입니다 —
    #   「한 곳을 고치고 다른 곳을 잊는다」.
    #   그래서 **있는 것을 전부 옮깁니다.** 목록이 없으면 잊을 것도 없습니다.
    for 갈래 in ('css', 'js'):
        칸 = os.path.join(ASSETS, 갈래)
        if not os.path.isdir(칸):
            continue
        for 이름 in sorted(os.listdir(칸)):
            if not 이름.endswith('.' + 갈래):
                continue
            io.write(os.path.join(나갈곳, 'assets', 갈래, 이름),
                     io.read(os.path.join(칸, 이름)))

    # ── 사진 — 자료가 가리키는 것만 옮깁니다 (2026-09-27 규칙 6-1)
    #
    #   site/ 를 스스로 온전하게 만들어야 검사가 보는 것과
    #   올라가는 것이 같아집니다. 옛 저장소에 기대면 로컬에서는
    #   깨진 채로 통과하고 서버에서만 멀쩡해집니다.
    옮긴수, 건너뛴수, 못찾음 = 0, 0, []

    def 옮기기(상대):
        """사진 한 장을 옮깁니다. 못 찾으면 **적어 둡니다.**"""
        바탕 = 사진바탕(상대)
        if 바탕 is None:
            못찾음.append(상대)
            return
        갈곳 = os.path.join(나갈곳, 상대.replace('/', os.sep))
        if (os.path.isfile(갈곳)
                and os.path.getsize(갈곳) == os.path.getsize(바탕)):
            return True                   # 이미 같습니다 (계약-07)
        io.copy_binary(바탕, 갈곳)
        return False

    for 한장 in d.사진들:
        상대 = 한장.get('파일')
        if not 상대:
            continue
        났나 = 옮기기(상대)
        if 났나 is True:
            건너뛴수 += 1
        elif 났나 is False:
            옮긴수 += 1

    # ★ **걸러 낸 사진은 치웁니다** (2026-09-29 주인 지시)
    #
    #   photo-reject.json 에 적어 자료에서는 걸렀는데, **전에 옮겨 둔
    #   파일이 site/ 에 그대로 남아** 있었습니다.
    #   계약-07(두 번 만들어도 결과가 같아야 한다)이 이것을 잡았습니다.
    #   자료에 없는 파일은 아무도 안 만들고 아무도 안 지우니
    #   다시 만들 때마다 결과가 달라집니다.
    #
    #   원본은 옛 저장소(badagaja-site/img/)에 그대로 있습니다.
    #   여기서 지우는 것은 **옮겨 둔 사본**뿐입니다.
    치운수 = 0
    for _버릴 in sorted(d.거른사진):
        _길 = os.path.join(나갈곳, _버릴.replace('/', os.sep))
        if os.path.isfile(_길):
            # ★ 지우는 것은 **site/ 안의 사본**뿐입니다.
            #   원본은 옛 저장소(badagaja-site/img/)에 그대로 있고,
            #   이 파일은 build 가 스스로 옮겨 둔 생성물입니다.
            #   자료를 지우는 것이 아니므로 밝히고 지웁니다.
            os.remove(_길)  # 계약-17 예외
            치운수 += 1

    # 걸음 카드 그림 — 옛 첫 화면 짜임이 씁니다 (2026-09-27)
    #   img/ui/step/1.webp … 6.webp
    for n in range(1, 7):
        옮기기('img/ui/step/%d.webp' % n)

    # ★ 못 찾은 것을 **조용히 넘기지 않습니다** (2026-09-28)
    #   전에는 그냥 건너뛰었습니다. 그래서 옛 저장소가 없는
    #   컴퓨터(깃허브 액션)에서 **사진 0장**이 되는데도 아무 말이
    #   없었습니다. 주인이 화면을 보고서야 잡았던 그 사고입니다.
    if 못찾음:
        print('  ✗ 사진을 못 찾았습니다 %d장 — 첫 세 장: %s'
              % (len(못찾음), ' · '.join(못찾음[:3])))
        print('     assets/photo/ 에 있어야 합니다 (주인 규칙 15)')

    # 그린 그림 — 사진 자료가 없는 쪽이 씁니다 (2026-09-27)
    #   engine/make_cover.py 가 만든 것을 그대로 옮깁니다.
    덮개뿌리 = os.path.join(ASSETS, 'cover')
    if os.path.isdir(덮개뿌리):
        for 이름 in sorted(os.listdir(덮개뿌리)):
            바탕 = os.path.join(덮개뿌리, 이름)
            if os.path.isfile(바탕):
                io.write(os.path.join(나갈곳, 'assets', 'cover', 이름),
                         io.read(바탕))

    # 대상 아이콘 — 목록 카드가 씁니다 (2026-09-28 주인 규칙 6-1)
    #   engine/make_icons.py 가 그린 것을 그대로 옮깁니다.
    #   맨 위 큰 덮개 그림을 뺀 뒤 「그림이 하나도 없는 쪽」이 생겨
    #   check_photos 가 잡았습니다. 카드마다 작게 넣습니다.
    아이콘뿌리 = os.path.join(ASSETS, 'icon')
    뿌리로갈것 = ('favicon.ico', 'favicon.svg', 'apple-touch-icon.png')
    if os.path.isdir(아이콘뿌리):
        for 이름 in sorted(os.listdir(아이콘뿌리)):
            if 이름.endswith('.svg') and 이름 not in 뿌리로갈것:
                io.write(os.path.join(나갈곳, 'assets', 'icon', 이름),
                         io.read(os.path.join(아이콘뿌리, 이름)))

    # 아이콘 — 쪽마다 머리에서 부르므로 뿌리에 있어야 합니다.
    # 없으면 416쪽 전부에서 아이콘이 깨집니다 (2026-09-26 check_links 가 잡음)
    for 이름 in 뿌리로갈것:
        바탕 = os.path.join(ASSETS, 'icon', 이름)
        if os.path.exists(바탕):
            io.copy_binary(바탕, os.path.join(나갈곳, 이름))

    # ★ 검색엔진에게 알리는 세 파일 (2026-09-28)
    #   sitemap.xml · robots.txt · llms.txt
    #   **판 지문보다 먼저** 만듭니다 — 지문이 이 셋까지 세어야
    #   서버에 올린 것이 내가 만든 그것인지 증명됩니다.
    #   ★ make_sitemap 은 **글만 돌려줍니다.** 쓰는 것은 여기입니다 —
    #     site/ 에 쓰는 곳이 둘이 되면 나중에 무엇이 어디서
    #     만들어졌는지 모르게 됩니다 (계약-01).
    from engine import make_sitemap
    알림글, _, _ = make_sitemap.만들글()
    for 이름 in sorted(알림글):
        io.write(os.path.join(나갈곳, 이름), 알림글[이름])
    print('  검색 알림 %s' % ' · '.join(sorted(알림글)))

    # ★ **여기가 어디인지 밝히는 쪽지** — 운영에도 둡니다
    #   (2026-09-29 — 운영 배포가 이것이 없어 되돌려졌습니다)
    #
    #   전에는 검증판(mark_stage)만 만들었습니다. 그런데 이 쪽지는
    #   **「검사기가 애초에 딴 데를 보고 있지 않은가」**를 막는
    #   장치입니다. 운영에서 더 중요합니다 — 딴 곳을 재고
    #   「괜찮다」고 하면 손님이 있는 쪽이 망가져도 모릅니다.
    #
    #   검증판은 mark_stage 가 kind 를 stage 로 덮어씁니다.
    import json as _j
    io.write(os.path.join(나갈곳, '__probe__', 'identity.json'),
             _j.dumps({
                 '_무엇인가': 'badagaja-probe',
                 '_왜있나': ('이 쪽지가 열리는 자리가 검사기가 재고 있는 '
                             '자리입니다. 열리지 않으면 검사기가 딴 곳을 '
                             '보고 있는 것입니다.'),
                 'where': '/',
                 'kind': 'production',
             }, ensure_ascii=False, indent=2) + '\n')

    # ★ 맨 마지막에 판 지문을 남깁니다 (2026-09-27 바깥 검수 3차)
    #   올린 것이 내가 만든 바로 그것인지 서버에서 증명하려고.
    #   시각은 안 넣습니다 — 넣으면 다시 만들 때마다 달라져
    #   멱등성(계약-07)이 깨집니다.
    from engine import build_id
    판 = build_id.만들기(나갈곳)

    for 쪽길, 크기, 수 in 쓴것:
        print('  %-40s %6.1fKB  포인트 %d곳' % (쪽길, 크기 / 1024.0, 수))
    print('')
    print('  쪽 %d개 · 합계 %.0fKB' % (len(쓴것), sum(x[1] for x in 쓴것) / 1024.0))
    print('  사진 %d장 (새로 옮긴 것 %d · 그대로 둔 것 %d%s)'
          % (옮긴수 + 건너뛴수, 옮긴수, 건너뛴수,
             ' · 명소와 달라 치운 것 %d' % 치운수 if 치운수 else ''))
    print('  판 지문  커밋 %s · 파일 %d개 · %s'
          % (판.get('커밋짧게'), 판.get('파일수', 0),
             판.get('통지문', '')[:16]))
    if 떨어짐:
        print('')
        print('  ~ 그 언어 값이 없어 한국어로 떨어진 곳 %d번'
              % sum(떨어짐.values()))
        print('    한국어로 나온 자리에는 lang="ko" 가 붙습니다 — '
              '조용히 섞이지 않습니다')
        print('    얼마나 비었는지는 engine/check_i18n.py 가 잽니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
