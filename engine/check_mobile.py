# -*- coding: utf-8 -*-
"""**휴대폰 폭에서 가로로 넘치는 것**을 찾습니다 (주인 규칙 23)

★ 왜 만들었나 (2026-09-28)

    주인 규칙 23 은 이렇게 못 박습니다.

        확인도 휴대폰(360·375px)과 PC(1280·1920px)에서 둘 다 합니다.

    그런데 **지금까지 한 번도 제대로 안 했습니다.**

    크롬 헤드리스에 `--window-size=375,800` 을 주면 창이 375px 가
    될 것 같지만, 실제로 쪽이 받는 폭은 **500px** 입니다.
    윈도에서 크롬 창이 그보다 좁아지지 못합니다. 375 를 줘도,
    360 을 줘도 500 입니다.

        --window-size=375,800   → clientWidth 500
        --window-size=360,800   → clientWidth 500

    그래서 제가 찍은 「휴대폰 사진」은 전부 **500px 로 그린 것을
    375px 그림에 담은 것**이었습니다. 오른쪽이 잘려 보였고,
    저는 그것을 「쪽이 통째로 넘친다」고 잘못 읽었습니다.

    진짜 375px 로 재 보니 넘치는 것은 **물때 칸 넷**뿐이었습니다.
    (옆으로 미는 띠였습니다 — 3×2 격자로 고쳤습니다)

★ 그래서 여기서는 **iframe 안에 넣어** 잽니다

    크롬 창은 좁아지지 않지만, 창 안의 iframe 은 얼마든지 좁게
    만들 수 있습니다. 그 안에서 쪽을 그리면 **진짜 375px** 입니다.

    완전한 기기 흉내는 아닙니다(터치·기기 문자열은 없습니다).
    그러나 **폭 때문에 깨지는 것**은 이것으로 다 잡힙니다.
    그리고 그것이 규칙 23 이 걱정하는 바로 그것입니다.

쓰는 법
    python engine/check_mobile.py
    python engine/check_mobile.py --strict     어기면 끝난값 1
    python engine/check_mobile.py --all        416쪽 전부
"""
import os
import re
import sys
import json
import glob
import shutil
import tempfile
import subprocess
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io        # noqa: E402
from engine import machine   # noqa: E402
from engine import _fake_tide  # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 주인 규칙 23 — 휴대폰은 360·375
#
# ★ **중간 폭을 빠뜨리고 있었습니다** (2026-09-30 주인 지적 「화면넘침」)
#
#   360·375 만 보고 「넘치는 것이 없습니다」 하고 넘어갔습니다.
#   그런데 주인 화면에서 물때 카드가 **가로로 넘쳐** 있었습니다.
#   폭이 **약 800px** 이었습니다 — 요즘 큰 휴대폰 가로,
#   태블릿, 폴드 펼침이 모두 이 구간입니다.
#
#   좁은 화면 규칙은 640px 이하에서만 걸렸고, 그 위는
#   PC 규칙(7열)이 그대로 걸려 칸이 좁아지다 못해 넘쳤습니다.
#   **아무도 안 보는 구간이 있으면 거기서 깨집니다.**
재볼폭들 = (360, 375, 480, 640, 768, 820, 1024)

# 검사 등급 (계약-21)
#   막음 — 고쳐야 하는 것. 배포를 막습니다
#   알림 — 살펴볼 것. 막지 않습니다
막음, 알림 = [], []
못잼 = []


def 크롬찾기():
    return machine.크롬찾기()


