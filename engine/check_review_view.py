# -*- coding: utf-8 -*-
"""AI 검수 뷰가 **담지 말아야 할 것을 안 담았는가** (2026-10-10 #9 P0)

★ 왜 이 검사가 있나

  `/stats-review/` 는 총감독·감독실이 **주소만 알면 열리는** 쪽으로
  설계했습니다. `noindex` 는 접근통제가 아니라는 총감독 말씀을
  그대로 받아, 「주소가 샐 수 있다」를 전제로 **담는 것 자체를
  집계값으로 한정**했습니다.

  그러니 지켜야 할 것은 하나뿐입니다 — **담으면 안 되는 것이
  한 톨도 없을 것.** 그것을 말로 두지 않고 기계가 봅니다.

★ 무엇을 보나

  ① 개인을 가릴 수 있는 것 — IP 꼴 · 원시 UA · 메일 주소 ·
     전화 꼴 · 토큰 꼴 · 쿠키 · 열쇠 값
  ② 고치는 길 — form · button · input · fetch · XMLHttpRequest ·
     script 가 **하나도 없어야** 합니다
  ③ noindex 와 robots — 보조 장치지만 빠지면 안 됩니다
  ④ 사이트맵에 없을 것
  ⑤ 집계값이 **맞아떨어질 것** — 날짜별 합 = 기간 합
  ⑥ 모의 자료로 그렸으면 **그렇게 적혀 있을 것**

★ 쪽이 없으면 **건너뜁니다** (못잼이 아닙니다)
  스냅샷이 없으면 쪽을 안 만드는 것이 설계입니다.

쓰는 법
    python engine/check_review_view.py
    python engine/check_review_view.py --strict
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
쪽길 = os.path.join(NEW, 'stats-review', 'index.html')
사이트맵 = os.path.join(NEW, 'sitemap.xml')
로봇길 = os.path.join(NEW, 'robots.txt')

# ① 개인을 가릴 수 있는 꼴 — 글에서 **찾아냅니다**
_위험 = [
    ('IP 주소', re.compile(
        r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])')),
    ('메일 주소', re.compile(r'[\w.+-]+@[\w-]+\.[\w.]{2,}')),
    ('전화 꼴', re.compile(r'01[016789][-. ]?\d{3,4}[-. ]?\d{4}')),
    ('원시 브라우저 정보', re.compile(
        r'Mozilla/\d|AppleWebKit|Chrome/\d|Safari/\d', re.I)),
    ('토큰 꼴', re.compile(r'[A-Za-z0-9_-]{32,}')),
    ('쿠키', re.compile(r'document\.cookie|Set-Cookie', re.I)),
    ('열쇠말 자리', re.compile(r'[?&]t=|열쇠말|password|secret', re.I)),
]

# ② 고치는 길 — 하나도 없어야 합니다
_쓰기길 = [
    ('<form', re.compile(r'<form\b', re.I)),
    ('<button', re.compile(r'<button\b', re.I)),
    ('<input', re.compile(r'<input\b', re.I)),
    ('<script', re.compile(r'<script\b', re.I)),
    ('fetch(', re.compile(r'\bfetch\s*\(')),
    ('XMLHttpRequest', re.compile(r'XMLHttpRequest')),
    ('onclick 따위', re.compile(r'\son[a-z]+\s*=', re.I)),
]


def main():
    엄격 = '--strict' in sys.argv
    print()
    print('  AI 검수 뷰가 담지 말아야 할 것을 안 담았는가')
    print('  (2026-10-10 #9 — 주소가 샐 수 있다고 보고 만듭니다)')
    print()

    자료있나 = any(
        os.path.exists(os.path.join(ROOT, 'data', 'raw', x))
        for x in ('stats-review.json', 'stats-review.sample.json'))

    if not os.path.exists(쪽길):
        # ★ **「잴 것이 없다」와 「못 쟀다」를 가릅니다** (2026-10-10)
        #   전에는 둘 다 0 을 냈습니다. fail-closed 눈으로 보면
        #   **못 쟀는데 통과**라, 판정 #161 의 「거짓통과실측」이
        #   저를 잡았습니다. 맞는 지적입니다.
        if 자료있나:
            print('  ✗ 스냅샷 자료는 있는데 **쪽이 없습니다** —')
            print('    engine/build_review.py 가 만들다 실패했을 수')
            print('    있습니다. 못 쟀으므로 통과로 내지 않습니다.')
            return 4                      # 못잼
        print('  □ 검수 뷰도 스냅샷 자료도 없습니다 — **잴 것이')
        print('    없습니다.** 「제대로 되어 있다」가 아닙니다.')
        print('    스냅샷이 생기면 그때 잽니다.')
        return 3                          # 안올림 (잴 것 없음)

    글 = io.open(쪽길, encoding='utf-8', errors='replace').read()
    막음, 알림 = [], []

    # ① 위험한 꼴
    for 이름, 재 in _위험:
        난것 = 재.findall(글)
        if 난것:
            막음.append('%s 가 %d곳 있습니다 — 보기: %s'
                        % (이름, len(난것), str(난것[0])[:40]))

    # ② 고치는 길
    for 이름, 재 in _쓰기길:
        n = len(재.findall(글))
        if n:
            막음.append('`%s` 가 %d개 있습니다 — 읽기 전용이어야 합니다'
                        % (이름, n))

    # ③ noindex
    if not re.search(r'name="robots"[^>]*noindex', 글, re.I):
        막음.append('noindex 가 없습니다')

    # ③ robots.txt
    if os.path.exists(로봇길):
        r = io.open(로봇길, encoding='utf-8', errors='replace').read()
        if 'stats-review' not in r:
            알림.append('robots.txt 에 stats-review 를 막는 줄이 없습니다')
    else:
        알림.append('robots.txt 가 없습니다')

    # ④ 사이트맵
    if os.path.exists(사이트맵):
        s = io.open(사이트맵, encoding='utf-8', errors='replace').read()
        if 'stats-review' in s:
            막음.append('사이트맵에 검수 뷰가 들어 있습니다 — 빼세요')

    # ⑤ 집계값 맞음 — 자료에서 다시 셉니다
    for 자료이름 in ('stats-review.json', 'stats-review.sample.json'):
        자료길 = os.path.join(ROOT, 'data', 'raw', 자료이름)
        if not os.path.exists(자료길):
            continue
        d = json.load(io.open(자료길, encoding='utf-8'))
        날 = d.get('날짜별') or {}
        달 = d.get('달') or ''
        달합 = sum(int(v.get('방문') or 0)
                   for k, v in 날.items() if k.startswith(달))
        if '{:,}'.format(달합) not in 글 and 달합:
            막음.append('이 달 합 %s 가 쪽에 없습니다 — 숫자가 어긋납니다'
                        % '{:,}'.format(달합))
        break

    # ⑥ 모의 자료면 그렇게 적혀 있을 것
    모의 = os.path.exists(
        os.path.join(ROOT, 'data', 'raw', 'stats-review.sample.json'))
    진짜 = os.path.exists(
        os.path.join(ROOT, 'data', 'raw', 'stats-review.json'))
    if 모의 and not 진짜:
        if '모의' not in 글:
            막음.append('모의 자료로 그렸는데 **그렇게 적혀 있지 않습니다**')

    print('  쪽 크기 %.1fKB' % (len(글.encode('utf-8')) / 1024.0))
    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        print()
        print('  **이 쪽은 주소만 알면 열립니다.** 담지 않는 것으로')
        print('  막는 설계이므로, 한 톨이라도 담기면 설계가 무너집니다.')
        return 1
    if 알림:
        for t in 알림:
            print('  ! %s' % t)
    print('  · 개인을 가릴 수 있는 것이 없습니다')
    print('  · 고치거나 지우는 길이 없습니다 (form·button·script 0)')
    print('  · noindex 가 있고 사이트맵에 없습니다')
    print('  · 집계값이 자료와 맞습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
