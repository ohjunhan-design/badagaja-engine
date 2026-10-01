# -*- coding: utf-8 -*-
"""주소를 만드는 **단 하나의 곳**입니다.  (계약-03)

왜
    옛 사이트는 주소 규칙이 두 가지였습니다.

        point/01_sinan_fishing.html          전남 15권역
        point/gangwon/sokcho_fishing.html    나머지 42권역

    통일하려면 쪽·사이트맵·링크 1,098군데를 고쳐야 해서 손대지 못했습니다.
    여기 함수만 쓰면 규칙을 **한 줄 고쳐 전부 바뀝니다.**

규칙
    · 주소는 자료의 아이디에서 만듭니다. 이름에서 만들지 않습니다
    · 묶음 폴더를 두지 않습니다 — 권역 아이디가 이미 유일합니다
    · 언어는 맨 앞에 붙입니다 (`/zh-cn/...`)

보기
    point_list('taean', '낚시')       point/taean-fishing.html
    point_list('taean', '낚시', 'zh') zh-cn/point/taean-fishing.html
    region('taean')                   taean.html
"""
import os
import posixpath

SITE = 'https://badagaja.com'

# 갈래 아이디 ↔ 주소에 쓰는 글자
갈래주소 = {'낚시': 'fishing', '해루질': 'gleaning'}

# 언어 ↔ 앞에 붙는 폴더. 한국어는 안 붙입니다
언어폴더 = {'ko': '', 'zh': 'zh-cn'}


def _붙이기(언어, *조각):
    앞 = 언어폴더.get(언어, '')
    부분 = ([앞] if 앞 else []) + [str(x) for x in 조각 if x]
    return posixpath.join(*부분)


def region(권역, 언어='ko'):
    """권역 첫 쪽 — taean.html"""
    return _붙이기(언어, '%s.html' % 권역)


# 옛 사이트의 포인트 쪽 주소. **주소를 바꾸지 않기 위해** 그대로 씁니다.
# data/raw/index.json 의 _옛주소 를 읽어 둡니다 (계약-03 — 여기 한 곳에서만).
_옛주소 = None


def _옛주소표():
    global _옛주소
    if _옛주소 is None:
        import json
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.dirname(here)
        데이터 = os.environ.get('BADAGAJA_DATA', os.path.join(root, 'data'))
        길 = os.path.join(데이터, 'raw', 'index.json')
        try:
            with open(길, encoding='utf-8-sig') as f:
                _옛주소 = (json.load(f).get('_옛주소') or {}).get('포인트쪽') or {}
        except OSError:
            _옛주소 = {}
    return _옛주소


def point_list(권역, 갈래, 언어='ko'):
    """포인트 목록 쪽.

    ★ 옛 주소를 그대로 씁니다 (2026-09-26, 바깥 검수 지적)
      처음에는 point/taean-fishing.html 로 통일했습니다. 보기에는
      깔끔하지만, 그러면 옛 주소 118쪽이 404 가 됩니다.
      검색에 쌓아 둔 것이 날아가고, 즐겨찾기 해 두신 분이 못 찾습니다.

      코드가 깔끔해지자고 걸 만한 것이 아닙니다.
      옛 사이트는 전남만 point/01_sinan_fishing.html 꼴이고 나머지는
      point/gangwon/sokcho_fishing.html 꼴로 섞여 있습니다.
      그 섞인 모습 그대로 두되, **읽는 곳은 여기 하나**입니다.
    """
    있는것 = (_옛주소표().get(권역) or {}).get(갈래)
    if 있는것:
        return _붙이기(언어, 있는것) if 언어폴더.get(언어) else 있는것
    # 새로 생긴 권역은 새 꼴로 (옛 주소가 없으니 바뀔 것도 없습니다)
    g = 갈래주소.get(갈래, 갈래)
    return _붙이기(언어, 'point', '%s-%s.html' % (권역, g))


def group(묶음, 언어='ko'):
    """묶음 쪽 — chungnam/"""
    return _붙이기(언어, 묶음, 'index.html')


def home(언어='ko'):
    return _붙이기(언어, 'index.html') if 언어폴더.get(언어) else 'index.html'


def festival(축제아이디, 언어='ko'):
    """축제 쪽 — festival/boryeong-2.html

    아이디는 옛 사이트의 파일 이름을 그대로 씁니다.
    주소가 바뀌면 검색에서 끊기기 때문입니다 (festival-files.json).
    """
    return _붙이기(언어, 'festival', '%s.html' % 축제아이디)


def festival_list(언어='ko'):
    """축제 달력 — festival/"""
    return _붙이기(언어, 'festival', 'index.html')


