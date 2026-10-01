# -*- coding: utf-8 -*-
"""**같은 사실을 두 곳에서 관리하고 있지 않은가** — 짜임을 봅니다.

★ 왜 만들었나 (2026-09-28 바깥 검수 7차 지시)

    하루에 일곱 번 같은 사고가 났습니다.

        바깥 자리 목록  check_console 만 가짐      → 검사기 셋이 몰랐습니다
        크롬 자리      검사기 여섯에 베껴짐
        메모리 재기     검사기 둘에 베껴짐
        keep.json 읽기  check_assets 만 읽음      → 6번·11번 FAIL
        홈으로 가는 길   build.py 안 일곱 군데      → 권역 57쪽 로고가 빈 링크
        갱신 차례      refresh 와 시험에 따로      → 서로 달랐습니다
        상태 목록      ERROR 를 더하고 찍는 표를 잊음 → 판정이 통째로 죽음
        차림표 목록     손으로 적어 tidegraph.css 를 잊음 → 쪽 57개가 깨짐

    바깥 검수가 뿌리를 짚었습니다.

        이번 사고 넷은 별개처럼 보이지만 사실 같은 뿌리입니다.
        **하나의 사실을 여러 곳에서 따로 정의하고 있습니다.**

        check_architecture.py 의 목적은 「코드가 예쁜가」가 아니라
        **「같은 사실을 두 곳에서 관리하고 있지 않은가」** 입니다.

★ 조심할 것 — 거짓 경보를 내면 아무도 안 봅니다
    바깥 검수가 짚었습니다.

        「리스트가 하드코딩되어 있으니 FAIL」 이라고 하면 안 됩니다.
        **「실제 파일 집합과 별도의 관리 목록이 존재한다」** 를 잡아야 합니다.

    그래서 목록 자체를 나무라지 않습니다.
    **진짜 있는 것과 어긋날 때만** 말합니다.

★ 검사 등급 (계약-21)
    막음 — 지금 어긋나 있습니다. 고쳐야 합니다
    알림 — 어긋날 수 있는 자리입니다. 봐 두세요

쓰는 법
    python engine/check_architecture.py
    python engine/check_architecture.py --strict
    python engine/check_architecture.py --자세히
"""
import ast
import os
import tempfile
import re
import sys
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

막음, 알림 = [], []
자세히 = False


def 소스들(밖=()):
    """저장소의 파이썬 소스. 만든 것·캐시는 뺍니다.

    ★ **자기 자신은 늘 뺍니다** — 찾을 무늬를 코드에 담고 있어
      안 빼면 언제나 자기를 잡습니다 (거짓 경보).
    """
    밖 = tuple(밖) + ('engine/check_architecture.py',)
    for p in sorted(glob.glob(os.path.join(ROOT, '**', '*.py'),
                              recursive=True)):
        상대 = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if 상대.startswith(('site/', '.git/')) or '__pycache__' in 상대:
            continue
        if any(상대.startswith(x) for x in 밖):
            continue
        yield 상대, io.read(p, default='')


def 말(등급, 글, 자세한말=''):
    (막음 if 등급 == '막음' else 알림).append(글)
    print('  %s %s' % ('✗' if 등급 == '막음' else '!', 글))
    if 자세한말:
        for 줄 in 자세한말.split('\n'):
            if 줄.strip():
                print('      %s' % 줄)


def 됨(글, 자세한말=''):
    print('  · %s' % 글)
    if 자세히 and 자세한말:
        for 줄 in 자세한말.split('\n'):
            if 줄.strip():
                print('      %s' % 줄)


# ── 1. 파일 목록을 손으로 적고 있는가 ─────────────────────
#
#   ★ 2026-09-28 — tidegraph.css 를 만들고 목록에 안 적어
#     배포본에서 빠졌습니다. 쪽 57개가 없는 차림표를 불렀습니다.
#
#   ★ 목록이 있다고 나무라지 않습니다.
#     **진짜 있는 것과 어긋날 때만** 말합니다.
def 검사1_파일목록():
    print('[1] 파일 이름을 손으로 적어 둔 곳이 진짜와 어긋나는가')
    볼것 = [
        ('차림표', os.path.join(ASSETS, 'css'), '.css'),
        ('스크립트', os.path.join(ASSETS, 'js'), '.js'),
        ('틀', os.path.join(ROOT, 'template'), '.html'),
    ]
    났나 = False
    for 무엇, 칸, 꼬리 in 볼것:
        if not os.path.isdir(칸):
            continue
        진짜 = set(x for x in os.listdir(칸) if x.endswith(꼬리))
        # ★ 조각 틀(_head.html 처럼)은 **틀이 틀을 부릅니다.**
        #   생성기가 이름을 안 적는 것이 정상입니다.
        진짜 = set(x for x in 진짜 if not x.startswith('_'))
        if not 진짜:
            continue
        # 소스에서 그 꼬리를 가진 이름을 모읍니다
        적힌것 = collections.defaultdict(set)
        무늬 = re.compile(r"['\"]([\w.-]+%s)['\"]" % re.escape(꼬리))
        for 상대, s in 소스들():
            for 이름 in 무늬.findall(s):
                if 이름 in 진짜:
                    적힌것[상대].add(이름)
        for 상대, 적은것 in sorted(적힌것.items()):
            # 두 개 넘게 적어 둔 곳만 「목록」으로 봅니다
            if len(적은것) < 2:
                continue
            # ★ 시험은 일부러 몇 개를 골라 적습니다 — 목록이 아닙니다
            if 상대.startswith('tests/'):
                continue
            # ★ 검사기가 「이것만 본다」고 고른 것도 목록이 아닙니다.
            #   진짜와 어긋나도 탈이 아닙니다.
            if 상대.startswith('engine/check_'):
                continue
            빠진것 = 진짜 - 적은것
            if 빠진것:
                났나 = True
                말('막음',
                   '%s에 %s 이름을 %d개 적어 두었는데 %d개가 빠졌습니다 (%s)'
                   % (상대, 무엇, len(적은것), len(빠진것), ' · '.join(sorted(빠진것))),
                   '진짜 있는 것: %s' % ' · '.join(sorted(진짜)))
    if not 났나:
        됨('손으로 적은 파일 목록이 진짜와 어긋나지 않습니다')


