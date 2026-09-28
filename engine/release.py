# -*- coding: utf-8 -*-
"""만든 쪽을 **판으로 봉해 두고, 언제든 되돌립니다.**

★ 왜 이것이 따로 필요한가 (2026-09-26 바깥 검수 지적)

    「원격 Git = 소스코드 복구 · 배포 릴리스 보관 = 실제 사이트 롤백
      이라서 둘은 같은 것이 아닙니다. 둘 다 갖추는 게 좋습니다」

    맞는 말입니다. 그동안 계약-22(되돌릴 수 있어야 배포한다)를
    「원격 창고가 없으니 못 잰다」고만 적어 두었는데, 그 둘은
    다른 일이었습니다.

        원격 Git      내 컴퓨터가 고장 나도 **소스**를 되찾습니다
        판 보관       사이트가 망가지면 **손님이 보는 쪽**을 되돌립니다

    소스가 멀쩡해도 되돌리는 데는 시간이 걸립니다. 다시 만들고,
    검사하고, 올려야 합니다. 그 사이 손님은 망가진 쪽을 봅니다.
    이미 만들어 둔 판이 있으면 **올리기만 하면 끝납니다.**

어떻게 두나
    release/
      _index.json                판 목록 · 지금 서버에 올라간 판
      20260926-1430-a1b2c3/
          site/                  그때의 쪽 전부
          _판.json               만든 때 · 커밋 · 쪽 수 · 지문

쓰는 법
    python engine/release.py                    판 목록을 봅니다
    python engine/release.py --seal             지금 site/ 를 판으로 봉합니다
    python engine/release.py --mark <판>        그 판이 서버에 올라갔다고 적습니다
    python engine/release.py --back             바로 앞 판으로 되돌립니다
    python engine/release.py --back <판>        그 판으로 되돌립니다
    python engine/release.py --prune            오래된 판을 지웁니다 (물어봅니다)

★ 되돌리기는 site/ 를 그 판의 내용으로 **되돌려 놓는 것**입니다.
    올리는 일은 따로입니다 — 그래야 올리기 전에 눈으로 볼 수 있습니다.

★ 디스크를 조심합니다 (2026-09-24 사고)
    제가 만든 검사 결과물이 19.7GB 까지 불어 디스크를 꽉 채운 적이
    있습니다. 판 하나가 7MB 남짓이라 괜찮지만, 그래도 몇 개까지
    둘지 정해 두고 넘으면 알립니다.
"""
import os
import re
import sys
import json
import time
import shutil
import hashlib
import datetime
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
RELEASE = os.environ.get('BADAGAJA_RELEASE', os.path.join(ROOT, 'release'))

# 판을 몇 개까지 둘지. 넘으면 알립니다 (지우지는 않습니다 — 계약-17)
둘판수 = 10

# ★ 초까지 넣습니다 (2026-09-26 tests/test_rollback.py 가 잡음)
#   처음에는 분까지만 넣었더니, 같은 분에 두 판이 생기면 이름 차례가
#   **지문 글자**에 좌우됐습니다. 「바로 앞 판」이 엉뚱한 것을 가리켜
#   되돌리기가 안 됐습니다. 급할 때 안 되는 되돌리기는 없는 것입니다.
판이름꼴 = re.compile(r'^\d{8}-\d{6}-[0-9a-f]{6}$')
# 초가 없던 옛 판도 읽을 수 있어야 합니다
옛판이름꼴 = re.compile(r'^\d{8}-\d{4}-[0-9a-f]{6}$')


def _색인길():
    return os.path.join(RELEASE, '_index.json')


def 색인():
    return io.read_json(_색인길(), default={'판': [], '올라간판': None})


def 판들():
    """있는 판을 **새것부터**.

    ★ 이름이 아니라 **만든 때**로 줄 세웁니다
        이름으로 세우면 같은 시각에 봉한 두 판의 차례가 지문 글자에
        좌우됩니다. 그러면 「바로 앞 판」이 엉뚱한 것을 가리킵니다.
        만든 때를 못 읽으면 그때만 이름을 씁니다.
    """
    if not os.path.isdir(RELEASE):
        return []
    나옴 = []
    for x in os.listdir(RELEASE):
        if not (판이름꼴.match(x) or 옛판이름꼴.match(x)):
            continue
        if not os.path.isdir(os.path.join(RELEASE, x)):
            continue
        m = io.read_json(os.path.join(RELEASE, x, '_판.json'), default={})
        나옴.append((m.get('만든때') or '', x))
    나옴.sort(reverse=True)
    return [x for _, x in 나옴]


def 지문(뿌리):
    """그 자리 밑 모든 파일의 내용 지문"""
    나옴 = {}
    for r, _, fs in os.walk(뿌리):
        for f in fs:
            p = os.path.join(r, f)
            키 = os.path.relpath(p, 뿌리).replace(os.sep, '/')
            with open(p, 'rb') as fh:
                나옴[키] = hashlib.sha256(fh.read()).hexdigest()
    return 나옴


