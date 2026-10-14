# -*- coding: utf-8 -*-
"""서버 PHP  과 **같은 규칙**을 파이썬으로 옮겨 시험합니다.

★ 왜 거울인가 (2026-10-14)
  제 컴퓨터에 PHP 가 없어  도 못 돌립니다. 서버 PHP 는
  저장소에 두지 않습니다(관리 암호가 들어 있는 파일이라 공개
  저장소에 올릴 수 없습니다). 그래서 **문법**은 서버에 올려 봐야
  압니다.

  그러나 **로직**은 여기서 잴 수 있습니다. PHP 에 쓴 규칙을
  한 줄씩 옮겨
    ① 운영 57곳이 **통과하는가** (거짓 양성이 없는가)
    ② 일부러 망가뜨린 것을 **잡는가** (헛돌지 않는가)
  를 봅니다. ②가 없으면 ①은 아무 뜻이 없습니다 — 아무것도
  안 잡는 검증도 「전부 통과」라고 나옵니다.

★ ★ **PHP 를 고치면 이 파일도 함께 고쳐야 합니다.** ★ ★
  같은 규칙이 두 곳에 있으니 언젠가 어긋납니다. 어긋나면 이
  시험이 「운영이 막힌다」나 「못 잡는다」로 알려 줍니다 —
  그것이 이 거울을 두는 까닭입니다.

  PHP 쪽: api/tide-refresh.php 의 
          (작업 틀은 감독실 폴더에 있습니다)
"""
import copy
import datetime
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

요일글 = ['월', '화', '수', '목', '금', '토', '일']


def 조석검증(줄, 오늘):
    """PHP 쪽과 같은 규칙. 돌려주는 것은 (탈, 알림, 빈)."""
    탈, 알림, 빈 = [], [], 0
    앞날 = None
    앞끝 = None          # (종류, 조위) — 바로 이웃한 날일 때만
    for i, x in enumerate(줄):
        키 = x.get('date') or ''
        if not 키 or '/' not in 키:
            탈.append('%d번째 날짜를 못 읽습니다' % (i + 1))
            break
        바른 = 오늘 + datetime.timedelta(days=i)
        바른키 = '%d/%d' % (바른.month,바른.day)
        if 키 != 바른키:
            탈.append('%d번째가 %s 여야 하는데 %s 입니다'
                      % (i + 1, 바른키, 키))
            break
        if x.get('day'):
            바른요일 = 요일글[바른.weekday()]
            if x['day'] != 바른요일:
                탈.append('%s 는 %s 인데 %s 로 적혀 있습니다'
                          % (키, 바른요일, x['day']))
                break

        것들 = x.get('events')
        것들 = 것들 if isinstance(것들, list) else []
        수 = len(것들)
        if 수 == 0:
            빈 += 1
            앞끝 = None          # 끊김
            앞날 = 바른
            continue
        if 수 == 1:
            알림.append('%s 는 사건이 하나뿐입니다' % 키)
        if 수 > 6:
            탈.append('%s 에 사건이 %d개입니다' % (키, 수))
            break

        앞분 = None
        앞종류 = None
        앞조위 = None
        if 앞끝 is not None and 앞날 is not None \
                and (바른 - 앞날).days <= 1:
            앞종류, 앞조위 = 앞끝
        끊고나감 = False
        for e in 것들:
            t = e.get('time')
            분 = None
            if isinstance(t, str) and len(t) == 5 and t[2] == ':':
                try:
                    h, m = int(t[:2]), int(t[3:])
                    if 0 <= h <= 23 and 0 <= m <= 59:
                        분 = h * 60 + m
                except ValueError:
                    분 = None
            if 분 is None:
                탈.append('%s 의 시각 꼴이 이상합니다' % 키)
                끊고나감 = True
                break
            if 앞분 is not None and 분 <= 앞분:
                탈.append('%s 에서 시각이 거꾸로 갑니다 (%s)' % (키, t))
                끊고나감 = True
                break
            종류 = e.get('type')
            if 종류 not in ('간조', '만조'):
                탈.append('%s 의 종류가 이상합니다' % 키)
                끊고나감 = True
                break
            조위 = e.get('level')
            조위 = float(조위) if isinstance(조위, (int, float)) else None
            if 앞종류 is not None:
                if 종류 == 앞종류:
                    탈.append('%s %s — %s 가 잇따릅니다' % (키, t, 종류))
                    끊고나감 = True
                    break
                if 조위 is not None and 앞조위 is not None:
                    높 = 조위 if 종류 == '만조' else 앞조위
                    낮 = 앞조위 if 종류 == '만조' else 조위
                    if 높 <= 낮:
                        탈.append('%s %s — 만조(%g)가 간조(%g)보다 낮습니다'
                                  % (키, t, 높, 낮))
                        끊고나감 = True
                        break
            앞분, 앞종류, 앞조위 = 분, 종류, 조위
        if 끊고나감:
            break
        앞끝 = (앞종류, 앞조위)
        앞날 = 바른
    return 탈, 알림, 빈


