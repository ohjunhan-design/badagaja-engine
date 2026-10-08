# -*- coding: utf-8 -*-
"""**첫 화면에 무엇이 보이는가** — 주인 규칙 6-2 를 돕습니다

★ 왜 (2026-10-09)

  주인 규칙 6-2 는 기계가 재는 것과 사람이 보는 것을 갈라 두고,
  사람 쪽에 이렇게 적어 두셨습니다.

    · 첫 화면에서 무엇이 먼저 보이는가
    · 핵심을 3~5초에 아는가
    · 다음에 무엇을 누를지 바로 보이는가

  이것은 **기계가 판정할 수 없습니다.** 다만 **무엇이 거기
  있는지 적어 드릴 수는 있습니다.** 그러면 주인이 「이게 먼저
  보여야 하는데」를 짚으실 수 있습니다.

  가리는 도구가 아니라 **보여 드리는 도구**입니다
  (`photo_sheet.py` 와 같은 뜻).

쓰는 법 — `python engine/firstscreen.py [쪽 ...]`
  쪽을 안 적으면 갈래마다 하나씩 봅니다.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
sys.path.insert(0, 여기)

import mustmeasure   # noqa: E402

막음, 알림 = [], []        # 계약-21 — 모듈 수준에 둡니다

폰폭, 폰높 = 390, 844       # 아이폰 세로 한 화면
기본쪽 = [
    'index.html', 'taean.html', 'gear.html', 'muldae.html',
    'rig/index.html', 'rig/bottom.html', 'fish/index.html',
    'catch/index.html', 'travel/index.html', 'festival/index.html',
    'point/chungnam/taean_gleaning.html',
]

잼 = """
(function(){
  function 글(el){ return (el.textContent||'').replace(/\s+/g,' ').trim(); }
  var 난것 = { 제목:[], 단추:[], 그림:[], 숫자:[], 넘김:0 };
  var 바닥 = %d;
  document.querySelectorAll('h1,h2,h3').forEach(function(el){
    var b = el.getBoundingClientRect();
    if (b.top < 바닥 && b.bottom > 0 && 글(el))
      난것.제목.push(Math.round(b.top) + 'px ' + 글(el).slice(0,34));
  });
  document.querySelectorAll('a,button').forEach(function(el){
    var b = el.getBoundingClientRect();
    if (b.top < 바닥 && b.bottom > 0 && b.height >= 28 && 글(el))
      난것.단추.push(Math.round(b.top) + 'px ' + 글(el).slice(0,24));
  });
  document.querySelectorAll('img,svg,picture').forEach(function(el){
    var b = el.getBoundingClientRect();
    if (b.top < 바닥 && b.bottom > 0 && b.width > 60 && b.height > 40)
      난것.그림.push(Math.round(b.top) + 'px ' +
                   Math.round(b.width) + 'x' + Math.round(b.height));
  });
  var 글전체 = 글(document.body);
  var 수 = 글전체.match(/[0-9][0-9,]{1,8}(곳|개|권역|가지|장|km|m)/g);
  난것.숫자 = (수 || []).slice(0, 6);
  난것.넘김 = Math.round(document.body.scrollHeight / 바닥 * 10) / 10;
  var d = document.createElement('div');
  d.id = '__첫화면__'; d.style.display = 'none';
  d.textContent = JSON.stringify(난것);
  document.body.appendChild(d);
})();
""" % 폰높


def _크롬():
    for 후보 in (r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                 r'C:\Program Files (x86)\Google\Chrome\Application'
                 r'\chrome.exe',
                 '/usr/bin/google-chrome', '/usr/bin/chromium-browser'):
        if os.path.exists(후보):
            return 후보
    return None


def 한쪽재기(크롬, 쪽길, 터):
    """쪽을 **같은 폴더에** 복사해 띄웁니다 — 차림표를 잃지 않게.

    ★ 임시 폴더로 옮겨 띄웠다가 **차림표를 하나도 못 불러** 넘침이
      0 으로 나온 적이 있습니다 (2026-10-09). 쪽이 깨끗해서가
      아니라 **민낯으로 그려진 것**이었습니다.
    """
    잰것 = 쪽길 + '.__재는중__.html'
    글 = io.open(쪽길, encoding='utf-8').read()
    글 = 글.replace('</body>', '<script>%s</script></body>' % 잼, 1)
    io.open(잰것, 'w', encoding='utf-8').write(글)
    냄 = os.path.join(터, 'dom.html')
    try:
        subprocess.run(
            [크롬, '--headless=new', '--disable-gpu', '--hide-scrollbars',
             '--window-size=%d,%d' % (폰폭, 폰높),
             '--virtual-time-budget=5000', '--dump-dom',
             'file:///' + os.path.abspath(잰것).replace(os.sep, '/')],
            stdout=io.open(냄, 'w', encoding='utf-8', errors='replace'),
            stderr=subprocess.DEVNULL, timeout=90)
        돔 = io.open(냄, encoding='utf-8', errors='replace').read()
    finally:
        try:
            os.remove(잰것)
        except OSError:
            pass
    m = re.search(r'id="__첫화면__"[^>]*>(.*?)</div>', 돔, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def main():
    크롬 = _크롬()
    if not 크롬:
        print('  ✗ 크롬을 못 찾았습니다 — **못 쟀습니다**')
        return 4

    쪽들 = sys.argv[1:] or 기본쪽
    mustmeasure.있어야한다(쪽들, '볼 쪽', 최소=1, 어디='site/')

    터 = tempfile.mkdtemp()
    잰것, 못쟨것 = [], []
    for 쪽 in 쪽들:
        길 = os.path.join(뿌리, 'site', *쪽.split('/'))
        if not os.path.exists(길):
            못쟨것.append(쪽)
            continue
        난것 = 한쪽재기(크롬, 길, 터)
        if 난것 is None:
            못쟨것.append(쪽)
            continue
        잰것.append((쪽, 난것))

    mustmeasure.있어야한다(잰것, '잰 쪽', 최소=1, 어디='site/')

    print()
    print('  휴대폰 첫 화면(%d×%d)에 무엇이 보이나 — 쪽 %d개'
          % (폰폭, 폰높, len(잰것)))
    print('  ★ 이것은 **판정이 아닙니다.** 무엇이 거기 있는지만')
    print('    적습니다 (주인 규칙 6-2 — 사람 눈이 봐야 하는 것).')
    print()
    for 쪽, x in 잰것:
        print('  ── %s   (다 보려면 %.1f 화면)' % (쪽, x['넘김']))
        for 어디, 것들 in (('제목', x['제목']), ('누를 것', x['단추']),
                         ('그림', x['그림'])):
            if 것들:
                print('     %-6s %s' % (어디, ' · '.join(것들[:4])))
            else:
                print('     %-6s (없음)' % 어디)
        if x['숫자']:
            print('     %-6s %s' % ('숫자', ' · '.join(x['숫자'])))
        print()

    if 못쟨것:
        print('  못 잰 쪽 %d개 — %s' % (len(못쟨것), ' · '.join(못쟨것[:5])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
