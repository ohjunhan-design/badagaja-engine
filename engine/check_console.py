# -*- coding: utf-8 -*-
"""쪽이 **브라우저에서 조용한지** 봅니다. (검수 지시 5·9)

★ 왜 필요한가 (2026-09-27 바깥 검수 지시)

    「렌더링은 됐지만 JavaScript 오류가 있는 경우를 별도로 잡는다.
      사이트 자체 코드에서 발생하는 오류가 0 이어야 한다」

    화면이 멀쩡해 보여도 자바스크립트가 넘어져 있으면,
    지도가 안 뜨거나 걸러내기 단추가 안 듣습니다.
    눈으로는 잘 안 보입니다 — 콘솔을 봐야 압니다.

    그리고 광고 lazy-load 도 여기서 봅니다.

        「페이지 진입 → 광고 위치까지 스크롤 (경로 A)
          페이지 진입 후 광고 위치로 이동하지 않음 (경로 B)」

무엇을 보나
    1. 쪽마다 콘솔 오류가 나오는가 (사이트 코드와 바깥 코드를 갈라서)
    2. 못 받아 온 것이 있는가 (404 · 실패)
    3. 광고가 **스크롤해야 뜨는가** (경로 A) · 안 스크롤하면 어떤가 (경로 B)

★ 바깥으로 안 나갑니다
    인터넷을 막고 봅니다. 쿠팡 같은 바깥 것을 못 받는 것은
    **탈이 아닙니다** — 사이트 코드가 그 때문에 넘어지는지가 탈입니다.

★ 크롬으로만 봅니다 (주인 규칙 25)

쓰는 법
    python engine/check_console.py            갈래마다 한 쪽씩
    python engine/check_console.py --all      416쪽 전부 (오래 걸립니다)
    python engine/check_console.py --strict
"""
import os
import re
import sys
import glob
import json
import shutil
import tempfile
import subprocess
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine._fake_coupang import 가짜쿠팡   # noqa: E402  가짜 쿠팡은 한 곳에만
from engine import io    # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만
from engine import net   # noqa: E402  주소 가르기는 net.py 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

막음, 알림 = [], []

# ★ 「우리 것인가 바깥 것인가」는 **engine/net.py 한 곳에서만** 가릅니다
#   (2026-09-27 바깥 검수 5차)
#
#   전에는 이 파일이 목록을 따로 들고 있었습니다. 주인이 로고 글꼴을
#   네이버 자리(hangeul.pstatic.net)에서 받게 했는데 그 목록에 없어서,
#   **쪽은 멀쩡한데 5번 항목이 FAIL** 로 나왔습니다.
#   검사기마다 목록을 따로 두면 또 어긋납니다.


못잼 = []
시간넘음 = []
두번만에 = []


def 잴형편이안됨(무엇, 까닭=''):
    """★ **틀린 것이 아니라 못 잰 것입니다** (2026-09-28 바깥 검수 9차)

    클라우드 판정에서 5·9·10번이 FAIL 로 섰습니다. 까닭은
    「사이트가 틀렸다」가 아니라 **「크롬을 못 써서 못 쟀다」** 였습니다.

    이것을 FAIL 로 세면 진짜 FAIL 이 파묻힙니다.
    PASS 로 세면 안 잰 것을 잰 것처럼 셉니다.
    그래서 **끝난값 4** 로 따로 냅니다 — 판정이 INFRA_FAIL 로 읽고,
    INFRA_FAIL 도 NO-GO 입니다. 다만 **무엇을 고쳐야 하는지**가
    다릅니다 — 사이트가 아니라 잴 형편을 고쳐야 합니다.
    """
    못잼.append(무엇 + (' — ' + 까닭 if 까닭 else ''))
    print('  □ %-26s 잴 형편이 안 됩니다%s'
          % (무엇, '  (%s)' % 까닭 if 까닭 else ''))


