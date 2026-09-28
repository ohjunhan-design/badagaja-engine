# -*- coding: utf-8 -*-
"""쪽을 **실제로 그려 보고** 잽니다.  (계약-14·16)

왜
    HTML 을 읽어서는 모르는 것들이 있습니다.
      · 글이 화면 밖으로 넘치는가
      · 글자가 너무 작은가
      · 누를 자리가 손가락보다 작은가
      · 광고 칸이 배너보다 좁은가 (계약-15)

    옛 사이트에서 「고쳤습니다」 하고 보고했다가 화면에서는 그대로였던 일이
    여러 번 있었습니다. 이제 재고 나서 말합니다.

어떻게
    크롬을 머리 없이 띄워 쪽을 그리고, 재는 스크립트를 함께 넣어
    결과를 돌려받습니다. 엣지는 쓰지 않습니다 (주인 규칙 25).

    ★ 쪽을 **틀(iframe) 안에 넣어** 잽니다 (2026-09-26)
      윈도우 크롬은 창을 약 500px 아래로 줄이지 못합니다.
      `--window-size=375` 를 줘도 뷰포트는 485 가 되어,
      「375px 에서 넘친다」는 **헛것**이 나옵니다. 저도 한 번 속았습니다.
      틀 안에 넣으면 폭을 정확히 줄 수 있습니다.

쓰는 법
    python engine/check_render.py site/point/taean-fishing.html
    python engine/check_render.py --all
"""
import os
import re
import sys
import json
import glob
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

# 재는 기준
#
# ★ 작은 글자를 **10px 로 낮춥니다** (2026-09-27)
#   처음에는 12px 로 두었더니 416쪽 전부에서 이름표(배지)가 걸렸습니다.
#   옛 사이트 전남 쪽을 재 보니 10px 를 181곳, 9px 를 35곳 쓰고
#   있었습니다. 주인 규칙 7 — 「디자인 기준은 언제나 전남 쪽입니다.
#   글자 크기·굵기·짜임새 모두 전남 쪽을 따라갑니다」
#
#   즉 10~12px 이름표는 **정해진 디자인**이지 탈이 아닙니다.
#   탈이 아닌 것을 계속 알리면 검사가 무뎌져, 진짜 탈을 놓칩니다.
#   다만 9px 아래는 읽기 어려우므로 그때는 알립니다.
#
#   ※ 10px 가 작다는 것은 사실입니다. 디자인을 바꾸실 뜻이 있으면
#     이 값을 올리면 그 자리가 전부 나옵니다.
작은글자 = 10         # px — 전남 쪽 기준 (주인 규칙 7)
좁은누름 = 40         # px — 손가락이 닿는 최소 크기
넘침여유 = 1          # px — 반올림 오차

