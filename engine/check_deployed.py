# -*- coding: utf-8 -*-
"""**올린 뒤** 서버가 내 것과 같은지 봅니다. (검수 지시 20)

★ 왜 이 검사가 필요한가 (2026-09-27 바깥 검수 지시)

    「20번 Post-deploy 검증을 반드시 넣으세요. 지금 구조에서는
      로컬에서 416페이지가 전부 PASS 해도 카페24 FTP 업로드
      과정에서 누락·잔존 파일·권한·경로 문제가 생길 수 있습니다」

    맞습니다. 내 컴퓨터에서 멀쩡한 것과 서버에서 멀쩡한 것은
    다릅니다. FTP 는 조용히 빠뜨립니다.

무엇을 보나
    1. 올린 쪽이 **내 것과 같은가** (지문을 견줍니다)
    2. 꼭 열려야 할 쪽이 200 으로 열리는가
    3. 자산(차림표·움직임·아이콘)이 열리는가
    4. 옛 중국어판이 안 깨졌는가 — 남기기로 한 것이 살아 있는가
    5. sitemap · robots 가 열리는가

★ 배포 전에는 **NOT_TESTED** 입니다
    「아직 안 올렸습니다」는 「멀쩡합니다」가 아닙니다.

★ 바깥에 나갑니다
    실제 서버에 물어보는 유일한 검사입니다. --net 없이는
    아무것도 재지 않습니다.

쓰는 법
    python engine/check_deployed.py            무엇을 볼지 보여만 줍니다
    python engine/check_deployed.py --net      실제 서버에 물어봅니다
    python engine/check_deployed.py --net --strict
"""
import os
import re
import sys
import glob
import json
import hashlib
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
# ★ 주소는 **한 곳에서** 봅니다 (SSOT — 바깥 검수 7차)
#   smoke.py 는 BADAGAJA_URL 을 보는데 여기만 박아 두어
#   같은 사실이 두 곳에 있었습니다. 검증 배포(_stage)를 재려면
#   두 도구가 **같은 곳**을 봐야 합니다.
SITE = os.environ.get('BADAGAJA_URL', 'https://badagaja.com').rstrip('/')

# ★ **뿌리**는 따로 봅니다 (2026-09-28)
#
#   검증 배포는 같은 서버의 하위 칸(/_stage/)에 올립니다.
#   그런데 **옛 사이트에 남기기로 한 쪽은 뿌리에만 있습니다** —
#   새 틀이 안 만드니 /_stage/ 에는 올라갈 것이 없습니다.
#
#   처음 돌렸을 때 about.html 이 404 로 나와 멈췄습니다.
#   검사는 옳은 말을 했는데 **볼 곳이 틀렸습니다.**
#   옛 쪽은 언제나 뿌리에서 봅니다.
뿌리 = os.environ.get('BADAGAJA_URL_ROOT',
                      'https://badagaja.com').rstrip('/')
검증자리 = (SITE != 뿌리)

막음, 알림 = [], []


_마지막에친때 = [0.0]


