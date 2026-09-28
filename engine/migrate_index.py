# -*- coding: utf-8 -*-
"""57권역 목록(index.json)을 만듭니다 — **모든 숫자의 기준** (계약-05)

왜 이것이 먼저인가
    옛 사이트는 권역 목록이 아홉 군데로 갈라져 있었습니다.

        data/coast-regions.json            충남 6
        data/coast-regions-<묶음>.json     다섯 묶음 26
        data/jeju-regions.json             제주 7
        js/app.js 의 COORDS                전남 15 (좌표만)
        <권역>.html                        전남의 나머지 (쪽이 원본)

    그래서 「우리 권역이 몇 개인가」에 답하려면 아홉 곳을 더해야 했고,
    쪽마다 적힌 숫자가 조금씩 어긋났습니다. 한 곳으로 모읍니다.

무엇을 안 담나
    **포인트 수를 적지 않습니다** (계약-04). 셀 수 있는 것은 저장하지
    않습니다 — 엔진이 points/ 를 읽어 셉니다. 옛 사이트가 숫자를 적어
    두었다가 어긋난 것이 바로 그 사고였습니다.

    명소·먹거리·축제·어종은 travel/ · festivals/ 로 따로 갑니다.
    여기에는 **권역의 신원**만 둡니다.

쓰는 법
    python engine/migrate_index.py            보여만 줍니다
    python engine/migrate_index.py --write    씁니다
"""
import os
import re
import sys
import glob
import json
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 묶음 차례 — 서해 북쪽에서 시계 방향으로 돕니다
묶음차례 = ['sudogwon', 'chungnam', 'jeonbuk', 'jeonnam', 'jeju',
            'gyeongnam', 'busanulsan', 'gyeongbuk', 'gangwon']

# 권역이 닿는 바다 — 안내글(조수 차·조심할 것)이 달라집니다.
# 묶음으로만 정하면 전남이 틀립니다: 여수·순천·광양·고흥은 남해입니다.
# 예외를 코드에 두지 않고 **자료에 적어** 둡니다 (계약-02)
묶음바다 = {
    'sudogwon': '서해', 'chungnam': '서해', 'jeonbuk': '서해', 'jeonnam': '서해',
    'jeju': '제주', 'gyeongnam': '남해', 'busanulsan': '남해',
    'gyeongbuk': '동해', 'gangwon': '동해',
}
남해권역 = ['haenam', 'wando', 'gangjin', 'jangheung', 'boseong',
            'goheung', 'yeosu', 'suncheon', 'gwangyang']

묶음이름 = {
    'sudogwon': {'ko': '인천·경기', 'zh': '仁川·京畿'},
    'chungnam': {'ko': '충남', 'zh': '忠南'},
    'jeonbuk': {'ko': '전북', 'zh': '全北'},
    'jeonnam': {'ko': '전남', 'zh': '全南'},
    'jeju': {'ko': '제주', 'zh': '济州'},
    'gyeongnam': {'ko': '경남', 'zh': '庆南'},
    'busanulsan': {'ko': '부산·울산', 'zh': '釜山·蔚山'},
    'gyeongbuk': {'ko': '경북', 'zh': '庆北'},
    'gangwon': {'ko': '강원', 'zh': '江原'},
}


def 중국어이름():
    """권역 중국어 이름 — 세 군데에 흩어져 있습니다.

        coast-zh.json    35권역 (여덟 묶음)
        jeju-zh.json      7권역
        zh-cn/<권역>.html 15권역 (전남 — 또 쪽이 원본입니다)
    """
    나옴 = {}
    d = io.read_json(os.path.join(OLD, 'zh-cn', 'i18n', 'coast-zh.json'), default={})
    for 권역, v in (d.get('region') or {}).items():
        나옴[권역] = (v.get('short') or v.get('n') or '').strip() or None
    j = io.read_json(os.path.join(OLD, 'zh-cn', 'i18n', 'jeju-zh.json'), default={})
    for 권역, v in (j.get('regions') or {}).items():
        나옴[권역] = (v.get('name') or '').strip() or 나옴.get(권역)
    for p in glob.glob(os.path.join(OLD, 'zh-cn', '*.html')):
        권역 = os.path.splitext(os.path.basename(p))[0]
        if 나옴.get(권역):
            continue
        m = re.search(r'class="accent"[^>]*>\s*([^<]+)', io.read(p, default=''))
        if m:
            나옴[권역] = m.group(1).strip() or None
    return 나옴


