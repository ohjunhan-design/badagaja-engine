# -*- coding: utf-8 -*-
"""판 견주기와 되돌림 계획을 잽니다 (2026-10-08).

★ 이것은 **지우는 계획을 세우는 코드**입니다. 틀리면 손님이 보는
  쪽이 사라집니다. 그래서 쓰기 전에 시험부터 씁니다.

★ 특히 꼭 재야 하는 것
  · 목록을 못 읽었을 때 **아무것도 안 지우는가** (빈 목록과 구별)
  · `api/` · 중국어판 · `.htaccess` 를 **건드리지 않는가**
  · 지울 것이 지나치게 많으면 **멈추는가**
"""
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import release as R   # noqa: E402

실패 = []


def 봄(이름, 참인가, 덧=''):
    if 참인가:
        print('  · %s' % 이름)
    else:
        print('  ✗ %s' % 이름)
        if 덧:
            print('      %s' % 덧)
        실패.append(이름)


def 시험_판읽기():
    print('[1] build.json 읽기')
    파일, 판 = R.판읽기('{"파일":{"a.html":"11","b.css":"22"},'
                        '"판번호":"abc"}')
    봄('제대로 읽습니다', 파일 == {'a.html': '11', 'b.css': '22'}
       and 판 == 'abc', '%s %s' % (파일, 판))

    for 글, 왜 in (('', '빈 글'), ('{', '깨진 JSON'),
                   ('{"파일":[]}', '파일이 목록이 아님'),
                   ('{}', '파일 칸이 없음'), (None, 'None')):
        파일, 판 = R.판읽기(글)
        봄('못 읽으면 None 입니다 (%s)' % 왜, 파일 is None, repr(파일))


def 시험_견주기():
    print('[2] 두 판 견주기')
    옛 = {'그대로.html': 'aa', '바뀐.html': 'bb', '사라진.html': 'cc'}
    새 = {'그대로.html': 'aa', '바뀐.html': 'XX', '생긴.html': 'dd'}
    d = R.견주기(옛, 새)
    봄('생긴 것', d['생김'] == ['생긴.html'], d['생김'])
    봄('사라진 것', d['사라짐'] == ['사라진.html'], d['사라짐'])
    봄('바뀐 것', d['바뀜'] == ['바뀐.html'], d['바뀜'])
    봄('그대로인 것', d['그대로'] == ['그대로.html'], d['그대로'])

    # ★ 차례가 정해져 있어야 두 번 돌려도 같습니다
    많음 = dict(('%03d.html' % i, str(i)) for i in range(50))
    a = R.견주기({}, 많음)['생김']
    b = R.견주기({}, dict(reversed(list(많음.items()))))['생김']
    봄('차례가 정해져 있습니다', a == b == sorted(많음))


def 시험_건드리면안될것():
    print('[3] 건드리면 안 되는 것')
    for 길 in ('.htaccess', 'api/marine.php', 'zh-cn/index.html',
               '.well-known/x.txt', 'favicon.ico', '/api/a.php'):
        봄('지킵니다 — %s' % 길, R.건드리면안되나(길))
    for 길 in ('index.html', 'assets/css/site.css',
               'point/13_yeosu_fishing.html', 'apixyz.html'):
        봄('보통 파일은 아닙니다 — %s' % 길, not R.건드리면안되나(길))


def 시험_되돌림계획():
    print('[4] 되돌림 계획')
    옛 = {'a.html': '1', 'b.html': '2', 'api/x.php': '9'}
    새 = {'a.html': '1', 'b.html': 'CHANGED', 'c.html': '3',
          'api/x.php': 'SERVER-CHANGED', 'zh-cn/z.html': 'z'}
    계획 = R.되돌림계획(옛, 새)
    봄('이번 판에만 생긴 것만 지웁니다',
       계획['지울것'] == ['c.html'], 계획['지울것'])
    봄('바뀐 것은 되돌립니다',
       계획['되돌릴것'] == ['b.html'], 계획['되돌릴것'])
    봄('api/ 는 지우지도 되돌리지도 않습니다',
       'api/x.php' not in 계획['지울것']
       and 'api/x.php' not in 계획['되돌릴것'])
    봄('중국어판도 안 건드립니다',
       'zh-cn/z.html' not in 계획['지울것'])

    # 사라진 것도 되돌립니다
    계획2 = R.되돌림계획({'사라진.html': '1'}, {})
    봄('사라진 것은 되돌립니다',
       계획2['되돌릴것'] == ['사라진.html'], 계획2['되돌릴것'])