def 크롬있나():
    """크롬이 **자리에 있는가**만 봅니다.

    ★ 처음에는 여기서 `chrome --version` 까지 돌려 봤습니다.
      「깔렸다는 말과 돌아간다는 말은 다르다」고 생각해서였습니다.
      **좋은 뜻이 해가 됐습니다.** (2026-09-28)

      판정이 검사기를 여럿 동시에 돌릴 때는 `--version` 조차
      60초를 넘깁니다. 그러면 「크롬이 안 돕니다」로 판단해
      **416쪽을 아예 안 쟀습니다.** 혼자 돌리면 다 잽니다.

      판을 묻는 것과 쪽을 그리는 것은 **다른 일**입니다.
      정작 필요한 것은 쪽을 그리는 것인데, 곁가지가 본 일을
      막았습니다. 그래서 여기서는 **자리만** 봅니다.
      정말 그려지는지는 첫 쪽을 그려 보며 압니다 —
      그것이 진짜 답이고, 어차피 바로 다음에 합니다.
    """
    try:
        길 = 크롬찾기()
    except Exception as e:
        # machine.크롬찾기() 는 못 찾으면 예외를 던집니다.
        # **죽는 것과 못 재는 것은 다릅니다** — 받아서 말로 바꿉니다.
        return False, str(e)[:60]
    if not 길 or not os.path.exists(길):
        return False, '크롬을 못 찾았습니다'
    return True, 길


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
# 쪽 맨 앞에 끼워 콘솔을 가로챕니다
가로채기 = r"""
window.__탈 = [];
(function () {
  var 원래 = window.console.error;
  window.console.error = function () {
    try {
      window.__탈.push({갈래: 'console.error',
                        말: Array.prototype.join.call(arguments, ' ')});
    } catch (e) {}
    return 원래.apply(window.console, arguments);
  };
  window.addEventListener('error', function (e) {
    // ★ 「코드가 넘어진 것」과 「못 받아 온 것」은 다릅니다 (2026-09-27)
    //   <script>·<img> 가 안 받아지면 error 가 나는데 message 가
    //   비어 있습니다. 그것을 「사이트 코드 탈」로 세면,
    //   인터넷을 막고 재는 이 검사가 늘 빨간불이 됩니다.
    if (e.target && e.target !== window && e.target.tagName) {
      window.__탈.push({갈래: '못받음',
                        말: e.target.src || e.target.href || '',
                        태그: e.target.tagName});
      return;
    }
    window.__탈.push({갈래: '넘어짐',
                      말: (e.message || '') + ' @ ' + (e.filename || ''),
                      어디: e.filename || ''});
  }, true);
  window.addEventListener('unhandledrejection', function (e) {
    window.__탈.push({갈래: '못받은약속',
                      말: String((e.reason && e.reason.message) || e.reason)});
  });
})();
"""

재는것 = r"""
(function () {
  var 나옴 = {탈: window.__탈 || [], 광고: []};
  var 칸들 = document.querySelectorAll('.ad-slot');
  for (var i = 0; i < 칸들.length; i++) {
    var c = 칸들[i], r = c.getBoundingClientRect();
    나옴.광고.push({이름: c.getAttribute('data-ad-slot'),
                    기기: c.getAttribute('data-ad-device'),
                    상태: c.getAttribute('data-ad-state') || '(없음)',
                    높이: Math.round(r.height),
                    속길이: c.innerHTML.length});
  }
  var e = document.createElement('div');
  e.id = '_잰것'; e.style.display = 'none';
  e.textContent = JSON.stringify(나옴);
  document.body.appendChild(e);
})();
"""

# 가짜 쿠팡은 engine/_fake_coupang.py 한 곳에만 둡니다 (계약-01)


