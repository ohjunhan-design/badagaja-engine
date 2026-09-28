# -*- coding: utf-8 -*-
"""전남 15권역의 여행 자료를 쪽에서 캐냅니다.

왜 또 전남만인가
    포인트와 똑같습니다. **전남만 자료가 없고 HTML 이 원본**입니다.
    명소·먹거리·어종·코스·축제가 전부 <권역>.html 안에만 있습니다.

    옛 사이트에서 전남이 늘 뒤처진 이유가 이것입니다. 자료로 옮기면
    다른 42권역과 **같은 틀**을 쓰게 되고, 그때부터 예외가 사라집니다
    (계약-02).

먹거리·명소는 zh-cn/i18n/region-ko.json 에도 있습니다 (중국어판 만들며
정리해 둔 것). 그쪽을 먼저 쓰고, 없는 것만 쪽에서 캡니다.

쓰는 법
    python engine/extract_jeonnam_travel.py            보여만 줍니다
    python engine/extract_jeonnam_travel.py --write    씁니다
"""
import os
import re
import sys
import glob
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

달이름 = {'1월': 1, '2월': 2, '3월': 3, '4월': 4, '5월': 5, '6월': 6,
          '7월': 7, '8월': 8, '9월': 9, '10월': 10, '11월': 11, '12월': 12}


def 카드나누기(조각, 클래스):
    """같은 클래스의 카드들을 하나씩 떼어 냅니다.

    ★ 정규식으로 `<div class="x">(.*?)</div>` 를 쓰면 안 됩니다 (2026-09-26).
      카드 안에 또 <div> 가 있으면 엉뚱한 데서 끊기고, 뒤에 </div> 를
      요구하면 마지막 하나만 잡힙니다. 실제로 어종 16개 가운데 2개만
      캐 놓고 멀쩡한 줄 알았습니다.

      클래스로 쪼개면 카드 수가 늘 정확합니다.
    """
    부분 = re.split(r'<div class="%s[^"]*"[^>]*>' % re.escape(클래스), 조각)
    return 부분[1:]


