# -*- coding: utf-8 -*-
"""올린 직후 서버를 재고, **되돌릴지 말지**를 판정합니다.

★ 왜 생겼나 (2026-09-27 바깥 검수 4차)

      「무조건 자동 rollback 에는 반대합니다. 조건부 자동 롤백입니다.

        자동 rollback 해도 되는 것
          서버 파일 fingerprint 불일치 · 필수 파일 없음 · 5xx 지속
          index 접근 불가 · build.json 불일치

        자동 rollback 하면 안 되는 것
          1회 timeout · 일시적 네트워크 오류 · 특정 외부 API 응답 지연
          광고 응답 지연 · 한 번의 404

        curl 1회 실패 → rollback 이면 네트워크 순간 장애 때문에
        정상 배포를 되돌릴 수 있습니다」

    옳습니다. 그래서 이렇게 합니다.

        1차 봄 → 실패 → 3초 쉼 → 2차 봄 → 실패 → 6초 쉼 → 3차 봄
              → 그래도 실패면 **결정적인가?** 를 따집니다
              → 결정적 → 되돌림
              → 아니면 → 주인께 알리고 멈춤

★ 이 도구는 **되돌리지 않습니다.** 판정만 냅니다.
    되돌리는 것은 engine/release.py 가 합니다. 재는 것과 고치는 것을
    한 도구에 두면, 잘못 쟀을 때 잘못 고칩니다.

끝난값
    0   괜찮습니다
    3   **되돌려야 합니다** (결정적 오류)
    4   수상하지만 결정적이지 않습니다 — 사람이 봅니다
    2   못 쟀습니다 (--net 없이 돌렸거나 바깥에 못 나갔습니다)

쓰는 법
    python engine/smoke.py             무엇을 볼지만 보여 줍니다
    python engine/smoke.py --net       실제로 서버에 물어봅니다
"""
import os
import re
import sys
import ssl
import json
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

SITE = os.environ.get('BADAGAJA_URL', 'https://badagaja.com').rstrip('/')

# ★ **뿌리**는 따로 봅니다 (2026-09-28 — check_deployed 와 같은 이야기)
#
#   검증 배포는 하위 칸(/_stage/)에 올립니다. 그런데 「남기기로 한
#   옛 쪽」(zh-cn/ · robots.txt)은 **뿌리에만 있습니다.**
#   그 둘을 /_stage/ 밑에서 찾으면 404 가 나오고, 검사기는
#   「배포가 사이트를 깼다」고 말합니다. 사이트는 멀쩡한데요.
뿌리 = os.environ.get('BADAGAJA_URL_ROOT',
                      'https://badagaja.com').rstrip('/')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

봄횟수 = 3
쉼 = (0, 3, 6)          # 1차는 바로, 그 뒤로 3초·6초 쉽니다

# ── 되돌려야 하는 것 (결정적) ───────────────────────────────
#   여기 든 것은 **서버가 잘못 올라갔다**는 뜻입니다. 시간이 지나도
#   저절로 낫지 않습니다.
결정적 = []
# ── 수상하지만 결정적이지 않은 것 ──────────────────────────
#   네트워크·바깥 API 형편일 수 있습니다. 사람이 봅니다.
수상함 = []