겉틀 = """<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#fff}
iframe{border:0;display:block}</style></head><body>
<iframe id="F" src="%s" width="%d" height="2400"></iframe>
<div id="R" style="display:none">?</div>
<script>
document.getElementById('F').addEventListener('load', function () {
  setTimeout(function () {
    var f = document.getElementById('F');
    var d = f.contentDocument, w = f.contentWindow;
    var W = d.documentElement.clientWidth;
    var 넘친것 = [];
    var 모두 = d.querySelectorAll('body *');
    for (var i = 0; i < 모두.length; i++) {
      var e = 모두[i];
      var r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (r.right > W + 1 || r.left < -1) {
        // 부모가 이미 넘쳤으면 자식은 안 셉니다 — **뿌리만** 찾습니다
        var p = e.parentElement, 부모넘침 = false;
        while (p && p !== d.body) {
          var pr = p.getBoundingClientRect();
          if (pr.right > W + 1 || pr.left < -1) { 부모넘침 = true; break; }
          p = p.parentElement;
        }
        if (부모넘침) continue;
        // 일부러 옆으로 밀게 만든 것은 봐줍니다
        var 밀수있나 = false, q = e;
        while (q && q !== d.body) {
          var st = w.getComputedStyle(q);
          if (st.overflowX === 'auto' || st.overflowX === 'scroll') {
            밀수있나 = true; break;
          }
          q = q.parentElement;
        }
        넘친것.push({
          t: e.tagName.toLowerCase(),
          c: (e.className || '').toString().slice(0, 34),
          l: Math.round(r.left), r: Math.round(r.right),
          w: Math.round(r.width),
          밀기: 밀수있나,
          글: (e.textContent || '').trim().slice(0, 24)
        });
      }
    }
    // ★ **가짜가 먹었는지 함께 봅니다** (2026-10-01)
    //   가짜 물때가 죽으면 그래프가 안 그려지고, 그러면 검사는
    //   **그래프 없는 쪽**을 재게 됩니다. 조용히 헛도는 것을 막습니다.
    var 그래프칸 = d.querySelector('.tide-graph');
    var 그래프 = 그래프칸 ? 그래프칸.querySelector('svg') : null;
    var out = document.getElementById('R');
    out.textContent = JSON.stringify({
      화면폭: W,
      몸폭: d.body.scrollWidth,
      그래프칸: !!그래프칸,
      그래프: !!그래프,
      그래프폭: 그래프 ? Math.round(그래프.getBoundingClientRect().width) : 0,
      넘침: 넘친것.slice(0, 10)
    });
  // ★ 900ms 는 짧습니다 — 물높이 그래프가 그려질 시간을 줍니다
  }, 2200);
});
</script></body></html>"""


def _가짜심은쪽(쪽길, 임시):
    """쪽을 베껴 **가짜 물때**를 심습니다.

    ★ 2026-10-01 — 이것이 없어서 주인이 먼저 찾으셨습니다.
      물높이 그래프가 1490px 로 커져 문서를 넓히고 있었는데,
      검사는 인터넷을 막고 재느라 **그래프가 없는 쪽**을 봤습니다.
      「넘치는 것이 없습니다」 하고 통과시켰습니다.

    ★ 인터넷을 여는 것이 아니라 **가짜를 심습니다.**
      바깥이 느린 날 검사가 흔들리면 그것은 시험이 아닙니다.

    ★ 같은 폴더에 둡니다 — 차림표·그림이 상대 경로라
      딴 데 두면 **차림표 없는 쪽**을 재게 됩니다.
    """
    글 = io.read(쪽길, default='')
    if not 글:
        return 쪽길
    심을것 = _fake_tide.심을글()
    if '</head>' in 글:
        글 = 글.replace('</head>', 심을것 + '</head>', 1)
    else:
        글 = 심을것 + 글
    새길 = os.path.join(os.path.dirname(쪽길), '__재기임시.html')
    io.write(새길, 글)
    임시.append(새길)
    return 새길


def 재기(쪽길, 폭):
    """iframe 안에 넣어 **진짜 그 폭으로** 그려 봅니다."""
    t = tempfile.mkdtemp(prefix='mobile-')
    임시 = []
    try:
        # ★ 가짜 물때를 심어 **그래프가 그려진 채로** 잽니다 (2026-10-01)
        쪽길 = _가짜심은쪽(쪽길, 임시)
        안길 = 'file:///' + os.path.abspath(쪽길).replace(os.sep, '/')
        겉 = 겉틀 % (안길, 폭)
        p = os.path.join(t, 'z.html')
        io.write(p, 겉)
        try:
            r = subprocess.run(
                machine.크롬앞머리() + [
                 '--window-size=%d,2600' % max(폭 + 140, 620),
                 '--allow-file-access-from-files',
                 # 바깥으로 안 나갑니다 — 인터넷에 흔들리면 시험이 아닙니다
                 '--host-resolver-rules=MAP * 127.0.0.1:1',
                 '--virtual-time-budget=11000', '--dump-dom',
                 'file:///' + p.replace(os.sep, '/')],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=180)
        except subprocess.TimeoutExpired:
            return None
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout or '', re.S)
        if not m:
            return None
        글 = _h.unescape(m.group(1))
        if 글.strip() in ('', '?'):
            return None
        try:
            return json.loads(글)
        except ValueError:
            return None
    finally:
        shutil.rmtree(t, ignore_errors=True)
        for x in 임시:
            try:
                os.remove(x)  # 계약-17 예외 — **방금 내가 만든** 임시 쪽만 지웁니다
            except OSError:
                pass