def 글(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = _html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip() or None


def 구역(s, 아이디):
    """<section id="..."> … </section> 한 덩이"""
    i = s.find('id="%s"' % 아이디)
    if i < 0:
        return ''
    j = s.find('</section>', i)
    return s[i:j if j > 0 else len(s)]


def 어종캐기(권역, s):
    """제철 어종·패류. 낚시 무리와 해루질 무리가 따로 있습니다"""
    조각 = 구역(s, 'catch')
    나옴 = []
    # 무리(catch-group)마다 머리에 '해루질' 또는 '낚시' 가 적혀 있습니다
    무리들 = re.split(r'<div class="catch-group">', 조각)[1:]
    for 무리 in 무리들:
        머리 = 글(무리[:무리.find('catch-grid')] if 'catch-grid' in 무리 else 무리[:400])
        갈래 = '해루질' if '해루질' in (머리 or '') else '낚시'
        for 카드 in 카드나누기(무리, 'catch-card'):
            철 = 글((re.search(r'class="season">([^<]*)', 카드) or [None, ''])[1])
            이름 = 글((re.search(r'<h3[^>]*>([^<]*)', 카드) or [None, ''])[1])
            설명 = 글((re.search(r'<p>(.*?)</p>', 카드, re.S) or [None, ''])[1])
            그림 = (re.search(r'data-icon="([\w\-]+)"', 카드) or [None, None])[1]
            if not 이름:
                continue
            나옴.append({'이름': 이름, '갈래': 갈래, '철': 철,
                         '설명': 설명, '그림': 그림})
    # 같은 이름이 두 번 나오면 한 번만
    본것, 고른것 = set(), []
    for x in 나옴:
        키 = (x['이름'], x['갈래'])
        if 키 in 본것:
            continue
        본것.add(키)
        고른것.append(x)
    나옴 = 고른것
    표 = []
    센것 = {'낚시': 0, '해루질': 0}
    for x in 나옴:
        센것[x['갈래']] += 1
        표시 = 'fish' if x['갈래'] == '낚시' else 'catch'
        표.append({
            'id': '%s-%s-%02d' % (권역, 표시, 센것[x['갈래']]),
            '이름': {'ko': x['이름'], 'zh': None},
            '갈래': x['갈래'],
            '철': x['철'],
            '설명': {'ko': x['설명'], 'zh': None},
            '그림': x['그림'],
        })
    return 표


def 명소캐기(권역, s, 정리된):
    """명소. 정리된 자료(region-ko.json)가 있으면 그것을 씁니다"""
    if 정리된:
        나옴 = []
        for i, x in enumerate(정리된, 1):
            나옴.append({
                'id': '%s-spot-%02d' % (권역, i),
                '이름': {'ko': 글(x.get('n')), 'zh': None},
                '갈래': 글(x.get('k')),
                '주소': 글(x.get('a')),
                '설명': {'ko': 글(x.get('d')), 'zh': None},
                '좌표': None,
                '배로가나': False,
            })
        return 나옴
    조각 = 구역(s, 'coastspot')
    나옴 = []
    for i, 카드 in enumerate(카드나누기(조각, 'spot-card'), 1):
        나옴.append({
            'id': '%s-spot-%02d' % (권역, i),
            '이름': {'ko': 글((re.search(r'<h3[^>]*>([^<]*)', 카드) or [None, ''])[1]),
                     'zh': None},
            '갈래': 글((re.search(r'class="spot-kind"[^>]*>([^<]*)', 카드) or [None, ''])[1]),
            '주소': 글((re.search(r'class="spot-addr"[^>]*>([^<]*)', 카드) or [None, ''])[1]),
            '설명': {'ko': 글((re.search(r'class="spot-desc"[^>]*>(.*?)</p>', 카드, re.S)
                              or [None, ''])[1]), 'zh': None},
            '좌표': None,
            '배로가나': False,
        })
    return [x for x in 나옴 if x['이름']['ko']]


def 먹거리캐기(권역, s, 정리된):
    if 정리된:
        나옴 = []
        for i, x in enumerate(정리된, 1):
            나옴.append({
                'id': '%s-eat-%02d' % (권역, i),
                '이름': {'ko': 글(x.get('n')), 'zh': None},
                '설명': {'ko': 글(x.get('d')), 'zh': None},
                '철': None,
                '그림': 글(x.get('i')),
            })
        return [x for x in 나옴 if x['이름']['ko']]
    조각 = 구역(s, 'eat')
    나옴 = []
    for i, 카드 in enumerate(카드나누기(조각, 'eat-card'), 1):
        나옴.append({
            'id': '%s-eat-%02d' % (권역, i),
            '이름': {'ko': 글((re.search(r'<h3[^>]*>([^<]*)', 카드) or [None, ''])[1]),
                     'zh': None},
            '설명': {'ko': 글((re.search(r'<p[^>]*>(.*?)</p>', 카드, re.S) or [None, ''])[1]),
                     'zh': None},
            '철': None,
            '그림': (re.search(r'data-icon="([\w\-]+)"', 카드) or [None, None])[1],
        })
    return [x for x in 나옴 if x['이름']['ko']]


def 축제캐기(권역, s):
    """달마다 한 칸. 한 달에 축제가 여럿일 수 있습니다.

    ★ 이름이 <a> 안에 들어 있습니다 (2026-09-26).
      `class="fm-name">([^<]*)` 로 잡으면 바로 뒤가 <a 라 빈 글자만
      집히고, 축제가 **한 건도** 안 캐집니다. 태그를 걷어 내고 읽습니다.
    """
    조각 = 구역(s, 'festival')
    나옴 = []
    차례 = 0
    for 칸 in 카드나누기(조각, 'fest-month'):
        달글 = 글((re.search(r'class="fm-num"[^>]*>(.*?)</div>', 칸, re.S)
                   or [None, ''])[1])
        이름들 = [글(x) for x in
                  re.findall(r'class="fm-name"[^>]*>(.*?)</div>', 칸, re.S)]
        설명들 = [글(x) for x in
                  re.findall(r'class="fm-desc"[^>]*>(.*?)</div>', 칸, re.S)]
        길들 = re.findall(r'class="fm-name"[^>]*>\s*<a href="([^"]+)"', 칸)
        for i, 이름 in enumerate(이름들):
            if not 이름:
                continue
            차례 += 1
            나옴.append({
                'id': '%s-fest-%02d' % (권역, 차례),
                '이름': {'ko': 이름, 'zh': None},
                '달': 달이름.get(달글 or ''),
                '곳': None,
                '설명': {'ko': 설명들[i] if i < len(설명들) else None, 'zh': None},
                '해': None,
                '쪽': 길들[i] if i < len(길들) else None,
            })
    return 나옴


def 코스캐기(권역, s):
    조각 = 구역(s, 'course')
    나옴 = []
    for i, 카드 in enumerate(카드나누기(조각, 'course-card'), 1):
        이름 = 글((re.search(r'<h3[^>]*>([^<]*)', 카드) or [None, ''])[1])
        누구 = 글((re.search(r'class="course-badge[^"]*"[^>]*>([^<]*)', 카드) or [None, ''])[1])
        차례 = []
        for s2 in re.finditer(r'class="c-time">([^<]*)</span>\s*<span class="c-text">([^<]*)',
                              카드):
            때, 무엇 = 글(s2.group(1)), 글(s2.group(2))
            if 무엇:
                차례.append('%s — %s' % (때, 무엇) if 때 else 무엇)
        if not 이름:
            continue
        나옴.append({
            'id': '%s-course-%02d' % (권역, i),
            '이름': {'ko': 이름, 'zh': None},
            '누구와': 누구,
            '차례': 차례,
        })
    return 나옴


def main():
    쓰기 = '--write' in sys.argv
    정리 = io.read_json(os.path.join(OLD, 'zh-cn', 'i18n', 'region-ko.json'),
                        default={})
    쪽들 = {}
    for 권역 in 정리:
        p = os.path.join(OLD, '%s.html' % 권역)
        if os.path.exists(p):
            쪽들[권역] = io.read(p, default='')

    if not 쪽들:
        print('전남 권역 쪽을 찾지 못했습니다: %s' % OLD)
        return 1

    목록 = []
    print('전남 여행 자료를 쪽에서 캐냅니다')
    print('  권역 %d개' % len(쪽들))
    print('')
    print('  권역        명소 먹거리 어종 축제 코스')
    for 권역 in sorted(쪽들, key=lambda k: (정리.get(k) or {}).get('no') or 99):
        s = 쪽들[권역]
        v = 정리.get(권역) or {}
        한권역 = {
            'id': 권역,
            '명소': 명소캐기(권역, s, v.get('spot')),
            '먹거리': 먹거리캐기(권역, s, v.get('eat')),
            '축제': 축제캐기(권역, s),
            '어종': 어종캐기(권역, s),
            '코스': 코스캐기(권역, s),
            '마을': [],
            '통제': [],
            '관광안내': ({'이름': 글((v.get('official') or {}).get('n')),
                          '주소': (v.get('official') or {}).get('href')}
                         if v.get('official') else None),
        }
        목록.append(한권역)
        print('  %-12s %4d %5d %4d %4d %4d' % (
            권역, len(한권역['명소']), len(한권역['먹거리']),
            len(한권역['어종']), len(한권역['축제']), len(한권역['코스'])))
    print('')
    print('  합계  명소 %d · 먹거리 %d · 어종 %d · 축제 %d · 코스 %d' % (
        sum(len(x['명소']) for x in 목록),
        sum(len(x['먹거리']) for x in 목록),
        sum(len(x['어종']) for x in 목록),
        sum(len(x['축제']) for x in 목록),
        sum(len(x['코스']) for x in 목록)))
    print('')

    # ★ 쪽에 있는 카드 수와 캐낸 수를 맞춰 봅니다 (2026-09-26)
    #   처음에는 「빈 칸이 있나」만 봤습니다. 그랬더니 어종 16개 가운데
    #   2개만 캐고도 통과했고, 축제는 0개인데 그냥 넘어갔습니다.
    #   **수가 맞는지** 봐야 조용한 실패를 잡습니다.
    셈할것 = [('명소', 'spot-card'), ('먹거리', 'eat-card'),
              ('어종', 'catch-card'), ('축제', 'fm-name'),
              ('코스', 'course-card')]
    어긋남 = []
    for x in 목록:
        쪽글 = 쪽들[x['id']]
        for 칸, 클래스 in 셈할것:
            쪽수 = len(re.findall(r'class="%s[^"]*"' % 클래스, 쪽글))
            캔수 = len(x[칸])
            # 명소·먹거리는 정리된 자료(region-ko.json)를 먼저 쓰므로
            # 쪽보다 적거나 많을 수 있습니다 — 아예 0 일 때만 잡습니다
            if 칸 in ('명소', '먹거리'):
                if 쪽수 and not 캔수:
                    어긋남.append('%s %s 쪽 %d → 캔 것 0' % (x['id'], 칸, 쪽수))
            elif 쪽수 != 캔수:
                어긋남.append('%s %s 쪽 %d → 캔 것 %d' % (x['id'], 칸, 쪽수, 캔수))
    if 어긋남:
        print('  ★ 쪽에 있는 수와 캐낸 수가 다릅니다 %d건' % len(어긋남))
        for x in 어긋남[:10]:
            print('      %s' % x)
        if len(어긋남) > 10:
            print('      … 그 밖 %d건' % (len(어긋남) - 10))
        print('     (뽑는 규칙이 그 쪽 모양과 안 맞는 것입니다)')
        print('')
        if 쓰기:
            print('     수가 안 맞아 쓰지 않았습니다.')
            return 1
    else:
        print('  · 쪽에 있는 수와 캐낸 수가 모두 같습니다')
        print('')

    if 쓰기:
        목록.sort(key=lambda x: x['id'])
        io.write_json(os.path.join(DATA, 'raw', 'travel', 'jeonnam.json'), {
            '_설명': '전남 권역의 명소·먹거리·축제·어종·코스. '
                     '**옛 사이트의 HTML 에서 캐냈습니다** — 자료가 없었기 때문입니다. '
                     '손으로 고치려면 data/overrides/travel/ 에',
            '권역': 목록,
        })
        print('자료에 썼습니다: data/raw/travel/jeonnam.json')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
