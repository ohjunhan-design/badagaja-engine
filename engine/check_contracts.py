# -*- coding: utf-8 -*-
"""계약을 지키고 있는지 **기계가** 봅니다.  (docs/CONTRACTS.md)

왜
    계약은 여러 AI의 의견을 모아 정한 이 틀의 뼈대입니다.
    그런데 글로만 적어 두면 지켜지는지 아무도 모릅니다.
    옛 사이트가 꼭 그랬습니다 — 규칙은 있었는데 검사가 없었습니다.

    「새 검사는 잡은 뒤에 만듭니다」(주인 규칙 26)의 한 걸음 앞으로,
    **정해 둔 규칙을 늘 스스로 재게** 합니다.

무엇을 하나
    계약마다 「어떻게 확인하는가」를 코드로 적었습니다.
    기계가 못 재는 것은 그렇다고 솔직히 적어 둡니다 — 숨기지 않습니다.

쓰는 법
    python engine/check_contracts.py
    python engine/check_contracts.py --strict    안 지키면 1 로 끝냅니다
"""
import os
import re
import sys
import glob
import json
import shutil
import tempfile
import subprocess
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, template   # noqa: E402
from engine.data import 자료       # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

결과 = []

# 검사 등급 (계약-21)
#   막음 — 계약을 어긴 것. 고쳐야 합니다
#   알림 — 아직 안 한 것·기계가 못 재는 것. 막지 않습니다
막음, 알림 = [], []


# ── 계약의 상태는 넷 중 하나입니다 (2026-09-26 바깥 검수 요구) ────
#
#   지킴    실제로 재 봤고 지켰습니다              (PASS)
#   어김    재 봤는데 안 지켰습니다                (FAIL)
#   안잼    **아직 안 재 봤습니다**                (NOT TESTED)
#   해당없음 이번에는 잴 것이 없습니다             (N/A)
#
# ★ 「안잼」을 「지킴」으로 세지 않는 것이 핵심입니다.
#   광고 칸이 0개인데 「광고 검사 지킴」이라고 하면 거짓입니다.
#   잰 적이 없으면 없다고 말해야 합니다.
상태들 = ('지킴', '어김', '안잼', '해당없음')


def 적기(번호, 이름, 상태, 말=''):
    if 상태 not in 상태들:
        raise ValueError('모르는 상태입니다: %s (%s 중 하나여야 합니다)'
                         % (상태, ' · '.join(상태들)))
    결과.append({'번호': 번호, '이름': 이름, '상태': 상태, '말': 말})



def 빠르게():
    """빠른 진단인가. **--smoke 가 으뜸 이름**입니다 (2026-09-28).

    ★ 바깥 검수 6차 — 「fast 는 사람이 무의식적으로 『빠른 최종검사』
      라고 받아들일 가능성이 있습니다」. 맞는 말이라 이름을 바꿨습니다.
      옛 이름(--fast)도 받아 줍니다.
    """
    return '--smoke' in sys.argv or '--fast' in sys.argv


def 파이썬들(밖=()):
    for p in sorted(glob.glob(os.path.join(ROOT, '**', '*.py'), recursive=True)):
        상대 = os.path.relpath(p, ROOT).replace('\\', '/')
        if 상대.startswith(('site/', '.git/')) or '__pycache__' in 상대:
            continue
        if any(상대.startswith(x) for x in 밖):
            continue
        yield 상대, io.read(p, default='')


# ── 계약-01 · 쪽을 만드는 곳은 하나다 ──────────────────────
def 계약01():
    나쁜것 = []
    for 상대, s in 파이썬들():
        if 상대 == 'engine/build.py':
            continue
        # site/ 아래에 파일을 쓰는 코드가 build.py 밖에 있으면 안 됩니다
        if re.search(r'io\.write\w*\([^)]*나갈곳', s) or \
           re.search(r'io\.write\w*\(\s*os\.path\.join\(\s*NEW', s):
            나쁜것.append(상대)
    # 검사 결과를 tests/out/ 에 적는 것은 쪽을 만드는 일이 아닙니다.
    # site/ 를 건드리지 않으므로 계약-01 과 어긋나지 않습니다 (2026-09-27)
    # 검사 결과·표를 적는 것은 쪽을 만드는 일이 아닙니다.
    # site/ 를 건드리지 않으므로 계약-01 과 어긋나지 않습니다 (2026-09-27)
    #   gate.py       판정 결과를 tests/out/ 에
    #   url_table.py  주소 이관표를 data-private/ 에
    # ★ engine/mark_stage.py — **밝힌 예외** (2026-09-28)
    #
    #   이것은 배포 직전에 검증판 표시를 다는 후처리입니다.
    #   build.py 안에 넣을 수 없습니다 — 운영판에는 붙으면 안 되고
    #   검증판에만 붙어야 하니까요.
    #
    #   ★ 위험한 예외입니다. 표시가 남은 채 운영에 나가면
    #     416쪽이 통째로 검색에서 사라집니다. 그래서
    #     check_seo.py 가 「검증판 표시가 남아 있는가」를 **막음**으로
    #     보고 있습니다. 예외를 두되 지키는 것을 함께 둡니다.
    나쁜것 = [x for x in 나쁜것
             if x not in ('engine/gate.py', 'engine/url_table.py',
                          'engine/mark_stage.py')]
    적기('01', '쪽을 만드는 곳은 하나다',
         '어김' if 나쁜것 else '지킴',
         ' · '.join(나쁜것) if 나쁜것 else 'engine/build.py 만 site/ 에 씁니다')


# ── 계약-02 · 권역에 예외를 두지 않는다 ────────────────────
def 계약02(d):
    칸 = ('id', '묶음', '이름', '차례', '좌표', '바다')
    빠진것 = []
    for r in d.권역들:
        없는칸 = [k for k in 칸 if k not in r]
        if 없는칸:
            빠진것.append('%s(%s)' % (r['id'], ','.join(없는칸)))
    # 포인트도 같은 모양인가
    포인트칸 = ('id', '권역', '갈래', '이름', '좌표', '출입')
    나쁜포인트 = []
    for x in d.포인트들[:99999]:
        없 = [k for k in 포인트칸 if k not in x]
        if 없:
            나쁜포인트.append(x['id'])
            if len(나쁜포인트) > 3:
                break
    말 = []
    if 빠진것:
        말.append('권역 %d곳에 빠진 칸' % len(빠진것))
    if 나쁜포인트:
        말.append('포인트 %s' % ' · '.join(나쁜포인트[:3]))
    적기('02', '권역에 예외를 두지 않는다',
         '어김' if 말 else '지킴',
         ' / '.join(말) if 말 else
         '권역 %d곳·포인트 %d곳이 같은 모양입니다' % (len(d.권역들), d.셈()))


# ── 계약-03 · 주소를 만드는 곳은 하나다 ────────────────────
def 계약03():
    나쁜것 = []
    for 상대, s in 파이썬들(밖=('engine/url.py',)):
        # .html 을 손으로 이어 붙이는 코드
        for m in re.finditer(r"'[^']*%s[^']*\.html'|\"[^\"]*%s[^\"]*\.html\"", s):
            줄 = s[:m.start()].count('\n') + 1
            앞 = s[max(0, m.start() - 120):m.start()]
            if 'url.' in 앞.split('\n')[-1]:
                continue
            나쁜것.append('%s:%d' % (상대, 줄))
    # 옮기는 도구·검사기는 옛 사이트 주소를 읽어야 하므로 봐줍니다
    나쁜것 = [x for x in 나쁜것
             if not x.startswith(('engine/migrate', 'engine/extract',
                                  'engine/compare_page.py',
                                  'engine/check_calendar.py',
                                  'engine/check_contracts.py'))]
    적기('03', '주소를 만드는 곳은 하나다',
         '어김' if 나쁜것 else '지킴',
         ' · '.join(나쁜것[:3]) if 나쁜것 else 'engine/url.py 만 주소를 만듭니다')


