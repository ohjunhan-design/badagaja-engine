# -*- coding: utf-8 -*-
"""사이트 구조를 **그림 한 장**으로 그립니다.

★ 2026-09-27 주인 지시
  「두 번째 도전의 사이트 맵을 이해하기 쉽게 그림으로 만들어서
    나에게 보여줘」

  글로 적은 목록은 416쪽이 어떻게 얽혀 있는지 한눈에 안 들어옵니다.
  규칙 6-1 — 사람은 눈으로 봅니다.

★ 숫자는 **자료에서 셉니다** (주인 규칙 29)
  묶음 수·권역 수·포인트 수를 손으로 적지 않습니다. 자료가 늘면
  그림도 저절로 맞습니다.

쓰는 법
    python engine/make_sitemap_pic.py            무엇이 그려질지 봅니다
    python engine/make_sitemap_pic.py --write    data-private/ 에 씁니다
"""
import os
import sys
import glob
import html
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io    # noqa: E402
from engine.data import 자료   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 색 — assets/css/site.css 와 같은 갈래
크림 = '#FDF6EC'
바탕 = '#FFFFFF'
글 = '#2B2116'
흐린글 = '#7A6A58'
줄 = '#E3D8C6'
주황 = '#C07B22'
짙은 = '#2E3A32'
바다 = '#2F5D57'


def 쪽세기():
    갈 = collections.Counter()
    for p in glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True):
        상 = os.path.relpath(p, NEW).replace(os.sep, '/')
        if 상 == 'index.html':
            갈['첫화면'] += 1
        elif '/' not in 상:
            갈['권역·묶음'] += 1
        else:
            갈[상.split('/')[0]] += 1
    return 갈


def 상자(x, y, w, h, 채움, 테두리, r=12, 굵기=1.5):
    return ('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" '
            'fill="%s" stroke="%s" stroke-width="%g"/>'
            % (x, y, w, h, r, 채움, 테두리, 굵기))


def 글자(x, y, s, 크기=13, 색=None, 굵기=600, 가운데=True):
    return ('<text x="%g" y="%g" font-size="%g" fill="%s" '
            'font-weight="%s" text-anchor="%s" '
            'font-family="Malgun Gothic,AppleGothic,sans-serif">%s</text>'
            % (x, y, 크기, 색 or 글, 굵기,
               'middle' if 가운데 else 'start', html.escape(s)))


def 선(x1, y1, x2, y2, 색=None, 굵기=1.6, 점선=False):
    ㄷ = ' stroke-dasharray="5 4"' if 점선 else ''
    return ('<path d="M%g %g L%g %g" stroke="%s" stroke-width="%g" '
            'fill="none"%s/>' % (x1, y1, x2, y2, 색 or 줄, 굵기, ㄷ))


def 굽은선(x1, y1, x2, y2, 색=None, 굵기=1.6):
    가운데y = (y1 + y2) / 2.0
    return ('<path d="M%g %g C %g %g, %g %g, %g %g" stroke="%s" '
            'stroke-width="%g" fill="none"/>'
            % (x1, y1, x1, 가운데y, x2, 가운데y, x2, y2, 색 or 줄, 굵기))


