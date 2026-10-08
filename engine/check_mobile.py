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
# 표본에 꼭 들어야 하는 쪽은 samples 한 곳에서 가립니다 (2026-10-08)
from engine import samples   # noqa: E402

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
<!-- ★ **폭을 한꺼번에 잽니다** (2026-10-06 주인 지시)
     주인 — 「판정시간을 단축시킬 수 있는 방법을 찾아봐 … 3분 이내로」

     재 보니 이 검사기 하나가 판정 시간의 **열에 여덟**을 먹고
     있었습니다. 까닭은 간단했습니다 —

         for 폭 in 7가지:
             for 쪽 in 38개:
                 크롬을 띄운다          ← 266번 · 한 번 3.5초

     쪽 하나를 **일곱 번 다시 그리느라** 15분이 걸렸습니다.
     한 쪽에 iframe 일곱을 나란히 두면 **크롬은 38번**이면
     됩니다. 그리는 일은 그대로이고 띄우는 품만 덜어 냅니다.

     가짜 물때를 심은 사본도 쪽마다 한 번만 만들면 됩니다 —
     전에는 폭마다 만들었다 지웠습니다. -->
%s
<div id="R" style="display:none">?</div>
<script>
var 틀들 = %s;          /* [[id, 폭], …] */
var 남은 = 틀들.length;
var 모은것 = {};