def 좌표표():
    """권역 대표 좌표 — 두 군데에 흩어져 있습니다.

        js/coast-data.js   35권역 (lat/lng)
        js/app.js COORDS   전남 15 · 제주 7
    """
    나옴 = {}
    s = io.read(os.path.join(OLD, 'js', 'coast-data.js'), default='')
    i, j = s.find('{'), s.rstrip().rstrip(';').rfind('}')
    if i > 0 and j > i:
        try:
            for 권역, v in json.loads(s[i:j + 1]).items():
                if v.get('lat') and v.get('lng'):
                    나옴[권역] = (float(v['lat']), float(v['lng']))
        except ValueError:
            pass
    a = io.read(os.path.join(OLD, 'js', 'app.js'), default='')
    m = re.search(r'var COORDS = \{(.*?)\n  \};', a, re.S)
    if m:
        for 권역, 위, 경 in re.findall(r'(\w+):\s*\[([\d.]+),\s*([\d.]+)\]', m.group(1)):
            나옴.setdefault(권역, (float(위), float(경)))
    return 나옴


def 전남자료():
    """zh-cn/i18n/region-ko.json — 전남 15권역의 **유일한 정리된 자료**입니다.

    중국어판을 만들면서 쪽에서 뽑아 둔 것입니다. 차례·소개글이 여기 있습니다.
    """
    return io.read_json(os.path.join(OLD, 'zh-cn', 'i18n', 'region-ko.json'),
                        default={})


def 쪽에서(권역):
    """전남 권역 쪽에서 이름·설명·대표사진을 캡니다. 쪽이 원본입니다."""
    s = io.read(os.path.join(OLD, '%s.html' % 권역), default='')
    if not s:
        return {}
    나옴 = {}
    m = re.search(r'<title>([^<]*)</title>', s)
    if m:
        제목 = _html.unescape(m.group(1))
        나옴['이름'] = 제목.split()[0] if 제목 else None
    m = re.search(r'name="description" content="([^"]*)"', s)
    if m:
        나옴['설명'] = _html.unescape(m.group(1))
    # h1 의 강조 글자가 권역 이름입니다 — "이곳은 … '신안' 입니다"
    m = re.search(r'<span class="accent">\s*[\'\u2018\u2019]?([^<\'\u2018\u2019]+)', s)
    if m:
        나옴['이름'] = m.group(1).strip() or 나옴.get('이름')
    m = re.search(r'og:image" content="([^"?]+)', s)
    if m:
        나옴['대표사진길'] = m.group(1).replace('https://badagaja.com/', '')
    # 히어로 한 줄 — h1 바로 뒤 문단
    m = re.search(r'</h1>\s*<p[^>]*>(.*?)</p>', s, re.S)
    if m:
        t = re.sub(r'<[^>]+>', ' ', m.group(1))
        나옴['안내'] = re.sub(r'\s+', ' ', _html.unescape(t)).strip() or None
    return 나옴


def 자료묶음들():
    """자료가 있는 여덟 묶음을 읽습니다"""
    나옴 = []
    파일 = sorted(glob.glob(os.path.join(OLD, 'data', 'coast-regions*.json')))
    파일 += [os.path.join(OLD, 'data', 'jeju-regions.json')]
    for p in 파일:
        d = io.read_json(p, default={})
        묶음 = (d.get('group') or {}).get('key')
        if not 묶음:
            묶음 = 'jeju' if 'jeju' in os.path.basename(p) else 'chungnam'
        for r in d.get('regions', []):
            나옴.append((묶음, r))
    return 나옴


def 바다(묶음, 권역):
    return '남해' if 권역 in 남해권역 else 묶음바다.get(묶음, '서해')


def 만들기(묶음, r, zh, 좌표):
    """권역 하나를 새 모양으로"""
    권역 = r['slug']
    st = r.get('station') or {}
    위경 = 좌표.get(권역, (r.get('lat'), r.get('lng')))
    return {
        'id': 권역,
        '묶음': 묶음,
        '이름': {'ko': r.get('name') or 권역, 'zh': zh.get(권역)},
        '짧은이름': r.get('short') or r.get('name'),
        '차례': r.get('no'),
        '색': r.get('color'),
        '한줄': r.get('tag'),
        '소개': r.get('lead'),
        '안내': r.get('band'),
        '설명': r.get('desc'),
        '좌표': {'위도': 위경[0], '경도': 위경[1]},
        '바다': 바다(묶음, 권역),
        '물때관측소': ({'이름': st.get('name'), '코드': st.get('code'),
                        '메모': st.get('note')} if st.get('code') else None),
        '시군구': r.get('sigungu') or [],
        '항구': r.get('ports') or [],
        '지역코드': r.get('areaCode'),
        '법정동코드': r.get('lDongRegnCd'),
        '관광안내': r.get('tourUrl'),
        '포인트안내': r.get('pointsIntro'),
        '대표사진': None,
        '엶': r.get('open', True),
    }


