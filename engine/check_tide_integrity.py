# -*- coding: utf-8 -*-
"""물때 자료가 **조석으로서 말이 되는가** 전수로 봅니다.

★ 왜 (2026-10-14 주인 요구 · 감독실 지시)
  「물때 API 수신 후 합치기할 때 오류 안 나게 관리 잘해」

  서버가 구간별로 받아 **합칩니다.** 합치기는 날짜 키로 모으는데,
  잘못되면 **날이 뒤섞이거나 빠지거나 겹칩니다.** 그런데 겉보기
  JSON 은 멀쩡해서 아무도 모릅니다. 손님은 **틀린 물때**를 보고
  갯바위에 나갑니다. 그래서 **조석으로서 말이 되는지** 봅니다.

★ 오류와 정보를 **엄격히 가릅니다**

  오류(막음) — **구조**가 어긋난 것. 합치기가 만들 수 있는 잘못.
    ① JSON·필수 칸                  읽히는가
    ② 날짜 연속성                    i번째 날 = 오늘+i (중복·건너뜀·역순)
    ③ 요일 일치                      날짜로 센 요일과 같은가
    ④ 시각 오름차순                  하루 안에서 거꾸로 가지 않는가
    ⑤ 간조·만조 **교대**             같은 종류가 잇따르지 않는가
    ⑥ 고저 역전                      만조 조위 > 인접 간조 조위

  정보(막지 않음) — **원자료 특성**일 수 있는 것.
    ⑦ 간조↔만조 시간 간격이 드문 값
    ⑧ 하루 사건 수가 0(빈 날) 또는 1
    ⑨ 조차(만조−간조)가 아주 작음

  ★ 왜 간격을 오류로 삼지 않는가 (2026-10-14)
    감독실이 13곳에서 88~102분·928~992분 간격을 찾았습니다.
    그런데 그 13곳은 **동해안 10곳 + 제주 2곳 + 울릉도**입니다.
    동해는 조차가 10~30cm 로 아주 작고 일주조 성분이 강해
    하루 사건이 2~4회로 들쑥날쑥합니다. 삼척 10/14 를 보면
    18:46 만조 29 → 23:00 간조 26 으로 **조위 차가 3cm** 입니다.
    이런 곳에서 간격이 고르기를 바라는 것은 **바다를 모르는
    기대**입니다. 그래서 **보여 드리고 사람이 가립니다** —
    기계가 못 가리는 것을 오류라 부르지 않습니다.
    [[show-dont-judge]]

쓰는 법
    python -m engine.check_tide_integrity              # 서버 57곳
    python -m engine.check_tide_integrity --자리 data/tide
    python -m engine.check_tide_integrity --권역 samcheok --자세히
    python -m engine.check_tide_integrity --대조 samcheok   # 손님 경로와
"""
import argparse
import collections
import datetime
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
서버앞 = 'https://badagaja.com/assets/tide/'
손님앞 = 'https://badagaja.com/api/tide-cache.php'

요일글 = ['월', '화', '수', '목', '금', '토', '일']

# ⑦ 흔한 간격 — 반일주조는 약 12시간 25분이니 간조↔만조는 약 372분
#   ★ **한도가 아니라 「흔한가」입니다.** 벗어나면 보여 주기만 합니다.
#   ★ 처음에 300~500분으로 좁게 잡아 **649군데**가 걸렸습니다.
#     291분·279분까지 걸리는데 그건 흔한 값입니다. 너무 많이
#     보여 주면 **아무도 안 봅니다** — 보여 주는 뜻이 사라집니다.
#     감독실이 짚은 88~102분·928~992분만 남게 넓혔습니다.
흔한간격 = (150, 700)      # 분

# ★ 사건 사이가 이보다 멀면 **끊어진 것**으로 봅니다.
#   빈 날이 하나만 있어도 간격이 하루를 넘습니다.
하루상한 = 1440            # 분