def 시험_모르면안지움():
    print('[5] 모르면 아무것도 안 지웁니다')
    #   ★ 이것이 가장 중요합니다. 목록을 못 읽었는데 빈 목록으로
    #     셈하면 「전부 지워라」가 나옵니다.
    for 옛, 새, 왜 in ((None, {'a': '1'}, '지난 판을 모름'),
                       ({'a': '1'}, None, '이번 판을 모름'),
                       (None, None, '둘 다 모름')):
        계획 = R.되돌림계획(옛, 새)
        봄('안 지웁니다 (%s)' % 왜,
           계획['지울것'] == [] and 계획['되돌릴것'] == []
           and 계획['막힘'], 계획)


def 시험_위험한가():
    print('[6] 너무 많이 지우려 하면 멈춥니다')
    적당 = R.되돌림계획(dict(('%d.html' % i, '1') for i in range(100)),
                        dict(('%d.html' % i, '1') for i in range(105)))
    봄('조금 지우는 것은 괜찮습니다',
       R.위험한가(적당, 모두=105) is None, R.위험한가(적당, 모두=105))

    많이 = R.되돌림계획({'a.html': '1'},
                        dict(('%d.html' % i, '1') for i in range(100)))
    봄('절반 넘게 지우려 하면 멈춥니다',
       R.위험한가(많이, 모두=100) is not None)

    막힘 = R.되돌림계획(None, {'a': '1'})
    봄('못 읽은 것도 멈춤 사유입니다',
       R.위험한가(막힘, 모두=1) is not None)


def 시험_실제판():
    print('[7] 실제 build.json 으로')
    길 = os.path.join(여기, 'site', 'build.json')
    if not os.path.isfile(길):
        print('  □ site/build.json 이 없습니다 — 먼저 build.py')
        return
    import io
    파일, 판 = R.판읽기(io.open(길, encoding='utf-8').read())
    봄('읽힙니다', 파일 is not None and len(파일) > 100,
       len(파일 or {}))
    # 같은 판끼리 견주면 지울 것도 되돌릴 것도 없어야 합니다
    계획 = R.되돌림계획(파일, 파일)
    봄('같은 판끼리는 아무 일도 없습니다',
       계획['지울것'] == [] and 계획['되돌릴것'] == [], 계획)
    봄('위험하지 않습니다',
       R.위험한가(계획, 모두=len(파일)) is None)


def 시험_lftp명령():
    print('[8] 지우는 명령 만들기')
    줄들, 뺀것 = R.lftp지우기(['a.html', 'sub/b.css'])
    봄('보통 파일은 명령이 됩니다',
       줄들 == ['rm -f "/www/a.html";', 'rm -f "/www/sub/b.css";'], 줄들)
    봄('뺀 것이 없습니다', 뺀것 == [], 뺀것)

    # ★ **따옴표가 든 경로는 뺍니다** — 명령이 깨져 엉뚱한 것을
    #   지우느니 안 지우는 편이 낫습니다
    줄들, 뺀것 = R.lftp지우기(['괜찮.html', 'bad".html', "bad'.html",
                               'bad\nnewline.html', 'back\\slash.html'])
    봄('따옴표·줄바꿈이 든 경로는 뺍니다',
       줄들 == ['rm -f "/www/괜찮.html";'] and len(뺀것) == 4,
       '%s / %s' % (줄들, 뺀것))

    # ★ 혹시 계획에 섞여 들어와도 **여기서 한 번 더** 막습니다
    줄들, 뺀것 = R.lftp지우기(['.htaccess', 'api/x.php', 'ok.html'])
    봄('건드리면 안 될 것은 명령에서도 막습니다',
       줄들 == ['rm -f "/www/ok.html";'] and len(뺀것) == 2,
       '%s / %s' % (줄들, 뺀것))

    봄('mirror --delete 를 쓰지 않습니다',
       all('--delete' not in x for x in 줄들))


