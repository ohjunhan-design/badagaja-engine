# -*- coding: utf-8 -*-
"""그림 안에서 **그림 밖으로 뻗는 글자**를 찾습니다.

★ 2026-09-29 — 삽화를 되살리자 375px 에서 글자가 잘렸습니다

        「① 방수 장갑 — 젖은 손이 가장 빨리 식습니다」
         → 「…가장 빨리」에서 끊겨 손님이 못 읽습니다

    SVG 는 글자를 **줄바꿈하지 않습니다.** viewBox 를 넘으면
    그대로 잘립니다. 그런데 화면을 찍어 봐도 잘린 자리가
    자연스러워 보여 놓치기 쉽습니다. 그래서 셈으로 잡습니다.

    한글은 글자 크기와 폭이 거의 같습니다(1.0).
    숫자·영문은 0.55 쯤으로 봅니다.
    textLength 를 준 것은 그 폭에 맞춰 그려지므로 셈에서 뺍니다.
"""
import math
import re

한글폭 = 1.0
영문폭 = 0.55


def 글자폭(글, 크기):
    return sum(크기 * (한글폭 if ord(c) > 0x2000 else 영문폭) for c in 글)


def 밖으로나간글자(svg, 너비=320):
    """[(글, 오른쪽끝, 너비), ...] 를 냅니다. 없으면 빈 목록."""
    난것 = []
    for m in re.finditer(r'<text([^>]*)>([^<]*)</text>', svg or ''):
        속 = m.group(1)
        글 = m.group(2).strip()
        if not 글 or 'textLength' in 속:
            continue
        자리 = re.search(r'x=[\'"]([-0-9.]+)', 속)
        if not 자리:
            continue
        x = float(자리.group(1))
        크기 = re.search(r'font-size=[\'"]([0-9.]+)', 속)
        크기 = float(크기.group(1)) if 크기 else 12.0
        닻 = re.search(r'text-anchor=[\'"]([a-z]+)', 속)
        닻 = 닻.group(1) if 닻 else 'start'
        폭 = 글자폭(글, 크기)
        if 닻 == 'start':
            오른쪽 = x + 폭
        elif 닻 == 'middle':
            오른쪽 = x + 폭 / 2
        else:
            오른쪽 = x
        if 오른쪽 > 너비 + 1:
            난것.append((글, int(round(오른쪽)), 너비))
    return 난것

# ── 도형도 봅니다 ────────────────────────────────────────
#
# ★ 2026-09-30 — **글자만 보아서는 모자랐습니다**
#
#   막대찌(200mm)가 채비도 **왼쪽 밖으로 86px 잘려** 주황 톱이
#   사라지고 회색 토막만 남았습니다. 부품 쪽 카드도 같았습니다.
#   「가늘고 긴 찌입니다」라 적어 놓고 그림은 짧은 막대였습니다.
#   그런데 위의 글자 검사는 통과했습니다 —
#   **글자는 안 났으니까요. 난 것은 도형이었습니다.**
#
# ★ 처음 지은 것은 **헛것을 보았습니다** (같은 날 곧바로 잡음)
#   `rotate()` 만 보고 `translate()` 를 안 봤습니다. 어종 그림의
#   물고기는 `<g transform="translate(…)">` 안에 상대 좌표(-32 …)로
#   있어, **옮기기 전 자리**로 재는 바람에 215갈래가 「나갔다」고
#   나왔습니다. 눈으로 보니 멀쩡했습니다.
#   그래서 이제 **변환을 쌓아 가며** 봅니다.
#
#   못 알아보는 변환이 있으면 그 그룹은 **건너뜁니다.**
#   헛경보로 멀쩡한 그림을 막는 것이 못 잡는 것보다 나쁩니다.
#
#   곡선은 **끝점만** 셉니다. 제어점은 곡선 바깥에 있어
#   함께 세면 실제보다 크게 잡혀 또 헛경보가 납니다.

_수 = r'(-?[0-9.]+(?:e-?[0-9]+)?)'
_그냥 = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)      # 아무것도 안 하는 변환


