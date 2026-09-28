# -*- coding: utf-8 -*-
"""**이 주소는 무엇인가** — 한 곳에서만 답합니다.

★ 왜 만들었나 (2026-09-27 — 오늘 같은 병이 **세 번째**입니다)

    판정에서 6번과 11번이 FAIL 로 나왔습니다. 까닭을 캐 보니
    둘이 같은 뿌리였습니다.

        `travel/index.html` 은 `keep.json` 에
        **「옛 쪽을 일부러 남깁니다」**로 적혀 있습니다.

        check_assets   keep.json 을 읽습니다   → 통과
        check_links    안 읽습니다             → **FAIL**
        check_urls     안 읽습니다             → **FAIL**

    **검사기마다 답이 달랐습니다.** 쪽은 멀쩡한데 판정이 빨간불입니다.

    오늘 같은 병이 세 번 나왔습니다.

        바깥 자리 목록   check_console 만 가짐      → net.py 로 모음
        크롬 자리       검사기 6개에 베껴짐          → machine.py 로 모음
        주소의 갈래     check_assets 만 keep 을 봄  → **이 파일**

    주인 규칙 29 의 뜻과 같습니다 —
    「한 곳을 고치고 다른 곳을 잊으면 쪽마다 값이 달라집니다」.
    숫자만 그런 것이 아니라 **판단도** 그렇습니다.

★ 주소는 다섯 중 하나입니다

    있음          새 틀이 만들었습니다. site/ 에 파일이 있습니다
    남긴옛쪽       새 틀은 안 만들지만 **옛 쪽이 서버에 그대로** 있습니다
                  (배포가 파일을 안 지웁니다. keep.json 에 적은 것만)
    나중에         만들기로 했는데 아직 안 만들었습니다 (url-map.json)
    일부러없앰      두지 않기로 했습니다 (url-map.json)
    없음          **아무 데도 안 적힌 채 깨졌습니다** — 진짜 탈

★ 「남긴 옛 쪽」을 봐주는 데도 조건이 있습니다
    배포가 파일을 안 지우므로 옛 쪽이 남는 것은 사실입니다.
    다만 그것은 **우연히 안전한 것**이라, keep.json 에
    「일부러 남깁니다」라고 적어 둔 것만 봐줍니다.
    안 적었으면 탈입니다.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

있음 = '있음'
남긴옛쪽 = '남긴옛쪽'
나중에 = '나중에'
일부러없앰 = '일부러없앰'
없음 = '없음'


def _같은뜻(길):
    """`guide/index.html` 과 `guide` 와 `guide/` 는 같은 곳입니다."""
    나옴 = {길}
    if 길.endswith('/index.html'):
        뿌리 = 길[:-len('/index.html')]
        나옴.add(뿌리)
        나옴.add(뿌리 + '/')
    if 길.endswith('/'):
        나옴.add(길.rstrip('/'))
        나옴.add(길.rstrip('/') + '/index.html')
    if 길 and not 길.endswith(('/', '.html')):
        나옴.add(길 + '/')
        나옴.add(길 + '/index.html')
    return 나옴


def _펴기(것들):
    나옴 = set()
    for x in 것들:
        if not x or x.startswith('_'):
            continue
        나옴 |= _같은뜻(x)
    return 나옴


def 남긴옛쪽들():
    """`keep.json` 의 「남길것」 — 일부러 서버에 두는 옛 파일."""
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
    return _펴기(d.get('남길것') or {})


def 나중에만들쪽들():
    """`url-map.json` 의 「아직_안_만듦」."""
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    return _펴기((d.get('아직_안_만듦') or {}).get('쪽') or [])


def 일부러없앤쪽들():
    """`url-map.json` 의 「일부러_없앰」."""
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json'))
    return _펴기((d.get('일부러_없앰') or {}).get('쪽') or {})


class 갈래표(object):
    """한 번 읽어 두고 여러 번 묻습니다.

    ★ 검사기가 링크 만 개를 봅니다. 그때마다 json 을 읽으면 느립니다.
    """

    def __init__(self, 있는파일=None):
        self.있는파일 = set(있는파일 or ())
        self.남긴것 = 남긴옛쪽들()
        self.나중것 = 나중에만들쪽들()
        self.없앤것 = 일부러없앤쪽들()

    def 무엇인가(self, 길):
        """주소 하나가 다섯 갈래 중 무엇인지."""
        길 = (길 or '').strip()
        if not 길:
            return 없음
        이름들 = _같은뜻(길)
        if self.있는파일 and (이름들 & self.있는파일):
            return 있음
        # ★ 차례가 뜻을 정합니다
        #   「남긴 옛 쪽」이 「나중에」보다 먼저입니다. 둘 다 적혀 있으면
        #   **지금 서버에 있다**는 쪽이 참입니다 — 404 가 안 납니다.
        if 이름들 & self.남긴것:
            return 남긴옛쪽
        if 이름들 & self.나중것:
            return 나중에
        if 이름들 & self.없앤것:
            return 일부러없앰
        return 없음

    def 손님이404를보나(self, 길):
        """**손님이 눌렀을 때 404 가 나는가.** 이것만이 막을 까닭입니다.

        「나중에 만들 쪽」도 지금은 404 입니다. 다만 적어 두었으니
        빠뜨린 것이 아니라 아는 빚입니다 — 알림으로 둡니다.
        """
        return self.무엇인가(길) == 없음

    def 봐줄만한가(self, 길):
        """404 가 나더라도 적어 두었으니 막지는 않는 것."""
        return self.무엇인가(길) in (있음, 남긴옛쪽, 나중에, 일부러없앰)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    표 = 갈래표()
    print('주소의 갈래를 한 곳에서 봅니다')
    print('  남긴 옛 쪽     %3d개 (keep.json)' % len(남긴옛쪽들()))
    print('  나중에 만들 쪽  %3d개 (url-map.json)' % len(나중에만들쪽들()))
    print('  일부러 없앤 것  %3d개 (url-map.json)' % len(일부러없앤쪽들()))
    print('')
    for 길 in ('travel/index.html', 'travel/', 'travel',
               'tide', 'rule.html', 'guide', '404.html',
               '_ad-compare.html', 'aaa-없는쪽.html'):
        print('  %-24s %s' % (길, 표.무엇인가(길)))
