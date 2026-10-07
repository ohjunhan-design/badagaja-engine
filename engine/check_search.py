# -*- coding: utf-8 -*-
"""**찾을 곳도 없이 검색창을 두고 있지 않은가** (2026-10-07 주인 지적).

★ 왜 만들었나
  주인 —
    「**치명적인 오류야 물때를 검색했더니 축제가 나오고있어**」

  까닭은 자료가 아니었습니다. 첫 쪽 검색 폼이 이랬습니다 —

      <form class="g-search" action="festival/index.html" method="get">

  **무엇을 쳐도 축제 쪽으로** 갔습니다. 「이번주 물때」를 쳐서 축제가
  나온 것이 아니라, 처음부터 **축제로만** 보냈습니다.
  검색 색인도 분류도 점수 계산도 **아예 없었습니다.**

  더 나쁜 것은 생성기 주석에 제 손으로 이렇게 적혀 있었다는 것입니다 —
      「옛 쪽은 guide/?q= 로 보냈습니다. 새 틀엔 그 쪽이 없어
        지금은 **있는 쪽으로 곧장** 보냅니다」
  임시로 꽂아 두고 **찾기 쪽을 안 만들었습니다.**

★ 왜 기존 검사가 못 잡았나
      check_links      링크가 깨졌나   → 축제 쪽은 **멀쩡히 있습니다**
      check_promise    간 쪽에 내용이  → 축제 목록이 **있긴 합니다**
      check_reachable  들어갈 길이 있나 → 있습니다

  **「폼이 엉뚱한 데로 보내는가」를 재는 검사가 없었습니다.**

★ 바깥 검수가 정한 계약 (2026-10-07)
    「action 목적지는 **실제 search endpoint** 여야 함」
    「search endpoint 가 없는데 **검색폼이 존재하면 FAIL**」
    「festival/guide/travel 같은 **특정 콘텐츠 쪽을 통합 검색폼
      action 으로 쓰면 FAIL**」
    「즉, 지금 상태에서는 검색 endpoint 가 없으니 **검색폼이 없어야
      정상**입니다」

  「CSS 로만 display:none 하지 말고 **생성기에서 아예 렌더링하지 않는**
    쪽이 낫습니다. 그래야 **접근성 트리와 HTML 에도 거짓 폼이 남지
    않습니다**」 — 그래서 이 검사는 **숨겼는지**가 아니라 **있는지**를 봅니다.

검사 등급 (계약-21)
  막음 — 찾을 곳 없이 검색폼이 있습니다 / 콘텐츠 쪽을 검색 목적지로 씁니다
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('BADAGAJA_SITE') or os.path.join(ROOT, 'site')

# ★ **찾기 쪽**으로 인정하는 주소 — 여기 없으면 검색 목적지가 아닙니다
#   찾기 쪽을 만들면 그 주소를 여기 더합니다.
찾는곳 = ('search.html', 'search/', 'find.html', 'find/')

# ★ **검색 목적지로 쓰면 안 되는** 콘텐츠 쪽
#   바깥 검수 — 「festival/guide/travel 같은 특정 콘텐츠 페이지를
#   통합 검색폼 action 으로 쓰면 FAIL」
콘텐츠쪽 = ('festival', 'guide', 'travel', 'catch', 'fish', 'tide',
            'point', 'rule', 'gear')

_폼 = re.compile(r'<form[^>]*>', re.I)
_액션 = re.compile(r'action="([^"]*)"', re.I)
_클래스 = re.compile(r'class="([^"]*)"', re.I)
_검색칸 = re.compile(r'<input[^>]+type="search"', re.I)


def 검색폼인가(폼태그, 몸):
    """이 폼이 **통합 검색**을 내세우는가.

    `role="search"` 이거나 클래스에 search 가 있거나
    `<input type="search">` 를 품으면 검색폼으로 봅니다.
    """
    if 'role="search"' in 폼태그.lower():
        return True
    m = _클래스.search(폼태그)
    if m and 'search' in m.group(1).lower():
        return True
    return bool(_검색칸.search(몸))


def 찾는곳인가(간곳):
    """목적지가 **진짜 찾기 쪽**인가."""
    s = (간곳 or '').split('?')[0].split('#')[0].lstrip('./')
    s = s.rsplit('/', 1)[-1] or s
    return any(x.rstrip('/').endswith(s.rstrip('/')) or s.startswith(x)
               for x in 찾는곳)


def 콘텐츠쪽인가(간곳):
    """목적지가 **특정 콘텐츠 쪽**인가 (검색 목적지로 쓰면 안 됩니다)."""
    s = (간곳 or '').split('?')[0].split('#')[0]
    토막 = [x for x in re.split(r'[/\\]', s) if x and x != '..']
    for x in 토막:
        이름 = x.replace('.html', '')
        if 이름 in 콘텐츠쪽:
            return True
    return False


def 폼들(글):
    """(폼태그, 폼 안 몸) 목록."""
    것 = []
    for m in _폼.finditer(글):
        끝 = 글.find('</form>', m.end())
        것.append((m.group(0), 글[m.end():끝 if 끝 > 0 else m.end() + 600]))
    return 것


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('**찾을 곳도 없이 검색창을 두고 있지 않은가**')

    if not os.path.isdir(SITE):
        print('  ~ site/ 가 없습니다 — 먼저 만들어야 잽니다')
        return 0

    쪽들 = []
    for 뿌, _, 들 in os.walk(SITE):
        for 이 in 들:
            if 이.endswith('.html'):
                쪽들.append(os.path.join(뿌, 이))

    # 찾기 쪽이 있는가
    있는찾기 = [x for x in 찾는곳
                if os.path.exists(os.path.join(SITE, *x.rstrip('/').split('/')))
                or os.path.exists(os.path.join(SITE, x.rstrip('/'),
                                               'index.html'))]
    print('      쪽 %d개 · 찾기 쪽 %s'
          % (len(쪽들), ' · '.join(있는찾기) if 있는찾기 else '없음'))

    막음 = []
    거짓, 콘텐츠로 = [], []
    for 길 in 쪽들:
        쪽 = os.path.relpath(길, SITE).replace(os.sep, '/')
        글 = io.open(길, encoding='utf-8', errors='replace').read()
        for 태그, 몸 in 폼들(글):
            if not 검색폼인가(태그, 몸):
                continue
            m = _액션.search(태그)
            간곳 = m.group(1) if m else ''
            if 찾는곳인가(간곳):
                continue
            if 콘텐츠쪽인가(간곳):
                콘텐츠로.append((쪽, 간곳))
            elif not 있는찾기:
                거짓.append((쪽, 간곳))

    print('')
    print('[1] 찾을 곳이 없는데 검색폼이 있는가')
    if 거짓:
        막음.append('찾을 곳 없이 검색폼이 있는 쪽 %d개' % len(거짓))
        print('  ✗ %d개' % len(거짓))
        for 쪽, 간 in 거짓[:5]:
            print('      %-28s → %s' % (쪽, 간 or '(없음)'))
    else:
        print('  · 없습니다')

    print('')
    print('[2] 콘텐츠 쪽을 검색 목적지로 쓰고 있는가')
    if 콘텐츠로:
        막음.append('콘텐츠 쪽을 검색 목적지로 쓰는 쪽 %d개' % len(콘텐츠로))
        print('  ✗ %d개 — **입력과 상관없이 그리로만 갑니다**' % len(콘텐츠로))
        for 쪽, 간 in 콘텐츠로[:5]:
            print('      %-28s → %s' % (쪽, 간))
        print('      → 「이번주 물때」를 쳐도 그 쪽이 나옵니다.')
    else:
        print('  · 없습니다')

    print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **찾기 쪽을 만들기 전까지는 검색창을 두지 않습니다.**')
        print('    주인 지적 2026-10-07 — 「치명적인 오류야 물때를')
        print('    검색했더니 축제가 나오고있어」')
        print('    CSS 로 숨기는 것으로는 모자랍니다 — 접근성 트리와')
        print('    HTML 에 **거짓 폼이 그대로 남습니다** (바깥 검수).')
        return 1
    print('거짓 검색창이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