def 전남만들기(권역, 차례, 좌표, zh, 전남):
    """전남 권역 하나 — region-ko.json 과 쪽에서 캡니다"""
    쪽 = 쪽에서(권역)
    v = 전남.get(권역) or {}
    위경 = 좌표.get(권역, (None, None))
    이름 = 쪽.get('이름') or 권역
    return {
        'id': 권역,
        '묶음': 'jeonnam',
        '이름': {'ko': 이름, 'zh': zh.get(권역)},
        '짧은이름': 이름,
        '차례': 400 + (v.get('no') or 차례),
        '색': None,
        '한줄': None,
        '소개': None,
        '안내': v.get('lede') or 쪽.get('안내'),
        '설명': 쪽.get('설명'),
        '좌표': {'위도': 위경[0], '경도': 위경[1]},
        '바다': 바다('jeonnam', 권역),
        '물때관측소': None,     # 전남은 옛 사이트에도 없습니다 — 좌표로 찾습니다
        '시군구': [],
        '항구': [],
        '지역코드': None,
        '법정동코드': None,
        '관광안내': None,
        '포인트안내': None,
        '대표사진': None,
        '엶': True,
    }


def 전남차례():
    """point/01_sinan_fishing.html 의 앞 두 자리가 차례입니다"""
    나옴 = {}
    for p in glob.glob(os.path.join(OLD, 'point', '[0-9][0-9]_*.html')):
        m = re.match(r'(\d\d)_([a-z]+)_', os.path.basename(p))
        if m:
            나옴.setdefault(m.group(2), int(m.group(1)))
    return 나옴


def main():
    쓰기 = '--write' in sys.argv
    zh = 중국어이름()
    좌표 = 좌표표()
    전남 = 전남자료()

    권역들 = []
    for 묶음, r in 자료묶음들():
        권역들.append(만들기(묶음, r, zh, 좌표))

    for 권역, 차례 in sorted(전남차례().items(), key=lambda x: x[1]):
        권역들.append(전남만들기(권역, 차례, 좌표, zh, 전남))

    # 차례 고정 (계약-07) — 묶음 차례 → 권역 차례
    권역들.sort(key=lambda x: (묶음차례.index(x['묶음']) if x['묶음'] in 묶음차례 else 99,
                               x['차례'] or 0, x['id']))

    print('57권역 목록 만들기')
    print('  옛 사이트: %s' % OLD)
    print('')
    지금 = None
    for x in 권역들:
        if x['묶음'] != 지금:
            지금 = x['묶음']
            n = sum(1 for y in 권역들 if y['묶음'] == 지금)
            print('  [%s] %d권역' % (묶음이름[지금]['ko'], n))
        print('      %-12s %-8s %s' % (
            x['id'], x['이름']['ko'],
            '물때 %s' % x['물때관측소']['코드'] if x['물때관측소'] else '물때 없음'))
    print('')
    print('  합계 %d권역' % len(권역들))
    print('')

    # 검사
    탈 = []
    if len(권역들) != 57:
        탈.append('권역이 57개가 아닙니다 — %d개' % len(권역들))
    아이디 = [x['id'] for x in 권역들]
    겹침 = set(a for a in 아이디 if 아이디.count(a) > 1)
    if 겹침:
        탈.append('아이디가 겹칩니다: %s' % ' · '.join(sorted(겹침)))
    for x in 권역들:
        위, 경 = x['좌표']['위도'], x['좌표']['경도']
        if 위 is None or 경 is None:
            탈.append('%s — 좌표가 없습니다' % x['id'])
        elif not (33.0 <= 위 <= 39.0) or not (124.0 <= 경 <= 132.0):
            탈.append('%s — 좌표가 한반도 밖입니다 (%.3f, %.3f)' % (x['id'], 위, 경))
        if not x['이름']['ko'] or x['이름']['ko'] == x['id']:
            탈.append('%s — 한글 이름을 못 읽었습니다' % x['id'])

    빈중국어 = [x['id'] for x in 권역들 if not x['이름']['zh']]
    if 빈중국어:
        print('  ~ 중국어 이름이 없는 권역 %d곳 (막지는 않습니다 — 계약-21)'
              % len(빈중국어))
        print('      %s' % ' · '.join(빈중국어))
        print('')

    if 탈:
        print('★ 손볼 곳 %d건' % len(탈))
        for x in 탈[:12]:
            print('    %s' % x)
        print('')
        return 1

    if 쓰기:
        io.write_json(os.path.join(DATA, 'raw', 'index.json'), {
            '_설명': '57권역 목록. **모든 숫자는 여기서 셉니다.** 포인트 수는 '
                     '적지 않습니다 — 엔진이 points/ 를 읽어 셉니다 (계약-04)',
            '묶음차례': 묶음차례,
            '묶음이름': 묶음이름,
            '권역': 권역들,
        })
        print('자료에 썼습니다: data/raw/index.json')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
