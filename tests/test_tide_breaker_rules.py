# -*- coding: utf-8 -*-
"""보호 장치 셋의 로직을 **운영 자료로** 재어 봅니다.

  PHP 가 없어 문법은 못 보지만 **고르기 규칙**은 지금 잴 수 있습니다.
  가장 두려운 것은 **아무 권역도 안 고르게 되는 것**입니다 —
  빈 날만 남은 곳을 여섯 시간 쉬게 했는데, 지금 57곳이 전부
  60일이라 **모두 쉬면 갱신이 멎습니다.** 그래도 되는지,
  의도대로인지 눈으로 확인합니다.
"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'D:\바다가자\두번째도전')
from engine import kst   # noqa: E402

DAYS = 60
빈날쉼 = 6 * 3600


def 권역들():
    import os
    칸 = r'D:\바다가자\두번째도전\data\tide'
    return sorted(n[:-5] for n in os.listdir(칸)
                  if n.endswith('.json') and not n.startswith('_'))


def 살피기(권역, 오늘키):
    try:
        req = urllib.request.Request(
            'https://badagaja.com/assets/tide/%s.json' % 권역,
            headers={'User-Agent': 'badagaja-mirror/1.0',
                     'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read().decode('utf-8'))
    except Exception:
        return None
    날 = d.get('days') or []
    키 = [x.get('date') for x in 날]
    자리 = 키.index(오늘키) if 오늘키 in 키 else -1
    if 자리 < 0:
        return None
    남 = 날[자리:]
    빈 = sum(1 for x in 남 if not (x.get('events') or []))
    return {'남은': len(남), '빈': 빈}


def 고르기(살핌, 빈날시도, 지금):
    """PHP 의 고르기 규칙을 그대로 옮긴 것."""
    고른것 = None
    건너뛴빈날 = 0
    for 이름, s in 살핌.items():
        모자람 = max(0, DAYS - s['남은'])
        if 모자람 <= 0 and s['빈'] > 0:
            언제 = 빈날시도.get(이름, 0)
            if 지금 - 언제 < 빈날쉼:
                건너뛴빈날 += 1
                continue
        아쉬움 = 모자람 * 10 + s['빈']
        if 아쉬움 <= 0:
            continue
        if 고른것 is None or 아쉬움 > 고른것['아쉬움']:
            고른것 = {'권역': 이름, '아쉬움': 아쉬움,
                      '남은': s['남은'], '빈': s['빈'],
                      '모자람': 모자람}
    return 고른것, 건너뛴빈날


오늘키 = kst.오늘키()
print('운영 57곳을 받아 고르기 규칙을 재어 봅니다 (오늘 %s)' % 오늘키)
print('=' * 60)

살핌 = {}
못읽음 = []
for n in 권역들():
    s = 살피기(n, 오늘키)
    if s is None:
        못읽음.append(n)
    else:
        살핌[n] = s
print('  읽은 곳 %d · 못 읽은 곳 %d' % (len(살핌), len(못읽음)))
모자란곳 = [n for n, s in 살핌.items() if s['남은'] < DAYS]
빈날곳 = [n for n, s in 살핌.items() if s['남은'] >= DAYS and s['빈'] > 0]
다찬곳 = [n for n, s in 살핌.items()
          if s['남은'] >= DAYS and s['빈'] == 0]
print('  날 수가 모자란 곳 %d · 빈 날만 남은 곳 %d · 다 찬 곳 %d'
      % (len(모자란곳), len(빈날곳), len(다찬곳)))
print('  빈 날 합계 %d' % sum(s['빈'] for s in 살핌.values()))
print()

지금 = 1791900000
print('① 처음 — 아무도 쉰 적 없을 때')
고른것, 건너 = 고르기(살핌, {}, 지금)
print('   고른 곳: %s' % (고른것 and '%s (남은 %d · 빈 %d · 아쉬움 %d)'
                          % (고른것['권역'], 고른것['남은'],
                             고른것['빈'], 고른것['아쉬움'])
                          or '**없음**'))
print('   빈 날 때문에 건너뛴 곳: %d' % 건너)
print()

print('② 빈 날만 남은 곳을 **모두 방금 두드렸다**면')
시도 = {n: 지금 - 60 for n in 빈날곳}
고른것2, 건너2 = 고르기(살핌, 시도, 지금)
print('   고른 곳: %s' % (고른것2 and '%s (모자람 %d)'
                          % (고른것2['권역'], 고른것2['모자람'])
                          or '**없음 — 여섯 시간 쉽니다**'))
print('   건너뛴 곳: %d' % 건너2)
print('   → %s' % ('모자란 곳이 있어 그곳으로 갑니다'
                   if 고른것2 else
                   '할 일이 없어 쉽니다 — **의도한 대로**입니다. '
                   '여섯 시간 뒤 다시 갑니다'))
print()

print('③ 여섯 시간이 지나면')
시도3 = {n: 지금 - (빈날쉼 + 60) for n in 빈날곳}
고른것3, 건너3 = 고르기(살핌, 시도3, 지금)
print('   고른 곳: %s' % (고른것3 and 고른것3['권역'] or '**없음**'))
print('   → %s' % ('다시 빈 날을 쫓습니다 — 맞습니다'
                   if 고른것3 else '★ 여섯 시간 뒤에도 안 갑니다 — 틀렸습니다'))
print()

print('④ 한 곳이 모자라면 **그곳을 먼저** 가는가 (모자람 ×10)')
흉내 = dict(살핌)
어떤곳 = sorted(살핌)[0]
흉내[어떤곳] = {'남은': 50, '빈': 0}        # 모자람 10 · 빈 0
가장빈곳 = max(살핌, key=lambda n: 살핌[n]['빈'])
print('   %s 를 50일(모자람 10·빈 0)로 두고,' % 어떤곳)
print('   빈 날이 가장 많은 곳은 %s (빈 %d)'
      % (가장빈곳, 살핌[가장빈곳]['빈']))
고른것4, _ = 고르기(흉내, {}, 지금)
print('   고른 곳: %s' % (고른것4 and 고른것4['권역']))
print('   → %s' % ('모자란 곳을 먼저 갑니다 — 맞습니다'
                   if 고른것4 and 고른것4['권역'] == 어떤곳
                   else '★ 빈 날을 먼저 갑니다 — 가중치가 모자랍니다'))
print()

print('=' * 60)
탈 = []
if not 고른것3:
    탈.append('여섯 시간 뒤에도 안 갑니다')
if 고른것4 and 고른것4['권역'] != 어떤곳:
    탈.append('모자란 곳보다 빈 날을 먼저 갑니다')
if 탈:
    for x in 탈:
        print('★ %s' % x)
    sys.exit(1)
print('★ 고르기 규칙이 뜻대로 돕니다.')
print('  · 빈 날만 남은 곳은 여섯 시간에 한 번만 갑니다')
print('  · 날 수가 모자란 곳이 **먼저** 갑니다 (모자람 ×10)')
print('  · 모두 쉬는 동안에는 **아무 호출도 하지 않습니다**')
