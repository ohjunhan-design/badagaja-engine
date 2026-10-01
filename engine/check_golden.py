# -*- coding: utf-8 -*-
"""**있던 것이 사라지지 않았는가** — 쪽의 생김새를 재어 견줍니다.

★ 왜 만들었나 (2026-09-27 바깥 검수 5차 지시)

    검사기 20개가 전부 PASS 였는데, 주인이 화면을 보고 셋을
    잡아냈습니다.

        416쪽에 사진이 **한 장도** 없음
        링크 안에 링크가 들어가 02 칸이 거대한 막대로 깨짐
        빠른이동 아이콘 **7칸이 통째로** 사라짐

    셋 다 검사기가 못 잡았습니다. 까닭은 하나입니다.

        **없는 것을 검사하는 검사가 없었습니다.**

    링크가 깨졌는지는 봤지만, 링크가 **있는지**는 안 봤습니다.
    사진 주소가 맞는지는 봤지만, 사진이 **있는지**는 안 봤습니다.

    바깥 검수가 이렇게 말했습니다.

        「모든 것을 검사한다」가 아니라
        「변경으로 인해 기존에 존재하던 중요한 사용자 경험이
          사라지는 것을 감시한다」 쪽으로 가야 합니다.

    맞는 말입니다. 그래서 **전에 어떤 모습이었는지를 적어 두고**,
    크게 달라지면 알립니다.

★ 다름은 FAIL 이 아닙니다 — **CHANGE DETECTED** 입니다

    사진을 더 좋은 것으로 바꾸면 수가 달라집니다. 포인트를 더하면
    링크가 늡니다. 그것을 FAIL 로 내면 아무도 이 검사를 안 믿게
    되고, 결국 꺼 버립니다.

        달라짐  →  **사람이 봅니다**  →  뜻한 것이면 새 기준으로 저장
                                     →  뜻하지 않은 것이면 고칩니다

    `--받아들이기` 로 새 기준을 저장합니다.

★ 그런데 **언제나 지켜야 할 것**은 FAIL 입니다 ([2]장)

    「사진이 몇 장인가」는 달라질 수 있습니다.
    「링크 안에 링크가 있는가」는 달라지면 안 됩니다. 늘 틀린 것입니다.

★ 크롬을 안 씁니다
    글만 읽어 셉니다. 빠르고, 리눅스에서도 그대로 돕니다.
    (깃허브 액션에서 판정을 돌리기로 했습니다)

쓰는 법
    python engine/check_golden.py              기준과 견줍니다
    python engine/check_golden.py --받아들이기   지금 모습을 기준으로 삼습니다
    python engine/check_golden.py --기준내기     기준을 화면에 찍어만 봅니다
"""
import os
import re
import sys
import json
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
기준길 = os.path.join(ROOT, 'tests', 'golden', '구조.json')

# 검사 등급 (계약-21) — 막을 것과 알릴 것을 **따로** 둡니다
#   막음 — 배포를 막습니다. 늘 틀린 것
#          (링크 안 링크 · 보이는 것이 0인 쪽 · 빈 링크 · alt 없는 사진)
#   알림 — 막지 않습니다. 전과 달라진 것 — **사람이 보고 정합니다**
막음 = []
알림 = []
달라짐 = []      # 알림 가운데 「전과 달라짐」만 따로 셉니다 (끝난값 2)

# ── 무엇을 세는가 ──────────────────────────────────────────
#
#   ★ 「사람 눈에 보이는 것」과 「누를 수 있는 것」을 셉니다.
#     class 이름은 세지 않습니다 — 디자인을 고치면 바뀌는데,
#     그것까지 잡으면 알림이 너무 잦아 아무도 안 봅니다.
세는것 = [
    ('사진',     r'<img\b'),
    ('그림',     r'<svg\b'),
    ('picture',  r'<picture\b'),
    ('링크',     r'<a\b[^>]*\bhref='),
    ('단추',     r'<button\b'),
    ('입력칸',   r'<input\b'),
    ('form',     r'<form\b'),
    ('section',  r'<section\b'),
    ('nav',      r'<nav\b'),
    ('표',       r'<table\b'),
    ('큰제목',   r'<h1\b'),
    ('중제목',   r'<h2\b'),
    ('작은제목', r'<h3\b'),
    ('목록',     r'<li\b'),
    ('iframe',   r'<iframe\b'),
    ('광고자리', r'class="[^"]*\bad-slot\b'),
]

