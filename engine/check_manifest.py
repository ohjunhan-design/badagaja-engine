# -*- coding: utf-8 -*-
"""검사 — **쪽이 거는 모든 주소를 build 가 만드는가** (2026-10-01).

★ 왜 — 끊긴 쪽을 **여덟 번** 찾았습니다
  하루 사이에 이렇게 나왔습니다 —

      rule.html · gear.html · tide/ · guide/        (어제 넷)
      about · sources · privacy · photos            (오늘 넷)
      fish/basics · catch/basics · muldae           (오늘 셋)
      data.html                                     (오늘 하나, 여덟 번째)

  모두 같은 모양이었습니다. **쪽이 거는데 build 가 안 만들고,
  서버에 남은 옛 파일이 200 을 내는 것**입니다. 손님이 누르면
  디자인이 통째로 다른 쪽으로 떨어지고, 거기 적힌 숫자는 낡았습니다.

★ 바깥 검수 지시 (2026-10-01)
  「단순히 data.html 하나를 추가하는 데서 끝내지 말고, 현재 446쪽이
    내부에서 링크하는 **모든 .html 대상이 manifest 에 존재하는지
    자동 검사**를 한 번 돌리세요. 또 **아홉 번째가 서버에 숨어 있는
    일**을 막는 게 중요합니다」

  그리고 그 전에 이렇게도 말했습니다 —
  「**keep.json 에 있다는 이유만으로 통과시키는 것도 금지**합니다.
    preserve 에는 '새 사이트에 남겨야 하는가' 가 명시되어야 합니다.
    **사용자에게 보이는 HTML 페이지는 원칙적으로 legacy preserve
    대상에서 제거하는 방향**으로 가겠습니다. api/·서버 설정류만
    의도적으로 공유하는 자원과 예전 HTML 문서는 성격이 전혀 다릅니다」

  맞는 말입니다. 제가 `keep.json` 에 「새 틀은 아직 안 만듭니다」라고
  적어 두어 **검사기가 통과시킨 것**이 바로 fish/basics 였습니다.

★ 그래서 이 검사는 **keep.json 을 핑계로 받아 주지 않습니다.**
  손님이 눌러서 가는 **.html 쪽**은 build 가 만들어야 합니다.
  나눠 주는 자원(api/ · css/ · 중국어판)은 따로 봅니다.

★ 막음입니다. 아홉 번째를 여기서 끊습니다.
"""
import os
import re
import sys


여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
from engine import mustmeasure   # noqa: E402
쪽밭 = os.environ.get('BADAGAJA_SITE') or os.path.join(여기, 'site')

# ★ **일부러 옛것으로 두는 것** — 손님이 보는 한국어 쪽이 아닙니다
#   · zh-cn/ : 중국어판 190쪽은 옛 틀 그대로 두기로 주인이 정했습니다
#   · api/   : 물때 자료를 받는 곳. 새 틀도 그대로 씁니다
#   이 둘 말고 **.html 쪽은 모두 build 가 만들어야 합니다.**
봐주는앞머리 = ('zh-cn/', 'api/')

_링크 = re.compile(r'(?:href|src)="([^"#?]+)"')


# ── 검사 등급 (계약-21) ──────────────────────────────
#   막는 것과 알리는 것을 **따로 모읍니다.**
막음, 알림 = [], []

def _자료칸():
    """자료가 있는 자리.

    ★ **시험이 주는 사본을 봅니다** (2026-10-02 판정 [2])
      박아 두면 검사기 자기검증이 자료를 망가뜨려도 **멀쩡한 진짜
      자료**를 재고 「탈 없다」고 합니다. 잡는 척하는 검사기는
      없는 것보다 나쁩니다.
    """
    return os.environ.get('BADAGAJA_DATA', os.path.join(여기, 'data'))



def 쪽들():
    for 뿌리, _, 파일들 in os.walk(쪽밭):
        for 이름 in 파일들:
            if not 이름.endswith('.html') or 이름.startswith('__'):
                continue
            길 = os.path.join(뿌리, 이름)
            try:
                글 = open(길, encoding='utf-8').read()
            except OSError:
                continue
            yield os.path.relpath(길, 쪽밭).replace('\\', '/'), 글


