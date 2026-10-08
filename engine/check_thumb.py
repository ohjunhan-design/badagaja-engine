# -*- coding: utf-8 -*-
"""**휴대폰에서 엄지가 닿는가** (2026-10-08 밤 주인 지시)

★ 왜 이 검사가 있나 — 주인 규칙 6-2

    「휴대폰은 「안 잘린다」가 기준이 아닙니다 — **한 손으로 쓸 수
    있는가, 엄지가 닿는 자리에 주요 단추가 있는가**까지 봅니다」

    `check_render` 도 누름자리를 보지만 **알림으로만** 냅니다.
    그래서 첫 화면 칩이 34px 인 채로 오래 있었습니다 —
    손님이 가장 먼저 누르는 것인데 손가락보다 작았습니다.

    여기서는 **막습니다.** 다만 거짓 양성이 많으면 둘 수 없으니
    기준선을 쌓고 **새로 느는 것만** 막습니다.

무엇을 재나 (휴대폰 390px 에서만)

    ① 누르는 것이 **44px** 이상인가
       — 애플·구글이 함께 권하는 값입니다. 짐작이 아닙니다.
    ② 누르는 것끼리 **8px** 이상 떨어져 있는가
       — 붙어 있으면 옆 것을 누릅니다.

    ★ 글 속 링크(본문 문장 안의 `<a>`)는 뺍니다 — 그것까지 44px 로
      만들면 글이 읽히지 않습니다. **단추처럼 생긴 것**만 봅니다:
      테두리·바탕·둥근 모서리가 있거나 `role="button"` 인 것.

쓰는 법
    python engine/check_thumb.py          표본
    python engine/check_thumb.py --all    전수
"""
import io
import os
import re
import sys
import json
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
기준길 = os.path.join(ROOT, 'tests', 'golden', '엄지.json')

누름최소 = 44          # 애플·구글이 함께 권하는 값
사이최소 = 8

재는스크립트 = r"""
<script>
(function () {
  function 보이나(e) {
    var s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden'
        || s.opacity === '0') return false;
    var r = e.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  function 단추처럼인가(e, s) {
    // ★ **글 속 링크는 뺍니다** — 44px 로 만들면 글이 안 읽힙니다.
    //   단추처럼 생긴 것만 봅니다.
    if (e.tagName === 'BUTTON') return true;
    if (e.getAttribute('role') === 'button') return true;
    if (s.borderTopWidth !== '0px' || s.borderRadius !== '0px') return true;
    var bg = s.backgroundColor || '';
    var v = bg.match(/[\\d.]+/g);
    if (v && (v.length < 4 || Number(v[3]) > 0.05)
        && bg !== 'rgba(0, 0, 0, 0)') return true;
    // 글 한복판에 있으면 본문 링크입니다
    var p = e.parentElement;
    if (p && (p.tagName === 'P' || p.tagName === 'LI')
        && (p.innerText || '').length > (e.innerText || '').length + 12) {
      return false;
    }
    return false;
  }
  function 재자() {
    var 난것 = { 폭: innerWidth, 작은것: [], 붙은것: [] };
    var 것들 = document.querySelectorAll(
      'a[href], button, [role="button"], input, select');
    var 잰것 = [];
    for (var i = 0; i < 것들.length; i++) {
      var e = 것들[i];
      if (!보이나(e)) continue;
      // 아래 고정 차림표는 제 규칙이 있습니다
      if (e.closest('.tabbar')) continue;
      var s = getComputedStyle(e);
      if (!단추처럼인가(e, s)) continue;
      var r = e.getBoundingClientRect();
      잰것.push({ e: e, r: r });
      if (r.height < __최소__ - 0.5) {
        var 사 = [], pp = e;
        while (pp && pp !== document.body) {
          var cn = (pp.className || '').toString().trim();
          사.push(pp.tagName.toLowerCase()
                  + (cn ? '.' + cn.split(/\s+/)[0] : ''));
          pp = pp.parentElement;
        }
        난것.작은것.push({
          태그: e.tagName,
          사슬: 사.slice(0, 3).join(' < '),
          클래스: (e.className || '').toString().trim().split(/\\s+/)[0] || '',
          글: (e.textContent || '').trim().slice(0, 18),
          높이: Math.round(r.height), 폭: Math.round(r.width)
        });
        if (난것.작은것.length >= 6) break;
      }
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


def 쪽재기(쪽길, 폭=390, 높이=2200):
    글 = _io.read(쪽길)
    글 = 글.replace('</body>',
                    재는스크립트.replace('__최소__', str(누름최소)) + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-thumb-')
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
    print('  휴대폰에서 엄지가 닿는가 (390px · 누름자리 %dpx)' % 누름최소)
    print('  (주인 규칙 6-2 — 「엄지가 닿는 자리에 주요 단추가 있는가」)')
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
        for x in 잰것['작은것']:
            막음.append('%s — `%s` 가 %dpx 입니다 (%d 넘어야 · 「%s」)'
                        % (짧, x.get('사슬') or x['클래스'] or x['태그'],
                           x['높이'], 누름최소, x['글']))

    mustmeasure.있어야한다(range(잰쪽), '잰 쪽', 최소=10, 어디=NEW)
    print('  쪽 %d개를 휴대폰 폭으로 그려 봤습니다 (%s)'
          % (잰쪽, '전수' if 전부 else '표본 — 전수는 --all'))
    print()

    if 받아들이기:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        _io.write(기준길, json.dumps({
            '_무엇인가': ('휴대폰에서 손가락보다 작은 누름자리의 '
                          '기준선입니다. 여기 있는 것은 **새로 생긴 '
                          '것이 아니라는 뜻**일 뿐입니다.'),
            '_기준': '%dpx — 애플·구글이 함께 권하는 값' % 누름최소,
            '알던것': sorted(막음),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(막음), os.path.relpath(기준길, ROOT)))
        return 0

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
        print('  손가락은 화살표가 아닙니다. 작은 단추는 옆 것을')
        print('  누르게 만듭니다 (주인 규칙 6-2).')
        return 1

    print('  · 엄지가 닿지 않는 단추가 새로 생기지 않았습니다 (쌓인 것 %d곳)'
          % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
