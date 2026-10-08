# -*- coding: utf-8 -*-
"""좌표를 다시 봐야 하는 곳을 **차례대로** 뽑습니다 (2026-10-08).

★ `engine/check_coast.py` 는 「무엇이 의심스러운가」를 가립니다.
  이 도구는 그 결과를 **사람이 하나씩 고칠 수 있는 차례**로 냅니다.

★ 바깥 검수 —
  「3,514곳을 다시 찍지 마세요. 후보만 재검증해야 합니다 …
    지금 필요한 것은 자동수정이 아니라
    **자동 선별 → 재지오코딩 → 검증 → 사람 확인**입니다.
    각 후보에 기존 이름·권역·지형·현재좌표·해안거리·동일지명
    기준점들을 붙이세요」

★ **고치지 않습니다.** 짐작해 좌표를 당기면 틀린 좌표를 그럴듯한
  다른 틀린 좌표로 바꿉니다. 이 도구는 **볼 것을 줄여 줄 뿐**입니다.

★ 먼저 볼 차례
    ① 같은 이름 무리에서 혼자 떨어진 것 — 무리가 클수록 확실합니다
       (주인이 잡으신 「개도 모전리」가 바로 이것입니다)
    ② 해안형 지형(방파제·선착장·갯바위)인데 바다에서 먼 것
    ③ 나머지 먼 것
"""
import io as _io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import check_coast as C   # noqa: E402

낼곳 = os.path.join(여기, 'data-private', '좌표-다시볼곳.md')


def main():
    격자, 눈금 = C.해안읽기()
    if 격자 is None:
        print('□ 해안선 자료가 없습니다 — tools/make_coastline.py 로 만드세요')
        return 1
    것들 = C.포인트들()
    표 = dict((x.get('id'), x) for x in 것들)

    # 바다까지
    잰것 = {}
    for x in 것들:
        좌 = x.get('좌표') or {}
        la, lo = 좌.get('위도'), 좌.get('경도')
        if la is None:
            continue
        km = C.바다까지(격자, 눈금, la, lo)
        if km is not None:
            잰것[x['id']] = km

    # 같은 지명 무리
    # ★ 검사기와 **같은 함수**를 씁니다 — 두 곳에서 따로 셈하면
    #   반드시 어긋납니다 (기억 「숫자는 한 곳에서만」)
    묶음 = C.지명묶기(것들)
    지명이상 = C.외톨이찾기(묶음)
    무리좌표 = {}
    for (권역, 앞), 들 in 묶음.items():
        for y in 들:
            if y.get('id') in 지명이상:
                무리좌표[y['id']] = [
                    ((z.get('이름') or {}).get('ko'),
                     (z.get('좌표') or {}).get('위도'),
                     (z.get('좌표') or {}).get('경도'))
                    for z in 들 if z.get('id') != y.get('id')][:4]

    후보 = set(지명이상) | set(k for k, v in 잰것.items() if v > C.검토선)

    def 차례(아이디):
        x = 표.get(아이디) or {}
        해안, 예외 = C.지형갈래(x.get('지형'))
        km = 잰것.get(아이디)
        if 아이디 in 지명이상:
            d, 앞, n = 지명이상[아이디]
            return (0, -(n * 100 + d))      # 무리가 크고 멀수록 먼저
        if 해안 and not 예외 and km and km > C.경고선:
            return (1, -km)
        return (2, -(km or 0))

    줄 = ['# 좌표를 다시 봐야 하는 곳', '',
          '`engine/check_coast.py` 가 가려 낸 것을 **먼저 볼 차례**로',
          '늘어놓은 것입니다. **고치지 않았습니다** — 짐작해 당기면',
          '틀린 좌표를 그럴듯한 다른 틀린 좌표로 바꿉니다.', '',
          '고친 뒤에는 `tests/golden/좌표.json` 에서 그 id 를 지우세요.',
          '그러면 다음에 같은 일이 생길 때 배포가 막힙니다.', '',
          '모두 **%d곳**입니다.' % len(후보), '',
          '## ① 같은 이름 무리에서 혼자 떨어진 것', '',
          '무리가 클수록 「혼자 틀린 것」일 가능성이 높습니다.', '']

    앞선것 = sorted(후보, key=차례)
    낸것 = 0
    머리낸것 = {0: True, 1: False, 2: False}
    for 아이디 in 앞선것:
        갈, _ = 차례(아이디)
        if 갈 == 1 and not 머리낸것[1]:
            머리낸것[1] = True
            줄 += ['', '## ② 해안형 자리인데 바다에서 먼 것', '',
                   '방파제·선착장·갯바위가 바다에서 %gkm 넘게 떨어져'
                   ' 있습니다.' % C.경고선, '']
        if 갈 == 2 and not 머리낸것[2]:
            머리낸것[2] = True
            줄 += ['', '## ③ 그 밖에 바다에서 %gkm 넘는 것' % C.검토선,
                   '', '갯벌·조간대처럼 **실제로 멀 수 있는** 자리도'
                   ' 섞여 있습니다.', '']
        x = 표.get(아이디) or {}
        좌 = x.get('좌표') or {}
        이름 = (x.get('이름') or {}).get('ko') or ''
        줄.append('- **%s** · %s · `%s`'
                  % (이름, x.get('지형') or '', 아이디))
        줄.append('  - 지금 좌표 `%s, %s` · 권역 `%s`'
                  % (좌.get('위도'), 좌.get('경도'), x.get('권역')))
        if 아이디 in 잰것:
            줄.append('  - 바다까지 **%.2fkm**' % 잰것[아이디])
        if 아이디 in 지명이상:
            d, 앞, n = 지명이상[아이디]
            줄.append('  - 「%s」 무리 %d곳에서 **혼자 %.1fkm 떨어져'
                      ' 있습니다** (가장 가까운 동료까지)' % (앞, n, d))
            for 이, a, b in 무리좌표.get(아이디, []):
                줄.append('    - 같은 무리: %s `%s, %s`' % (이, a, b))
        낸것 += 1

    줄 += ['', '---', '',
           '※ 이 파일은 `data-private/` 에 있습니다 — 웹에 안 냅니다'
           ' (주인 규칙 11).']

    os.makedirs(os.path.dirname(낼곳), exist_ok=True)
    _io.open(낼곳, 'w', encoding='utf-8').write('\n'.join(줄))
    print('  · 다시 볼 곳 %d곳을 적었습니다' % 낸것)
    print('  · %s' % os.path.relpath(낼곳, 여기))
    return 0


if __name__ == '__main__':
    sys.exit(main())