# ── 2. 같은 판단을 여러 곳에서 하는가 ─────────────────────
#
#   ★ 한 곳에 모아 둔 것을 **정말 다들 쓰는지** 봅니다.
#     모아 놓고 딴 데서 또 하면 모은 뜻이 없습니다.
모은것 = [
    ('우리 것인가 바깥 것인가', 'engine/net.py',
     [r'coupang', r'fonts\.googleapis', r'pstatic', r'daumcdn'],
     ('engine/net.py',)),
    ('크롬은 어디 있나', 'engine/machine.py',
     [r'Program Files.*[Cc]hrome', r'google-chrome'],
     ('engine/machine.py',)),
    ('메모리는 얼마나 남았나', 'engine/machine.py',
     [r'GlobalMemoryStatusEx', r'MemAvailable'],
     ('engine/machine.py',)),
    ('이 주소는 무엇인가', 'engine/pages.py',
     # ★ 이름만 스치는 것이 아니라 **실제로 읽는 것**만 봅니다
     [r"read_json\([^)]*keep\.json", r"'남길것'"],
     ('engine/pages.py', 'engine/check_keep.py', 'engine/keep_detail.py',
      'engine/build.py')),
    ('갱신 차례', 'engine/refresh.py',
     [r"migrate_photos\.py'", r"migrate_map\.py'"],
     ('engine/refresh.py',)),
]


def 검사2_모은판단():
    print('[2] 한 곳에 모은 판단을 딴 곳에서 또 하고 있는가')
    났나 = False
    for 무엇, 집, 무늬들, 봐줄것 in 모은것:
        어긴곳 = []
        for 상대, s in 소스들():
            if 상대 in 봐줄것:
                continue
            for 무늬 in 무늬들:
                if re.search(무늬, s):
                    어긴곳.append(상대)
                    break
        if 어긴곳:
            났나 = True
            말('알림',
               '「%s」는 %s 가 맡는데 %d곳에서 또 합니다'
               % (무엇, 집, len(어긴곳)),
               ' · '.join(어긴곳[:5]))
        else:
            됨('「%s」 — %s 한 곳에서만' % (무엇, 집))
    if not 났나:
        pass


# ── 3. 상태 목록이 쓰는 곳과 맞는가 ───────────────────────
#
#   ★ 2026-09-28 — ERROR 를 더하고 **찍는 표에 안 더해**
#     판정이 KeyError 로 통째로 죽었습니다.
def 검사3_상태목록():
    print('[3] 상태를 더했는데 다루는 곳을 빠뜨렸는가')
    s = io.read(os.path.join(ROOT, 'engine', 'gate.py'), default='')
    m = re.search(r"상태들 = \(([^)]*)\)", s)
    if not m:
        말('알림', 'gate.py 에서 상태 목록을 못 찾았습니다')
        return
    상태들 = re.findall(r"'([A-Z_.]+)'", m.group(1))
    # 상태를 다루는 표·판정
    표들 = re.findall(r"표 = \{([^}]*)\}", s)
    다룸 = set()
    for 표 in 표들:
        다룸 |= set(re.findall(r"'([A-Z_.]+)'", 표))
    빠진것 = [x for x in 상태들 if x not in 다룸]
    # setdefault 로 채우면 봐줍니다
    if 빠진것 and 'setdefault' not in s:
        말('막음', '상태 %s 를 찍는 표가 안 다룹니다 — KeyError 가 납니다'
           % ' · '.join(빠진것))
    else:
        됨('상태 %d가지를 찍는 표가 모두 다룹니다 (%s)'
           % (len(상태들), ' · '.join(상태들)))


# ── 4. 검사기가 판정에 물려 있는가 ────────────────────────
#
#   ★ 검사기를 만들어 두고 gate 에 안 물리면 **아무도 안 돌립니다.**
#     있는 줄 알았던 검사가 도는 적이 없습니다.
def 검사4_검사기등록():
    print('[4] 만든 검사기가 판정에 물려 있는가')
    gate = io.read(os.path.join(ROOT, 'engine', 'gate.py'), default='')
    검사기 = sorted(os.path.basename(p) for p in
                    glob.glob(os.path.join(ROOT, 'engine', 'check_*.py')))
    안물림 = [x for x in 검사기 if x not in gate]
    if 안물림:
        말('막음', '판정에 안 물린 검사기 %d개 — 아무도 안 돌립니다'
           % len(안물림), ' · '.join(안물림))
    else:
        됨('검사기 %d개가 모두 판정에 물려 있습니다' % len(검사기))


# ── 5. 같은 고르개가 여러 차림표에 있는가 ─────────────────
#
#   ★ 바깥 검수 지시 — 세 등급으로 나눕니다
#       같은 고르개가 여러 파일에                    알림
#       + 같은 속성까지 겹침                        센 알림
#       + 값이 서로 다름                            부딪힘 (막음)
def 검사5_차림표겹침():
    print('[5] 같은 고르개가 여러 차림표에서 부딪히는가')
    칸 = os.path.join(ASSETS, 'css')
    if not os.path.isdir(칸):
        return
    규칙 = collections.defaultdict(dict)   # 고르개 → {파일: {속성: 값}}
    for 이름 in sorted(os.listdir(칸)):
        if not 이름.endswith('.css'):
            continue
        s = io.read(os.path.join(칸, 이름), default='')
        s = re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)
        for m in re.finditer(r'([^{}@]+)\{([^{}]*)\}', s):
            고르개 = ' '.join(m.group(1).split())
            if not 고르개 or 고르개.startswith(('@', '%')):
                continue
            # ★ **from · to · 25%** 는 고르개가 아닙니다 (2026-09-29)
            #   @keyframes 안의 **자리 표시**입니다. 움직임을 두 파일에
            #   각각 넣으면 「같은 고르개가 다른 값」으로 잘못 잡혔습니다.
            #   겪은 일: home.css 의 gbIn 과 site.css 의 fpIn 이
            #   둘 다 from 을 써서 배포가 막혔습니다.
            #   ★ 2026-10-01 — `0%,100%` 처럼 **쉼표로 묶인 것**도
            #     자리 표시입니다. 전에는 쉼표가 있으면 안 걸러져
            #     home.css 의 gbFloat 와 site.css 의 pbnPulse 가
            #     부딪힌 것으로 잡혀 배포가 막혔습니다.
            def _자리표시(한조각):
                한조각 = 한조각.strip()
                return (한조각 in ('from', 'to')
                        or (한조각.endswith('%')
                            and 한조각[:-1].replace('.', '', 1).isdigit()))

            if 고르개 and all(_자리표시(조각)
                              for 조각 in 고르개.split(',')):
                continue
            속성 = {}
            for 줄 in m.group(2).split(';'):
                if ':' in 줄:
                    k, v = 줄.split(':', 1)
                    속성[k.strip()] = v.strip()
            if 속성:
                규칙[고르개][이름] = 속성

    부딪힘, 센것, 겹침 = [], [], 0
    for 고르개, 파일별 in 규칙.items():
        if len(파일별) < 2:
            continue
        겹침 += 1
        파일들 = sorted(파일별)
        같은속성 = set(파일별[파일들[0]])
        for f in 파일들[1:]:
            같은속성 &= set(파일별[f])
        if not 같은속성:
            continue
        다른값 = [k for k in 같은속성
                  if len(set(파일별[f][k] for f in 파일들)) > 1]
        if 다른값:
            부딪힘.append('%s — %s (%s)'
                          % (고르개, ' vs '.join(파일들),
                             ' · '.join(sorted(다른값)[:3])))
        else:
            센것.append('%s — %s' % (고르개, ' vs '.join(파일들)))

    if 부딪힘:
        말('막음', '같은 고르개가 여러 차림표에서 **다른 값**을 줍니다 %d건'
           % len(부딪힘), '\n'.join(부딪힘[:6]))
    elif 센것:
        말('알림', '같은 고르개·같은 속성이 여러 차림표에 %d건' % len(센것),
           '\n'.join(센것[:5]))
    else:
        됨('겹치는 고르개 %d개 — 값이 부딪히지 않습니다' % 겹침)


