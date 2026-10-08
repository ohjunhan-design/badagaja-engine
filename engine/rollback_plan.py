# -*- coding: utf-8 -*-
"""되돌림 계획을 **공개 판 목록만 받아** 셉니다 (2026-10-08 주인 뜻).

★ ★ 주인 말씀 (두 번 하셨습니다) ★ ★

      「배포에 시간이 너무 많이 걸려. **백업본 다운받고 저장해
        버리면 간단할텐데**」

  재 보니 맞습니다. 성공한 배포 39분 26초 가운데
      서버 내려받기 10분 39초 + 되돌림 계획 재 보기 8분 54초
      = **19분 33초(절반)** 가 「되돌리기 준비」였습니다.

★ 그런데 **이미 거의 다 되어 있었습니다**

  배포가 끝날 때 「올린 판을 봉해 둡니다」가 돌아 아티팩트로
  남습니다 — `build.json`(파일 926개의 SHA-256) 과 `site.tgz`.
  그 단계 주석에 **「다음 배포가 찾아 쓸 이름입니다」**라고
  적혀 있는데, **정작 아무도 안 쓰고 있었습니다.**

★ 그리고 더 줄일 수 있습니다

  되돌리기는 **드물게** 일어납니다. 평소에 필요한 것은 「무엇이
  달라졌는가」뿐이고, 그것은 **목록 파일 하나**로 압니다.

      지금  FTP 로 서버 전체 받기      115MB · 10분 39초
      이것  공개 build.json 받기        95KB · **0.09초**

  되돌릴 **내용**(site.tgz)은 **정말 되돌릴 때만** 받으면 됩니다.

★ 이 도구는 **셈하고 보여 줄 뿐** 지우거나 올리지 않습니다.
  셈은 `engine/release.py` 가 하고 시험 33가지를 통과했습니다.
"""
import io as _io
import json
import os
import sys
import urllib.request

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine import release_diff as R   # noqa: E402

기본주소 = 'https://badagaja.com/build.json'
낼곳 = os.path.join(여기, 'tests', 'out', '되돌림계획.json')


def 공개판받기(주소, 초=25):
    """공개 서버의 판 목록. 못 받으면 `(None, 사유)`.

    ★ 못 받은 것을 **빈 목록으로 보지 않습니다.** 빈 목록으로
      셈하면 「전부 지워라」가 나옵니다 (release.판읽기 가 막습니다).
    """
    try:
        req = urllib.request.Request(
            주소, headers={'User-Agent': 'badagaja-rollback-plan'})
        with urllib.request.urlopen(req, timeout=초) as r:
            if r.status != 200:
                return None, 'HTTP %s' % r.status
            return r.read().decode('utf-8', 'replace'), None
    except Exception as e:
        return None, str(e)


def main():
    주소 = 기본주소
    for i, a in enumerate(sys.argv):
        if a == '--주소' and i + 1 < len(sys.argv):
            주소 = sys.argv[i + 1]
    엄격 = '--strict' in sys.argv

    print('되돌림 계획 — 공개 판 목록만 받아 셉니다 (2026-10-08)')
    print('  공개 %s' % 주소)

    글, 왜 = 공개판받기(주소)
    if 글 is None:
        print('□ 공개 판 목록을 못 받았습니다 — %s' % 왜)
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  이럴 때는 기존대로 서버를 통째로 받아 둡니다.')
        return 4 if 엄격 else 0

    옛파일, 옛판 = R.판읽기(글)
    if 옛파일 is None:
        print('□ 공개 판 목록을 읽을 수 없습니다 (모양이 다릅니다)')
        print('  **못 잰 것입니다.** 기존대로 서버를 통째로 받습니다.')
        return 4 if 엄격 else 0

    내길 = os.path.join(여기, 'site', 'build.json')
    if not os.path.isfile(내길):
        print('✗ site/build.json 이 없습니다 — 먼저 build.py 를 돌리세요')
        return 1
    새파일, 새판 = R.판읽기(_io.open(내길, encoding='utf-8').read())
    if 새파일 is None:
        print('✗ 이번 판 목록을 못 읽었습니다')
        return 1

    print('  공개 판 %s — 파일 %d개' % (옛판 or '?', len(옛파일)))
    print('  이번 판 %s — 파일 %d개' % (새판 or '?', len(새파일)))
    print('')

    d = R.견주기(옛파일, 새파일)
    print('  이번 배포가 바꾸는 것')
    print('    새로 생김 %4d' % len(d['생김']))
    print('    바뀜      %4d' % len(d['바뀜']))
    print('    사라짐    %4d' % len(d['사라짐']))
    print('    그대로    %4d' % len(d['그대로']))
    print('')

    계획 = R.되돌림계획(옛파일, 새파일)
    위험 = R.위험한가(계획, 모두=len(새파일))
    print('  되돌려야 한다면')
    print('    지울 것   %4d  (이번 판에만 생긴 것)' % len(계획['지울것']))
    print('    되돌릴 것 %4d  (바뀌었거나 사라진 것)' % len(계획['되돌릴것']))
    print('    api/ · 중국어판 · .htaccess 는 건드리지 않습니다')
    print('')

    난것 = {
        '_무엇인가': ('되돌려야 할 때 무엇을 지우고 무엇을 되돌릴지. '
                      'engine/rollback_plan.py 가 공개 판 목록만 받아 '
                      '셉니다. 손으로 고치지 마세요.'),
        '공개판': 옛판, '이번판': 새판,
        '공개파일수': len(옛파일), '이번파일수': len(새파일),
        '바뀜': {'생김': len(d['생김']), '바뀜': len(d['바뀜']),
                 '사라짐': len(d['사라짐']), '그대로': len(d['그대로'])},
        '지울것': 계획['지울것'],
        '되돌릴것': 계획['되돌릴것'],
        '위험': 위험,
    }
    try:
        os.makedirs(os.path.dirname(낼곳), exist_ok=True)
        _io.open(낼곳, 'w', encoding='utf-8').write(
            json.dumps(난것, ensure_ascii=False, indent=1))
        print('  · 계획을 적었습니다 — %s' % os.path.relpath(낼곳, 여기))
    except Exception as e:
        print('  ~ 계획을 못 적었습니다 (%s)' % e)

    if 위험:
        print('')
        print('✗ 계획이 위험합니다 — %s' % 위험)
        print('  이대로 되돌리면 안 됩니다. 기존대로 서버를 통째로')
        print('  받아 두고 사람이 보세요.')
        return 1

    print('')
    print('되돌림 계획을 셀 수 있습니다.')
    print('  ★ 되돌릴 **내용**(지난 판 파일)은 아직 안 받았습니다 —')
    print('    되돌리기는 드물게 일어나므로 **정말 되돌릴 때만**')
    print('    지난 배포가 봉해 둔 site.tgz 를 받으면 됩니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