def 받아오기(주소, 글자로=True, 다시=2):
    """★ **천천히 묻고, 막히면 한 번 더 묻습니다** (2026-09-28)

    처음 검증 배포를 재 봤을 때 이렇게 나왔습니다.

        about.html      404
        css/style.css   404
        assets/js/tide.js  404

    그래서 「배포가 옛 파일을 지웠나」 싶었습니다. 아니었습니다.
    같은 주소를 curl 로 **하나씩** 치면 전부 200 이었습니다.

    **서버가 연달아 오는 요청을 막고 있었습니다.** 그런데
    막을 때 403 이 아니라 **404** 를 돌려줍니다. 그래서 검사기가
    「파일이 없다」고 잘못 말했습니다. 없는 것과 막힌 것은
    아주 다른 일인데, 겉보기가 같습니다.

    사람이 쪽을 볼 때는 이런 일이 안 납니다 — 한 쪽씩 보니까요.
    검사기만 몇십 개를 몰아치기 때문에 걸립니다.
    **검사기 때문에 난 탈을 사이트 탈로 읽으면 안 됩니다.**
    """
    import time
    import urllib.request
    import urllib.error
    # 서버가 숨 쉴 틈을 줍니다
    사이 = time.time() - _마지막에친때[0]
    if 사이 < 0.4:
        time.sleep(0.4 - 사이)
    _마지막에친때[0] = time.time()
    요청 = urllib.request.Request(
        주소, headers={'User-Agent': 'badagaja-deploy-check'})
    def 다시물어볼까(끝):
        # 404·403·429 는 **막힌 것**일 수 있습니다.
        # 정말 없는 것이면 쉬었다 물어도 같은 답이 옵니다 —
        # 한 번 더 묻는 값은 싸고, 헛 FAIL 의 값은 비쌉니다.
        if 다시 <= 0 or 끝.get('코드') not in (403, 404, 429, 503):
            return 끝
        import time as _t
        _t.sleep(1.5)
        return 받아오기(주소, 글자로=글자로, 다시=다시 - 1)

    try:
        with urllib.request.urlopen(요청, timeout=25) as f:
            몸 = f.read()
            return {'코드': f.status,
                    '글': 몸.decode('utf-8', 'ignore') if 글자로 else None,
                    '바이트': 몸,
                    '길이': len(몸)}
    except urllib.error.HTTPError as e:
        return 다시물어볼까({'코드': e.code, '글': None,
                            '바이트': None, '길이': 0})
    except Exception as e:
        return {'코드': None, '글': None, '바이트': None, '길이': 0,
                '탈': str(e)[:60]}


검증판표시 = '<!-- badagaja:stage -->'
def 검증판표시벗기기(글):
    """검증판이 덧붙인 것을 **벗기고** 견줍니다 (2026-09-29).

    ★ 왜 필요한가

      검증 배포(`_stage`)는 `engine/mark_stage.py` 가 쪽마다
      **noindex 와 빨간 띠**를 넣습니다. 그러면 서버 것이 내
      것과 다를 수밖에 없고, 20번은 **반드시 어김**이 납니다.

      그러면 **검증 배포로는 영영 20번을 확인할 수 없습니다.**
      「올려 봐야 안다」면서 올려 봐도 모르는 것입니다.

    ★ 무르게 하는 것이 아닙니다

      벗기는 것은 **mark_stage 가 넣는 바로 그것뿐**입니다.
      그 밖에 한 글자라도 다르면 여전히 잡습니다.
      운영 배포에는 이 표시가 아예 없으므로 아무 영향이 없습니다.
    """
    if 검증판표시 not in (글 or ''):
        return 글                       # 운영판 — 손대지 않습니다
    벗긴것 = 글.replace(검증판표시, '')
    벗긴것 = re.sub(r'<meta name="(?:robots|Yeti)" '
                    r'content="noindex,nofollow">', '', 벗긴것)
    # 빨간 띠 — 여는 div 부터 닫는 div 까지
    벗긴것 = re.sub(r'<div style="position:sticky;top:0;z-index:9999;'
                    r'background:#b3261e;.*?</div>', '', 벗긴것, flags=re.S)
    return 벗긴것


def 볼쪽들():
    """갈래마다 하나씩 — 416쪽을 다 물어볼 수는 없습니다."""
    나옴 = []
    for 무늬 in ('index.html', 'taean.html', 'chungnam.html',
                 'point/chungnam/taean_fishing.html',
                 'festival/index.html', 'fish/*.html', 'catch/*.html'):
        것 = sorted(glob.glob(os.path.join(NEW, 무늬)))
        것 = [x for x in 것 if not x.endswith('index.html')] or 것
        if 것:
            나옴.append(os.path.relpath(것[0], NEW).replace(os.sep, '/'))
    return 나옴


def 남기기로한것():
    d = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
    return [k for k in (d.get('남길것') or {}) if not k.startswith('_')]


def 주소로(길):
    if 길 == 'index.html':
        return SITE + '/'
    if 길.endswith('/index.html'):
        return '%s/%s' % (SITE, 길[:-len('index.html')])
    return '%s/%s' % (SITE, 길)