# ── 6. 실제 파일인데 아무도 안 쓰는 것 ────────────────────
def 검사6_버려진것():
    print('[6] 만들어 두고 아무도 안 쓰는 것이 있는가')
    버려진것 = []
    for 칸, 꼬리 in ((os.path.join(ASSETS, 'css'), '.css'),
                     (os.path.join(ASSETS, 'js'), '.js'),
                     (os.path.join(ROOT, 'template'), '.html')):
        if not os.path.isdir(칸):
            continue
        for 이름 in sorted(os.listdir(칸)):
            if not 이름.endswith(꼬리) or 이름.startswith('_'):
                continue
            쓰나 = False
            # ★ **시험은 빼고 봅니다** (2026-09-28)
            #   시험이 「아무도 안 쓰는 파일」을 일부러 만들어 보는데,
            #   그 이름이 시험 코드에 적혀 있으면 검사기가
            #   「누가 쓰고 있다」고 봅니다.
            #   **시험이 검사를 무력하게 만듭니다.**
            #   진짜로 쓰는 것은 engine/ 과 틀입니다.
            for _상대, s in 소스들(밖=('tests/',)):
                if 이름 in s:
                    쓰나 = True
                    break
            if not 쓰나:
                # 틀끼리 부르는 경우도 봅니다
                for p in glob.glob(os.path.join(ROOT, 'template', '*.html')):
                    if 이름 in io.read(p, default=''):
                        쓰나 = True
                        break
            if not 쓰나:
                버려진것.append(os.path.relpath(os.path.join(칸, 이름), ROOT))
    if 버려진것:
        말('알림', '아무도 안 쓰는 파일 %d개 — 지우거나 쓰세요'
           % len(버려진것), ' · '.join(버려진것))
    else:
        됨('만들어 두고 안 쓰는 차림표·스크립트·틀이 없습니다')



def 검사7_워크플로가정말도는가():
    """★ 클라우드 판정이 **한 번도 돈 적이 없었습니다** (2026-09-28)

    여섯 번을 올려 여섯 번 다 「Failure」 였습니다. 저는 그것을
    판정 결과로 여겼습니다. 아니었습니다 —

        The identifier '판정' is invalid.
        IDs may only contain alphanumeric characters, '_', and '-'.

    깃허브는 워크플로 파일을 **아예 안 읽었습니다.** 판정은
    시작조차 못 했는데, 목록에 빨간 줄이 서 있으니 돌고 있는 줄
    알았습니다. **안 도는 판정은 없는 판정입니다.**

    더 뼈아픈 것은, 바로 그 파일 49줄에 같은 교훈이 이미 적혀
    있었다는 것입니다(`id: 크롬` 사고). 글은 적어 두었는데
    **기계가 보지 않으니 옆줄에서 같은 잘못을 또 했습니다.**

    이것도 「같은 사실이 두 곳에」입니다 — 판정이 이 컴퓨터와
    클라우드 두 곳에 있는데, 한쪽이 죽은 것을 아무도 몰랐습니다.
    """
    print('[7] 워크플로가 깃허브에서 정말 읽히는가')
    뿌리 = os.path.join(ROOT, '.github', 'workflows')
    if not os.path.isdir(뿌리):
        됨('워크플로가 없습니다 — 클라우드에서 안 돌립니다')
        return

    한글 = re.compile(r'[가-힣]')
    # 식별자가 되는 자리만 봅니다.
    #   ① jobs: 밑의 일 이름      (들여쓰기 2칸 + 이름 + 콜론)
    #   ② id: · needs: 의 값
    #   ③ 식 안의 steps.○○ · inputs.○○ · jobs.○○ · needs.○○
    일이름 = re.compile(r'^  ([^\s:#]+):\s*$')
    # ★ run: 안의 **셸 변수**도 봅니다 (2026-09-28)
    #   진단 워크플로를 처음 돌렸을 때 이렇게 죽었습니다.
    #       볼것="..."  →  line 15: 볼것=  (명령을 못 찾습니다)
    #   리눅스 셸도 한글 이름을 못 씁니다. 식별자 이야기와
    #   같은 뿌리인데, 자리가 달라 안 잡히고 있었습니다.
    셸변수 = re.compile(r'^\s*([^\s=#|&;()]+)=[^=]')
    열쇠값 = re.compile(r'(?<![A-Za-z0-9_.])(?:id|needs)\s*:\s*([^\s#]+)')
    식이름 = re.compile(r'(?<![A-Za-z0-9_.])(?:steps|jobs|inputs|needs)\.([^\s.)}\]]+)')

    나쁜것 = []
    센것 = 0
    일칸 = False
    for 이름 in sorted(os.listdir(뿌리)):
        if not 이름.endswith(('.yml', '.yaml')):
            continue
        센것 += 1
        글 = io.read(os.path.join(뿌리, 이름), default='')
        일칸 = False
        for 번호, 줄 in enumerate(글.split('\n'), 1):
            벗긴 = 줄.split('#', 1)[0]          # 주석은 봐줍니다
            if not 벗긴.strip():
                continue
            if 벗긴.startswith('jobs:'):
                일칸 = True
            elif 벗긴[:1] not in (' ', '\t'):
                일칸 = False

            값들 = []
            if 일칸:
                m = 일이름.match(벗긴.rstrip())
                if m:
                    값들.append(m.group(1))
            값들 += 열쇠값.findall(벗긴)
            값들 += 식이름.findall(벗긴)
            m = 셸변수.match(벗긴)
            if m:
                값들.append(m.group(1))
            for 값 in 값들:
                if 한글.search(값):
                    나쁜것.append('%s:%d  %s'
                                  % (이름, 번호, 줄.strip()[:60]))
                    break

    if 나쁜것:
        말('막음', '워크플로에 한글 식별자가 있습니다 %d곳' % len(나쁜것),
           '\n'.join('      %s' % x for x in 나쁜것[:6]))
        print('      → id·needs·jobs 이름이면 깃허브가 **파일을 아예 안 읽습니다.**')
        print('        run: 안의 셸 변수면 **그 줄에서 죽습니다.**')
        print('        어느 쪽이든 판정이 도는 줄 알지만 안 돕니다.')
        print('        name: 과 주석은 한글로 두고, 이름만 영어로 적습니다.')
    else:
        됨('워크플로 %d개에 한글 식별자가 없습니다' % 센것)



