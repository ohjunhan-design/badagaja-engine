# -*- coding: utf-8 -*-
"""쪽마다 **보이는 것**이 있는지 봅니다. (주인 규칙 6-1)

★ 왜 생겼나 (2026-09-27)

    새 틀로 만든 416쪽에 **사진이 한 장도 없었습니다.**
    옛 사이트는 500장을 씁니다.

    그런데 판정 20개가 전부 PASS 였습니다. 어디에도
    「사진이 있는가」를 묻는 검사가 없었기 때문입니다.
    검사가 없으면 없는 것도 통과합니다.

    게다가 `build.py` 가 대표 사진 주소를 **자료를 안 보고
    지어내고** 있었습니다.

        지어낸 것   img/taean/hero.jpg        ← 없는 파일
        실제 파일   img/coast/taean-hero.jpg

    57권역 가운데 15곳만 맞았습니다. 공유 미리보기(og:image)가
    52갈래 깨진 채였습니다. 카톡·네이버로 나눠도 그림이 안 떴을
    것입니다.

무엇을 보나
    [1] 쪽마다 보이는 것이 있는가          (규칙 6-1)
    [2] 가리키는 그림 파일이 진짜 있는가    (지어낸 주소를 잡습니다)
    [3] 촬영자가 적혀 있는가               (규칙 5)
    [4] 설명에 이용허락 종류를 안 적었는가  (규칙 6)
    [5] og:image 가 가이드를 지키는가       (규칙 28)
    [6] 사진과 그림을 구별해 적었는가       (규칙 5)

쓰는 법
    python engine/check_photos.py
    python engine/check_photos.py --strict
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure   # noqa: E402
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []

# 명소 사진 제목에 들면 **다른 곳일 수 있는** 말 (2026-10-09)
#   「해수욕장」인데 제목이 「…역 승강장」이면 다른 곳입니다.
#   막지 않고 알립니다 — 이름이 맞는 것도 걸립니다.
다른장소말 = (
    '승강장', '플랫폼', '무덤', '대교', '주탑', '교량', '터널',
    '휴게소', '정류장', '공항', '성터', '산성', '읍성', '향교',
    '서원', '퇴적암', '지층', '노두', '박물관', '전시관', '기념관',
    '시청', '군청', '구청', '주민센터', '도서관',
    'station', 'platform', 'tomb', 'bridge', 'tunnel',
    'museum', 'fortress', 'airport', 'terminal',
)


# 쪽에 적으면 안 되는 말 — 이용허락 종류는 photos.html 에만 (규칙 6)
이용허락말 = re.compile(r'공공누리|CC BY|CC0|Public domain', re.I)


def 쪽들():
    # 쪽은 io.쪽들() 한 곳에서 모읍니다 (2026-10-06)
    return io.쪽들(NEW)


def 자료사진들():
    """`data/raw/photos.json` 이 적은 사진 목록. 못 읽으면 빈 것."""
    d = io.read_json(os.path.join(DATA, 'raw', 'photos.json'), default={})
    if isinstance(d, list):
        return d
    for 열쇠 in ('사진', 'photos', 'items'):
        if isinstance(d.get(열쇠), list):
            return d[열쇠]
    return []



def _몸통만(s):
    """머리(<header>)와 꼬리(<footer>)를 뺀 가운데만 돌려줍니다.

    로고는 머리·꼬리에 있습니다. 그것까지 세면
    「보이는 것이 있는가」 검사가 **영영 아무것도 못 잡습니다.**
    """
    몸 = s
    for 여는, 닫는 in (('<header', '</header>'), ('<footer', '</footer>')):
        while True:
            i = 몸.find(여는)
            if i < 0:
                break
            j = 몸.find(닫는, i)
            if j < 0:
                break
            몸 = 몸[:i] + 몸[j + len(닫는):]
    return 몸

def main():
    것들 = 쪽들()
    # ★ 「잴 것이 없습니다」로 **통과(0)** 를 내고 있었습니다 (2026-10-08)
    #   아무것도 안 본 것과 탈이 없는 것은 다릅니다.
    mustmeasure.있어야한다(것들, '쪽', 최소=50, 어디=NEW)
    if not 것들:
        print('잴 것이 없습니다 — site/ 에 쪽이 없습니다.')
        return 0

    print('쪽마다 보이는 것이 있는가 (주인 규칙 6-1)')
    print('  쪽 %d개' % len(것들))
    print('')

    # ── 0. 자료에 같은 사진이 두 번 적혀 있는가
    #
    #   ★ 2026-09-28 — 바깥 검수가 숫자를 의심해 찾아냈습니다
    #
    #     검수서에 「사진 264장」이라 적었는데 저장소에는 263장뿐이었습니다.
    #     바깥 검수가 **「숫자의 정의가 불명확한 것 자체가 위험 신호」**
    #     라고 해서 파고들었더니, 자료에 같은 줄이 두 번 있었습니다.
    #
    #         img/jeju/photo/jejusi-yongduam.jpg · 용두암   (같은 줄 두 번)
    #
    #     주인 규칙 29 는 「숫자는 자료에서 센다」인데,
    #     **자료에 겹친 줄이 있으면 센 숫자가 틀립니다.**
    #     사이트에 적히는 사진 수가 하나 많았습니다.
    print('[0] 자료에 같은 사진이 두 번 적혀 있는가')
    겹친것, 본것 = [], {}
    for x in 자료사진들():
        파일 = x.get('파일')
        if not 파일:
            continue
        if 파일 in 본것:
            겹친것.append('%s (%s · %s)'
                          % (파일, 본것[파일], x.get('제목') or '?'))
        else:
            본것[파일] = x.get('제목') or '?'
    if 겹친것:
        막음.append('자료에 같은 사진이 두 번 적힌 것 %d건' % len(겹친것))
        print('  ✗ 같은 사진이 두 번 적혀 있습니다 %d건' % len(겹친것))
        for x in 겹친것[:5]:
            print('      %s' % x)
        print('      자료에서 센 숫자가 틀어집니다 (주인 규칙 29)')
    else:
        print('  · 서로 다른 사진 %d장 — 겹친 줄이 없습니다' % len(본것))
    print('')

    # ★ **자료에 적힌 파일이 정말 있는가** (2026-10-09)
    #   명소 사진 대조표를 만들다 **빈 칸 7개**를 보았습니다.
    #   자료에는 「일광해수욕장」·「다대포해수욕장」처럼 적혀 있는데
    #   파일이 없었습니다. 쪽 검사는 **쪽에 걸린 것**만 보므로
    #   안 걸렸습니다 — 생성기가 없는 것을 조용히 건너뜁니다.
    #   그래서 **명소에 사진이 있다고 자료에 적어 두고도 안 보이는
    #   일**이 생깁니다 (기억 「약속한 것이 거기 있어야」).
    빈것 = []
    for x in 자료사진들():
        쪽길 = (x.get('파일') or '').strip()
        if not 쪽길:
            continue
        조각 = 쪽길.split('/')
        if any(os.path.exists(os.path.join(터, *조각))
               for 터 in (NEW, ROOT)):
            continue
        빈것.append('%s (%s · %s)'
                    % (쪽길, x.get('명소') or x.get('제목') or '?',
                       x.get('쓰임') or '-'))
    if 빈것:
        막음.append('자료에 적혔는데 파일이 없는 사진 %d장' % len(빈것))
        print('  ✗ 자료에 적혔는데 **파일이 없습니다** %d장' % len(빈것))
        for t in 빈것[:8]:
            print('      %s' % t)
        print('      자료에서 센 숫자가 틀어지고, 그 명소 칸이 빕니다')
    else:
        print('  · 자료에 적힌 사진이 모두 제자리에 있습니다')
    print('')

    # ★ **제목에 다른 장소 유형이 들었는가** (2026-10-09 · 알림)
    #   2026-10-09 명소 사진 일곱 장이 **전혀 다른 곳**이었습니다 —
    #   「일광해수욕장」은 일광**역 승강장**, 「오이도 빨간등대」는
    #   **무덤**, 「나정고운모래해변」은 **불가사리 접사**.
    #   자료 제목은 관광공사가 붙인 이름 그대로라 **이름만으로는
    #   못 가립니다.**
    #
    #   색(푸른 비율)으로 가려 보려다 버렸습니다 — 61장이 걸렸는데
    #   대부분 어종·노을 사진이었고 정작 문제의 사진은 안 걸렸습니다.
    #
    #   지피티 권고(2026-10-09) — 「기계가 의심 사진을 **좁히고**
    #   사람이 최종 확인」. 그래서 **막지 않고 알립니다.**
    #   「문무대왕릉 ← Underwater Tomb of King Munmu」처럼 이름이
    #   맞는 것도 걸립니다(그 사진은 완벽한 바다 사진입니다).
    #   최종 증거는 `engine/photo_sheet.py` 의 대조표입니다.
    다른유형 = []
    for x in 자료사진들():
        if (x.get('쓰임') or '') not in ('spot', 'hero'):
            continue
        제 = (x.get('제목') or '').lower()
        명 = (x.get('명소') or '').lower()
        걸린 = [말 for 말 in 다른장소말
                if 말 in 제 and 말 not in 명]
        if 걸린:
            다른유형.append('%s ← %s [%s]'
                            % (x.get('명소') or '?',
                               (x.get('제목') or '?')[:40],
                               ' · '.join(걸린)))
    if 다른유형:
        알림.append('제목에 다른 장소 유형이 든 사진 %d장 '
                    '(눈으로 보세요)' % len(다른유형))
        print('  ~ 제목에 **다른 장소 유형**이 든 사진 %d장'
              % len(다른유형))
        for t in 다른유형[:6]:
            print('      %s' % t)
        print('      engine/photo_sheet.py 로 대조표를 만들어 눈으로 봅니다')
    else:
        print('  · 제목에 다른 장소 유형이 든 사진이 없습니다')
    print('')

    # ── 1. 보이는 것이 있는가
    print('[1] 쪽마다 보이는 것이 있는가')
    사진없는쪽 = []
    모든그림 = {}
    for p in 것들:
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        s = io.read(p, default='')
        그림들 = re.findall(r'<img[^>]+src="([^"]+)"', s)
        # ★ **눈으로 읽히는 것은 사진만이 아닙니다** (2026-09-29)
        #   주인 규칙 6-1 은 「사진뿐 아니라 **지도·막대·아이콘·카드**처럼
        #   눈으로 읽히는 것」을 함께 쓰라고 했습니다.
        #   그런데 이 검사는 <img> 만 세어, 축제 쪽에 넣은
        #   **달별 축제 수 막대**(SVG)를 「없다」고 했습니다.
        #
        #   ★ 머리·꼬리는 **뺍니다.** 로고가 모든 쪽에 있어
        #     그것까지 세면 이 검사가 영영 아무것도 못 잡습니다.
        몸통 = _몸통만(s)
        보임 = bool(그림들) or ('<svg' in 몸통)
        if not 보임:
            사진없는쪽.append(이름)
        모든그림[이름] = (그림들, s)
    print('      보이는 것이 있는 쪽 %d개 · 없는 쪽 %d개'
          % (len(것들) - len(사진없는쪽), len(사진없는쪽)))
    if 사진없는쪽:
        막음.append('보이는 것이 없는 쪽 %d개' % len(사진없는쪽))
        print('  ✗ %d쪽에 그림이 하나도 없습니다' % len(사진없는쪽))
        for x in 사진없는쪽[:8]:
            print('      %s' % x)
        print('      → 글만 있는 쪽에는 손님이 머물지 않습니다 (규칙 6-1)')
    else:
        print('  · 모든 쪽에 보이는 것이 있습니다')
    print('')

    # ── 2. 가리키는 파일이 진짜 있는가
    print('[2] 가리키는 그림 파일이 진짜 있는가')
    없는파일 = []
    본것 = set()
    for 이름, (그림들, _) in 모든그림.items():
        뿌리 = os.path.dirname(os.path.join(NEW, 이름.replace('/', os.sep)))
        for 주소 in 그림들:
            if 주소.startswith(('http://', 'https://', 'data:')):
                continue
            깨끗 = 주소.split('?')[0].split('#')[0]
            실제 = os.path.normpath(os.path.join(뿌리,
                                                 깨끗.replace('/', os.sep)))
            if 실제 in 본것:
                continue
            본것.add(실제)
            if not os.path.isfile(실제):
                없는파일.append('%s — %s' % (이름, 주소))
    print('      본 그림 %d갈래 · 없는 것 %d갈래'
          % (len(본것), len(없는파일)))
    if 없는파일:
        막음.append('없는 그림을 가리키는 곳 %d갈래' % len(없는파일))
        print('  ✗ %d갈래가 없는 파일을 가리킵니다' % len(없는파일))
        for x in 없는파일[:8]:
            print('      %s' % x)
        print('      → 주소를 짐작해 만들지 마세요. 자료에서 읽습니다.')
    else:
        print('  · 가리키는 그림이 모두 있습니다')
    print('')

    # ── 3·4·6. 설명을 제대로 적었는가
    print('[3] 사진 설명을 제대로 적었는가 (규칙 5·6)')
    촬영자없음, 허락적음, 설명없음 = [], [], []
    for 이름, (_, s) in 모든그림.items():
        for m in re.finditer(r'<figure[^>]*class="([^"]*)"[^>]*>(.*?)</figure>',
                             s, re.S):
            반, 안 = m.group(1), m.group(2)
            # ★ **설명을 묻기 전에 사진인지부터 봅니다** (2026-10-01)
            #   아래에 사진·그림을 가리는 줄이 이미 있는데, 그보다
            #   **먼저** 설명을 물어서 **우리가 직접 그린 그림**까지
            #   「설명이 없습니다」로 막았습니다.
            #
            #   물때 쪽(muldae.html)의 선그림 일곱 장이 그렇게 잡혀
            #   배포가 멈췄습니다. 그림에는 `aria-label` 로 뜻을
            #   적어 두었고, 그것이 올바른 방법입니다. 사진이 아니면
            #   촬영자도 설명도 요구하지 않습니다 (규칙 5).
            if '<img' not in 안:
                continue
            설명 = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', 안, re.S)
            글 = re.sub(r'<[^>]+>', '', 설명.group(1)).strip() if 설명 else ''
            if not 글:
                설명없음.append(이름)
                continue
            if 이용허락말.search(글):
                허락적음.append('%s — %s' % (이름, 글[:40]))
            # ★ **사진과 직접 그린 그림을 가릅니다** (2026-09-29)
            #
            #   규칙 5·6 이 촬영자를 요구하는 까닭은 **남의 사진**을
            #   쓰기 때문입니다. 직접 그린 그림에는 촬영자가 없고,
            #   지어내서도 안 됩니다(규칙 5).
            #
            #   사진이란 <img> 로 넣은 것입니다. <svg> 만 있으면
            #   우리가 그린 것입니다.
            #
            #   겪은 일: 어종 쪽에 삽화 246개를 되살리자 사진
            #   검사가 「촬영자가 빠진 곳 246개」라 했습니다.
            #   그림에 촬영자를 적을 수는 없습니다.
            사진인가 = '<img' in 안
            # ★ **채비 안내도는 우리가 만든 그림입니다** (2026-10-01)
            #   `<img>` 이지만 남이 찍은 사진이 아닙니다.
            #   `rig-guide` 칸에는 `data/img/rig/` 의 우리 안내도만
            #   들어갑니다. 촬영자가 없으니 「그림 · …」이 맞습니다.
            그린것 = ('photo--drawn' in 반) or ('rig-guide' in 반)
            그린것 = 그린것 or (not 사진인가)
            if not 사진인가 and 'ls-card' in 반:
                # 배우는 차례 카드의 글은 사진 설명이 아니라
                # 가르치는 본문입니다. 설명 규칙을 대지 않습니다.
                continue
            if 그린것:
                # 그림은 「그림 · …」으로 적어야 합니다
                if not 글.startswith('그림'):
                    촬영자없음.append('%s — 그림인데 「그림」이라 안 적었습니다'
                                      % 이름)
            else:
                # 사진은 「사진 · 제목 · 촬영자」
                if not 글.startswith('사진'):
                    촬영자없음.append('%s — 사진인데 「사진」이라 안 적었습니다'
                                      % 이름)
                elif 글.count('·') < 2:
                    촬영자없음.append('%s — 촬영자가 없습니다: %s'
                                      % (이름, 글[:40]))
    print('      설명이 없는 쪽 %d · 촬영자가 빠진 곳 %d · '
          '이용허락 종류를 적은 곳 %d'
          % (len(설명없음), len(촬영자없음), len(허락적음)))
    if 설명없음:
        막음.append('사진 설명이 없는 곳 %d개' % len(설명없음))
        for x in 설명없음[:4]:
            print('  ✗ %s' % x)
    if 촬영자없음:
        막음.append('촬영자가 빠진 곳 %d개' % len(촬영자없음))
        for x in 촬영자없음[:5]:
            print('  ✗ %s' % x)
        print('      → 촬영자는 자료가 준 값만 적습니다 (규칙 5).')
        print('        지어내지 말고, 없으면 그림으로 밝히세요.')
    if 허락적음:
        막음.append('쪽에 이용허락 종류를 적은 곳 %d개' % len(허락적음))
        for x in 허락적음[:5]:
            print('  ✗ %s' % x)
        print('      → 「공공누리 제1유형」 같은 종류는 photos.html 에만')
        print('        둡니다 (규칙 6).')
    if not (설명없음 or 촬영자없음 or 허락적음):
        print('  · 설명을 규칙대로 적었습니다')
    print('')

    # ── 5. og:image
    # ── [4] 대표 사진이 **그 권역 것**인가
    #
    #   ★ 2026-09-29 바깥 검수 12차
    #
    #     「신안 페이지에 다른 지역 사진이 들어가도 파일 자체는
    #       정상적인 이미지이기 때문에 일반적인 이미지 검사는
    #       통과할 수 있습니다. 사진의 **존재** 검사와 사진의
    #       **의미적 매칭** 검사는 별개로 생각해야 합니다.」
    #
    #     재 보니 57권역이 다 맞았습니다. 그러나 **맞는지 재는
    #     검사가 없었습니다.** 우연히 맞은 것일 수도 있습니다.
    #
    #   첫 화면은 전국 쪽이라 어느 권역 사진이든 들어갑니다.
    print('[4] 대표 사진이 그 권역 것인가')
    사진표 = {}
    for x in 자료사진들():
        if x.get('파일'):
            사진표[x['파일']] = x
    첫화면들 = {'index'}
    어긋난것, 원장에없는것, 본쪽 = [], [], 0
    읽은쪽 = 0
    for 길 in 쪽들():
        이름 = os.path.basename(길)[:-5]
        if 이름 in 첫화면들 or os.sep in os.path.relpath(길, NEW):
            continue                       # 권역 쪽만 봅니다
        글 = io.read(길, default='')
        읽은쪽 += 1 if 글 else 0
        m = re.search(r'<img[^>]*src="([^"]*img/[^"]+)"', 글)
        if not m:
            continue
        본쪽 += 1
        사진길 = re.sub(r'^\.\./', '', m.group(1)).lstrip('./')
        한장 = 사진표.get(사진길)
        if 한장 is None:
            원장에없는것.append('%s → %s' % (이름, 사진길))
        elif 한장.get('권역') and 한장['권역'] != 이름:
            어긋난것.append('%s 쪽인데 사진은 %s 것 (%s)'
                            % (이름, 한장['권역'], 사진길))
    if not 본쪽:
        print('  ~ 권역 쪽이 없습니다 — 잴 것이 없습니다.')
    else:
        if 원장에없는것:
            막음.append('사진 원장에 없는 대표 사진 %d장' % len(원장에없는것))
            print('  ✗ 원장(photos.json)에 없는 대표 사진 %d장'
                  % len(원장에없는것))
            for x in 원장에없는것[:5]:
                print('      %s' % x)
        if 어긋난것:
            막음.append('다른 권역 사진을 쓴 쪽 %d개' % len(어긋난것))
            print('  ✗ 다른 권역 사진을 쓴 쪽 %d개' % len(어긋난것))
            for x in 어긋난것[:5]:
                print('      %s' % x)
            print('      → 파일은 멀쩡해도 **그 고장 바다가 아닙니다.**')
    # ── 히어로 사진이 **너무 작지 않은가** (2026-10-01) ──
    #
    #   바깥 검수 지적 — 「작은 사진은 키운다고 히어로급이 되지
    #   않습니다. 픽셀은 늘어도 세부가 돌아오지 않습니다」
    #
    #   맞습니다. 양양이 699×466 이었습니다. 다른 권역은 모두
    #   940×626 안팎인데 양양만 흐렸습니다. 같은 권역에 940짜리가
    #   있어 바꿨습니다. **다시 이런 일이 없게 여기서 막습니다.**
    #
    #   900px 로 잡은 까닭 — 관광공사가 주는 원본이 940px 입니다.
    #   그보다 작으면 **어디선가 줄인 것**입니다.
    # ── 자료에 적혔는데 **아무 데도 안 붙는** 사진 ──────
    #
    #   2026-10-01 — 제주 명소 사진 29장이 그랬습니다.
    #   photos.json 에 적혀 있는데 권역도 쓰임도 비어 있어
    #   어느 쪽에도 안 붙고 파일만 14MB 올라가고 있었습니다.
    #
    #   주인 규칙 6-1 — 좋은 바다 사진을 자료에 쌓아 두고
    #   안 보여 주면 **없는 것과 같습니다.**
    #
    #   ★ 막지 않고 알립니다. 일부러 자료에만 두는 경우가
    #     있을 수 있고, 지우는 일은 만드는 일보다 어려워야
    #     합니다 (계약-17).
    print('')
    print('[10] 자료에 적혔는데 아무 데도 안 붙는 사진')
    떠도는것 = []
    for 한장 in 자료사진들():
        파일 = 한장.get('파일')
        if not 파일:
            continue
        if not 한장.get('권역') and not 한장.get('쓰임'):
            떠도는것.append('%s (%s)'
                            % (파일, 한장.get('제목') or '제목 없음'))
    if 떠도는것:
        알림.append('권역·쓰임이 비어 안 붙는 사진 %d장'
                    % len(떠도는것))
        print('  ~ 권역도 쓰임도 비어 어느 쪽에도 안 붙는 사진 %d장'
              % len(떠도는것))
        for x in 떠도는것[:8]:
            print('      %s' % x)
        if len(떠도는것) > 8:
            print('      … 그 밖 %d장' % (len(떠도는것) - 8))
        print('      → 지우지 마십시오. **권역과 쓰임을 채우면**')
        print('        권역 쪽의 「이 고장의 다른 풍경」에 나옵니다.')
    else:
        print('  · 자료에 적힌 사진이 모두 어딘가에 붙습니다')
    print('')
    print('[9] 히어로 사진이 너무 작지 않은가')
    작은히어로 = []
    for 한장 in 자료사진들():
        if not str(한장.get('쓰임') or '').startswith('hero'):
            continue
        가로 = 한장.get('가로') or 0
        if 가로 and 가로 < 900:
            작은히어로.append('%s %dx%d (%s)'
                              % (한장.get('파일'), 가로,
                                 한장.get('세로') or 0,
                                 한장.get('제목') or ''))
    if 작은히어로:
        막음.append('히어로로 쓰기엔 작은 사진 %d장' % len(작은히어로))
        print('  ✗ 히어로로 쓰기엔 작은 사진 %d장' % len(작은히어로))
        for x in 작은히어로[:8]:
            print('      %s' % x)
        print('      → 키운다고 또렷해지지 않습니다.')
        print('      → 같은 권역의 큰 사진으로 **바꾸십시오**.')
    else:
        print('  · 히어로 사진이 모두 가로 900px 이상입니다')
        if not 원장에없는것 and not 어긋난것:
            print('  · 권역 쪽 %d개의 대표 사진이 모두 그 고장 것입니다'
                  % 본쪽)
    print('')
    # ★ 목록은 있는데 **내용을 하나도 못 읽으면** 못잼입니다
    mustmeasure.있어야한다(range(읽은쪽), '읽은 쪽', 최소=50, 어디=NEW)

    print('[5] 공유 미리보기 그림이 제대로인가 (규칙 28)')
    사진표 = io.read_json(os.path.join(DATA, 'raw', 'photos.json'),
                          default={}) or {}
    크기표 = dict((x.get('파일'), (x.get('가로'), x.get('세로')))
                  for x in (사진표.get('사진') or []) if x.get('파일'))
    og없음, og깨짐, og비율 = [], [], []
    같은것 = {}
    for 이름, (_, s) in 모든그림.items():
        m = re.search(r'og:image"\s+content="([^"]+)"', s)
        if not m:
            og없음.append(이름)
            continue
        주소 = m.group(1)
        상대 = re.sub(r'^https?://[^/]+/', '', 주소)
        같은것.setdefault(상대, []).append(이름)
        실제 = os.path.join(NEW, 상대.replace('/', os.sep))
        if not os.path.isfile(실제):
            og깨짐.append('%s — %s' % (이름, 주소))
        넓, 높 = 크기표.get(상대, (None, None))
        if 넓 and 높:
            if 넓 < 150 or 높 < 150 or 넓 / float(높) > 3 or 높 / float(넓) > 3:
                og비율.append('%s — %dx%d' % (상대, 넓, 높))
    print('      og:image 가 없는 쪽 %d · 없는 파일을 가리키는 쪽 %d '
          '· 가이드를 어긴 그림 %d'
          % (len(og없음), len(og깨짐), len(set(og비율))))
    if og없음:
        막음.append('og:image 가 없는 쪽 %d개' % len(og없음))
        for x in og없음[:4]:
            print('  ✗ %s' % x)
    if og깨짐:
        막음.append('og:image 가 없는 파일을 가리키는 쪽 %d개' % len(og깨짐))
        for x in og깨짐[:5]:
            print('  ✗ %s' % x)
        print('      → 이것이 2026-09-27 에 52갈래 깨져 있던 그 탈입니다.')
    if og비율:
        막음.append('og:image 가이드를 어긴 그림 %d개' % len(set(og비율)))
        for x in sorted(set(og비율))[:5]:
            print('  ✗ %s' % x)
    # 쪽마다 다른 사진이어야 합니다 (규칙 28)
    많이겹침 = [(k, v) for k, v in 같은것.items() if len(v) > 60]
    if 많이겹침:
        알림.append('여러 쪽이 같은 og:image 를 씁니다 %d갈래' % len(많이겹침))
        print('  ~ 여러 쪽이 같은 그림을 씁니다')
        for k, v in sorted(많이겹침, key=lambda x: -len(x[1]))[:4]:
            print('      %-42s %d쪽' % (k, len(v)))
        print('      가이드는 **쪽마다 다른 사진**을 권합니다 (규칙 28).')
    if not (og없음 or og깨짐 or og비율):
        print('  · 공유 미리보기가 모두 제대로입니다')
    print('')

    # ── 걸러 놓은 사진이 쪽에 남아 있는가
    #
    #   ★ 2026-09-29 주인 지적 — 「명소들이 이미지 잘못들어간게 많아」
    #
    #   다대포해수욕장 자리에 **지하철역 승강장** 사진이 실려 있었습니다.
    #   눈으로 골라 photo-reject.json 에 적었는데, **그 목록이 실제로
    #   먹었는지**는 아무도 재지 않았습니다. 여기서 잽니다.
    #
    #   자료만 고치고 엔진이 안 읽으면 아무 일도 안 일어납니다.
    print('[거른 사진] 명소와 다른 사진이 쪽에 남았나')
    _거를것 = io.read_json(os.path.join(DATA, 'raw', 'photo-reject.json'),
                           default={}) or {}
    _거른길 = [x.get('파일') for x in _거를것.get('거를것', []) if x.get('파일')]
    _남은것 = []
    for _길 in 것들:
        _글 = io.read(_길, default=chr(39)+chr(39)) or chr(39)+chr(39)
        for _사 in _거른길:
            # 쪽마다 상대 주소가 다르니 **파일 이름만** 견줍니다
            if os.path.basename(_사) in _글:
                _남은것.append((_길, os.path.basename(_사)))
    if _거른길 and _남은것:
        막음.append('거르기로 한 사진이 아직 %d곳에 있습니다' % len(_남은것))
        for _길, _이 in _남은것[:6]:
            print('  ✗ %s 에 %s' % (_길, _이))
        print('      → data.py 사진들() 이 photo-reject.json 을 읽는지 보세요.')
    elif _거른길:
        print('  · 걸러 놓은 %d장이 어느 쪽에도 없습니다' % len(_거른길))
    else:
        print('  · 거를 사진이 없습니다')
    print('')

    # ── 사진이 **정말 그 명소에서 찍혔는가** (좌표로)
    #
    #   ★ 2026-09-29 주인 제안
    #     「지역 명소 사진을 쓸 때 사진에 나온 곳 주소가 관광지 주소와
    #       동일했으면 더 좋겠어. 검수할 때 이렇게 검수하면 더 좋지 않을까?」
    #
    #   맞는 말씀입니다. **이름으로는 못 가립니다.**
    #     「다대포해수욕장역」과 「다대포해수욕장」은 이름이 거의 같은데
    #     한쪽은 지하철역이고 한쪽은 바다입니다.
    #   **좌표는 못 속입니다.**
    #
    #   위키미디어가 사진 좌표를 주므로 명소 좌표와 거리를 재어
    #   data/raw/photo-distance.json 에 적어 둡니다.
    print('[사진 거리] 사진이 정말 그 명소에서 찍혔나 (주인 제안)')
    _거리 = io.read_json(os.path.join(DATA, 'raw', 'photo-distance.json'),
                         default={}) or {}
    _km = _거리.get('거리km') or {}
    _먼것 = [(k, v) for k, v in _km.items() if v > 3]
    _좀먼것 = [(k, v) for k, v in _km.items() if 1 < v <= 3]
    if _먼것:
        막음.append('명소와 3km 넘게 떨어진 사진 %d장' % len(_먼것))
        for k, v in sorted(_먼것, key=lambda t: -t[1])[:6]:
            print('  ✗ %.1fkm  %s' % (v, k))
        print('      → photo-reject.json 에 적어 거르세요.')
    if _좀먼것:
        print('  ~ 1~3km 인 사진 %d장 (넓은 해변·섬이면 그럴 수 있습니다)'
              % len(_좀먼것))
        for k, v in sorted(_좀먼것, key=lambda t: -t[1])[:3]:
            print('      %.2fkm  %s' % (v, k))
    if _km and not _먼것:
        print('  · 잰 %d장이 모두 명소에서 3km 안입니다' % len(_km))
    # 못 잰 것은 **숨기지 않습니다** — 모르는 것을 안다고 하지 않습니다
    _명소사진수 = len([x for x in 자료사진들() if x.get('쓰임') == 'spot'])
    _못잰 = _명소사진수 - len(_km)
    if _못잰 > 0:
        print('  ~ %d장은 **찍은 곳을 몰라 못 쟀습니다**' % _못잰)
        print('      (한국관광공사 사진은 좌표를 안 줍니다. '
              '제목이 명소 이름과 같아 그것으로 봅니다)')
    print('')

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 사람은 눈으로 봅니다. 글만 있는 쪽은 아무리 내용이')
        print('    옳아도 손님이 머물지 않습니다 (주인 규칙 6-1).')
        return 1 if '--strict' in sys.argv else 0

    print('쪽 %d개에 모두 보이는 것이 있고, 설명도 규칙대로입니다.'
          % len(것들))
    return 0


if __name__ == '__main__':
    sys.exit(main())