def 볼쪽들(전부):
    if 전부:
        return sorted(glob.glob(os.path.join(NEW, '**', '*.html'),
                                recursive=True))
    나옴 = []
    for 이름, 무늬 in (('첫화면', 'index.html'),
                       ('묶음', 'chungnam/index.html'),
                       ('권역', 'taean.html'),
                       # ★ 2026-09-28 — 풍경칸(.shots)이 있는 쪽입니다.
                       #   표본에 없는 짜임은 **앞으로도 못 잽니다.**
                       ('권역·풍경칸', 'seongsan.html'),
                       ('포인트목록', 'point/chungnam/taean_gleaning.html'),
                       ('해루질대상', 'catch/index.html'),
                       ('해루질하나', 'catch/bajirak.html'),
                       ('낚시하나', 'fish/gamseongdom.html'),
                       ('축제', 'festival/index.html'),
                       # ★ 2026-09-30 — **새 쪽을 표본에 안 넣었습니다**
                       #   채비 쪽 3갈래를 새로 짓고도 여기에 안 더해,
                       #   휴대폰 검사가 **한 번도 본 적 없이** 배포됐습니다.
                       #   바로 위 주석에 「표본에 없는 짜임은 앞으로도
                       #   못 잽니다」라고 적어 두고 같은 일을 했습니다.
                       #   채비 쪽은 **표·채비도·부품 카드**라 짜임이
                       #   다른 쪽과 아주 다릅니다 — 꼭 봐야 합니다.
                       ('채비목록', 'rig/index.html'),
                       ('채비하나', 'rig/float_rod.html'),
                       ('부품사전', 'rig/parts.html'),
                       # ★ 2026-09-30 — 에기를 두 채비로 가르며 생긴 새 쪽.
                       #   표본에 안 넣으면 영영 안 봅니다.
                       ('에기봉돌', 'rig/egi_sinker.html')):
        p = os.path.join(NEW, 무늬.replace('/', os.sep))
        if os.path.exists(p):
            나옴.append(p)

    # ★ **맨 위 쪽은 모두 봅니다** (2026-10-01 — 세 번째 같은 일)
    #
    #   2026-09-28 「표본에 없는 짜임은 앞으로도 못 잽니다」
    #   2026-09-30 채비 쪽을 새로 짓고 표본에 안 넣었습니다
    #   2026-10-01 rule·gear 를 새로 짓고 **또** 안 넣었습니다
    #
    #   손으로 적는 한 같은 일이 되풀이됩니다. 맨 위 쪽은 한 장
    #   짜리 특별한 쪽들이라 **다 보는 것이 맞습니다.** 폴더 안
    #   쪽들은 서로 짜임이 같으니 갈래마다 하나면 됩니다.
    #
    #   (56개 권역 쪽은 taean.html 하나로 갈음합니다 — 같은 틀)
    권역들 = set()
    try:
        import json
        판 = os.path.join(NEW, 'build.json')
        if os.path.isfile(판):
            with open(판, encoding='utf-8') as f:
                권역들 = {k for k in (json.load(f).get('파일') or {})
                           if k.endswith('.html') and '/' not in k}
    except Exception:
        pass
    맨위틀 = {'index.html', 'taean.html'}        # 이미 넣은 것
    # 권역 쪽은 모두 같은 틀이라 하나면 됩니다
    권역틀 = {x for x in 권역들
              if x not in ('index.html', 'rule.html', 'gear.html')}
    import re as _re
    for 이름 in sorted(권역들):
        if 이름 in 맨위틀:
            continue
        # 권역 쪽인지 — 자료에 그 권역이 있으면 권역 쪽입니다
        if 이름 in ('rule.html', 'gear.html', 'about.html',
                    'privacy.html', 'sources.html', 'photos.html',
                    'gear.html', 'copyright.html', 'muldae.html'):
            p = os.path.join(NEW, 이름)
            if os.path.exists(p) and p not in 나옴:
                나옴.append(p)
    for 무늬 in ('tide/index.html', 'guide/index.html'):
        p = os.path.join(NEW, 무늬.replace('/', os.sep))
        if os.path.exists(p) and p not in 나옴:
            나옴.append(p)
    return 나옴