def 검사8_없음을빈것으로바꿔읽나():
    """★ **누락을 숨길 수 있는 코드**를 찾습니다 (2026-09-28 바깥 검수 9차)

    검사기가 이렇게 읽고 있었습니다.

        사이트맵 = io.꼭읽기(os.path.join(NEW, 'sitemap.xml'))

    그러면 이 둘이 똑같아집니다.

        파일이 아예 없음      → ''
        파일은 있으나 0바이트  → ''

    실제로 sitemap.xml 이 통째로 없었는데 `<loc>` 이 하나도 없으니
    「사이트맵이 가리키는 쪽이 모두 있습니다」로 넘어갔습니다.
    **없는 것을 「다 맞다」고 세는 검사**였습니다.

    바깥 검수의 말: 「파일 누락 검사가 아니라 **누락을 숨길 수 있는
    코드 검사**까지 가야 합니다.」

    ★ 다만 `default=''` 가 다 나쁜 것은 아닙니다.
      「없어도 되는 것」을 읽을 때는 옳은 씀씀이입니다.
      그래서 **꼭 있어야 하는 것**을 읽는 자리만 봅니다 —
      그 줄에 필수 파일 이름이 보이는가.
    """
    print('[8] 「없음」을 「빈 것」으로 바꿔 읽는 자리가 있는가')

    # 반드시 있어야 하는 것들. 없으면 배포가 깨집니다.
    꼭있어야하는것 = (
        'sitemap.xml', 'robots.txt', 'llms.txt', 'build.json',
        'keep.json', 'url-map.json', 'refresh-plan.json',
        'site.css', 'tide.js', 'index.html',
    )
    숨기는법 = (
        "default=''", 'default=""', "default=[]", "default={}",
        "or ''", 'or ""',
    )

    나쁜것 = []
    for 상대, 글 in 소스들(밖=('tests/',)):
        for 번호, 줄 in enumerate(글.split('\n'), 1):
            벗긴 = 줄.split('#', 1)[0]
            # ★ **정말 읽는 줄만** 봅니다 (2026-09-28)
            #   처음에는 그 줄에 글자가 보이기만 하면 잡았습니다.
            #   그랬더니 **제가 쓴 설명 글**까지 잡았습니다 —
            #       ★ keep.json 을 `default={}` 로 읽던 자리를…
            #   글자로 판정하면 늘 어딘가 샙니다. 오늘 네 번째입니다.
            if not ('io.read(' in 벗긴 or 'io.read_json(' in 벗긴):
                continue
            if not any(x in 벗긴 for x in 숨기는법):
                continue
            if not any(x in 벗긴 for x in 꼭있어야하는것):
                continue
            # ★ 옛 저장소는 **없을 수 있습니다.**
            #   없으면 INFRA_FAIL 로 가야지, 「빈 것으로 읽는다」고
            #   나무랄 일이 아닙니다.
            if 'OLD' in 벗긴:
                continue
            나쁜것.append('%s:%d  %s' % (상대, 번호, 줄.strip()[:64]))

    if 나쁜것:
        말('막음', '없어서는 안 될 파일을 빈 것으로 바꿔 읽습니다 %d곳'
           % len(나쁜것),
           '\n'.join('      %s' % x for x in 나쁜것[:6]))
        print('      → 없는 것과 빈 것이 같아집니다.')
        print('        io.파일상태() 나 io.꼭있어야함() 으로 읽으세요 —')
        print('        MISSING · EMPTY · INVALID · VALID 를 가려 줍니다.')
    else:
        됨('꼭 있어야 하는 파일을 빈 것으로 바꿔 읽는 자리가 없습니다')



