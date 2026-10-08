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
import json
import os
import re
import sys
import glob

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ★ **볼 자리를 바꿀 수 있게 둡니다** (2026-10-08)
#   그래야 일부러 깨뜨린 설정을 임시 폴더에 두고 **검사기가 정말
#   잡는지** 재어 볼 수 있습니다. 시험이 없으면 검사기가 조용히
#   헛돌아도 모릅니다 (기억 「뮤테이션은 정말 망가뜨려야」).
일꾼터 = os.environ.get(
    'BADAGAJA_WORKFLOWS',
    os.path.join(여기, '.github', 'workflows'))

# ★ **작업 수준 `env:` 에서 못 쓰는 것** — 단계 안에서만 삽니다
단계전용 = ('runner', 'steps', 'job', 'matrix', 'strategy')

# 깃허브가 아는 컨텍스트 이름
아는것 = ('github', 'env', 'vars', 'secrets', 'inputs', 'needs',
          'runner', 'steps', 'job', 'jobs', 'matrix', 'strategy')

# ★ **자리마다 쓸 수 있는 컨텍스트가 다릅니다** (바깥 검수가 준 표)
#   「env, jobs.<id>.env, runs-on, job.if, step.if … 마다 허용
#     컨텍스트가 다릅니다. 예를 들어 jobs.<job_id>.env 에도 runner 는
#     안 되고, jobs.<job_id>.if 에는 runner·secrets·matrix 도
#     허용되지 않습니다. 반면 step 수준은 훨씬 넓습니다」
#   한 줄 때문에 워크플로가 통째로 거절되고, 그동안 배포를 걸
#   수도 없습니다 (2026-10-08에 여섯 번 겪음).
자리별허용 = {
    'jobs.<id>.if': ('github', 'needs', 'vars', 'inputs'),
    'jobs.<id>.env': ('github', 'needs', 'strategy', 'matrix',
                      'vars', 'secrets', 'inputs'),
    'runs-on': ('github', 'needs', 'strategy', 'matrix', 'vars', 'inputs'),
}

# ★ **재사용 워크플로를 부르는 작업**은 쓸 수 있는 칸이 좁습니다
#   「jobs.<id>.uses: 로 다른 workflow 를 부르는 job 은 일반 job 처럼
#     runs-on·steps·env 등을 마음대로 같이 둘 수 없습니다」
재사용허용 = ('uses', 'with', 'secrets', 'needs', 'if', 'permissions',
              'strategy', 'concurrency', 'name')

# ★ **셸에서 쓸 수 없는 변수 이름** — 한글로 시작하는 대입
#   bash 는 `밭=값` 을 **명령**으로 읽습니다 (exit 127).
def _셸변수한글(줄):
    """그 줄이 **셸 변수를 한글로 짓는** 대입인가.

    ★ 정규식을 안 씁니다 (2026-10-08에 겪음)
      `[^\\x00-\\x7f]` 를 쓰려다 도구를 거치며 **진짜 널 바이트**가
      파일에 박혔고, 파이썬이 「source code cannot contain null
      bytes」로 파일 전체를 못 읽었습니다.
      글자 코드를 직접 보는 편이 짧고 안전합니다.
      (기억 「정규식에 백슬래시 쓰지 않기」와 같은 종류입니다)
    """
    벗 = (줄 or '').strip()
    if '=' not in 벗:
        return False
    앞 = 벗.split('=', 1)[0]
    if not 앞 or ' ' in 앞 or '"' in 앞 or "'" in 앞:
        return False
    return ord(앞[0]) > 127


