# -*- coding: utf-8 -*-
"""그림자 장부가 **제대로 세는가** (2026-10-08).

★ 이 장부가 「전체 백업을 건너뛰어도 되는가」를 정합니다. 잘못 세면
  **증명되지 않은 것을 증명된 것으로** 보고 19분짜리 안전장치를
  내립니다. 그래서 세는 법을 시험합니다.

★ 꼭 재야 하는 것
  · 연속이 **끊기면 0** 으로 돌아가는가 (세 번 중 두 번으로는 안 됨)
  · 같은 판을 **두 번 적어도 안 부푸는가** (다시 돌려도 괜찮아야)
"""
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import shadow_tally as T   # noqa: E402

실패 = []


def 봄(이름, 참인가, 덧=''):
    if 참인가:
        print('  · %s' % 이름)
    else:
        print('  ✗ %s' % 이름)
        if 덧:
            print('      %s' % 덧)
        실패.append(이름)


def main():
    print('그림자 장부가 제대로 세는가')
    print('')

    # 본 장부를 건드리지 않습니다 — 임시 자리로 옮겨 놓고 씁니다
    import tempfile
    t = tempfile.mkdtemp(prefix='장부-')
    참길 = T.장부길
    T.장부길 = os.path.join(t, '그림자장부.json')
    try:
        봄('처음에는 0회', T.연속() == 0, T.연속())

        T.적기('aaa', True)
        T.적기('bbb', True)
        봄('두 번 같으면 2회', T.연속() == 2, T.연속())

        T.적기('ccc', False, '새것만 3개')
        봄('한 번 다르면 **0으로 돌아갑니다**', T.연속() == 0, T.연속())

        T.적기('ddd', True)
        T.적기('eee', True)
        T.적기('fff', True)
        봄('그 뒤 세 번 같으면 3회', T.연속() == 3, T.연속())
        봄('합격선을 넘었습니다', T.연속() >= T.합격선)

        # ★ 같은 판을 두 번 적어도 안 부풀어야 합니다
        앞 = T.연속()
        T.적기('fff', True)
        봄('같은 판을 두 번 적어도 안 부풉니다', T.연속() == 앞,
           '%s → %s' % (앞, T.연속()))

        # ★ 같은 판이 **다르게** 다시 적히면 그 값이 이겨야 합니다
        T.적기('fff', False, '다시 재니 달랐습니다')
        봄('같은 판을 다시 적으면 새 값이 이깁니다', T.연속() == 0,
           T.연속())

        # 기록이 끝없이 늘지 않아야 합니다
        for i in range(40):
            T.적기('p%d' % i, True)
        장부 = T.읽기()
        봄('기록이 끝없이 늘지 않습니다',
           len(장부.get('기록') or []) <= 20,
           len(장부.get('기록') or []))
    finally:
        T.장부길 = 참길
        import shutil
        shutil.rmtree(t, ignore_errors=True)

    print('')
    if 실패:
        print('✗ %d가지가 틀렸습니다' % len(실패))
        return 1
    print('모두 통과 — 장부를 믿을 수 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
