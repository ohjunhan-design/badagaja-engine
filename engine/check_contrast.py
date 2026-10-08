# -*- coding: utf-8 -*-
"""**글이 바탕과 구별되는가** (2026-10-08 밤 주인 지시)

★ 왜 이 검사가 있나

    주인 지시 — 「전체적으로 **시각적으로** 오류가 있는지 찾아봐.
    **디자인 오류** …」

    글자 크기는 `check_render` 가 봅니다. 그러나 **글이 흐려서 안
    읽히는 것**은 아무도 안 봤습니다. 크기가 16px 이어도 바탕과
    색이 비슷하면 읽을 수 없습니다.

    바다가자는 바탕이 `#FFFBF3`(크림색)이고 흐린 글씨가
    `#6B5E4F` 입니다. 그 위에 더 흐린 색을 얹거나, 사진 위에 글을
    올리면 **눈이 아픕니다.**

무엇을 재나

    W3C 가 정한 **밝기 대비**(WCAG contrast ratio)를 잽니다.
      · 보통 글 (18px 미만, 또는 14px 미만 굵게) — **4.5 : 1** 이상
      · 큰 글 (18px 이상, 또는 14px 이상 굵게) — **3 : 1** 이상

    ★ 짐작으로 고르지 않았습니다. 이것이 **표준에 적힌 수**입니다.

    ★ 사진 위의 글은 뺍니다 — 바탕색을 알 수 없습니다. 거짓으로
      잡느니 안 잡습니다 (기준선에 쌓아 둡니다).

쓰는 법
    python engine/check_contrast.py         표본
    python engine/check_contrast.py --all   전수
"""
import io
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
from engine import io as _io          # noqa: E402
from engine import machine            # noqa: E402
from engine import mustmeasure        # noqa: E402
from engine import check_render as R  # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
기준길 = os.path.join(ROOT, 'tests', 'golden', '대비.json')

# W3C 표준값 — 짐작이 아닙니다
보통글기준 = 4.5
큰글기준 = 3.0

