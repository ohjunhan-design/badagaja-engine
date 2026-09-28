# -*- coding: utf-8 -*-
"""판정표를 **깃허브 요약 쪽**에 씁니다.

★ 왜 생겼나 (2026-09-29 — 결과를 보는 데 고생을 했습니다)

    판정이 어김으로 끝났는데, **무엇이 어겼는지 보려고
    로그를 한참 뒤져야 했습니다.**

      · 로그는 접혀 있어 단계를 눌러야 펼쳐집니다
      · 펼쳐도 가상 스크롤이라 가운데가 잘립니다
      · 결국 「TRUNCATED」만 보고 끝난 적이 여러 번입니다

    판정 결과는 이미 `tests/out/gate.json` 에 온전히 있습니다.
    그것을 깃허브가 주는 **요약 칸**에 표로 옮겨 놓으면,
    판정 쪽을 열자마자 무엇이 어겼는지 바로 보입니다.

    로그를 뒤지는 일은 사람 손이 하는 일이라, 바빠지면
    건너뛰게 됩니다. **건너뛰면 어긴 것을 못 봅니다.**

무엇을 하나
    · 상태별 숫자 한 줄
    · 어긴 것 · 못 잰 것을 위로 올린 표
    · 어긴 것은 까닭 몇 줄까지 함께

쓰는 법
    python engine/summary.py                요약 칸에 씁니다
    python engine/summary.py --화면          화면에도 찍습니다
"""
import io
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 보기 나쁜 것부터 위로 올립니다 — 눈에 먼저 들어오게
차례 = ('FAIL', 'ERROR', 'INFRA_FAIL', 'NOT_TESTED', 'N.A.', 'PASS')

표시 = {
    'PASS': '✅ 통과',
    'FAIL': '❌ 어김',
    'ERROR': '💥 죽음',
    'INFRA_FAIL': '🔧 잴 형편 안 됨',
    'NOT_TESTED': '⬜ 못 쟀음',
    'N.A.': '➖ 잴 것 없음',
}


def 까닭들(항목, 최대=12):
    """검사기가 뱉은 말에서 어긴 줄만 골라 옵니다.

    ★ **검사기 이름으로 찾습니다** (2026-09-29)

      기록은 tests/out/log/ 에 **검사기 파일 이름**으로 쌓입니다
      (check_ads_strict.txt 처럼 인자가 꼬리로 붙습니다).
      판정표의 「롤백」 같은 사람 이름으로는 못 찾습니다.
      그래서 gate 가 항목에 남긴 '검사기' 를 씁니다.
    """
    도구 = os.path.basename((항목.get('검사기') or '').replace('/', os.sep))
    도구 = 도구[:-3] if 도구.endswith('.py') else 도구
    칸 = os.path.join(ROOT, 'tests', 'out', 'log')
    길 = None
    if 도구 and os.path.isdir(칸):
        # 꼬리(_strict 따위)가 붙으므로 앞이 같은 것을 고릅니다
        맞는것 = sorted(f for f in os.listdir(칸)
                        if f.startswith(도구) and f.endswith('.txt'))
        if 맞는것:
            길 = os.path.join(칸, 맞는것[0])
    if 길 is None:
        return []
    try:
        줄들 = io.open(길, encoding='utf-8',
                       errors='replace').read().splitlines()
    except OSError:
        return []
    # ★ **어긴 줄만으로는 모자랍니다** (2026-09-29)
    #
    #   19번 롤백이 「✗ 되돌린 쪽이 첫 판과 바이트까지 같다」라고만
    #   해서, **무엇이 어떻게 달랐는지** 알 수가 없었습니다.
    #   검사기는 그 바로 뒤에 까닭을 적습니다. 그 줄도 담습니다.
    고른것 = []
    for i, 줄 in enumerate(줄들):
        if 줄.lstrip().startswith(('✗', 'Traceback', '  File ')):
            고른것.append(줄.rstrip())
            # 바로 뒤에 들여쓴 설명이 있으면 함께 담습니다
            for 뒤 in 줄들[i + 1:i + 4]:
                if 뒤.strip() and 뒤.startswith(('      ', '	')):
                    고른것.append(뒤.rstrip())
                else:
                    break
    if 고른것:
        return 고른것[:최대]

    # ★ **기록은 있는데 ✗ 표가 없는 경우** (2026-09-29)
    #
    #   검사기가 「손볼 곳 3건」처럼 끝에서만 말하는 일이 있습니다.
    #   그때 빈손으로 돌아가면 「못 찾았습니다」로 보여, 기록이
    #   아예 없는 것과 구별이 안 됩니다. **다른 상황입니다.**
    #   끝부분을 보여 주는 편이 아무것도 없는 것보다 낫습니다.
    끝줄들 = [x.rstrip() for x in 줄들 if x.strip()]
    return (['(✗ 표가 없어 기록 끝부분을 옮깁니다 — %s)'
             % os.path.basename(길)] + 끝줄들[-최대:]) if 끝줄들 else []