def 풀기(쪽, 주소):
    """상대 주소를 site/ 기준 길로."""
    if 주소.startswith(('http://', 'https://', 'mailto:', 'tel:',
                        'data:', '//')):
        return None
    집 = os.path.dirname(쪽)
    길 = os.path.normpath(os.path.join(집, 주소)).replace('\\', '/')
    if 길.startswith('..'):
        return None
    # ★ `href="./"` 는 **첫 쪽**입니다 (2026-10-01)
    #   normpath 가 `.` 으로 만듭니다. 그대로 두면 `./index.html` 이
    #   되어 **445쪽이 끊긴 것처럼** 보였습니다. 제 검사의 버그였고,
    #   쪽은 멀쩡했습니다. 검사기가 틀린 것을 쪽 탓으로 돌리면
    #   없는 잘못을 고치게 됩니다.
    if 길 in ('.', ''):
        return 'index.html'
    if 길.endswith('/'):
        길 += 'index.html'
    elif not os.path.splitext(길)[1]:
        길 = 길.rstrip('/') + '/index.html'
    return 길


def main():
    만든것 = {쪽 for 쪽, _글 in 쪽들()}
    # ★ 쪽이 0개면 「없는 주소 0곳」이라 통과였습니다 (2026-10-08)
    mustmeasure.있어야한다(만든것, '쪽', 최소=50, 어디=쪽밭)
    print('[1] 쪽이 거는 .html 주소를 build 가 모두 만드는가')
    print('      만든 쪽 %d개' % len(만든것))

    없는것 = {}
    for 쪽, 글 in 쪽들():
        for 주 in set(_링크.findall(글)):
            길 = 풀기(쪽, 주)
            if not 길 or not 길.endswith('.html'):
                continue
            if any(길.startswith(p) for p in 봐주는앞머리):
                continue
            if 길 in 만든것:
                continue
            없는것.setdefault(길, set()).add(쪽)

    if 없는것:
        막음.append('build 가 안 만드는 .html 주소 %d갈래' % len(없는것))
        print('  ✗ build 가 안 만드는데 쪽이 거는 주소 %d갈래'
              % len(없는것))
        for 길, 거는곳 in sorted(없는것.items(),
                                 key=lambda t: -len(t[1]))[:10]:
            print('      %-28s %d곳이 겁니다' % (길, len(거는곳)))
            print('          예: %s' % ' · '.join(sorted(거는곳)[:3]))
        print()
        print('      ★ 서버가 200 을 내도 **성한 것이 아닙니다.**')
        print('        옛 사이트 파일이 남아 응답하는 것일 수 있습니다.')
        print('        지금까지 이렇게 **여덟 번** 끊겨 있었습니다.')
        print('        keep.json 에 적혀 있어도 봐주지 않습니다 —')
        print('        손님이 보는 .html 쪽은 build 가 만들어야 합니다.')
    else:
        print('  · 쪽이 거는 .html 주소를 build 가 모두 만듭니다')
    print('')

    # ── [2] keep.json 이 손님용 .html 을 감싸고 있지 않은가
    print('[2] 남길 것 목록에 **손님이 보는 한국어 쪽**이 있는가')
    from engine import io as _io
    남길것 = (_io.read_json(
        os.path.join(_자료칸(), 'raw', 'keep.json'),
        default={}).get('남길것') or {})
    감싼것 = []
    for 길 in 남길것:
        if 길.startswith('_') or not 길.endswith('.html'):
            continue
        if any(길.startswith(p) for p in 봐주는앞머리):
            continue
        if 길 in 만든것:
            continue          # build 가 만들면 괜찮습니다
        감싼것.append(길)
    if 감싼것:
        알림.append('남길 것에 아직 안 만드는 한국어 쪽 %d개' % len(감싼것))
        print('  ~ build 가 안 만드는데 남길 것에 적힌 쪽 %d개'
              % len(감싼것))
        for 길 in 감싼것[:8]:
            print('      %s' % 길)
        print('      → 손님이 보는 쪽이면 **build 가 만들어야** 합니다.')
    else:
        print('  · 남길 것 목록에 안 만드는 한국어 쪽이 없습니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1
    print('쪽이 가리키는 곳을 build 가 모두 만듭니다 — 아홉 번째는 '
          '없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