# 쪽 갈래 — 첫 칸의 이름으로 나눕니다
def 갈래(이름):
    """`jeonnam/yeosu/index.html` → `jeonnam`, `index.html` → `(첫화면)`"""
    쪽 = 이름.split('/')
    if len(쪽) == 1:
        return '(첫화면)' if 쪽[0] == 'index.html' else '(맨위)' + 쪽[0]
    # 권역은 수가 많아 한 갈래로 묶습니다
    if len(쪽) >= 3:
        return 쪽[0] + '/*/'
    return 쪽[0] + '/'


def 쪽들():
    """잴 쪽 목록.

    ★ `__` 로 시작하는 것은 **검사기의 살림살이**입니다
      (2026-10-01). `check_mobile.py` 가 잴 때 만들었다 지우는
      `__재기임시.html` 을 골든이 그 순간 잡아 「새 갈래가
      생겼다」고 알렸습니다.

      즉 **검사 차례에 따라 결과가 흔들립니다.** 자료를 안
      고쳤는데 결과가 달라지면 골든은 못 믿을 것이 됩니다
      (주인 규칙 26). 사이트 쪽은 `__` 로 시작하지 않습니다.
    """
    것 = []
    for p in sorted(glob.glob(os.path.join(NEW, '**', '*.html'),
                              recursive=True)):
        상대 = os.path.relpath(p, NEW).replace(os.sep, '/')
        if any(조각.startswith('__') for 조각 in 상대.split('/')):
            continue
        것.append((상대, p))
    return 것


def 몸통만(s):
    """<head> 와 <script>·<!-- --> 를 뺍니다.

    ★ 머리와 스크립트 안의 `<img` 는 **사람 눈에 안 보입니다.**
      그것까지 세면 「사진이 있다」가 거짓이 됩니다.
      실제로 416쪽에 사진이 0장일 때도 구조화 자료(JSON-LD)에는
      사진 주소가 적혀 있었습니다.
    """
    s = re.sub(r'(?is)<head\b.*?</head>', ' ', s)
    s = re.sub(r'(?is)<script\b.*?</script>', ' ', s)
    s = re.sub(r'(?is)<style\b.*?</style>', ' ', s)
    s = re.sub(r'(?s)<!--.*?-->', ' ', s)
    s = re.sub(r'(?is)<template\b.*?</template>', ' ', s)
    return s


def 재기(s):
    몸 = 몸통만(s)
    나옴 = {}
    for 이름, 무늬 in 세는것:
        나옴[이름] = len(re.findall(무늬, 몸, re.I))
    return 나옴


# ── [2] 언제나 지켜야 할 것 ────────────────────────────────
#
#   달라질 수 있는 것이 아닙니다. 있으면 **늘 틀린 것**입니다.
def 늘틀린것(이름, s):
    난것 = []
    몸 = 몸통만(s)

    # ★ 링크 안에 링크 — 주인이 화면 보고 잡은 것 (2026-09-27)
    #   HTML 이 금합니다. 브라우저가 제멋대로 고쳐 짜서
    #   02 칸 알약이 **거대한 세로 막대**로 깨졌습니다.
    for m in re.finditer(r'(?is)<a\b[^>]*>(.*?)</a>', 몸):
        if re.search(r'<a\b[^>]*\bhref=', m.group(1), re.I):
            난것.append('링크 안에 링크')
            break

    # 단추 안에 단추 — 같은 까닭
    for m in re.finditer(r'(?is)<button\b[^>]*>(.*?)</button>', 몸):
        if re.search(r'<button\b', m.group(1), re.I):
            난것.append('단추 안에 단추')
            break

    # ★ 보이는 것이 하나도 없는 쪽 — 주인 규칙 6-1
    #   「사람은 눈으로 봅니다. 쪽에는 보이는 것이 있어야 합니다.」
    보이는것 = (len(re.findall(r'<img\b', 몸, re.I))
                + len(re.findall(r'<svg\b', 몸, re.I))
                + len(re.findall(r'<picture\b', 몸, re.I)))
    if 보이는것 == 0:
        난것.append('보이는 것이 하나도 없음 (사진·그림 0)')

    # 설명 없는 사진 — 눈이 불편한 분이 못 읽습니다
    민사진 = 0
    for m in re.finditer(r'(?is)<img\b[^>]*>', 몸):
        if not re.search(r'\balt=', m.group(0), re.I):
            민사진 += 1
    if 민사진:
        난것.append('alt 없는 사진 %d장' % 민사진)

    # 빈 링크 — 눌러도 아무 데도 안 갑니다
    빈링크 = len(re.findall(r'<a\b[^>]*\bhref=(""|\'\')', 몸, re.I))
    if 빈링크:
        난것.append('빈 링크 %d개' % 빈링크)

    return 난것


