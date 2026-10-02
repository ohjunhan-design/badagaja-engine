# -*- coding: utf-8 -*-
"""**보고 나서 판단까지 되는가** (계약-33 · 바깥 검수 11차)

★ 왜 만들었나 (2026-09-28)

    물때표를 새로 지으며 카드 열넷·우리말 이름·막대·물높이·
    간조 만조 시각까지 넣었습니다. 옛 쪽보다 훨씬 보기 좋아졌습니다.

    그런데 옛 쪽에 있던 한 줄이 사라졌습니다.

        「물이 가장 많이 빠지는 날은 오늘이에요」
        「이번 주말은 조금 무렵이라 물이 적게 빠집니다.
          해루질보다는 낚시가 낫습니다」

    손님이 **열네 칸을 눈으로 훑어 스스로 고르게** 둔 것입니다.

    check_coverage.py 는 이것을 못 잡았습니다 — 자료는 다
    나왔기 때문입니다. **주인이 화면에 직접 표시해 주셔서
    알았습니다.** 검사기가 못 본 것을 사람이 본 것입니다.

★ 바깥 검수 11차가 이렇게 말했습니다

    「**자료가 화면에 나왔다 ≠ 사용자가 그 자료로 결정을
      내릴 수 있다**」

    「SOURCE → COMPUTE → RENDERED → **ACTIONABLE** 네 단계로
      만들면 검수 체계가 한 단계 더 완성됩니다」

★ 이것은 사람 눈으로만 볼 일이 아닙니다

    「그래서 언제 가면 좋은가」가 쪽에 **있는지 없는지**는
    기계가 봅니다. 그 말이 **옳은지**는 8번(물때 독립 검증)이
    이미 국립해양조사원 자료와 견주고 있습니다.

쓰는 법
    python engine/check_actionable.py
    python engine/check_actionable.py --strict    없으면 끝난값 1
    python engine/check_actionable.py --list      어느 쪽이 빠졌는지
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io     # noqa: E402
from engine import data   # noqa: E402
from engine import url    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

막음, 알림 = [], []


def 글만(html):
    s = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s)


def 판단칸있나(원문):
    """「이번 주 언제 갈까」 칸이 쪽에 있는가.

    ★ 글자가 아니라 **칸**을 봅니다. 글은 날마다 바뀝니다
      (오늘이었다가 모레였다가). 칸은 늘 같은 자리에 있습니다.

    ★ 2026-10-02 — **클래스가 더 붙어도 찾습니다**
      `class="when"` 만 글자 그대로 보다가, 제가 꾸미려고
      `class="when tt-advice"` 로 바꾸자 **못 찾았습니다.**
      쪽은 멀쩡한데 검사가 「없다」고 했습니다.
      검사기가 헛것을 잡으면 진짜가 묻힙니다.

    ★ 낱말 경계 기호는 **쓰지 않습니다.** 도구를 거치며 먹혀
      검사가 조용히 죽습니다. 클래스 목록을 쪼개 봅니다.
    """
    for m in re.finditer(r'class\s*=\s*["\']([^"\']*)["\']', 원문):
        if 'when' in m.group(1).split():
            return True
    return False


def 무엇을말하나(원문):
    """그 칸이 실제로 무엇을 말하는지 꺼냅니다."""
    m = re.search(r'<div class="when">(.*?)</div>\s*(?=<div|<section|$)',
                  원문, re.S)
    if not m:
        m = re.search(r'<div class="when">(.*)', 원문, re.S)
    if not m:
        return {}
    토막 = m.group(1)[:1200]
    끝 = {}
    for 반, 열쇠 in (('when-t', '판단'), ('when-s', '근거'),
                     ('when-w', '주말')):
        mm = re.search(r'class="%s"[^>]*>(.*?)<' % 반, 토막, re.S)
        if mm:
            끝[열쇠] = re.sub(r'\s+', ' ', mm.group(1)).strip()
    return 끝



def 그릴수있나():
    """크롬이 자리에 있는가. **없으면 못 잰 것입니다.**"""
    try:
        from engine import machine
        길 = machine.크롬찾기()
        if 길 and os.path.exists(길):
            return True, 길
        return False, '크롬을 못 찾았습니다'
    except Exception as e:
        return False, str(e)[:60]


def 그려보기(쪽길):
    """크롬으로 그려 **손님이 보는 것**을 돌려줍니다.

    ★ 바깥 인터넷은 막습니다 — 판단 칸은 계산으로 나오므로
      물때 API 가 없어도 보여야 합니다(계약-23 · 1층).
      그것까지 여기서 함께 봅니다.
    """
    import subprocess
    from engine import machine
    try:
        r = subprocess.run(
            machine.크롬앞머리() + [
                '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--virtual-time-budget=9000', '--dump-dom',
                'file:///' + os.path.abspath(쪽길).replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=180)
        return r.stdout or None
    except (subprocess.TimeoutExpired, OSError):
        return None


def main():
    d = data.자료()
    보임 = '--list' in sys.argv

    print('보고 나서 판단까지 되는가 (계약-33 · 바깥 검수 11차)')
    print('  ★ **자료가 화면에 나왔다 ≠ 손님이 그것으로 결정할 수 있다**')
    print('')

    봐야할쪽 = []
    for r in d.권역들:
        길 = url.region(r['id'])
        p = os.path.join(NEW, 길.replace('/', os.sep))
        if os.path.exists(p):
            봐야할쪽.append((r, 길, p))

    if not 봐야할쪽:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        print('NOT_TESTED')
        return 2

    print('[1] 권역 쪽에 「이번 주 언제 갈까」가 있는가')

    # ★ **그려서 봐야 합니다** (2026-09-28 · 만들자마자 고침)
    #
    #   처음에는 HTML 파일만 읽었더니 57쪽 모두 「없다」고 했습니다.
    #   판단 칸은 **자바스크립트가 만듭니다.** 파일에는 없고
    #   브라우저가 그려야 생깁니다.
    #
    #   검사기가 헛것을 잡으면 진짜가 묻힙니다. 오늘만 네 번째입니다.
    #
    #   ★ 표본만 봅니다 — 57쪽을 다 그리면 몇 분이 걸립니다.
    #     쪽을 만드는 곳은 하나이므로(계약-01) 한 쪽이 되면
    #     나머지도 같습니다. 대신 **정말 그려지는지**를 봅니다.
    됨, 까닭 = 그릴수있나()
    if not 됨:
        print('  □ %s' % 까닭)
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  BADAGAJA_CHROME 으로 크롬 자리를 알려 주세요.')
        print('')
        print('NOT_TESTED')
        return 4 if '--strict' in sys.argv else 0

    볼것 = 봐야할쪽[:3] if '--all' not in sys.argv else 봐야할쪽
    print('  권역 쪽 %d개 중 %d개를 크롬으로 그려 봅니다'
          % (len(봐야할쪽), len(볼것)))
    없는쪽, 있는쪽 = [], []
    본보기 = None
    for r, 길, p in 볼것:
        원 = 그려보기(p)
        if 원 is None:
            알림.append('%s — 못 그렸습니다' % 길)
            continue
        if 판단칸있나(원):
            있는쪽.append(길)
            if 본보기 is None:
                본보기 = (길, 무엇을말하나(원))
        else:
            없는쪽.append(길)
    봐야할쪽 = 볼것

    print('  쪽 %d개 중 %d개에 있습니다' % (len(봐야할쪽), len(있는쪽)))
    if 없는쪽:
        막음.append('판단 칸이 없는 권역 쪽 %d개' % len(없는쪽))
        print('  ✗ 없는 쪽 %d개' % len(없는쪽))
        보일것 = 없는쪽[:20] if 보임 else 없는쪽[:4]
        for x in 보일것:
            print('      %s' % x)
        if len(없는쪽) > len(보일것):
            print('      … 그 밖 %d개 (--list 로 다 봅니다)'
                  % (len(없는쪽) - len(보일것)))
        print('      → 손님이 열네 칸을 훑어 스스로 고르게 둔 것입니다.')
    print('')

    print('[2] 그 칸이 무엇을 말하는가')
    if not 본보기:
        print('  - 볼 것이 없습니다')
    else:
        길, 말 = 본보기
        print('  본보기 %s' % 길)
        for 열쇠 in ('판단', '근거', '주말'):
            있나 = 열쇠 in 말 and 말[열쇠]
            print('    %s %-4s %s' % ('·' if 있나 else '✗', 열쇠,
                                      말.get(열쇠, '(없습니다)')[:56]))
        # ★ **주말을 따로 말해야 합니다** — 가장 자주 묻는 것입니다.
        if '주말' not in 말 or not 말['주말']:
            막음.append('주말 조건을 따로 말하지 않습니다')
            print('      → 주말에 갈 수 있는지가 가장 자주 묻는 것입니다.')
        if '판단' not in 말 or not 말['판단']:
            막음.append('언제 가면 좋은지 말하지 않습니다')
    print('')

    print('[3] 셈이 실제 조차를 쓰는가')
    # ★ 물때 번호로 재면 며칠 어긋납니다 — 정작 가장 많이 빠지는
    #   날에 「중간」이 붙습니다. 그래서 실제 조차로 재야 합니다.
    물때길 = os.path.join(ROOT, 'assets', 'js', 'tide.js')
    물때글 = io.read(물때길, default='')
    if not 물때글:
        알림.append('assets/js/tide.js 를 못 읽었습니다')
        print('  ~ 물때 셈을 못 읽었습니다')
    else:
        # ★ **글자가 아니라 쓰이는 곳을 봅니다** (2026-10-02)
        #   전에는 「언제갈까」라는 글자가 있기만 하면 통과했습니다.
        #   그런데 그 이름은 **함수를 짓는 줄**에도 나옵니다.
        #   판단을 화면에 붙이는 줄을 통째로 지워도 정의가 남아
        #   통과했습니다 — 「문구만 있고 기능은 없는」 바로 그 꼴입니다.
        #   **짓는 줄을 뺀 쓰임**이 있어야 판단이 사는 것입니다.
        import re as _re
        쓰임 = len(_re.findall(r'(?<!function )언제갈까\s*\(', 물때글))
        지음 = len(_re.findall(r'function\s+언제갈까\s*\(', 물때글))
        정말쓰나 = (쓰임 - 지음) >= 1
        if '조차세기' in 물때글 and 정말쓰나:
            print('  · 실제 조차로 세고, 그 값으로 판단합니다'
                  ' (언제갈까를 %d곳에서 부릅니다)' % (쓰임 - 지음))
        else:
            막음.append('판단이 실제 조차를 안 씁니다')
            print('  ✗ 실제 조차로 세지 않거나 **판단을 아무 데서도 '
                  '부르지 않습니다**')
            print('      언제갈까 — 짓는 곳 %d · 부르는 곳 %d'
                  % (지음, 쓰임 - 지음))
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림[:4]:
            print('  ~ %s' % x)
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  **보기만 하고 판단을 못 하면 반쪽입니다.**')
        print('  손님은 「그래서 언제 가야 하나」를 알고 싶어 합니다.')
        return 1 if '--strict' in sys.argv else 0

    print('보고 나서 판단까지 됩니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