def guide(어종, 갈래, 언어='ko'):
    """어종 안내 쪽 — fish/ureok.html · catch/bajirak.html

    옛 사이트와 같은 자리에 둡니다. 주소가 바뀌면 검색에서 끊깁니다.
    """
    칸 = 'fish' if 갈래 == '낚시' else 'catch'
    return _붙이기(언어, 칸, '%s.html' % 어종)


def guide_list(갈래, 언어='ko'):
    """어종 목록 — fish/ · catch/"""
    칸 = 'fish' if 갈래 == '낚시' else 'catch'
    return _붙이기(언어, 칸, 'index.html')


def rig(갈래, 언어='ko'):
    """채비법 쪽 — rig/float.html · rig/bottom.html …

    ★ 2026-09-30 주인 지시 —
      「낚시 채비법에 관한 별도 페이지가 있었으면 좋겠어
        원투법 찌낙시법 등 채비에 관한 별도 페이지가 있으면 좋겠어」

    갈래 이름은 `data/raw/rigs.json` 의 열쇠를 그대로 씁니다
    (bottom · float · sabiki · egi · jighead). 자료가 주소를 정합니다.
    """
    return _붙이기(언어, 'rig', '%s.html' % 갈래)


def rig_list(언어='ko'):
    """채비법 모음 — rig/"""
    return _붙이기(언어, 'rig', 'index.html')


def rig_parts(언어='ko'):
    """부품별 이름과 쓰는 법 — rig/parts.html

    ★ 2026-09-30 주인 지시 —
      「각 부품별 크기 사용용도, 종류 이렇게 별도의 한 페이지를
        만들면 어떨까?」
      「낚시 채비법 페이지에 부품별 명칭 및 사용법 바로가기
        이렇게 페이지하나만들면 더 좋을거 같아」
    """
    return _붙이기(언어, 'rig', 'parts.html')


def species(어종, 언어='ko'):
    return _붙이기(언어, 'fish', '%s.html' % 어종)


def full(길, 언어='ko'):
    """사이트 안 길 → 온전한 주소. canonical·og:url·사이트맵이 씁니다

    ★ 뿌리의 index.html 도 `/` 로 냅니다 (2026-09-27)

        전에는 'festival/index.html' → '/festival/' 로는 바꾸면서
        맨 뿌리의 'index.html' 은 그대로 두었습니다. 그래서

            옛 사이트  canonical = https://badagaja.com/
            새 틀      canonical = https://badagaja.com/index.html

        **검색엔진은 이 둘을 다른 쪽으로 봅니다.** 네이버에 이미
        색인된 것은 `/` 입니다. 새 쪽이 「나는 /index.html 이다」라고
        하면 쌓아 둔 순위가 흔들립니다.

        첫 화면은 사이트에서 가장 중요한 쪽입니다. 다른 407쪽이
        멀쩡해도 이 한 줄 때문에 크게 잃을 수 있었습니다.
    """
    if 길 == 'index.html' or 길.endswith('/index.html'):
        길 = 길[:-len('index.html')]
    return '%s/%s' % (SITE, 길.lstrip('/'))


def rel(여기, 저기):
    """쪽 하나에서 다른 쪽으로 가는 상대 주소.

    point/taean-fishing.html 에서 taean.html 로 → ../taean.html
    """
    나온길 = posixpath.relpath(저기, posixpath.dirname(여기) or '.')
    return 나온길


def 뿌리로(쪽길, 언어='ko'):
    """그 쪽에서 **첫 화면으로 가는 길.**

    ★ 왜 함수로 뺐나 (2026-09-27 — 로고가 눌려도 안 움직였습니다)

        build.py 안에 이 줄이 **여섯 군데 베껴져** 있었습니다.

            뿌리 = url.rel(쪽길, 'index.html').replace('index.html', '')

        깊은 쪽은 잘 됩니다.
            point/chungnam/x.html  →  ../../index.html  →  ../../
            festival/index.html    →  ../index.html     →  ../

        그런데 **뿌리에 있는 쪽**은 이렇게 됩니다.
            taean.html             →  index.html        →  ''   ← 빈 링크

        그래서 권역 쪽 57개 **전부**의 로고가 `href=""` 였습니다.
        눌러도 홈으로 안 가고 **제자리에서 새로고침**만 됩니다.
        손님이 홈으로 가려고 누르는 자리인데 말입니다.

        engine/check_golden.py 를 만들어 처음 돌리자마자 잡았습니다
        (「빈 링크 2개 — 57쪽」). 링크 검사기는 못 잡았습니다 —
        **빈 주소는 「없는 곳」이 아니라서** 걸러지지 않았습니다.

    ★ 빈 글을 안 돌려줍니다
        어디서 부르든 **눌리는 주소**가 나옵니다.
    """
    끝 = rel(쪽길, home(언어)).replace('index.html', '')
    return 끝 or './'


