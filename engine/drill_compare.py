# -*- coding: utf-8 -*-
"""되돌리기 연습에서 **새 셈이 진짜와 맞는지** 잽니다 (2026-10-08).

★ 연습 칸의 A판·B판은 **우리가 만든 것**이라 무엇이 늘고 줄었는지
  이미 알고 있습니다. 그래서 새 셈이 맞는지 가릴 수 있습니다.

★ 워크플로 안에 파이썬을 바로 적지 않고 **파일로 둡니다.**
  짜임 검사가 「워크플로에 한글 식별자가 있습니다」로 잡았습니다 —
  YAML 안의 인라인 코드는 들여쓰기·따옴표·인코딩에 걸리기 쉽고,
  무엇보다 **시험할 수가 없습니다.** 파일이면 여기서 바로 돌려 봅니다.
"""
import hashlib
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import release_diff as R   # noqa: E402


def 지문들(밭):
    """폴더의 `{상대경로: 지문}`."""
    난것 = {}
    for 뿌리, _, 파일들 in os.walk(밭):
        for f in 파일들:
            p = os.path.join(뿌리, f)
            r = os.path.relpath(p, 밭).replace(os.sep, '/')
            h = hashlib.sha256()
            try:
                with open(p, 'rb') as fp:
                    for 덩이 in iter(lambda: fp.read(65536), b''):
                        h.update(덩이)
            except Exception:
                continue
            난것[r] = h.hexdigest()
    return 난것


def main():
    앞 = sys.argv[1] if len(sys.argv) > 1 else '_A'
    뒤 = sys.argv[2] if len(sys.argv) > 2 else '_B'
    칸 = os.environ.get('CARD', '_stage')

    print('── 새 방식(release.py)이 셈한 것과 실제를 견줍니다')
    if not os.path.isdir(앞) or not os.path.isdir(뒤):
        print('   □ %s 나 %s 가 없습니다 — 재지 못했습니다' % (앞, 뒤))
        return 0

    옛 = 지문들(앞)
    새 = 지문들(뒤)
    print('   %s %d개 · %s %d개' % (앞, len(옛), 뒤, len(새)))

    계획 = R.되돌림계획(옛, 새)
    print('   셈한 것 — 지울 것 %d개 · 되돌릴 것 %d개'
          % (len(계획['지울것']), len(계획['되돌릴것'])))

    # 진짜 — 뒤에만 있는 것 / 달라졌거나 앞에만 있는 것
    진짜지울것 = sorted(k for k in 새 if k not in 옛
                        and not R.건드리면안되나(k))
    진짜되돌릴것 = sorted(
        k for k in 옛
        if (k not in 새 or 옛[k] != 새[k]) and not R.건드리면안되나(k))

    나쁨 = 0
    if 계획['지울것'] != 진짜지울것:
        print('   ✗ 지울 것이 다릅니다')
        print('      셈: %s' % 계획['지울것'][:5])
        print('      참: %s' % 진짜지울것[:5])
        나쁨 = 1
    else:
        print('   · 지울 것이 진짜와 똑같습니다')
    if 계획['되돌릴것'] != 진짜되돌릴것:
        print('   ✗ 되돌릴 것이 다릅니다')
        print('      셈: %s' % 계획['되돌릴것'][:5])
        print('      참: %s' % 진짜되돌릴것[:5])
        나쁨 = 1
    else:
        print('   · 되돌릴 것이 진짜와 똑같습니다')

    위험 = R.위험한가(계획, 모두=len(새))
    print('   위험한가: %s' % (위험 or '아니오'))

    줄들, 뺀것 = R.lftp지우기(계획['지울것'], 뿌리='/www/%s/' % 칸)
    print('   지우는 명령 %d줄 (뺀 것 %d개)' % (len(줄들), len(뺀것)))
    for x in 줄들[:3]:
        print('      %s' % x)
    return 나쁨


if __name__ == '__main__':
    sys.exit(main())