재는스크립트 = """
<script>
(function () {
  function 숫자들(c) {
    var m = (c || '').match(/[\\d.]+/g);
    return m ? m.map(Number) : null;
  }
  function 밝기(c) {
    var v = 숫자들(c);
    if (!v || v.length < 3) return null;
    if (v.length > 3 && v[3] === 0) return null;      // 완전히 투명
    var a = v.slice(0, 3).map(function (x) {
      x = x / 255;
      return x <= 0.03928 ? x / 12.92
                          : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
  }
  function 사진위인가(e) {
    // ★ 히어로는 `<img>` 를 **깔고** 그 위에 글을 얹습니다.
    //   `background-image` 만 보면 못 가려 「대비 1.47」 같은 헛것이
    //   나옵니다 (2026-10-08 밤에 158곳 가운데 여럿이 그랬습니다).
    var p = e;
    while (p && p !== document.documentElement) {
      var s = getComputedStyle(p);
      if (s.position !== 'static'
          && p.querySelector('img, picture, video, canvas')) return true;
      p = p.parentElement;
    }
    return false;
  }
  function 바탕찾기(e) {
    if (사진위인가(e)) return null;          // 색을 알 수 없습니다
    // 비치는 바탕은 위로 올라가며 찾습니다
    var p = e;
    while (p && p !== document.documentElement) {
      var s = getComputedStyle(p);
      // 사진이 깔려 있으면 **색을 알 수 없습니다** — 포기합니다
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;
      var v = 숫자들(s.backgroundColor);
      if (v && (v.length < 4 || v[3] > 0.92)) return s.backgroundColor;
      p = p.parentElement;
    }
    return 'rgb(255,255,255)';
  }
  function 글만(e) {
    var t = '';
    for (var i = 0; i < e.childNodes.length; i++) {
      if (e.childNodes[i].nodeType === 3) t += e.childNodes[i].nodeValue;
    }
    return t.trim();
  }
  function 재자() {
    var 난것 = { 폭: innerWidth, 흐린글: [] };
    var 모두 = document.querySelectorAll('body *');
    var 본것 = {};
    for (var i = 0; i < 모두.length; i++) {
      var e = 모두[i];
      var 글 = 글만(e);
      if (글.length < 4) continue;
      var s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden'
          || s.opacity === '0') continue;
      var r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      var 바탕 = 바탕찾기(e);
      if (!바탕) continue;                       // 사진 위 — 못 잽니다
      var a = 밝기(s.color), b = 밝기(바탕);
      if (a === null || b === null) continue;
      var 대비 = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      var 크기 = parseFloat(s.fontSize) || 16;
      var 굵게 = (parseInt(s.fontWeight, 10) || 400) >= 700;
      var 큰글 = 크기 >= 18 || (굵게 && 크기 >= 14);
      var 기준 = 큰글 ? __큰글__ : __보통글__;
      if (대비 >= 기준) continue;
      var 열쇠 = s.color + '|' + 바탕 + '|' + Math.round(크기);
      if (본것[열쇠]) continue;
      본것[열쇠] = 1;
      난것.흐린글.push({
        글: 글.slice(0, 20),
        클래스: (e.className || '').toString().trim().split(/\\s+/)[0] || '',
        글색: s.color, 바탕: 바탕,
        대비: Math.round(대비 * 100) / 100, 기준: 기준,
        크기: Math.round(크기), 굵게: 굵게
      });
      if (난것.흐린글.length >= 6) break;
    }
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    try { parent.document.body.appendChild(d); }
    catch (e2) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 250);
  else addEventListener('load', function () { setTimeout(재자, 250); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=1280, 높이=2200):
    글 = _io.read(쪽길)
    낌 = (재는스크립트.replace('__큰글__', str(큰글기준))
          .replace('__보통글__', str(보통글기준)))
    글 = 글.replace('</body>', 낌 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-contrast-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        _io.write(사본, 글)
        R._자산옮기기(임시)
        틀 = os.path.join(임시, '틀.html')
        _io.write(틀, (R.틀쪽.replace('__쪽__', R._틀에서부를길(임시, 사본))
                       .replace('__폭__', str(폭))
                       .replace('__높이__', str(높이))))
        나옴 = subprocess.run(
            machine.크롬앞머리() + [
                '--hide-scrollbars',
                '--window-size=%d,%d' % (폭 + 40, 높이 + 60),
                '--virtual-time-budget=2500', '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=90)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('크롬이 결과를 안 돌려줬습니다')
        import html as _h
        return json.loads(_h.unescape(m.group(1)))
    finally:
        shutil.rmtree(임시, ignore_errors=True)


_색박음 = re.compile(r'(?<![-\w])color:\s*#([0-9A-Fa-f]{3,8})')
_토큰 = re.compile(r'^\s*(--[\w-]+)\s*:', re.M)


def 임의색찾기():
    """★ **역할 토큰을 쓰는가** (2026-10-08 바깥 검수)

      「새 색을 추가할 때마다 임의 HEX 를 넣기보다 --orange,
        --orange-ink, --gold-ink, --muted 처럼 **역할 기반 토큰만**
        쓰는 방식으로 막는 게 좋습니다」

    작은 글씨(14px 미만)에 **토큰이 아닌 HEX 를 직접 박은 곳**을
    찾습니다. 오늘 하루에만 #8A8277 · #B08A4A · #F6C06A · #D8A24C …
    다섯 가지가 각각 다른 자리에서 나왔습니다. 한 곳씩 쫓는 대신
    **들어오는 길**을 막습니다.

    ★ 큰 글씨·바탕·테두리는 봐 줍니다 — 디자인의 자유입니다.
    """
    난것 = []
    _블록 = re.compile(r'([^{}]+)\{([^{}]*)\}')
    _크기 = re.compile(r'font-size:\s*([\d.]+)px')
    for p in sorted(glob.glob(os.path.join(ROOT, 'assets', 'css', '*.css'))):
        글 = _io.read(p, default='')
        for m in _블록.finditer(글):
            고르개, 속 = m.group(1).strip(), m.group(2)
            if 고르개.startswith('@') or 고르개.startswith(':root'):
                continue
            크 = _크기.search(속)
            if not 크 or float(크.group(1)) >= 14:
                continue
            for cm in _색박음.finditer(속):
                난것.append('%s — `%s` 가 색을 직접 박았습니다 (#%s · %spx)'
                            % (os.path.basename(p), 고르개[:34],
                               cm.group(1), 크.group(1)))
    return 난것


def 볼쪽들(전부):
    것들 = sorted(_io.쪽들(NEW))
    if 전부:
        return 것들
    칸별 = {}
    for p in 것들:
        칸 = os.path.dirname(os.path.relpath(p, NEW)) or '.'
        칸별.setdefault(칸, []).append(p)
    난것 = []
    for 칸 in sorted(칸별):
        난것 += 칸별[칸][:2]
    return 난것


def main():
    전부 = '--all' in sys.argv
    받아들이기 = '--받아들이기' in sys.argv
    print()
    print('  글이 바탕과 구별되는가 (W3C 대비 %s:1 · 큰 글 %s:1)'
          % (보통글기준, 큰글기준))
    print('  (2026-10-08 밤 주인 지시 — 「디자인 오류」)')
    print()

    것들 = 볼쪽들(전부)
    mustmeasure.있어야한다(것들, '쪽', 최소=10, 어디=NEW)

    기준 = {}
    try:
        기준 = json.loads(_io.read(기준길, default='{}'))
    except Exception:                                 # noqa: BLE001
        기준 = {}
    알던것 = set(기준.get('알던것') or [])

    막음, 알림 = [], []
    잰쪽 = 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        try:
            잰것 = 쪽재기(p)
        except Exception as e:                        # noqa: BLE001
            알림.append('%s — 못 쟀습니다 (%s)' % (짧, str(e)[:40]))
            continue
        잰쪽 += 1
        for x in 잰것['흐린글']:
            막음.append('%s — `%s` 가 흐립니다 (대비 %s · %s 넘어야 · '
                        '%dpx%s · 「%s」)'
                        % (짧, x['클래스'] or '글', x['대비'], x['기준'],
                           x['크기'], ' 굵게' if x['굵게'] else '',
                           x['글']))

    mustmeasure.있어야한다(range(잰쪽), '잰 쪽', 최소=10, 어디=NEW)
    print('  쪽 %d개를 그려 봤습니다 (%s)'
          % (잰쪽, '전수' if 전부 else '표본 — 전수는 --all'))
    print()

    if 받아들이기:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        _io.write(기준길, json.dumps({
            '_무엇인가': ('글이 바탕과 덜 구별되는 곳의 기준선입니다. '
                          '여기 있는 것은 **새로 생긴 것이 아니라는 '
                          '뜻**일 뿐, 읽기 좋다는 뜻이 아닙니다.'),
            '_기준': 'W3C — 보통 글 %s:1 · 큰 글 %s:1' % (보통글기준, 큰글기준),
            '알던것': sorted(막음),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(막음), os.path.relpath(기준길, ROOT)))
        return 0

    # ★ **역할 토큰을 쓰는가** (바깥 검수 2026-10-08)
    박은것 = 임의색찾기()
    for t in 박은것:
        알림.append('%s — 역할 토큰(`--orange-ink` 같은)을 쓰세요' % t)

    새것 = [t for t in 막음 if t not in 알던것]
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:3]:
            print('  ~ %s' % t)
        print()
    if 새것:
        print('  **새로 생긴** 손볼 곳 %d가지' % len(새것))
        for t in 새것[:12]:
            print('  ✗ %s' % t)
        print()
        print('  글자가 커도 **흐리면 안 읽힙니다.** 색을 진하게')
        print('  하거나 바탕을 바꾸세요.')
        return 1

    print('  · 글이 모두 바탕과 구별됩니다 (쌓인 것 %d곳)' % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
