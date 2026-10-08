# -*- coding: utf-8 -*-
"""**선상낚시가 새어 들어오지 않았나** (주인 규칙 10)

★ 왜 이 검사가 있나

    「낚시 포인트는 **갯바위·항구에서 직접 하는 낚시** 기준입니다.
      배 타고 나가는 선상낚시 자료는 넣지 않습니다.」 (CLAUDE.md 10)

    2026-10-09, 채비 쪽 둘에서 새어 있었습니다.

        rig/sabiki  「방파제, 갯바위, **선상** 등 모든 생활낚시에서…」
        rig/landing 「방파제·갯바위·**선상** 등 모든 낚시에서 필수…」

    자료 메모에는 「배낚시(선상) 대목은 모두 뺐습니다 — 주인 규칙 10」
    이라고 **적혀 있었습니다.** 적어 두고도 샜습니다.
    적어 두는 것으로는 못 막습니다. 기계가 봐야 합니다.

무엇을 재나 — **쪽을 봅니다. 자료를 보지 않습니다.**

    ★ 처음에는 `data/raw/*.json` 을 봤습니다. 그랬더니
      `차례근거`(「네이버 지식백과 — 붕장어 던질낚시와 배낚시」)가
      걸렸습니다. **그 칸은 쪽에 안 나갑니다.** 검사기만 읽습니다.
      「`_` 로 시작하지 않으면 쪽에 나간다」고 **짐작한 제 잘못**입니다.

      쪽에 무엇이 나갔는지는 **쪽이 압니다.** (기억: 쪽 종류는 쪽이
      말하게 · 자료 이름 모양으로 가리지 않기)

    ① 쪽 본문에 배낚시 말이 있는가
    ② 「선상낚시는 다루지 않습니다」처럼 **안 넣는다고 밝히는 글**은 뺍니다
    ③ 「S선상7호콘도」·「선상 횟집」처럼 **이름**에 든 글자는 뺍니다
    ④ 남은 것은 기준선과 견줍니다 — **새로 느는 것만 막습니다**
       (축제 프로그램의 「선상 낚시 체험」은 그 축제의 사실입니다.
        지우면 축제가 거짓이 됩니다. 알고 두는 것과 새는 것은 다릅니다)

쓰는 법
    python engine/check_boatfishing.py
    python engine/check_boatfishing.py --받아들이기     기준선 다시 깔기
"""
import io
import os
import re
import sys
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
기준길 = os.path.join(ROOT, 'tests', 'golden', '선상낚시.json')

# 배 타고 나가서 하는 낚시를 가리키는 말
배낚시말 = ('선상', '배낚시', '외줄낚시', '다운라이닝')

# 이 말이 함께 있으면 **안 넣는다고 밝히는 글**입니다 — 규칙을 지키는 쪽
밝힘말 = ('다루지 않', '싣지 않', '넣지 않', '뺐습니다', '제외', '규칙 10',
          '안 다룹니다', '다루지않')

# 낚시 방식이 아니라 **이름**에 든 글자
이름속 = ('콘도', '횟집', '펜션', '모텔', '호텔', '빌라', '아파트', '리조트')

_군더더기 = re.compile(
    r'<(script|style)\b[^>]*>.*?</\1>|<!--.*?-->', re.S | re.I)
_태그 = re.compile(r'<[^>]+>')
_빈칸 = re.compile(r'[ \t \r\n]+')


def 글만(s):
    s = _군더더기.sub(' ', s)
    s = _태그.sub(' ', s)
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&')
          .replace('&lt;', '<').replace('&gt;', '>')
          .replace('&quot;', '"').replace('&#39;', "'"))
    return _빈칸.sub(' ', s)


def 쪽하나(길):
    """걸린 자리를 (말, 앞뒤글) 로 돌려줍니다"""
    try:
        글 = 글만(io.open(길, encoding='utf-8').read())
    except Exception:
        return []
    나옴 = []
    for 말 in 배낚시말:
        i = 글.find(말)
        while i >= 0:
            앞뒤 = 글[max(0, i - 34):i + len(말) + 34]
            if not any(x in 앞뒤 for x in 밝힘말) \
               and not any(x in 앞뒤 for x in 이름속):
                나옴.append((말, 앞뒤.strip()))
            i = 글.find(말, i + 1)
    return 나옴


def 쪽들():
    것 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    return [p for p in 것 if os.path.basename(p) != '404.html']


def 재기():
    나옴 = {}
    for p in 쪽들():
        걸림 = 쪽하나(p)
        if 걸림:
            이름 = os.path.relpath(p, NEW).replace('\\', '/')
            나옴[이름] = len(걸림)
    return 나옴


def main():
    받아 = '--받아들이기' in sys.argv
    것들 = 쪽들()
    if not 것들:
        print('✗ 쪽이 없습니다 — 먼저 build 를 돌리세요')
        return 4                  # 못잼 (계약)

    이번 = 재기()
    모두 = sum(이번.values())

    if 받아:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        io.open(기준길, 'w', encoding='utf-8').write(
            json.dumps({'_왜': '주인 규칙 10 — 알고 두는 것만 적습니다. '
                               '여기 없는 쪽에 선상낚시가 생기면 막습니다',
                        '쪽': 이번},
                       ensure_ascii=False, indent=1, sort_keys=True) + '\n')
        print('기준선을 깔았습니다 — 쪽 %d개 · %d군데' % (len(이번), 모두))
        return 0

    기준 = {}
    if os.path.exists(기준길):
        기준 = (json.load(io.open(기준길, encoding='utf-8')) or {}).get('쪽', {})

    새것 = {k: v for k, v in 이번.items()
            if k not in 기준 or v > 기준[k]}
    사라짐 = [k for k in 기준 if k not in 이번]

    print('선상낚시 새어들기 — 쪽 %d개를 봤습니다 (주인 규칙 10)' % len(것들))
    print('  · 알고 두는 것 %d쪽' % len(기준))
    if 사라짐:
        print('  · 없어진 것 %d쪽 — 기준선을 다시 깔면 깔끔합니다 (%s)'
              % (len(사라짐), ', '.join(sorted(사라짐)[:3])))
    if not 새것:
        print('  ✓ 새로 샌 것 0')
        return 0

    print('  ✗ 새로 샌 것 %d쪽' % len(새것))
    for 이름 in sorted(새것)[:14]:
        for 말, 글 in 쪽하나(os.path.join(NEW, 이름))[:2]:
            print('      %s 「%s」 … %s' % (이름, 말, 글[:60]))
    print('  → 이 사이트는 갯바위·항구에서 직접 하는 낚시만 다룹니다.')
    print('    축제 프로그램처럼 **그 축제의 사실**이면')
    print('    --받아들이기 로 기준선에 넣고 까닭을 커밋에 적으세요.')
    return 1                      # 어김 (계약)


if __name__ == '__main__':
    sys.exit(main())
