# -*- coding: utf-8 -*-
"""검사 23 — 규정(금어기·크기제한)과 **어종 아이디 대응**.

★ 왜 따로 두나 (2026-10-01 합의 C-001)
  규정은 **틀리면 사람이 법을 어기는** 유일한 자료입니다.
  다른 검사에 섞어 두면 나중에 등급을 낮추기 쉽습니다.

★ 오늘 찾은 함정 — **아이디가 두 벌입니다**
  어종 자료 한 항목에 아이디가 둘 있습니다.

      id        쪽 파일 이름이 되는 것   site/fish/byeongedom.html
      어종아이디  포인트 자료가 부르는 것   "대상": ["bengedom", ...]

  대개 같지만 **셋이 어긋납니다.**

      byeongedom ↔ bengedom      (벵에돔)
      gapojingeo ↔ gabojingeo    (갑오징어)
      muni       ↔ muniojingeo   (무늬오징어)

  이걸 모르고 `id` 로 맞추면 **포인트 1,169곳이 조용히 빠집니다**
  (벵에돔 564 · 무늬오징어 303 · 갑오징어 302).
  오류도 안 나고 쪽도 만들어집니다. **아무도 모릅니다.**

  제가 실제로 1차 조사에서 그렇게 틀렸습니다. 그 길로 어종 거르개를
  만들었으면 손님이 벵에돔 564곳을 못 찾았을 것입니다.

★ 아직 안 넣은 검사
  · 설명문에 금어기 날짜가 박혔는가 — 지금 36곳 있습니다.
    **고친 뒤에** 넣습니다 (주인 규칙 26 — 새 검사는 잡은 뒤에).
  · 규정 자료(`data/raw/rules/금어기.json`) 검사 — 자료가 아직 없습니다.
    자료 꼴이 굳으면 열 가지를 더합니다 (합의 C 표).

쓰는 법
    python engine/check_rules.py            빠르게 봅니다
    python engine/check_rules.py --strict   판정 (어기면 끝난값 1)
"""
import io
import json
import os
import sys
import glob

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
엄격 = '--strict' in sys.argv
어김 = []


def 말(s=''):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('utf-8', 'replace').decode('ascii', 'replace'))


def 어겼다(무엇, 자세히=''):
    어김.append((무엇, 자세히))
    말('  어김 — %s' % 무엇)
    if 자세히:
        말('         %s' % 자세히)


def 이름만(v):
    if isinstance(v, dict):
        return v.get('ko') or v.get('이름') or ''
    return v or ''


def 자료읽기():
    p = os.path.join(뿌리, 'data', 'raw', 'guide.json')
    if not os.path.isfile(p):
        return None
    return json.load(io.open(p, encoding='utf-8'))


def 포인트읽기():
    것들 = []
    for p in sorted(glob.glob(os.path.join(뿌리, 'data', 'raw',
                                           'points', '*.json'))):
        j = json.load(io.open(p, encoding='utf-8'))
        몸 = j if isinstance(j, list) else (j.get('포인트') or j.get('것들'))
        while isinstance(몸, dict):
            몸 = list(몸.values())[0]
        if isinstance(몸, list):
            것들.extend(몸)
    return 것들


# ── ① 두 벌 아이디가 서로 **유일하게** 맞는가 ────────
def 검사_아이디대응(어종들):
    말('[1] 어종 아이디 두 벌이 서로 유일하게 맞는가')
    아이디 = {}
    포인트쪽 = {}
    for 것 in 어종들:
        i = 것.get('id')
        if not i:
            어겼다('id 가 없는 어종이 있습니다', 이름만(것.get('이름')))
            continue
        if i in 아이디:
            어겼다('id 가 겹칩니다', i)
        아이디[i] = 것
        포 = 것.get('어종아이디') or i
        if 포 in 포인트쪽:
            어겼다('어종아이디가 겹칩니다',
                   '%s — %s 와 %s' % (포, 포인트쪽[포], i))
        포인트쪽[포] = i
    말('  어종 %d가지 · id %d · 어종아이디 %d'
       % (len(어종들), len(아이디), len(포인트쪽)))

    다른것 = [(i, 것.get('어종아이디')) for i, 것 in 아이디.items()
              if 것.get('어종아이디') and 것.get('어종아이디') != i]
    말('  두 벌이 다른 어종 %d가지' % len(다른것))
    for i, 포 in sorted(다른것):
        말('      %-14s ↔ %-14s (%s)'
           % (i, 포, 이름만(아이디[i].get('이름'))))
    return 아이디, 포인트쪽