function 하나재기(아이디, 폭, 열쇠) {
  var f = document.getElementById(아이디);
  var d = f.contentDocument, w = f.contentWindow;
  var W = d.documentElement.clientWidth;
    var 넘친것 = [];
    var 모두 = d.querySelectorAll('body *');
    for (var i = 0; i < 모두.length; i++) {
      var e = 모두[i];
      // ★ **SVG 안쪽은 세지 않습니다** (2026-10-01)
      //
      //   제주 묶음 쪽이 「넘침 3곳」으로 걸렸는데, 보니 로고 안의
      //   <rect>·<path> 였습니다. SVG 는 viewBox 로 **제 안에서
      //   잘립니다** — 안쪽 모양이 아무리 커도 화면 밖으로 안
      //   나갑니다. 겉의 <svg> 만 보면 됩니다.
      //
      //   재는 자리가 틀리면 **없는 잘못을 잡고** 진짜 잘못은
      //   그 소리에 묻힙니다.
      if (e.ownerSVGElement) continue;
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
    // ★ **접힌 칸 안이면 안 그려진 것이 맞습니다** (2026-10-02)
    //   /tide/ 는 그래프를 <details class="tide-detail"> 안에 둡니다.
    //   손님이 펼쳐야 그립니다. 그런데 검사는 쪽을 열기만 하므로
    //   「그래프가 안 그려졌습니다」라고 **거짓으로** 알렸습니다.
    //   접혀 있는지 보고, 그렇다면 탓하지 않습니다.
    var 접힘 = false;
    if (그래프칸 && !그래프) {
      var 위 = 그래프칸.closest('details');
      접힘 = !!(위 && !위.open);
    }
    // ★ **주소로 들어온 상세가 첫 화면에 있는가** (2026-10-08)
    //
    //   `?point=` 로 들어오면 그 포인트를 보러 온 것입니다. 그런데
    //   휴대폰(375×812)에서 재 보니 패널이 **750px 자리**에 있어
    //   **0.92 화면**을 내려야 보였습니다. PC 는 패널이 지도
    //   오른쪽이라 바로 보이는데, 휴대폰은 지도 아래로 갑니다.
    //   주소를 공유받은 분은 머리글과 지도만 보고 「왜 아무것도
    //   없지」 합니다.
    //
    //   ★ **「안 잘린다」가 기준이 아닙니다** (규칙 6-2).
    //     넘침은 하나도 없었고 검사기는 모두 통과했습니다.
    //     눈으로 봐야 잡혔습니다. 그래서 **재는 것**으로 옮깁니다.
    //     기억 「스크롤은 두 숫자로」 — 「몇 화면 내려야」를 셉니다.
    //   ★ **iframe 높이로 세면 안 됩니다** (2026-10-08에 겪음)
    //     iframe 을 2400px 로 띄워 재는데, `innerHeight` 를 그대로
    //     쓰면 「한 화면」이 2400px 가 됩니다. 750px 자리에 있는
    //     패널이 0.31 화면으로 셈돼 **통과**했습니다. 끌어올리기를
    //     일부러 꺼서 심었는데도 안 잡혀 알았습니다.
    //     진짜 휴대폰은 812px 입니다. **사람이 보는 높이**로 셉니다.
    var 진짜높이 = 812;
    var 패널 = d.querySelector('.pp');
    var 몇화면 = null;
    if (패널 && !패널.hidden) {
      var pr = 패널.getBoundingClientRect();
      var 꼭대기 = pr.top + (w.scrollY || 0);
      몇화면 = Math.round((꼭대기 / 진짜높이) * 100) / 100;
    }
    모은것[열쇠] = {
      화면폭: W,
      몸폭: d.body.scrollWidth,
      그래프칸: !!그래프칸,
      그래프: !!그래프,
      접힘: 접힘,
      그래프폭: 그래프 ? Math.round(그래프.getBoundingClientRect().width) : 0,
      패널있나: !!(패널 && !패널.hidden),
      패널몇화면: 몇화면,
      넘침: 넘친것.slice(0, 10)
    };
}

/* ★ **모두 그려진 뒤 한 번에 잽니다** (2026-10-06)
     iframe 일곱이 제각기 끝납니다. 하나가 끝날 때마다 재면
     아직 안 끝난 것이 섞입니다. 다 끝난 것을 세어 기다립니다.
     ★ 900ms 는 짧습니다 — 물높이 그래프가 그려질 시간을 줍니다 */
function 다왔나() {
  남은 -= 1;
  if (남은 > 0) { return; }
  setTimeout(function () {
    for (var i = 0; i < 틀들.length; i++) {
      /* ★ 열쇠는 **쪽번호|폭** 입니다 (2026-10-07)
         한 판에 쪽이 여럿 들어가므로 폭만으로는 못 가립니다. */
      var 열쇠 = String(틀들[i][2]) + '|' + String(틀들[i][1]);
      try { 하나재기(틀들[i][0], 틀들[i][1], 열쇠); }
      catch (e) { 모은것[열쇠] = null; }
    }
    var R = document.getElementById('R');
    R.textContent = JSON.stringify(모은것);
    /* ★ **계약된 측정이 모두 끝났다**는 신호 (2026-10-07 바깥 검수)
       「『무언가 나왔다』가 아니라 **『계약된 측정이 모두 끝났다』**를
         봅니다. 결과가 **일부만 그려져도 DOM 은 비어 있지 않을 수**
         있어서, 『비었나?』만 보면 **거짓 통과가 가능**합니다」
       이 신호가 없으면 **긴 예산으로 한 번 더** 돕니다. */
    R.setAttribute('data-다잿음', String(틀들.length));
  }, 2200);
}

for (var i = 0; i < 틀들.length; i++) {
  document.getElementById(틀들[i][0])
          .addEventListener('load', 다왔나);
}
</script></body></html>"""


def _첫포인트(쪽길):
    """그 쪽의 **첫 포인트 아이디**. 포인트 쪽이 아니면 None.

    ★ 쪽 종류를 **쪽이 말하게** 합니다 (기억 「쪽 종류는 쪽이
      말하게」). 폴더나 파일 이름으로 가리면 새 쪽마다 오해합니다.
      `#쪽자료` 에 포인트 목록이 있고 상세 패널이 켜져 있으면
      포인트 쪽입니다.
    """
    try:
        글 = io.read(쪽길, default='') or ''
    except Exception:                                 # noqa: BLE001
        return None
    m = re.search(
        r'<script type="application/json" id="쪽자료">(.*?)</script>',
        글, re.S)
    if not m:
        return None
    try:
        자 = json.loads(m.group(1))
    except ValueError:
        return None
    if not 자.get('상세패널'):
        return None
    것들 = 자.get('포인트') or []
    return (것들[0].get('id') if 것들 else None)


def _가짜심은쪽(쪽길, 임시, 둘자리=None):
    """쪽을 베껴 **가짜 물때**를 심습니다.

    ★ **`site/` 안에 만들지 않습니다** (2026-10-06 — 네 번 당했습니다)

      전에는 그 쪽과 **같은 폴더**에 `__재기임시.html` 을 만들었다
      지웠습니다. 차림표·그림이 상대 경로라 딴 데 두면 차림표
      없는 쪽을 재게 되기 때문이었습니다.

      그런데 그 몇 초 사이에 다른 검사기가 `site/` 를 보면 탈이
      납니다. 오늘만 네 번입니다 —

          ① 아이콘 전수 · 미작성 쪽 고아 링크   (읽다가)
          ② check_assets                      (읽다가)
          ③ check_seo — 제목·설명·canonical    (읽다가)
          ④ 뮤테이션 · 416쪽 렌더링             (**베끼다가**)

      ①②③ 은 `io.쪽들()` 로 막았습니다. 그런데 ④ 는 `copytree` 로
      통째로 베끼다가 **그 파일이 중간에 사라져** 터졌습니다.
      읽는 쪽을 아무리 고쳐도 베끼는 쪽은 막을 수 없습니다.

      **자리를 옮기는 것이 뿌리입니다.** `<base href>` 를 넣으면
      딴 자리에 두어도 상대 경로가 원래 쪽을 가리킵니다.
      `site/` 는 한 글자도 안 늘어납니다.

    ★ 2026-10-01 — 이것이 없어서 주인이 먼저 찾으셨습니다.
      물높이 그래프가 1490px 로 커져 문서를 넓히고 있었는데,
      검사는 인터넷을 막고 재느라 **그래프가 없는 쪽**을 봤습니다.
      「넘치는 것이 없습니다」 하고 통과시켰습니다.

    ★ 인터넷을 여는 것이 아니라 **가짜를 심습니다.**
      바깥이 느린 날 검사가 흔들리면 그것은 시험이 아닙니다.

    ★ ~~같은 폴더에 둡니다~~ → **`<base href>` 로 자리를 가리킵니다**
      차림표·그림이 상대 경로라 딴 데 두면 차림표 없는 쪽을
      재게 됩니다. 그래서 전에는 같은 폴더에 두었습니다.
      `<base>` 한 줄이면 딴 자리에서도 원래 쪽을 가리킵니다.
    """
    글 = io.read(쪽길, default='')
    if not 글:
        return 쪽길
    심을것 = _fake_tide.심을글()

    # ★ **`<base>` 가 맨 앞이어야 합니다**
    #   `<base>` 보다 앞에 적힌 상대 주소는 **그 전 기준**으로
    #   풀립니다. 차림표가 `<head>` 첫 줄에 있으므로 반드시
    #   `<head>` 바로 뒤에 넣습니다.
    바탕 = ('file:///'
            + os.path.dirname(os.path.abspath(쪽길)).replace(os.sep, '/')
            + '/')
    기준 = '<base href="%s">' % 바탕
    if '<head>' in 글:
        글 = 글.replace('<head>', '<head>' + 기준, 1)
    else:
        글 = 기준 + 글

    if '</head>' in 글:
        글 = 글.replace('</head>', 심을것 + '</head>', 1)
    else:
        글 = 심을것 + 글

    # ★ **`site/` 밖에 둡니다** — 다른 검사기가 베끼다 터지지 않게
    자리 = 둘자리 or tempfile.mkdtemp(prefix='mobile-쪽-')
    # ★ **이름이 겹치면 안 됩니다** (2026-10-07)
    #
    #   한 판에 쪽을 여럿 넣게 되면서 이 자리가 탈이 났습니다.
    #   이름이 `재기임시.html` 로 **고정**이라, 한 묶음의 쪽 셋이
    #   **서로 덮어써서 셋 다 마지막 쪽을 보고 있었습니다.**
    #   about.html 에 없는 물때 그래프가 보였습니다.
    #
    #   `tests/mobile_ab.py` 가 259칸 가운데 **100칸이 다르다**고
    #   잡아 주었습니다. 묶음을 넣기 전에 기준선을 떠 두지
    #   않았다면 **조용히 거짓 통과**했을 것입니다.
    새길 = os.path.join(자리, '재기임시.html')
    번 = 0
    while os.path.exists(새길):
        번 += 1
        새길 = os.path.join(자리, '재기임시-%d.html' % 번)
    io.write(새길, 글)
    임시.append(새길)
    return 새길


def 묶음크기():
    """**한 판에 몇 쪽**을 넣을까 (2026-10-07 바깥 검수).

    「1 batch = 3쪽 × 7폭 = iframe 21개 **부터**입니다 …
      5쪽 × 7폭 = 35 iframe 도 기술적으로 가능하지만, 지금 검사
      목적이 『가로 넘침을 놓치지 않는 것』이라 **렌더 타이밍과
      메모리 안정성을 먼저 확인해야** 합니다」

    ★ **속도보다 결과 동일성이 먼저입니다.**
      `tests/mobile_ab.py --견주기` 가 259칸을 모두 견줍니다.
      한 칸이라도 다르면 그 크기는 **탈락**입니다.

    시험할 때만 환경변수로 바꿉니다 — 평소에는 손대지 않습니다.
    """
    try:
        것 = int(os.environ.get('BADAGAJA_MOBILE_BATCH') or 3)
    except ValueError:
        것 = 3
    return max(1, min(것, 12))


def 재기여러폭(쪽길, 폭들):
    """쪽 하나를 여러 폭으로 — **재기여러쪽() 에 맡깁니다**."""
    return 재기여러쪽([쪽길], 폭들).get(쪽길) or dict(
        (폭, None) for 폭 in 폭들)


def 재기여러쪽(쪽길들, 폭들):
    """쪽 하나를 **여러 폭으로 한 번에** 잽니다 (2026-10-06).

    돌려주는 것: {폭: 잰것 또는 None}

    ★ 왜 한 번에 재나 — 판정 시간의 83%가 여기였습니다
      전에는 `재기(쪽길, 폭)` 이 폭마다 크롬을 띄웠습니다.
      38쪽 × 7폭 = **266번**, 한 번 3.5초라 15분이 걸렸습니다.
      iframe 을 폭 수만큼 나란히 두면 크롬은 **쪽마다 한 번**
      이면 됩니다. 그리는 일은 그대로이고 띄우는 품만 덜어 냅니다.

    ★ 창은 가장 넓은 폭에 맞춥니다
      창보다 넓은 iframe 은 제 폭대로 못 그립니다.
    """
    t = tempfile.mkdtemp(prefix='mobile-')
    임시 = []
    try:
        # ★ 가짜 물때를 심어 **그래프가 그려진 채로** 잽니다 (2026-10-01)
        #   쪽마다 **한 번만** 만듭니다 — 전에는 폭마다 만들었습니다.
        #   자리는 `t`(임시 폴더)입니다 — `site/` 를 안 건드립니다.
        # ★ **쪽 × 폭을 모두 한 판에** 늘어놓습니다 (2026-10-07)
        #   전에는 쪽마다 크롬을 띄워 37번이었습니다. 바닥을 재니
        #   크롬 37번이 29.1초로 **전체의 100%** 였습니다.
        #   예산을 줄여도 안 줄었던 까닭이 이것입니다.
        #
        #   ※ 묶음 크기는 **속도보다 결과 동일성이 먼저**입니다
        #     (바깥 검수). tests/mobile_ab.py 로 259칸을 견줍니다.
        칸들 = []
        for 쪽번 in range(len(쪽길들)):
            심은것 = _가짜심은쪽(쪽길들[쪽번], 임시, 둘자리=t)
            안길 = 'file:///' + os.path.abspath(심은것).replace(os.sep, '/')
            # ★ **포인트 쪽은 상세를 연 채로 잽니다** (2026-10-08)
            #   `?point=` 를 안 붙이면 패널이 닫힌 쪽만 재게 되고,
            #   「상세가 첫 화면에 있는가」는 **영영 안 돕니다.**
            #   표본에 없는 짜임은 앞으로도 못 잽니다 (이 파일이
            #   세 번 당한 그 잘못입니다).
            첫것 = _첫포인트(쪽길들[쪽번])
            if 첫것:
                안길 += '?point=' + 첫것
            for 폭 in 폭들:
                칸들.append((len(칸들), 안길, 폭, 쪽번))
        틀글 = ''.join(
            '<iframe id="F%d" src="%s" width="%d" height="2400"></iframe>'
            % (i, 안길, 폭) for i, 안길, 폭, _ in 칸들)
        목록 = '[' + ','.join('["F%d",%d,%d]' % (i, 폭, 쪽번)
                              for i, _, 폭, 쪽번 in 칸들) + ']'
        겉 = 겉틀 % (틀글, 목록)
        p = os.path.join(t, 'z.html')
        io.write(p, 겉)
        빈것 = dict((쪽, dict((폭, None) for 폭 in 폭들))
                    for 쪽 in 쪽길들)
        # ★ **예산은 상한일 뿐입니다** (2026-10-07 바깥 검수)
        #   20초를 **무조건 다 써서** 31초가 걸렸습니다. 쪽 안
        #   타이머는 2,200ms 면 답을 냅니다. 6초로 줄이고,
        #   **다 못 쟀으면** 긴 예산으로 한 번 더 돕니다.
        r, 다잿나 = None, False
        for 예산 in (6000, 20000):
            try:
                r = subprocess.run(
                     machine.크롬앞머리() + [
                     # ★ 창은 **한 줄에 늘어선 모든 칸**을 담아야 합니다
                     '--window-size=%d,2600'
                     % max(sum(폭 for _, _, 폭, _ in 칸들) + 140, 620),
                     '--allow-file-access-from-files',
                     # 바깥으로 안 나갑니다 — 인터넷에 흔들리면 시험이 아닙니다
                     '--host-resolver-rules=MAP * 127.0.0.1:1',
                     '--virtual-time-budget=%d' % 예산, '--dump-dom',
                     'file:///' + p.replace(os.sep, '/')],
                    capture_output=True, text=True, encoding='utf-8',
                    errors='replace', timeout=240)
            except subprocess.TimeoutExpired:
                return 빈것
            # ★ **완료 신호**를 봅니다 — 「비었나」가 아닙니다
            다잿나 = ('data-다잿음="%d"' % len(칸들)) in (r.stdout or '')
            if 다잿나:
                break
        if not 다잿나:
            return 빈것
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout or '', re.S)
        if not m:
            return 빈것
        글 = _h.unescape(m.group(1))
        if 글.strip() in ('', '?'):
            return 빈것
        try:
            받은것 = json.loads(글)
        except ValueError:
            return 빈것
        # ★ 열쇠가 **쪽번호|폭** 입니다 — 쪽길로 되돌립니다
        나옴 = {}
        for 쪽번, 쪽 in enumerate(쪽길들):
            나옴[쪽] = dict((폭, 받은것.get('%d|%d' % (쪽번, 폭)))
                           for 폭 in 폭들)
        return 나옴
    finally:
        shutil.rmtree(t, ignore_errors=True)
        for x in 임시:
            try:
                os.remove(x)  # 계약-17 예외 — **방금 내가 만든** 임시 쪽만 지웁니다
            except OSError:
                pass


def 재기(쪽길, 폭):
    """폭 하나만 잴 때 — 위 함수를 그대로 씁니다 (부르는 곳이 남아 있습니다)."""
    return 재기여러폭(쪽길, [폭]).get(폭)


def 쪽갈래(상대):
    """쪽 하나가 **어느 갈래**인가 — 주소 꼴로 가릅니다.

    ★ 2026-10-01 — 바깥 검수 지적
      「13→17 로 표본을 손으로 더한 것만으로는 근본 해결이
        아닙니다. 다음에 18번째 쪽 갈래를 만들면 또 빠집니다.
        검사 대상도 지금 build 에서 **자동으로 파생**하도록
        만드십시오. 새 쪽 갈래가 생기면 검사 코드를 고치지
        않아도 저절로 최소 한 장이 검사를 받아야 합니다」

      맞습니다. 저는 같은 잘못을 **세 번** 했습니다.
      주석에 「표본에 없는 짜임은 앞으로도 못 잽니다」라고
      적어 두고도 두 번 더 빠뜨렸습니다.
    """
    칸 = 상대.split('/')
    if len(칸) == 1:
        # 맨 위 쪽 — 권역 쪽은 서로 같은 틀이라 하나로 묶습니다
        return '맨위:' + 칸[0]
    if len(칸) == 2:
        return 칸[0]
    return '/'.join(칸[:2])        # point/jeonbuk/... → point/jeonbuk


def 볼쪽들(전부):
    """**지금 지은 것에서 갈래마다 한 장씩** 뽑습니다.

    손으로 적지 않습니다. build.json 이 아는 쪽을 갈래로 묶어
    각 갈래의 첫 쪽을 봅니다. 새 갈래가 생기면 저절로 듭니다.

    ★ 권역 쪽 57개는 **틀이 같아** 하나로 갈음합니다.
      다만 풍경칸이 있는 쪽은 짜임이 달라 따로 넣습니다.
    """
    if 전부:
        # 쪽은 io.쪽들() 한 곳에서 모읍니다 (2026-10-06)
        # ★ 이 검사기가 바로 `__재기임시.html` 을 만드는 쪽입니다.
        #   밖에서 죽으면 finally 가 안 돌아 자국이 남습니다.
        #   제가 남긴 자국을 제가 또 재면 안 됩니다.
        return io.쪽들(NEW)
    import json
    모든쪽 = []
    판 = os.path.join(NEW, 'build.json')
    if os.path.isfile(판):
        try:
            with open(판, encoding='utf-8') as f:
                모든쪽 = [k for k in (json.load(f).get('파일') or {})
                          if k.endswith('.html')]
        except Exception:
            모든쪽 = []
    if not 모든쪽:
        모든쪽 = [os.path.relpath(p, NEW).replace(os.sep, '/')
                  for p in io.쪽들(NEW)]

    # 권역 쪽을 가려냅니다 — 자료가 아는 권역 이름입니다
    권역들 = set()
    try:
        from engine.data import 자료
        권역들 = {r['id'] + '.html' for r in 자료().권역들}
    except Exception:
        pass

    나옴, 본갈래 = [], set()
    꼭볼것 = ('seongsan.html',)        # 풍경칸이 있는 권역 쪽
    for 상대 in sorted(모든쪽):
        if 상대 in 권역들 and 상대 not in 꼭볼것:
            갈 = '권역'              # 57개를 하나로 묶습니다
        else:
            갈 = 쪽갈래(상대)
        if 갈 in 본갈래:
            continue
        본갈래.add(갈)
        p = os.path.join(NEW, 상대.replace('/', os.sep))
        if os.path.exists(p):
            나옴.append(p)
    for 이름 in 꼭볼것:
        p = os.path.join(NEW, 이름)
        if os.path.exists(p) and p not in 나옴:
            나옴.append(p)
    # ★ **새 짜임을 켠 쪽을 반드시 봅니다** (2026-10-08)
    #   갈래로 묶으면 포인트 쪽 하나로 갈음되는데, 상세 패널을
    #   켠 쪽은 **짜임이 다릅니다.** 표본에 없으면 그 쪽이 휴대폰
    #   폭에서 넘치는지 아무도 안 봅니다.
    for _, 길 in samples.켠쪽들(NEW):
        if 길 not in 나옴:
            나옴.append(길)
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

    # ★ **쪽을 바깥, 폭을 안쪽으로 뒤집었습니다** (2026-10-06 주인 지시)
    #   전에는 폭마다 38쪽을 돌아 크롬을 266번 띄웠습니다.
    #   이제 쪽마다 한 번 띄워 일곱 폭을 함께 잽니다.
    #   보이는 차례는 그대로 두려고 결과를 먼저 모은 뒤 폭별로 냅니다.
    # ★ **쪽을 묶어** 한 판에 그립니다 (2026-10-07)
    #   크롬 37번이 29.1초로 전체의 100% 였습니다.
    #   묶으면 띄우는 횟수가 그만큼 줄어듭니다.
    묶음 = 묶음크기()
    잰것 = {}
    for i in range(0, len(쪽들), 묶음):
        잰것.update(재기여러쪽(쪽들[i:i + 묶음], list(재볼폭들)))

    for 폭 in 재볼폭들:
        print('[%dpx]' % 폭)
        for p in 쪽들:
            이름 = os.path.relpath(p, NEW).replace(os.sep, '/')
            것 = 잰것[p].get(폭)
            if 것 is None:
                못잼.append('%s (%dpx)' % (이름, 폭))
                print('  □ %-40s 잴 형편이 안 됩니다' % 이름)
                continue
            진짜넘침 = [x for x in 것['넘침'] if not x.get('밀기')]
            민것 = [x for x in 것['넘침'] if x.get('밀기')]

            # ★ **상세가 첫 화면에 있는가** (2026-10-08에 눈으로 잡음)
            #   「안 잘린다」가 기준이 아닙니다 (규칙 6-2).
            #   넘침은 0이었는데 휴대폰에서 0.92 화면을 내려야
            #   포인트가 보였습니다. 그래서 **재는 것**으로 옮깁니다.
            # ★ **「상세가 첫 화면에 있는가」는 여기서 못 잽니다**
            #   (2026-10-08 — 만들어 보고 빼기까지 한 자리입니다)
            #
            #   공개 서버에서 눈으로 찾은 문제였습니다 — 휴대폰에서
            #   `?point=` 로 들어가면 패널이 **0.92 화면 아래**에
            #   있어, 주소를 받은 분이 빈 화면을 봅니다. 고치고
            #   나서 「다음에도 기계가 잡게」 하려고 여기 넣었습니다.
            #
            #   그런데 **헛돌았습니다.** 고친 판과 일부러 망가뜨린
            #   판이 **똑같이 27쪽**을 잡았습니다. 끌어올리기가
            #   iframe 안에서는 일어나지 않아 둘을 구별하지 못합니다.
            #   (iframe 을 2400px 로 띄워 재는 짜임이라, 재는 시점과
            #    스크롤 기준이 진짜 휴대폰과 다릅니다)
            #
            #   **구별하지 못하는 검사는 두지 않습니다.** 늘 27쪽을
            #   잡으면 소음이 되고, 소음은 진짜를 덮습니다.
            #   재는 값(`패널몇화면`)은 남겨 둡니다 — 나중에 진짜
            #   창 크기로 재는 길이 생기면 그때 씁니다.
            pass
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
                    if 것.get('그래프'):
                        꼬리 = '  · 그래프 %dpx' % 것.get('그래프폭', 0)
                    elif 것.get('접힘'):
                        # 접힌 칸 안입니다 — 손님이 펼쳐야 그립니다.
                        # 안 그려진 것이 **맞습니다.**
                        꼬리 = '  · 그래프는 접힌 칸 안에 있습니다'
                    else:
                        꼬리 = '  ★ 그래프가 안 그려졌습니다'
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