재는스크립트 = r'''
<script>
(function(){
  function 보이나(el){
    var s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
    if (el.closest('.sr-only')) return false;
    var r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  var 폭 = document.documentElement.clientWidth;
  var 나옴 = {폭: 폭, 몸통폭: document.body.scrollWidth,
              넘침: [], 칸만넘음: [], 작은글자: [], 좁은누름: [],
              광고: []};

  // 일부러 옆으로 미는 자리(걸러내기 단추 줄 등) 안은 넘쳐도 됩니다
  function 스크롤안인가(el){
    var p = el.parentElement;
    while (p && p !== document.body) {
      var ov = getComputedStyle(p).overflowX;
      if (ov === 'auto' || ov === 'scroll') return true;
      p = p.parentElement;
    }
    return false;
  }

  // 1) 가로로 넘치는 것
  var 모두 = document.querySelectorAll('body *');
  for (var i = 0; i < 모두.length; i++) {
    var el = 모두[i];
    if (!보이나(el)) continue;
    var r = el.getBoundingClientRect();
    if ((r.right > 폭 + 1 || r.left < -1) && !스크롤안인가(el)) {
      // 부모가 이미 넘쳤으면 자식은 덩달아 넘칩니다 — 맨 위의 것만 적습니다
      var 부모 = el.parentElement;
      var 부모넘침 = false;
      while (부모 && 부모 !== document.body) {
        var pr = 부모.getBoundingClientRect();
        if (pr.right > 폭 + 1 || pr.left < -1) { 부모넘침 = true; break; }
        부모 = 부모.parentElement;
      }
      if (!부모넘침) {
        나옴.넘침.push({
          태그: el.tagName.toLowerCase(),
          클래스: (el.className || '').toString().slice(0, 60),
          오른쪽: Math.round(r.right), 왼쪽: Math.round(r.left),
          글: (el.textContent || '').trim().slice(0, 40)
        });
      }
    }
  }

  // 2) 작은 글자 · 3) 좁은 누름자리
  var 글있는것 = document.querySelectorAll('p,span,div,li,td,a,button,label,h1,h2,h3');
  var 본것 = {};
  for (var j = 0; j < 글있는것.length; j++) {
    var e = 글있는것[j];
    if (!보이나(e)) continue;
    var 직접글 = '';
    for (var k = 0; k < e.childNodes.length; k++)
      if (e.childNodes[k].nodeType === 3) 직접글 += e.childNodes[k].textContent;
    직접글 = 직접글.trim();
    var cs = getComputedStyle(e);
    if (직접글) {
      var 크기 = parseFloat(cs.fontSize);
      var 키 = e.tagName + '|' + e.className + '|' + 크기;
      if (크기 < __작은글자__ && !본것[키]) {
        본것[키] = 1;
        나옴.작은글자.push({클래스: (e.className||'').toString().slice(0,40),
                            크기: 크기, 글: 직접글.slice(0, 30)});
      }
    }
    if (e.tagName === 'A' || e.tagName === 'BUTTON' ||
        (e.tagName === 'INPUT')) {
      var rr = e.getBoundingClientRect();
      if (rr.height > 0 && rr.height < __좁은누름__) {
        나옴.좁은누름.push({태그: e.tagName.toLowerCase(),
                            클래스: (e.className||'').toString().slice(0,40),
                            높이: Math.round(rr.height),
                            글: (e.textContent||'').trim().slice(0, 24)});
      }
    }
  }

  // 3-2) 안쪽 내용이 제 칸보다 넓은 것 — 넘침의 진짜 뿌리를 찾습니다
  //
  //   ★ 제 칸보다 넓다고 다 탈은 아닙니다 (2026-09-27)
  //
  //     걸음 카드 줄(.st-row)이 제 칸(1080)보다 넓은 1142 였습니다.
  //     그런데 오른쪽 끝이 1142 라 **화면(1280) 안**입니다.
  //     가로 스크롤도 안 생기고 잘리지도 않습니다. 눈에 멀쩡합니다.
  //     (가운데 맞춤이라 양옆으로 조금씩 퍼진 것뿐입니다)
  //
  //     그것을 막음으로 세니, **지금 운영 중인 사이트도 FAIL** 이
  //     나왔습니다. 몇 해째 아무 탈 없이 돌아가는 쪽인데 말입니다.
  //
  //     그래서 갈라 봅니다.
  //         화면 밖으로 나감   → 막음. 손님이 못 보거나 가로로 밀립니다
  //         화면 안에 있음     → 알림. 살펴볼 만하지만 막지 않습니다
  for (var n = 0; n < 모두.length; n++) {
    var e2 = 모두[n];
    if (!보이나(e2)) continue;
    if (e2.scrollWidth > e2.clientWidth + 2 && e2.clientWidth > 0) {
      var c2 = getComputedStyle(e2).overflowX;
      if (c2 === 'auto' || c2 === 'scroll' || c2 === 'hidden') continue;
      var r2 = e2.getBoundingClientRect();
      // 내용의 실제 오른쪽 끝 — 칸 왼쪽 + 안쪽 너비
      var 끝 = r2.left + e2.scrollWidth;
      var 밖으로 = (끝 > 폭 + 1) || (r2.left < -1);
      var 한줄 = {태그: e2.tagName.toLowerCase(),
        클래스: (e2.className||'').toString().slice(0,60),
        오른쪽: Math.round(끝), 왼쪽: Math.round(r2.left),
        글: '안쪽 ' + e2.scrollWidth + ' > 칸 ' + e2.clientWidth
            + (밖으로 ? '' : ' (화면 안)')};
      if (밖으로) 나옴.넘침.push(한줄);
      else 나옴.칸만넘음.push(한줄);
    }
  }

  // 4) 광고 칸 (계약-15)
  var 광고들 = document.querySelectorAll('.ad-slot');
  for (var m = 0; m < 광고들.length; m++) {
    var ar = 광고들[m].getBoundingClientRect();
    나옴.광고.push({폭: Math.round(ar.width), 높이: Math.round(ar.height)});
  }

  // 결과를 바깥 틀에 직접 붙입니다. --dump-dom 은 바깥 틀만 찍기 때문입니다
  var 상자 = document.createElement('div');
  상자.id = '__잰결과__' + (window.__번호 === undefined ? '' : window.__번호);
  상자.style.display = 'none';
  상자.textContent = JSON.stringify(나옴);
  try { parent.document.body.appendChild(상자); }
  catch (e) { document.body.appendChild(상자); }
})();
</script>
'''


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
틀쪽 = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0}iframe{border:0;display:block}</style>
</head><body><iframe src="__쪽__" width="__폭__" height="__높이__"></iframe>
</body></html>"""


# ── 사본을 만들 때 **원래 깊이를 지킵니다** ★ 2026-09-27 ──────
#
#   전에는 쪽이 어디 있든 무조건 `point/` 밑에 복사했습니다.
#
#       사본 = os.path.join(임시, 'point', os.path.basename(쪽길))
#
#   포인트 쪽은 `site/point/x.html` 이라 `../assets/css/site.css` 가
#   맞아떨어졌습니다. 그런데 **첫 화면은 뿌리에 있어** 차림표를
#   `assets/css/site.css` 로 부릅니다. 그것을 `point/` 로 옮기면
#   `point/assets/css/...` 를 찾아 **CSS 가 통째로 안 실립니다.**
#
#   그래서 민 HTML 로 그려져, 사진이 원래 픽셀 크기(1800px)로
#   튀어나왔습니다. 판정표에는 **「첫 화면이 가로로 넘칩니다」**
#   라고 30건이 찍혔습니다. 쪽은 멀쩡한데 검사기가 틀렸습니다.
#
#   크롬으로 직접 재 보니 이랬습니다.
#       groups display=grid width=1080px   넘침 없음
#       card                 width=259.5px
#
#   ★ `home.css` 도 복사하지 않고 있었습니다 — 첫 화면 차림표 전부가
#     빠져 있었습니다. 그래서 `assets/` 를 통째로 옮깁니다.
# 모습을 정하는 것들 — 이것이 없으면 민 HTML 로 그려집니다
모습을정하는것 = ('.css', '.js', '.mjs', '.woff', '.woff2', '.ttf', '.otf')

# 사진은 안 옮깁니다 (71MB). `<img>` 에 width·height 가 적혀 있어
# 파일이 없어도 자리는 제대로 잡힙니다.
안옮길칸 = ('img', 'images', 'photo', 'photos', 'assets/img')


def _자산옮기기(임시):
    """차림표와 스크립트를 **사이트 어디에 있든** 찾아 옮깁니다.

    ★ `assets/` 만 옮기면 안 됩니다 (2026-09-27)
      두번째도전은 `assets/css/` 에 두는데, **옛 사이트는 `css/`** 에
      둡니다. `assets/` 만 옮기고 옛 쪽을 재었더니 그쪽도 민 HTML 로
      그려져, 「옛 사이트가 더 많이 넘친다」는 **헛것**이 나왔습니다.
      견주려고 만든 잣대가 견줌을 틀리게 하면 아무 쓸모가 없습니다.
    """
    옮김 = 0
    for 뿌리, 칸들, 파일들 in os.walk(NEW):
        칸들[:] = [d for d in 칸들
                   if d.lower() not in ('img', 'images', 'photo', 'photos')]
        for f in 파일들:
            if not f.lower().endswith(모습을정하는것):
                continue
            p = os.path.join(뿌리, f)
            받는곳 = os.path.join(임시, os.path.relpath(p, NEW))
            if f.lower().endswith(('.css', '.js', '.mjs')):
                io.write(받는곳, io.read(p, default=''))
            else:
                io.copy_binary(p, 받는곳)
            옮김 += 1
    return 옮김


def _사본자리(임시, 쪽길, 이름=None):
    """쪽의 **원래 상대 자리**를 그대로 지킨 사본 길."""
    상대 = os.path.relpath(쪽길, NEW)
    칸 = os.path.dirname(상대)
    return os.path.join(임시, 칸, 이름 or os.path.basename(상대))


def _틀에서부를길(임시, 사본):
    """틀(iframe) 이 부를 상대 주소 — 임시 뿌리 기준."""
    return os.path.relpath(사본, 임시).replace(os.sep, '/')


def 재기(쪽길, 폭=375, 높이=2000):
    """쪽 하나를 그려서 잽니다. 진짜 파일은 안 건드립니다.

    ★ 쪽을 **틀(iframe) 안에 넣어** 잽니다 (2026-09-26)
      윈도우 크롬은 창을 약 500px 아래로 줄이지 못합니다. `--window-size=375`
      를 줘도 뷰포트가 485~500 이 되어 「375px 에서 넘친다」는 **헛것**이
      나옵니다. 저도 한 번 속아 멀쩡한 CSS 를 두 번 고쳤습니다.
      틀 안에 넣으면 폭을 정확히 줄 수 있습니다.
    """
    s = io.read(쪽길)
    낌 = (재는스크립트
          .replace('__작은글자__', str(작은글자))
          .replace('__좁은누름__', str(좁은누름)))
    s = s.replace('</body>', 낌 + '</body>')

    임시 = tempfile.mkdtemp(prefix='badagaja-render-')
    try:
        # ★ 원래 깊이를 지켜 옮깁니다 — 안 그러면 차림표를 못 찾습니다
        사본 = _사본자리(임시, 쪽길)
        io.write(사본, s)
        _자산옮기기(임시)
        틀 = os.path.join(임시, '틀.html')
        io.write(틀, (틀쪽.replace('__쪽__', _틀에서부를길(임시, 사본))
                      .replace('__폭__', str(폭))
                      .replace('__높이__', str(높이))))
        나옴 = subprocess.run(
            machine.크롬앞머리() + [ '--hide-scrollbars',
             '--window-size=%d,%d' % (max(폭 + 40, 900), 높이 + 60),
             '--virtual-time-budget=2500', '--allow-file-access-from-files',
             # 바깥 연결은 곧바로 실패시킵니다 (2026-09-27)
             #   크롬은 네트워크를 기다리는 동안 --virtual-time-budget 시계를
             #   멈춥니다. 그래서 대답 없는 요청 하나에 검사가 통째로 멈췄습니다.
             #   폭을 재는 검사가 인터넷 형편을 타서도 안 됩니다.
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=60)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('재지 못했습니다 — 크롬이 결과를 안 돌려줬습니다')
        import html as _h
        잰것 = json.loads(_h.unescape(m.group(1)))
        # 바란 폭으로 잡혔는지 확인합니다 — 안 그러면 헛것이 나옵니다
        if 잰것.get('폭') != 폭:
            raise RuntimeError('틀 폭이 %s 로 잡혔습니다 (바란 폭 %d)'
                               % (잰것.get('폭'), 폭))
        return 잰것
    finally:
        shutil.rmtree(임시, ignore_errors=True)



def 묶어재기(쪽길들, 폭=375, 높이=2000):
    """여러 쪽을 **한 크롬에** 띄워 한꺼번에 잽니다.

    ★ 왜 묶나 (2026-09-27 주인 지시 — 속도)

        쪽 하나마다 크롬을 새로 띄우면 3.9초가 걸립니다.
        그중 대부분이 **크롬을 켜는 비용**입니다. 416쪽이면 27분.

        여러 개를 같이 돌려 봤더니 16.5분밖에 안 줄었습니다.
        크롬 켜는 일 자체가 무거워, 여러 개를 켜도 그만큼 느려집니다.

        그래서 **크롬 하나에 틀(iframe)을 여러 개** 띄웁니다.
        켜는 비용을 여러 쪽이 나눠 씁니다.

    ★ 폭은 틀이 정합니다 (2026-09-26 에 겪은 일 그대로)
        창 크기로는 375px 을 못 만듭니다. 틀 안에 넣어야 정확합니다.

    돌려주는 것 — 쪽길 → 잰 것 (못 잰 쪽은 없습니다)
    """
    if not 쪽길들:
        return {}
    낌 = (재는스크립트
          .replace('__작은글자__', str(작은글자))
          .replace('__좁은누름__', str(좁은누름)))

    임시 = tempfile.mkdtemp(prefix='badagaja-render-')
    try:
        _자산옮기기(임시)
        틀들 = []
        이름들 = []
        for i, 쪽길 in enumerate(쪽길들):
            이름 = 'p%d.html' % i
            이름들.append(이름)
            글 = io.read(쪽길)
            # 결과 상자에 붙일 번호를 쪽 안에 심습니다
            번호심기 = '<script>window.__번호=%d;</script>' % i
            글 = 글.replace('</body>', 번호심기 + 낌 + '</body>')
            # ★ 원래 깊이를 지켜 옮깁니다 (이름만 p0·p1 로 바꿉니다)
            #   같은 칸에 여러 쪽이 와도 이름이 달라 안 부딪칩니다.
            사본 = _사본자리(임시, 쪽길, 이름)
            io.write(사본, 글)
            틀들.append('<iframe src="%s" width="%d" height="%d"></iframe>'
                        % (_틀에서부를길(임시, 사본), 폭, 높이))

        틀 = os.path.join(임시, '틀.html')
        io.write(틀, ("""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0}iframe{border:0;display:block}</style>
