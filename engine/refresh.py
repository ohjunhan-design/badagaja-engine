# -*- coding: utf-8 -*-
"""자료를 옛 사이트에서 다시 캐냅니다 — **여기 하나로만** 합니다.

★ 왜 이 파일이 있나 (2026-09-26, tests/test_idempotent.py 가 잡음)

    이관 도구 여덟은 저마다 멱등적입니다. 두 번 돌려도 같습니다.
    그런데 **차례가 어긋나면** 결과가 달라집니다.

        migrate.py      포인트를 캐 씁니다 — 대상이 「감성돔·농어」
        fix_species.py  그 파일을 열어 아이디로 바꿉니다 — 「gamseongdom」

    같은 파일을 둘이 건드립니다. 자료를 갱신하려고 migrate 만
    다시 돌리면, fix_species 가 해 둔 일이 **통째로 날아갑니다.**

    그런데 파일 개수도 포인트 수도 그대로입니다.
    개수를 세는 검사는 아무것도 못 잡습니다.

    사람이 차례를 외우게 두면 언젠가 틀립니다.
    그래서 차례를 **여기 한 곳에** 적어 둡니다.

쓰는 법
    python engine/refresh.py             무엇을 할지 보여만 줍니다
    python engine/refresh.py --write     자료를 다시 캐냅니다
    python engine/refresh.py --write --only migrate   하나만 (위험)

★ 하나만 돌리는 것은 왜 위험한가
    --only 는 고칠 때 쓰라고 둔 것입니다. 끝나고 나면 반드시
    --write 로 차례 전체를 한 번 돌려야 합니다. 안 그러면 뒤 도구가
    할 일이 남아 자료가 어중간한 자리에 멈춥니다.
    check_stale.py 가 그 상태를 잡습니다.
"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# ★ **이 차례가 유일한 출처입니다.** 다른 데 베껴 적지 않습니다.
#   새 이관 도구를 만들면 여기 한 줄 더합니다.
#   앞이 캐고 뒤가 다듬습니다. 뒤엣것을 앞으로 옮기면 안 됩니다.
#
# ★★ 2026-09-28 — 이 목록이 **통째로 터져 있었습니다**
#
#   2026-09-27 에 사진·첫화면·지도를 더하면서 칸 수를 틀리게 넣었습니다.
#
#       ('migrate.py', '설명')                    ← 2칸
#       ('migrate_photos.py', ('--write',), '설명')  ← 3칸
#
#   푸는 쪽은 `for 도구, 설명 in 차례` 로 2칸을 봅니다. 3칸이 오니
#
#       ValueError: too many values to unpack (expected 2)
#
#   **그날부터 `refresh.py` 가 아예 안 돌았습니다.** 자료를 매달
#   다시 캐는 도구인데 죽어 있었습니다. 다음 달 갱신이 통째로
#   안 될 뻔했습니다. 18번 판정(멱등성)이 이것을 가리키고 있었는데
#   저는 「자료가 안 돌아온다」로만 읽고 뿌리를 안 봤습니다.
#
#   ★ 그리고 같은 차례가 `tests/test_idempotent.py` 에 **따로 적혀**
#     있었고 **서로 달랐습니다** (fix_species 자리가 다르고
#     migrate_home 이 빠져 있었습니다). 그래서 시험과 실제가
#     다른 것을 재고 있었습니다.
#     이제 그 시험은 **이 목록을 읽어 씁니다.** 베끼지 않습니다.
#
#   칸은 셋으로 통일했습니다 — (도구, 인자, 설명)
차례 = [
    ('migrate.py', ('--write',), '포인트 8묶음 2,526곳을 옛 자료에서'),
    ('extract_jeonnam.py', ('--write',), '전남 1,077곳을 옛 HTML 에서'),
    ('migrate_index.py', ('--write',), '57권역 색인'),
    ('migrate_travel.py', ('--write',), '여행지'),
    ('extract_jeonnam_travel.py', ('--write',), '전남 여행지'),
    ('migrate_festival.py', ('--write',), '축제'),
    ('migrate_guide.py', ('--write',), '안내글'),
    ('migrate_zh.py', ('--write',), '중국어 낱말표 (옛 zh-cn/i18n/ 에서)'),
    # ★ 2026-09-27 에 더했습니다 — 사진·첫화면 차림표·지도
    ('migrate_photos.py', ('--write',), '사진'),
    ('migrate_home.py', ('--write',), '옛 첫 화면 차림표'),
    ('migrate_map.py', ('--write',), '전국 바다지도 좌표'),
    # ★ 2026-09-28 — 만들고 여기 안 적어 계약-27 을 어겼습니다
    ('migrate_tidegraph.py', ('--write',), '시간별 물높이 그래프'),
    # ↓ 여기부터는 **앞이 캔 것을 다듬는** 도구입니다. 반드시 뒤에 옵니다.
    ('fix_species.py', ('--write',), '어종 이름을 아이디로 (앞이 캔 것을 고칩니다)'),
]

다듬는것 = ('fix_species.py',)


def 돌리기(도구, 쓰기):
    인자 = [sys.executable, os.path.join(HERE, 도구)]
    if 쓰기:
        인자.append('--write')
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_DATA'] = DATA
    r = subprocess.run(인자, env=환경, timeout=3600)
    return r.returncode


def main():
    쓰기 = '--write' in sys.argv
    하나만 = None
    if '--only' in sys.argv:
        i = sys.argv.index('--only')
        if i + 1 < len(sys.argv):
            하나만 = sys.argv[i + 1]
            if not 하나만.endswith('.py'):
                하나만 += '.py'

    print('자료를 다시 캐냅니다')
    print('  나갈 자리: %s' % DATA)
    print('')

    할것 = [x for x in 차례 if not 하나만 or x[0] == 하나만]
    if 하나만 and not 할것:
        print('그런 도구가 없습니다: %s' % 하나만)
        print('  있는 것: %s' % ' · '.join(x[0] for x in 차례))
        return 1

    for i, (도구, _인자, 설명) in enumerate(할것, 1):
        print('  %d. %-26s %s' % (i, 도구, 설명))
    print('')

    if 하나만 and 하나만 not in 다듬는것:
        print('★ 하나만 돌립니다 — 끝나면 차례 전체를 한 번 더 돌리세요.')
        print('  앞 도구가 캔 것을 뒤 도구가 다듬습니다. 건너뛰면')
        print('  자료가 어중간한 자리에 멈춥니다.')
        print('')

    if not 쓰기:
        print('보여만 준 것입니다. 하려면 --write 를 붙이세요.')
        return 0

    for i, (도구, _인자, 설명) in enumerate(할것, 1):
        print('')
        print('─' * 60)
        print('  %d/%d  %s' % (i, len(할것), 도구))
        print('─' * 60)
        코드 = 돌리기(도구, True)
        if 코드 != 0:
            print('')
            print('★ %s 가 %d 로 멈췄습니다. 차례를 여기서 세웁니다.' % (도구, 코드))
            print('  뒤엣것을 안 돌렸으니 자료가 어중간합니다.')
            print('  고친 뒤 처음부터 다시 돌리세요.')
            return 코드

    print('')
    print('─' * 60)
    print('차례 %d개를 모두 마쳤습니다.' % len(할것))
    print('  이어서 확인하세요:')
    print('    python engine/check_stale.py       자료가 어중간하지 않은가')
    print('    python engine/verify_migration.py  옛 사이트와 맞는가')
    print('    python engine/build.py --all       쪽을 다시 만듭니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
