# -*- coding: utf-8 -*-
"""되돌리면 **정확히 그 판이 되는가** (2026-10-07 바깥 검수 순서 ③④⑤⑦).

★ 왜
    바깥 검수 — 「지금 발견한 구멍은 **실제 구멍**입니다.
      현재 rollback 은 **『파일을 덮어쓰는 복원』**이지
      **『정확히 이전 판으로 되돌리는 복원』**은 아닙니다.
      다만 `--delete` 는 **칼이 큰 만큼**, 먼저 **백업 완전성 +
      삭제 계획을 증명하고** 넣는 것이 맞습니다」

    지금 코드는 `mirror -R _before/ /www/` 입니다. 새 판에만 있던
    파일이 되돌린 뒤에도 남습니다. 새 쪽을 더한 배포를 되돌리면
    **그 쪽이 고아로 남고** sitemap 과 어긋납니다.

★ 바깥 검수가 정해 준 차례 가운데 여기서 하는 것
    ③ 로컬 가짜 /www 로 `--delete` rollback exactness 시험
    ④ `_stage` 보존 시험
    ⑤ `api/` · 중국어판 · `.htaccess` 보존 시험
    ⑦ 삭제 예정 경로 위험검사

  **서버에 붙지 않습니다.** 살아 있는 사이트라 함부로 못 합니다.
  그래서 셈을 순수함수로 떼어 두고 여기서 가짜 밭으로 잽니다.

쓰는 법
    python tests/test_rollback_exact.py
"""
import io as _io
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.check_backup import (견주기, 지울것, 위험한가,
                                 길다듬기, 건드리면안될것,
                                 lftp계획읽기)

통과, 실패 = 0, []


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s %s' % (이름, 덧))


# ── 가짜 서버 — 옛 판과 새 판
옛판 = ['index.html', 'taean.html', 'css/style.css',
        '.htaccess', 'api/tide.php', 'zh-cn/index.html',
        'img/a.jpg', 'favicon.ico']
새판 = ['index.html', 'taean.html', 'css/style.css',
        '.htaccess', 'api/tide.php', 'zh-cn/index.html',
        'img/a.jpg', 'favicon.ico',
        '새쪽.html', 'fish/bollak.html']        # ★ 새로 생긴 둘


def 시험_삭제계획():
    print('[1] ③ 되돌릴 때 **무엇이 지워져야 하는가**')

    지울 = 지울것(새판, 옛판)
    봄('① 새 판에만 있던 것 둘을 지운다',
       지울 == ['fish/bollak.html', '새쪽.html'], 지울)

    # ★ 지금 코드(--delete 없음)는 **아무것도 안 지웁니다**
    봄('② 안 지우면 새 쪽이 서버에 남는다',
       set(새판) - set(지울것([], [])) != set(옛판),
       '지금 되돌리기가 바로 이 상태입니다')

    봄('③ 같은 판끼리는 지울 것이 없다', 지울것(옛판, 옛판) == [])


def 시험_보존():
    print('')
    print('[2] ④⑤ **지우면 안 되는 것**이 삭제 목록에 드는가')

    # ④ _stage — 백업에서 일부러 뺐으니 지울 것에도 없어야 합니다
    서버 = 새판 + ['_stage/index.html', '_stage/css/a.css']
    지울 = 지울것(서버, 옛판)
    봄('④ _stage 는 지울 목록에 안 든다',
       not [x for x in 지울 if x.startswith('_stage')],
       '백업에서 뺀 것을 지우면 **검증판 자리가 사라집니다**')

    # ⑤ .htaccess · api/ · 중국어판 — 백업에 **들어 있으면** 안 지웁니다
    봄('⑤ 백업에 든 .htaccess 는 안 지운다',
       '.htaccess' not in 지울것(새판, 옛판))
    봄('⑥ 백업에 든 api/ 는 안 지운다',
       not [x for x in 지울것(새판, 옛판) if x.startswith('api/')])
    봄('⑦ 백업에 든 중국어판은 안 지운다',
       not [x for x in 지울것(새판, 옛판) if x.startswith('zh-cn/')])


def 시험_위험검사():
    print('')
    print('[3] ⑦ **삭제 예정 경로 위험검사** — 못 받았을 때를 잡는가')

    # ★ 이것이 가장 무서운 경우입니다.
    #   `ftp:list-options -a` 가 없어 **.htaccess 를 못 받으면**,
    #   되돌릴 목록에 없으니 **지울 것**으로 뽑힙니다.
    못받은백업 = [x for x in 옛판 if x != '.htaccess']
    지울 = 지울것(새판, 못받은백업)
    걸린 = 위험한가(지울)
    봄('⑧ .htaccess 를 못 받았으면 **위험으로 잡는다**',
       any(x[1] == '.htaccess' for x in 걸린),
       '안 잡으면 되돌릴 때 사이트가 **500 으로 멈춥니다**')

    못받은2 = [x for x in 옛판 if not x.startswith('api/')]
    봄('⑨ api/ 를 못 받았으면 위험으로 잡는다',
       any('api/' in x[1] for x in 위험한가(지울것(새판, 못받은2))))

    봄('⑩ 멀쩡할 때는 위험이 없다', 위험한가(지울것(새판, 옛판)) == [])


