# -*- coding: utf-8 -*-
"""**서버에 남은 옛 판 잔재를 셉니다** (2026-10-09 감독팀 지시 2)

★ 왜 이 검사가 있나

    배포가 `--delete` 를 **안 씁니다.** 그래서 옛 판이 올려 둔
    쪽이 새 판에 없어도 **서버에 그대로 남습니다.**

    실제로 `/club.html` 이 남아 `badagaja.cloud` 를 가리키고
    있었습니다 — 새 판 450쪽 어디서도 그 쪽으로 가는 길이
    없는데도 주소를 치면 열립니다.

    감독팀 지시 — 「읽기 전용 전수 대조 승인. 서버 목록 확보 →
    새 배포 목록과 대조 → 『잔재 / 보호 대상 / 판단 불가』로
    분류 → **삭제 없이 보고서만.**」

무엇을 하나 — **읽기만 합니다. 아무것도 지우지 않습니다.**

    ① 옛 판 저장소의 쪽 목록을 만듭니다
    ② 새 판이 만드는 쪽 목록을 만듭니다
    ③ ①에만 있는 것을 **운영 주소로 찔러** 200 인지 봅니다
    ④ 「잔재 / 보호 대상 / 판단 불가」로 가릅니다

    ★ 보호 대상(api/ · .htaccess · zh-cn/)은 **건드리면 안 되는
      것**이라 잔재로 세지 않습니다.
    ★ 못 닿은 것은 「판단 불가」입니다 — 없는 것으로 치지 않습니다.

쓰는 법
    python engine/check_server_leftover.py
    python engine/check_server_leftover.py --옛판 D:/바다가자/badagaja-site
"""
import io
import os
import sys
import glob
import json
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

뿌리 = os.environ.get('BADAGAJA_LIVE', 'https://badagaja.com')
옛판바탕 = os.environ.get('BADAGAJA_OLD', 'D:/바다가자/badagaja-site')
때 = 15

# 올라가지 않는 자리 — 옛 판 저장소에 있어도 서버에 없습니다
안올림 = ('oldsite/', 'tools/', 'tests/', 'node_modules/', '_', '.git/',
          'data-private/', 'docs/', 'backup', '.tmp/')

# 건드리면 안 되는 것 (감독팀 — 보호 대상)
보호 = ('api/', 'zh-cn/', '.htaccess')


def 서버에있나(길):
    """(코드, 바이트수) — 못 닿으면 (None, 까닭)"""
    주소 = 뿌리.rstrip('/') + '/' + 길.lstrip('/')
    req = urllib.request.Request(
        주소, method='HEAD',
        headers={'User-Agent': 'badagaja-leftover/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=때) as r:
            return r.getcode(), r.headers.get('Content-Length')
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:                            # noqa: BLE001
        return None, str(e)


def 쪽목록(바탕):
    것 = set()
    for p in glob.glob(os.path.join(바탕, '**', '*.html'), recursive=True):
        r = os.path.relpath(p, 바탕).replace('\\', '/')
        if any(r.startswith(x) or ('/' + x) in r for x in 안올림):
            continue
        것.add(r)
    return 것


def main():
    옛바탕 = 옛판바탕
    if '--옛판' in sys.argv:
        옛바탕 = sys.argv[sys.argv.index('--옛판') + 1]

    print()
    print('  서버에 남은 옛 판 잔재 — %s' % 뿌리)
    print('  (감독팀 지시 2 — **읽기만 합니다. 아무것도 지우지 않습니다**)')
    print()

    if not os.path.isdir(옛바탕):
        print('  ✗ 옛 판 저장소를 못 찾았습니다 — %s' % 옛바탕)
        print('    --옛판 으로 자리를 알려 주세요.')
        return 4                                      # 못잼

    옛 = 쪽목록(옛바탕)
    새 = 쪽목록(os.path.join(ROOT, 'site'))
    if not 옛 or not 새:
        print('  ✗ 쪽 목록이 비었습니다 (옛 %d · 새 %d)' % (len(옛), len(새)))
        return 4

    후보 = sorted(옛 - 새)
    print('  옛 판 %d쪽 · 새 판 %d쪽 · 새 판에 없는 옛 쪽 %d개'
          % (len(옛), len(새), len(후보)))
    print('  이제 **운영 주소로 하나씩 찔러** 살아 있는지 봅니다.')
    print()

    잔재, 보호된것, 모름, 없음 = [], [], [], 0
    for i, 길 in enumerate(후보, 1):
        if i % 40 == 0:
            print('    … %d/%d' % (i, len(후보)), flush=True)
        if any(길.startswith(x) for x in 보호):
            보호된것.append(길)
            continue
        코드, 덧 = 서버에있나(길)
        if 코드 is None:
            모름.append((길, 덧))
        elif 코드 == 200:
            잔재.append((길, 덧))
        else:
            없음 += 1

    print()
    print('  ── 가른 결과 ─────────────────────────────')
    print('  잔재(서버에 살아 있음)   %d개' % len(잔재))
    print('  보호 대상(안 봄)        %d개' % len(보호된것))
    print('  판단 불가(못 닿음)      %d개' % len(모름))
    print('  이미 없음(404 등)       %d개' % 없음)
    print()

    if 잔재:
        print('  ── 잔재 목록 ─────────────────────────────')
        for 길, 크기 in 잔재[:60]:
            print('    %-46s %s' % (길, (크기 + '바이트') if 크기 else ''))
        if len(잔재) > 60:
            print('    … 그 밖에 %d개' % (len(잔재) - 60))
        print()
    if 모름:
        print('  ── 판단 불가 ─────────────────────────────')
        for 길, 까닭 in 모름[:8]:
            print('    %s — %s' % (길, str(까닭)[:50]))
        print()

    # 보고서로 남깁니다
    낼곳 = os.path.join(ROOT, 'docs', '서버-잔재-대조.json')
    os.makedirs(os.path.dirname(낼곳), exist_ok=True)
    io.open(낼곳, 'w', encoding='utf-8').write(json.dumps({
        '_무엇인가': '서버에 남은 옛 판 쪽. 읽기만 했고 아무것도 '
                     '지우지 않았습니다 (감독팀 지시 2).',
        '_잰때': None,          # 시각을 안 넣습니다 (계약-08)
        '옛판쪽': len(옛), '새판쪽': len(새),
        '잔재': [x for x, _ in 잔재],
        '보호대상': 보호된것,
        '판단불가': [x for x, _ in 모름],
        '이미없음': 없음,
    }, ensure_ascii=False, indent=1) + '\n')
    print('  보고서: docs/서버-잔재-대조.json')
    print()

    if 모름:
        print('  ⬜ 못 닿은 것이 있어 **다 보지 못했습니다** (못잼)')
        return 4
    if 잔재:
        print('  ~ 잔재 %d개를 찾았습니다. **지우지 않았습니다** —'
              ' 무엇을 할지는 주인이 정하십니다.' % len(잔재))
        return 0        # 알림일 뿐, 막지 않습니다
    print('  ✓ 잔재가 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