def 시험_가짜서버되돌리기():
    print('[9] 가짜 서버에서 **실제로** 되돌려 봅니다')
    #   ★ 셈이 맞는 것과 실제로 되돌아가는 것은 다릅니다.
    #     폴더를 서버 삼아 계획대로 지우고 덮어 보고, 끝난 모습이
    #     지난 판과 **똑같은지** 봅니다.
    import shutil
    import tempfile
    t = tempfile.mkdtemp(prefix='되돌리기-')
    try:
        서버 = os.path.join(t, 'www')
        지난판 = os.path.join(t, 'before')
        for d in (서버, 지난판):
            os.makedirs(os.path.join(d, 'sub'))
            os.makedirs(os.path.join(d, 'api'))

        def 쓰기(밭, 길, 글):
            p = os.path.join(밭, 길.replace('/', os.sep))
            d = os.path.dirname(p)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            io_ = __import__('io')
            io_.open(p, 'w', encoding='utf-8').write(글)

        # 지난 판 (되돌아갈 모습)
        옛파일 = {}
        for 길, 글 in (('a.html', '옛a'), ('sub/b.css', '옛b'),
                       ('사라질.html', '옛사라질')):
            쓰기(지난판, 길, 글)
            쓰기(서버, 길, 글)
            옛파일[길] = 글

        # 이번 판 — a 를 고치고, c 를 새로 올리고, 사라질.html 을 없앰
        쓰기(서버, 'a.html', '새a')
        쓰기(서버, 'c.html', '새c')
        os.remove(os.path.join(서버, '사라질.html'))
        새파일 = {'a.html': '새a', 'sub/b.css': '옛b', 'c.html': '새c'}

        # 서버에만 있는 것 — 되돌리기가 **건드리면 안 됩니다**
        쓰기(서버, 'api/marine.php', '손으로 올린 것')
        쓰기(서버, '손으로올린.txt', '남의 것')

        계획 = R.되돌림계획(옛파일, 새파일)
        봄('지울 것은 c.html 뿐', 계획['지울것'] == ['c.html'],
           계획['지울것'])
        봄('되돌릴 것은 a.html 과 사라질.html',
           계획['되돌릴것'] == ['a.html', '사라질.html'],
           계획['되돌릴것'])

        # 실제로 되돌립니다 — 지우고, 지난 판을 덮습니다
        for k in 계획['지울것']:
            p = os.path.join(서버, k.replace('/', os.sep))
            if os.path.isfile(p):
                os.remove(p)
        for k in 계획['되돌릴것']:
            쓰기(서버, k, 옛파일[k])

        # 끝난 모습을 봅니다
        def 읽기(밭, 길):
            p = os.path.join(밭, 길.replace('/', os.sep))
            if not os.path.isfile(p):
                return None
            return __import__('io').open(p, encoding='utf-8').read()

        봄('a.html 이 옛 것으로 돌아왔습니다',
           읽기(서버, 'a.html') == '옛a', 읽기(서버, 'a.html'))
        봄('사라졌던 것이 살아났습니다',
           읽기(서버, '사라질.html') == '옛사라질')
        봄('이번 판에만 있던 c.html 이 사라졌습니다',
           읽기(서버, 'c.html') is None)
        봄('안 바뀐 것은 그대로입니다',
           읽기(서버, 'sub/b.css') == '옛b')
        # ★ 가장 중요합니다 — 남의 것을 안 건드렸는가
        봄('api/ 를 안 건드렸습니다',
           읽기(서버, 'api/marine.php') == '손으로 올린 것')
        봄('서버에만 있던 파일도 그대로입니다',
           읽기(서버, '손으로올린.txt') == '남의 것')
    finally:
        shutil.rmtree(t, ignore_errors=True)


def main():
    print('판 견주기와 되돌림 계획 (2026-10-08)')
    print('')
    시험_판읽기()
    시험_견주기()
    시험_건드리면안될것()
    시험_되돌림계획()
    시험_모르면안지움()
    시험_위험한가()
    시험_실제판()
    시험_lftp명령()
    시험_가짜서버되돌리기()
    print('')
    if 실패:
        print('✗ %d가지가 틀렸습니다' % len(실패))
        for x in 실패:
            print('   ✗ %s' % x)
        return 1
    print('모두 통과 — 되돌림 계획을 믿을 수 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