# ── 계약-04 · 틀에 숫자를 쓰지 않는다 ──────────────────────
def 계약04():
    나쁜것 = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'template', '*.html'))):
        이름 = os.path.basename(p)
        숫자 = template.숫자검사(이름)
        if 숫자:
            나쁜것.append('%s %s' % (이름, 숫자))
    적기('04', '틀에 숫자를 쓰지 않는다',
         '어김' if 나쁜것 else '지킴',
         ' · '.join(나쁜것) if 나쁜것 else '틀 %d개에 박힌 숫자가 없습니다'
         % len(glob.glob(os.path.join(ROOT, 'template', '*.html'))))


# ── 계약-05 · 묶음 합계 = 전국 합계 ────────────────────────
def 계약05(d):
    묶음별 = d.묶음별셈()
    합 = sum(묶음별.values())
    전국 = d.셈()
    적기('05', '묶음 합계 = 전국 합계',
         '지킴' if 합 == 전국 else '어김',
         '묶음 합 %d · 전국 %d' % (합, 전국))


# ── 계약-06 · 숫자는 사람이나 AI가 세지 않는다 ─────────────
def 계약06(d):
    """쪽에 적힌 포인트 수가 자료에서 센 값과 같은가"""
    나쁜것 = []
    for r in d.권역들:
        p = os.path.join(NEW, '%s.html' % r['id'])
        if not os.path.exists(p):
            continue
        s = io.read(p)
        m = re.search(r'포인트 (\d+)곳 보기', s)
        if m and int(m.group(1)) != d.셈(r['id']):
            나쁜것.append('%s 쪽 %s / 자료 %d' % (r['id'], m.group(1), d.셈(r['id'])))
    적기('06', '숫자는 사람이나 AI가 세지 않는다',
         '어김' if 나쁜것 else '지킴',
         ' · '.join(나쁜것[:3]) if 나쁜것 else
         '권역 %d곳의 쪽 숫자가 자료와 같습니다' % len(d.권역들))


# ── 계약-07 · 두 번 만들어도 결과가 같아야 한다 ────────────
def 계약07():
    """★ 검사는 결과물을 건드리지 않습니다 (2026-09-26 주인 지적)

    처음에는 site/ 에 대고 build.py 를 다시 돌렸습니다.
    검사가 결과물을 바꾸는 셈이라, 주인이 걱정하신 그 모양이었습니다.

        「검수기가 정교해지는 것은 좋은데 후처리가 통일이 안 되는
          문제점이 발생하게 될까 봐 걱정이 되」

    그래서 **딴 자리에 새로 만들어** 지금 것과 견줍니다.
    진짜 site/ 는 한 글자도 안 바뀝니다.
    """
    지금 = {}
    for r, _, fs in os.walk(NEW):
        for f in fs:
            p = os.path.join(r, f)
            with open(p, 'rb') as fh:
                지금[os.path.relpath(p, NEW).replace(os.sep, '/')] = fh.read()

    딴자리 = tempfile.mkdtemp(prefix='contract07-')
    try:
        환경 = dict(os.environ)
        환경['BADAGAJA_SITE'] = 딴자리
        환경['PYTHONIOENCODING'] = 'utf-8'
        subprocess.run([sys.executable,
                        os.path.join(ROOT, 'engine', 'build.py')],
                       capture_output=True, timeout=1800, env=환경)
        새로 = {}
        for r, _, fs in os.walk(딴자리):
            for f in fs:
                p = os.path.join(r, f)
                with open(p, 'rb') as fh:
                    새로[os.path.relpath(p, 딴자리).replace(os.sep, '/')] = fh.read()
    finally:
        shutil.rmtree(딴자리, ignore_errors=True)

    # ★ build.json 은 build.py 가 만드는 것이 아닙니다 (2026-09-27)
    #
    #   이 검사는 **build.py 가 두 번 같은 것을 만드는가**를 봅니다.
    #   그런데 `site/build.json` 은 `engine/build_id.py` 가 나중에
    #   따로 만드는 **배포판 지문**입니다. 딴 자리에 build.py 만
    #   돌리면 그 파일이 아예 없어, 「있음 vs 없음」을 견주며
    #   **늘 어김**이 났습니다. 쪽은 한 글자도 안 다른데 말입니다.
    #
    #   그냥 빼기만 하면 숨기는 것이라, 아래에 **더 센 검사**를
    #   붙였습니다 — 지문에 적힌 해시가 실제 파일과 맞는가
    #   (`_지문이맞는가`). 쪽을 다시 만들고 지문을 안 고치면 잡힙니다.
    지문은빼기 = {'build.json'}
    다름 = [k for k in sorted(set(지금) | set(새로))
            if k not in 지문은빼기 and 지금.get(k) != 새로.get(k)]
    증거 = (' · '.join(다름[:3]) if 다름 else
            '딴 자리에 새로 만들어 견줬습니다 — 쪽 %d개 차이 0'
            % (len(지금) - len(지문은빼기 & set(지금))))

    # 지문이 지금 쪽과 맞는지 — 어긋나면 그것도 어김입니다
    지문탈 = _지문이맞는가(지금)
    if 지문탈:
        다름 = 다름 + ['build.json — ' + 지문탈]
        증거 = 'build.json — ' + 지문탈

    적기('07', '두 번 만들어도 결과가 같아야 한다',
         '어김' if 다름 else '지킴', 증거)


def _지문이맞는가(지금):
    """`site/build.json` 에 적힌 해시가 **실제 파일과 같은가.**

    ★ 왜 보나 (2026-09-27)
      쪽을 다시 만들고 `build_id.py` 를 안 돌리면, 지문이 낡은 채
      남습니다. 그 상태로 올리면 `check_deployed --net` 이
      「서버가 내가 만든 것과 다르다」고 헛것을 냅니다.
      **지문은 판을 증명하는 물건이라 낡으면 쓸모가 없습니다.**

    돌려주는 것 — 탈이 있으면 한 줄, 없으면 빈 글
    """
    import hashlib
    import json as _json
    옛 = 지금.get('build.json')
    if 옛 is None:
        return ''            # 아직 안 만들었습니다 — 여기서 따질 일이 아닙니다
    try:
        판 = _json.loads(옛.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return '읽을 수 없습니다'
    적힌것 = 판.get('파일') or {}
    실제 = dict((k, hashlib.sha256(v).hexdigest())
                for k, v in 지금.items() if k != 'build.json')
    빠짐 = sorted(set(실제) - set(적힌것))
    남음 = sorted(set(적힌것) - set(실제))
    틀림 = sorted(k for k in (set(적힌것) & set(실제))
                  if 적힌것[k] != 실제[k])
    if 빠짐 or 남음 or 틀림:
        return ('지문이 낡았습니다 — 안 적힌 것 %d · 없는데 적힌 것 %d · '
                '내용이 다른 것 %d  (python engine/build_id.py 로 다시 만드세요)'
                % (len(빠짐), len(남음), len(틀림)))
    if 판.get('쪽수') != sum(1 for k in 실제 if k.endswith('.html')):
        return '지문의 쪽수가 실제와 다릅니다'
    return ''


# ── 계약-08 · 결과물에 시각을 넣지 않는다 ──────────────────
def 계약08():
    """만든 시각(분·초)이 쪽에 들어가면 안 고쳐도 결과가 달라집니다"""
    나쁜것 = []
    for p in sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True)):
        s = io.read(p)
        # 2026-09-26 15:43 같은 시각, ?v=202609261543 같은 판 번호
        if re.search(r'\d{4}-\d\d-\d\d[ T]\d\d:\d\d', s) or \
           re.search(r'\?v=20\d{10}', s):
            나쁜것.append(os.path.relpath(p, NEW))
    적기('08', '결과물에 시각을 넣지 않는다',
         '어김' if 나쁜것 else '지킴',
         ' · '.join(나쁜것[:3]) if 나쁜것 else
         '판 번호는 파일 내용에서 만듭니다')