def 검사9_크롬을따로부르지않나():
    """★ **크롬 깃발은 한 곳에서만 정합니다** (2026-09-28)

    겪은 일 — 클라우드 판정이 416쪽을 **한 쪽도 못 쟀습니다.**

      크롬을 부르는 자리가 열한 군데였는데 `--no-sandbox` 를
      주는 곳은 한 곳뿐이었습니다. 내 컴퓨터(윈도)에서는 아무
      탈이 없었습니다. 깃허브 러너는 루트로 돌기 때문에 그
      깃발이 없으면 크롬이 시작조차 안 합니다.

      판정표에는 INFRA_FAIL 2 · FAIL 1 · NOT_TESTED 2 로 찍혔고,
      메시지는 「크롬이 도는 자리에서 다시 재세요」였습니다.
      크롬은 있었습니다. **깃발 하나가 없었습니다.**

    그래서 machine.크롬앞머리() 를 거치지 않고 크롬을 부르는
    자리가 있으면 여기서 막습니다.
    """
    print('[9] 크롬을 따로 부르는 자리가 있는가')

    # ★ **글자로 찾으면 설명글까지 잡습니다** (2026-09-28 · 바로 고침)
    #
    #   처음에는 줄에 `--headless` 가 있는지만 봤습니다. 그랬더니
    #   크롬을 죽이는 도구(clean_chrome.py)의 **설명글**과
    #   이 검사 자신의 코드까지 걸렸습니다. 오늘만 세 번째입니다.
    #
    #   그래서 코드를 읽습니다. subprocess 를 부르면서 그 인자
    #   목록에 크롬 깃발이 박혀 있는 자리만 봅니다. 설명글은
    #   코드가 아니므로 저절로 빠집니다.
    따로 = []
    곳 = os.path.join(ROOT, 'engine')
    for 뿌, 칸들, 파일들 in os.walk(곳):
        칸들[:] = [c for c in 칸들 if c != '__pycache__']
        for f in sorted(파일들):
            if not f.endswith('.py') or f == 'machine.py':
                continue
            글 = io.read(os.path.join(뿌, f), default='')
            try:
                나무 = ast.parse(글)
            except SyntaxError:
                continue
            for 마디 in ast.walk(나무):
                if not isinstance(마디, ast.Call):
                    continue
                for 인자 in 마디.args:
                    if not isinstance(인자, ast.List):
                        continue
                    깃발들 = [x.value for x in 인자.elts
                              if isinstance(x, ast.Constant)
                              and isinstance(x.value, str)]
                    if any(x.startswith('--headless') for x in 깃발들):
                        따로.append('%s:%d' % (f, 인자.lineno))
    if 따로:
        막음.append('크롬을 따로 부르는 자리 %d곳' % len(따로))
        print('  ✗ machine.크롬앞머리() 를 안 거치는 곳 %d' % len(따로))
        for x in 따로[:6]:
            print('      %s' % x)
        print('      → 깃발 하나가 빠지면 그 자리만 조용히 못 잽니다.')
    else:
        print('  · 모두 machine.크롬앞머리() 를 거칩니다')
    print('')


def 검사10_일꾼한도가검사기보다넉넉한가():
    """★ **일꾼이 검사기보다 먼저 죽으면 안 됩니다** (2026-09-28)

    gate.yml 의 timeout-minutes 가 60 인데 gate.py 는 검사기
    하나에 7200초(120분)를 주고 있었습니다. 앞뒤가 안 맞습니다.

      · 검사기가 120분까지 버텨도 일꾼이 60분에 죽습니다
      · 그때는 **판정 결과가 아예 안 남습니다**
        왜 죽었는지도, 어디까지 쟀는지도 모릅니다

    크롬 깃발을 고치자 416쪽을 진짜로 재기 시작했고, 5분이던
    판정이 40분을 넘겼습니다. **제대로 재면 오래 걸리는 것이
    맞습니다.** 그러니 한도를 재는 시간에 맞춰야지, 반대로
    재는 것을 한도에 맞출 수는 없습니다.
    """
    print('[10] 일꾼 한도가 검사기 한도보다 넉넉한가')
    일길 = os.path.join(ROOT, '.github', 'workflows', 'gate.yml')
    일글 = io.read(일길, default='')
    m = re.search(r'timeout-minutes:\s*(\d+)', 일글)
    if not m:
        알림.append('gate.yml 에 timeout-minutes 가 없습니다')
        print('  ~ gate.yml 에 한도가 안 적혀 있습니다')
        print('')
        return
    일꾼분 = int(m.group(1))
    검글 = io.read(os.path.join(ROOT, 'engine', 'gate.py'), default='')
    초들 = [int(x) for x in re.findall(r'시간=(\d+)', 검글)]
    가장긴 = max(초들) if 초들 else 0
    가장긴분 = (가장긴 + 59) // 60
    print('  일꾼 %d분 · 가장 오래 기다리는 검사기 %d분'
          % (일꾼분, 가장긴분))
    if 가장긴분 >= 일꾼분:
        막음.append('일꾼 한도(%d분)가 검사기 한도(%d분)보다 짧습니다'
                    % (일꾼분, 가장긴분))
        print('  ✗ 일꾼이 먼저 죽습니다 — 판정 결과가 아예 안 남습니다')
        print('      gate.yml 의 timeout-minutes 를 늘리세요.')
    else:
        print('  · 일꾼이 검사기보다 %d분 더 버팁니다'
              % (일꾼분 - 가장긴분))
    print('')



def 검사11_재는자리가내컴퓨터와같은가():
    """★ **적어 놓은 것과 하는 것이 달랐습니다** (2026-09-28)

    gate.yml 에 이렇게 적혀 있었습니다.

        「OS · 브라우저 · 판 · 뷰포트 · DPR · 글꼴 · 로케일 ·
          시간대를 CI 에서 고정하십시오」

    시간대(TZ)와 로케일(LANG)은 정말 고정했습니다.
    **글꼴은 적어 놓기만 하고 안 깔았습니다.**

    우분투 러너에는 한글 글꼴이 없습니다. 크롬이 한글을 대체
    글꼴로 그리면 글자 너비가 달라지고, 줄바꿈과 누름자리
    크기가 내 컴퓨터와 어긋납니다.

    그래서 4번(416쪽 렌더링)이 내 컴퓨터에서는 「탈 없음」인데
    클라우드에서는 「손볼 곳 4건」이었습니다.
    **쪽이 잘못된 것이 아니라 재는 자리가 달랐던 것**입니다.

    거짓 판정은 판정이 없는 것보다 나쁩니다.
    """
    print('[11] 클라우드가 재는 자리가 내 컴퓨터와 같은가')

    # ★ **크롬을 쓰는 일꾼은 모두 봐야 합니다** (2026-09-28 · 바로 고침)
    #   처음에는 gate.yml 만 봤습니다. 그런데 deploy.yml 도
    #   크롬을 쓰면서 글꼴을 안 깔고 있었습니다. 운영 배포 때
    #   같은 일이 납니다. **한 곳만 보면 나머지를 놓칩니다.**
    볼것 = (
        ('시간대', 'TZ:', '물때는 시간대가 다르면 하루가 밀립니다'),
        ('로케일', 'LANG:', '글자 정렬·숫자 꼴이 달라집니다'),
        ('한글 글꼴', 'fonts-noto-cjk',
         '한글 글꼴이 없으면 글자 너비가 달라져 넘침이 어긋납니다'),
    )
    칸 = os.path.join(ROOT, '.github', 'workflows')
    빠진것 = []
    본일꾼 = 0
    for f in sorted(os.listdir(칸) if os.path.isdir(칸) else []):
        if not f.endswith(('.yml', '.yaml')):
            continue
        글 = io.read(os.path.join(칸, f), default='')
        if 'setup-chrome' not in 글:
            continue      # 크롬을 안 쓰면 글꼴도 안 씁니다
        본일꾼 += 1
        모자란것 = [(이름, 왜) for 이름, 표, 왜 in 볼것 if 표 not in 글]
        if 모자란것:
            for 이름, 왜 in 모자란것:
                빠진것.append('%s — %s 를 안 고정합니다 (%s)'
                              % (f, 이름, 왜))
        else:
            print('  · %-14s 시간대·로케일·한글 글꼴 모두 고정합니다' % f)
    if not 본일꾼:
        print('  - 크롬을 쓰는 일꾼이 없습니다 — 잴 것이 없습니다')
    if 빠진것:
        막음.append('재는 자리가 안 고정된 일꾼 %d가지' % len(빠진것))
        for x in 빠진것:
            print('  ✗ %s' % x)
        print('      → 내 컴퓨터와 클라우드가 다른 답을 냅니다.')
        print('        거짓 판정은 판정이 없는 것보다 나쁩니다.')
    print('')