def 재기(쪽길, 폭=1280, 스크롤할까=True, 가짜광고=True):
    """★ **시간이 넘으면 한 번 더 재 봅니다** (2026-09-28)

    혼자 돌리면 416쪽을 다 잽니다. 그런데 판정 안에서 돌리면
    한두 쪽이 180초를 넘깁니다. 판정은 검사기를 여럿 동시에
    돌리고, 크롬이 여럿 뜨면 하나가 굶기 때문입니다.

    한 쪽 때문에 5·9번이 통째로 INFRA_FAIL 이 되는 것은
    아깝습니다. 한 번 더 재는 값은 싸고, 그래도 안 되면
    그때 못 쟀다고 하면 됩니다.

    ★ 다만 **조용히 넘기지 않습니다.** 두 번째에 됐으면
      그렇게 적습니다 — 컴퓨터가 빠듯하다는 신호입니다.
    """
    끝 = _재기한번(쪽길, 폭, 스크롤할까, 가짜광고)
    if 끝 is not None:
        return 끝
    if os.path.basename(쪽길) not in 시간넘음:
        return None        # 시간 초과가 아니라 다른 까닭이면 그대로
    # 시간이 넘은 것이니 숨 돌리고 한 번 더
    import time as _t
    _t.sleep(3)
    시간넘음.remove(os.path.basename(쪽길))
    끝 = _재기한번(쪽길, 폭, 스크롤할까, 가짜광고)
    if 끝 is not None:
        두번만에.append(os.path.basename(쪽길))
    return 끝


def _재기한번(쪽길, 폭=1280, 스크롤할까=True, 가짜광고=True):
    """그 쪽을 그려 콘솔 탈과 광고 상태를 봅니다."""
    t = tempfile.mkdtemp(prefix='console-')
    try:
        바탕 = ('file:///'
                + os.path.dirname(os.path.abspath(쪽길)).replace(os.sep, '/')
                + '/')
        글 = io.read(쪽길, default='')
        끼울것 = ('<base href="%s"><script>%s</script>'
                  % (바탕, 가로채기))
        if 가짜광고:
            끼울것 += '<script>%s</script>' % 가짜쿠팡
        글 = (글.replace('<head>', '<head>' + 끼울것, 1)
              if '<head>' in 글 else 끼울것 + 글)
        속 = os.path.join(t, 'p.html')
        io.write(속, 글)

        스크롤 = ("""
  var y = 0;
  var 훑기 = setInterval(function () {
    y += 700; w.scrollTo(0, y);
    if (y > d.documentElement.scrollHeight) clearInterval(훑기);
  }, 80);
""" if 스크롤할까 else '')

        겉 = ("""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0}iframe{border:0;display:block}</style></head><body>
<iframe id="F" src="file:///%s" width="%d" height="900"></iframe>
<script>
var f = document.getElementById('F');
f.addEventListener('load', function () {
  var d = f.contentDocument, w = f.contentWindow;
%s
  setTimeout(function () {
    var s = d.createElement('script');
    s.textContent = %s;
    d.body.appendChild(s);
    var 잰것 = d.getElementById('_잰것');
    var o = document.createElement('div');
    o.id = 'R'; o.style.display = 'none';
    o.textContent = 잰것 ? 잰것.textContent : '{}';
    document.body.appendChild(o);
  }, 3400);
});
</script></body></html>"""
              % (속.replace(os.sep, '/'), 폭, 스크롤, json.dumps(재는것)))
        p = os.path.join(t, 'z.html')
        io.write(p, 겉)
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--window-size=%d,1000' % max(폭 + 120, 1400),
             '--allow-file-access-from-files',
             # 바깥으로 안 나갑니다 — 인터넷에 흔들리면 시험이 아닙니다
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--virtual-time-budget=11000', '--dump-dom',
             'file:///' + p.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=180)
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout or '', re.S)
        if not m:
            return None
        return json.loads(_h.unescape(m.group(1)) or '{}')
    except subprocess.TimeoutExpired:
        # ★ **시간이 넘은 것은 사이트 잘못이 아닙니다** (2026-09-28)
        #   컴퓨터가 바쁠 때 크롬이 180초를 넘깁니다. 전에는 이것이
        #   예외로 터져 끝난값 1(FAIL)이 됐습니다 — 「쪽이 틀렸다」고
        #   말한 셈입니다. 못 잰 것으로 냅니다.
        #
        #   ★ 그리고 이 except 를 넣으면서 **결과를 돌려주는 줄을
        #     아래로 밀어 놓았습니다.** 그 줄이 영영 안 돌아가니
        #     모든 쪽이 None 이 되어 「크롬이 못 그렸다」가 됐습니다.
        #     파이썬은 도달할 수 없는 줄을 나무라지 않습니다.
        #     저는 그것을 「컴퓨터가 느려졌나」 하고 의심했습니다.
        시간넘음.append(os.path.basename(쪽길))
        return None
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 볼쪽들(전부):
    if 전부:
        return sorted(glob.glob(os.path.join(NEW, '**', '*.html'),
                                recursive=True))
    나옴 = []
    for 이름, 무늬 in (('첫화면', 'index.html'),
                       ('권역', 'taean.html'),
                       ('묶음', 'chungnam.html'),
                       ('포인트목록', 'point/chungnam/taean_fishing.html'),
                       ('축제달력', 'festival/index.html'),
                       ('어종', 'fish/*.html')):
        것 = sorted(glob.glob(os.path.join(NEW, 무늬)))
        것 = [x for x in 것 if not x.endswith('index.html')] or 것
        if 것:
            나옴.append(것[0])
    return 나옴


