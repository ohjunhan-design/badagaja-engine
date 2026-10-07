# -*- coding: utf-8 -*-
"""**만들어 놓고 들어갈 길이 없는 쪽**이 있는가 (2026-10-07 주인 지적).

★ 왜 만들었나
  주인이 첫 쪽 그림에 동그라미를 치고 —
    「너희 이것도 확인해 **이거 링크 없어**」

      <a href="#bada">향토 먹거리 · 명소</a>

  `#bada` 는 **같은 쪽 안 닻**입니다. 누르면 제자리로 갑니다.
  `travel/`(바다 여행)이 바로 그 내용인데, 2026-10-01 에 쪽을
  만들고도 **첫 쪽에서 안 걸었습니다.**

  고치면서 같은 것을 하나 더 찾았습니다 —
      `data.html` 「가진 자료」 20.4KB — **아무 쪽도 안 걸고**
      있었습니다. 검색엔진에는 열려 있는데 손님은 영영 못 봅니다.

★ 왜 기존 검사가 못 잡았나
      check_links     링크가 **깨졌나**를 봅니다 — 안 깨졌습니다
      check_manifest  쪽이 **있나**를 봅니다 — 있습니다
      check_promise   간 쪽에 **내용이 있나**를 봅니다 — 아예 안 갑니다

  **「만들어 놓고 아무도 안 거는가」를 재는 검사가 없었습니다.**

★ 끝 슬래시에 속지 않습니다
  처음 재었을 때 `guide/index.html` 도 고아로 나왔습니다. **틀렸습니다.**
  `url.rel()` 이 `guide/` 를 **`guide`** 로 줄여 내보내는데 제 셈법이
  그것을 쪽으로 안 봤습니다. 끝 슬래시가 없어도 폴더 쪽으로 봅니다.

★ 검색에 숨긴 쪽은 뺍니다
  `stats.html` 은 `noindex,nofollow` 가 붙은 **운영자용**입니다.
  안 걸리는 것이 **의도한 것**이라 잡지 않습니다.

══════════════════════════════════════════════════════════
★ **판정 핵심은 순수 함수로 떼어 둡니다** (2026-10-07 바깥 검수)

  처음에는 모든 논리를 `main()` 안에 넣고, 시험은 **진짜 site/
  449쪽을 복사해** 링크를 끊는 식으로 만들었습니다.
  **네 번 깨졌습니다** — 그런데 깨진 데가 전부 「사본 만들기」와
  「정규식 꼴 맞추기」였고, **검사 논리는 한 줄도 안 건드렸습니다.**

  바깥 검수 —
    「지금 네 번 깨진 것도 check_reachable 의 **논리가 틀린 게
      아니라 시험 준비 과정이 복잡해서** 깨진 것입니다」
    「핵심 논리를 main() 에서 떼세요 … 그러면 시험은 아주 작게
      만들 수 있습니다」
    「지금 방식은 **실사이트 복사와 정규식이 잘 되느냐**를 시험하고
      있었지, 검사기 핵심 논리를 제대로 겨냥하지 못했습니다」

  그래서 이렇게 나눕니다 —

      어느쪽()        주소 한 개 → 쪽 이름        (순수)
      링크그래프()     {쪽: 글} → 나감·걸린곳      (순수)
      닿는걸음()       그래프 → {쪽: 걸음}         (순수)
      고아들()        위 셋을 엮어 → 고아·못닿음   (순수)
      main()          site/ 를 읽고 · 출력하고 · 끝난값을 냅니다

  단위시험은 **작은 가짜 입력**으로 몇 밀리초에 끝나고,
  통합시험은 **작은 가짜 사이트 한 벌**로 CLI 를 한 번만 돕니다.

검사 등급 (계약-21)
  막음 — 검색에 열어 두고 **들어갈 길이 없는 쪽**이 있습니다
  알림 — 첫 쪽에서 **네 걸음보다 먼** 쪽 (손님이 못 찾습니다)
"""
import io
import os
import re
import sys
from urllib.parse import urljoin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('BADAGAJA_SITE') or os.path.join(ROOT, 'site')

# ★ 첫 쪽에서 이보다 멀면 손님이 못 찾습니다 — 알림입니다
먼걸음 = 4
첫쪽 = 'index.html'

_닫음 = re.compile(r'name="robots"\s+content="[^"]*noindex', re.I)
_고리 = re.compile(r'href="([^"#?]+)')
_바깥 = ('http', 'mailto', 'tel', 'javascript', '//', 'data:')


# ══════════════════════════════════════════════════════
#  판정 핵심 — **순수 함수**입니다 (파일도 환경도 안 봅니다)
# ══════════════════════════════════════════════════════
def 어느쪽(간, 쪽집합):
    """주소가 가리키는 쪽 — **끝 슬래시가 없어도** 폴더로 봅니다.

    `url.rel()` 이 `guide/` 를 `guide` 로 줄여 내보냅니다.
    그것을 쪽으로 안 보면 **멀쩡한 쪽을 고아라고** 잘못 잡습니다.
    """
    간 = (간 or '').lstrip('/')
    if 간 in 쪽집합:
        return 간
    for 꼴 in (간.rstrip('/') + '/index.html', 간 + 'index.html'):
        if 꼴 in 쪽집합:
            return 꼴
    return None


