# -*- coding: utf-8 -*-
"""포인트 상세 패널이 **쪽마다 제대로 걸렸는가** (2026-10-08).

★ 왜 만드나
  상세 패널을 한 쪽(여수 낚시)에서 다듬은 뒤 **114쪽 전체로**
  켰습니다. 바깥 검수가 켜 주는 조건으로 넷을 걸었습니다.

      「① 114쪽 모두 패널 JS/CSS 가 정상 연결되고 중복 ID 가 0인가
        ② 물때주소·권역이름·권역이 빠졌을 때 **거짓 숫자 없이**
           안전하게 실패하는가
        ③ 각 지역에서 「○○ 물때 자세히」의 권역명이 맞는가
        ④ 대표군만 사람 눈으로 본다」

  ①②③ 은 기계가 잽니다. 그것이 이 파일입니다.
  ④ 는 사람이 봅니다 (규칙 6-2 — 기계가 잰 것과 사람이 본 것을
  섞지 않습니다).

★ 처음 재면서 **내가 먼저 틀렸습니다 — 그 자리가 이 검사의 핵심**
  임시로 `site/point/*/*.html` 로 훑었더니 **84쪽**만 잡혔습니다.
  전남 15권역의 30쪽은 `site/point/01_sinan_fishing.html` 처럼
  **한 칸 위**에 있어 글롭이 통째로 못 봤습니다. 그 30쪽이
  빠진 채 「어김 0건, 전수 통과」가 나왔습니다.

  **못 잰 것을 통과로 세면 검사기가 거짓말을 합니다.**
  그래서 여기서는 쪽을 `io.쪽들()` 한 곳에서만 모읍니다
  (`os.walk` 라 깊이에 걸리지 않습니다).
  그리고 **쪽 수가 권역 수와 맞는지**도 함께 셉니다 — 다음에
  쪽이 통째로 안 잡히면 그 자리에서 드러나게 합니다.

★ 쪽 종류는 **쪽이 말하게 합니다** (기억 「쪽 종류는 쪽이 말하게」)
  폴더 이름·파일 이름으로 「이건 포인트 쪽」이라 가리지 않습니다.
  쪽 안의 `#쪽자료` 에 `포인트` 목록이 있으면 포인트 쪽입니다.
"""
import os
import io as _io
import re
import sys
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

막음, 알림 = [], []                 # 계약-21

# 패널이 일하려면 **넷이 다 있어야** 합니다.
#   tide-next   다음 물때까지 얼마 — 한 곳에서만 셈
#   tide-graph  compact 그래프
#   point-panel 패널 그 자체
#   point-list  목록에서 패널을 부르는 쪽
필요한자바 = ('tide-next.js', 'tide-graph.js', 'point-panel.js',
              'point-list.js')