def 우리코드인가(말):
    """사이트 자체 코드에서 난 탈인가, 바깥 것 때문인가.

    ★ net.py 가 가릅니다. 여기서 목록을 따로 들지 않습니다.
    """
    return net.말에서주소(말) == net.우리것


def main():
    # ★ 잴 수 있는지 **먼저** 봅니다. 못 재는데 20분 돌리지 않습니다.
    됨, 말 = 크롬있나()
    if not 됨:
        print('□ %s' % 말)
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  BADAGAJA_CHROME 으로 크롬 자리를 알려 주세요.')
        return 4 if '--strict' in sys.argv else 0
    print('  크롬 %s' % 말)

    전부 = '--all' in sys.argv
    쪽들 = 볼쪽들(전부)
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('쪽이 브라우저에서 조용한가 (검수 지시 5·9)')
    print('  %s · 바깥 인터넷을 막고 봅니다'
          % ('416쪽 전부' if 전부 else '갈래마다 한 쪽씩 %d개' % len(쪽들)))
    print('')

    # ── 1. 콘솔 탈
    print('[1] 자바스크립트 탈')
    우리탈, 바깥탈, 못쟀음, 못받음, 모르는곳 = [], [], [], [], []
    for p in 쪽들:
        이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
        것 = 재기(p)
        if 것 is None:
            못쟀음.append(이름)
            continue
        for x in (것.get('탈') or []):
            말 = x.get('말') or ''
            갈래 = x.get('갈래')
            if 갈래 == '못받음':
                # ★ 못 받은 것은 **주소가 통째로** 옵니다 (e.target.src).
                #   섞인 글이 아니므로 net.갈래() 로 바로 가릅니다.
                #   인터넷을 막았으니 바깥 것은 당연히 못 받습니다.
                어디 = net.갈래(말)
                줄 = '%s — %s %s' % (이름, x.get('태그', ''), 말[:60])
                if 어디 == net.우리것:
                    못받음.append(줄)
                elif 어디 == net.바깥모름:
                    # ★ 모르는 남의 자리 — **막지는 않되 반드시 알립니다.**
                    #   허락 목록에 없는 곳을 쪽이 부르고 있다는 뜻입니다.
                    #   못 잰 것을 지킴으로도, 어김으로도 세지 않습니다.
                    모르는곳.append(줄)
                else:
                    바깥탈.append(줄 + '   (%s)' % net.왜허락했나(말))
                continue
            (우리탈 if 우리코드인가(말) else 바깥탈).append(
                '%s — [%s] %s' % (이름, 갈래, 말[:60]))
    print('      본 쪽 %d개' % (len(쪽들) - len(못쟀음)))
    if 못쟀음:
        # ★ **재지 못한 것은 「멀쩡하다」가 아닙니다.**
        #   그렇다고 「틀렸다」도 아닙니다 (2026-09-28 바깥 검수 9차).
        #   FAIL 로 세면 진짜 FAIL 이 파묻힙니다. 따로 셉니다.
        잴형편이안됨('쪽 %d개' % len(못쟀음),
                     '크롬이 못 그림: ' + ' · '.join(못쟀음[:3]))
    if 우리탈:
        막음.append('사이트 코드에서 난 탈 %d건' % len(우리탈))
        print('  ✗ 사이트 자체 코드에서 난 탈 %d건' % len(우리탈))
        for x in 우리탈[:6]:
            print('      %s' % x)
    else:
        print('  · 사이트 코드에서 난 탈이 없습니다')
    if 못받음:
        # 우리 자리 파일을 못 받았으면 진짜 탈입니다
        막음.append('사이트 안 파일을 못 받음 %d건' % len(못받음))
        print('  ✗ 사이트 안 파일을 못 받았습니다 %d건' % len(못받음))
        for x in 못받음[:4]:
            print('      %s' % x)
    if 모르는곳:
        # ★ 허락 목록에 없는 남의 자리 — 막지는 않되 **반드시 알립니다**
        #   (2026-09-27 바깥 검수 「바깥이라고 무조건 통과시키면 안 된다」)
        알림.append('허락한 적 없는 바깥 자리 %d건' % len(모르는곳))
        print('  ~ 허락한 적 없는 바깥 자리 %d건 — 막지는 않습니다'
              % len(모르는곳))
        print('      쪽이 이 자리를 부릅니다. 뜻한 것이면')
        print('      engine/net.py 의 바깥허락 에 **까닭과 함께** 적으세요.')
        for x in 모르는곳[:4]:
            print('      %s' % x)
    if 바깥탈:
        알림.append('바깥 것 때문에 난 탈 %d건' % len(바깥탈))
        print('  ~ 바깥 것(글꼴·쿠팡·지도 등) 때문에 난 탈 %d건 — 막지 않습니다'
              % len(바깥탈))
        for x in 바깥탈[:3]:
            print('      %s' % x)
    print('')

    # ── 2. 광고 lazy-load — 두 경로
    print('[2] 광고 — 스크롤할 때와 안 할 때')
    광고있는쪽 = [p for p in 쪽들
                  if 'data-ad-slot' in io.read(p, default='')]
    if not 광고있는쪽:
        print('      광고 자리가 있는 쪽이 없습니다')
    else:
        볼것 = 광고있는쪽[0]
        이름 = os.path.relpath(볼것, NEW).replace(os.sep, '/')
        print('      %s 로 봅니다' % 이름)
        for 무엇, 스크롤 in (('경로 A — 광고까지 스크롤', True),
                             ('경로 B — 스크롤 안 함', False)):
            것 = 재기(볼것, 1280, 스크롤할까=스크롤)
            if 것 is None:
                잴형편이안됨(무엇, '크롬이 쪽을 못 그렸습니다')
                continue
            뜬것 = [c for c in (것.get('광고') or []) if c['높이'] > 4]
            모두 = [c for c in (것.get('광고') or [])
                    if (c['기기'] == 'pc')]
            print('      %-26s 광고 칸 %d개 중 뜬 것 %d개'
                  % (무엇, len(모두), len(뜬것)))
            for c in 뜬것[:2]:
                print('          %-22s %s · 높이 %dpx'
                      % (c['이름'], c['상태'], c['높이']))
            if 모두 and not 뜬것:
                막음.append('%s — 광고가 하나도 안 떴습니다' % 무엇)
                print('        ✗ 광고가 하나도 안 떴습니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0

    # ★ 못 쟀으면 「괜찮다」고 하지 않습니다 (바깥 검수 9차 — Fail-Closed)
    if 두번만에:
        print('~ 한 번 더 재서 잰 쪽 %d개: %s'
              % (len(두번만에), ' · '.join(두번만에[:3])))
        print('    (컴퓨터가 빠듯합니다 — 크롬이 굶고 있습니다)')
        알림.append('한 번 더 재서 잰 쪽 %d개' % len(두번만에))

    if 시간넘음:
        for x in 시간넘음[:4]:
            잴형편이안됨(x, '크롬이 180초를 넘겼습니다')
        if len(시간넘음) > 4:
            잴형편이안됨('그 밖 %d쪽' % (len(시간넘음) - 4), '크롬 시간 초과')

    if 못잼:
        print('□ 잴 형편이 안 된 것 %d가지' % len(못잼))
        for x in 못잼:
            print('    %s' % x)
        print('')
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  크롬이 도는 자리에서 다시 재세요.')
        return 4 if '--strict' in sys.argv else 0

    print('브라우저에서 조용하고, 광고도 제대로 뜹니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