def 받기(주소, 시간=20):
    """한 번 받아 봅니다. 돌려주는 것: (코드, 글, 탈)"""
    틀 = ssl.create_default_context()
    req = urllib.request.Request(
        주소, headers={'User-Agent': 'badagaja-smoke/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=시간, context=틀) as r:
            날것 = r.read(600000)
            try:
                글 = 날것.decode('utf-8', 'replace')
            except (UnicodeDecodeError, AttributeError):
                글 = ''
            return r.getcode(), 글, None
    except urllib.error.HTTPError as e:
        return e.code, '', None
    except (urllib.error.URLError, OSError, ValueError) as e:
        return None, '', str(e)


def 세번봄(주소):
    """세 번까지 봅니다. 한 번이라도 되면 된 것입니다.

    ★ 한 번 실패로 판정하지 않습니다 (바깥 검수 4차)
    """
    마지막 = (None, '', '안 봤습니다')
    for 차례 in range(봄횟수):
        if 쉼[차례]:
            time.sleep(쉼[차례])
        코드, 글, 탈 = 받기(주소)
        마지막 = (코드, 글, 탈)
        if 코드 and 200 <= 코드 < 400:
            return 코드, 글, 탈, 차례 + 1
    return 마지막[0], 마지막[1], 마지막[2], 봄횟수



def _쪽지길():
    """쪽지 이름은 engine/mark_stage.py 한 곳에만 있습니다 (SSOT)."""
    from engine import mark_stage
    return mark_stage.이름표길


def 볼것들():
    """무엇을 볼지. 대표 쪽만 봅니다 — 전수는 check_deployed 가 합니다."""
    것 = [
        ('/', '첫 화면', True),
        ('/build.json', '판 지문', True),
        # ★ **여기가 어디인지 밝히는 쪽지** (2026-09-28 바깥 검수 9차)
        #   검증 칸에만 있습니다. 운영 뿌리를 잴 때는 없는 것이 맞으니
        #   「꼭」을 False 로 둡니다. check_deployed 가 엄하게 봅니다.
        ('/' + _쪽지길(), '여기가 어디인가', False),
        ('/taean.html', '권역(태안)', True),
        ('/point/chungnam/taean_fishing.html', '포인트 목록', True),
        ('/festival/', '축제 달력', True),
        ('/catch/baekhap.html', '어종(백합)', True),
        ('/assets/css/site.css', '차림표', True),
        ('/assets/js/tide.js', '물때 움직임', True),
        ('/img/coast/taean-hero.jpg', '대표 사진', True),
        # ↓ 이 둘은 **뿌리에서** 봅니다 (새 틀이 안 만드는 옛 것)
        ('/zh-cn/', '옛 중국어판 (남기기로 한 것)', True, True),
        ('/robots.txt', '로봇 안내', False, True),
    ]
    # 네 번째 값이 없으면 「이 자리에서 본다」는 뜻입니다
    return [(x + (False,))[:4] for x in 것]


def main():
    바깥 = '--net' in sys.argv
    것들 = 볼것들()

    print('올린 직후 서버를 봅니다 (바깥 검수 4차 — 조건부 롤백)')
    print('  서버 %s' % SITE)
    print('')

    if not 바깥:
        print('무엇을 볼지만 보여 드립니다 — 실제로는 안 물어봤습니다')
        print('')
        for 길, 이름, 꼭, 밖 in 것들:
            print('  %-4s %-40s %s'
                  % ('필수' if 꼭 else '', (뿌리 if 밖 else SITE) + 길, 이름))
        print('')
        print('  한 번 실패로 되돌리지 않습니다 — %d번까지 봅니다.' % 봄횟수)
        print('실제로 보려면 --net 을 붙이세요.')
        print('  ※ 이것은 「지킴」이 아닙니다. **아직 안 잰 것**입니다.')
        return 2

    # ── 1. 쪽이 열리는가
    print('[1] 쪽이 열리는가 (한 번 실패로 판정하지 않습니다)')
    내판 = io.read_json(os.path.join(NEW, 'build.json'), default=None)
    서버판 = None
    for 길, 이름, 꼭, 밖 in 것들:
        코드, 글, 탈, 몇번 = 세번봄((뿌리 if 밖 else SITE) + 길)
        표 = '·'
        덧 = ''
        if 코드 is None:
            표 = '✗'
            덧 = 탈 or '못 받음'
            # 못 닿은 것은 네트워크 형편일 수 있습니다
            (결정적 if 꼭 and 길 == '/' else 수상함).append(
                '%s — %s' % (길, 덧))
        elif 코드 >= 500:
            표 = '✗'
            덧 = '서버 오류 %d' % 코드
            결정적.append('%s — 서버 오류 %d 가 %d번 이어집니다'
                          % (길, 코드, 봄횟수))
        elif 코드 == 404:
            표 = '✗'
            덧 = '없음'
            (결정적 if 꼭 else 수상함).append('%s — 404' % 길)
        elif not (200 <= 코드 < 400):
            표 = '~'
            덧 = '코드 %d' % 코드
            수상함.append('%s — 코드 %d' % (길, 코드))
        if 길 == '/build.json' and 글:
            try:
                서버판 = json.loads(글)
            except ValueError:
                서버판 = None
        print('      %s %-42s %-24s %s%s'
              % (표, 길, 이름, 코드 or '-',
                 ('  (' + 덧 + ')') if 덧 else
                 ('  %d번째에 됐습니다' % 몇번 if 몇번 > 1 else '')))
    print('')

    # ── 2. 올라간 것이 내가 만든 그것인가
    #
    # ★ **되돌리기 연습에서는 묻지 않습니다** (2026-09-28)
    #
    #   이 물음은 **배포 직후**에만 뜻이 있습니다.
    #   「방금 올린 것이 내가 만든 그것인가」를 보는 것입니다.
    #
    #   되돌리기 연습은 다릅니다. 서버를 **옛 판**으로 되돌려 놓고
    #   그것이 제자리로 왔는지 봅니다. 그 옛 판은 옛 코드로 만든
    #   것이라 지금 코드로 만든 것과 당연히 다릅니다.
    #
    #   실제로 연습 #2 가 이렇게 말했습니다.
    #       내 것 8e5d1e32… 719개 · 서버 723c7208… 718개 ✗
    #   되돌리기는 **완벽히 됐는데도**(719개가 A판과 바이트까지
    #   같음) 엉뚱한 기준 때문에 어김으로 찍혔습니다.
    #
    #   **무엇을 재는지 틀리면, 맞게 잰 것도 틀리게 나옵니다.**
    if '--판지문묻지않기' in sys.argv:
        print('[2] 올라간 것이 내가 만든 그것인가 (판 지문)')
        print('      - 이번에는 묻지 않습니다 (--판지문묻지않기)')
        print('        되돌리기 연습은 **옛 판**으로 돌아왔는지를 봅니다.')
        print('        옛 판은 옛 코드로 만든 것이라 달라야 정상입니다.')
        print('')
    elif not 내판:
        수상함.append('내 쪽에 build.json 이 없습니다')
        print('      ~ 내 쪽에 site/build.json 이 없습니다')
    elif not 서버판:
        결정적.append('서버에서 build.json 을 못 읽었습니다')
        print('  ✗ 서버에서 판 지문을 못 읽었습니다')
    else:
        같나 = (내판.get('통지문') == 서버판.get('통지문'))
        print('      내 것  %s · 파일 %d개'
              % (내판.get('통지문', '')[:16], 내판.get('파일수', 0)))
        print('      서버   %s · 파일 %d개'
              % (서버판.get('통지문', '')[:16], 서버판.get('파일수', 0)))
        if 같나:
            print('  · 같습니다 — 올린 것이 내가 만든 그것입니다')
        else:
            내파일 = 내판.get('파일') or {}
            서버파일 = 서버판.get('파일') or {}
            빠짐 = sorted(set(내파일) - set(서버파일))
            다름 = sorted(k for k in set(내파일) & set(서버파일)
                          if 내파일[k] != 서버파일[k])
            결정적.append('판 지문이 다릅니다 — 빠짐 %d · 내용다름 %d'
                          % (len(빠짐), len(다름)))
            print('  ✗ 다릅니다 — 서버에 없는 것 %d · 내용이 다른 것 %d'
                  % (len(빠짐), len(다름)))
            for x in (빠짐[:3] + 다름[:3]):
                print('      %s' % x)
    print('')

    # ── 3. 물때가 맞는가 — 이 사이트의 뼈대입니다
    print('[3] 물때가 서버에서도 맞는가')
    코드, 글, 탈, _ = 세번봄(SITE + '/assets/js/tide.js')
    if 코드 == 200 and 글:
        내것 = io.꼭읽기(os.path.join(NEW, 'assets', 'js', 'tide.js'))
        같나 = (re.sub(r'\s+', ' ', 글).strip()
                == re.sub(r'\s+', ' ', 내것).strip())
        print('      물때 움직임이 내 것과 %s'
              % ('같습니다' if 같나 else '✗ 다릅니다'))
        if not 같나:
            결정적.append('서버의 tide.js 가 내 것과 다릅니다')
        # 식이 밀려 있지 않은가 — 2026-09-27 에 실제로 겪었습니다
        if '(음력날(날짜) + 6) % 15' in 글:
            결정적.append('서버의 물때 식이 한 칸 밀려 있습니다')
            print('  ✗ **물때 식이 한 칸 밀려 있습니다**')
    else:
        수상함.append('tide.js 를 못 받았습니다')
        print('      ~ 못 받았습니다')
    print('')

    # ── 판정
    print('  ' + '─' * 58)
    if 결정적:
        print('  판정: **되돌려야 합니다**  (결정적 오류 %d가지)'
              % len(결정적))
        for x in 결정적:
            print('    ✗ %s' % x)
        print('')
        print('    되돌리기: python engine/release.py --되돌리기')
        print('    되돌린 뒤 이 검사를 다시 돌려 확인하세요.')
        return 3
    if 수상함:
        print('  판정: 수상하지만 **결정적이지 않습니다** (%d가지)'
              % len(수상함))
        for x in 수상함:
            print('    ~ %s' % x)
        print('')
        print('    ★ 이런 것으로는 되돌리지 않습니다 (바깥 검수 4차).')
        print('      네트워크 형편이나 바깥 API 지연일 수 있습니다.')
        print('      사람이 보고 정합니다.')
        return 4
    print('  판정: 괜찮습니다 — 되돌릴 까닭이 없습니다')
    print('  ' + '─' * 58)
    return 0


if __name__ == '__main__':
    sys.exit(main())
