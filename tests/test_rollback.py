# -*- coding: utf-8 -*-
"""**되돌리기가 진짜 되는지** 봅니다.

★ 왜 이 시험이 필요한가 (2026-09-26 바깥 검수 지적)

    「계약-22 는 실제로 롤백 가능한 상태를 만든 뒤 PASS 시키는 게
      맞습니다. 이전 release 로 전환 → 복구 가 실제로 되는지를
      시험하는 겁니다」

    되돌리는 길을 만들어 두고 한 번도 안 써 보면, 정작 급할 때
    안 됩니다. 사이트가 망가진 그 순간이 **처음 써 보는 때**가
    되어서는 안 됩니다.

    그리고 롤백은 「되돌렸다」는 말이 아니라
    **바이트가 그때와 똑같은가**로 재야 합니다.

무엇을 보나
    1. 판을 봉하면 내용이 그대로 보관되는가
    2. 쪽을 망가뜨린 뒤 되돌리면 **바이트까지** 돌아오는가
    3. 두 판 사이를 오갈 수 있는가 (앞으로도, 뒤로도)
    4. 봉하지 않은 것을 덮어쓰려 하면 막는가
    5. 같은 내용은 판을 두 번 만들지 않는가 (디스크)

어떻게 보나
    진짜 site/ 와 release/ 는 **한 글자도 안 건드립니다.**
    임시 자리에 베껴 거기서 봉하고 되돌립니다.

쓰는 법
    python tests/test_rollback.py
"""
import os
import sys
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

통과, 실패 = 0, []


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s' % 이름)
        if 덧:
            for 줄 in str(덧).split('\n')[-6:]:
                print('      %s' % 줄)


def 돌리기(사이트, 판자리, 인자=()):
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_SITE'] = 사이트
    환경['BADAGAJA_RELEASE'] = 판자리
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'engine', 'release.py')]
        + list(인자),
        capture_output=True, text=True, encoding='utf-8',
        env=환경, timeout=900)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def 지문(뿌리):
    import hashlib
    나옴 = {}
    for r, _, fs in os.walk(뿌리):
        for f in fs:
            p = os.path.join(r, f)
            키 = os.path.relpath(p, 뿌리).replace(os.sep, '/')
            with open(p, 'rb') as fh:
                나옴[키] = hashlib.sha256(fh.read()).hexdigest()
    return 나옴


def 판이름들(글):
    import re
    return re.findall(r'\d{8}-\d{6}-[0-9a-f]{6}', 글)


