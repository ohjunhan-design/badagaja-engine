# -*- coding: utf-8 -*-
"""받은 **낚시부품 그림**이 어느 부품·채비 쪽 자리에 맞는가 (2026-10-15).

★ 왜 만드나 (총감독 지시 P1③)
  기획팀이 「낚시부품 26종」 그림을 보내 주셨습니다. 자료에도
  부품이 **마침 26가지** 있습니다. 숫자가 같으니 하나씩 짝이
  맞으리라 여기기 쉽습니다. **그렇지 않습니다.**

  ★ 이름을 보고 짐작하면 틀립니다 — [[rig-check-real-products]]
    「O형」은 고리가 아니라 검은 알갱이였습니다. 「전유동찌」는
    찌 종류가 아니라 **채비 방식** 이름입니다.

  그래서 **맞는 것만 맞다 하고, 못 가리는 것은 못 가린다 합니다.**
  [[show-dont-judge]] — 기계가 좁히고 사람이 확인합니다.

★ 무엇을 근거로 재나
  ① `data/raw/rigs.json` 의 `부품` 26가지 — 쪽의 `pt-○○` 자리
  ② 같은 자료의 `채비` 16가지 — `site/rig/*.html` 쪽
  ③ 받은 그림의 파일 이름

★ 네 갈래로 가릅니다
  · 확실 — 이름이 그대로 맞습니다. 바로 쓸 수 있습니다
  · 채비 — 부품이 아니라 **채비 쪽** 그림입니다 (이미 그림이 있어 겹칩니다)
  · 못가림 — 자료에 그 이름이 없습니다. **기획팀에 물어야 합니다**
  · 빈자리 — 자료에 있는데 그림이 안 온 부품

★ **읽기만 합니다.** 그림도 자료도 쪽도 고치지 않습니다.
  총감독 지시 — 「제작은 기획팀 소관. 실행팀은 이름→쪽 매핑과
  적용 경로만. 감사 합격 전 반영 금지, 이미지 재제작 금지.」

쓰는 법
    python -m engine.map_rig_parts --받은곳 "G:/…/규칙이름_26종"
    python -m engine.map_rig_parts --받은곳 … --표
"""
import argparse
import collections
import hashlib
import io
import json
import os
import re
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def 씻기(t):
    """괄호·가운뎃점·사이띄기를 걷어 맞대기 쉽게."""
    t = re.sub(r'\(.*?\)', '', t or '')
    return re.sub(r'[·\s_]', '', t)


def 번호떼기(이름):
    """`04_편대.png` → `편대`"""
    기 = os.path.splitext(이름)[0]
    return re.sub(r'^\d+[_\-]?', '', 기)