# ── 계약-09·10 · 후처리 ────────────────────────────────────
def 계약0910():
    """후처리(만든 뒤에 다시 손대는 것)가 있는가"""
    s = io.read(os.path.join(ROOT, 'engine', 'build.py'), default='')
    후처리 = re.findall(r'def (후처리\w*|post\w*)\(', s)
    적기('10', '후처리는 셋을 넘지 않는다',
         '어김' if len(후처리) > 3 else '지킴',
         '후처리 %d개' % len(후처리))


# ── 계약-11 · 무엇을 만들지는 자료가 정한다 ────────────────
def 계약11():
    s = io.read(os.path.join(ROOT, 'engine', 'build.py'), default='')
    m = re.search(r'def 만들목록\(.*?\n\n', s, re.S)
    몸 = m.group(0) if m else ''
    # 권역 아이디를 손으로 적어 둔 곳이 있으면 안 됩니다
    박힌것 = re.findall(r"'(taean|yeosu|sinan|jeju\w*|busan\w*)'", 몸)
    적기('11', '무엇을 만들지는 자료가 정한다',
         '어김' if 박힌것 else '지킴',
         ' · '.join(set(박힌것)) if 박힌것 else
         'd.권역들 을 돌며 스스로 정합니다')


# ── 계약-12 · 자료에 있는데 쪽이 없으면 실패 ───────────────
def 계약12(d):
    from engine import url
    없는것 = []
    for r in d.권역들:
        if not os.path.exists(os.path.join(NEW, url.region(r['id']))):
            없는것.append(r['id'])
        for 갈래 in ('낚시', '해루질'):
            if d.셈(r['id'], 갈래) and not os.path.exists(
                    os.path.join(NEW, url.point_list(r['id'], 갈래))):
                없는것.append('%s %s' % (r['id'], 갈래))
    적기('12', '자료에 있는데 쪽이 없으면 실패',
         '어김' if 없는것 else '지킴',
         ' · '.join(없는것[:3]) if 없는것 else
         '권역·포인트 쪽이 모두 있습니다 (engine/check_links.py 가 봅니다)')


# ── 계약-13 · 파일 쓰기는 io.write() 만 쓴다 ───────────────
def 계약13():
    나쁜것 = []
    for 상대, s in 파이썬들(밖=('engine/io.py', 'tests/')):
        for m in re.finditer(r"open\(([^)]*),\s*['\"][wa]", s):
            줄 = s[:m.start()].count('\n') + 1
            앞 = s[max(0, m.start() - 60):m.start()]
            if 'io.' in 앞 or 'tempfile' in 앞:
                continue
            나쁜것.append('%s:%d' % (상대, 줄))
    # ★ 소스에 **보이지 않는 제어문자**가 있는가 (2026-09-28)
    #
    #   계약-13 이 막으려는 것이 바로 이것입니다. 그런데 io.write() 는
    #   **쓸 때만** 봅니다. 이미 들어간 것은 못 봅니다.
    #
    #   실제로 겪었습니다 — 뮤테이션 시험을 스크립트로 만들면서
    #   `\\b`(단어 경계)를 쓰려다 역슬래시가 먹혀 **진짜 백스페이스
    #   문자(0x08)** 가 박혔습니다.
    #
    #       _re.sub(r'<img\x08[^>]*>', ...)
    #
    #   눈에는 `<img[^>]*>` 로 보입니다. 아무것도 안 지워지는데
    #   까닭을 알 수 없었습니다. 한 시간을 헤맸습니다.
    #
    #   그때 그 파일은 `tests/` 라 계약-13 검사에서 빠져 있었고,
    #   io.write() 도 안 지났습니다. **두 겹 다 뚫렸습니다.**
    제어문자 = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
    더러운것 = []
    for 상대, s in 파이썬들():
        m = 제어문자.search(s)
        if m:
            줄 = s[:m.start()].count('\n') + 1
            더러운것.append('%s:%d (\\x%02x)' % (상대, 줄, ord(m.group())))

    탈 = 나쁜것 + 더러운것
    if 더러운것:
        증거 = '보이지 않는 제어문자: ' + ' · '.join(더러운것[:3])
    elif 나쁜것:
        증거 = ' · '.join(나쁜것[:3])
    else:
        증거 = '직접 열어 쓰는 곳이 없고, 제어문자도 없습니다'
    적기('13', '파일 쓰기는 io.write() 만 쓴다',
         '어김' if 탈 else '지킴', 증거)


# ── 계약-14·16 · 그려서 본다 ───────────────────────────────
def 계약1416():
    있나 = os.path.exists(os.path.join(ROOT, 'engine', 'check_render.py'))
    적기('14', '배포 전에 실제로 그려서 본다',
         '지킴' if 있나 else '안잼',
         'engine/check_render.py — 크롬으로 375·1280px 에서 잽니다')
    적기('16', '고쳤다고 말하기 전에 화면에서 확인한다',
         '지킴' if 있나 else '안잼',
         '같은 도구를 씁니다. 틀 안에 넣어 폭을 정확히 줍니다')


# ── 계약-15 · 광고 칸이 배너보다 좁으면 실패 ───────────────
def 계약15():
    """★ 광고를 **실제로 그려 봅니다** (2026-09-26)

    처음에는 「광고 칸이 쪽에 있으면 지킴」으로 두었습니다.
    그런데 칸이 있어도 광고가 안 뜰 수 있습니다 — 실제로
    hidden 때문에 **한 번도 안 떴습니다.** 칸을 세는 것으로는
    못 잡습니다. check_ads.py 를 그 자리에서 돌립니다.
    """
    광고 = 0
    쪽수 = 0
    for p in glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True):
        쪽수 += 1
        광고 += io.read(p).count('ad-slot')
    if 광고 == 0:
        적기('15', '광고 칸이 배너보다 좁으면 실패', '안잼',
             '쪽 %d개에 광고 칸 0개 — 아직 안 넣었습니다' % 쪽수)
        return
    도구 = os.path.join(ROOT, 'engine', 'check_ads.py')
    if not os.path.exists(도구):
        적기('15', '광고 칸이 배너보다 좁으면 실패', '안잼',
             'engine/check_ads.py 가 없습니다')
        return
    if 빠르게():
        적기('15', '광고 칸이 배너보다 좁으면 실패', '안잼',
             '--smoke 로 건너뛰었습니다 — 이것은 「지킴」이 아닙니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구, '--strict'],
                       capture_output=True, text=True, encoding='utf-8',
                       env=환경, timeout=1800)
    글 = (r.stdout or '') + (r.stderr or '')
    괜찮나 = (r.returncode == 0
              and '광고가 뜰 때도 안 뜰 때도 쪽이 멀쩡합니다' in 글)
    적기('15', '광고 칸이 배너보다 좁으면 실패',
         '지킴' if 괜찮나 else '어김',
         ('광고를 실제로 그려 봤습니다 — 칸 %d개 · 뜰 때도 안 뜰 때도 '
          '넘침 0 (PC 1280 · 휴대폰 360·375)' % 광고) if 괜찮나 else
         ('check_ads.py 가 잡았습니다: %s'
          % (글.strip().split('\n')[-1][:60] if 글.strip() else '알 수 없음')))


