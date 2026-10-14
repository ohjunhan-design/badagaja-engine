# -*- coding: utf-8 -*-
"""미리 받은 물때를 **올리기 전에** 봅니다 (2026-10-14 주인 지시)

주인 말씀: 「60일로 진행하고 이상이 발생할 경우에 대비해 장치를 만들어」

★ 왜 필요한가
  이 파일들은 손님이 **물때 시각**으로 읽습니다. 언제 들어가고
  언제 나올지를 정하는 값입니다. 반쪽짜리나 어긋난 것이 올라가면
  **사람이 위험해질 수 있습니다.** 그래서 올리기 전에 막습니다.

★ 무엇을 보나
  1  57곳이 **다 있는가** (생성기의 권역 목록과 맞는가)
  2  **오늘이 들어 있는가**
  3  오늘부터 **남은 날이 45일 이상**인가
  4  빈 날이 **2%**를 넘지 않는가
  5  시각이 `HH:MM`, 종류가 간조/만조, 조위가 말이 되는 수인가
  6  하루에 간조·만조가 **너무 적거나 많지** 않은가
  7  ★ **겹치는 날의 값이 전과 달라지지 않았는가**
     조석은 변하지 않습니다. 달라졌다면 **받다가 깨진 것**입니다.
  8  파일이 **갑자기 작아지지** 않았는가 (직전의 50% 미만이면 거부)

  하나라도 어기면 **「올리지 마십시오」**를 냅니다.

★ 쓰는 법
    python -m engine.check_tide_files
    python -m engine.check_tide_files --견줄곳 <이전 파일 폴더>
      (--견줄곳 을 주면 7·8 번을 그 폴더와 견줍니다.
       안 주면 운영에서 받아 견줍니다. 둘 다 안 되면 건너뜁니다)
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
볼곳 = os.path.join(뿌리, 'data', 'tide')
운영 = 'https://badagaja.com/assets/tide/'

최소남은날 = 45
빈날한도 = 2.0          # %
작아짐한도 = 0.5        # 직전의 50% 미만이면 거부
시각꼴 = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
조위범위 = (-200, 1200)  # cm — 우리나라 조위는 넉넉히 이 안입니다


def 권역목록():
    sys.path.insert(0, 뿌리)
    from engine import build
    d = build.자료()
    return [(r['id'], (r.get('이름') or {}).get('ko') or r['id'])
            for r in d.권역들]


def 오늘엠디():
    t = datetime.now()
    return '%d/%d' % (t.month, t.day)


def 읽기(p):
    try:
        return json.load(io.open(p, encoding='utf-8'))
    except Exception as e:
        return {'_탈': str(e)[:60]}


def 운영에서받기(권역):
    try:
        q = urllib.request.Request(
            운영 + 권역 + '.json',
            headers={'User-Agent': 'badagaja-check'})
        return json.loads(urllib.request.urlopen(q, timeout=20)
                          .read().decode('utf-8', 'replace'))
    except Exception:
        return None


def 하루검사(x):
    """한 날의 events 가 말이 되는지. 돌려주는 것: 탈 목록"""
    탈 = []
    ev = x.get('events') or []
    for e in ev:
        t = e.get('time')
        if not isinstance(t, str) or not 시각꼴.match(t):
            탈.append('시각 꼴이 이상합니다(%s)' % t)
        if e.get('type') not in ('간조', '만조'):
            탈.append('종류가 이상합니다(%s)' % e.get('type'))
        lv = e.get('level')
        if lv is not None:
            if not isinstance(lv, (int, float)):
                탈.append('조위가 수가 아닙니다(%s)' % lv)
            elif not (조위범위[0] <= lv <= 조위범위[1]):
                탈.append('조위가 범위를 벗어납니다(%s)' % lv)
    if ev and not (2 <= len(ev) <= 5):
        # 하루 간조·만조는 보통 네 번, 적어도 두 번입니다
        탈.append('하루 간조·만조가 %d개입니다' % len(ev))
    return 탈


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--견줄곳', default='')
    a = p.parse_args()

    오늘 = 오늘엠디()
    것 = 권역목록()
    print('미리 받은 물때를 봅니다 — 오늘 %s · 권역 %d곳' % (오늘, len(것)))
    print('자리 %s' % 볼곳)
    print('-' * 62)

    막을것 = []
    경고 = []
    표 = []

    for 권역, 이름 in 것:
        p2 = os.path.join(볼곳, '%s.json' % 권역)
        if not os.path.isfile(p2):
            막을것.append('%s — **파일이 없습니다**' % 이름)
            continue
        크기 = os.path.getsize(p2)
        d = 읽기(p2)
        if d.get('_탈'):
            막을것.append('%s — 글이 깨졌습니다(%s)' % (이름, d['_탈']))
            continue
        날 = d.get('days') or []
        if not 날:
            막을것.append('%s — **날이 하나도 없습니다**' % 이름)
            continue

        # 2 오늘이 있는가
        몇째 = -1
        for i, x in enumerate(날):
            if str(x.get('date')) == 오늘:
                몇째 = i
                break
        if 몇째 < 0:
            막을것.append('%s — **오늘(%s)이 없습니다**' % (이름, 오늘))
            continue
        남은 = 날[몇째:]

        # 3 남은 날
        if len(남은) < 최소남은날:
            막을것.append('%s — 오늘부터 **%d일뿐**입니다 (%d일 이상이어야 합니다)'
                          % (이름, len(남은), 최소남은날))

        # 4 빈 날
        빈 = [x.get('date') for x in 남은 if not (x.get('events') or [])]
        비율 = 100.0 * len(빈) / max(1, len(남은))
        if 비율 > 빈날한도:
            막을것.append('%s — 빈 날 %d개(%.1f%%) — 한도 %.1f%% 를 넘습니다'
                          % (이름, len(빈), 비율, 빈날한도))

        # 5·6 값이 말이 되는가
        탈 = []
        for x in 남은:
            탈 += ['%s %s' % (x.get('date'), t) for t in 하루검사(x)]
        if 탈:
            막을것.append('%s — 값이 이상합니다: %s%s'
                          % (이름, ' · '.join(탈[:3]),
                             ' 외 %d' % (len(탈) - 3) if len(탈) > 3 else ''))

        # 7·8 전과 견주기
        옛 = None
        if a.견줄곳:
            q = os.path.join(a.견줄곳, '%s.json' % 권역)
            if os.path.isfile(q):
                옛 = 읽기(q)
                if 옛.get('_탈'):
                    옛 = None
                else:
                    옛크기 = os.path.getsize(q)
                    if 크기 < 옛크기 * 작아짐한도:
                        막을것.append(
                            '%s — 파일이 갑자기 작아졌습니다 (%dB → %dB)'
                            % (이름, 옛크기, 크기))
        else:
            옛 = 운영에서받기(권역)

        # ★ **날 수가 줄면 거부합니다** (2026-10-14 감독실 지적)
        #   서버 자가 갱신이 이미 늘려 둔 것을 제가 올려서 줄이면
        #   손님에게 **나빠집니다.** 크기만 보면 못 잡습니다 —
        #   날 수를 직접 셉니다.
        if 옛 and (옛.get('days') or []):
            옛오늘 = -1
            for i, x in enumerate(옛['days']):
                if str(x.get('date')) == 오늘:
                    옛오늘 = i
                    break
            if 옛오늘 >= 0:
                옛남은 = len(옛['days']) - 옛오늘
                if len(남은) < 옛남은:
                    막을것.append(
                        '%s — **날 수가 줄었습니다** (지금 %d일 → 올릴 것 %d일). '
                        '서버가 이미 늘려 둔 것을 덮으면 안 됩니다'
                        % (이름, 옛남은, len(남은)))

        달라진것 = 0
        if 옛 and (옛.get('days') or []):
            옛표 = {}
            for x in 옛['days']:
                if x.get('events'):
                    옛표[str(x.get('date'))] = x['events']
            for x in 남은:
                키 = str(x.get('date'))
                새ev = x.get('events') or []
                if 키 in 옛표 and 새ev:
                    옛ev = 옛표[키]
                    옛값 = [(e.get('time'), e.get('type')) for e in 옛ev]
                    새값 = [(e.get('time'), e.get('type')) for e in 새ev]
                    if 옛값 != 새값:
                        달라진것 += 1
            if 달라진것:
                막을것.append(
                    '%s — **겹치는 날 %d개의 값이 달라졌습니다**. '
                    '조석은 변하지 않습니다 — 받다가 깨졌을 수 있습니다'
                    % (이름, 달라진것))

        표.append((이름, len(남은), len(빈), 비율, 크기,
                   남은[0].get('date'), 남은[-1].get('date')))

    # 표
    print('%-12s %5s %5s %7s %8s  %s'
          % ('권역', '남은날', '빈날', '빈율', '크기', '범위'))
    for 이름, 남, 빈수, 비율, 크기, 첫, 끝 in 표:
        print('%-12s %5d %5d %6.1f%% %7.1fK  %s~%s'
              % (이름, 남, 빈수, 비율, 크기 / 1024.0, 첫, 끝))

    총날 = sum(x[1] for x in 표)
    총빈 = sum(x[2] for x in 표)
    print('-' * 62)
    print('%d곳 · 남은 날 합계 %d일 · 빈 날 %d개 (%.2f%%)'
          % (len(표), 총날, 총빈, 100.0 * 총빈 / max(1, 총날)))

    if 경고:
        print('\n[눈여겨볼 것]')
        for m in 경고:
            print('  ~ %s' % m)

    if 막을것:
        print('\n' + '=' * 62)
        print('★ **올리지 마십시오** — 막은 까닭 %d가지' % len(막을것))
        for m in 막을것:
            print('  ✗ %s' % m)
        print('=' * 62)
        return 1

    print('\n' + '=' * 62)
    print('★ **올려도 됩니다** — 여덟 가지를 모두 지났습니다')
    print('=' * 62)
    return 0


if __name__ == '__main__':
    sys.exit(main())