def 시험_견주기():
    print('')
    print('[4] ② 백업 완전성 — 서버와 받은 것을 견주는가')

    봄('⑪ 다 받았으면 못 받은 것이 없다', 견주기(옛판, 옛판) == ([], []))

    못받음, _ = 견주기(옛판, [x for x in 옛판 if x != '.htaccess'])
    봄('⑫ .htaccess 를 빠뜨리면 집어낸다', 못받음 == ['.htaccess'],
       못받음)

    # _stage 는 일부러 안 받았으니 **빠진 것이 아닙니다**
    못받음2, _ = 견주기(옛판 + ['_stage/a.html'], 옛판)
    봄('⑬ 일부러 뺀 _stage 는 빠진 것으로 세지 않는다', 못받음2 == [],
       못받음2)


def 시험_길다듬기():
    print('')
    print('[5] lftp 가 낸 줄을 제대로 읽는가')
    봄('⑭ /www/ 를 뗀다', 길다듬기('/www/index.html') == 'index.html')
    봄('⑮ 폴더 안쪽도 읽는다',
       길다듬기('/www/zh-cn/index.html') == 'zh-cn/index.html')
    봄('⑯ 빈 줄은 버린다', 길다듬기('   ') is None)
    봄('⑰ 점 파일도 읽는다', 길다듬기('/www/.htaccess') == '.htaccess')
    # ★ **폴더는 세지 않습니다** (2026-10-07 ⑥ 실측에서 드러남)
    #   lftp find 는 폴더도 끝에 / 를 붙여 냅니다. 파일로 세었더니
    #   폴더 93개가 「안 받은 것」으로 잡혀 배포를 막았습니다.
    #   lftp 는 정작 0개를 지우겠다고 했습니다.
    봄('⑱ 폴더(/ 로 끝남)는 안 센다', 길다듬기('/www/api/') is None,
       길다듬기('/www/api/'))
    봄('⑲ 폴더 안 파일은 센다',
       길다듬기('/www/api/tide.php') == 'api/tide.php')


def 시험_진짜파일로():
    """★ 목록 셈이 맞아도 **파일로 해 보면 다를 수** 있습니다.

    가짜 밭을 만들어 「지울것() 대로 지우고 되돌릴 것을 덮어쓰면
    **정확히 옛 판**이 되는가」를 봅니다.
    """
    print('')
    print('[6] ③ 가짜 서버에 **실제로 해 봅니다**')
    t = tempfile.mkdtemp(prefix='되돌리기-')
    try:
        www = os.path.join(t, 'www')
        백업 = os.path.join(t, '_before')

        def 짓기(밭, 것들, 속=''):
            for 길 in 것들:
                p = os.path.join(밭, *길.split('/'))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                _io.open(p, 'w', encoding='utf-8').write(속 + 길)

        짓기(백업, 옛판, '옛 ')                 # 받아 둔 것
        짓기(www, 새판, '새 ')                  # 지금 서버
        짓기(www, ['_stage/index.html'], '검증 ')

        # ── 되돌리기 흉내 — 덮어쓰고 + 지웁니다
        for 길 in 옛판:
            ㄱ = os.path.join(백업, *길.split('/'))
            ㄴ = os.path.join(www, *길.split('/'))
            os.makedirs(os.path.dirname(ㄴ), exist_ok=True)
            shutil.copy2(ㄱ, ㄴ)
        for 길 in 지울것(새판, 옛판):
            p = os.path.join(www, *길.split('/'))
            if os.path.exists(p):
                os.remove(p)

        뒤 = []
        for 터, _, 것들 in os.walk(www):
            for 이름 in 것들:
                뒤.append(os.path.relpath(os.path.join(터, 이름), www)
                          .replace(os.sep, '/'))

        봄('⑱ 되돌린 뒤 **정확히 옛 판**이다 (_stage 빼고)',
           sorted(x for x in 뒤 if not x.startswith('_stage')) == sorted(옛판),
           sorted(set(뒤) ^ set(옛판)))
        봄('⑲ _stage 는 그대로 남아 있다',
           os.path.exists(os.path.join(www, '_stage', 'index.html')))
        봄('⑳ 내용도 옛 판이다',
           _io.open(os.path.join(www, 'index.html'),
                    encoding='utf-8').read().startswith('옛 '))
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 시험_교차검증():
    """★ lftp 가 하려는 일과 **내 셈**이 같은가.

    바깥 검수 — 「저는 `lftp --dry-run` **출력 문자열 자체를
      안전판정의 유일한 근거로 쓰지는 않겠습니다.** … 판정은
      **경로 집합 계산**을 기준으로 하고, `--dry-run` 은
      **우리 계산이 맞는지** 확인하는 교차검증으로 쓰세요」
    """
    print('')
    print('[7] lftp 가 낸 삭제 계획을 제대로 읽는가')

    글 = [
        'mkdir /www/새폴더',
        'rm /www/새쪽.html',
        'rm /www/fish/bollak.html',
        'put /www/index.html',
        'rmdir /www/연습임시',
        '',
    ]
    것 = lftp계획읽기(글)
    봄('㉑ 지우겠다는 것만 뽑는다',
       것 == ['fish/bollak.html', '새쪽.html', '연습임시'], 것)
    봄('㉒ 올리는 줄은 안 센다', 'index.html' not in 것)
    봄('㉓ 빈 줄에 안 걸린다', lftp계획읽기(['', '   ']) == [])
    봄('㉔ 점 파일도 제 이름으로 읽는다',
       lftp계획읽기(['rm /www/.htaccess']) == ['.htaccess'],
       lftp계획읽기(['rm /www/.htaccess']))

    # ★ **내 셈과 lftp 가 같은지**가 쓰임새입니다
    내셈 = 지울것(새판, 옛판)
    lftp것 = lftp계획읽기(['rm /www/' + x for x in 내셈])
    봄('㉕ 내 셈과 lftp 가 같으면 차이가 없다',
       sorted(내셈) == sorted(lftp것))
    # 하나를 빠뜨리면 **드러나야** 합니다
    모자란것 = lftp계획읽기(['rm /www/' + x for x in 내셈[:1]])
    봄('㉖ lftp 가 덜 지우면 차이로 드러난다',
       set(내셈) ^ set(모자란것) != set())