def 링크그래프(쪽글들):
    """{쪽: 글} → (나감, 걸린곳).

    나감   {쪽: 그 쪽이 거는 쪽들}
    걸린곳 {쪽: 그 쪽을 거는 쪽들}
    """
    쪽집합 = set(쪽글들)
    나감, 걸린곳 = {}, {}
    for 쪽 in sorted(쪽글들):
        for m in _고리.finditer(쪽글들[쪽] or ''):
            a = m.group(1)
            if a.startswith(_바깥):
                continue
            간 = 어느쪽(urljoin('/' + 쪽, a), 쪽집합)
            if 간 and 간 != 쪽:
                나감.setdefault(쪽, set()).add(간)
                걸린곳.setdefault(간, set()).add(쪽)
    return 나감, 걸린곳


def 닿는걸음(나감, 시작=첫쪽):
    """{쪽: 시작에서 몇 걸음} — 너비 우선입니다."""
    닿음, 줄 = {시작: 0}, [시작]
    while 줄:
        이번 = 줄.pop(0)
        for 다음 in sorted(나감.get(이번, ())):
            if 다음 not in 닿음:
                닿음[다음] = 닿음[이번] + 1
                줄.append(다음)
    return 닿음


def 숨긴쪽들(쪽글들):
    """검색에 숨긴 쪽 — 안 걸리는 것이 **의도한 것**이라 뺍니다."""
    return {쪽 for 쪽, 글 in 쪽글들.items() if _닫음.search(글 or '')}


def 고아들(쪽글들, 시작=첫쪽):
    """**판정 한 덩이** — (고아, 못닿음, 먼것, 닿음, 걸린곳).

    고아   아무 쪽도 안 거는 쪽
    못닿음 걸려 있어도 시작에서 가는 길이 없는 쪽
    먼것   시작에서 `먼걸음` 보다 먼 쪽 [(걸음, 쪽), …]
    """
    나감, 걸린곳 = 링크그래프(쪽글들)
    닿음 = 닿는걸음(나감, 시작)
    숨김 = 숨긴쪽들(쪽글들)
    볼것 = [x for x in sorted(쪽글들) if x != 시작 and x not in 숨김]
    고아 = [x for x in 볼것 if x not in 걸린곳]
    못닿음 = [x for x in 볼것 if x not in 닿음]
    먼것 = sorted((v, k) for k, v in 닿음.items() if v > 먼걸음)
    return 고아, 못닿음, 먼것, 닿음, 걸린곳


# ══════════════════════════════════════════════════════
#  여기부터는 **파일을 읽고 사람에게 말합니다**
# ══════════════════════════════════════════════════════
def _읽어오기(밭):
    """{쪽: 글} — site/ 의 모든 html."""
    것 = {}
    for 뿌, _, 들 in os.walk(밭):
        for 이 in 들:
            if not 이.endswith('.html'):
                continue
            길 = os.path.join(뿌, 이)
            쪽 = os.path.relpath(길, 밭).replace(os.sep, '/')
            것[쪽] = io.open(길, encoding='utf-8', errors='replace').read()
    return 것


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('**만들어 놓고 들어갈 길이 없는 쪽**이 있는가')

    if not os.path.isdir(SITE):
        print('  ~ site/ 가 없습니다 — 먼저 만들어야 잽니다')
        return 0

    쪽글들 = _읽어오기(SITE)
    if 첫쪽 not in 쪽글들:
        print('  ~ 첫 쪽이 없습니다 — 건너뜁니다')
        return 0

    고아, 못닿음, 먼것, 닿음, 걸린곳 = 고아들(쪽글들)
    숨김 = 숨긴쪽들(쪽글들)
    막음, 알림 = [], []

    print('      쪽 %d개 · 검색에 숨긴 쪽 %d개' % (len(쪽글들), len(숨김)))

    print('')
    print('[1] 아무 쪽도 안 거는 쪽이 있는가')
    if 고아:
        막음.append('아무 쪽도 안 거는 쪽 %d개' % len(고아))
        print('  ✗ %d개 — **만들어 놓고 들어갈 길이 없습니다**' % len(고아))
        for x in 고아[:8]:
            print('      %s' % x)
        print('      → 검색엔진에는 열려 있는데 **손님은 영영 못 봅니다.**')
        print('        꼬리말·안내 단추·묶음 쪽 가운데 맞는 자리에 겁니다.')
    else:
        print('  · 모든 쪽에 들어갈 길이 있습니다')

    print('')
    print('[2] 첫 쪽에서 못 닿는 쪽이 있는가')
    if 못닿음:
        막음.append('첫 쪽에서 못 닿는 쪽 %d개' % len(못닿음))
        print('  ✗ %d개 — 걸려 있어도 **첫 쪽에서 가는 길이 없습니다**'
              % len(못닿음))
        for x in 못닿음[:8]:
            print('      %-34s (거는 쪽 %s)'
                  % (x, ' · '.join(sorted(걸린곳.get(x, ()))[:2]) or '없음'))
    else:
        print('  · 모든 쪽이 첫 쪽에서 닿습니다')

    print('')
    print('[3] 너무 먼 쪽이 있는가 (%d걸음 넘음)' % 먼걸음)
    if 먼것:
        알림.append('첫 쪽에서 %d걸음 넘는 쪽 %d개' % (먼걸음, len(먼것)))
        print('  ~ %d개' % len(먼것))
        for v, k in 먼것[:6]:
            print('      %2d걸음  %s' % (v, k))
    else:
        print('  · 가장 먼 쪽도 %d걸음입니다'
              % (max(닿음.values()) if 닿음 else 0))

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
        print('')
        print('  ★ **쪽을 만든 것과 손님이 거기 가는 것은 다릅니다.**')
        print('    2026-10-07 주인 지적 — 「이거 링크 없어」')
        return 1
    print('만든 쪽에 모두 들어갈 길이 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
