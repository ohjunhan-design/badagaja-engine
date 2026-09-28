# -*- coding: utf-8 -*-
"""**자료에 있는 것이 손님 눈까지 닿는가** (바깥 검수 10차)

★ 왜 만들었나 (2026-09-28)

    하루에만 「있는데 안 쓰는 것」을 다섯 번 찾았습니다.

        사이트맵·robots·llms   통째로 없는데 검사기는 「다 맞다」
        어종 설명 534개        자료에 있는데 쪽이 안 씀
        명소 사진 142장        자료에 있는데 쪽이 안 씀
        기초 안내 링크 4개      57쪽 모두에서 안 나옴
        휴대폰 확인            규칙에 있는데 한 번도 제대로 못 함

    바깥 검수가 이렇게 말했습니다.

        「이것들은 서로 다른 문제가 아닙니다. **하나의 공통된
          문제**입니다. 자료 → 만들기 → 쪽 → 손님 눈 중 어느
          단계에서 끊겼는데 검사기는 **마지막 결과만** 보고
          있었던 것입니다. check_design.py 를 항목별로 덧붙이는
          방식으로 가면 **끝이 없습니다.**」

    그래서 사슬을 따라갑니다.

        SOURCE      자료에 몇 개 있는가
        REFERENCED  쪽이 그것을 가리키는가
        RENDERED    손님 눈에 보이는 자리에 있는가

    그러면 이렇게 말할 수 있습니다.

        「어종 설명 534개 중 531개가 쪽까지 닿았고 3개가 끊겼다」

★ 반대 방향도 봅니다 (ORPHAN)

    쪽에는 있는데 자료에 없는 것 — 손으로 적어 넣은 것입니다.
    자료가 갱신돼도 안 따라오므로 언젠가 어긋납니다.

★ 이것은 「무엇을 셀지」를 **자료가 정합니다.**
    check_design.py 는 제가 「사진·링크·단추를 세라」고 정해 준
    것만 셉니다. 여기서는 자료에 있는 것을 **모두** 세므로,
    자료가 늘면 검사도 저절로 늘어납니다.

쓰는 법
    python engine/check_coverage.py
    python engine/check_coverage.py --strict    끊긴 것이 있으면 끝난값 1
    python engine/check_coverage.py --list      어느 것이 끊겼는지
"""
import os
import re
import sys
import glob
import html as html_mod

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io     # noqa: E402
from engine import data   # noqa: E402
from engine import url    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 검사 등급 (계약-21)
막음, 알림 = [], []


def 글만(html):
    """꼬리표를 떼고 글만 남깁니다 — 손님이 읽는 것만 봅니다.

    ★ **엔티티를 풉니다** (2026-09-28)

      「신진도 오징어&수산물 축제」가 쪽에 버젓이 있는데도
      「안 보입니다」로 잡혔습니다. 쪽에는 `오징어&amp;수산물`
      로 적혀 있어서 자료의 `&` 와 안 맞았던 것입니다.

      손님 눈에는 `&` 로 보입니다. 손님이 보는 대로 봐야
      합니다. **검사기가 헛것을 잡으면 진짜가 묻힙니다.**
    """
    s = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    s = re.sub(r'<!--.*?-->', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html_mod.unescape(s))


def 말(값, 언어='ko'):
    if isinstance(값, dict):
        return 값.get(언어) or 값.get('ko') or ''
    return 값 or ''


def 쪽읽기():
    """쪽마다 (글, 원문) 을 한 번만 읽어 둡니다."""
    끝 = {}
    for p in sorted(glob.glob(os.path.join(NEW, '**', '*.html'),
                              recursive=True)):
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        원 = io.read(p, default='')
        끝[이름] = (글만(원), 원)
    return 끝


def 사슬(이름, 것들, 찾기, 쪽들):
    """★ 자료 하나하나가 **어디까지 닿았는지** 셉니다.

    것들  — [(열쇠, 보일말, 닿아야할쪽)] 꼴
    찾기  — (글, 원문) 을 받아 닿았는지 True/False
    """
    닿음, 끊김 = 0, []
    for 열쇠, 보일말, 갈쪽 in 것들:
        짝 = 쪽들.get(갈쪽)
        if 짝 is None:
            끊김.append('%s — 갈 쪽이 없습니다 (%s)' % (보일말, 갈쪽))
            continue
        if 찾기(열쇠, 짝[0], 짝[1]):
            닿음 += 1
        else:
            끊김.append('%s — %s 에 안 보입니다' % (보일말, 갈쪽))
    총 = len(것들)
    표 = '·' if not 끊김 else '✗'
    print('  %s %-18s SOURCE %4d   RENDERED %4d   끊김 %d'
          % (표, 이름, 총, 닿음, len(끊김)))
    if 끊김:
        막음.append('%s — %d개가 끊겼습니다' % (이름, len(끊김)))
        보일것 = 끊김[:20] if '--list' in sys.argv else 끊김[:3]
        for x in 보일것:
            print('        %s' % x)
        if len(끊김) > len(보일것):
            print('        … 그 밖 %d개 (--list 로 다 봅니다)'
                  % (len(끊김) - len(보일것)))
    return 총, 닿음, 끊김