# ── 계약-17·18 · 지우는 일 ─────────────────────────────────
def 계약1718():
    """★ 둘 다 **실제로 잽니다** (2026-09-27)

    전에는 계약-17 을 「기계가 재기 어렵다」고 두고, 계약-18 은
    아무 데도 안 쓰는 표시(_지우지_말_것)를 찾고 있었습니다.
    둘 다 재는 법이 있었는데 안 찾아본 것입니다.
    """
    # ── 계약-17 — 지우는 도구가 **그냥은 안 지우는가**
    #   사람이 실수로 한 번 잘못 치면 되돌릴 수 없는 일이 벌어집니다.
    #   지우는 코드가 있는 도구는 --yes 같은 다짐을 받아야 합니다.
    지우는도구 = []
    막는것 = []
    안막는것 = []
    for 상대, s in 파이썬들(밖=('tests/',)):
        if not re.search(r'shutil\.rmtree\(|os\.remove\(|os\.unlink\(', s):
            continue
        # 임시 폴더를 치우는 것은 지우는 일이 아닙니다
        진짜지움 = re.search(
            r'(shutil\.rmtree|os\.remove|os\.unlink)\((?!.*(t|임시|딴자리|'
            r'일터|tempfile|prefix))', s)
        if not 진짜지움:
            continue
        지우는도구.append(상대)
        # 다짐을 받거나, **밝힌 예외**여야 합니다.
        # 「계약-17 예외」라고 그 줄에 적어 두면 봐줍니다 —
        # 조용히 지우는 것과 밝히고 지우는 것은 다릅니다.
        다짐받음 = re.search(r"'--yes' (in|not in) sys\.argv|"
                             r"'--force' (in|not in) sys\.argv", s)
        밝힌예외 = re.search(r'(shutil\.rmtree|os\.remove|os\.unlink)'
                             r'\([^\n]*\)\s*#\s*계약-17 예외', s)
        if 다짐받음 or 밝힌예외:
            막는것.append(상대)
        else:
            안막는것.append(상대)
    적기('17', '삭제는 만드는 일보다 어려워야 한다',
         '어김' if 안막는것 else '지킴',
         ('다짐 없이 지우는 도구 %d개: %s'
          % (len(안막는것), ' · '.join(안막는것[:3]))) if 안막는것 else
         ('지우는 도구 %d개가 모두 --yes·--force 다짐을 받습니다'
          % len(지우는도구)) if 지우는도구 else
         '지우는 도구가 없습니다')

    # ── 계약-18 — 지우면 안 되는 것이 자료에 적혀 있고, 지켜지는가
    자리 = os.path.join(DATA, 'raw', 'keep.json')
    if not os.path.exists(자리):
        적기('18', '지우면 안 되는 것은 자료에 표시한다', '안잼',
             'data/raw/keep.json 이 없습니다 — 무엇을 남길지 안 적었습니다')
        return
    도구 = os.path.join(ROOT, 'engine', 'check_keep.py')
    if not os.path.exists(도구):
        적기('18', '지우면 안 되는 것은 자료에 표시한다', '안잼',
             'engine/check_keep.py 가 없습니다 — 적어만 두고 안 잽니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구, '--strict'],
                       capture_output=True, text=True, encoding='utf-8',
                       env=환경, timeout=900)
    글 = (r.stdout or '') + (r.stderr or '')
    괜찮나 = r.returncode == 0 and '중국어판이 멀쩡합니다' in 글
    남길것 = io.read_json(자리, default={}).get('남길것') or {}
    적기('18', '지우면 안 되는 것은 자료에 표시한다',
         '지킴' if 괜찮나 else '어김',
         ('남길 것 %d갈래를 적어 두었고, 옛 중국어 쪽이 쓰는 것이 '
          '모두 살아남습니다' % len(남길것)) if 괜찮나 else
         (글.strip().split('\n')[-1][:60] if 글.strip() else '알 수 없음'))


# ── 계약-19 · 작업 전에 규모를 잰다 ────────────────────────
def 계약19():
    잰다 = []
    for 이름 in ('migrate.py', 'migrate_index.py', 'migrate_travel.py',
                 'extract_jeonnam.py', 'extract_jeonnam_travel.py',
                 'fix_species.py', 'build.py'):
        s = io.read(os.path.join(ROOT, 'engine', 이름), default='')
        if '--write' in s or '--list' in s:
            잰다.append(이름)
    적기('19', '작업 전에 규모를 잰다',
         '지킴' if len(잰다) >= 6 else '어김',
         '도구 %d개가 먼저 보여 주고 --write 를 붙여야 씁니다' % len(잰다))


# ── 계약-20 · 사람이 고친 것은 덮이지 않는다 ───────────────
def 계약20():
    s = io.read(os.path.join(ROOT, 'engine', 'data.py'), default='')
    읽나 = 'overrides' in s
    나쁜것 = []
    for 상대, t in 파이썬들(밖=('engine/data.py',)):
        if re.search(r"io\.write\w*\([^)]*overrides", t):
            나쁜것.append(상대)
    적기('20', '사람이 고친 것은 덮이지 않는다',
         '어김' if (나쁜것 or not 읽나) else '지킴',
         ' · '.join(나쁜것) if 나쁜것 else
         'raw 와 overrides 를 합쳐 읽고, overrides 에 쓰는 도구가 없습니다')


# ── 계약-21 · 검사는 세 등급으로 나눈다 ────────────────────
def 계약21():
    """막을 것과 알릴 것을 **따로 모아 두는가**를 봅니다.

    글자만 찾으면 무딥니다 — 주석에 '알림' 이라고만 써 있어도 통과합니다.
    막는 목록과 알리는 목록을 **둘 다 두고**, 끝에서 둘을 가려
    돌려주는지를 봅니다.
    """
    안나눈것 = []
    모두 = sorted(glob.glob(os.path.join(ROOT, 'engine', 'check_*.py')))
    for p in 모두:
        s = io.read(p)
        이름 = os.path.basename(p)
        막는목록 = re.search(r'^(막음|문제)\s*[,=]', s, re.M)
        알리는목록 = re.search(r'알림\s*=\s*\[\]|,\s*알림\s*=', s)
        가름 = 'if 알림' in s or 'if 문제' in s or 'if 막음' in s
        if not (막는목록 and 알리는목록 and 가름):
            안나눈것.append(이름)
    적기('21', '검사는 세 등급으로 나눈다',
         '어김' if 안나눈것 else '지킴',
         ' · '.join(안나눈것) if 안나눈것 else
         '검사기 %d개가 막을 것과 알릴 것을 따로 둡니다' % len(모두))


# ── 계약-22 · 되돌릴 수 있어야 배포한다 ────────────────────
def 계약22():
    """★ 되돌리기를 **실제로 해 보고** 잽니다 (2026-09-26 바깥 검수 지적)

        「계약-22 는 실제로 롤백 가능한 상태를 만든 뒤 PASS 시키는
          게 맞습니다」

    되돌리는 길이 있다고 적어 두는 것으로는 부족합니다.
    tests/test_rollback.py 를 **그 자리에서 돌려** 봅니다.
    말이 아니라 바이트로 잽니다.
    """
    도구 = os.path.join(ROOT, 'engine', 'release.py')
    시험 = os.path.join(ROOT, 'tests', 'test_rollback.py')
    if not (os.path.exists(도구) and os.path.exists(시험)):
        적기('22', '되돌릴 수 있어야 배포한다', '안잼',
             'release.py 와 tests/test_rollback.py 가 둘 다 있어야 합니다')
        return
    if 빠르게():
        적기('22', '되돌릴 수 있어야 배포한다', '안잼',
             '--smoke 로 건너뛰었습니다 — 이것은 「지킴」이 아닙니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 시험], capture_output=True,
                       text=True, encoding='utf-8', env=환경, timeout=1800)
    글 = (r.stdout or '') + (r.stderr or '')
    m = re.search(r'(\d+)가지 모두 통과', 글)
    적기('22', '되돌릴 수 있어야 배포한다',
         '지킴' if (r.returncode == 0 and m) else '어김',
         ('되돌리기를 실제로 해 봤습니다 — %s가지 통과 (바이트까지 견줌)'
          % m.group(1)) if m else
         '되돌리기 시험이 실패했습니다: %s' % 글.strip().split('\n')[-1][:60])