def 통지문(뿌리):
    """자리 전체를 한 줄로 — 두 판이 같은지 한눈에 봅니다"""
    것 = 지문(뿌리)
    h = hashlib.sha256()
    for k in sorted(것):
        h.update(('%s %s\n' % (k, 것[k])).encode('utf-8'))
    return h.hexdigest()


def 지금커밋():
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=30)
        if r.returncode == 0:
            return (r.stdout or '').strip()
    except OSError:
        pass
    return None


def 깨끗한가():
    """안 커밋한 것이 있는지. 있으면 되돌아갈 자리가 흐려집니다"""
    try:
        r = subprocess.run(['git', 'status', '--porcelain'],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=30)
        if r.returncode == 0:
            return not (r.stdout or '').strip()
    except OSError:
        pass
    return None


def 베끼기(from_, to):
    """파일을 그대로 옮깁니다. 글이든 그림이든 바이트 그대로."""
    for r, _, fs in os.walk(from_):
        for f in fs:
            p = os.path.join(r, f)
            상대 = os.path.relpath(p, from_)
            io.copy_binary(p, os.path.join(to, 상대))


def 봉하기():
    if not os.path.isdir(NEW):
        print('만들어진 쪽이 없습니다: %s' % NEW)
        return 1
    쪽수 = sum(1 for r, _, fs in os.walk(NEW) for f in fs
               if f.endswith('.html'))
    if not 쪽수:
        print('쪽이 하나도 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    통 = 통지문(NEW)
    이제 = datetime.datetime.now()
    이름 = '%s-%s' % (이제.strftime('%Y%m%d-%H%M%S'), 통[:6])
    자리 = os.path.join(RELEASE, 이름)

    # 같은 내용이면 또 봉하지 않습니다 — 디스크가 헛되이 찹니다
    기존 = 판들()
    for x in 기존:
        메모 = io.read_json(os.path.join(RELEASE, x, '_판.json'), default={})
        if 메모.get('통지문') == 통:
            print('내용이 똑같은 판이 이미 있습니다: %s' % x)
            print('  새로 봉하지 않았습니다. 자료가 안 바뀐 것입니다.')
            return 0

    print('지금 쪽을 판으로 봉합니다')
    print('  판 이름: %s' % 이름)
    print('  쪽 %d개' % 쪽수)

    깨끗 = 깨끗한가()
    if 깨끗 is False:
        print('  ~ 안 커밋한 것이 있습니다 — 되돌아갈 자리가 흐려집니다')

    베끼기(NEW, os.path.join(자리, 'site'))
    io.write_json(os.path.join(자리, '_판.json'), {
        '이름': 이름,
        '만든때': 이제.strftime('%Y-%m-%d %H:%M:%S'),
        '커밋': 지금커밋(),
        '커밋깨끗': 깨끗,
        '쪽수': 쪽수,
        '통지문': 통,
        '파일수': sum(len(fs) for _, _, fs in os.walk(NEW)),
    })

    c = 색인()
    c['판'] = [이름] + [x for x in c.get('판', []) if x != 이름]
    io.write_json(_색인길(), c)

    print('  봉했습니다: release/%s/' % 이름)
    모두 = 판들()
    if len(모두) > 둘판수:
        print('')
        print('  ~ 판이 %d개입니다 (정해 둔 것은 %d개)' % (len(모두), 둘판수))
        print('    오래된 것을 지우려면: python engine/release.py --prune')
    return 0


def 되돌리기(어느것=None):
    모두 = 판들()
    if not 모두:
        print('봉해 둔 판이 없습니다. 먼저 --seal 하세요.')
        return 1

    if 어느것:
        if 어느것 not in 모두:
            print('그런 판이 없습니다: %s' % 어느것)
            print('  있는 판: %s' % ' · '.join(모두[:5]))
            return 1
        갈곳 = 어느것
    else:
        c = 색인()
        올라간 = c.get('올라간판')
        # 지금 올라간 판의 **바로 앞**으로
        차례 = 모두
        if 올라간 and 올라간 in 차례:
            i = 차례.index(올라간)
            if i + 1 >= len(차례):
                print('더 앞선 판이 없습니다 (지금 올라간 판: %s)' % 올라간)
                return 1
            갈곳 = 차례[i + 1]
        else:
            if len(차례) < 2:
                print('판이 하나뿐이라 되돌릴 곳이 없습니다.')
                return 1
            갈곳 = 차례[1]

    메모 = io.read_json(os.path.join(RELEASE, 갈곳, '_판.json'), default={})
    print('그 판으로 되돌립니다')
    print('  판       %s' % 갈곳)
    print('  만든때   %s' % 메모.get('만든때', '?'))
    print('  쪽       %s개' % 메모.get('쪽수', '?'))
    print('  커밋     %s' % (메모.get('커밋') or '(없음)'))
    print('')

    바탕 = os.path.join(RELEASE, 갈곳, 'site')
    if not os.path.isdir(바탕):
        print('그 판에 site/ 가 없습니다 — 판이 깨졌습니다.')
        return 1

    # 지금 site/ 를 지우고 그 판으로 채웁니다.
    # 되돌리기 전의 것도 판으로 남아 있어야 다시 앞으로 갈 수 있습니다.
    통 = 통지문(NEW) if os.path.isdir(NEW) else None
    있던판 = None
    for x in 판들():
        m = io.read_json(os.path.join(RELEASE, x, '_판.json'), default={})
        if 통 and m.get('통지문') == 통:
            있던판 = x
            break
    if 통 and not 있던판:
        print('  ~ 지금 site/ 가 어느 판과도 다릅니다.')
        print('    되돌리면 지금 것은 사라집니다. 먼저 --seal 하세요.')
        if '--force' not in sys.argv:
            print('    그래도 하려면 --force 를 붙이세요.')
            return 1

    if os.path.isdir(NEW):
        shutil.rmtree(NEW)
    베끼기(바탕, NEW)

    확인 = 통지문(NEW)
    맞나 = 확인 == 메모.get('통지문')
    print('  site/ 를 그 판으로 되돌렸습니다')
    print('  %s 되돌린 내용이 판과 %s'
          % ('·' if 맞나 else '✗', '똑같습니다' if 맞나 else '다릅니다'))
    if not 맞나:
        print('    판이 깨졌거나 베끼다 탈이 났습니다. 사람이 봐야 합니다.')
        return 1

    c = 색인()
    c['되돌린기록'] = (c.get('되돌린기록') or [])[:19]
    c['되돌린기록'].insert(0, {
        '때': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '판': 갈곳,
    })
    io.write_json(_색인길(), c)
    print('')
    print('  이제 올리면 됩니다. 올린 뒤에는 적어 두세요:')
    print('    python engine/release.py --mark %s' % 갈곳)
    return 0


def 올림표시(이름):
    모두 = 판들()
    if 이름 not in 모두:
        print('그런 판이 없습니다: %s' % 이름)
        return 1
    c = 색인()
    c['올라간판'] = 이름
    c['올린때'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    io.write_json(_색인길(), c)
    print('서버에 올라간 판을 %s 로 적었습니다.' % 이름)
    return 0


def 솎기():
    모두 = 판들()
    c = 색인()
    지킬것 = set(모두[:둘판수])
    if c.get('올라간판'):
        지킬것.add(c['올라간판'])
    지울것 = [x for x in 모두 if x not in 지킬것]
    if not 지울것:
        print('지울 판이 없습니다 (판 %d개 · 두기로 한 것 %d개)'
              % (len(모두), 둘판수))
        return 0
    print('오래된 판 %d개를 지웁니다' % len(지울것))
    for x in 지울것:
        print('    %s' % x)
    print('')
    print('★ 지우면 그 판으로는 되돌릴 수 없습니다 (계약-17)')
    if '--yes' not in sys.argv:
        print('  정말 지우려면 --yes 를 붙이세요.')
        return 0
    for x in 지울것:
        shutil.rmtree(os.path.join(RELEASE, x), ignore_errors=True)
    c['판'] = [x for x in c.get('판', []) if x not in 지울것]
    io.write_json(_색인길(), c)
    print('지웠습니다. 남은 판 %d개' % len(판들()))
    return 0


def 보여주기():
    모두 = 판들()
    c = 색인()
    올라간 = c.get('올라간판')
    print('봉해 둔 판')
    print('  자리: %s' % RELEASE)
    print('')
    if not 모두:
        print('  아직 없습니다. python engine/release.py --seal 로 봉하세요.')
        print('')
        print('  ★ 판이 없으면 사이트가 망가졌을 때 되돌릴 것이 없습니다.')
        return 0
    print('      판                       만든때              쪽    커밋')
    for x in 모두:
        m = io.read_json(os.path.join(RELEASE, x, '_판.json'), default={})
        표 = '◀ 올라감' if x == 올라간 else ''
        print('      %-24s %-19s %4s  %-8s %s'
              % (x, m.get('만든때', '?'), m.get('쪽수', '?'),
                 m.get('커밋') or '-', 표))
    print('')
    if not 올라간:
        print('  ~ 어느 판이 서버에 올라가 있는지 안 적혀 있습니다.')
        print('    올린 뒤 --mark <판> 으로 적어 두세요.')
    되돌림 = c.get('되돌린기록') or []
    if 되돌림:
        print('  되돌린 기록')
        for x in 되돌림[:3]:
            print('      %s → %s' % (x['때'], x['판']))
    return 0


def main():
    if '--seal' in sys.argv:
        return 봉하기()
    if '--back' in sys.argv:
        i = sys.argv.index('--back')
        어느것 = None
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
            어느것 = sys.argv[i + 1]
        return 되돌리기(어느것)
    if '--mark' in sys.argv:
        i = sys.argv.index('--mark')
        if i + 1 >= len(sys.argv):
            print('어느 판인지 적어 주세요: --mark <판>')
            return 1
        return 올림표시(sys.argv[i + 1])
    if '--prune' in sys.argv:
        return 솎기()
    return 보여주기()


if __name__ == '__main__':
    sys.exit(main())