def 시험_차단자리():
    """★ `--delete` 가 들어가는 **그 순간부터** 막는 자리가 앞이어야 합니다.

    바깥 검수 —
      「현재는 MEASURE NOW · BLOCK AFTER 20 을 **과도기로 허용**합니다.
        까닭은 실제 rollback 에 아직 `--delete` 가 없기 때문입니다.
        … 다만 `--delete` 를 실제 rollback 에 넣는 순간부터는
        **순서를 바꿔야 합니다** — 위험하면 **즉시 STOP**,
        그 뒤에 20번 post-deploy 검증.
        이 차이를 **TODO 가 아니라 코드 계약으로 승격**하세요」

    ★ 지금은 통과합니다. **`--delete` 를 넣는 커밋에서 이 시험이
      막습니다.** 주석으로만 적어 두면 그때 아무도 안 봅니다 —
      오늘 이미 「만들어 놓고 목록에 안 적어 아무도 안 돌린」 일을
      겪었습니다.
    """
    print('')
    print('[8] --delete 가 들어가면 막는 자리가 앞인가')
    import io as _io
    import re as _re
    배포글 = _io.open(os.path.join(ROOT, '.github', 'workflows',
                                  'deploy.yml'), encoding='utf-8').read()

    # 「나쁘면 되돌립니다」 단계 안에 --delete 가 있는가
    시 = 배포글.find('- name: 나쁘면 되돌립니다')
    마 = 배포글.find('- name: ', 시 + 20)
    되돌리기몸 = 배포글[시:마 if 마 > 0 else len(배포글)]
    딜리트쓰나 = '--delete' in 되돌리기몸

    자리_재기 = 배포글.find('- name: 되돌림 계획을 재 봅니다')
    자리_막기 = 배포글.find('- name: 되돌림 준비가 됐는가')
    자리_20번 = 배포글.find('- name: 올린 것을 서버에서 확인')

    봄('㉗ 세 단계가 모두 있다',
       min(자리_재기, 자리_막기, 자리_20번) > 0,
       '(재기 %d · 막기 %d · 20번 %d)' % (자리_재기, 자리_막기, 자리_20번))
    봄('㉘ 재기는 20번보다 **앞**에 있다', 0 < 자리_재기 < 자리_20번)

    if 딜리트쓰나:
        # ★ **승격된 계약** — 이제 막기도 앞이어야 합니다
        봄('㉙ --delete 를 쓰므로 막기도 20번보다 **앞**이어야 한다',
           0 < 자리_막기 < 자리_20번,
           '되돌리기가 정말 지우는데 20번 뒤에서 막으면 **늦습니다**')
    else:
        봄('㉙ 아직 --delete 를 안 쓰므로 막기는 20번 뒤여도 된다',
           자리_막기 > 자리_20번,
           '과도기 허용 — 올린 것이 멀쩡한지 먼저 봅니다')

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('되돌리면 **정확히 그 판이 되는가** (바깥 검수 2026-10-07)')
    print('')
    시험_삭제계획()
    시험_보존()
    시험_위험검사()
    시험_견주기()
    시험_길다듬기()
    시험_진짜파일로()
    시험_교차검증()
    시험_차단자리()
    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **되돌릴 수 없는 백업은 백업이 아닙니다.**')
        return 1
    print('%d가지 모두 통과 — 삭제 계획과 위험검사가 제대로 돕니다.' % 통과)
    print('  ※ 아직 **실제 되돌리기에는 --delete 를 안 넣었습니다.**')
    print('    바깥 검수 순서 ⑥(운영 대상 --dry-run)이 남았습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