# ── 계약-29 · 소스는 내 컴퓨터 밖에도 둔다 ─────────────────
def 계약29():
    """★ 계약-22 에서 갈라냈습니다 (2026-09-26 바깥 검수 지적)

        「원격 Git = 소스코드 복구 · 배포 릴리스 보관 = 실제 사이트
          롤백 이라서 둘은 같은 것이 아닙니다」

    묶어 두었더니 원격이 없다는 이유로 **할 수 있는 롤백까지**
    못 하고 있었습니다.
    """
    깃 = os.path.isdir(os.path.join(ROOT, '.git'))
    if not 깃:
        적기('29', '소스는 내 컴퓨터 밖에도 둔다', '어김',
             '저장소가 아닙니다')
        return
    원격 = subprocess.run(['git', '-C', ROOT, 'remote'],
                          capture_output=True, text=True).stdout.strip()
    적기('29', '소스는 내 컴퓨터 밖에도 둔다',
         '지킴' if 원격 else '안잼',
         ('원격: %s' % 원격.replace('\n', ' · ')) if 원격 else
         '내 컴퓨터에만 있습니다 — 주인 지시로 일단 이렇게 둡니다 '
         '(2026-09-26 「일단은 컴퓨터에서만 진행하자」)')


# ── 계약-23 · 바깥 자료가 죽어도 사이트는 산다 ─────────────
def 계약23():
    s = io.꼭읽기(os.path.join(ROOT, 'assets', 'js', 'tide.js'))
    막음 = 'catch(' in s and '불러오지 못했습니다' in s
    p = io.read(os.path.join(ROOT, 'assets', 'js', 'point-list.js'), default='')
    막음2 = '지도없음' in p
    적기('23', '바깥 자료가 죽어도 사이트는 산다',
         '지킴' if (막음 and 막음2) else '어김',
         '물때는 계산으로 늘 나오고, 지도를 못 불러와도 목록은 그대로입니다')


# ── 계약-24 · 바깥 자료의 형식을 검사한다 ──────────────────
def 계약24():
    s = io.read(os.path.join(ROOT, 'engine', 'check_tide.py'), default='')
    적기('24', '바깥 자료의 형식을 검사한다',
         '지킴' if '해양조사원물때' in s else '안잼',
         '물때는 해양조사원에서 받아 대조합니다. '
         '다른 바깥 자료는 아직 안 씁니다')


# ── 계약-25 · 옮긴 자료는 전수 검사한다 ────────────────────
def 계약25():
    있나 = os.path.exists(os.path.join(ROOT, 'engine', 'verify_migration.py'))
    있나2 = os.path.exists(os.path.join(ROOT, 'engine', 'compare_page.py'))
    적기('25', '옮긴 자료는 전수 검사한다',
         '지킴' if (있나 and 있나2) else '어김',
         'verify_migration.py(자료) · compare_page.py(쪽) 둘 다 있습니다')


# ── 계약-26 · 옮기는 도구는 멱등이어야 한다 ────────────────
def 계약26():
    """시험이 **모든 도구를 다루는지** 봅니다.

    시험 파일이 있다고 끝이 아닙니다. 새 이관 도구를 만들고 시험에
    안 넣으면, 시험은 통과하는데 그 도구는 안 재집니다 (2026-09-26).
    """
    시험길 = os.path.join(ROOT, 'tests', 'test_idempotent.py')
    if not os.path.exists(시험길):
        적기('26', '옮기는 도구는 멱등이어야 한다', '안잼',
             'tests/test_idempotent.py 가 없습니다')
        return
    글 = io.read(시험길, default='')
    옮기는것 = [os.path.basename(p) for p in
                sorted(glob.glob(os.path.join(ROOT, 'engine', 'migrate*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'extract_*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'fix_*.py')))]
    # ★ 시험이 **차례를 읽어 쓰면** 그 차례와 견줍니다 (2026-09-28)
    #
    #   전에는 시험 파일에서 도구 이름을 **글자로** 찾았습니다.
    #   그런데 같은 차례가 refresh.py 와 시험에 **따로 적혀 어긋나서**,
    #   시험이 refresh.py 에서 읽어 쓰게 고쳤습니다(SSOT).
    #   그랬더니 시험 파일에 이름이 없어져 **이 검사가 어김을 냈습니다.**
    #
    #   **옳게 고쳤는데 옛 검사가 나무라는 꼴**입니다.
    #   검사가 「무엇을 적었나」가 아니라 **「무엇을 도는가」**를 봐야 합니다.
    읽어쓰나 = 'from engine.refresh import 차례' in 글
    if 읽어쓰나:
        try:
            sys.path.insert(0, ROOT)
            from engine.refresh import 차례 as 갱신차례
            도는것 = set(x[0] for x in 갱신차례)
        except Exception:                      # noqa: BLE001
            도는것 = set()
        빠진것 = [x for x in 옮기는것 if x not in 도는것]
    else:
        빠진것 = [x for x in 옮기는것 if ("'%s'" % x) not in 글]
    적기('26', '옮기는 도구는 멱등이어야 한다',
         '어김' if 빠진것 else '지킴',
         ('시험에 안 든 도구 %d개: %s' % (len(빠진것), ' · '.join(빠진것)))
         if 빠진것 else
         '도구 %d개를 사본에 대고 두 번 돌려 바이트까지 견줍니다'
         % len(옮기는것))


# ── 계약-27 · 자료를 다시 캐는 길은 하나다 ─────────────────
def 계약27():
    """차례가 한 곳에 묶여 있고, 어중간한 상태를 잡는 검사가 있는가.

    도구 여덟이 저마다 멱등이어도 차례가 어긋나면 결과가 달라집니다.
    migrate 만 다시 돌리면 fix_species 의 일이 날아가는데, 개수는
    그대로라 세는 검사는 못 잡습니다.
    """
    묶은길 = os.path.join(ROOT, 'engine', 'refresh.py')
    잡는길 = os.path.join(ROOT, 'engine', 'check_stale.py')
    if not os.path.exists(묶은길) or not os.path.exists(잡는길):
        적기('27', '자료를 다시 캐는 길은 하나다', '어김',
             'refresh.py 와 check_stale.py 가 둘 다 있어야 합니다')
        return
    글 = io.read(묶은길, default='')
    옮기는것 = [os.path.basename(p) for p in
                sorted(glob.glob(os.path.join(ROOT, 'engine', 'migrate*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'extract_*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'fix_*.py')))]
    빠진것 = [x for x in 옮기는것 if ("'%s'" % x) not in 글]
    적기('27', '자료를 다시 캐는 길은 하나다',
         '어김' if 빠진것 else '지킴',
         ('refresh.py 의 차례에 빠진 도구 %d개: %s'
          % (len(빠진것), ' · '.join(빠진것))) if 빠진것 else
         'refresh.py 가 %d개를 차례대로 돌리고, check_stale.py 가 '
         '어중간한 자료를 잡습니다' % len(옮기는것))