def 검사12_옛쪽표본이저장소에있나():
    """★ **옛 쪽을 저장소 안에 둡니다** (2026-09-28)

    클라우드에는 옛 사이트가 없습니다. 그래서 검사기 셋이
    「볼 것이 0개 = 걸린 것도 0개」로 조용히 통과했습니다.
    못 잰 것을 통과로 세지 않게 고치자, 이번에는 클라우드에서
    영영 GO 가 안 나오게 됐습니다.

    그래서 engine/make_oldsite.py 로 옛 쪽(html·css·js)을
    떠서 oldsite/ 에 둡니다. 23MB 남짓입니다.
    시험의 **고정된 표본**이 되어 앞으로도 항상 같게 잽니다.

    여기서는 세 가지를 봅니다.
      · 표본이 있는가 (없으면 클라우드에서 못 잽니다)
      · 쪽이 넉넉히 있는가 (빈 껍데기면 없는 것과 같습니다)
      · **개인 휴대전화가 섞이지 않았는가** (저장소는 공개입니다)
    """
    print('[12] 옛 쪽 표본이 저장소에 있는가')
    # ★ **BADAGAJA_OLD 가 가리키는 곳을 봅니다** (2026-09-28 · 바로 고침)
    #
    #   처음에는 ROOT/oldsite 만 봤습니다. 그랬더니 뮤테이션이
    #   사본에서 이 검사를 돌릴 때 **사본에는 oldsite 가 없어**
    #   「표본이 없다」고 막았습니다.
    #   제가 만든 검사가 제 발등을 찍었습니다.
    #
    #   표본이 어디 있는지는 BADAGAJA_OLD 가 압니다.
    #   26MB 를 사본마다 뜨는 것보다 그 자리를 보는 것이 맞습니다.
    칸 = os.environ.get('BADAGAJA_OLD') or os.path.join(ROOT, 'oldsite')
    if not os.path.isdir(칸):
        막음.append('옛 쪽 표본(oldsite/)이 없습니다')
        print('  ✗ oldsite/ 가 없습니다')
        print('      → 클라우드에서 16·24번을 못 잽니다.')
        print('        python engine/make_oldsite.py 로 뜨세요.')
        print('')
        return
    쪽수, 중국어, 번호든쪽 = 0, 0, []
    무늬 = re.compile(r'(?<![0-9])01[016789](?:[-. ]\d{3,4}[-. ]\d{4}'
                      r'|\d{7,8})(?![0-9])')
    for 뿌, 칸들, 파일들 in os.walk(칸):
        for f in 파일들:
            # ★ **html 밖도 봅니다** (2026-09-28 · 바로 고침)
            #   처음에는 html 만 봤습니다. 그랬더니 data/*.json 의
            #   35곳을 놓쳤습니다. 어느 꼴로 적혔든 같습니다.
            if not f.endswith(('.html', '.json', '.js',
                               '.css', '.xml', '.txt')):
                continue
            if f.endswith('.html'):
                쪽수 += 1
            상대 = os.path.relpath(os.path.join(뿌, f), 칸)
            상대 = 상대.replace(os.sep, '/')
            if 상대.startswith('zh-cn/') and f.endswith('.html'):
                중국어 += 1
            if 무늬.search(io.read(os.path.join(뿌, f), default='')):
                번호든쪽.append(상대)
    print('  쪽 %d장 (그중 중국어 %d장)' % (쪽수, 중국어))
    # ★ 몇 장이면 넉넉한가 — 중국어판이 190쪽 남짓입니다.
    #   절반도 안 되면 표본이 상한 것입니다.
    if 쪽수 < 300 or 중국어 < 100:
        막음.append('옛 쪽 표본이 너무 적습니다 (쪽 %d · 중국어 %d)'
                    % (쪽수, 중국어))
        print('  ✗ 표본이 너무 적습니다 — 다시 뜨세요')
    if 번호든쪽:
        막음.append('옛 쪽 표본에 개인 휴대전화가 있습니다 %d쪽'
                    % len(번호든쪽))
        print('  ✗ 개인 휴대전화가 든 쪽 %d개' % len(번호든쪽))
        for x in 번호든쪽[:4]:
            print('      %s' % x)
        print('      → 저장소는 공개이고 **기록은 지워도 남습니다.**')
        print('        make_oldsite.py 가 가리게 돼 있습니다.')
    elif 쪽수 >= 300:
        print('  · 개인 휴대전화가 섞이지 않았습니다')
    print('')



