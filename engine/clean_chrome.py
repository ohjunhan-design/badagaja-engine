# -*- coding: utf-8 -*-
"""검사가 남긴 크롬 찌꺼기를 치웁니다.

★ 왜 생겼나 (2026-09-27 주인 물음 「내가 켜놓은 크롬 11개는 뭐야?」)

    검사기가 크롬을 수십 번 띄웁니다. 대개는 스스로 닫지만,
    시간이 넘거나 판정이 죽으면 **그대로 남습니다.**

    2026-09-27 에 13개가 남아 있었습니다. 제가 「헤드리스 표시가
    있는 것만 내 것」이라 보고 둘만 닫았습니다. **틀렸습니다.**

        크롬은 본체 하나가 새끼를 여럿 냅니다.
            본체      --headless 가 붙어 있습니다
            새끼      --type=renderer · gpu-process · utility …
                      **--headless 가 안 붙습니다**

    그래서 제가 남긴 것 11개를 주인 것으로 잘못 봤습니다.

★ 어떻게 가려내나 — **창이 있는가**
    주인이 쓰는 크롬은 창이 있습니다. 검사가 띄운 것은 창이 없습니다.
    본체에 창이 없고 그 본체가 headless 면, 그 식구 전부가 우리 것입니다.

★ 그냥은 안 지웁니다 (계약-17)
    --닫기 를 붙여야 닫습니다. 그냥 돌리면 **무엇이 있는지만** 봅니다.

쓰는 법
    python engine/clean_chrome.py           무엇이 남았는지 봅니다
    python engine/clean_chrome.py --닫기    검사가 남긴 것을 닫습니다
"""
import os
import sys
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 검사기가 크롬에 늘 붙이는 표시 — 이것이 있으면 우리가 띄운 것입니다
우리표시 = ('--headless', 'badagaja-render-', 'newmoon-', 'months-',
            'console-', 'ads-check-', 'tide-check-', '두번째도전')


def 물어보기(글):
    try:
        # ★ errors='replace' 가 있어야 합니다 (2026-09-27)
        #   파워셸이 잘못을 알릴 때는 **윈도 한글(cp949)** 로 씁니다.
        #   utf-8 로만 읽으면 거기서 통째로 넘어져,
        #   크롬이 있는데도 「없습니다」가 나옵니다.
        r = subprocess.run(['powershell', '-NoProfile', '-Command', 글],
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=90)
        return r.stdout or ''
    except (OSError, subprocess.SubprocessError):
        return ''


def 크롬들():
    """돌고 있는 크롬을 모두 봅니다. (번호, 부모, 갈래, MB, 명령줄)"""
    글 = 물어보기(
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        "Select-Object ProcessId,ParentProcessId,WorkingSetSize,CommandLine | "
        "ConvertTo-Json -Compress")
    if not 글.strip():
        return []
    try:
        것 = json.loads(글)
    except ValueError:
        return []
    if isinstance(것, dict):
        것 = [것]
    나옴 = []
    for x in 것:
        줄 = x.get('CommandLine') or ''
        갈래 = '본체'
        m = '--type='
        if m in 줄:
            갈래 = 줄.split(m, 1)[1].split()[0].split('"')[0]
        나옴.append({
            '번호': x.get('ProcessId'),
            '부모': x.get('ParentProcessId'),
            '갈래': 갈래,
            'MB': round((x.get('WorkingSetSize') or 0) / 1048576.0),
            '명령줄': 줄,
        })
    return 나옴


def 창있는것():
    """창이 떠 있는 크롬 번호 — **주인이 쓰는 것**입니다."""
    글 = 물어보기(
        "Get-Process -Name chrome -ErrorAction SilentlyContinue | "
        "Where-Object { $_.MainWindowTitle } | "
        "Select-Object -ExpandProperty Id")
    나옴 = set()
    for 줄 in 글.split('\n'):
        줄 = 줄.strip()
        if 줄.isdigit():
            나옴.add(int(줄))
    return 나옴


def 가려내기():
    """(우리것, 주인것) 으로 가릅니다.

    ★ 새끼는 --headless 가 안 붙습니다. **부모를 보고** 따라갑니다.
    """
    것들 = 크롬들()
    창 = 창있는것()
    번호로 = dict((x['번호'], x) for x in 것들)

    우리본체 = set()
    주인본체 = set()
    for x in 것들:
        if x['갈래'] != '본체':
            continue
        if x['번호'] in 창:
            주인본체.add(x['번호'])
        elif any(t in x['명령줄'] for t in 우리표시):
            우리본체.add(x['번호'])

    def 뿌리찾기(번호, 깊이=0):
        """새끼를 거슬러 올라가 본체를 찾습니다."""
        if 깊이 > 8:
            return None
        x = 번호로.get(번호)
        if not x:
            return None
        if x['갈래'] == '본체':
            return 번호
        return 뿌리찾기(x['부모'], 깊이 + 1)

    우리것, 주인것, 모름 = [], [], []
    for x in 것들:
        뿌리 = 뿌리찾기(x['번호'])
        if 뿌리 in 우리본체:
            우리것.append(x)
        elif 뿌리 in 주인본체:
            주인것.append(x)
        elif x['번호'] in 창:
            주인것.append(x)
        else:
            모름.append(x)
    return 우리것, 주인것, 모름


def main():
    닫기 = '--닫기' in sys.argv
    우리것, 주인것, 모름 = 가려내기()

    print('검사가 남긴 크롬이 있는가')
    print('  (2026-09-27 주인 물음 「내가 켜놓은 크롬 11개는 뭐야?」)')
    print('')
    print('  %-16s %4s개 %6sMB' % ('검사가 띄운 것', len(우리것),
                                    sum(x['MB'] for x in 우리것)))
    print('  %-16s %4s개 %6sMB' % ('주인이 쓰는 것', len(주인것),
                                    sum(x['MB'] for x in 주인것)))
    print('  %-16s %4s개 %6sMB' % ('누구 것인지 모름', len(모름),
                                    sum(x['MB'] for x in 모름)))
    print('')

    if 모름:
        print('  ~ 누구 것인지 모르는 것은 **안 닫습니다.**')
        print('    주인이 쓰는 것을 잘못 닫으면 하던 일이 날아갑니다.')
        for x in 모름[:6]:
            print('      %-8s %-16s %4dMB' % (x['번호'], x['갈래'], x['MB']))
        print('')

    if not 우리것:
        print('검사가 남긴 크롬이 없습니다.')
        return 0

    if not 닫기:
        print('  닫으려면 --닫기 를 붙이세요.')
        print('  ★ 그냥은 안 닫습니다 (계약-17).')
        return 0

    # ★ 우리가 띄운 것만 닫습니다 — 창이 있는 것은 손대지 않습니다
    번호들 = ','.join(str(x['번호']) for x in 우리것)
    물어보기('Stop-Process -Id %s -Force -ErrorAction SilentlyContinue'
             % 번호들)   # 계약-17 예외 — 우리가 띄운 것만 닫습니다
    print('  검사가 남긴 크롬 %d개를 닫았습니다 (%dMB)'
          % (len(우리것), sum(x['MB'] for x in 우리것)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