def main():
    전부 = '--all' in sys.argv
    쪽들 = 볼쪽들(전부)
    if not 쪽들:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    print('휴대폰 폭에서 가로로 넘치는 것 (주인 규칙 23)')
    print('  ★ 크롬 창은 500px 보다 좁아지지 않습니다.')
    print('    그래서 **iframe 안에 넣어** 진짜 폭으로 그립니다.')
    print('  쪽 %d개 · 폭 %s' % (len(쪽들), ' · '.join('%dpx' % w
                                                      for w in 재볼폭들)))
    print('')

    for 폭 in 재볼폭들:
        print('[%dpx]' % 폭)
        for p in 쪽들:
            이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
            것 = 재기(p, 폭)
            if 것 is None:
                못잼.append('%s (%dpx)' % (이름, 폭))
                print('  □ %-40s 잴 형편이 안 됩니다' % 이름)
                continue
            진짜넘침 = [x for x in 것['넘침'] if not x.get('밀기')]
            민것 = [x for x in 것['넘침'] if x.get('밀기')]
            if 진짜넘침:
                막음.append('%s (%dpx) — %d곳' % (이름, 폭, len(진짜넘침)))
                print('  ✗ %-40s 몸 %dpx · 넘친 것 %d'
                      % (이름, 것['몸폭'], len(진짜넘침)))
                for x in 진짜넘침[:3]:
                    print('        <%s class="%s"> %d~%d (%dpx)  %s'
                          % (x['t'], x['c'], x['l'], x['r'], x['w'], x['글']))
            elif 민것:
                알림.append('%s (%dpx) — 옆으로 미는 것 %d'
                            % (이름, 폭, len(민것)))
                print('  ~ %-40s 몸 %dpx · 옆으로 미는 것 %d (일부러 그런 것)'
                      % (이름, 것['몸폭'], len(민것)))
            else:
                # ★ **가짜가 눈이 멀었는지** 함께 보입니다 (2026-10-01)
                #   그래프 칸이 있는데 안 그려졌으면, 검사는
                #   **그래프 없는 쪽**을 잰 것입니다 — 헛돕니다.
                꼬리 = ''
                if 것.get('그래프칸'):
                    꼬리 = ('  · 그래프 %dpx' % 것.get('그래프폭', 0)
                            if 것.get('그래프')
                            else '  ★ 그래프가 안 그려졌습니다')
                    if not 것.get('그래프'):
                        알림.append('%s (%dpx) — 그래프를 못 그려 '
                                    '덜 재었습니다' % (이름, 폭))
                print('  · %-40s 몸 %dpx%s'
                      % (이름, 것['몸폭'], 꼬리))
        print('')

    if 못잼:
        print('□ 잴 형편이 안 된 것 %d가지' % len(못잼))
        for x in 못잼[:4]:
            print('    %s' % x)
        print('  **틀린 것이 아니라 못 잰 것입니다.**')
        print('  크롬이 도는 자리에서 다시 재세요.')
        return 4 if '--strict' in sys.argv else 0

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림[:4]:
            print('  ~ %s' % x)
        print('')

    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음[:8]:
            print('  ✗ %s' % x)
        print('')
        print('  **휴대폰에서 글과 단추가 화면 밖으로 나갑니다.**')
        print('  손님은 옆으로 밀 수 있다는 것을 모릅니다.')
        print('  (주인 규칙 23 — 확인은 휴대폰과 PC 둘 다)')
        return 1 if '--strict' in sys.argv else 0

    print('휴대폰 폭에서 화면 밖으로 나가는 것이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
