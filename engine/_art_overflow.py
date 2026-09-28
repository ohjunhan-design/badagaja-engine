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
