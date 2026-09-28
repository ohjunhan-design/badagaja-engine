# -*- coding: utf-8 -*-
"""새로 만든 쪽을 옛 쪽과 **내용으로** 견줍니다.

왜 겉모습이 아니라 내용인가
    새 쪽은 디자인이 달라지므로 글자 그대로 같을 수 없습니다.
    중요한 것은 **보여 주던 것이 하나도 안 빠졌는가** 입니다.

    옛 사이트에서 났던 사고가 바로 이것입니다 — 쪽을 다시 만들었는데
    포인트가 조용히 줄고, 한 달 넘게 아무도 몰랐습니다.

무엇을 견주나
    1. 포인트 이름   — 옛 쪽에 있던 것이 새 쪽에 다 있는가
    2. 좌표          — 같은 자리를 가리키는가
    3. 대상 어종     — 빠진 것이 없는가
    4. 숫자          — 쪽에 적힌 수와 실제 카드 수가 맞는가
                       (옛 쪽은 「76곳」이라 적고 74개를 실었습니다)

쓰는 법
    python engine/compare_page.py taean 낚시
    python engine/compare_page.py --all
"""
import os
import re
import sys
import glob
import html as _html
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, url   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

갈래파일 = {'낚시': 'fishing', '해루질': 'gleaning'}


def 어종고르기():
    """어종 이름을 견줄 수 있게 고릅니다.

    일부러 하나로 모은 이름(놀래미→노래미, 쭈꾸미→주꾸미)을 모르면
    「어종이 줄었다」는 헛것을 냅니다. 모으기 표를 그대로 씁니다.
    """
    import importlib.util
    길 = os.path.join(HERE, 'fix_species.py')
    스펙 = importlib.util.spec_from_file_location('_fs', 길)
    m = importlib.util.module_from_spec(스펙)
    스펙.loader.exec_module(m)
    return m.같은것, m.어종아님


같은것, 어종아님 = 어종고르기()


def 어종맞추기(이름들):
    """모으기·걸러내기를 거친 뒤의 이름 꾸러미"""
    나옴 = set()
    for x in 이름들:
        x = (x or '').strip()
        if not x or 어종아님.match(x):
            continue
        나옴.add(같은것.get(x, x))
    return 나옴