def 기준읽기():
    if not os.path.exists(기준길):
        return None
    try:
        return io.read_json(기준길)
    except (ValueError, OSError):
        return None


def 지금모습():
    """갈래마다 **쪽수·합계·가장 적은 쪽**을 적습니다.

    ★ 쪽마다 따로 적지 않습니다.
      포인트 하나만 늘어도 416줄이 흔들려 아무도 안 보게 됩니다.
      갈래로 묶으면 「사진이 통째로 사라짐」 같은 큰일만 드러납니다.
      다만 **가장 적은 쪽**은 적어 둡니다 — 한 쪽만 빈 경우를
      합계로는 못 잡기 때문입니다.
    """
    모음 = collections.defaultdict(list)
    늘틀림 = []
    for 이름, p in 쪽들():
        s = io.read(p, default='')
        모음[갈래(이름)].append((이름, 재기(s)))
        for x in 늘틀린것(이름, s):
            늘틀림.append((이름, x))

    나옴 = {}
    for g in sorted(모음):
        것들 = 모음[g]
        한갈래 = {'쪽수': len(것들)}
        for 이름, _무늬 in 세는것:
            값 = [x[1][이름] for x in 것들]
            한갈래[이름] = {'합': sum(값), '가장적은쪽': min(값)}
        나옴[g] = 한갈래
    return 나옴, 늘틀림



def 줄었나(한가지):
    """달라진 것 하나가 **줄어든** 것인가 (2026-09-29).

    이 검사의 이름이 「있던 것이 사라지지 않았는가」입니다.
    줄어든 것과 늘어난 것은 무게가 다릅니다 — 늘어난 것은
    새로 넣은 것이지만, **줄어든 것은 잃은 것**입니다.
    """
    _쪽, _무엇, 옛값, 새값 = 한가지
    return (isinstance(옛값, int) and isinstance(새값, int)
            and 새값 < 옛값)


def 견주기(기준, 지금):
    """갈래마다 무엇이 얼마나 달라졌는지."""
    난것 = []
    for g in sorted(set(기준) | set(지금)):
        if g not in 지금:
            난것.append((g, '갈래가 통째로 사라짐', 기준[g].get('쪽수'), 0))
            continue
        if g not in 기준:
            난것.append((g, '새 갈래', 0, 지금[g].get('쪽수')))
            continue
        옛, 새 = 기준[g], 지금[g]
        if 옛.get('쪽수') != 새.get('쪽수'):
            난것.append((g, '쪽수', 옛.get('쪽수'), 새.get('쪽수')))
        for 이름, _무늬 in 세는것:
            ㅇ = (옛.get(이름) or {})
            ㅅ = (새.get(이름) or {})
            for 무엇 in ('합', '가장적은쪽'):
                a, b = ㅇ.get(무엇), ㅅ.get(무엇)
                if a is None or b is None:
                    continue
                if a != b:
                    난것.append((g, '%s %s' % (이름, 무엇), a, b))
    return 난것


