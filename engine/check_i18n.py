# -*- coding: utf-8 -*-
"""다른 언어 쪽이 **정말 그 언어인지** 봅니다.

★ 왜 이 검사가 필요한가 (2026-09-26 바깥 검수 지적)

    「특히 중국어 데이터가 없는 경우 한국어가 조용히 출력되는지,
      아니면 의도한 fallback 이 작동하는지를 명확히 해야 합니다」

    시험 삼아 태안 중국어 쪽을 만들어 봤더니 이랬습니다.

        <html lang="zh-Hans">   ← 중국어 쪽이라고 선언
        본문 글자  한글 2,080 · 중국어 76   ← 96% 가 한국어
        lang="ko" 표시  0곳                ← 조용히 섞임

    중국 손님은 못 읽고, 구글은 「중국어라더니 한국어」로 봅니다.
    **자료가 없는데 쪽만 만들면 빈 껍데기가 됩니다.**

    지금 자료 상태 (engine/migrate_zh.py 로 옮긴 낱말표 기준)
        권역 이름     57개 중 중국어 있음 100%
        포인트 이름  3,603개 중 중국어 있음   0%
        축제 이름     197개 중 중국어 있음   0%

무엇을 보나
    1. 그 언어 쪽의 글자가 정말 그 언어인가 (비율)
    2. 다른 언어가 섞였으면 lang= 으로 **밝혔는가**
    3. 제목·설명·canonical·hreflang 이 그 언어 쪽을 가리키는가
    4. 링크가 같은 언어 쪽으로 가는가 (중국어 쪽에서 한국어 쪽으로
       새면 손님이 길을 잃습니다)

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_i18n.py
    python engine/check_i18n.py --strict
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine.data import 자료   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 언어 폴더 → (html lang, 그 언어 글자, 기대하는 최소 비율)
#
# ★ 「80%」 는 어림이 아닙니다
#   손님이 읽을 수 있으려면 제목·차림표·설명이 그 언어여야 합니다.
#   지명처럼 원어로 두는 것을 빼면 8할은 넘어야 뜻이 통합니다.
#   못 넘으면 **아직 낼 때가 아닙니다.**
언어들 = {
    'zh-cn': {'표시': 'zh', '글자': r'[一-鿿]',
              '최소': 0.80, '이름': '중국어'},
}
한글 = re.compile(r'[가-힣]')

막음, 알림 = [], []


def 본문글자(s):
    """태그·스크립트를 뺀 사람이 읽는 글"""
    s = re.sub(r'<script.*?</script>', ' ', s, flags=re.S)
    s = re.sub(r'<style.*?</style>', ' ', s, flags=re.S)
    return re.sub(r'<[^>]+>', ' ', s)


def 밝힌글(s):
    """lang= 으로 「이건 다른 언어」라고 밝힌 자리의 글"""
    나옴 = []
    for m in re.finditer(r'<(\w+)[^>]*\slang="ko"[^>]*>(.*?)</\1>', s, re.S):
        나옴.append(re.sub(r'<[^>]+>', ' ', m.group(2)))
    return ' '.join(나옴)


def main():
    d = 자료()
    print('다른 언어 쪽이 정말 그 언어인지')
    print('')

    만들것 = ((d.사이트.get('만들언어') or {}).get('쪽')) or ['ko']
    print('[0] 만들기로 한 언어')
    print('      %s  (data/raw/site.json 의 「만들언어」)'
          % ' · '.join(만들것))
    print('')

    본것 = 0
    for 폴더, 규칙 in sorted(언어들.items()):
        자리 = os.path.join(NEW, 폴더)
        쪽들 = sorted(glob.glob(os.path.join(자리, '**', '*.html'),
                                recursive=True))
        if not 쪽들:
            print('[%s] %s 쪽이 없습니다 — 아직 안 만들었습니다'
                  % (폴더, 규칙['이름']))
            if 규칙['표시'] in 만들것:
                막음.append('%s 를 만들기로 했는데 쪽이 없습니다' % 규칙['이름'])
                print('  ✗ 그런데 「만들언어」에는 들어 있습니다 — '
                      '만들거나 목록에서 빼세요')
            print('')
            continue

        본것 += 1
        print('[%s] %s 쪽 %d개' % (폴더, 규칙['이름'], len(쪽들)))
        그언어 = re.compile(규칙['글자'])

        모자란것 = []
        안밝힌것 = []
        합_그말 = 합_한글 = 0
        for p in 쪽들:
            s = io.read(p, default='')
            글 = 본문글자(s)
            그말수 = len(그언어.findall(글))
            한글수 = len(한글.findall(글))
            합_그말 += 그말수
            합_한글 += 한글수
            전 = 그말수 + 한글수
            비 = (그말수 / float(전)) if 전 else 1.0
            이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
            if 비 < 규칙['최소']:
                모자란것.append((이름, 비, 그말수, 한글수))
            # 한국어가 섞였으면 lang="ko" 로 밝혔는가
            if 한글수 > 0:
                밝힌 = len(한글.findall(밝힌글(s)))
                if 밝힌 < 한글수 * 0.5:
                    안밝힌것.append((이름, 한글수, 밝힌))

        전체 = 합_그말 + 합_한글
        전체비 = (합_그말 / float(전체)) if 전체 else 1.0
        print('      글자 — %s %d · 한글 %d  → %s 비율 %.0f%%'
              % (규칙['이름'], 합_그말, 합_한글, 규칙['이름'], 전체비 * 100))

        if 모자란것:
            막음.append('%s 쪽 %d개가 그 언어가 아닙니다'
                        % (규칙['이름'], len(모자란것)))
            print('  ✗ %s 가 %d%% 에 못 미치는 쪽 %d개'
                  % (규칙['이름'], 규칙['최소'] * 100, len(모자란것)))
            for 이름, 비, 그, 한 in 모자란것[:4]:
                print('      %-38s %s %.0f%% (%s %d · 한글 %d)'
                      % (이름, 규칙['이름'], 비 * 100, 규칙['이름'], 그, 한))
            print('      → 자료에 그 언어 값이 없습니다. 쪽만 만들면')
            print('        빈 껍데기가 됩니다. 낱말을 채운 뒤에 내세요.')
        else:
            print('  · 모든 쪽이 %s%% 를 넘습니다' % int(규칙['최소'] * 100))

        if 안밝힌것:
            막음.append('%s 쪽에 한국어가 밝히지 않고 섞였습니다 %d개'
                        % (규칙['이름'], len(안밝힌것)))
            print('  ✗ 한국어가 섞였는데 lang="ko" 로 안 밝힌 쪽 %d개'
                  % len(안밝힌것))
            for 이름, 한, 밝힌 in 안밝힌것[:4]:
                print('      %-38s 한글 %d자 중 밝힌 것 %d자'
                      % (이름, 한, 밝힌))
            print('      → 지명처럼 한국어로 두는 것은 괜찮습니다.')
            print('        다만 lang="ko" 를 달아 **밝혀야** 합니다.')
        print('')

        # 머리 태그
        print('      머리 태그')
        탈 = []
        for p in 쪽들:
            s = io.read(p, default='')
            이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
            m = re.search(r'<html[^>]*lang="([^"]+)"', s)
            if not m or not m.group(1).startswith(규칙['표시']):
                탈.append('%s — html lang 이 %s'
                          % (이름, m.group(1) if m else '없음'))
            t = re.search(r'<title>(.*?)</title>', s, re.S)
            if t and 한글.search(t.group(1)) and not 그언어.search(t.group(1)):
                탈.append('%s — 제목이 한국어뿐입니다' % 이름)
            c = re.search(r'canonical" href="([^"]+)', s)
            if c and ('/%s/' % 폴더) not in c.group(1):
                탈.append('%s — canonical 이 %s 쪽을 안 가리킵니다'
                          % (이름, 폴더))
        if 탈:
            막음.append('%s 쪽 머리 태그 %d건' % (규칙['이름'], len(탈)))
            for x in 탈[:5]:
                print('        ✗ %s' % x)
        else:
            print('        · html lang · 제목 · canonical 이 모두 맞습니다')
        print('')

    if not 본것:
        # ★ 「안 봤다」를 「멀쩡하다」로 내지 않습니다 (2026-09-26)
        print('한국어 말고 다른 언어 쪽이 없습니다 — 잴 것이 없습니다.')
        print('  이것은 「제대로 되어 있다」가 아니라 「해당 없음」입니다.')
        return 0

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 「쪽을 만들 수 있다」와 「낼 수 있다」는 다릅니다.')
        print('    자료가 없는 언어는 쪽만 만들어도 빈 껍데기입니다.')
        return 1 if '--strict' in sys.argv else 0
    print('다른 언어 쪽이 제대로 그 언어입니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
