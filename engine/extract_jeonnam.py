# -*- coding: utf-8 -*-
"""전남 포인트 1,077곳을 HTML 에서 캐냅니다.

왜 이 도구가 필요한가
    옛 사이트에서 **전남만 자료가 없습니다.** HTML 쪽 자체가 원본입니다.
    생성기(build-coast-points.ps1) 3번째 줄에 그대로 적혀 있습니다.

        "전남 point/*.html 은 읽기만 하고 고치지 않습니다"

    다른 8묶음 2,526곳은 자료에서 쪽이 만들어지는데, 전남만 반대입니다.
    jeonnam-extra.json 에 228곳이 있을 뿐, 나머지 849곳은 오직 HTML 안에만
    있습니다.

    그래서 전남은 늘 뒤처졌습니다 — 광고가 빠지고, 숫자가 낡고,
    새 기능이 안 들어갔습니다. 이 도구가 그것을 끝냅니다.

캐낸 뒤
    전남도 다른 권역과 **같은 자료 구조**를 갖습니다 (계약-02).
    그때부터 예외가 사라집니다.

쓰는 법
    python engine/extract_jeonnam.py            보여만 줍니다
    python engine/extract_jeonnam.py --write    data/raw/points/jeonnam.json 에 씁니다
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

# 자료가 나갈 자리. 시험이 딴 자리를 줄 수 있어야 합니다 —
# 안 그러면 멱등성 시험이 진짜 자료를 덮어씁니다 (2026-09-26)
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 쪽 이름에서 권역과 갈래를 읽습니다 — point/01_sinan_fishing.html
PAGE = re.compile(r'(\d\d)_([a-z]+)_(fishing|gleaning)\.html$')

# 카드 한 덩이. 다음 카드가 시작되거나 목록이 끝날 때까지
CARD = re.compile(
    r'<div class="card" id="point-(\d+)"([^>]*)>(.*?)(?=<div class="card" id="point-|</section>|</main>)',
    re.S)

ATTR = re.compile(r'data-(lat|lng|loc)="([^"]*)"')
# 이름 — "2. 고산 선착장" 처럼 앞에 번호가 붙습니다
NAME = re.compile(r'font-size:1\.08rem[^>]*>\s*(?:\d+\.\s*)?([^<]+?)\s*</div>')
BADGE = re.compile(r'<span class="badge[^"]*"[^>]*>\s*([^<]+?)\s*</span>')
FIELD = re.compile(r'<b[^>]*>\s*([^<:]+?)\s*:?\s*</b>\s*([^<]*)')
GRADE = re.compile(r'class="badge grade-([A-Z])"')


def 글자(s):
    """태그를 떼고 실체 참조를 풀어 사람이 읽는 글로"""
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = _html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def 나누기(s):
    """'감성돔·농어·우럭' 또는 '감성돔, 농어' 를 목록으로"""
    if not s:
        return []
    부분 = re.split(r'[·,/]|\s{2,}', s)
    return [x.strip() for x in 부분 if x.strip()]


def 카드읽기(권역, 갈래, 차례, 번호, 속성, 안쪽):
    a = dict((k, v) for k, v in ATTR.findall(속성))
    이름 = None
    m = NAME.search(안쪽)
    if m:
        이름 = 글자(m.group(1))

    # 이름표(배지) — 첫째는 등급 표시라 빼고, 나머지가 지형입니다
    배지 = [글자(x) for x in BADGE.findall(안쪽)]
    지형 = None
    for b in 배지:
        if b and not re.search(r'검증|확인|제보|완료|미확인', b):
            지형 = b
            break

    # 대상·추천·방법 같은 항목
    항목 = {}
    for 이름표, 값 in FIELD.findall(안쪽):
        항목[글자(이름표)] = 글자(값)

    등급 = None
    g = GRADE.search(속성 + 안쪽)
    if g:
        등급 = g.group(1)

    def 수(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    갈래표 = 'f' if 갈래 == 'fishing' else 'g'
    return {
        'id': '%s-%s-%03d' % (권역, 갈래표, 차례),
        '권역': 권역,
        '갈래': '낚시' if 갈래 == 'fishing' else '해루질',
        '이름': {'ko': 이름 or '', 'zh': None},
        '좌표': {'위도': 수(a.get('lat')), '경도': 수(a.get('lng'))},
        '지형': 지형,
        '대상': 나누기(항목.get('대상')),
        '철': 항목.get('추천') or 항목.get('시기') or None,
        '등급': 등급,
        '방법': 항목.get('방법') or 항목.get('채비') or None,
        '메모': 항목.get('메모') or 항목.get('참고') or None,
        '배로가나': bool(re.search(r'배로\s*이동|여객선', 안쪽)),
        '출입': '금지' if re.search(r'출입\s*금지|채취\s*금지', 안쪽)
                else '확인필요' if re.search(r'통제|제한|주의', 안쪽)
                else '자유',
        '_원본카드': int(번호),
    }


def main():
    쓰기 = '--write' in sys.argv
    쪽들 = sorted(glob.glob(os.path.join(OLD, 'point', '[0-9][0-9]_*.html')))
    if not 쪽들:
        print('전남 포인트 쪽을 찾지 못했습니다: %s' % os.path.join(OLD, 'point'))
        return 1

    print('전남 포인트를 HTML 에서 캐냅니다')
    print('  옛 사이트: %s' % OLD)
    print('  쪽 %d개' % len(쪽들))
    print('')

    모두 = []
    탈 = []
    권역별 = {}

    for p in 쪽들:
        m = PAGE.search(os.path.basename(p))
        if not m:
            continue
        _, 권역, 갈래 = m.groups()
        s = io.read(p, default='')
        카드들 = CARD.findall(s)
        for i, (번호, 속성, 안쪽) in enumerate(카드들, 1):
            항 = 카드읽기(권역, 갈래, i, 번호, 속성, 안쪽)
            # 검사 (계약-25)
            어디 = '%s (%s)' % (항['id'], 항['이름']['ko'] or '이름없음')
            if not 항['이름']['ko']:
                탈.append('%s — 이름을 못 읽음' % 항['id'])
            위, 경 = 항['좌표']['위도'], 항['좌표']['경도']
            if 위 is None or 경 is None:
                탈.append('%s — 좌표 없음' % 어디)
            else:
                if not (33.0 <= 위 <= 39.0):
                    탈.append('%s — 위도 %.4f 가 한반도 밖' % (어디, 위))
                if not (124.0 <= 경 <= 132.0):
                    탈.append('%s — 경도 %.4f 가 한반도 밖' % (어디, 경))
            모두.append(항)
            권역별.setdefault(권역, {'낚시': 0, '해루질': 0})
            권역별[권역][항['갈래']] += 1

    print('  권역        낚시  해루질    합')
    for 권역 in sorted(권역별):
        v = 권역별[권역]
        print('  %-12s %4d  %5d  %4d' % (권역, v['낚시'], v['해루질'], v['낚시'] + v['해루질']))
    print('  %-12s %4d  %5d  %4d' % ('합계',
                                     sum(v['낚시'] for v in 권역별.values()),
                                     sum(v['해루질'] for v in 권역별.values()),
                                     len(모두)))
    print('')

    # 캐낸 값이 얼마나 채워졌나 — 빈칸이 많으면 뽑기가 실패한 것입니다
    채움 = {}
    for k in ('지형', '대상', '철', '등급', '방법'):
        n = sum(1 for x in 모두 if x[k])
        채움[k] = n
    print('  캐낸 값이 채워진 비율')
    for k, n in 채움.items():
        print('    %-6s %4d / %d  (%.0f%%)' % (k, n, len(모두), 100.0 * n / max(len(모두), 1)))
    print('')

    if 탈:
        print('★ 살펴볼 것 %d건' % len(탈))
        for x in 탈[:10]:
            print('    %s' % x)
        if len(탈) > 10:
            print('    … 그 밖 %d건' % (len(탈) - 10))
        print('')

    if 쓰기:
        모두.sort(key=lambda x: x['id'])
        for x in 모두:
            x.pop('_원본카드', None)
        io.write_json(os.path.join(DATA, 'raw', 'points', 'jeonnam.json'), {
            '_설명': '전남 포인트. **옛 사이트의 HTML 에서 캐냈습니다** — 자료가 없었기 때문입니다. '
                     '손으로 고치려면 data/overrides/ 에 두세요',
            '_캐낸곳': 'point/[0-9][0-9]_*.html (쪽 %d개)' % len(쪽들),
            '포인트': 모두,
        })
        print('자료에 썼습니다: data/raw/points/jeonnam.json')
    else:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