def 만들기(d):
    글 = []
    끝 = d.get('FINAL') or '(모름)'
    글.append('## 판정 — %s' % 끝)
    글.append('')
    셈 = ['%s %d' % (표시.get(k, k), d.get(k, 0))
          for k in 차례 if d.get(k)]
    글.append(' · '.join(셈) or '(센 것이 없습니다)')
    글.append('')
    글.append('잰 때 %s · 커밋 %s · 검산 %s'
              % (d.get('잰때', '?'), d.get('커밋', '?'),
                 '맞음' if d.get('검산맞음') else '**어긋남**'))
    글.append('')

    항목 = list(d.get('항목') or []) + list(d.get('덧검사') or [])
    순서 = {s: i for i, s in enumerate(차례)}
    항목.sort(key=lambda x: (순서.get(x.get('상태'), 99),
                            str(x.get('번호', ''))))

    글.append('| 번호 | 무엇을 재나 | 판정 | 증거 |')
    글.append('|---|---|---|---|')
    for x in 항목:
        글.append('| %s | %s | %s | %s |'
                  % (x.get('번호') or '덧', x.get('이름', ''),
                     표시.get(x.get('상태'), x.get('상태', '')),
                     str(x.get('증거', '')).replace('|', '\\|')[:160]))
    글.append('')

    나쁜것 = [x for x in 항목
              if x.get('상태') in ('FAIL', 'ERROR', 'INFRA_FAIL')]
    if 나쁜것:
        글.append('### 어긴 것의 까닭')
        글.append('')
        for x in 나쁜것:
            줄들 = 까닭들(x)
            글.append('<details><summary>%s %s — %s</summary>'
                      % (x.get('번호') or '덧', x.get('이름', ''),
                         표시.get(x.get('상태'), '')))
            글.append('')
            글.append('```')
            글.extend(줄들 or [
                '(이 검사기의 기록을 못 찾았습니다 — 검사기 %s)'
                % (x.get('검사기') or '(어느 검사기인지 안 적혀 있습니다)'),
                '판정결과 꾸러미의 tests/out/log/ 를 내려받아 보세요.'])
            글.append('```')
            글.append('')
            글.append('</details>')
            글.append('')
    else:
        글.append('어긴 것이 없습니다.')
        글.append('')
    return '\n'.join(글)


def main():
    길 = os.path.join(ROOT, 'tests', 'out', 'gate.json')
    if not os.path.isfile(길):
        print('판정 결과가 없습니다: %s' % 길)
        return 0          # 요약을 못 써도 판정을 뒤엎지 않습니다
    try:
        d = json.load(io.open(길, encoding='utf-8'))
    except ValueError as e:
        print('판정 결과를 못 읽었습니다: %s' % e)
        return 0
    글 = 만들기(d)
    칸 = os.environ.get('GITHUB_STEP_SUMMARY')
    if 칸:
        with io.open(칸, 'a', encoding='utf-8') as f:
            f.write(글 + '\n')
        print('요약 칸에 판정표를 썼습니다 (%d줄)' % 글.count('\n'))
    else:
        print('요약 칸이 없습니다 — 화면에만 찍습니다')
    if 칸 is None or '--화면' in sys.argv:
        print('')
        print(글)
    return 0


if __name__ == '__main__':
    sys.exit(main())