def 그리기():
    d = 자료()
    갈 = 쪽세기()
    묶음차례 = d.색인['묶음차례']
    묶음별 = d.묶음별셈()
    모든쪽 = sum(갈.values())

    W, H = 1500, 1180
    조각 = []
    조각.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
                'width="%d" height="%d" font-family="Malgun Gothic,sans-serif">'
                % (W, H, W, H))
    조각.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, 크림))

    # ── 머리
    조각.append(글자(W / 2, 52, '바다가자닷컴 — 두번째도전 사이트 구조',
                     28, 글, 800))
    조각.append(글자(W / 2, 82,
                     '쪽 %d개 · 묶음 %d · 권역 %d · 포인트 %s곳 '
                     '(자료에서 센 값입니다)'
                     % (모든쪽, len(묶음차례), len(d.권역들),
                        '{:,}'.format(d.셈())),
                     14, 흐린글, 500))

    # ── 1층: 첫 화면
    첫x, 첫y, 첫w, 첫h = W / 2 - 150, 112, 300, 62
    조각.append(상자(첫x, 첫y, 첫w, 첫h, 짙은, 짙은, 14))
    조각.append(글자(W / 2, 첫y + 27, '첫 화면  /', 17, '#FFF6E8', 800))
    조각.append(글자(W / 2, 첫y + 47, '지도 · 검색 · 물때 · 01~06 걸음',
                     11.5, 'rgba(255,246,232,.78)', 500))

    # ── 2층: 큰 갈래 넷
    갈래들 = [
        ('전국 바다지도', '묶음 %d곳' % len(묶음차례), 주황),
        ('물때', 'tide/ (옛 쪽)', 바다),
        ('잡기', '해루질 %d · 낚시 %d'
         % (len(d.안내('해루질')), len(d.안내('낚시'))), '#1E8A5F'),
        ('축제·여행', '축제 %d개' % len(d.축제들), '#D9558A'),
    ]
    칸w, 칸h, 사이 = 260, 58, 40
    모두w = 칸w * len(갈래들) + 사이 * (len(갈래들) - 1)
    시작x = (W - 모두w) / 2
    이층y = 228
    for i, (이름, 밑, 색) in enumerate(갈래들):
        x = 시작x + i * (칸w + 사이)
        조각.append(굽은선(W / 2, 첫y + 첫h, x + 칸w / 2, 이층y, 줄, 2))
        조각.append(상자(x, 이층y, 칸w, 칸h, 바탕, 색, 12, 2))
        조각.append(글자(x + 칸w / 2, 이층y + 25, 이름, 15, 색, 800))
        조각.append(글자(x + 칸w / 2, 이층y + 44, 밑, 11.5, 흐린글, 500))

    # ── 3층: 묶음 아홉
    삼층y = 352
    조각.append(글자(60, 삼층y - 14, '묶음 %d곳 — 지도에서 고릅니다'
                     % len(묶음차례), 13, 흐린글, 700, False))
    묶w, 묶h = 152, 72
    사이2 = 12
    한줄 = 9
    전체w = 묶w * 한줄 + 사이2 * (한줄 - 1)
    시작x2 = (W - 전체w) / 2
    묶음자리 = {}
    for i, 묶 in enumerate(묶음차례):
        x = 시작x2 + i * (묶w + 사이2)
        이름 = d.색인['묶음이름'][묶].get('ko') or 묶
        권역수 = sum(1 for r in d.권역들 if r['묶음'] == 묶)
        묶음자리[묶] = (x + 묶w / 2, 삼층y + 묶h)
        조각.append(굽은선(시작x + 칸w / 2, 이층y + 칸h,
                          x + 묶w / 2, 삼층y, 줄, 1.2))
        조각.append(상자(x, 삼층y, 묶w, 묶h, 바탕, 줄, 11))
        조각.append(글자(x + 묶w / 2, 삼층y + 26, 이름, 14, 글, 800))
        조각.append(글자(x + 묶w / 2, 삼층y + 45, '%d권역' % 권역수,
                         11.5, 흐린글, 500))
        조각.append(글자(x + 묶w / 2, 삼층y + 61,
                         '포인트 %s' % '{:,}'.format(묶음별.get(묶, 0)),
                         11, 주황, 700))

    # ── 4층: 권역
    사층y = 500
    조각.append(상자(시작x2, 사층y, 전체w, 76, 바탕, 주황, 12, 2))
    조각.append(글자(W / 2, 사층y + 30,
                     '권역 %d곳 — 태안 · 신안 · 여수 · 거제 …'
                     % len(d.권역들), 16, 주황, 800))
    조각.append(글자(W / 2, 사층y + 54,
                     '물때표 7일 · 포인트 · 제철 어종 · 먹거리 · 해안 명소 '
                     '· 축제 · 여행 코스', 12, 흐린글, 500))
    for 묶, (mx, my) in 묶음자리.items():
        조각.append(굽은선(mx, my, mx, 사층y, 줄, 1.2))

    # ── 5층: 잎 쪽들
    오층y = 636
    잎들 = [
        ('포인트 목록', 'point/', 갈.get('point', 0),
         '권역마다 낚시·해루질 두 갈래\n지도에 핀 %s개'
         % '{:,}'.format(d.셈()), 주황),
        ('축제', 'festival/', 갈.get('festival', 0),
         '달마다 걸러 보기\n권역별 축제 쪽', '#D9558A'),
        ('해루질 대상', 'catch/', 갈.get('catch', 0),
         '바지락 · 맛조개 · 낙지 …\n시기 · 자리 · 잡는 법', '#1E8A5F'),
        ('낚시 어종', 'fish/', 갈.get('fish', 0),
         '우럭 · 감성돔 · 광어 …\n채비 · 입질 자리', 바다),
    ]
    잎w, 잎h, 잎사이 = 330, 116, 26
    잎전체 = 잎w * len(잎들) + 잎사이 * (len(잎들) - 1)
    잎시작 = (W - 잎전체) / 2
    for i, (이름, 길, 수, 밑, 색) in enumerate(잎들):
        x = 잎시작 + i * (잎w + 잎사이)
        조각.append(굽은선(W / 2, 사층y + 76, x + 잎w / 2, 오층y, 줄, 1.4))
        조각.append(상자(x, 오층y, 잎w, 잎h, 바탕, 색, 12, 2))
        조각.append(글자(x + 잎w / 2, 오층y + 28, 이름, 15.5, 색, 800))
        조각.append(글자(x + 잎w / 2, 오층y + 50, '%s  ·  %d쪽' % (길, 수),
                         12, 흐린글, 600))
        for k, 줄글 in enumerate(밑.split('\n')):
            조각.append(글자(x + 잎w / 2, 오층y + 74 + k * 18, 줄글,
                             11.5, 흐린글, 500))

    # ── 아래: 남기는 옛 쪽
    아래y = 800
    조각.append(상자(잎시작, 아래y, 잎전체, 96, '#F3EADA', 줄, 12, 1.5))
    조각.append(글자(W / 2, 아래y + 28,
                     '서버에 그대로 두는 옛 쪽 — 새 틀이 안 만듭니다',
                     14.5, 짙은, 800))
    조각.append(글자(W / 2, 아래y + 52,
                     'tide/ (전국 물때표) · guide/ · travel/ · gear.html '
                     '· rule.html · photos.html · about.html …',
                     11.5, 흐린글, 500))
    조각.append(글자(W / 2, 아래y + 74,
                     'zh-cn/ 중국어판 190쪽 — 2차 출시 과제로 미뤘습니다',
                     11.5, 흐린글, 500))
    조각.append(굽은선(W / 2, 오층y + 잎h, W / 2, 아래y, 줄, 1.4))

    # ── 맨 아래: 자료와 엔진
    엔진y = 930
    조각.append(상자(120, 엔진y, W - 240, 190, 바탕, 짙은, 14, 2))
    조각.append(글자(W / 2, 엔진y + 30,
                     '이 모든 쪽을 만드는 것 — 엔진', 16, 짙은, 800))
    조각.append(글자(W / 2, 엔진y + 52,
                     '쪽은 손으로 안 만듭니다. 자료가 바뀌면 '
                     '416쪽이 함께 바뀝니다 (계약-01)', 11.5, 흐린글, 500))
    엔진들 = [
        ('자료', 'data/raw/*.json', '포인트 · 권역 · 축제 · 어종\n'
         '사진 264장 · 지도 좌표'),
        ('생성기', 'engine/build.py', '자료 → 쪽 416개\n'
         '숫자는 셉니다 (규칙 29)'),
        ('검사기', 'engine/check_*.py', '20개 항목 + 덧검사\n'
         '어기면 배포가 멈춥니다'),
        ('판정', 'engine/gate.py', 'GO / NO-GO 를 기계가\n'
         '못 잰 것은 통과가 아님'),
    ]
    ew = (W - 300) / len(엔진들)
    for i, (이름, 길, 밑) in enumerate(엔진들):
        x = 150 + i * ew
        if i:
            조각.append(선(x - 12, 엔진y + 76, x - 12, 엔진y + 172, 줄, 1))
        조각.append(글자(x + ew / 2 - 12, 엔진y + 96, 이름, 14, 짙은, 800))
        조각.append(글자(x + ew / 2 - 12, 엔진y + 116, 길, 11, 주황, 600))
        for k, 줄글 in enumerate(밑.split('\n')):
            조각.append(글자(x + ew / 2 - 12,엔진y + 138 + k * 17, 줄글,
                             11, 흐린글, 500))

    조각.append(글자(W / 2, H - 16,
                     '숫자는 모두 자료에서 센 값입니다 — 손으로 적지 '
                     '않았습니다 (주인 규칙 29)', 11, 흐린글, 500))
    조각.append('</svg>')
    return ''.join(조각), 모든쪽


def main():
    쓰기 = '--write' in sys.argv
    그림, 쪽수 = 그리기()
    print('사이트 구조 그림')
    print('  쪽 %d개를 그렸습니다 · %.1fKB' % (쪽수, len(그림) / 1024.0))
    if 쓰기:
        # ★ 근거·설명 자료는 웹에 안 냅니다 (주인 규칙 11)
        나갈파일 = os.path.join(
            os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site'),
            'data-private', '사이트구조.svg')
        io.write(나갈파일, 그림)
        print('  썼습니다: data-private/사이트구조.svg')
    else:
        print('  --write 를 붙이면 data-private/ 에 씁니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