def 검사13_배포가검사를건너뛰지않나():
    """★ **눈감는 옵션이 배포에 새어 들면 안 됩니다** (2026-09-28)

    되돌리기 연습에서 smoke.py 가 「내가 만든 것과 서버가 같은가」를
    물어 어김이 났습니다. 연습은 **옛 판**으로 되돌려 놓고 보는
    것이라 다른 게 당연했습니다. 그래서 --판지문묻지않기 를
    만들었습니다.

    그런데 이런 옵션은 **배포 때 쓰이면 눈을 감는 것**입니다.
    「방금 올린 것이 내가 만든 그것인가」는 배포에서 가장
    중요한 물음입니다. 그것을 건너뛰면 엉뚱한 판이 올라가도
    모릅니다.

    그래서 연습 말고 다른 일꾼이 이 옵션을 쓰면 막습니다.
    """
    print('[13] 눈감는 옵션이 배포에 새어 들지 않았나')
    눈감는것 = ('--판지문묻지않기',)
    봐줄일꾼 = ('rollback-drill.yml',)
    칸 = os.path.join(ROOT, '.github', 'workflows')
    샌것 = []
    for f in sorted(os.listdir(칸) if os.path.isdir(칸) else []):
        if not f.endswith(('.yml', '.yaml')) or f in 봐줄일꾼:
            continue
        글 = io.read(os.path.join(칸, f), default='')
        for 옵 in 눈감는것:
            if 옵 in 글:
                샌것.append('%s 가 %s 를 씁니다' % (f, 옵))
    if 샌것:
        막음.append('눈감는 옵션이 배포 일꾼에 있습니다 %d곳' % len(샌것))
        for x in 샌것:
            print('  ✗ %s' % x)
        print('      → 배포에서 그것을 건너뛰면 엉뚱한 판이 올라가도')
        print('        모릅니다. 연습에서만 씁니다.')
    else:
        print('  · 눈감는 옵션은 되돌리기 연습에서만 씁니다')
    print('')



def 검사14_크롬소켓길이가넉넉한가():
    """★ **크롬 소켓 경로는 108바이트를 못 넘습니다** (2026-09-29)

    판정 #24 에서 크롬이 죽었습니다.

        process_singleton_posix.cc:313] Socket path too long

    크롬은 TMPDIR 밑에 `.org.chromium.Chromium.XXXXXX/SingletonSocket`
    을 만듭니다. 유닉스 소켓 경로는 **108바이트**가 한계입니다.

    그런데 `engine/tmp.py` 가 TMPDIR 을 작업 폴더 옆(`.tmp`)으로
    옮기고 있었습니다. 윈도에서 C: 가 꽉 차던 것을 막으려
    만든 것인데, 리눅스에서는 경로를 이렇게 길게 만듭니다.

        /home/runner/work/badagaja-engine/badagaja-engine/
          .tmp/mutation-xxxxxxxx/.tmp/        ← 사본 안에 또 .tmp
          .org.chromium.Chromium.XXXXXX/SingletonSocket
        = 124바이트 → 넘칩니다

    **막으려던 것은 막았는데 다른 까닭으로 또 죽었습니다.**
    고친 뒤 다음 판정을 본 덕에 알았습니다.

    여기서는 두 가지를 봅니다.
      · 리눅스에서 tmp 가 임시 자리를 건드리지 않는가
      · 지금 재는 자리로 크롬 소켓을 만들면 108 안쪽인가
    """
    print('[14] 크롬 소켓 경로가 108바이트 안쪽인가')
    try:
        from engine import tmp as _t
    except Exception as e:
        막음.append('tmp 를 못 읽었습니다')
        print('  ✗ engine/tmp.py 를 못 읽었습니다: %s' % str(e)[:60])
        print('')
        return

    # ── ① 리눅스인 척하고 맞춤() 을 불러 봅니다
    원래 = _t.윈도인가
    원래환경 = os.environ.get('BADAGAJA_TMP')
    try:
        _t.윈도인가 = False
        os.environ.pop('BADAGAJA_TMP', None)
        난것 = _t.맞춤()
    finally:
        _t.윈도인가 = 원래
        if 원래환경 is not None:
            os.environ['BADAGAJA_TMP'] = 원래환경
        _t.맞춤()          # 이 판의 자리를 되돌립니다

    if 난것 is not None:
        막음.append('리눅스에서 임시 자리를 옮깁니다 — 크롬이 죽습니다')
        print('  ✗ 리눅스에서도 임시 자리를 옮깁니다: %s' % 난것)
        print('      → 크롬 소켓 경로가 108바이트를 넘어 죽습니다.')
        print('        tmp.맞춤() 은 리눅스에서 None 을 내야 합니다.')
    else:
        print('  · 리눅스에서는 임시 자리를 건드리지 않습니다')

    # ── ② 지금 자리로 소켓을 만들면 몇 바이트인가
    #      크롬이 덧붙이는 것: /.org.chromium.Chromium.XXXXXX/SingletonSocket
    덧붙는것 = len('/.org.chromium.Chromium.XXXXXX/SingletonSocket')
    # 리눅스에서만 걸리는 한계입니다. 윈도에서 돌 때는
    # **클라우드였다면** 어땠을지를 셈해 봅니다.
    if sys.platform.startswith('win'):
        바탕 = '/tmp'
    else:
        바탕 = tempfile.gettempdir()
    # 검사기는 사본 안에서 돕니다 — 한 겹 더 깊어질 수 있습니다
    사본몫 = len('/mutation-xxxxxxxx')
    잰길이 = len(바탕.encode('utf-8')) + 사본몫 + 덧붙는것
    if 잰길이 >= 108:
        막음.append('크롬 소켓 경로가 %d바이트 — 108 을 넘습니다' % 잰길이)
        print('  ✗ %s 를 바탕으로 하면 %d바이트입니다' % (바탕, 잰길이))
        print('      → 크롬이 뜨다 죽습니다. 바탕을 짧게 잡습니다.')
    else:
        print('  · %s 바탕으로 넉넉히 %d바이트 (한계 108)' % (바탕, 잰길이))
    print('')