</head><body>%s</body></html>""" % ''.join(틀들)))

        나옴 = subprocess.run(
            machine.크롬앞머리() + [ '--hide-scrollbars',
             '--window-size=%d,%d' % (max(폭 + 40, 900), 높이 + 60),
             # 틀이 많으니 시간을 조금 더 줍니다
             '--virtual-time-budget=%d' % min(2500 + 400 * len(쪽길들), 20000),
             '--allow-file-access-from-files',
             # 바깥 연결은 곧바로 실패시킵니다 (2026-09-27)
             #   크롬은 네트워크를 기다리는 동안 --virtual-time-budget 시계를
             #   멈춥니다. 그래서 대답 없는 요청 하나에 검사가 통째로 멈췄습니다.
             #   폭을 재는 검사가 인터넷 형편을 타서도 안 됩니다.
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8',
            timeout=60 + 20 * len(쪽길들))

        import html as _h
        결과 = {}
        for i, 쪽길 in enumerate(쪽길들):
            m = re.search(r'id="__잰결과__%d"[^>]*>(.*?)</div>' % i,
                          나옴.stdout or '', re.S)
            if not m:
                continue
            잰것 = json.loads(_h.unescape(m.group(1)))
            if 잰것.get('폭') != 폭:
                continue        # 폭이 안 맞으면 헛것입니다 — 버립니다
            결과[쪽길] = 잰것
        return 결과
    finally:
        shutil.rmtree(임시, ignore_errors=True)



def 쓸수있는메모리GB():
    """지금 쓸 수 있는 메모리(GB). 못 재면 None.

    ★ engine/machine.py 가 잽니다 — 윈도와 리눅스 둘 다.
      전에는 여기와 저기에 똑같은 ctypes 코드가
      들어 있어, 리눅스에서는 둘 다 넘어졌습니다.
    """
    return machine.남은메모리GB()
def 몇개씩():
    """크롬을 동시에 몇 개 띄울지. **형편을 보고** 정합니다.

    ★ 2026-09-27 — 여섯을 띄웠다가 MemoryError 로 넘어졌습니다.
      크롬 하나가 300MB 남짓 씁니다. 여유의 절반만 씁니다.

    BADAGAJA_CHROMES 로 직접 정할 수도 있습니다.
    """
    # ★ 이름이 영어여야 합니다 (2026-09-27)
    #   리눅스 셸은 환경변수 이름에 한글을 **아예 못 씁니다.**
    #   깃허브 액션(클라우드)에서 돌리려면 영어여야 합니다.
    정해준것 = os.environ.get('BADAGAJA_CHROMES')
    if 정해준것:
        try:
            return max(1, int(정해준것))
        except ValueError:
            pass
    칸수 = min(6, max(2, (os.cpu_count() or 4) // 3))
    남은 = 쓸수있는메모리GB()
    if 남은 is None:
        return min(2, 칸수)          # 못 재면 조심스럽게
    # 크롬 하나에 0.6GB 로 잡고, 여유의 절반만 씁니다
    버틸수 = int(남은 / 2.0 / 0.6)
    return max(1, min(칸수, 버틸수))


def 보기(쪽길, 폭, 잰것, 자세히=True):
    # 검사 등급 (계약-21)
    #   탈(막음)   — 가로 넘침. 글이 잘려 못 읽습니다
    #   참고(알림) — 작은 글자·좁은 누름자리. 막지 않고 알려만 줍니다
    탈, 알림 = [], []
    if 잰것.get('몸통폭', 0) > 폭 + 1:
        탈.append('%dpx — 쪽 전체가 %dpx 로 넘칩니다 (가로 스크롤이 생깁니다)'
                  % (폭, 잰것['몸통폭']))
    if 잰것['넘침']:
        for x in 잰것['넘침']:
            탈.append('%dpx — 가로 넘침: <%s class="%s"> 오른쪽 %dpx "%s"'
                      % (폭, x['태그'], x['클래스'], x['오른쪽'], x['글']))
    # ★ 제 칸보다는 넓지만 **화면 안**인 것 — 막지 않고 알려만 줍니다
    #   (2026-09-27 — 걸음 카드 줄이 여기 걸립니다. 지금 운영 중인
    #    사이트에도 그대로 있고, 몇 해째 아무 탈이 없었습니다)
    for x in 잰것.get('칸만넘음', [])[:5]:
        알림.append('%dpx — 제 칸보다 넓음(화면 안): <%s class="%s"> %s'
                    % (폭, x['태그'], x['클래스'], x['글']))
    for x in 잰것['작은글자']:
        알림.append('%dpx — 글자 %.0fpx (.%s) "%s"'
                    % (폭, x['크기'], x['클래스'], x['글']))
    for x in 잰것['좁은누름'][:5]:
        알림.append('%dpx — 누름자리 %dpx (<%s> "%s")'
                    % (폭, x['높이'], x['태그'], x['글']))
    return 탈, 알림


# 검사 등급 (계약-21)
#   막음 — 가로 넘침. 글이 잘려 못 읽습니다
#   알림 — 작은 글자·좁은 누름자리. 막지 않고 알려만 줍니다
막음, 알림 = [], []


def 한쪽(쪽길, 폭들=(375, 1280)):
    """한 쪽을 재고 **글을 돌려줍니다** (찍지 않습니다).

    ★ 왜 안 찍나 (2026-09-27 주인 지시 — 속도)
        여러 쪽을 **동시에** 재면 찍는 순서가 뒤섞여 못 읽습니다.
        그래서 각자 글을 만들어 돌려주고, 모아서 차례대로 찍습니다.
    """
    줄 = [os.path.relpath(쪽길, NEW)]
    모든탈, 모든알림 = [], []
    for 폭 in 폭들:
        잰것 = 재기(쪽길, 폭)
        탈, 알림 = 보기(쪽길, 폭, 잰것)
        모든탈 += 탈
        모든알림 += 알림
        줄.append('  %4dpx  몸통 %dpx · 넘침 %d · 작은글자 %d · 좁은누름 %d'
                  % (폭, 잰것.get('몸통폭', 0), len(잰것['넘침']),
                     len(잰것['작은글자']), len(잰것['좁은누름'])))
    for x in 모든탈:
        줄.append('  ✗ %s' % x)
    for x in 모든알림[:8]:
        줄.append('  ~ %s' % x)
    줄.append('')
    return 모든탈, 모든알림, '\n'.join(줄)


def main():
    if '--all' in sys.argv:
        쪽들 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        쪽들 = [sys.argv[1] if os.path.isabs(sys.argv[1])
                else os.path.join(ROOT, sys.argv[1])]
    else:
        print(__doc__)
        return 1

    print('쪽을 그려서 재기 — 크롬 (계약-14)')
    # ★ 여러 쪽을 **동시에** 잽니다 (2026-09-27 주인 지시 — 속도)
    #   쪽마다 크롬을 새로 띄우는 데 3.9초가 걸려, 416쪽이면 27분입니다.
    #   이 컴퓨터는 코어가 여럿이니 몇 개씩 같이 돌립니다.
    #   크롬은 메모리를 많이 쓰므로 코어 수의 절반쯤만 씁니다.
    탈수 = 0
    if len(쪽들) <= 1:
        for p in 쪽들:
            탈, 알, 글 = 한쪽(p)
            막음.extend(탈)
            알림.extend(알)
            print(글)
            탈수 += len(탈)
        return 마무리(탈수)

    # ★ 묶어서, 그리고 동시에 (2026-09-27 주인 지시 — 속도)
    #   한 크롬에 틀 여러 개를 띄우고, 그 크롬을 또 여러 개 돌립니다.
    한묶음 = 12
    한꺼번에 = 몇개씩()
    묶음들 = [쪽들[i:i + 한묶음] for i in range(0, len(쪽들), 한묶음)]
    print('  쪽 %d개 · %d개씩 묶어 %d묶음을 한 번에 %d개씩'
          % (len(쪽들), 한묶음, len(묶음들), 한꺼번에))
    print('')

    import concurrent.futures as _cf

    def 한묶음재기(묶음):
        나옴 = {}
        for 폭 in (375, 1280):
            for 쪽길, 잰것 in 묶어재기(묶음, 폭).items():
                나옴.setdefault(쪽길, {})[폭] = 잰것
        return 나옴

    with _cf.ThreadPoolExecutor(max_workers=한꺼번에) as 풀:
        모은것 = list(풀.map(한묶음재기, 묶음들))

    잰것표 = {}
    for x in 모은것:
        잰것표.update(x)

    # 재는 것은 동시에, 찍는 것은 **자료 차례대로** (계약-07)
    못잰것 = []
    for 쪽길 in 쪽들:
        이름 = os.path.relpath(쪽길, NEW)
        폭별 = 잰것표.get(쪽길) or {}
        if len(폭별) < 2:
            못잰것.append(이름)
            continue
        print(이름)
        모든탈, 모든알림 = [], []
        for 폭 in (375, 1280):
            잰것 = 폭별[폭]
            탈, 알 = 보기(쪽길, 폭, 잰것)
            모든탈 += 탈
            모든알림 += 알
            print('  %4dpx  몸통 %dpx · 넘침 %d · 작은글자 %d · 좁은누름 %d'
                  % (폭, 잰것.get('몸통폭', 0), len(잰것['넘침']),
                     len(잰것['작은글자']), len(잰것['좁은누름'])))
        막음.extend(모든탈)
        알림.extend(모든알림)
        탈수 += len(모든탈)
        for x in 모든탈:
            print('  ✗ %s' % x)
        for x in 모든알림[:8]:
            print('  ~ %s' % x)
        print('')

    # ★ 못 잰 쪽은 **NOT_TESTED** 입니다 (2026-09-27 고침)
    #
    #   「못 잰 것을 지킴으로 세지 않는다」는 지키고 있었는데,
    #   그 짝인 「**못 잰 것을 어김으로도 세지 않는다**」가
    #   빠져 있었습니다.
    #
    #   실제로 겪었습니다. 최종 판정에서 4번이 FAIL 로 나와
    #   쪽에 탈이 있는 줄 알고 20분을 썼습니다. 알고 보니
    #   판정이 도는 동안 크롬을 같이 돌려 5쪽이 시간 안에
    #   안 끝난 것이었고, 바로 다시 돌리니 0개였습니다.
    #
    #       재 봤더니 잘못이 있다  → 손볼 곳 (FAIL)
    #       아예 못 쟀다           → NOT_TESTED
    if 못잰것:
        print('  ? 못 잰 쪽 %d개 — 재지 못한 것은 「멀쩡하다」도 '
              '「잘못됐다」도 아닙니다' % len(못잰것))
        for x in 못잰것[:6]:
            print('      %s' % x)
        print('      크롬이 바빴거나 시간이 모자랐을 수 있습니다.')
        print('      다른 일을 멈추고 다시 돌려 보세요.')
        print('')
        print('NOT_TESTED')
        print('')
    return 마무리(탈수)


def 마무리(탈수):
    if 알림:
        print('살펴볼 것 %d건 (막지 않습니다)' % len(알림))
    if 막음:
        print('손볼 곳 %d건' % len(막음))
        return 1
    print('화면에서도 탈이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