# ── 계약-28 · 검사기도 시험받는다 ──────────────────────────
def 계약28():
    """검사기마다 「일부러 망가뜨려 보는 시험」이 있는가.

    검사기가 늘 통과를 내도록 망가져 있어도 모르면 소용없습니다.
    실제로 check_tide 가 tide.js 의 식을 베껴 적어 메아리였습니다.
    """
    시험길 = os.path.join(ROOT, 'tests', 'test_checkers.py')
    if not os.path.exists(시험길):
        적기('28', '검사기도 시험받는다', '안잼',
             'tests/test_checkers.py 가 없습니다')
        return
    글 = io.read(시험길, default='')
    검사기 = [os.path.basename(p) for p in
              sorted(glob.glob(os.path.join(ROOT, 'engine', 'check_*.py')))]
    # 계약 검사 자신은 여기서 빼지 않습니다 — 그것도 시험받아야 합니다
    빠진것 = [x for x in 검사기 if ("'%s'" % x) not in 글]
    적기('28', '검사기도 시험받는다',
         '어김' if 빠진것 else '지킴',
         ('시험이 안 다루는 검사기 %d개: %s'
          % (len(빠진것), ' · '.join(빠진것))) if 빠진것 else
         '검사기 %d개에 일부러 망가뜨려 보는 시험이 있습니다' % len(검사기))


# ── 계약-30 · 다른 언어 쪽은 그 언어여야 낸다 ──────────────
def 계약30():
    """check_i18n.py 를 그 자리에서 돌립니다.

    만든 언어가 한국어뿐이면 **잴 것이 없습니다** — 「해당없음」입니다.
    「지킴」이 아닙니다. 안 잰 것을 지켰다고 하지 않습니다.
    """
    도구 = os.path.join(ROOT, 'engine', 'check_i18n.py')
    if not os.path.exists(도구):
        적기('30', '다른 언어 쪽은 그 언어여야 낸다', '안잼',
             'engine/check_i18n.py 가 없습니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구, '--strict'],
                       capture_output=True, text=True, encoding='utf-8',
                       env=환경, timeout=900)
    글 = (r.stdout or '') + (r.stderr or '')
    if '잴 것이 없습니다' in 글:
        적기('30', '다른 언어 쪽은 그 언어여야 낸다', '해당없음',
             '한국어 쪽만 만듭니다 — 다른 언어 쪽이 없어 잴 것이 없습니다')
        return
    괜찮나 = r.returncode == 0 and '제대로 그 언어입니다' in 글
    적기('30', '다른 언어 쪽은 그 언어여야 낸다',
         '지킴' if 괜찮나 else '어김',
         '다른 언어 쪽이 제 언어로 되어 있습니다' if 괜찮나 else
         (글.strip().split('\n')[-1][:60] if 글.strip() else '알 수 없음'))


# ── 계약-31 · 검색 기준은 가이드를 따른다 ──────────────────
def 계약31():
    """check_seo.py 를 그 자리에서 돌립니다 (주인 규칙 28)."""
    도구 = os.path.join(ROOT, 'engine', 'check_seo.py')
    if not os.path.exists(도구):
        적기('31', '검색 기준은 가이드를 따른다', '안잼',
             'engine/check_seo.py 가 없습니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구, '--strict'],
                       capture_output=True, text=True, encoding='utf-8',
                       env=환경, timeout=900)
    글 = (r.stdout or '') + (r.stderr or '')
    m = re.search(r'쪽 (\d+)개가 검색 기준을 모두 지킵니다', 글)
    적기('31', '검색 기준은 가이드를 따른다',
         '지킴' if (r.returncode == 0 and m) else '어김',
         ('쪽 %s개가 제목·설명·og·canonical 기준을 지킵니다' % m.group(1))
         if m else
         ('손볼 곳: %s' % ' · '.join(
             x.strip().lstrip('✗ ').split('  ')[0]
             for x in 글.split('\n') if x.strip().startswith('✗'))[:70]))


# ── 계약-32 · 갱신은 대장 한곳에서 본다 ────────────────────
def 계약32():
    """check_refresh.py 를 그 자리에서 돌립니다 (주인 규칙 30).

    ★ 기한이 지난 자료가 있어도 **어김이 아닙니다** (계약-21).
      대장이 없거나 자료가 대장에 안 적혔을 때만 어김입니다.
      자료가 낡는 것은 시간이 하는 일이고, 대장을 안 적는 것은
      사람이 하는 일입니다. 둘은 다릅니다.
    """
    # ★ 갱신 도구 자체가 **돌기는 하는가** (2026-09-28)
    #
    #   `refresh.py` 가 2026-09-27 부터 통째로 터져 있었습니다.
    #   차례 목록에 칸 수가 다른 줄을 넣어서입니다.
    #
    #       ('migrate.py', '설명')                     ← 2칸
    #       ('migrate_photos.py', ('--write',), '설명')  ← 3칸
    #       → ValueError: too many values to unpack
    #
    #   **자료를 매달 다시 캐는 도구가 죽어 있었습니다.**
    #   대장을 아무리 잘 적어 둬도 캐는 손이 부러져 있으면 소용없습니다.
    #   그래서 여기서 **정말 돌아가는지** 봅니다 (--write 없이).
    갱신도구 = os.path.join(ROOT, 'engine', 'refresh.py')
    if os.path.exists(갱신도구):
        환경0 = dict(os.environ)
        환경0['PYTHONIOENCODING'] = 'utf-8'
        r0 = subprocess.run([sys.executable, 갱신도구], capture_output=True,
                            text=True, encoding='utf-8', errors='replace',
                            env=환경0, timeout=300)
        if r0.returncode != 0:
            끝 = [x for x in ((r0.stdout or '') + (r0.stderr or '')
                              ).strip().split('\n') if x.strip()]
            적기('32', '갱신은 대장 한곳에서 본다', '어김',
                 'refresh.py 가 안 돕니다 — ' + (끝[-1][:70] if 끝 else '?'))
            return

    자리 = os.path.join(DATA, 'raw', 'refresh-plan.json')
    도구 = os.path.join(ROOT, 'engine', 'check_refresh.py')
    if not (os.path.exists(자리) and os.path.exists(도구)):
        적기('32', '갱신은 대장 한곳에서 본다', '안잼',
             'refresh-plan.json 과 check_refresh.py 가 둘 다 있어야 합니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구], capture_output=True,
                       text=True, encoding='utf-8', env=환경, timeout=900)
    글 = (r.stdout or '') + (r.stderr or '')
    안적힘 = '대장에 안 적힌 자료' in 글 and '자료가 모두 대장에 있습니다' not in 글
    갈래수 = re.search(r'적힌 자료 (\d+)갈래', 글)
    적기('32', '갱신은 대장 한곳에서 본다',
         '어김' if 안적힘 else '지킴',
         '대장에 안 적힌 자료가 있습니다' if 안적힘 else
         ('자료 %s갈래가 대장에 있고, 마지막 갱신일을 git 에서 읽습니다'
          % (갈래수.group(1) if 갈래수 else '?')))