def main():
    print('되돌리기가 진짜 되는지')
    print('  진짜 site/ 와 release/ 는 안 건드립니다')
    print('')

    t = tempfile.mkdtemp(prefix='rollback-')
    try:
        사이트 = os.path.join(t, 'site')
        판자리 = os.path.join(t, 'release')
        shutil.copytree(os.path.join(ROOT, 'site'), 사이트)

        # ── 1. 판이 없을 때
        print('[1] 판이 없을 때')
        코드, 글 = 돌리기(사이트, 판자리)
        봄('판이 없으면 없다고 말한다', '아직 없습니다' in 글, 글)
        코드, 글 = 돌리기(사이트, 판자리, ('--back',))
        봄('판이 없으면 되돌리기를 막는다',
           코드 != 0 and '봉해 둔 판이 없습니다' in 글, 글)
        print('')

        # ── 2. 첫 판을 봉합니다
        print('[2] 판을 봉하기')
        처음 = 지문(사이트)
        코드, 글 = 돌리기(사이트, 판자리, ('--seal',))
        판A = (판이름들(글) or [None])[0]
        봄('판을 봉한다', 코드 == 0 and bool(판A), 글)
        if not 판A:
            return 1
        봉한것 = 지문(os.path.join(판자리, 판A, 'site'))
        봄('봉한 내용이 지금 쪽과 똑같다', 봉한것 == 처음,
           '파일 %d개 ↔ %d개' % (len(처음), len(봉한것)))

        # 같은 내용은 또 봉하지 않아야 합니다 (디스크)
        코드, 글 = 돌리기(사이트, 판자리, ('--seal',))
        봄('같은 내용은 판을 또 만들지 않는다',
           '똑같은 판이 이미 있습니다' in 글, 글)
        코드, 글 = 돌리기(사이트, 판자리, ('--mark', 판A))
        봄('올라간 판을 적어 둔다', 코드 == 0, 글)
        print('')

        # ── 3. 쪽을 바꾸고 두 번째 판
        print('[3] 쪽을 바꾸고 두 번째 판')
        p = os.path.join(사이트, 'index.html')
        io.write(p, io.read(p).replace('</body>',
                                       '<p>두 번째 판입니다</p></body>'))
        둘째 = 지문(사이트)
        봄('쪽이 실제로 바뀌었다', 둘째 != 처음)
        코드, 글 = 돌리기(사이트, 판자리, ('--seal',))
        판B = [x for x in 판이름들(글) if x != 판A]
        판B = 판B[0] if 판B else None
        봄('두 번째 판을 봉한다', 코드 == 0 and bool(판B), 글)
        if not 판B:
            return 1
        코드, 글 = 돌리기(사이트, 판자리, ('--mark', 판B))
        print('')

        # ── 4. ★ 되돌리기 — 바이트까지 돌아오는가
        print('[4] 되돌리기 — 바이트까지 돌아오는가')
        코드, 글 = 돌리기(사이트, 판자리, ('--back',))
        봄('바로 앞 판으로 되돌린다', 코드 == 0, 글)
        되돌림 = 지문(사이트)
        봄('되돌린 쪽이 첫 판과 **바이트까지** 같다', 되돌림 == 처음,
           '파일 %d개 ↔ %d개 · 다른 파일 %d개'
           % (len(처음), len(되돌림),
              len([k for k in set(처음) | set(되돌림)
                   if 처음.get(k) != 되돌림.get(k)])))
        s = io.read(os.path.join(사이트, 'index.html'), default='')
        봄('두 번째 판에서 넣은 글이 사라졌다', '두 번째 판입니다' not in s)
        print('')

        # ── 5. 앞으로도 갈 수 있는가
        print('[5] 되돌린 뒤 다시 앞으로')
        코드, 글 = 돌리기(사이트, 판자리, ('--back', 판B))
        봄('두 번째 판으로 다시 간다', 코드 == 0, 글)
        다시 = 지문(사이트)
        봄('두 번째 판과 바이트까지 같다', 다시 == 둘째,
           '다른 파일 %d개' % len([k for k in set(둘째) | set(다시)
                                   if 둘째.get(k) != 다시.get(k)]))
        print('')

        # ── 6. 봉하지 않은 것을 덮으려 하면 막는가
        print('[6] 봉하지 않은 것을 지키는가')
        io.write(p, io.read(p).replace('</body>',
                                       '<p>아직 안 봉한 것</p></body>'))
        코드, 글 = 돌리기(사이트, 판자리, ('--back', 판A))
        봄('안 봉한 것이 있으면 되돌리기를 막는다',
           코드 != 0 and '먼저 --seal' in 글, 글)
        s = io.read(p, default='')
        봄('막았으니 안 봉한 것이 그대로 있다', '아직 안 봉한 것' in s)
        코드, 글 = 돌리기(사이트, 판자리, ('--back', 판A, '--force'))
        봄('--force 를 붙이면 되돌린다', 코드 == 0, 글)
        봄('force 로 되돌린 것도 첫 판과 같다', 지문(사이트) == 처음)
        print('')

        # ── 7. 없는 판을 달라고 하면
        print('[7] 없는 판')
        코드, 글 = 돌리기(사이트, 판자리, ('--back', '19700101-0000-abcdef'))
        봄('없는 판은 막는다', 코드 != 0 and '그런 판이 없습니다' in 글, 글)
        print('')

        # ── 8. 솎기는 물어보는가 (계약-17)
        print('[8] 지우기는 어려워야 한다 (계약-17)')
        코드, 글 = 돌리기(사이트, 판자리, ('--prune',))
        봄('--yes 없이는 안 지운다',
           '지울 판이 없습니다' in 글 or '--yes 를 붙이세요' in 글, 글)
        봄('솎은 뒤에도 판이 남아 있다', len(os.listdir(판자리)) >= 2)

    finally:
        shutil.rmtree(t, ignore_errors=True)

    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  되돌리는 길을 만들어 두고 안 써 보면 급할 때 안 됩니다.')
        return 1
    print('%d가지 모두 통과 — 되돌리기가 실제로 됩니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
