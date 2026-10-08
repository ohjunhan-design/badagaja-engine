# -*- coding: utf-8 -*-
"""일꾼 설정(.github/workflows)이 **깃허브가 읽을 수 있는가** (2026-10-08).

★ 왜 만드나 — 한 줄 때문에 **배포를 못 걸었습니다**

  그림자 장부 자리를 `env:` 에 적으며 이렇게 썼습니다

      BADAGAJA_TALLY: ${{ runner.workspace }}/../장부.json

  깃허브가 거절했습니다 —

      Invalid workflow file: .github/workflows/deploy.yml#L1
      (Line: 92, Col: 23): Unrecognized named-value: 'runner'.

  `runner` 컨텍스트는 **단계(step) 안에서만** 살아 있습니다.
  작업(job) 수준 `env:` 에서는 못 씁니다.

★ 무엇이 나빴나 — **깨진 것을 한참 몰랐습니다**

  깨진 워크플로는 조용히 가만있지 않습니다. 푸시할 때마다
  「Invalid workflow file」로 **실패 기록을 남기고**, 그동안
  **배포를 걸 수도 없습니다.** 여섯 번 그러고서야, 그것도
  화면에서 워크플로 이름이 「운영 배포」가 아니라 파일 경로로
  바뀐 것을 보고 알았습니다.

  내 컴퓨터에서는 **YAML 문법만 맞으면 통과**합니다. 깃허브가
  거절하는 것은 문법이 아니라 **쓸 수 없는 자리에 쓴 값**입니다.
  그래서 그 규칙을 여기 옮겨 둡니다.

★ 보는 것
  ① YAML 로 읽히는가
  ② `name:` 과 `on:` 이 있는가 (없으면 깃허브가 파일 경로를
     이름으로 씁니다 — 깨졌다는 신호입니다)
  ③ **작업 수준 `env:` 에서 단계 전용 컨텍스트를 쓰지 않는가**
  ④ 쓰는 컨텍스트 이름이 깃허브가 아는 것인가

쓰는 법
    python engine/check_workflow.py
    python engine/check_workflow.py --strict
"""
import io
import os
import re
import sys
import glob

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

일꾼터 = os.path.join(여기, '.github', 'workflows')

# ★ **작업 수준 `env:` 에서 못 쓰는 것** — 단계 안에서만 삽니다
단계전용 = ('runner', 'steps', 'job', 'matrix', 'strategy')

# 깃허브가 아는 컨텍스트 이름
아는것 = ('github', 'env', 'vars', 'secrets', 'inputs', 'needs',
          'runner', 'steps', 'job', 'jobs', 'matrix', 'strategy')


def 주석뺀것(줄):
    """`#` 뒤를 지웁니다.

    ★ 처음에는 주석까지 봤습니다. 그래서 **「이렇게 쓰면 깨집니다」고
      적어 둔 주석**을 잘못으로 잡았습니다. 고친 내력을 적어 두는
      것이 이 저장소의 방식인데, 그것을 막으면 안 됩니다.
    """
    i = 줄.find('#')
    return 줄 if i < 0 else 줄[:i]