# ── 계약-09·10 다짐 · 검수기는 고치지 않는다 ───────────────
def 검수기는읽기만():
    """★ 주인 걱정에서 나온 검사입니다 (2026-09-26)

        「검수기가 정교해지는 것은 좋은데 후처리가 통일이 안 되는
          문제점이 발생하게 될까 봐 걱정이 되」

    옛 사이트가 망가진 길이 그것입니다.
      생성기 28개 + 후처리 16개 = 44곳이 결과물을 건드렸고,
      서로 어긋나 「고쳤는데 되돌아가는」 일이 났습니다.

    그래서 이 틀에서는 **고치는 곳은 build.py 하나**뿐입니다.
    검수기·검증기는 읽기만 합니다. 임시 폴더는 봐줍니다.
    """
    고치는것 = []
    보는도구 = (sorted(glob.glob(os.path.join(ROOT, 'engine', 'check_*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'verify_*.py')))
                + sorted(glob.glob(os.path.join(ROOT, 'engine', 'compare_*.py'))))
    for p in 보는도구:
        이름 = os.path.basename(p)
        s = io.read(p)
        임시씀 = 'tempfile' in s
        for m in re.finditer(r'io\.write\w*\(([^)]{0,80})', s):
            안 = m.group(1)
            # 임시 폴더(t, 딴자리 …)에 쓰는 것은 괜찮습니다
            if 임시씀 and re.search(r'\b(t|임시|딴자리|일터)\b', 안):
                continue
            # ★ tests/out/ 은 **검사 결과를 적는 자리**입니다 (2026-09-28)
            #   쪽도 자료도 아닙니다. 계약-01 에서 gate.py·url_table.py
            #   를 봐주는 것과 같은 이치입니다.
            #   check_deployed.py 가 「어디를 언제 어느 판으로 쟀는지」를
            #   여기 남깁니다 — 사람이 기억해서 보고하면 틀립니다.
            if "'tests'" in 안 and "'out'" in 안:
                continue
            if 'NEW' in 안 or 'DATA' in 안 or 'ROOT' in 안:
                고치는것.append('%s → %s' % (이름, 안.strip()[:40]))
    적기('09', '검수기는 고치지 않는다 (읽기만)',
         '어김' if 고치는것 else '지킴',
         ' · '.join(고치는것[:3]) if 고치는것 else
         '보는 도구 %d개가 진짜 자료·쪽을 한 글자도 안 고칩니다' % len(보는도구))


def 문서의계약번호():
    """docs/CONTRACTS.md 에 적힌 계약 번호를 차례대로.

    ★ 계약 수를 **손으로 적지 않습니다** (주인 규칙 29, 2026-09-26)
        「계약 26개를 …」이라고 두 곳에 박아 두었는데, 계약을 28개로
        늘린 뒤에도 그대로 남아 바깥 검수에서 「26인가 28인가」를
        묻게 만들었습니다. 숫자는 늘 문서에서 셉니다.
    """
    글 = io.read(os.path.join(ROOT, 'docs', 'CONTRACTS.md'), default='')
    return re.findall(r'^### 계약-(\d+)', 글, re.M)


def 번호검사():
    """번호가 01부터 빠짐없이 이어지는가.

    계약을 지우고 번호를 비워 두면, 「28개」라는 말과 실제 내용이
    어긋납니다. 겹친 번호도 같은 탈입니다.
    """
    번호들 = 문서의계약번호()
    수 = [int(x) for x in 번호들]
    겹침 = sorted(k for k, v in collections.Counter(수).items() if v > 1)
    빠짐 = [i for i in range(1, (max(수) if 수 else 0) + 1) if i not in 수]
    말 = []
    if 겹침:
        말.append('겹친 번호 %s' % ' · '.join('%02d' % x for x in 겹침))
    if 빠짐:
        말.append('빠진 번호 %s' % ' · '.join('%02d' % x for x in 빠짐))
    return 번호들, 말



# ── 계약-33 · 보고 나서 판단까지 되어야 한다 ────────────────
def 계약33():
    """check_actionable.py 를 그 자리에서 돌립니다.

    ★ 자료가 화면에 나오는 것만으로는 모자랍니다 (바깥 검수 11차).
      손님이 그것을 보고 **다음에 무엇을 할지 정할 수 있어야** 합니다.

      물때표가 그 사례였습니다. 카드 열넷을 예쁘게 그려 놓고
      「그래서 언제 가면 좋은가」를 빼 두었습니다.
      사슬 검사는 못 잡았습니다 — 자료는 다 나왔기 때문입니다.
    """
    도구 = os.path.join(ROOT, 'engine', 'check_actionable.py')
    if not os.path.exists(도구):
        적기('33', '보고 나서 판단까지 되어야 한다', '안 잼',
             'check_actionable.py 가 없습니다')
        return
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([sys.executable, 도구, '--strict'],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=환경, timeout=900)
    글 = (r.stdout or '') + (r.stderr or '')
    if r.returncode == 4:
        # ★ 크롬이 없으면 **못 잰 것**입니다 — 통과가 아닙니다
        적기('33', '보고 나서 판단까지 되어야 한다', '안 잼',
             '크롬이 있어야 잽니다')
    elif r.returncode == 0:
        적기('33', '보고 나서 판단까지 되어야 한다', '지킴',
             '보고 나서 판단까지 됩니다')
    else:
        끝 = [x.strip() for x in 글.split('\n')
              if x.strip().startswith('✗')]
        적기('33', '보고 나서 판단까지 되어야 한다', '어김',
             (끝[0].lstrip('✗ ')[:70] if 끝 else '판단 칸이 없습니다'))


# ── 계약-34 · 「필요 없다」와 「못 했다」를 섞지 않는다 ─────
def 계약34():
    """gate.재료가없나() 가 둘을 제대로 가르는가.

    ★ N.A. 는 GO 후보에 들고 INFRA_FAIL 은 안 듭니다.
      섞이면 **재지 않고 통과**합니다. (바깥 검수 11차)
    """
    try:
        from engine import gate as _g
    except Exception as e:
        적기('34', '「필요 없다」와 「못 했다」를 섞지 않는다', '안 잼',
             'gate 를 못 읽었습니다: %s' % str(e)[:40])
        return
    if not hasattr(_g, '재료가없나'):
        적기('34', '「필요 없다」와 「못 했다」를 섞지 않는다', '어김',
             'gate.재료가없나() 가 없습니다 — 둘을 안 가릅니다')
        return
    봄 = [
        ('한국어 말고 다른 언어 쪽이 없습니다 — 잴 것이 없습니다.', False),
        ('옛 사이트가 없습니다 — 잴 것이 없습니다.', True),
        ('크롬을 못 찾았습니다. 잴 것이 없습니다.', True),
        ('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.', True),
        # ★ 2026-09-29 — 사진 검사가 이 말로 통과하고 있었습니다
        ('잴 것이 없습니다 — site/ 에 쪽이 없습니다.', True),
        # 이쪽은 N.A. 가 맞습니다 — 헷갈려 같이 잡으면 안 됩니다
        ('옛 계산을 쓰는 쪽이 없습니다 — 잴 것이 없습니다.', False),
    ]
    틀린것 = [글[:30] for 글, 바람 in 봄
              if bool(_g.재료가없나(글)) != 바람]
    if 틀린것:
        적기('34', '「필요 없다」와 「못 했다」를 섞지 않는다', '어김',
             '못 가르는 말 %d가지: %s' % (len(틀린것), 틀린것[0]))
    else:
        적기('34', '「필요 없다」와 「못 했다」를 섞지 않는다', '지킴',
             '재료가 없는 것을 N.A. 로 세지 않습니다')

def main():
    번호들, 번호탈 = 번호검사()
    print('계약 %d개를 지키고 있는지  (docs/CONTRACTS.md)' % len(번호들))
    if '--list' in sys.argv:
        글 = io.read(os.path.join(ROOT, 'docs', 'CONTRACTS.md'), default='')
        print('')
        for 번호, 이름 in re.findall(r'^### 계약-(\d+) · (.+)$', 글, re.M):
            print('  계약-%s  %s' % (번호, 이름))
        print('')
        print('  모두 %d개 · 번호 %s ~ %s'
              % (len(번호들), 번호들[0], 번호들[-1]))
        if 번호탈:
            print('  ✗ %s' % ' / '.join(번호탈))
        else:
            print('  · 번호가 01부터 빠짐없이 이어집니다')
        return 0
    if 번호탈:
        print('  ✗ %s' % ' / '.join(번호탈))
    print('')
    d = 자료()

    계약01()
    계약02(d)
    계약03()
    계약04()
    계약05(d)
    계약06(d)
    if not 빠르게():
        계약07()
    else:
        적기('07', '두 번 만들어도 결과가 같아야 한다', '안잼',
             '--smoke 로 건너뛰었습니다 — 이것은 「지킴」이 아닙니다')
    계약08()
    계약0910()
    검수기는읽기만()
    계약11()
    계약12(d)
    계약13()
    계약1416()
    계약15()
    계약1718()
    계약19()
    계약20()
    계약21()
    계약22()
    계약23()
    계약24()
    계약25()
    계약26()
    계약27()
    계약28()
    계약29()
    계약30()
    계약31()
    계약32()

    계약33()

    계약34()
    표 = {'지킴': '·', '어김': '✗', '안잼': '~', '해당없음': '-'}
    for x in sorted(결과, key=lambda v: v['번호']):
        print('  %s 계약-%s %-32s %s'
              % (표.get(x['상태'], '?'), x['번호'], x['이름'], x['말']))

    # ★ 합계가 계약 수와 맞는지 **검사 자신이 확인합니다** (2026-09-26)
    #   처음 보고에서 22+0+2+1 = 25 로 하나가 빠져 있었습니다.
    #   「건너뜀」을 어느 칸에도 안 세었기 때문입니다.
    #   숫자를 기계가 센다고 해 놓고, 정작 검사 결과의 숫자가 안 맞았습니다.
    #   검사 결과를 검사하는 것도 검사입니다.
    문서계약 = len(문서의계약번호())
    센것 = collections.Counter(x['상태'] for x in 결과)
    합 = sum(센것.values())

    # ★ 「몇 개 지켰다」와 「배포해도 된다」를 섞지 않습니다
    #   (2026-09-26 바깥 검수 지적)
    #     「24개 통과했다」와 「배포할 수 있다」를 혼동하지 않게
    #   안 잰 것이 하나라도 있으면 배포는 아닙니다. 어긴 것이 없어도
    #   마찬가지입니다 — 재 보지 않은 것은 지킨 것이 아니기 때문입니다.
    안잰번호 = sorted(x['번호'] for x in 결과 if x['상태'] == '안잼')
    어긴번호 = sorted(x['번호'] for x in 결과 if x['상태'] == '어김')
    print('')
    print('  ' + '─' * 46)
    print('  검수 결과')
    print('  ' + '─' * 46)
    print('  총 계약      %4d' % 문서계약)
    print('  지킴         %4d' % 센것['지킴'])
    print('  어김         %4d' % 센것['어김'])
    print('  안 잰 것     %4d' % 센것['안잼'])
    if 센것['해당없음']:
        print('  해당없음     %4d' % 센것['해당없음'])
    if 어긴번호:
        print('')
        print('  어김')
        for x in sorted(결과, key=lambda v: v['번호']):
            if x['상태'] == '어김':
                print('  %s  %s' % (x['번호'], x['말'][:52]))
    if 안잰번호:
        print('')
        print('  안 잰 것')
        for x in sorted(결과, key=lambda v: v['번호']):
            if x['상태'] == '안잼':
                print('  %s  %s' % (x['번호'], x['말'][:52]))
    print('  ' + '─' * 46)
    막을일 = 센것['어김'] or 센것['안잼'] or (문서계약 and 합 != 문서계약)

    # ★ 이 도구는 **배포를 말하지 않습니다** (2026-09-28 바깥 검수 6차)
    #
    #   전에는 여기서 「배포 가능 여부: 예」라고 찍었습니다.
    #   그 말을 검수 요청서에 그대로 옮겼더니, 같은 문서 안에
    #
    #       「배포 가능 여부: 예」
    #       「--full 을 아직 한 번도 성공 못 했습니다」
    #
    #   가 나란히 있게 됐습니다. 바깥 검수가 바로 잡아냈습니다.
    #
    #       「검수 시스템이 건전해졌다」와 「사이트가 배포 준비를
    #         끝냈다」는 서로 다른 문제인데 둘이 섞여 있습니다.
    #
    #   맞는 말입니다. 계약 32개를 지켰다는 것은 **엔진이 건전하다**는
    #   뜻이지 **사이트를 올려도 된다**가 아닙니다.
    #   배포 판정은 `engine/gate.py --full` 만 냅니다.
    print('  계약 상태: %s' % ('어긴 것이 있습니다' if 막을일
                               else '모두 지켰습니다'))
    print('  ★ 이것은 **배포 판정이 아닙니다.** 엔진이 건전한가만 봅니다.')
    print('    배포 판정은  python engine/gate.py --full  이 냅니다.')
    if 막을일:
        왜 = []
        if 센것['어김']:
            왜.append('어긴 계약 %d개' % 센것['어김'])
        if 센것['안잼']:
            왜.append('안 잰 계약 %d개' % 센것['안잼'])
        if 문서계약 and 합 != 문서계약:
            왜.append('합계가 안 맞음')
        print('    까닭: %s' % ' · '.join(왜))
        print('    「몇 개 지켰다」와 「배포해도 된다」는 다릅니다.')
        print('    재 보지 않은 것은 지킨 것이 아닙니다.')
    print('  ' + '─' * 46)

    if 문서계약 and 합 != 문서계약:
        print('')
        print('  ✗ 합계가 계약 수와 다릅니다 — %d ≠ %d' % (합, 문서계약))
        print('    어느 칸에도 안 센 계약이 있습니다. 검사 자체가 미덥지 않습니다.')
        본번호 = set(x['번호'] for x in 결과)
        모든번호 = set(re.findall(r'^### 계약-(\d+)',
                                  io.read(os.path.join(ROOT, 'docs',
                                                       'CONTRACTS.md'),
                                          default=''), re.M))
        빠진것 = sorted(모든번호 - 본번호)
        겹친것 = [k for k, v in
                  collections.Counter(x['번호'] for x in 결과).items() if v > 1]
        if 빠진것:
            print('    안 본 계약: %s' % ' · '.join(빠진것))
        if 겹친것:
            print('    두 번 센 계약: %s' % ' · '.join(겹친것))
        문제있음 = True
    else:
        문제있음 = False
    if 문제있음:
        막음.append({'번호': '--', '이름': '검사 결과의 합계가 안 맞음',
                     '상태': '어김', '말': '%d ≠ %d' % (합, 문서계약)})
    막음.extend(x for x in 결과 if x['상태'] == '어김')
    알림.extend(x for x in 결과 if x['상태'] == '안잼')
    어긴것 = 막음
    if 어긴것:
        print('')
        print('★ 어긴 계약 %d개' % len(어긴것))
        for x in 어긴것:
            print('    계약-%s %s — %s' % (x['번호'], x['이름'], x['말']))
        return 1 if '--strict' in sys.argv else 0
    안잰것 = [x for x in 알림 if x['상태'] == '안잼']
    if 안잰것:
        print('')
        print('~ 아직 안 재 본 계약 %d개 — **지킨다고 말할 수 없습니다**'
              % len(안잰것))
        for x in 안잰것:
            print('    계약-%s %-30s %s' % (x['번호'], x['이름'], x['말']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