def 글자만(s):
    """견줄 때 쓰는 알맹이 — 서버가 조금 손대도 되는 것은 빼고 봅니다."""
    s = re.sub(r'<!--.*?-->', '', s or '', flags=re.S)
    return re.sub(r'\s+', ' ', s).strip()



def 여기가어디인가():
    """★ **재기 전에 「내가 어디를 재고 있는가」부터 묻습니다**

    (2026-09-28 바깥 검수 9차 숙제 3)

    오늘 20번 검사가 이렇게 말했습니다.

        assets/css/site.css   404
        about.html            404

    서버 탓인 줄 알고 반나절을 의심했습니다 — 카페24가 요청을 막나,
    해외 IP 를 막나, 구글봇도 못 읽는 것 아닌가. 진단 워크플로까지
    만들어 깃허브 러너에서 재 봤습니다. 전부 200 이었습니다.

    **검사기가 딴 곳을 묻고 있었습니다.**

        자산:  badagaja.com/assets/css/site.css     ← _stage 가 빠짐
        옛 쪽: badagaja.com/_stage/about.html       ← _stage 가 붙음

    카나리도 뮤테이션도 이걸 못 잡았습니다. 그것들은 「사이트에
    불량을 넣으면 잡는가」를 봅니다. 이것은 **「검사기가 애초에
    딴 데를 보고 있지 않은가」** 입니다. 다른 층입니다.

    그래서 재기 전에 쪽지를 한 장 열어 봅니다.
    안 나오면 **거기서 멈춥니다.** 딴 데를 재고 「괜찮다」고
    말하느니 「어디를 재는지 모르겠다」고 하는 편이 낫습니다.
    """
    print('[-1] 내가 재려는 곳이 정말 그 곳인가')
    print('      재려는 곳  %s' % SITE)

    # ★ 쪽지 이름을 **한 곳에서** 읽습니다 (2026-09-28)
    #   처음에는 세 파일에 따로 적어 두었습니다. .txt 를 .json 으로
    #   바꿀 때 세 곳을 다 고쳐야 했습니다 — 오늘 내내 잡던 그 뿌리입니다.
    from engine import mark_stage
    것 = 받아오기('%s/%s' % (SITE, mark_stage.이름표길), 다시=1)
    글 = 것.get('글') or ''
    if 것.get('코드') == 200 and 'badagaja-probe' in 글:
        어디 = ''
        try:
            어디 = (json.loads(글) or {}).get('where') or ''
        except ValueError:
            pass
        print('      쪽지가 말함  %s' % (어디 or '(안 적혀 있음)'))
        # 쪽지가 말하는 칸과 내가 재려는 주소가 맞는가
        if 어디 and 어디 not in SITE:
            print('  ✗ **딴 곳을 재고 있습니다** — 쪽지는 %s 라는데 '
                  '나는 %s 를 재려 합니다' % (어디, SITE))
            막음.append('검사기가 딴 곳을 재고 있습니다')
            return False
        print('  · 재려던 곳을 재고 있습니다')
        print('')
        return True

    if 검증자리:
        # 검증 자리에는 쪽지가 **반드시** 있어야 합니다.
        from engine import mark_stage
        print('  ✗ 쪽지가 안 열립니다 (%s)' % (것.get('코드') or '못받음'))
        print('      %s/%s' % (SITE, mark_stage.이름표길))
        print('      → 검증판이 제대로 안 올라갔거나,')
        print('        **내가 딴 곳을 재고 있습니다.**')
        print('        어느 쪽이든 여기서 멈춥니다 — 딴 데를 재고')
        print('        「괜찮다」고 말하느니 모른다고 하는 편이 낫습니다.')
        막음.append('어디를 재는지 확인하지 못했습니다')
        return False

    # 운영 뿌리에는 쪽지가 없습니다 (검증판에만 둡니다)
    print('      쪽지 없음 — 운영 뿌리를 재는 중입니다')
    print('')
    return True