def _곱(m, n):
    """변환 둘을 잇습니다 (SVG 의 matrix(a b c d e f) 차례)."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2,      b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2,      b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _먹이기(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def _변환읽기(글):
    """transform="…" 을 변환 하나로 바꿉니다. 모르는 것이 있으면 None."""
    난 = _그냥
    본데까지 = 0
    글 = 글 or ''
    for m in re.finditer(r'([a-zA-Z]+)\s*\(([^)]*)\)', 글):
        if 글[본데까지:m.start()].strip(' ,'):
            return None                      # 못 읽은 글자가 끼어 있습니다
        본데까지 = m.end()
        낱 = m.group(1)
        값 = [float(v) for v in re.findall(_수, m.group(2))]
        if 낱 == 'translate' and 값:
            하나 = (1, 0, 0, 1, 값[0], 값[1] if len(값) > 1 else 0)
        elif 낱 == 'scale' and 값:
            하나 = (값[0], 0, 0, 값[1] if len(값) > 1 else 값[0], 0, 0)
        elif 낱 == 'rotate' and 값:
            r = math.radians(값[0])
            c, s = math.cos(r), math.sin(r)
            하나 = (c, s, -s, c, 0, 0)
            if len(값) >= 3:                 # 가운데를 정한 회전
                cx, cy = 값[1], 값[2]
                하나 = _곱(_곱((1, 0, 0, 1, cx, cy), 하나),
                           (1, 0, 0, 1, -cx, -cy))
        elif 낱 == 'matrix' and len(값) >= 6:
            하나 = tuple(값[:6])
        else:
            return None                      # skewX·skewY 등은 모릅니다
        난 = _곱(난, 하나)
    if 글[본데까지:].strip(' ,'):
        return None
    return 난


def _잰값(조각, 이름):
    m = re.search(r'\b%s=[\'"]%s' % (이름, _수), 조각)
    return float(m.group(1)) if m else None


def _여유주기(점, 여유):
    if not 여유:
        return 점
    난 = []
    for x, y in 점:
        난 += [(x - 여유, y - 여유), (x + 여유, y + 여유)]
    return 난


def _도형점들(조각):
    """도형 하나가 지나는 점들을 냅니다. 모르는 것은 빈 목록."""
    굵기 = _잰값(조각, 'stroke-width')
    여유 = (굵기 or 0.0) / 2
    낱 = re.match(r'<([a-z]+)', 조각).group(1)

    if 낱 == 'rect':
        x = _잰값(조각, 'x') or 0.0
        y = _잰값(조각, 'y') or 0.0
        w = _잰값(조각, 'width')
        h = _잰값(조각, 'height')
        if w is None or h is None:
            return []
        return [(x - 여유, y - 여유), (x + w + 여유, y + h + 여유)]

    if 낱 == 'ellipse':
        cx = _잰값(조각, 'cx') or 0.0
        cy = _잰값(조각, 'cy') or 0.0
        rx = _잰값(조각, 'rx')
        ry = _잰값(조각, 'ry')
        if rx is None or ry is None:
            return []
        return [(cx - rx - 여유, cy - ry - 여유),
                (cx + rx + 여유, cy + ry + 여유)]

    if 낱 == 'circle':
        cx = _잰값(조각, 'cx') or 0.0
        cy = _잰값(조각, 'cy') or 0.0
        r = _잰값(조각, 'r')
        if r is None:
            return []
        return [(cx - r - 여유, cy - r - 여유), (cx + r + 여유, cy + r + 여유)]

    if 낱 == 'line':
        점 = [(_잰값(조각, 'x1') or 0.0, _잰값(조각, 'y1') or 0.0),
              (_잰값(조각, 'x2') or 0.0, _잰값(조각, 'y2') or 0.0)]
        return _여유주기(점, 여유)

    if 낱 in ('path', 'polygon', 'polyline'):
        if 낱 == 'path':
            d = re.search(r"\bd=['\"]([^'\"]+)", 조각)
            점 = _길점들(d.group(1)) if d else []
        else:
            값 = re.search(r"points=['\"]([^'\"]+)", 조각)
            수들 = [float(v) for v in re.findall(_수, 값.group(1))] if 값 else []
            점 = list(zip(수들[0::2], 수들[1::2]))
        return _여유주기(점, 여유)
    return []


def _길점들(d):
    """path 의 d 를 훑어 **지나는 끝점**을 모읍니다.

    곡선의 제어점은 빼고 끝점만 셉니다 — 제어점은 곡선 밖에 있어
    함께 세면 실제보다 크게 잡혀 멀쩡한 그림을 막습니다.
    """
    점 = []
    x = y = 0.0
    시작 = (0.0, 0.0)
    끝점몇째 = {'M': (0, 1), 'L': (0, 1), 'T': (0, 1),
                'C': (4, 5), 'S': (2, 3), 'Q': (2, 3), 'A': (5, 6)}
    묶음 = {'M': 2, 'L': 2, 'T': 2, 'C': 6, 'S': 4, 'Q': 4, 'A': 7}
    for m in re.finditer(r'([MmLlCcSsQqTtAaVvHhZz])([^MmLlCcSsQqTtAaVvHhZz]*)',
                         d or ''):
        낱 = m.group(1)
        큰 = 낱.upper()
        값 = [float(v) for v in re.findall(_수, m.group(2))]
        상대 = 낱.islower()
        if 큰 == 'Z':
            x, y = 시작
            점.append((x, y))
            continue
        if 큰 in ('V', 'H'):
            for v in 값:
                if 큰 == 'V':
                    y = y + v if 상대 else v
                else:
                    x = x + v if 상대 else v
                점.append((x, y))
            continue
        n = 묶음.get(큰)
        if not n:
            continue
        i, j = 끝점몇째[큰]
        for k in range(0, len(값) - n + 1, n):
            토막 = 값[k:k + n]
            x = x + 토막[i] if 상대 else 토막[i]
            y = y + 토막[j] if 상대 else 토막[j]
            점.append((x, y))
            if 큰 == 'M' and k == 0:
                시작 = (x, y)
    return 점


_낱들 = (r'<g\b[^>]*>|</g>'
         r'|<(?:rect|ellipse|circle|line|path|polygon|polyline)\b[^>]*>')


def 밖으로나간도형(svg, 너비=None, 높이=None, 여유=1.0):
    """[(도형, 어느쪽, 얼마나px), ...] 를 냅니다. 없으면 빈 목록.

    너비·높이를 안 주면 viewBox 에서 읽습니다.
    """
    svg = svg or ''
    if 너비 is None or 높이 is None:
        박스 = re.search(r'viewBox=[\'"]\s*%s[\s,]+%s[\s,]+%s[\s,]+%s'
                         % ((_수,) * 4), svg)
        if not 박스:
            return []
        너비 = float(박스.group(3))
        높이 = float(박스.group(4))

    난것 = []
    쌓임 = [_그냥]
    모름 = 0              # 못 읽은 변환 안에 있으면 건너뜁니다
    for m in re.finditer(_낱들, svg):
        조각 = m.group(0)
        if 조각.startswith('<g'):
            글 = re.search(r"transform=['\"]([^'\"]*)", 조각)
            바뀜 = _변환읽기(글.group(1)) if 글 else _그냥
            if 바뀜 is None:
                모름 += 1
                쌓임.append(쌓임[-1])
            else:
                쌓임.append(_곱(쌓임[-1], 바뀜))
            continue
        if 조각 == '</g>':
            if len(쌓임) > 1:
                쌓임.pop()
                if 모름:
                    모름 -= 1
            continue
        if 모름:
            continue
        점 = _도형점들(조각)
        if not 점:
            continue
        여기 = 쌓임[-1]
        글 = re.search(r"transform=['\"]([^'\"]*)", 조각)
        if 글:
            바뀜 = _변환읽기(글.group(1))
            if 바뀜 is None:
                continue
            여기 = _곱(여기, 바뀜)
        점 = [_먹이기(여기, px, py) for px, py in 점]
        좌 = min(p[0] for p in 점)
        우 = max(p[0] for p in 점)
        위 = min(p[1] for p in 점)
        아래 = max(p[1] for p in 점)
        낱 = re.match(r'<([a-z]+)', 조각).group(1)
        if 좌 < -여유:
            난것.append((낱, '왼쪽', round(-좌, 1)))
        if 우 > 너비 + 여유:
            난것.append((낱, '오른쪽', round(우 - 너비, 1)))
        if 위 < -여유:
            난것.append((낱, '위', round(-위, 1)))
        if 아래 > 높이 + 여유:
            난것.append((낱, '아래', round(아래 - 높이, 1)))
    return 난것
