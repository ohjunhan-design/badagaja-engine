# -*- coding: utf-8 -*-
"""바깥 꾸러미 — **없을 때 조용히 통과하지 않는가** (계약-24)

★ 왜 이 검사가 있나 (2026-10-09)

  이틀에 **두 번** 같은 함정에 빠졌습니다.

  · 2026-10-08 `PyYAML` — 제 윈도우에는 있어서 짜임 검사가 다
    통과했는데, 우분투 일꾼에는 없어서 `check_workflow` 가
    **한 줄도 안 보고 통과**했습니다.
  · 2026-10-09 `Pillow` — 일꾼이 PyYAML 만 깔아서 `그림크기()` 가
    모두 (0,0) 을 돌려주고, 사진의 width/height 속성이 **조용히**
    빠졌습니다. 서버에 올라간 **38쪽**에서 사진이 뜰 때 쪽이
    흔들렸습니다(CLS). 배포는 성공이라고 했습니다.

  두 번 다 뿌리가 같습니다 — **`try: import … except: 넘어가기`**.
  그래서 이제 기계가 봅니다.

★ 세 가지를 봅니다

  1. 바깥 꾸러미를 쓰는 파일마다 **없을 때 멈추는가**
     (`mustmeasure.꾸러미가있어야한다` 를 부르는가)
  2. 그 꾸러미가 **일꾼 설정의 깔기 단계에 있는가**
  3. 정말 멈추는가 — **가짜 모듈로 가려 보고 끝난값을 봅니다**
     (짜임만 보면 부르는 척하고 안 멈출 수 있습니다)

  3번이 없으면 1번은 흉내입니다 (기억 「뮤테이션은 정말 망가뜨려야」).
"""
import ast
import io
import os
import re
import subprocess
import sys
import tempfile

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
sys.path.insert(0, 여기)

import mustmeasure   # noqa: E402

막음, 알림 = [], []        # 계약-21 — 모듈 수준에 둡니다

# 파이썬에 딸려 오지 않는 꾸러미 — 가져오기 이름 → 깔 이름
바깥것 = {
    'PIL': 'Pillow',
    'yaml': 'PyYAML',
    'requests': 'requests',
    'bs4': 'beautifulsoup4',
    'lxml': 'lxml',
    'numpy': 'numpy',
}

# 검사기가 아니라 **손으로 쓸 때만 돌리는 것** — 일꾼이 안 돌립니다.
# 그래도 멈추는 편이 낫지만, 배포를 막지는 않습니다(알림).
손으로만 = ('shot_', 'import_', 'adopt_', 'make_', 'fetch_', 'gen_')


def _쓰는곳():
    """바깥 꾸러미를 가져오는 `engine/*.py` 를 찾습니다."""
    것들 = {}
    for 이름 in sorted(os.listdir(여기)):
        if not 이름.endswith('.py'):
            continue
        길 = os.path.join(여기, 이름)
        글 = io.open(길, encoding='utf-8').read()
        try:
            나무 = ast.parse(글)
        except SyntaxError:
            알림.append('%s — 짜임을 못 읽었습니다' % 이름)
            continue
        쓴것 = set()
        for 가지 in ast.walk(나무):
            if isinstance(가지, ast.Import):
                for a in 가지.names:
                    뿌리이름 = a.name.split('.')[0]
                    if 뿌리이름 in 바깥것:
                        쓴것.add(뿌리이름)
            elif isinstance(가지, ast.ImportFrom) and 가지.module:
                뿌리이름 = 가지.module.split('.')[0]
                if 뿌리이름 in 바깥것:
                    쓴것.add(뿌리이름)
        if 쓴것:
            것들[이름] = (쓴것, 글)
    return 것들


def _일꾼이깔것():
    """일꾼 설정의 깔기 단계에 적힌 꾸러미 이름."""
    깔것 = {}
    설정뿌리 = os.path.join(뿌리, '.github', 'workflows')
    if not os.path.isdir(설정뿌리):
        return 깔것
    for 이름 in sorted(os.listdir(설정뿌리)):
        if not 이름.endswith('.yml'):
            continue
        글 = io.open(os.path.join(설정뿌리, 이름), encoding='utf-8').read()
        모은것 = set()
        for m in re.finditer(r'pip install([^\n]*)', 글):
            꼬리 = m.group(1)
            for 낱말 in 꼬리.split():
                if 낱말.startswith('-'):
                    continue
                모은것.add(낱말)
        깔것[이름] = 모은것
    return 깔것


맞는인자 = {'build.py': ['--only', 'index']}