def 남기기(나빴나):
    """★ **어디를 언제 어느 판으로 쟀는지** 남깁니다 (2026-09-28)

    바깥 검수 9차의 말: 「수동 통과를 자동 PASS 로 승격하지 마세요.
    사람이 확인한 사실과 기계가 확인한 사실을 섞지 마세요.」

    검증 자리에서 통과한 것은 **운영에서 통과한 것이 아닙니다.**
    그래서 20번은 운영에 올리기 전까지 NOT_TESTED 로 둡니다.
    다만 「검증 자리에서는 이 판으로 통과했다」는 사실은 남깁니다 —
    사람이 기억해서 보고하면 오늘 아침처럼 틀립니다.
    """
    import datetime
    import subprocess
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=20)
        커밋 = (r.stdout or '').strip() or '(모름)'
    except (OSError, subprocess.SubprocessError):
        커밋 = '(모름)'
    io.write_json(os.path.join(ROOT, 'tests', 'out', 'deployed.json'), {
        '_설명': ('서버에 물어본 결과. engine/check_deployed.py 가 남깁니다 '
                  '— 손으로 고치지 마세요'),
        '_읽는법': ('검증 자리에서 통과한 것은 운영에서 통과한 것이 '
                    '아닙니다. engine/gate.py 가 증거로만 씁니다.'),
        '잰때': datetime.datetime.now().isoformat(timespec='seconds'),
        '커밋': 커밋,
        '잰곳': SITE,
        '뿌리': 뿌리,
        '검증자리인가': 검증자리,
        '통과': not 나빴나,
        '막은것': list(막음),
    })