def env칸찾기(글):
    """**작업 수준** `env:` 블록의 줄 범위를 찾습니다.

    ★ `steps:` **안**의 `env:` 는 빼야 합니다 (2026-10-08에 겪음)
      단계 안의 `env:` 에서는 `steps.*` 를 쓸 수 있습니다. 처음에
      들여쓰기만 보고 모두 잡았더니, 멀쩡히 돌던 `gate.yml` 의
      네 줄을 잘못으로 세었습니다. **잡는 것이 느는 것과 맞게
      잡는 것은 다릅니다.**

      그래서 `steps:` 를 만난 뒤로는 그 작업의 `env:` 를 보지
      않습니다. 다음 작업이 시작되면(들여쓰기가 얕아지면) 다시 봅니다.
    """
    줄들 = 글.splitlines()
    범위 = []
    steps깊이 = None
    i = 0
    while i < len(줄들):
        줄 = 주석뺀것(줄들[i])
        m단계 = re.match(r'^(\s+)steps:\s*$', 줄)
        if m단계:
            steps깊이 = len(m단계.group(1))
            i += 1
            continue
        if (steps깊이 is not None and 줄.strip()
                and not 줄.startswith(' ' * steps깊이)):
            steps깊이 = None        # 새 작업이 시작됐습니다
        m = re.match(r'^(\s+)env:\s*$', 줄)
        if m and steps깊이 is None:
            깊이 = len(m.group(1))
            j = i + 1
            while j < len(줄들):
                if (줄들[j].strip()
                        and not 줄들[j].startswith(' ' * (깊이 + 1))):
                    break
                j += 1
            범위.append((i + 1, j, 깊이))
            i = j
            continue
        i += 1
    return 범위


def main():
    엄격 = '--strict' in sys.argv
    막음, 알림 = [], []
    파일들 = sorted(glob.glob(os.path.join(일꾼터, '*.yml'))
                    + glob.glob(os.path.join(일꾼터, '*.yaml')))
    if not 파일들:
        print('□ 일꾼 설정을 못 찾았습니다 — %s' % 일꾼터)
        return 4 if 엄격 else 0

    print()
    print('  일꾼 설정이 깃허브가 읽을 수 있는 꼴인가')
    print()

    for 길 in 파일들:
        짧 = os.path.basename(길)
        글 = io.open(길, encoding='utf-8', errors='replace').read()

        # ① YAML 로 읽히는가
        d = None
        try:
            import yaml
            d = yaml.safe_load(글)
        except ImportError:
            알림.append('%s — yaml 이 없어 짜임을 못 봤습니다' % 짧)
        except Exception as e:                        # noqa: BLE001
            막음.append('%s — YAML 로 안 읽힙니다 (%s)'
                        % (짧, str(e)[:60]))
            continue

        if isinstance(d, dict):
            # ② 이름과 걸리는 조건
            if not d.get('name'):
                알림.append('%s — `name:` 이 없습니다 (깃허브 화면에'
                            ' 파일 경로가 뜹니다)' % 짧)
            # YAML 은 `on:` 을 참(True)으로 읽습니다 — 둘 다 봅니다
            if 'on' not in d and True not in d:
                막음.append('%s — `on:` 이 없습니다 (아무 때도 안 돕니다)'
                            % 짧)

        # ③ 작업 수준 env 에서 단계 전용 컨텍스트
        줄들 = 글.splitlines()
        for 시작, 끝, _깊이 in env칸찾기(글):
            for n in range(시작, min(끝, len(줄들))):
                줄 = 주석뺀것(줄들[n])
                for 이름 in re.findall(r'\$\{\{\s*([A-Za-z_][\w-]*)', 줄):
                    if 이름 in 단계전용:
                        막음.append(
                            '%s:%d — `env:` 에서 `%s` 를 쓸 수 없습니다'
                            ' (단계 안에서만 삽니다)' % (짧, n + 1, 이름))

        # ④ 아예 모르는 컨텍스트 이름
        for n, 줄 in enumerate(줄들, 1):
            for 이름 in re.findall(r'\$\{\{\s*([A-Za-z_][\w-]*)\s*\.', 주석뺀것(줄)):
                if 이름 not in 아는것:
                    알림.append('%s:%d — 모르는 이름 `%s`'
                                % (짧, n, 이름))

    print('  파일 %d개를 봤습니다' % len(파일들))
    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        print()
        print('  **깨진 일꾼 설정은 조용하지 않습니다.** 푸시마다')
        print('  실패 기록을 남기고, 그동안 배포를 걸 수도 없습니다.')
        return 1
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:6]:
            print('  ! %s' % t)
    print('  · 이름·걸리는 조건·컨텍스트가 모두 제자리입니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