# ── ② 쪽 파일 이름이 `id` 와 맞는가 ──────────────────
def 검사_쪽이름(아이디):
    말()
    말('[2] 쪽 파일 이름이 id 와 맞는가')
    쪽 = set()
    for 자리 in ('fish', 'catch'):
        밑 = os.path.join(뿌리, 'site', 자리)
        if not os.path.isdir(밑):
            continue
        for f in glob.glob(os.path.join(밑, '*.html')):
            이 = os.path.basename(f)[:-5]
            if 이 != 'index':
                쪽.add(이)
    if not 쪽:
        말('  site/ 가 아직 없습니다 — 건너뜁니다')
        return
    남는쪽 = 쪽 - set(아이디)
    없는쪽 = set(아이디) - 쪽
    말('  쪽 %d · 자료 %d' % (len(쪽), len(아이디)))
    if 남는쪽:
        어겼다('자료에 없는 쪽이 있습니다', ' '.join(sorted(남는쪽)))
    if 없는쪽:
        어겼다('자료에 있는데 쪽이 없습니다', ' '.join(sorted(없는쪽)))


# ── ③ 포인트의 「대상」이 **어종아이디** 쪽을 쓰는가 ──
def 검사_포인트대상(아이디, 포인트쪽):
    말()
    말('[3] 포인트의 대상어종이 어떤 아이디를 쓰는가')
    것들 = 포인트읽기()
    if not 것들:
        말('  포인트 자료가 없습니다 — 건너뜁니다')
        return
    셈 = {}
    for x in 것들:
        for 어 in (x.get('대상') or []):
            셈[어] = 셈.get(어, 0) + 1
    말('  포인트 %d곳 · 대상어종 %d가지 · 태그 %d개'
       % (len(것들), len(셈), sum(셈.values())))

    # 쪽 아이디(id)를 그대로 쓴 것이 있으면 **섞인 것**입니다
    섞임 = [어 for 어 in 셈
            if 어 in 아이디 and (아이디[어].get('어종아이디') or 어) != 어]
    if 섞임:
        어겼다('포인트가 쪽 아이디(id)를 쓴 곳이 있습니다',
               ' '.join('%s(%d곳)' % (x, 셈[x]) for x in sorted(섞임)))
        말('         포인트 자료는 「어종아이디」를 써야 합니다.')
        말('         섞이면 같은 어종이 둘로 세어집니다.')

    맞은것 = [어 for 어 in 셈 if 어 in 포인트쪽]
    덮 = sum(셈[어] for 어 in 맞은것)
    말('  쪽이 있는 어종 %d가지 · 태그의 %.0f%% 를 덮습니다'
       % (len(맞은것), 100.0 * 덮 / max(1, sum(셈.values()))))
    말('  쪽이 없는 어종 %d가지 — **어김이 아닙니다**'
       % (len(셈) - len(맞은것)))
    말('      (합의 P-002 — 쪽이 없어도 정상 아이디입니다)')


# ── ④ 규정 자료가 있으면 봅니다 (아직 없습니다) ──────
def 검사_규정자료():
    말()
    말('[4] 규정 자료')
    p = os.path.join(뿌리, 'data', 'raw', 'rules', '금어기.json')
    if not os.path.isfile(p):
        말('  아직 없습니다 — 자료 꼴을 굳히는 중입니다')
        말('      (합의 R-001 · 초안은 docs/금어기-초안.md)')
        return
    말('  있습니다 — 검사를 더해야 합니다')


def 하기():
    말('=' * 60)
    말('검사 23 — 규정과 어종 아이디 대응')
    말('=' * 60)
    d = 자료읽기()
    if not d:
        말('어종 자료가 없습니다 — 잴 형편이 안 됩니다')
        return 4
    어종들 = d.get('어종') or []
    아이디, 포인트쪽 = 검사_아이디대응(어종들)
    검사_쪽이름(아이디)
    검사_포인트대상(아이디, 포인트쪽)
    검사_규정자료()

    말()
    말('-' * 60)
    if 어김:
        말('어김 %d' % len(어김))
        return 1 if 엄격 else 0
    말('어김 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(하기())
