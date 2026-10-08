# -*- coding: utf-8 -*-
"""일꾼 설정 검사기(`check_workflow`)의 **회귀시험** (2026-10-08).

★ 왜 이 시험이 있나 — 바깥 검수가 못박았습니다

    「PyYAML 은 YAML 1.1 규칙 때문에 `on`·`off`·`yes`·`no` 를
      **boolean 으로 읽을 수** 있습니다. GitHub Actions 는 `on:` 을
      정상 키로 쓰므로, `safe_load()` 결과만 보고 `on` 존재 여부를
      검사하면 **검사기 자체가 틀릴 수 있습니다.**
      이건 지금 검사기에 **꼭 회귀시험을 하나 넣으세요**」

  실제로 그렇습니다. `deploy.yml` 을 읽으면 키가 이렇게 나옵니다 —
      ['name', True, 'concurrency', 'permissions', 'jobs']
  `'on'` 은 **없고** `True` 가 있습니다.

  검사기는 둘 다 보게 해 두었지만, **그 한 줄을 누가 지우면**
  검사기가 멀쩡한 워크플로를 「`on:` 이 없습니다」로 막습니다.
  그때 배포가 통째로 멈춥니다. 그것을 막는 시험입니다.

★ 그리고 2026-10-08 에 실제로 겪은 것들을 그대로 재현합니다 —
  작업 `env:` 의 `runner`, 같은 칸 두 번 적기.

  python tests/test_workflow_check.py
"""
import io
import os
import subprocess
import sys
import tempfile
import shutil

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

ok, fail = 0, 0


def 시험(이름, 조건, 설명=''):
    global ok, fail
    if 조건:
        ok += 1
        print('  · %s' % 이름)
    else:
        fail += 1
        print('  ✗ %s   %s' % (이름, 설명))


def 돌리기(글, yaml없이=False):
    """그 글을 워크플로 한 장으로 두고 검사기를 돌립니다.

    `yaml없이=True` 면 **PyYAML 을 못 찾는 환경**을 흉내 냅니다 —
    우분투 러너가 그렇습니다. 가짜 `yaml.py` 를 앞세워 import 를
    실패시킵니다.
    """
    터 = tempfile.mkdtemp(prefix='wf-test-')
    try:
        밭 = os.path.join(터, 'workflows')
        os.makedirs(밭)
        io.open(os.path.join(밭, 'a.yml'), 'w', encoding='utf-8').write(글)
        환 = dict(os.environ)
        환['PYTHONUTF8'] = '1'
        환['BADAGAJA_WORKFLOWS'] = 밭
        if yaml없이:
            가짜 = os.path.join(터, 'yaml없는곳')
            os.makedirs(가짜)
            io.open(os.path.join(가짜, 'yaml.py'), 'w',
                    encoding='utf-8').write(
                        "raise ImportError('없는 셈 칩니다')\n")
            환['PYTHONPATH'] = 가짜
        끝 = subprocess.run(
            [sys.executable, '-X', 'utf8',
             os.path.join(여기, 'engine', 'check_workflow.py')],
            cwd=여기, env=환, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=180)
        return 끝.returncode
    finally:
        shutil.rmtree(터, ignore_errors=True)


멀쩡한것 = (
    'name: 괜찮은 것\n'
    'on:\n'
    '  workflow_dispatch:\n'
    'jobs:\n'
    '  hi:\n'
    '    runs-on: ubuntu-latest\n'
    '    steps:\n'
    '      - run: echo 1\n')