def asset(길, 여기, 판=None):
    """그림·CSS·JS 주소. 판 번호를 붙여 브라우저가 옛것을 안 쓰게 합니다.

    판 번호는 **파일 내용에서** 만듭니다 — 시각을 넣으면 안 고쳐도
    결과가 달라져 재현성이 깨집니다 (계약-08).
    """
    주소 = rel(여기, 길)
    return '%s?v=%s' % (주소, 판) if 판 else 주소


def rule(언어='ko'):
    """금어기와 잡으면 안 되는 크기 — rule.html

    ★ 2026-10-01 — 434쪽이 이리로 링크를 거는데 쪽이
      없었습니다. 서버가 200 을 낸 것은 옛 사이트 파일이
      남아 있어서였습니다.
    """
    return _붙이기(언어, 'rule.html')


def gear(언어='ko'):
    """무엇을 챙겨 가나 — gear.html

    ★ **채비(rig)와 다릅니다.** gear 는 「무엇을 준비하나」,
      rig 는 「어떻게 묶나」입니다. 492곳이 거는 뜻을
      한꺼번에 바꾸면 404 는 없어져도 짜임이 틀어집니다.
    """
    return _붙이기(언어, 'gear.html')


def travel(언어='ko'):
    """바다 여행 — travel/index.html

    ★ **아홉 번째로 끊겨 있던 쪽**입니다 (2026-10-01).
      첫 화면 「06 무엇을 즐길까?」가 가리키는데 build 가 안 만들어
      서버의 옛 파일이 응답했습니다. check_manifest.py 가 찾았습니다.
    """
    return _붙이기(언어, 'travel', 'index.html')


def data(언어='ko'):
    """가진 자료 — data.html

    ★ **여덟 번째로 끊겨 있던 쪽**입니다 (2026-10-01).
      새 사이트에 없어 옛 파일이 응답했고, 거기 적힌 숫자가
      낡아 있었습니다 (사진 264장 · 축제 190개).
    """
    return _붙이기(언어, 'data.html')


def muldae(언어='ko'):
    """물때표 보는 법 — muldae.html

    ★ `tide/` 와 다릅니다. tide 는 「오늘 몇 시인가」,
      이 쪽은 「어떻게 읽는가」입니다 (2026-10-01).
      옛 사이트에 아홉 절·그림 7장으로 이미 좋은 글이 있었는데
      새 틀이 안 만들어 끊겨 있었습니다.
    """
    return _붙이기(언어, 'muldae.html')


def basics(갈래, 언어='ko'):
    """왕초보 그림 강의 — fish/basics.html · catch/basics.html

    ★ **권역 57쪽이 각각 겁니다.** 「처음이신가요」 칸이 여기로
      보냅니다. 새 사이트에 쪽이 없어 옛 디자인으로 떨어지고
      있었습니다 (2026-10-01).
    """
    집 = 'fish' if 갈래 == '낚시' else 'catch'
    return _붙이기(언어, 집, 'basics.html')


# ── 사이트를 밝히는 네 쪽 ────────────────────────────
#  ★ 2026-10-01 — **438쪽 모두가 꼬리에서 이 넷을 겁니다.**
#    그런데 새 사이트에 파일이 없어, 서버에 남은 **옛 사이트 파일**이
#    응답하고 있었습니다. 손님이 「개인정보처리방침」을 누르면
#    디자인이 통째로 다른 쪽으로 떨어집니다.
#    rule.html·gear.html 때와 **똑같은 구멍**입니다.
#
#    이 넷은 광고 심사에서 **반드시 보는 쪽**이기도 합니다.
#    누가 만드는가 · 자료는 어디서 오는가 · 개인정보를 어떻게 다루는가.
def about(언어='ko'):
    """누가 어떻게 만드나 — about.html"""
    return _붙이기(언어, 'about.html')


def privacy(언어='ko'):
    """개인정보처리방침 — privacy.html"""
    return _붙이기(언어, 'privacy.html')


def sources(언어='ko'):
    """자료 출처 — sources.html"""
    return _붙이기(언어, 'sources.html')


def photos(언어='ko'):
    """사진 출처 — photos.html"""
    return _붙이기(언어, 'photos.html')


def tide_list(언어='ko'):
    """전국 물때 — tide/index.html"""
    return _붙이기(언어, 'tide', 'index.html')


def guide_hub(언어='ko'):
    """무엇을 잡나 — guide/index.html"""
    return _붙이기(언어, 'guide', 'index.html')