def 권역들():
    # ★ 이름을 박지 않습니다 — 자료에서 읽습니다.
    #   (festival-all.json 은 옛 저장소 것이라 여기 없습니다)
    import os
    칸 = r'D:\바다가자\두번째도전\data\tide'
    return sorted(n[:-5] for n in os.listdir(칸)
                  if n.endswith('.json') and not n.startswith('_'))


def 받기(n):
    req = urllib.request.Request(
        'https://badagaja.com/assets/tide/%s.json' % n,
        headers={'User-Agent': 'badagaja-mirror/1.0',
                 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode('utf-8'))


오늘 = datetime.date.today()
print('① 운영 57곳이 새 검증을 통과하는가')
print('-' * 58)
잡힌곳, 못읽음, 알림수, 빈합 = [], [], 0, 0
표본 = {}
for n in 권역들():
    try:
        d = 받기(n)
    except Exception as e:
        못읽음.append('%s (%s)' % (n, type(e).__name__))
        continue
    탈, 알림, 빈 = 조석검증(d.get('days') or [], 오늘)
    알림수 += len(알림)
    빈합 += 빈
    if not 표본 and (d.get('days') or []):
        표본 = d
    if 탈:
        잡힌곳.append((n, 탈))
if 잡힌곳:
    print('   ✗ 막히는 곳 %d곳 — 서버가 갱신을 못 합니다' % len(잡힌곳))
    for n, 탈 in 잡힌곳[:8]:
        print('      %-13s %s' % (n, 탈[0]))
else:
    print('   · %d곳 모두 통과합니다 (알림 %d가지 · 빈 날 %d개)'
          % (len(권역들()) - len(못읽음), 알림수, 빈합))
if 못읽음:
    print('   못 읽은 곳 %d곳: %s' % (len(못읽음), ', '.join(못읽음[:4])))
print()

print('② 일부러 망가뜨리면 잡는가 (뮤테이션)')
print('-' * 58)
바탕 = 표본.get('days') or []
if len(바탕) < 5:
    print('   표본이 모자라 못 쟀습니다')
    sys.exit(4)


def 찬날자리(날들, 몇=2):
    것 = [i for i, x in enumerate(날들) if (x.get('events') or [])]
    return 것[:몇] if len(것) >= 몇 else 것


시험들 = []

# ㉠ 날짜를 하루 건너뜀
a = copy.deepcopy(바탕)
if len(a) > 3:
    del a[2]
시험들.append(('날을 하나 빼면', a))

# ㉠ 날짜 중복
b = copy.deepcopy(바탕)
if len(b) > 3:
    b[2] = copy.deepcopy(b[1])
시험들.append(('같은 날이 두 번이면', b))

# ㉡ 요일 틀림
c = copy.deepcopy(바탕)
c[0]['day'] = '일' if c[0].get('day') != '일' else '월'
시험들.append(('요일이 틀리면', c))

# ㉢ 시각 거꾸로
d2 = copy.deepcopy(바탕)
자리 = 찬날자리(d2, 1)
if 자리 and len(d2[자리[0]]['events']) >= 2:
    d2[자리[0]]['events'][1]['time'] = '00:01'
시험들.append(('시각이 거꾸로 가면', d2))

# ㉣ 교대 깨짐
e2 = copy.deepcopy(바탕)
자리 = 찬날자리(e2, 1)
if 자리 and len(e2[자리[0]]['events']) >= 2:
    e2[자리[0]]['events'][1]['type'] = e2[자리[0]]['events'][0]['type']
시험들.append(('간조가 잇따르면', e2))

# ㉤ 고저 역전
f2 = copy.deepcopy(바탕)
자리 = 찬날자리(f2, 1)
if 자리:
    for ev in f2[자리[0]]['events']:
        if ev.get('type') == '만조':
            ev['level'] = -150
            break
시험들.append(('만조가 간조보다 낮으면', f2))

# 꼴 깨짐
g2 = copy.deepcopy(바탕)
자리 = 찬날자리(g2, 1)
if 자리:
    g2[자리[0]]['events'][0]['time'] = '25:99'
시험들.append(('시각 꼴이 깨지면', g2))

모두잡았나 = True
for 이름, 자료 in 시험들:
    탈, _, _ = 조석검증(자료, 오늘)
    잡힘 = bool(탈)
    if not 잡힘:
        모두잡았나 = False
    print('   %-22s %s%s'
          % (이름, '잡습니다' if 잡힘 else '★ 못 잡습니다',
             ('  (%s)' % 탈[0][:46]) if 탈 else ''))

print()
print('=' * 58)
if 잡힌곳:
    print('★ 운영 자료가 막힙니다 — 검증이 너무 엄격합니다. 고쳐야 합니다.')
    sys.exit(1)
if not 모두잡았나:
    print('★ 못 잡는 것이 있습니다 — 검증이 헛돕니다.')
    sys.exit(1)
print('★ 운영 자료는 **통과하고**, 망가뜨린 것은 **모두 잡습니다.**')
print('  PHP 문법은 서버에 올려 봐야 압니다 — 감독실이 올린 직후')
print('  응답 코드와 status=1 을 봐 주셔야 합니다.')