def 쪽자료(글):
    m = re.search(
        r'<script type="application/json" id="쪽자료">(.*?)</script>',
        글, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return False            # 있는데 깨졌습니다 — 없는 것과 다릅니다


def main():
    from engine.data import 자료
    d = 자료()
    정답 = {}
    for r in d.권역들:
        이름 = (r.get('이름') or {})
        정답[r['id']] = {
            'ko': 이름.get('ko'),
            '짧은이름': r.get('짧은이름'),
        }

    쪽수 = 0
    켜진쪽 = 0
    포인트수 = 0
    권역별이름 = {}
    쪽있는권역 = set()

    for 길 in io.쪽들(NEW):
        짧 = os.path.relpath(길, NEW).replace(os.sep, '/')
        try:
            글 = _io.open(길, encoding='utf-8', errors='replace').read()
        except OSError:
            continue

        자 = 쪽자료(글)
        if 자 is False:
            막음.append('%s — #쪽자료 가 깨져 읽히지 않습니다' % 짧)
            continue
        if not 자 or not isinstance(자, dict):
            continue
        if 자.get('포인트') is None:
            continue            # 포인트 쪽이 아닙니다

        쪽수 += 1
        포인트수 += len(자.get('포인트') or [])
        켜짐 = bool(자.get('상세패널'))
        if not 켜짐:
            # 켜지 않은 쪽이 있어도 **막지 않습니다** — 스위치를
            # 한 쪽만 켜 두고 다듬는 중일 수 있습니다. 다만 알립니다.
            알림.append('%s — 상세 패널이 꺼져 있습니다' % 짧)
            continue
        켜진쪽 += 1

        # ── ① 자바스크립트가 **<script src=> 로** 정말 걸렸는가
        #    글자로만 찾으면 틀 주석에 속습니다 (check_promise 에서 배움)
        걸린자바 = set(
            re.findall(r'<script[^>]+src="[^"]*?/([A-Za-z0-9_\-]+\.js)', 글))
        for 이름 in 필요한자바:
            if 이름 not in 걸린자바:
                막음.append('%s — %s 가 안 걸렸습니다' % (짧, 이름))

        # ── ① 모양칸(CSS)
        if not re.findall(r'<link[^>]+href="[^"]*?\.css', 글):
            막음.append('%s — 차림표(css)가 하나도 안 걸렸습니다' % 짧)

        # ── ① 중복 아이디 — 패널이 틀린 칸을 집습니다
        아이디 = re.findall(r'\sid="([^"]+)"', 글)
        겹침 = sorted(k for k, v in collections.Counter(아이디).items()
                      if v > 1)
        if 겹침:
            막음.append('%s — 아이디가 겹칩니다: %s'
                        % (짧, ', '.join(겹침[:4])))

        # ── ② 필수 칸이 없으면 **거짓 숫자를 내는 대신 막습니다**
        #    패널은 물때 숫자를 보여 줍니다. 권역이 틀리면 **다른
        #    바다의 물때**를 제 것처럼 보여 주게 됩니다.
        for 칸 in ('권역', '권역이름', '물때주소', 'api'):
            if not 자.get(칸):
                막음.append('%s — 패널을 켰는데 「%s」 칸이 비었습니다'
                            % (짧, 칸))

        권역 = 자.get('권역') or ''
        이름 = 자.get('권역이름') or ''
        if 권역:
            쪽있는권역.add(권역)
            권역별이름.setdefault(권역, set()).add(이름)

        # ── ③ 단추에 그대로 적히는 이름이 자료와 맞는가
        #    point-panel.js — 「(권역이름) + ' 물때 자세히'」
        참 = 정답.get(권역)
        if 권역 and 참 is None:
            막음.append('%s — 자료에 없는 권역입니다: %s' % (짧, 권역))
        elif 참 and 이름 and 이름 not in {참['ko'], 참['짧은이름']}:
            막음.append('%s — 권역 이름이 어긋납니다: 쪽 "%s" / 자료 "%s"'
                        % (짧, 이름, 참['ko']))

        # ── ③ 물때주소가 **제 권역**을 가리키고 **그 쪽이 있는가**
        주소 = 자.get('물때주소') or ''
        if 주소:
            m = re.search(r'region=([A-Za-z0-9_\-]+)', 주소)
            if not m:
                막음.append('%s — 물때주소에 권역이 없습니다: %s'
                            % (짧, 주소))
            elif 권역 and m.group(1) != 권역:
                막음.append('%s — 물때주소가 다른 권역을 가리킵니다:'
                            ' 주소 %s / 쪽 %s' % (짧, m.group(1), 권역))
            닿 = os.path.normpath(os.path.join(
                os.path.dirname(길), 주소.split('#')[0].split('?')[0]))
            if not os.path.isfile(닿):
                # 약속한 것이 거기 있어야 합니다 (기억)
                막음.append('%s — 「물때 자세히」가 없는 쪽을 가리킵니다'
                            % 짧)

    # 한 권역을 두 이름으로 적으면 쪽마다 단추 글자가 달라집니다
    for 권역, 이름들 in sorted(권역별이름.items()):
        if len(이름들) > 1:
            막음.append('%s — 한 권역을 두 이름으로 적었습니다: %s'
                        % (권역, ' / '.join(sorted(이름들))))

    print()
    print('  포인트 상세 패널이 쪽마다 제대로 걸렸는가')
    print()
    print('  포인트 쪽 %d개 · 패널 켠 쪽 %d개 · 포인트 %d곳'
          % (쪽수, 켜진쪽, 포인트수))
    print('  쪽이 있는 권역 %d개 · 자료의 권역 %d개'
          % (len(쪽있는권역), len(정답)))

    # ★ **못 잰 것을 통과로 세지 않습니다.**
    #   처음에 글롭을 잘못 써서 전남 30쪽을 빼고 「전수 통과」를
    #   냈습니다. 쪽이 통째로 안 잡히면 여기서 드러나게 합니다.
    빠진권역 = sorted(set(정답) - 쪽있는권역)
    if 켜진쪽 and 빠진권역:
        알림.append('포인트 쪽을 못 찾은 권역 %d개: %s'
                    % (len(빠진권역), ', '.join(빠진권역[:8])))
    if 켜진쪽 and 쪽수 < len(정답):
        막음.append('포인트 쪽이 %d개뿐입니다 — 권역이 %d개인데'
                    ' 쪽을 통째로 못 본 것 같습니다'
                    % (쪽수, len(정답)))
    if not 쪽수:
        print()
        print('  □ 포인트 쪽을 하나도 못 찾았습니다 — 못 쟀습니다')
        return 4                                      # 계약 — 못 잼

    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:14]:
            print('  ✗ %s' % t)
        if len(막음) > 14:
            print('  … 그 밖 %d가지' % (len(막음) - 14))
        return 1
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:6]:
            print('  ! %s' % t)
        if len(알림) > 6:
            print('  … 그 밖 %d가지' % (len(알림) - 6))
    print('  · 패널 넷(JS)·차림표·아이디·권역 이름·물때주소가 모두'
          ' 쪽마다 맞습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