def 겹친키찾기(글):
    """**같은 칸을 두 번 적은 곳**을 찾습니다 (2026-10-08 바깥 검수).

    ★ 「PyYAML 은 중복 키를 기본적으로 **경고 없이 마지막 값으로
      덮는** 경우가 있어 별도 duplicate-key loader 가 좋습니다」

      `steps` 의 `id` 가 겹치거나 작업 이름이 겹치면, 읽을 때는
      조용히 하나만 남습니다. **쓴 사람은 둘 다 돈다고 믿습니다.**
      YAML 로는 완벽히 정상이라 문법 검사로는 못 잡습니다.
    """
    try:
        import yaml
    except ImportError:
        return []

    난것 = []

    class _겹침잡개(yaml.SafeLoader):
        pass

    def _매핑(loader, node, deep=False):
        본것 = set()
        for k, _v in node.value:
            키 = loader.construct_object(k, deep=deep)
            try:
                if 키 in 본것:
                    난것.append((str(키), k.start_mark.line + 1))
                본것.add(키)
            except TypeError:
                pass
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    _겹침잡개.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _매핑)
    try:
        yaml.load(글, Loader=_겹침잡개)
    except Exception:                                 # noqa: BLE001
        return []          # 못 읽는 것은 ①에서 따로 잡습니다
    return 난것


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

    # ★ **PyYAML 이 없으면 「못 잼」입니다. 통과가 아닙니다.**
    #   (2026-10-08 — 배포 #41 이 이것을 드러냈습니다)
    #
    #   `setup-python` 은 깨끗한 파이썬을 깝니다. 우분투 러너에는
    #   PyYAML 이 없어, 이 검사기가 짜임을 **하나도 안 보고**
    #   「✅ 통과 · 이름·걸리는 조건·컨텍스트가 모두 제자리입니다」
    #   를 찍고 있었습니다. 제 윈도우에서는 PyYAML 이 있어 멀쩡히
    #   돌았으므로 **반 년이라도 모를 수 있었습니다.**
    #
    #   검사가 안 돌았는데 통과로 보이는 것이 가장 나쁜 꼴입니다.
    try:
        import yaml                                   # noqa: F401
    except ImportError:
        print()
        print('  ✗ PyYAML 이 없어 일꾼 설정을 **한 줄도 못 봤습니다.**')
        print('    이것은 통과가 아닙니다 — `pip install PyYAML` 하세요.')
        print('    (일꾼 설정 넷에 깔기 단계가 들어 있습니다)')
        return 4
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

        # ⑤ **같은 칸을 두 번 적지 않았는가** (바깥 검수)
        for 키, 줄번 in 겹친키찾기(글):
            막음.append('%s:%d — 같은 칸을 두 번 적었습니다 (`%s`) —'
                        ' 조용히 마지막 것만 남습니다' % (짧, 줄번, 키))

        # ⑥⑦ **자리마다 쓸 수 있는 컨텍스트가 다릅니다**
        #     작업(job) 안을 보려면 짜임이 필요합니다
        작업들 = (d.get('jobs') or {}) if isinstance(d, dict) else {}
        for 작업이름, 작업 in (작업들.items()
                               if isinstance(작업들, dict) else []):
            if not isinstance(작업, dict):
                continue

            # ⑥ 재사용 워크플로를 부르는 작업은 둘 수 있는 칸이 좁습니다
            if 작업.get('uses'):
                덤 = [k for k in 작업 if k not in 재사용허용]
                if 덤:
                    막음.append(
                        '%s — 작업 `%s` 는 다른 워크플로를 부르는데'
                        ' `%s` 를 함께 두었습니다 (못 둡니다)'
                        % (짧, 작업이름, ', '.join(sorted(덤)[:3])))
                continue      # 아래 검사는 일반 작업 것입니다

            # ⑦ 자리별 허용 컨텍스트
            for 자리, 값 in (('jobs.<id>.if', 작업.get('if')),
                             ('runs-on', 작업.get('runs-on'))):
                쓴것 = re.findall(r'\$\{\{\s*([A-Za-z_][\w-]*)\s*\.',
                                  str(값 or ''))
                for 이름 in 쓴것:
                    if 이름 not in 자리별허용[자리]:
                        막음.append(
                            '%s — 작업 `%s` 의 `%s` 에서 `%s` 를 쓸 수'
                            ' 없습니다' % (짧, 작업이름, 자리, 이름))
            작업env = 작업.get('env')
            if isinstance(작업env, dict):
                for _k, v in 작업env.items():
                    for 이름 in re.findall(
                            r'\$\{\{\s*([A-Za-z_][\w-]*)\s*\.', str(v or '')):
                        if 이름 not in 자리별허용['jobs.<id>.env']:
                            막음.append(
                                '%s — 작업 `%s` 의 `env:` 에서 `%s` 를'
                                ' 쓸 수 없습니다 (단계 안에서만 삽니다)'
                                % (짧, 작업이름, 이름))

            # ⑧ 일반 작업이면 `runs-on` 과 `steps` 가 있어야 합니다
            if not 작업.get('runs-on'):
                막음.append('%s — 작업 `%s` 에 `runs-on` 이 없습니다'
                            % (짧, 작업이름))
            if not 작업.get('steps'):
                막음.append('%s — 작업 `%s` 에 `steps` 가 없습니다'
                            % (짧, 작업이름))
                continue

            # ⑨ **없는 것을 가리키지 않는가** (바깥 검수가 더 넣으라 한 것)
            #   「`steps.foo.outputs.bar`·`needs.build.outputs.x` 처럼
            #     참조했는데 실제 `id: foo` 나 `needs: build` 가 없는
            #     경우. 깃허브에서 **빈 문자열**이 되거나 검증 오류가
            #     섞여 나오니 정적으로 잡는 게 좋습니다」
            #   빈 문자열로 조용히 흘러가는 것이 가장 나쁩니다 —
            #   배포가 「성공」했는데 값이 비어 있을 수 있습니다.
            단계들 = 작업.get('steps') or []
            있는id = set()
            for s in 단계들:
                if isinstance(s, dict) and s.get('id'):
                    있는id.add(str(s['id']))
            필요 = 작업.get('needs')
            있는needs = set()
            if isinstance(필요, str):
                있는needs.add(필요)
            elif isinstance(필요, list):
                있는needs |= set(str(x) for x in 필요)

            글조각 = json.dumps(작업, ensure_ascii=False)
            for 쓴id in set(re.findall(r'steps\.([^.\s}]+)\.', 글조각)):
                if 쓴id not in 있는id:
                    막음.append(
                        '%s — 작업 `%s` 가 없는 단계 `steps.%s` 를'
                        ' 가리킵니다 (빈 값이 됩니다)'
                        % (짧, 작업이름, 쓴id))
            for 쓴n in set(re.findall(r'needs\.([^.\s}]+)\.', 글조각)):
                if 쓴n not in 있는needs:
                    막음.append(
                        '%s — 작업 `%s` 가 `needs:` 에 없는 `%s` 를'
                        ' 가리킵니다' % (짧, 작업이름, 쓴n))

            # ⑪ **셸 변수 이름을 한글로 짓지 않았는가** (2026-10-08에 겪음)
            #
            #   `밭="..."` 라고 썼더니 bash 가 그것을 **명령으로** 읽어
            #   `exit code 127`(명령 없음)로 배포가 3초 만에 죽었습니다.
            #       line 1: 밭=/home/runner/work/...: No such file or directory
            #
            #   이 저장소는 파이썬 변수를 **일부러 한글로** 씁니다.
            #   그 버릇이 셸로 넘어오면 죽습니다. 파이썬은 받고
            #   셸은 못 받습니다 — **같은 파일 안에서 규칙이 다릅니다.**
            #   YAML 로는 완벽히 정상이라 문법 검사로는 못 잡습니다.
            for i, s in enumerate(단계들, 1):
                if not isinstance(s, dict) or not s.get('run'):
                    continue
                쉘 = str(s.get('shell') or 'bash')
                if 'pwsh' in 쉘 or 'powershell' in 쉘:
                    continue      # 파워셸은 `$한글` 을 받습니다
                for 줄 in str(s['run']).splitlines():
                    벗 = 줄.strip()
                    if _셸변수한글(벗):
                        막음.append(
                            '%s — 작업 `%s` %d번째 단계가 **셸 변수를'
                            ' 한글로** 지었습니다 — bash 는 명령으로'
                            ' 읽고 죽습니다 (%s)'
                            % (짧, 작업이름, i, 벗[:30]))
                        break

            # ⑩ 단계마다 `run` 이나 `uses` 가 있어야 합니다
            for i, s in enumerate(단계들, 1):
                if not isinstance(s, dict):
                    continue
                if not s.get('run') and not s.get('uses'):
                    막음.append(
                        '%s — 작업 `%s` 의 %d번째 단계에 `run` 도'
                        ' `uses` 도 없습니다 (%s)'
                        % (짧, 작업이름, i, s.get('name') or '이름 없음'))

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