def _정말멈추나(파일, 꾸러미, 참을시간=240):
    """가짜 모듈로 가려 보고 **끝난값 4** 가 나오는지 봅니다."""
    with tempfile.TemporaryDirectory() as 가짜:
        io.open(os.path.join(가짜, 꾸러미 + '.py'), 'w',
                encoding='utf-8').write('raise ImportError("가려 봅니다")\n')
        터 = dict(os.environ)
        터['PYTHONPATH'] = 가짜
        터['PYTHONIOENCODING'] = 'utf-8'
        try:
            끝 = subprocess.run(
                [sys.executable, '-X', 'utf8',
                 os.path.join(여기, 파일)]
                + 맞는인자.get(파일, []),
                cwd=뿌리, env=터, timeout=참을시간,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode
        except subprocess.TimeoutExpired:
            return None
    return 끝


def main():
    것들 = _쓰는곳()
    mustmeasure.있어야한다(
        것들, '바깥 꾸러미를 쓰는 파일', 최소=2, 어디='engine/*.py')

    깔것 = _일꾼이깔것()
    mustmeasure.있어야한다(
        깔것, '일꾼 설정', 최소=3, 어디='.github/workflows/*.yml')

    print()
    print('  바깥 꾸러미를 쓰는 곳 %d개' % len(것들))
    print()

    # ── 1. 일꾼이 깔고 있는가
    쓰는꾸러미 = set()
    for 쓴것, _ in 것들.values():
        쓰는꾸러미 |= 쓴것

    for 꾸 in sorted(쓰는꾸러미):
        깔이름 = 바깥것[꾸]
        없는데 = [이름 for 이름, 모은것 in 깔것.items()
                  if 모은것 and 깔이름 not in 모은것]
        if 없는데:
            막음.append('`%s` 를 안 깔는 일꾼 설정 %d개 — %s'
                        % (깔이름, len(없는데), ' · '.join(sorted(없는데))))
            print('  X %-14s 일꾼 %d개가 안 깝니다'
                  % (깔이름, len(없는데)))
        else:
            print('  O %-14s 일꾼이 모두 깝니다' % 깔이름)

    # ── 2·3. 없을 때 멈추는가 (짜임 + 실측)
    print()
    재본것 = []
    for 이름, (쓴것, 글) in sorted(것들.items()):
        if 이름.startswith('check_deps'):
            continue
        # * **짜임이 아니라 실측이 증거입니다** (2026-10-09)
        #   「`꾸러미가있어야한다` 를 부르는가」로 쟀더니
        #   `check_workflow.py` 를 잘못 잡았습니다 - 그 파일은 손으로
        #   쓴 방식으로 제대로 4를 돌려줍니다. 부르는 법은 여럿이고,
        #   **정말 멈추는가**만이 뜻이 있습니다.
        손것 = 이름.startswith(손으로만)
        꾸 = sorted(쓴것)[0]
        # 손으로만 쓰는 것은 **짧게 끊습니다** (2026-10-09)
        #   안 멈추면 끝까지 도는데(그림을 통째로 다시 만들기도
        #   합니다) 어차피 막지 않고 알림만 냅니다. 판정이 한참
        #   길어지는 것이 더 나쁩니다.
        끝 = _정말멈추나(이름, 꾸, 참을시간=20 if 손것 else 240)
        재본것.append(이름)
        if 끝 is None:
            알림.append('%s - 가려 보니 시간이 넘었습니다%s'
                        % (이름, ' · 손으로만 돌리는 것' if 손것 else ''))
            print('  ~ %-26s 시간 넘음' % 이름)
        elif 끝 == 4:
            print('  O %-26s %s 를 가리면 못잼(4)' % (이름, 바깥것[꾸]))
        else:
            말 = ('%s - `%s` 를 가렸는데 끝난값이 %d 입니다 '
                  '(못잼 4 여야 합니다)' % (이름, 바깥것[꾸], 끝))
            if 손것:
                알림.append(말 + ' · 손으로만 돌리는 것')
                print('  ~ %-26s 끝난값 %d (손으로만)' % (이름, 끝))
            else:
                막음.append(말)
                print('  X %-26s 가렸는데 끝난값 %d' % (이름, 끝))

    mustmeasure.있어야한다(
        재본것, '정말 멈추는지 재 본 파일', 최소=2, 어디='engine/*.py')

    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('    X ' + x)
    if 알림:
        print('  알림 %d가지' % len(알림))
        for x in 알림:
            print('    ~ ' + x)
    if not 막음:
        print('  · 바깥 꾸러미가 없으면 모두 멈춥니다')
    print()
    print('  * 「내 컴퓨터에 있으니 괜찮다」가 두 번 저를 속였습니다 —')
    print('    PyYAML(10-08) · Pillow(10-09). 일꾼에는 없습니다.')
    return 1 if 막음 else 0


if __name__ == '__main__':
    sys.exit(main())