def 검사15_로케일을적어만두지않았나():
    """★ **적어 두는 것과 깔려 있는 것은 다릅니다** (2026-09-29)

    운영 배포가 여기서 막혔습니다.

        LC_ALL: ko_KR.UTF-8        ← 일꾼에 적어 둠
        setlocale: cannot change locale (ko_KR.UTF-8)   ← 없음

    그러자 lftp 가 서버의 **한글 이름**을 물음표로 바꿔
    못 찾았습니다.

        550 ?????????: No such file or directory

    되돌릴 것을 못 받아 배포가 멈췄습니다.
    **글꼴 때도 똑같이 「고정한다」고 적고 안 깔았습니다.**
    같은 병이 두 번째입니다.

    그리고 FTP 로 한글 이름을 다루려면 lftp 에 글자 인코딩을
    못 박아야 합니다.
    """
    print('[15] 로케일을 적어만 두고 안 깔지 않았나')
    칸 = os.path.join(ROOT, '.github', 'workflows')
    탈 = []
    for f in sorted(os.listdir(칸) if os.path.isdir(칸) else []):
        if not f.endswith(('.yml', '.yaml')):
            continue
        글 = io.read(os.path.join(칸, f), default='')
        적었나 = 'ko_KR.UTF-8' in 글
        깔았나 = 'locale-gen' in 글
        if 적었나 and not 깔았나:
            탈.append('%s — ko_KR.UTF-8 을 쓰는데 locale-gen 이 없습니다' % f)
        # FTP 를 쓰면 글자 인코딩을 못 박아야 합니다
        if 'lftp' in 글 and 'ftp:charset' not in 글:
            탈.append('%s — lftp 를 쓰는데 ftp:charset 이 없습니다' % f)
    if 탈:
        막음.append('로케일·인코딩을 적어만 둔 일꾼 %d곳' % len(탈))
        print('  ✗ %d곳' % len(탈))
        for x in 탈:
            print('      %s' % x)
        print('      → 한글 이름 파일을 못 읽어 배포가 멈춥니다.')
    else:
        print('  · 로케일을 쓰는 일꾼은 모두 실제로 깔고,')
        print('    FTP 를 쓰는 일꾼은 모두 글자 인코딩을 못 박습니다')
    print('')


def 검사16_남의상표를쓰지않았나():
    '''★ **남의 로고를 쓰면 안 됩니다** (2026-09-29 주인 지시)

    머리 로고가 네이버의 N 자 모양을 그대로 쓰고 있었습니다.
    검색창 생김새를 참고한 것까지는 좋으나, 남의 글자는 안 됩니다.

    쪽을 손으로 고치면 다시 만들 때 되돌아옵니다. 그래서
    생성기·모양새·틀을 모두 봅니다. 왜 바꿨는지 적은
    주석 줄은 빼고 셉니다.
    '''
    print('[16] 남의 상표를 쓰고 있지 않은가')
    from engine import _trademark
    걸린것, 본수 = _trademark.찾기(ROOT, io.read)
    if 걸린것:
        막음.append('남의 상표를 쓰는 곳 %d곳' % len(걸린것))
        print('  x %d곳' % len(걸린것))
        for 길, 줄, 이름 in 걸린것[:6]:
            print('      %s:%d - %s' % (길, 줄, 이름))
        print('      -> 생김새는 참고해도 남의 글자·로고는 못 씁니다.')
    else:
        print('  · 남의 상표를 쓰는 곳이 없습니다 (%d 파일을 봤습니다)'
              % 본수)
    print('')

def 검사17_줄바꿈이깨지지않았나():
    """캐리지리턴이 둘 붙지 않았는가 (2026-10-01).

    ★ 겪은 일 — `site.css` 에서 **2,147곳**이 깨져 있었습니다.
      파이썬으로 고칠 때 `newline=''` 로 읽고 새 글은 한 글자
      줄바꿈으로 쓰면, CRLF 파일에서 둘이 겹칩니다.

      차림표는 그래도 돌아가 눈에 안 띄지만, **찾기·바꾸기가
      조용히 실패**합니다. 같은 고치기를 네 번 되풀이했습니다.

    ★ **손으로 고치는 폴더만** 봅니다
      `data/` 까지 읽으면 검사가 10분을 넘깁니다.
      검사는 빨라야 자주 돕니다. 깨진 줄바꿈은 내가 고칠 때
      생기는 것이지 자료가 스스로 깨지지는 않습니다.
    """
    print('[17] 줄바꿈이 깨지지 않았나')
    깨진것 = (chr(13) + chr(13) + chr(10)).encode()
    볼것 = ('.css', '.js', '.py', '.html', '.md', '.yml')
    볼폴더 = ('engine', 'assets', 'template', 'docs', 'tests',
              '.github')
    길들 = []
    for 이름 in os.listdir(ROOT):
        한길 = os.path.join(ROOT, 이름)
        if os.path.isfile(한길) and 이름.endswith(볼것):
            길들.append(한길)
    for 폴더 in 볼폴더:
        자리 = os.path.join(ROOT, 폴더)
        if not os.path.isdir(자리):
            continue
        for 뿌리, 폴더들, 파일들 in os.walk(자리):
            폴더들[:] = [x for x in 폴더들 if x != '__pycache__']
            for 이름 in 파일들:
                if 이름.endswith(볼것):
                    길들.append(os.path.join(뿌리, 이름))
    나쁜것 = []
    for 한길 in 길들:
        try:
            바이트 = open(한길, 'rb').read()
        except OSError:
            continue
        n = 바이트.count(깨진것)
        if n:
            나쁜것.append((os.path.relpath(한길, ROOT), n))
    if 나쁜것:
        나쁜것.sort(key=lambda x: -x[1])
        말('막음', '줄바꿈이 깨진 파일이 있습니다 %d개' % len(나쁜것),
          chr(10).join('      %s — %d곳' % (a, b)
                       for a, b in 나쁜것[:6]))
    else:
        됨('줄바꿈이 깨진 파일이 없습니다 (파일 %d개를 봤습니다)'
          % len(길들))


def main():
    global 자세히
    자세히 = '--자세히' in sys.argv
    print('같은 사실을 두 곳에서 관리하고 있지 않은가 (바깥 검수 7차)')
    print('  ★ 「코드가 예쁜가」가 아닙니다.')
    print('    하루에 일곱 번 난 사고가 전부 이 뿌리였습니다.')
    print('')

    검사1_파일목록()
    print('')
    검사2_모은판단()
    print('')
    검사3_상태목록()
    print('')
    검사4_검사기등록()
    print('')
    검사5_차림표겹침()
    print('')
    검사6_버려진것()
    print('')
    검사7_워크플로가정말도는가()
    print('')
    검사8_없음을빈것으로바꿔읽나()
    검사9_크롬을따로부르지않나()
    검사10_일꾼한도가검사기보다넉넉한가()
    검사11_재는자리가내컴퓨터와같은가()
    검사12_옛쪽표본이저장소에있나()
    검사13_배포가검사를건너뛰지않나()
    검사14_크롬소켓길이가넉넉한가()
    검사15_로케일을적어만두지않았나()
    검사16_남의상표를쓰지않았나()
    검사17_줄바꿈이깨지지않았나()
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  **같은 사실이 두 곳에 있으면 언젠가 반드시 어긋납니다.**')
        return 1
    print('같은 사실을 두 곳에서 관리하는 곳이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