def 쪽자리(부품이름):
    """쪽이 쓰는 자리 이름. 생성기와 같은 규칙입니다 (build.py 7557)."""
    return 'pt-' + re.sub(r'\s+', '-', 부품이름)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--받은곳', required=True)
    p.add_argument('--표', action='store_true', help='마크다운 표로')
    a = p.parse_args()

    자료 = json.load(io.open(os.path.join(뿌리, 'data/raw/rigs.json'),
                             encoding='utf-8'))
    부품 = list(자료['부품'].keys())
    채비 = {k: v.get('이름') or k for k, v in 자료['채비'].items()}

    if not os.path.isdir(a.받은곳):
        print('★ 받은 곳이 없습니다: %s' % a.받은곳)
        return 1
    그림들 = sorted(x for x in os.listdir(a.받은곳)
                    if x.lower().endswith(('.png', '.webp', '.jpg')))
    if not 그림들:
        print('★ 그림이 없습니다 — 0장을 재면 당연히 0입니다')
        return 1                      # [[count-before-you-claim-zero]]

    # ── 같은 파일이 둘 이상인가 (지문으로) ─────────────────
    지문 = collections.defaultdict(list)
    for n in 그림들:
        with io.open(os.path.join(a.받은곳, n), 'rb') as f:
            지문[hashlib.sha256(f.read()).hexdigest()].append(n)
    쌍둥이 = [v for v in 지문.values() if len(v) > 1]

    확실, 채비것, 못가림 = [], [], []
    쓴부품 = set()
    for n in 그림들:
        이 = 번호떼기(n)
        키 = 씻기(이)

        # ① 부품 이름과 **그대로** 맞는가
        맞 = None
        for b in 부품:
            if 씻기(b) == 키:
                맞 = b
                break

        # ② 채비 쪽 이름과 맞는가 — **부품 포함 검사보다 먼저**입니다
        #    ★ 안 그러면 「문어에기」가 부품 「에기」로 잡힙니다.
        #      문어 에기는 `octopus` 채비 것이지 에기가 아닙니다.
        #      [[check-false-positive-first]] — 손으로 보고 잡았습니다.
        if 맞 is None:
            채 = None
            for cid, cn in 채비.items():
                if 씻기(cn) and (씻기(cn) in 키 or 키 in 씻기(cn)):
                    채 = (cid, cn)
                    break
            if 채:
                있 = os.path.isfile(os.path.join(
                    뿌리, 'site/img/rig/%s.webp' % 채[0]))
                채비것.append((n, 채[0], 채[1], 있))
                continue

        # ③ 한쪽이 다른 쪽을 품는가 — 품은 것이 **하나일 때만**
        #    (「일반봉돌」은 「봉돌」만 품습니다. 「고리봉돌」은 아닙니다)
        if 맞 is None:
            품은것 = [b for b in 부품
                      if 씻기(b) and (씻기(b) in 키 or 키 in 씻기(b))]
            if len(품은것) == 1:
                맞 = 품은것[0]

        if 맞:
            확실.append((n, 맞, 쪽자리(맞)))
            쓴부품.add(맞)
            continue

        못가림.append((n, 이))

    # ★ 한 부품에 두 장 이상이 맞았으면 **가린 것이 아닙니다**
    #   둘 다 못가림으로 돌립니다. 짐작으로 하나를 고르지 않습니다.
    셈 = collections.Counter(b for _, b, _ in 확실)
    다툼 = {b for b, c in 셈.items() if c > 1}
    if 다툼:
        남 = []
        for n, b, 자 in 확실:
            if b in 다툼:
                못가림.append((n, '%s — 부품 「%s」 자리를 여럿이 다툽니다'
                               % (번호떼기(n), b)))
            else:
                남.append((n, b, 자))
        확실 = 남
        쓴부품 = {b for _, b, _ in 확실}

    빈자리 = [b for b in 부품 if b not in 쓴부품]

    # ── 냅니다 ──────────────────────────────────────────
    if a.표:
        낼것 = 표로내기(확실, 채비것, 못가림, 빈자리, 쌍둥이, len(그림들))
        print(낼것)
    else:
        print('받은 부품 그림이 어느 자리에 맞는가')
        print('=' * 72)
        print('  받은 그림 %d장 · 자료의 부품 %d가지 · 채비 %d가지'
              % (len(그림들), len(부품), len(채비)))
        print()
        print('  ✓ **이름이** 맞는 것   %2d장  ← 그림 안은 사람이 봐야 합니다' % len(확실))
        for n, b, 자 in 확실:
            print('      %-28s → 부품 「%s」  (%s)' % (n, b, 자))
        print()
        print('  ~ 부품이 아니라 채비 쪽 그림  %2d장' % len(채비것))
        for n, cid, cn, 있 in 채비것:
            print('      %-28s → rig/%s.html 「%s」%s'
                  % (n, cid, cn, '  ★ 이미 그림이 있습니다' if 있 else ''))
        print()
        print('  ✗ 자료에 그 이름이 없습니다  %2d장  ← 기획팀에 물어야' % len(못가림))
        for n, 이 in 못가림:
            print('      %-28s 「%s」' % (n, 이))
        print()
        print('  ~ 자료에 있는데 그림이 안 온 부품  %2d가지' % len(빈자리))
        for b in 빈자리:
            print('      %-14s (%s)' % (b, 쪽자리(b)))
        if 쌍둥이:
            print()
            print('  ✗ 내용이 **똑같은** 그림 %d쌍' % len(쌍둥이))
            for v in 쌍둥이:
                print('      %s' % ' = '.join(v))
        print('-' * 72)
        print('[한 줄 요약] 이름이 맞는 것 %d장 · 채비 쪽 %d장 · '
              '물어야 할 것 %d장 · 빈 자리 %d가지 · 같은 그림 %d쌍'
              % (len(확실), len(채비것), len(못가림), len(빈자리),
                 len(쌍둥이)))
    return 0


def 표로내기(확실, 채비것, 못가림, 빈자리, 쌍둥이, 몇장):
    o = []
    o.append('## 받은 그림 %d장 — 자리 대조' % 몇장)
    o.append('')
    o.append('### ✓ **이름이** 맞는 것 %d장' % len(확실))
    o.append('')
    o.append('★ **이름만 맞댔습니다.** 그림 안에 무엇이 그려졌는지는'
             ' 이 도구가 못 읽습니다 — 사람이 봐야 합니다.')
    o.append('')
    o.append('| 받은 그림 | 자료의 부품 | 쪽의 자리 |')
    o.append('|---|---|---|')
    for n, b, 자 in 확실:
        o.append('| `%s` | %s | `#%s` |' % (n, b, 자))
    o.append('')
    o.append('### ~ 부품이 아니라 **채비 쪽** 그림 %d장' % len(채비것))
    o.append('')
    o.append('| 받은 그림 | 채비 쪽 | 이름 | 이미 그림이 |')
    o.append('|---|---|---|---|')
    for n, cid, cn, 있 in 채비것:
        o.append('| `%s` | `rig/%s.html` | %s | %s |'
                 % (n, cid, cn, '**있습니다**' if 있 else '없습니다'))
    o.append('')
    o.append('### ✗ 자료에 그 이름이 없습니다 %d장' % len(못가림))
    o.append('')
    for n, 이 in 못가림:
        o.append('- `%s` — 「%s」' % (n, 이))
    o.append('')
    o.append('### ~ 자료에 있는데 그림이 안 온 부품 %d가지' % len(빈자리))
    o.append('')
    o.append('%s' % ' · '.join(빈자리))
    if 쌍둥이:
        o.append('')
        o.append('### ✗ 내용이 똑같은 그림 %d쌍' % len(쌍둥이))
        for v in 쌍둥이:
            o.append('- %s' % ' = '.join('`%s`' % x for x in v))
    return '\n'.join(o)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