def 받기(주소, 기다림=25):
    try:
        req = urllib.request.Request(주소, headers={
            'User-Agent': 'badagaja-integrity/1.0',
            'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=기다림) as r:
            return json.loads(r.read().decode('utf-8')), None
    except urllib.error.HTTPError as e:
        return None, 'HTTP %d' % e.code
    except Exception as e:
        return None, type(e).__name__


def 분으로(글):
    """`HH:MM` → 분. 못 읽으면 None."""
    if not isinstance(글, str) or len(글) != 5 or 글[2] != ':':
        return None
    try:
        h, m = int(글[:2]), int(글[3:])
    except ValueError:
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h * 60 + m


def 날짜로(키, 해):
    """`10/14` → date. 못 읽으면 None."""
    if not isinstance(키, str) or '/' not in 키:
        return None
    try:
        달, 날 = 키.split('/')
        return datetime.date(해, int(달), int(날))
    except Exception:
        return None


def 한곳보기(권역, 자료, 오늘):
    """구조 규칙으로 봅니다. 돌려주는 것은 (오류목록, 정보목록, 셈).

    ★ 날짜에 **연도가 없습니다.** 그래서 오늘의 해로 시작해
      달이 거꾸로 가면 해를 하나 넘깁니다 — 60일은 한 해를
      넘지 못하므로 이것으로 충분합니다.
    """
    오류, 정보 = [], []
    날들 = (자료 or {}).get('days')
    if not isinstance(날들, list) or not 날들:
        return ['days 가 없거나 비었습니다'], [], {}

    # ── ② 날짜 연속성 ────────────────────────────────────
    해 = 오늘.year
    앞 = None
    날짜들 = []
    for i, x in enumerate(날들):
        키 = x.get('date')
        d = 날짜로(키, 해)
        if d is None:
            오류.append('%d번째 날짜를 못 읽습니다 (%r)' % (i, 키))
            날짜들.append(None)
            continue
        if 앞 is not None and d < 앞:
            # 해가 바뀐 것인가
            d2 = 날짜로(키, 해 + 1)
            if d2 and d2 > 앞:
                해 += 1
                d = d2
        if 앞 is not None:
            차 = (d - 앞).days
            if 차 == 0:
                오류.append('%s 가 두 번 나옵니다 (%d번째)' % (키, i))
            elif 차 < 0:
                오류.append('%s 가 앞 날(%s)보다 이릅니다 (%d번째)'
                            % (키, 앞.strftime('%m/%d'), i))
            elif 차 > 1:
                오류.append('%s 앞에서 %d일 건너뜁니다 (%d번째)'
                            % (키, 차 - 1, i))
        앞 = d
        날짜들.append(d)

        # ── ③ 요일 일치 ─────────────────────────────────
        있는요일 = x.get('day')
        맞는요일 = 요일글[d.weekday()]
        if 있는요일 and 있는요일 != 맞는요일:
            오류.append('%s 는 %s 인데 %s 로 적혀 있습니다'
                        % (키, 맞는요일, 있는요일))

    # ── 첫 날이 오늘인가 ─────────────────────────────────
    첫 = 날짜들[0] if 날짜들 else None
    if 첫 and 첫 != 오늘:
        (오류 if 첫 > 오늘 else 정보).append(
            '첫 날이 %s 입니다 (오늘은 %s)'
            % (첫.strftime('%m/%d'), 오늘.strftime('%m/%d')))

    # ── ④⑤⑥ 하루 안의 사건 ──────────────────────────────
    사건수 = collections.Counter()
    간격들 = []
    조차들 = []
    앞사건 = None        # (절대분, 종류, 조위, 날짜키)
    for x, d in zip(날들, 날짜들):
        키 = x.get('date')
        것들 = x.get('events') or []
        사건수[len(것들)] += 1
        if not 것들:
            continue
        앞분 = None
        for j, e in enumerate(것들):
            분 = 분으로(e.get('time'))
            종류 = e.get('type')
            조위 = e.get('level')
            if 분 is None:
                오류.append('%s %d번째 시각을 못 읽습니다 (%r)'
                            % (키, j, e.get('time')))
                continue
            if 종류 not in ('간조', '만조'):
                오류.append('%s %s 종류가 %r 입니다' % (키, e.get('time'), 종류))
                continue
            if not isinstance(조위, (int, float)):
                오류.append('%s %s 조위가 %r 입니다' % (키, e.get('time'), 조위))
                continue

            # ④ 시각 오름차순
            if 앞분 is not None and 분 <= 앞분:
                오류.append('%s 에서 시각이 거꾸로 갑니다 (%s)'
                            % (키, e.get('time')))
            앞분 = 분

            절대 = (d.toordinal() * 1440 + 분) if d else None
            # ★ **끊어진 자리를 넘어 비교하지 않습니다** (2026-10-14)
            #   처음에 이 가름을 안 두어 **12곳을 잘못 잡았습니다.**
            #     「11/12 23:52 와 11/15 01:10 — 만조가 잇따릅니다」
            #   11/13·11/14 가 **빈 날**이라 그 사이 사건이 없을 뿐,
            #   자료가 틀린 것이 아닙니다. 빈 날을 건너뛰고 맞대면
            #   교대도 고저도 간격도 **당연히 안 맞습니다.**
            #   없는 것을 두고 「어긋났다」고 하면 안 됩니다.
            끊김 = (앞사건 and 절대 and
                    절대 - 앞사건[0] > 하루상한)
            if 앞사건 and 절대 and not 끊김:
                앞절대, 앞종류, 앞조위, 앞키 = 앞사건
                # ⑤ 교대
                if 종류 == 앞종류:
                    오류.append('%s %s 와 %s %s — **%s 가 잇따릅니다**'
                                % (앞키, _시각(앞절대), 키, e.get('time'), 종류))
                else:
                    # ⑥ 고저 역전
                    높 = 조위 if 종류 == '만조' else 앞조위
                    낮 = 앞조위 if 종류 == '만조' else 조위
                    if 높 <= 낮:
                        오류.append('%s %s ↔ %s %s — **만조(%g)가 간조(%g)보다 낮습니다**'
                                    % (앞키, _시각(앞절대), 키, e.get('time'), 높, 낮))
                    else:
                        조차들.append(높 - 낮)
                    간격 = 절대 - 앞절대
                    간격들.append((간격, 앞키, _시각(앞절대),
                                   키, e.get('time'), 앞조위, 조위))
            if 절대:
                앞사건 = (절대, 종류, 조위, 키)

    # ── ⑦⑧⑨ 정보 ───────────────────────────────────────
    드문간격 = [g for g in 간격들
                if not (흔한간격[0] <= g[0] <= 흔한간격[1])]
    셈 = {
        '날수': len(날들),
        '사건수분포': dict(사건수),
        '간격수': len(간격들),
        '드문간격': 드문간격,
        '간격최소': min((g[0] for g in 간격들), default=None),
        '간격최대': max((g[0] for g in 간격들), default=None),
        '조차최소': min(조차들, default=None),
        '조차중간': (sorted(조차들)[len(조차들) // 2]
                     if 조차들 else None),
    }
    if 드문간격:
        정보.append('간격이 %d~%d분 밖인 곳 %d군데'
                    % (흔한간격[0], 흔한간격[1], len(드문간격)))
    빈날 = 사건수.get(0, 0)
    if 빈날:
        정보.append('빈 날 %d개' % 빈날)
    홑날 = 사건수.get(1, 0)
    if 홑날:
        정보.append('하루에 사건이 1개뿐인 날 %d개' % 홑날)
    if 셈['조차최소'] is not None and 셈['조차최소'] <= 3:
        정보.append('가장 작은 조차 %gcm — 조차가 아주 작은 바다입니다'
                    % 셈['조차최소'])
    return 오류, 정보, 셈


def _시각(절대분):
    m = 절대분 % 1440
    return '%02d:%02d' % (m // 60, m % 60)


def 권역목록():
    """권역 이름을 **자료에서** 읽습니다 — 이름을 박지 않습니다."""
    p = os.path.join(ROOT, 'data', 'festival-all.json')
    try:
        d = json.load(io.open(p, encoding='utf-8'))
        것 = sorted((d.get('regions') or {}).keys())
        if 것:
            return 것
    except Exception:
        pass
    칸 = os.path.join(ROOT, 'data', 'tide')
    if os.path.isdir(칸):
        return sorted(n[:-5] for n in os.listdir(칸)
                      if n.endswith('.json') and not n.startswith('_'))
    return []


def 대조하기(권역, 오늘):
    """정적 파일과 **손님 경로**를 맞대어 봅니다 (감독실 지시 ①).

    ★ 손님 경로(`api/tide-cache.php`)는 **합치기를 거치지 않습니다** —
      정부 API 를 불러 그대로 캐시합니다. 그래서 두 값이 같으면
      「이상 간격은 **원자료 그대로**이고 합치기가 만든 것이
      아니다」가 증명됩니다.
    """
    정, 탈1 = 받기(서버앞 + 권역 + '.json')
    손, 탈2 = 받기('%s?region=%s' % (손님앞, 권역), 기다림=60)
    if 정 is None:
        return None, '정적 파일을 못 읽습니다 (%s)' % 탈1
    if 손 is None:
        return None, '손님 경로를 못 읽습니다 (%s)' % 탈2

    def 뽑기(자료):
        것 = {}
        for x in (자료.get('days') or []):
            키 = x.get('date')
            if not 키:
                continue
            것[키] = tuple((e.get('time'), e.get('type'), e.get('level'))
                           for e in (x.get('events') or []))
        return 것

    # ★ **이상 간격이 나는 날을 콕 집어** 봅니다 (감독실 지시 ①)
    #   「141일이 다 같다」만으로는 모자랍니다 — 정작 **문제가
    #   난 날**이 그 141일 안에 있었는지 말해야 증거가 됩니다.
    _, _, 셈 = 한곳보기(권역, 정, 오늘)
    이상날 = set()
    for g in (셈.get('드문간격') or []):
        이상날.add(g[1])      # 앞 날
        이상날.add(g[3])      # 뒤 날

    a, b = 뽑기(정), 뽑기(손)
    겹침 = sorted(set(a) & set(b))
    같음, 다름, 한쪽빔 = 0, [], []
    for 키 in 겹침:
        # ★ **한쪽이 비었으면 맞댈 수 없습니다** (2026-10-14)
        #   처음에 이 가름을 안 두어 **합치기를 의심**했습니다.
        #   손님 경로가 그 날을 못 받아 비어 있었을 뿐입니다 —
        #   정부 API 는 들쑥날쑥해서 부를 때마다 다른 날이 빕니다.
        #   정적 쪽이 채워져 있는 것은 **합치기가 제 일을 한
        #   증거**이지 잘못이 아닙니다. 빈 것과 있는 것을 맞대어
        #   「다르다」고 하면 거꾸로 읽는 것입니다.
        if not a[키] or not b[키]:
            한쪽빔.append((키, len(a[키]), len(b[키])))
            continue
        if a[키] == b[키]:
            같음 += 1
        else:
            다름.append((키, a[키], b[키]))
    # 이상 간격 날 가운데 **실제로 맞댄 날**이 몇인가
    맞댄날 = {k for k in 겹침 if a[k] and b[k]}
    이상맞댐 = sorted(이상날 & 맞댄날)
    이상못맞댐 = sorted(이상날 - 맞댄날)
    return {'겹침': len(겹침), '같음': 같음, '다름': 다름,
            '한쪽빔': 한쪽빔,
            '맞댈수있던날': 같음 + len(다름),
            '이상날': sorted(이상날),
            '이상맞댐': 이상맞댐, '이상못맞댐': 이상못맞댐,
            '정적날수': len(a), '손님날수': len(b)}, None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--자리', default='',
                   help='폴더를 봅니다 (비우면 운영 서버)')
    p.add_argument('--권역', default='', help='한 곳만')
    p.add_argument('--자세히', action='store_true',
                   help='드문 간격을 낱낱이 보여 줍니다')
    p.add_argument('--대조', default='',
                   help='그 권역을 손님 경로와 맞대어 봅니다')
    p.add_argument('--strict', action='store_true')
    a = p.parse_args()

    오늘 = datetime.date.today()

    # ── 대조 모드 ────────────────────────────────────────
    if a.대조:
        print('%s — 정적 파일과 손님 경로를 맞대어 봅니다' % a.대조)
        print('=' * 62)
        것, 탈 = 대조하기(a.대조, 오늘)
        if 탈:
            print('  ✗ %s' % 탈)
            print('[한 줄 요약] 못 쟀습니다 — %s' % 탈)
            return 4
        print('  정적 %d일 · 손님 %d일 · 겹치는 날 %d일'
              % (것['정적날수'], 것['손님날수'], 것['겹침']))
        print('  그 가운데 **둘 다 채워진 날 %d일** — 같음 %d · 다름 %d'
              % (것['맞댈수있던날'], 것['같음'], len(것['다름'])))
        if 것['한쪽빔']:
            print('  한쪽이 빈 날 %d일 (맞댈 수 없습니다)'
                  % len(것['한쪽빔']))
            for 키, n1, n2 in 것['한쪽빔'][:4]:
                print('     %-7s 정적 %d개 · 손님 %d개' % (키, n1, n2))
        # ★ **정작 이상한 날**을 맞댔는가
        if 것['이상날']:
            print('  이상 간격이 난 날 %d일 가운데 **맞댄 날 %d일**'
                  % (len(것['이상날']), len(것['이상맞댐'])))
            if 것['이상맞댐']:
                print('     맞대어 같았음: %s'
                      % ' '.join(것['이상맞댐'][:10]))
            if 것['이상못맞댐']:
                print('     못 맞댐(손님이 안 줌): %s%s'
                      % (' '.join(것['이상못맞댐'][:8]),
                         ' …' if len(것['이상못맞댐']) > 8 else ''))
        else:
            print('  이상 간격이 난 날이 없습니다')
        for 키, x, y in 것['다름'][:5]:
            print('     ✗ %s' % 키)
            print('        정적 %s' % (x,))
            print('        손님 %s' % (y,))
        print('-' * 62)
        if 것['맞댈수있던날'] == 0:
            print('[한 줄 요약] 둘 다 채워진 날이 없어 못 가립니다')
            return 4
        if 것['다름']:
            print('[한 줄 요약] ✗ 맞댈 수 있던 %d일 중 **%d일이 다릅니다** — '
                  '합치기를 의심해야 합니다'
                  % (것['맞댈수있던날'], len(것['다름'])))
            return 2 if a.strict else 1
        print('[한 줄 요약] 둘 다 채워진 %d일이 **모두 같습니다** — '
              '값은 원자료 그대로입니다' % 것['맞댈수있던날'])
        return 0

    # ── 전수 보기 ────────────────────────────────────────
    곳들 = [a.권역] if a.권역 else 권역목록()
    어디 = a.자리 or '운영 서버'
    print('물때 자료가 조석으로서 말이 되는가 — %s · %d곳'
          % (어디, len(곳들)))
    print('=' * 62)

    탈난곳, 알림곳, 못읽음 = [], [], []
    전체셈 = collections.Counter()
    간격모음 = []
    for 권역 in 곳들:
        if a.자리:
            길 = os.path.join(ROOT, a.자리, 권역 + '.json')
            try:
                자료 = json.load(io.open(길, encoding='utf-8'))
            except Exception as e:
                못읽음.append('%s (%s)' % (권역, type(e).__name__))
                continue
        else:
            자료, 탈 = 받기(서버앞 + 권역 + '.json')
            if 자료 is None:
                못읽음.append('%s (%s)' % (권역, 탈))
                continue

        오류, 정보, 셈 = 한곳보기(권역, 자료, 오늘)
        전체셈['곳'] += 1
        전체셈['날'] += 셈.get('날수', 0)
        for g in 셈.get('드문간격') or []:
            간격모음.append((권역,) + g)
        if 오류:
            탈난곳.append((권역, 오류, 셈))
        elif 정보:
            알림곳.append((권역, 정보, 셈))

    if 탈난곳:
        print('  ✗ **구조가 어긋난 곳 %d곳** — 합치기를 의심합니다'
              % len(탈난곳))
        for 권역, 오류, 셈 in 탈난곳[:10]:
            print('     %-13s %d가지' % (권역, len(오류)))
            for x in 오류[:3]:
                print('        · %s' % x)
    else:
        print('  · 구조가 어긋난 곳이 **없습니다** '
              '(날짜 연속 · 요일 · 시각 차례 · 간조만조 교대 · 고저)')

    if 알림곳:
        print()
        print('  살펴볼 곳 %d곳 (막지 않습니다 — 원자료 특성일 수 있습니다)'
              % len(알림곳))
        for 권역, 정보, 셈 in 알림곳[:12]:
            print('     %-13s %-3d일  %s'
                  % (권역, 셈.get('날수', 0), ' · '.join(정보)))
        if len(알림곳) > 12:
            print('     … 그 밖 %d곳' % (len(알림곳) - 12))

    if 간격모음:
        print()
        print('  드문 간격 %d군데 (흔한 범위 %d~%d분 밖)'
              % (len(간격모음), 흔한간격[0], 흔한간격[1]))
        보여줄 = 간격모음 if a.자세히 else 간격모음[:8]
        for 권역, 분, 앞키, 앞시, 키, 시, 앞조위, 조위 in 보여줄:
            print('     %-13s %s %s → %s %s   %4d분  조위 %g→%g'
                  % (권역, 앞키, 앞시, 키, 시, 분, 앞조위, 조위))
        if not a.자세히 and len(간격모음) > 8:
            print('     … 그 밖 %d군데 (`--자세히` 로 전부)'
                  % (len(간격모음) - 8))

    if 못읽음:
        print()
        print('  못 읽은 곳 %d곳' % len(못읽음))
        for x in 못읽음[:5]:
            print('     ' + x)

    print('-' * 62)
    if 못읽음 and not 전체셈['곳']:
        print('[한 줄 요약] 한 곳도 못 읽었습니다 — 쟀다고 할 수 없습니다')
        return 4
    if 탈난곳:
        print('[한 줄 요약] ✗ %d곳의 구조가 어긋났습니다 (%d곳 · %d일 봤습니다)'
              % (len(탈난곳), 전체셈['곳'], 전체셈['날']))
        return 2 if a.strict else 1
    print('[한 줄 요약] %d곳 · %d일 — 구조는 모두 성합니다'
          % (전체셈['곳'], 전체셈['날'])
          + (' · 살펴볼 곳 %d곳' % len(알림곳) if 알림곳 else '')
          + (' · 못 읽음 %d곳' % len(못읽음) if 못읽음 else ''))
    return 4 if 못읽음 else 0


if __name__ == '__main__':
    sys.exit(main())