def main():
    받아들이기 = '--받아들이기' in sys.argv
    기준내기 = '--기준내기' in sys.argv

    print('있던 것이 사라지지 않았는가 (바깥 검수 5차 — Golden)')
    지금, 늘틀림 = 지금모습()
    쪽수 = sum(v['쪽수'] for v in 지금.values())
    print('  쪽 %d개 · 갈래 %d가지' % (쪽수, len(지금)))
    print('')

    if 기준내기:
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(지금, ensure_ascii=False, indent=2))
        return 0

    # ── [1] 전과 견주기
    print('[1] 전과 견주어 크게 달라진 것이 있는가')
    기준 = 기준읽기()
    if 기준 is None:
        print('  ~ 기준이 아직 없습니다 — 지금 모습을 기준으로 삼습니다')
        io.write_json(기준길, 지금)
        print('      %s 에 적었습니다' % os.path.relpath(기준길, ROOT))
        print('      (다음부터 이것과 견줍니다)')
    else:
        차 = 견주기(기준, 지금)
        if not 차:
            print('  · 달라진 것이 없습니다')
        elif 받아들이기:
            io.write_json(기준길, 지금)
            print('  · 달라진 것 %d가지를 **새 기준으로 받아들였습니다**'
                  % len(차))
            for g, 무엇, a, b in 차[:12]:
                print('      %-14s %-18s %s → %s' % (g, 무엇, a, b))
        else:
            # ★ FAIL 이 아닙니다. 사람이 보라는 뜻입니다.
            달라짐.append('%d가지가 달라졌습니다' % len(차))
            for g, 무엇, a, b in 차:
                알림.append('%s %s %s → %s' % (g, 무엇, a, b))
            print('  ! CHANGE DETECTED — %d가지가 달라졌습니다' % len(차))
            print('      **틀렸다는 뜻이 아닙니다.** 뜻한 것인지 보세요.')

            # ★ **줄어든 것을 먼저, 빠짐없이 보여 줍니다** (2026-09-29)
            #
            #   이 검사의 이름은 「있던 것이 사라지지 않았는가」입니다.
            #   그런데 앞 20가지만 찍고 나머지를 「그 밖 344가지」로
            #   덮고 있었습니다. **줄어든 것이 그 속에 숨으면
            #   사람이 볼 길이 없습니다.**
            #
            #   늘어난 것은 대개 새로 넣은 것이라 20가지만 봐도
            #   짐작이 됩니다. 줄어든 것은 **하나라도 놓치면 안 됩니다.**
            준것 = [x for x in 차 if 줄었나(x)]
            늘것 = [x for x in 차 if not 줄었나(x)]

            if 준것:
                print('')
                print('    ★ **줄어든 것 %d가지** — 있던 것을 잃었습니다'
                      % len(준것))
                for g, 무엇, a, b in 준것:          # 자르지 않습니다
                    print('      ↓ %-14s %-18s %s → %s' % (g, 무엇, a, b))
                print('')
            else:
                print('      · 줄어든 것은 하나도 없습니다 — 잃은 것이 없습니다')

            for g, 무엇, a, b in 늘것[:20]:
                print('      ↑ %-14s %-18s %s → %s' % (g, 무엇, a, b))
            if len(늘것) > 20:
                print('      … 그 밖 늘어난 것 %d가지' % (len(늘것) - 20))
            print('')
            print('      뜻한 것이면:  python engine/check_golden.py --받아들이기')
    print('')

    # ── [2] 늘 틀린 것
    print('[2] 언제나 지켜야 할 것')
    if not 늘틀림:
        print('  · 모두 지켰습니다')
        print('      링크 안 링크 · 단추 안 단추 · 빈 쪽 · alt 없는 사진 · 빈 링크')
    else:
        묶음 = collections.Counter(x[1].split(' ')[0] for x in 늘틀림)
        for 무엇, 몇 in 묶음.most_common():
            막음.append('%s — %d쪽' % (무엇, 몇))
        print('  ✗ 어긴 것 %d건' % len(늘틀림))
        for 이름, 무엇 in 늘틀림[:12]:
            print('      %-42s %s' % (이름[:42], 무엇))
        if len(늘틀림) > 12:
            print('      … 그 밖 %d건' % (len(늘틀림) - 12))
    print('')

    # ── 끝
    if 막음:
        print('✗ 지켜야 할 것을 어겼습니다')
        for x in 막음:
            print('    %s' % x)
        return 1
    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
    if 달라짐:
        print('! CHANGE DETECTED — 사람이 보고 정해 주세요')
        print('  (FAIL 이 아닙니다. 뜻한 변경이면 --받아들이기)')
        return 2
    print('있던 것이 그대로 있습니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