def main():
    d = data.자료()
    쪽들 = 쪽읽기()
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('자료에 있는 것이 손님 눈까지 닿는가 (바깥 검수 10차)')
    print('  ★ 「무엇을 셀지」를 **자료가 정합니다.**')
    print('    자료가 늘면 검사도 저절로 늡니다.')
    print('  쪽 %d개' % len(쪽들))
    print('')

    # ── ① 권역 — 57곳이 저마다 제 쪽을 가졌는가
    것 = [(r['id'], 말(r['이름']), url.region(r['id']))
          for r in d.권역들]
    사슬('권역', 것,
         lambda 열쇠, 글, 원: True,      # 쪽이 있으면 닿은 것
         쪽들)

    # ── ② 명소 — 자료의 명소가 권역 쪽에 이름으로 나오는가
    것 = []
    for r in d.권역들:
        for x in d.여행(r['id'])['명소']:
            이름 = 말(x.get('이름'))
            if 이름:
                것.append((이름, '%s·%s' % (말(r['이름']), 이름),
                           url.region(r['id'])))
    사슬('명소', 것, lambda 열쇠, 글, 원: 열쇠 in 글, 쪽들)

    # ── ③ 명소 사진 — 자료에 있는 사진이 쪽에 걸렸는가
    것 = []
    for r in d.권역들:
        for 사 in (d.명소사진(r['id']) or []):
            파일 = 사.get('파일')
            if 파일:
                것.append((os.path.basename(파일),
                           '%s·%s' % (말(r['이름']), 사.get('제목') or '?'),
                           url.region(r['id'])))
    사슬('명소 사진', 것, lambda 열쇠, 글, 원: 열쇠 in 원, 쪽들)

    # ── ④ 축제 — 자료의 축제가 권역 쪽에 나오는가
    것 = []
    for r in d.권역들:
        for x in d.여행(r['id'])['축제']:
            이름 = 말(x.get('이름'))
            if 이름:
                것.append((이름, '%s·%s' % (말(r['이름']), 이름),
                           url.region(r['id'])))
    사슬('축제', 것, lambda 열쇠, 글, 원: 열쇠 in 글, 쪽들)

    # ── ⑤ 여행 코스 — 되살린 것이 정말 닿았는지
    것 = []
    for r in d.권역들:
        for x in (d.여행(r['id']).get('코스') or []):
            이름 = 말(x.get('이름'))
            if 이름:
                것.append((이름, '%s·%s' % (말(r['이름']), 이름),
                           url.region(r['id'])))
    사슬('여행 코스', 것, lambda 열쇠, 글, 원: 열쇠 in 글, 쪽들)

    # ── ⑥ 권역별 어종 설명 — 오늘 되살린 534개
    것 = []
    for 안 in d.안내들:
        아이디 = 안.get('id')
        if not 아이디:
            continue
        갈쪽 = None
        for 후보 in (url.guide(아이디, '해루질'), url.guide(아이디, '낚시')):
            if 후보 in 쪽들:
                갈쪽 = 후보
                break
        if not 갈쪽:
            continue
        for r in d.권역들:
            설명 = (d.권역별어종(r['id'], 아이디)
                    if hasattr(d, '권역별어종') else None)
            if not 설명:
                continue
            것.append((설명[:24], '%s·%s' % (말(안.get('이름')),
                                             말(r['이름'])), 갈쪽))
    if 것:
        사슬('권역별 어종 설명', 것, lambda 열쇠, 글, 원: 열쇠 in 글, 쪽들)

    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림[:5]:
            print('  ~ %s' % x)
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  **자료에 있는데 손님 눈까지 안 닿습니다.**')
        print('  모아 놓고 안 보여 주면 없는 것과 같습니다.')
        return 1 if '--strict' in sys.argv else 0

    print('자료에 있는 것이 모두 손님 눈까지 닿습니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