def main():
    바깥에물어볼까 = '--net' in sys.argv
    쪽들 = 볼쪽들()
    자산 = ['assets/css/site.css', 'assets/js/tide.js',
            'assets/js/ads.js', 'assets/js/ads-data.js',
            'favicon.ico', 'favicon.svg', 'apple-touch-icon.png']
    남길것 = 남기기로한것()

    if not 여기가어디인가():
        return 1

    print('올린 뒤 서버가 내 것과 같은가 (검수 지시 20)')
    print('  서버 %s' % SITE)
    print('')

    if not 바깥에물어볼까:
        print('무엇을 볼지만 보여 드립니다 — 실제로는 안 물어봤습니다')
        print('')
        print('  쪽 %d개' % len(쪽들))
        for x in 쪽들:
            print('      %s' % 주소로(x))
        print('  자산 %d개' % len(자산))
        for x in 자산:
            print('      %s/%s' % (SITE, x))
        print('  남기기로 한 것 %d갈래 (옛 중국어판이 씁니다)' % len(남길것))
        for x in 남길것[:5]:
            print('      %s/%s' % (SITE, x))
        print('')
        print('실제로 보려면 --net 을 붙이세요.')
        print('  ※ 이것은 「지킴」이 아닙니다. **아직 안 잰 것**입니다.')
        return 0

    # ── 0. 새 틀이 올라가 있는가
    #   아직 안 올렸으면 「다르다」가 당연합니다. 그것을 탈로 세면
    #   검사가 늘 빨간불이라 무뎌집니다. 먼저 갈라 봅니다.
    print('[0] 새 틀이 올라가 있는가')
    내첫쪽 = io.꼭읽기(os.path.join(NEW, 'index.html'))
    m = re.search(r'<title>(.*?)</title>', 내첫쪽, re.S)
    내제목 = m.group(1).strip() if m else ''
    것 = 받아오기(SITE + '/')
    서버제목 = ''
    if 것.get('글'):
        m2 = re.search(r'<title>(.*?)</title>', 것['글'], re.S)
        서버제목 = m2.group(1).strip() if m2 else ''
    올라갔나 = (내제목 and 내제목 == 서버제목)
    print('      내 것   %s' % 내제목)
    print('      서버    %s' % (서버제목 or '(못 받음)'))
    if not 올라갔나:
        print('  ~ **아직 안 올렸습니다.** 아래는 옛 사이트를 잰 것입니다.')
        print('      올린 뒤에 다시 돌려야 뜻이 있습니다.')
        알림.append('새 틀이 아직 안 올라가 있습니다')
    else:
        print('  · 새 틀이 올라가 있습니다')
    print('')

    # ── 0.5 ★ 판 지문 — 올린 것이 **내가 만든 바로 그것인가**
    #
    #   바깥 검수(2026-09-27 3차)
    #     「배포 버전 식별자를 배포물에 넣으세요. 내 PC 의 commit 과
    #       서버의 commit 을 직접 비교할 수 있습니다. 파일 하나만
    #       달라도 SHA-256 으로 잡히게 하면 더 좋습니다」
    #
    #   몇 쪽만 골라 보는 것은 짐작입니다. 여기서는 **파일마다의
    #   지문**을 통째로 견줍니다.
    print('[0.5] 올린 것이 내가 만든 바로 그것인가 (판 지문)')
    from engine import build_id
    내판 = build_id.읽기(NEW)
    if not 내판:
        알림.append('내 쪽에 판 지문이 없습니다 (build.py 를 다시 돌리세요)')
        print('      ~ 내 쪽에 site/build.json 이 없습니다')
    else:
        print('      내 것   커밋 %s · 파일 %d개 · %s'
              % (내판.get('커밋짧게'), 내판.get('파일수', 0),
                 내판.get('통지문', '')[:16]))
        것 = 받아오기(SITE + '/build.json')
        서버판 = None
        if 것.get('코드') == 200 and 것.get('글'):
            try:
                서버판 = json.loads(것['글'])
            except ValueError:
                서버판 = None
        if not 서버판:
            (알림 if not 올라갔나 else 막음).append(
                '서버에 판 지문이 없습니다 (%s)'
                % (것.get('코드') or 것.get('탈', '?')))
            print('      서버    (못 받음 — %s)'
                  % (것.get('코드') or 것.get('탈', '?')))
            print('      → 올릴 때 site/build.json 도 함께 올려야 합니다.')
        else:
            print('      서버    커밋 %s · 파일 %d개 · %s'
                  % (서버판.get('커밋짧게'), 서버판.get('파일수', 0),
                     서버판.get('통지문', '')[:16]))
            같나 = (내판.get('통지문') == 서버판.get('통지문'))
            # ★ **검증판에서는 판 지문을 잴 수 없습니다** (2026-09-29)
            #
            #   검증 배포는 mark_stage 로 쪽마다 표시를 넣은 **뒤에**
            #   판 지문을 만듭니다. 그래서 서버 지문은 검증판 기준이고
            #   내 것은 표시 없는 기준이라 **반드시 다릅니다.**
            #
            #   이것을 PASS 로 우회하지 않습니다(바깥 검수 12차 지침 6
            #   — 「잴 수 없으면 절대 PASS 하지 마」). **못 쟀다**고
            #   적고, 운영에 올린 뒤 진짜로 잽니다.
            검증판인가 = '/_stage' in SITE or SITE.rstrip('/').endswith('_stage')
            if not 같나 and 검증판인가:
                print('  ~ 검증판이라 판 지문을 잴 수 없습니다')
                print('      검증 배포는 쪽마다 noindex·띠를 넣은 **뒤에**')
                print('      지문을 만듭니다. 내 것과 다를 수밖에 없습니다.')
                print('      → **운영에 올린 뒤 진짜로 잽니다.**')
                알림.append('검증판이라 판 지문은 못 쟀습니다 '
                            '(운영 배포에서 잽니다)')
            elif 같나:
                print('  · 통지문이 같습니다 — 올린 것이 내가 만든 그것입니다')
            else:
                # 어느 파일이 다른지 **이름을 댑니다**
                내파일 = 내판.get('파일') or {}
                서버파일 = 서버판.get('파일') or {}
                빠짐 = sorted(set(내파일) - set(서버파일))
                더있음 = sorted(set(서버파일) - set(내파일))
                다름2 = sorted(k for k in set(내파일) & set(서버파일)
                               if 내파일[k] != 서버파일[k])
                (막음 if 올라갔나 else 알림).append(
                    '판 지문이 다릅니다 — 빠짐 %d · 더있음 %d · 내용다름 %d'
                    % (len(빠짐), len(더있음), len(다름2)))
                print('  ✗ 통지문이 다릅니다')
                print('      서버에 없는 것 %d · 서버에만 있는 것 %d '
                      '· 내용이 다른 것 %d'
                      % (len(빠짐), len(더있음), len(다름2)))
                for x in (빠짐[:3] + 다름2[:3]):
                    print('        %s' % x)
            if (내판.get('커밋') != 서버판.get('커밋')
                    and 내판.get('커밋') != '(모름)'):
                print('      ~ 커밋이 다릅니다 — 내 %s · 서버 %s'
                      % (내판.get('커밋짧게'), 서버판.get('커밋짧게')))
    print('')

    # ── 1. 쪽이 열리고 내 것과 같은가
    print('[1] 쪽이 열리고 내 것과 같은가')
    다름, 안열림 = [], []
    for 길 in 쪽들:
        것 = 받아오기(주소로(길))
        코드 = 것.get('코드')
        if 코드 != 200:
            안열림.append('%s — %s' % (길, 코드 or 것.get('탈', '?')))
            print('      %-42s ✗ %s' % (길, 코드 or '못 받음'))
            continue
        내것 = 글자만(io.read(os.path.join(NEW, 길), default=''))
        서버것 = 글자만(검증판표시벗기기(것.get('글') or ''))
        같나 = (내것 == 서버것)
        print('      %-42s %s %s'
              % (길, 코드, '·' if 같나 else '✗ 내 것과 다릅니다'))
        if not 같나:
            # 얼마나 다른지 짧게
            다름.append('%s — 내 것 %d자 · 서버 %d자'
                        % (길, len(내것), len(서버것)))
    if 안열림:
        막음.append('안 열리는 쪽 %d개' % len(안열림))
        print('  ✗ 안 열리는 쪽 %d개' % len(안열림))
        for x in 안열림[:4]:
            print('      %s' % x)
    if 다름:
        (막음 if 올라갔나 else 알림).append(
            '서버 것이 내 것과 다른 쪽 %d개%s'
            % (len(다름), '' if 올라갔나 else ' (아직 안 올렸으니 당연합니다)'))
        print('  ✗ 서버 것이 내 것과 다릅니다 %d개' % len(다름))
        for x in 다름[:4]:
            print('      %s' % x)
        print('      → 올리다 빠뜨렸거나, 옛 파일이 남아 있습니다.')
    if not (안열림 or 다름):
        print('  · 본 쪽이 모두 내 것과 같습니다')
    print('')

    # ── 2. 자산
    print('[2] 자산이 열리는가')
    자산탈 = []
    for 길 in 자산:
        것 = 받아오기('%s/%s' % (SITE, 길), 글자로=False)
        코드 = 것.get('코드')
        내크기 = (os.path.getsize(os.path.join(NEW, 길))
                  if os.path.exists(os.path.join(NEW, 길)) else None)
        맞나 = (코드 == 200 and 내크기 is not None
                and 것.get('길이') == 내크기)
        print('      %-30s %-5s %s'
              % (길, 코드 or '못받음',
                 '·' if 맞나 else '✗ 크기가 다릅니다 (내 것 %s · 서버 %s)'
                 % (내크기, 것.get('길이'))))
        if not 맞나:
            자산탈.append(길)
    if 자산탈:
        (막음 if 올라갔나 else 알림).append(
            '자산 %d개가 다릅니다%s'
            % (len(자산탈), '' if 올라갔나 else ' (아직 안 올렸으니 당연합니다)'))
    else:
        print('  · 자산이 모두 같습니다')
    print('')

    # ── 3. 옛 중국어판이 안 깨졌는가
    print('[3] 옛 중국어판이 안 깨졌는가%s'
          % ('  (뿌리 %s 에서 봅니다)' % 뿌리 if 검증자리 else ''))
    깨진것 = []
    # ★ 웹으로 보이면 안 되는 것 (2026-09-27)
    #   .htaccess 가 200 이면 **서버 설정이 그대로 새는 것**이라
    #   오히려 큰일입니다. 403·404 가 정상입니다.
    숨어야할것 = ('.htaccess',)
    볼것 = [x for x in 남길것 if not x.endswith('/')][:9]
    for 길 in 볼것:
        것 = 받아오기('%s/%s' % (뿌리, 길), 글자로=False)
        코드 = 것.get('코드')
        if 길 in 숨어야할것:
            숨었나 = 코드 in (403, 404)
            print('      %-46s %s  %s' % (길, 코드 or '못받음',
                                          '· 가려져 있습니다' if 숨었나
                                          else '✗ 웹으로 보입니다'))
            if not 숨었나:
                막음.append('%s 가 웹으로 보입니다 — 서버 설정이 샙니다' % 길)
            continue
        print('      %-46s %s' % (길, 코드 or '못받음'))
        if 코드 != 200:
            깨진것.append('%s — %s' % (길, 코드))
    # 중국어 쪽 하나를 실제로 열어 봅니다
    것 = 받아오기('%s/zh-cn/' % 뿌리)
    print('      %-46s %s' % ('zh-cn/', 것.get('코드') or '못받음'))
    if 것.get('코드') != 200:
        깨진것.append('zh-cn/ — %s' % 것.get('코드'))
    if 깨진것:
        막음.append('중국어판이 쓰는 것 %d개가 안 열립니다' % len(깨진것))
        print('  ✗ %d개가 안 열립니다' % len(깨진것))
        for x in 깨진것[:4]:
            print('      %s' % x)
        print('      → 배포가 옛 파일을 지웠을 수 있습니다.')
    else:
        print('  · 중국어판이 쓰는 것이 모두 열립니다')
    print('')

    # ── 4. sitemap · robots
    if 검증자리:
        # ★ 검증판에는 사이트맵이 **일부러 없습니다**
        #   (engine/mark_stage.py 가 지웁니다 — 실수로 낼 수 있어서)
        #   여기서 볼 것은 **검색에서 제대로 감춰졌는가** 입니다.
        #   감춤이 안 됐는데 올라가면 운영 쪽과 같은 글이 두 벌
        #   검색에 오릅니다. 둘 다 손해입니다.
        print('[4] 검증판이 검색에서 감춰졌는가')
        안감춰짐 = []
        for 길 in ('index.html', 'taean.html', 'fish/bollak.html'):
            것 = 받아오기('%s/%s' % (SITE, 길))
            글 = 것.get('글') or ''
            감춰짐 = 'noindex' in 글
            print('      %-30s %s  %s'
                  % (길, 것.get('코드') or '못받음',
                     '· 감춰져 있습니다' if 감춰짐 else '✗ 안 감춰졌습니다'))
            if not 감춰짐:
                안감춰짐.append(길)
        것 = 받아오기('%s/sitemap.xml' % SITE)
        코드 = 것.get('코드')
        print('      %-30s %s  %s'
              % ('sitemap.xml', 코드 or '못받음',
                 '· 없는 것이 맞습니다' if 코드 != 200
                 else '✗ 검증판 사이트맵이 남아 있습니다'))
        if 코드 == 200:
            막음.append('검증판에 사이트맵이 남아 있습니다')
        if 안감춰짐:
            막음.append('검증판 %d쪽이 검색에서 안 감춰졌습니다'
                        % len(안감춰짐))
        else:
            print('  · 검증판이 검색에 안 걸립니다')
    else:
        print('[4] sitemap · robots')
        for 길 in ('sitemap.xml', 'robots.txt'):
            것 = 받아오기('%s/%s' % (SITE, 길))
            코드 = 것.get('코드')
            print('      %-16s %s' % (길, 코드 or '못받음'))
            if 코드 != 200:
                막음.append('%s 가 안 열립니다' % 길)
    print('')

    남기기(bool(막음))

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 올린 뒤가 진짜입니다. 내 컴퓨터에서 멀쩡한 것과')
        print('    서버에서 멀쩡한 것은 다릅니다.')
        return 1 if '--strict' in sys.argv else 0
    if not 올라갔나:
        print('아직 안 올렸습니다 — **잰 것이 아닙니다.**')
        print('  올린 뒤 다시 돌리세요: python engine/check_deployed.py --net')
        return 0
    print('서버가 내 것과 같습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