def main():
    print('일꾼 설정 검사기 시험 — 2026-10-08 에 겪은 것을 다시 겪지 않기')
    print('')

    print('[PyYAML 함정] `on:` 을 참(True)으로 읽습니다')
    try:
        import yaml
        d = yaml.safe_load('on:\n  push:\n')
        시험('on: 을 어느 꼴로든 읽습니다',
             (True in d) or ('on' in d),
             '둘 다 아니면 검사기의 `on` 판정을 다시 봐야 합니다')
        시험('지금 PyYAML 은 `True` 로 읽습니다 (바뀌면 알려 줍니다)',
             True in d,
             'YAML 1.2 로 바뀐 듯합니다 — check_workflow 를 보세요')
    except ImportError:
        시험('yaml 이 있습니다', False,
             '★ PyYAML 이 없습니다 — 이 시험 묶음은 PyYAML 을 **전제**합니다. '
             '일꾼 설정 넷에 `pip install PyYAML` 단계가 있습니다')

    print('')
    print('[검사가 안 돌았는데 통과로 보이지 않는가]')
    print('  ★ 2026-10-08 배포 #41 — 우분투에 PyYAML 이 없어')
    print('    검사기가 짜임을 **한 줄도 안 보고** 통과를 찍고 있었습니다.')
    시험('PyYAML 이 없으면 **못잼(4)** 을 냅니다 (통과 아님)',
         돌리기(멀쩡한것, yaml없이=True) == 4,
         '통과(0)를 내면 클라우드에서 검사가 죽어도 모릅니다')

    print('')
    print('[막지 말아야 할 것]')
    시험('멀쩡한 워크플로는 통과합니다', 돌리기(멀쩡한것) == 0,
         '★ `True` 키를 안 보면 여기서 걸립니다 — 배포가 통째로 멈춥니다')

    print('')
    print('[막아야 할 것]')
    시험('`on:` 이 없으면 막습니다',
         돌리기(멀쩡한것.replace('on:\n  workflow_dispatch:\n', '')) == 1)
    시험('작업 `env:` 의 `runner` 를 막습니다 (배포를 여섯 번 깨뜨린 줄)',
         돌리기(멀쩡한것.replace(
             '    steps:',
             '    env:\n'
             "      X: ${{ runner.workspace }}/a.json\n"
             '    steps:')) == 1)
    시험('같은 칸을 두 번 적으면 막습니다',
         돌리기(멀쩡한것.replace(
             '    runs-on: ubuntu-latest\n',
             '    runs-on: ubuntu-latest\n    runs-on: 또적음\n')) == 1)
    시험('`runs-on` 이 없으면 막습니다',
         돌리기(멀쩡한것.replace('    runs-on: ubuntu-latest\n', '')) == 1)
    시험('`steps` 가 없으면 막습니다',
         돌리기(멀쩡한것.replace(
             '    steps:\n      - run: echo 1\n', '')) == 1)
    시험('**없는 단계**를 가리키면 막습니다 (빈 값이 됩니다)',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n',
             '      - run: echo ${{ steps.nowhere.outputs.x }}\n')) == 1)
    시험('`needs:` 에 없는 작업을 가리키면 막습니다',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n',
             '      - run: echo ${{ needs.build.outputs.x }}\n')) == 1)
    시험('`run` 도 `uses` 도 없는 단계를 막습니다',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n', '      - name: 빈 단계\n')) == 1)
    # ★ 2026-10-08 — 배포 #40 이 **3초 만에 죽은** 그 줄입니다.
    #   `밭="..."` 를 bash 가 명령으로 읽어 exit 127.
    #   이 저장소는 파이썬 변수를 한글로 쓰는데, **셸만은 다릅니다.**
    시험('셸 변수를 한글로 지으면 막습니다 (배포를 3초 만에 죽인 줄)',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n',
             '      - run: |\n          \ubc2d="/home/x"\n'
             '          echo "$\ubc2d"\n')) == 1)
    시험('파워셸이면 `$한글` 을 통과시킵니다',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n',
             '      - shell: pwsh\n        run: |\n'
             '          $\ubc2d = "C:/x"\n')) == 0)

    print('')
    print('[막으면 안 되는 것]')
    print('  잡는 것이 느는 것과 **맞게 잡는 것**은 다릅니다.')
    시험('단계에 `id` 가 있으면 그 참조를 통과시킵니다',
         돌리기(멀쩡한것.replace(
             '      - run: echo 1\n',
             '      - id: aa\n        run: echo 1\n'
             '      - run: echo ${{ steps.aa.outputs.x }}\n')) == 0)
    시험('`needs:` 에 적힌 작업 참조는 통과시킵니다',
         돌리기('name: 시험\non:\n  workflow_dispatch:\njobs:\n'
                '  a:\n    runs-on: ubuntu-latest\n    steps:\n'
                '      - run: echo 1\n'
                '  b:\n    needs: a\n    runs-on: ubuntu-latest\n'
                '    steps:\n'
                '      - run: echo ${{ needs.a.outputs.x }}\n') == 0)

    print('')
    print('%d가지 통과 · %d가지 어김' % (ok, fail))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
