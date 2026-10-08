# -*- coding: utf-8 -*-
"""전체 백업을 건너뛰어도 되는가 **미리 봅니다** (2026-10-08).

★ 바깥 검수가 정한 전환 차례의 **2단계**입니다

      「full backup 을 건너뛰기 전에 직전 성공판 artifact 가 실제로
        존재하는지 확인합니다. 단순히 build_id 만 맞는 것이 아니라
        **직전 public build_id == 직전 성공 artifact build_id** 이고,
        **artifact 메타데이터가 존재**하고, **그 안의 build.json/
        manifest 가 읽히는** 상태여야 합니다. 이 셋 중 하나라도
        불확실하면 **기존 FTP 전체 백업으로 자동 fallback** 합니다」

★ 이 도구는 **묻기만 합니다.** 건너뛸지 말지는 배포가 정합니다.
  돌려주는 값
      0  괜찮습니다 — 건너뛰어도 됩니다
      3  **모르겠습니다** — 기존 전체 백업을 쓰세요
  ★ 3은 「틀렸다」가 아니라 「확신이 없다」입니다. 되돌리기 밑천을
    거는 일이라 **조금이라도 흐리면 기존 길**로 갑니다.
"""
import io
import json
import os
import subprocess
import sys
import urllib.request

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import release as R   # noqa: E402
from engine import shadow_tally   # noqa: E402

괜찮음 = 0
모르겠음 = 3
공개판주소 = 'https://badagaja.com/build.json'


def 공개판():
    try:
        req = urllib.request.Request(
            공개판주소, headers={'User-Agent': 'badagaja-preflight'})
        with urllib.request.urlopen(req, timeout=25) as r:
            if r.status != 200:
                return None, 'HTTP %s' % r.status
            return r.read().decode('utf-8', 'replace'), None
    except Exception as e:
        return None, str(e)


def 아티팩트목록():
    """직전 성공 배포가 봉해 둔 판 목록. `gh` 가 없으면 None."""
    들 = os.environ.get('BADAGAJA_ARTIFACTS')
    if 들:
        # 배포 일꾼이 미리 적어 준 것 (이름 한 줄씩)
        return [x.strip() for x in 들.splitlines() if x.strip()]
    try:
        끝 = subprocess.run(
            ['gh', 'api', '-X', 'GET',
             'repos/{owner}/{repo}/actions/artifacts',
             '-f', 'per_page=50', '--jq', '.artifacts[].name'],
            capture_output=True, text=True, timeout=40)
        if 끝.returncode != 0:
            return None
        return [x.strip() for x in (끝.stdout or '').splitlines()
                if x.strip()]
    except Exception:
        return None


def main():
    print('전체 백업을 건너뛰어도 되는가 (아티팩트 사전확인)')
    print('')

    # ── ① 그림자가 합격선을 넘었는가
    n = shadow_tally.연속()
    print('  [1] 그림자 연속 %d회 (합격선 %d회)'
          % (n, shadow_tally.합격선))
    if n < shadow_tally.합격선:
        print('      □ 아직입니다 — 기존 전체 백업을 씁니다')
        return 모르겠음

    # ── ② 공개 판을 읽을 수 있는가
    글, 왜 = 공개판()
    if 글 is None:
        print('  [2] □ 공개 판을 못 받았습니다 (%s)' % 왜)
        return 모르겠음
    공개파일, 공개id = R.판읽기(글)
    if 공개파일 is None or not 공개id:
        print('  [2] □ 공개 판을 읽을 수 없습니다')
        return 모르겠음
    print('  [2] 공개 판 %s · 파일 %d개' % (공개id, len(공개파일)))

    # ── ③ 그 판을 봉해 둔 아티팩트가 **정말 있는가**
    목록 = 아티팩트목록()
    if 목록 is None:
        print('  [3] □ 아티팩트 목록을 못 봤습니다 (gh 없음?)')
        return 모르겠음
    맞는것 = [x for x in 목록
              if x.startswith('배포판-') and 공개id in x]
    if not 맞는것:
        print('  [3] □ 공개 판(%s)을 봉해 둔 아티팩트가 없습니다'
              % 공개id)
        print('      (아티팩트 %d개 가운데 못 찾았습니다)' % len(목록))
        return 모르겠음
    print('  [3] 아티팩트 있음 — %s' % 맞는것[0])

    # ── ④ 그 안의 목록을 읽을 수 있는가
    받은길 = os.environ.get('BADAGAJA_PREV_BUILD_JSON')
    if not 받은길 or not os.path.isfile(받은길):
        print('  [4] □ 아티팩트 안의 build.json 을 아직 안 받았습니다')
        print('      (배포가 내려받아 BADAGAJA_PREV_BUILD_JSON 으로'
              ' 알려 주어야 합니다)')
        return 모르겠음
    옛파일, 옛id = R.판읽기(io.open(받은길, encoding='utf-8').read())
    if 옛파일 is None:
        print('  [4] □ 아티팩트 안의 목록을 못 읽었습니다')
        return 모르겠음
    if 옛id != 공개id:
        print('  [4] □ 판이 다릅니다 — 공개 %s · 아티팩트 %s'
              % (공개id, 옛id))
        print('      서버가 그 사이에 손으로 바뀌었을 수 있습니다')
        return 모르겠음
    print('  [4] 아티팩트 목록 읽힘 — 판 %s · 파일 %d개'
          % (옛id, len(옛파일)))

    print('')
    print('괜찮습니다 — 전체 백업을 건너뛰어도 됩니다.')
    print('  되돌려야 할 때는 이 아티팩트를 받아 씁니다.')
    return 괜찮음


if __name__ == '__main__':
    sys.exit(main())
