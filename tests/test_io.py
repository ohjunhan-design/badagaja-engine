# -*- coding: utf-8 -*-
"""io.write() 가 지난 사고를 정말로 막는지 시험합니다.

이 시험들은 **실제로 일어났던 일**을 그대로 재현합니다.
통과하지 못하면 같은 사고가 또 납니다.

  python tests/test_io.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import io   # noqa: E402

ok, fail = 0, 0


def 시험(이름, 조건, 설명=''):
    global ok, fail
    if 조건:
        ok += 1
        print('  · %s' % 이름)
    else:
        fail += 1
        print('  ✗ %s   %s' % (이름, 설명))


def main():
    tmp = tempfile.mkdtemp(prefix='badagaja-')
    print('io.write() 시험 — 지난 사고를 다시 겪지 않기 위해')
    print('')

    # ── 계약-13 · 제어문자 ────────────────────────────────────
    print('[계약-13] 보이지 않는 글자')
    p = os.path.join(tmp, 'deploy.yml')
    막혔나 = False
    try:
        # 실제 사고: sed 의 역참조 \1 을 쓰려다 진짜 제어문자가 들어갔고,
        # 깃허브가 파일을 못 읽어 배포가 하루 멈췄습니다.
        io.write(p, "run: sed 's|a|\x01/|'\n")
    except io.파일오류:
        막혔나 = True
    시험('제어문자가 든 파일은 쓰지 못한다', 막혔나,
         '← 이것을 못 막으면 배포가 또 하루 멈춥니다')
    시험('막혔으면 파일이 생기지도 않는다', not os.path.exists(p))

    # ── BOM ────────────────────────────────────────────────
    print('')
    print('[계약-13] BOM')
    p = os.path.join(tmp, '.htaccess')
    io.write(p, 'RewriteEngine On\n')
    with open(p, 'rb') as f:
        첫바이트 = f.read(3)
    시험('.htaccess 에 BOM 이 붙지 않는다', 첫바이트 != b'\xef\xbb\xbf',
         '← 붙으면 사이트 전체가 500 오류로 죽습니다')

    p2 = os.path.join(tmp, 'build.ps1')
    io.write(p2, '"한글이 깨지지 않아야 합니다"\n')
    with open(p2, 'rb') as f:
        시험('.ps1 에는 BOM 이 붙는다', f.read(3) == b'\xef\xbb\xbf',
             '← 없으면 PowerShell 에서 한글이 깨집니다')

    # BOM 이 이미 붙은 글을 넣어도 .htaccess 에는 안 붙어야 합니다
    p3 = os.path.join(tmp, 'robots.txt')
    io.write(p3, '﻿User-agent: *\n')
    with open(p3, 'rb') as f:
        시험('넣은 글에 BOM 이 있어도 떼어 낸다', f.read(3) != b'\xef\xbb\xbf')

    # ── 계약-07 · 되풀이해도 같은 결과 ──────────────────────────
    print('')
    print('[계약-07] 두 번 써도 같은 결과')
    p = os.path.join(tmp, 'data.json')
    io.write_json(p, {'나중': 2, '먼저': 1, '가운데': 3})
    첫판 = io.sha(p)
    io.write_json(p, {'가운데': 3, '먼저': 1, '나중': 2})   # 차례만 바꿈
    시험('열쇠 차례가 달라도 결과가 같다', io.sha(p) == 첫판,
         '← 다르면 돌릴 때마다 파일이 바뀐 것으로 잡힙니다')

    # ── 줄바꿈 ─────────────────────────────────────────────
    print('')
    print('[줄바꿈] 통일')
    p = os.path.join(tmp, 'a.html')
    io.write(p, '<p>가</p>\r\n<p>나</p>\r\n')
    with open(p, 'rb') as f:
        시험('\\r\\n 을 \\n 으로 맞춘다', b'\r' not in f.read())

    # ── 한글 경로 ───────────────────────────────────────────
    print('')
    print('[한글 경로]')
    p = os.path.join(tmp, '권역', '태안.html')
    io.write(p, '<h1>태안</h1>')
    시험('한글 폴더·파일 이름이 된다', io.read(p) == '<h1>태안</h1>')

    # ── scan ──────────────────────────────────────────────
    print('')
    print('[배포 전 마지막 확인]')
    시험('만든 파일에 탈이 없다', io.scan(tmp) == [])
    # 일부러 나쁜 파일을 직접 써 넣습니다 (write 를 안 거친 경우)
    나쁜파일 = os.path.join(tmp, 'bad.yml')
    with open(나쁜파일, 'w', encoding='utf-8', newline='') as f:
        f.write('name: \x01 나쁨\n')
    시험('직접 쓴 나쁜 파일은 scan 이 잡는다', len(io.scan(tmp)) >= 1,
         '← write() 를 안 거친 파일도 배포 전에 걸러야 합니다')

    print('')
    print('통과 %d · 실패 %d' % (ok, fail))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