def 글자(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    return re.sub(r'\s+', ' ', _html.unescape(s)).strip()


def 옛쪽찾기(권역, 갈래):
    """옛 사이트의 쪽은 자리가 두 가지입니다 (계약-03 이 없앤 그 문제)"""
    g = 갈래파일[갈래]
    후보 = glob.glob(os.path.join(OLD, 'point', '[0-9][0-9]_%s_%s.html' % (권역, g)))
    후보 += glob.glob(os.path.join(OLD, 'point', '*', '%s_%s.html' % (권역, g)))
    return 후보[0] if 후보 else None


def 옛읽기(길):
    s = io.read(길, default='')
    카드 = re.compile(
        r'<div class="card" id="point-\d+"([^>]*)>(.*?)'
        r'(?=<div class="card" id="point-|</section>|</main>)', re.S)
    이름뽑기 = re.compile(r'font-size:1\.08rem[^>]*>\s*(?:\d+\.\s*)?([^<]+?)\s*</div>')
    나옴 = []
    for 속성, 안쪽 in 카드.findall(s):
        m = 이름뽑기.search(안쪽)
        if not m:
            continue
        a = dict(re.findall(r'data-(lat|lng)="([^"]*)"', 속성))
        대상 = ''
        m2 = re.search(r'<b[^>]*>\s*대상\s*:?\s*</b>\s*([^<]*)', 안쪽)
        if m2:
            대상 = 글자(m2.group(1))
        나옴.append({
            '이름': 글자(m.group(1)),
            '위도': a.get('lat'), '경도': a.get('lng'),
            '대상': 어종맞추기(re.split(r'[·,]', 대상)),
        })
    # 쪽에 적힌 숫자 — 제목에 「76곳」처럼
    적힌수 = None
    m = re.search(r'<title>[^<]*?(\d+)\s*곳', s)
    if m:
        적힌수 = int(m.group(1))
    return 나옴, 적힌수


def 새읽기(길):
    s = io.read(길, default='')
    카드 = re.compile(r'<article class="card"([^>]*)>(.*?)</article>', re.S)
    나옴 = []
    for 속성, 안쪽 in 카드.findall(s):
        a = dict(re.findall(r'data-(lat|lng)="([^"]*)"', 속성))
        m = re.search(r'class="card-name">\s*(?:\d+\.\s*)?([^<]+?)\s*</h3>', 안쪽)
        대상 = ''
        m2 = re.search(r'<b>대상:</b>\s*([^<]*)', 안쪽)
        if m2:
            대상 = 글자(m2.group(1))
        나옴.append({
            '이름': 글자(m.group(1)) if m else '',
            '위도': a.get('lat') or None, '경도': a.get('lng') or None,
            '대상': 어종맞추기(re.split(r'[·,]', 대상)),
        })
    적힌수 = None
    m = re.search(r'<title>[^<]*?(\d+)\s*곳', s)
    if m:
        적힌수 = int(m.group(1))
    return 나옴, 적힌수


def 견주기(권역, 갈래, 조용히=False):
    옛길 = 옛쪽찾기(권역, 갈래)
    새길 = os.path.join(NEW, url.point_list(권역, 갈래))
    if not 옛길:
        return ['%s %s — 옛 쪽을 못 찾음' % (권역, 갈래)], []
    if not os.path.exists(새길):
        return ['%s %s — 새 쪽이 없음' % (권역, 갈래)], []

    옛, 옛수 = 옛읽기(옛길)
    새, 새수 = 새읽기(새길)
    탈, 알림 = [], []

    if not 조용히:
        print('%s %s' % (권역, 갈래))
        print('  옛 %s' % os.path.relpath(옛길, OLD))
        print('  새 %s' % os.path.relpath(새길, NEW))
        print('  카드  옛 %d개 · 새 %d개' % (len(옛), len(새)))

    # 1) 쪽에 적힌 숫자가 실제 카드 수와 맞는가
    if 옛수 is not None and 옛수 != len(옛):
        알림.append('옛 쪽은 제목에 %d곳이라 적고 %d개를 실었습니다' % (옛수, len(옛)))
    if 새수 is not None and 새수 != len(새):
        탈.append('새 쪽이 제목에 %d곳이라 적고 %d개를 실었습니다' % (새수, len(새)))

    # 2) 이름
    옛이름 = collections.Counter(x['이름'] for x in 옛)
    새이름 = collections.Counter(x['이름'] for x in 새)
    사라짐 = sorted((옛이름 - 새이름).elements())
    늘어남 = sorted((새이름 - 옛이름).elements())
    if 사라짐:
        탈.append('옛 쪽에 있는데 새 쪽에 없는 포인트 %d곳: %s'
                  % (len(사라짐), ' · '.join(사라짐[:5])))
    if 늘어남:
        알림.append('새 쪽에만 있는 포인트 %d곳: %s'
                    % (len(늘어남), ' · '.join(늘어남[:5])))

    # 3) 좌표·대상 — 이름으로 짝지어. 같은 이름이 여럿이면 건너뜁니다
    옛표 = {}
    for x in 옛:
        옛표[x['이름']] = None if x['이름'] in 옛표 else x
    좌표다름, 대상빠짐 = [], []
    for x in 새:
        y = 옛표.get(x['이름'])
        if not y:
            continue
        for 칸 in ('위도', '경도'):
            a, b = y[칸], x[칸]
            if a and b and abs(float(a) - float(b)) > 0.0001:
                좌표다름.append('%s %s 옛%s → 새%s' % (x['이름'], 칸, a, b))
        빠진 = y['대상'] - x['대상']
        if 빠진:
            대상빠짐.append('%s: %s' % (x['이름'], ' · '.join(sorted(빠진)[:3])))
    if 좌표다름:
        탈.append('좌표가 다른 곳 %d개: %s' % (len(좌표다름), ' · '.join(좌표다름[:3])))
    if 대상빠짐:
        알림.append('대상 어종이 줄어든 곳 %d개: %s'
                    % (len(대상빠짐), ' · '.join(대상빠짐[:3])))

    if not 조용히:
        for x in 탈:
            print('  ✗ %s' % x)
        for x in 알림:
            print('  ~ %s' % x)
        if not 탈 and not 알림:
            print('  · 빠진 것 없이 같습니다')
        print('')
    return 탈, 알림


def main():
    if '--all' in sys.argv:
        from engine.data import 자료
        d = 자료()
        모든탈, 모든알림 = [], []
        for r in d.권역들:
            for 갈래 in ('낚시', '해루질'):
                if not d.셈(r['id'], 갈래):
                    continue
                탈, 알림 = 견주기(r['id'], 갈래, 조용히=True)
                for x in 탈:
                    모든탈.append('%s %s — %s' % (r['id'], 갈래, x))
                for x in 알림:
                    모든알림.append('%s %s — %s' % (r['id'], 갈래, x))
        print('모든 쪽 대조')
        print('  손볼 곳 %d · 살펴볼 것 %d' % (len(모든탈), len(모든알림)))
        for x in 모든탈[:20]:
            print('  ✗ %s' % x)
        for x in 모든알림[:10]:
            print('  ~ %s' % x)
        return 1 if 모든탈 else 0

    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    탈, _ = 견주기(sys.argv[1], sys.argv[2])
    return 1 if 탈 else 0


if __name__ == '__main__':
    sys.exit(main())
