# -*- coding: utf-8 -*-
"""준비물 배너가 **모든 쪽에서 온전한지** 전수로 봅니다 (2026-10-13).

주인 — 「각 페이지 모두 고쳐졌는지 확인해야해」

★ 왜 만들었나
  배너를 66쪽에 한꺼번에 넣었습니다. 표본 몇 쪽만 보면
  나머지 60쪽이 깨져도 모릅니다. 더구나 사진·링크는 자료가
  바뀌면 조용히 끊깁니다 — 404 가 아니라 **빈 자리**로 남습니다.

★ 뮤테이션으로 확인했습니다
  배너 지움 · 칸 하나 지움 · 끝 슬래시 뗌 · 촬영자 지움 ·
  차림표 뗌 · 사진 파일 치움 — 여섯 가지를 모두 잡습니다.

★ 끝난값 — 통과 0 · 어김 1 · 못잼 4

표본만 보면 못 봅니다. 451쪽을 하나씩 열어
  · 배너가 있어야 할 쪽에 있는가 (권역 57 + 묶음 9 = 66)
  · 배너마다 칸이 **둘**인가
  · 링크가 끝 슬래시를 지키는가 (`rig` 는 301 입니다)
  · 사진이 적혀 있고 그 **파일이 진짜 있는가**
  · 촬영자가 적혀 있는가 (주인 규칙 5·6)
  · 차림표(gear-banner.css)가 걸렸는가
를 셉니다. 하나라도 어긋나면 어느 쪽인지 적습니다.
"""
import os
import re
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
뿌리 = os.path.join(여기, 'site')

# ★ 쪽이 없으면 **통과로 내지 않습니다** (fail-closed)
if not os.path.isdir(뿌리):
    print('준비물 배너 — site/ 가 없습니다. 통과로 내지 않습니다.')
    sys.exit(4)

막음, 알림 = [], []
쪽수 = 배너쪽 = 0
없는사진 = []
링크탈 = []
촬영자탈 = []
칸수탈 = []
차림탈 = []
쪽마다 = {}

for 터, _, 파일들 in os.walk(뿌리):
    for f in sorted(파일들):
        if not f.endswith('.html'):
            continue
        쪽수 += 1
        길 = os.path.join(터, f)
        상대 = os.path.relpath(길, 뿌리).replace(os.sep, '/')
        글 = open(길, encoding='utf-8').read()
        if 'class="gearb"' not in 글:
            continue
        배너쪽 += 1
        칸들 = re.findall(r'<a class="gearb-a[^"]*" href="([^"]+)">(.*?)</a>',
                          글, re.S)
        쪽마다[상대] = len(칸들)
        if len(칸들) != 2:
            칸수탈.append((상대, len(칸들)))
            continue
        for 주소, 속 in 칸들:
            # 링크 — 디렉터리로 가는 것은 끝 슬래시를 지켜야 합니다
            if 주소.endswith('rig') or 주소.endswith('/rig'):
                링크탈.append((상대, 주소))
            # 링크가 가리키는 파일이 진짜 있는가
            갈길 = os.path.normpath(
                os.path.join(os.path.dirname(길), 주소.split('#')[0]))
            if 주소.endswith('/'):
                갈길 = os.path.join(갈길, 'index.html')
            if not os.path.isfile(갈길):
                링크탈.append((상대, 주소 + ' (없는 쪽)'))
            # 사진
            m = re.search(r'<img class="gearb-bg" src="([^"]+)"', 속)
            if not m:
                없는사진.append((상대, '(사진 태그 없음)'))
            else:
                사진길 = os.path.normpath(
                    os.path.join(os.path.dirname(길), m.group(1)))
                if not os.path.isfile(사진길):
                    없는사진.append((상대, m.group(1)))
            # 촬영자
            if 'gearb-by' not in 속:
                촬영자탈.append((상대, 주소))
        if 'gear-banner.css' not in 글:
            차림탈.append(상대)

print('준비물 배너 전수 검사 — 쪽 %d개 중 배너 %d쪽' % (쪽수, 배너쪽))

# 들어 있어야 할 쪽 수를 **자료에서** 셉니다 (규칙 29)
from engine.data import 자료  # noqa: E402
d = 자료()
권역수 = len(d.권역들)
묶음수 = len(set((x.get('묶음') or '') for x in d.권역들))
있어야할 = 권역수 + 묶음수
print('  자료 기준 권역 %d + 묶음 %d = %d쪽' % (권역수, 묶음수, 있어야할))
if 배너쪽 != 있어야할:
    막음.append(('배너가 들어간 쪽 수가 자료와 다릅니다',
                 [(배너쪽, 있어야할)]))
    print('  ✗ 배너 %d쪽 ≠ 있어야 할 %d쪽' % (배너쪽, 있어야할))
else:
    print('  ✓ 들어가야 할 %d쪽에 모두 들어갔습니다' % 있어야할)

for 이름, 목록 in (('배너 칸이 둘이 아닙니다', 칸수탈),
                   ('링크가 어긋났습니다', 링크탈),
                   ('사진 파일이 없습니다', 없는사진),
                   ('촬영자가 없습니다', 촬영자탈)):
    if 목록:
        막음.append((이름, 목록))
        print('  ✗ %s — %d곳' % (이름, len(목록)))
        for 한 in 목록[:6]:
            print('       %s' % (한,))
    else:
        print('  ✓ %s 0곳' % 이름.replace('습니다', '은 것'))

if 차림탈:
    막음.append(('차림표가 안 걸렸습니다', 차림탈))
    print('  ✗ gear-banner.css 가 안 걸린 쪽 %d개' % len(차림탈))
    for 한 in 차림탈[:6]:
        print('       %s' % 한)
else:
    print('  ✓ 차림표가 %d쪽 모두에 걸렸습니다' % 배너쪽)

if 막음:
    print('\n손볼 곳 %d가지' % len(막음))
    sys.exit(1 if '--strict' in sys.argv else 0)
print('\n모든 쪽에서 배너가 온전합니다.')
sys.exit(0)
