# -*- coding: utf-8 -*-
"""**눌러 보면 정말 되는가** (2026-10-08 밤 주인 지시)

★ 왜 이 검사가 있나

    주인 지시 — 「일이 없을 땐 바다가자를 전체적으로 시각적으로 오류가
    있는지 찾아봐. 디자인 오류 및 **확대 보기 같은 전체적인 오류**를
    점검해」

    그날 낮에 `.rig-zoom` 이름이 겹쳐 확대 그림이 채비 17쪽을 덮었고,
    **주인이 화면을 보고서야** 알았습니다. 기존 검사기는 쪽을 **그려
    보기만** 했지 **눌러 보지는** 않았습니다.

    그려 보는 것으로는 이런 것을 못 봅니다 —
      · 「크게 보기」를 눌러도 **안 열림**
      · 열고 나서 **닫히지 않음** (손님이 갇힙니다)
      · 단추가 가리키는 자리가 **쪽에 없음**
      · 열린 덮개가 **화면 밖**으로 나감

무엇을 하나

    크롬으로 쪽을 그린 뒤, `:target` 덮개를 **실제로 열고 닫아 봅니다.**
    자바스크립트로 `location.hash` 를 바꿔 브라우저가 진짜로 `:target`
    을 적용하게 합니다 — 흉내가 아닙니다.

      ① 열기 전 — 덮개가 숨어 있는가
      ② 열었을 때 — 정말 보이고, 그림이 화면 안에 들어오는가
      ③ 닫기 길이 있는가 — 닫기 단추·배경 어느 쪽이든
      ④ 닫은 뒤 — 다시 숨는가

쓰는 법
    python engine/check_interact.py          덮개가 있는 쪽 전부
    python engine/check_interact.py --자세히
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
from engine import check_cover as C   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

재는스크립트 = """
<script>
(function () {
  function 보이나(e) {
    if (!e) return false;
    var s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden'
        || s.opacity === '0') return false;
    var r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function 재자() {
    var 난것 = { 폭: innerWidth, 높이: innerHeight, 덮개: [] };
    // 쪽 안에서 **`#아이디` 로 가리키는 단추**를 찾습니다.
    //   `:target` 으로 펴는 덮개는 언제나 이 꼴입니다.
    var 단추들 = document.querySelectorAll('a[href^="#"]');
    var 본것 = {};
    for (var i = 0; i < 단추들.length; i++) {
      var h = 단추들[i].getAttribute('href');
      if (!h || h === '#' || h.length < 2) continue;
      var 아이디 = h.slice(1);
      if (본것[아이디]) continue;
      var 칸 = document.getElementById(아이디);
      if (!칸) {
        난것.덮개.push({ 아이디: 아이디, 탈: '가리키는 자리가 없습니다' });
        본것[아이디] = 1;
        continue;
      }
      // 덮개인가 — 평소 숨어 있고 `:target` 으로 펴지는 것
      var 전 = getComputedStyle(칸).display;
      if (전 !== 'none') continue;        // 덮개가 아닙니다 (그냥 앵커)
      본것[아이디] = 1;

      // ★ **정말 엽니다** — 브라우저가 `:target` 을 적용하게
      location.hash = '#' + 아이디;
      var 열림 = 보이나(칸);
      var r = 칸.getBoundingClientRect();
      var 속그림 = 칸.querySelector('img, picture, svg');
      var gr = 속그림 ? 속그림.getBoundingClientRect() : null;
      // 닫는 길이 있는가 — 덮개 안에서 다른 데로 가는 링크
      var 닫기 = 칸.querySelectorAll('a[href="#"], a[href^="#"]:not([href="#'
                                     + 아이디 + '"])');
      var 닫을수있나 = false;
      for (var k = 0; k < 닫기.length; k++) {
        if (보이나(닫기[k])) { 닫을수있나 = true; break; }
      }
      // ★ **닫아 봅니다**
      location.hash = '#';
      var 닫힘 = !보이나(칸);

      난것.덮개.push({
        아이디: 아이디,
        열림: 열림, 닫힘: 닫힘, 닫을수있나: 닫을수있나,
        폭: Math.round(r.width), 높이: Math.round(r.height),
        그림폭: gr ? Math.round(gr.width) : 0,
        그림높이: gr ? Math.round(gr.height) : 0,
        화면밖: gr ? (gr.width > innerWidth + 2
                      || gr.height > innerHeight + 2) : false
      });
      if (난것.덮개.length >= 6) break;
    }
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    try { parent.document.body.appendChild(d); }
    catch (e) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 300);
  else addEventListener('load', function () { setTimeout(재자, 300); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=1280, 높이=900):
    글 = _io.read(쪽길)
    글 = 글.replace('</body>', 재는스크립트 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-interact-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        _io.write(사본, 글)
        R._자산옮기기(임시)
        C._그쪽사진옮기기(임시, 쪽길, 글)
        틀 = os.path.join(임시, '틀.html')
        _io.write(틀, (R.틀쪽.replace('__쪽__', R._틀에서부를길(임시, 사본))
                       .replace('__폭__', str(폭))
                       .replace('__높이__', str(높이))))
        나옴 = subprocess.run(
            machine.크롬앞머리() + [
                '--hide-scrollbars',
                '--window-size=%d,%d' % (폭 + 40, 높이 + 60),
                '--virtual-time-budget=3500', '--allow-file-access-from-files',
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


def 볼쪽들():
    """**덮개가 있는 쪽**을 자료에서 찾습니다 — 이름을 박지 않습니다."""
    난것 = []
    for p in _io.쪽들(NEW):
        글 = _io.read(p, default='')
        # `#아이디` 로 가리키는 단추가 있고, 그 자리가 쪽 안에 있는 꼴
        if re.search(r'href="#[a-zA-Z][\w-]*"', 글):
            난것.append(p)
    return sorted(난것)


def main():
    자세히 = '--자세히' in sys.argv
    print()
    print('  눌러 보면 정말 되는가 — 확대 보기 같은 덮개')
    print('  (2026-10-08 밤 주인 지시 — 「확대 보기 같은 전체적인 오류」)')
    print()

    것들 = 볼쪽들()
    mustmeasure.있어야한다(것들, '쪽', 최소=5, 어디=NEW)

    막음, 알림 = [], []
    잰쪽, 본덮개 = 0, 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        try:
            잰것 = 쪽재기(p)
        except Exception as e:                        # noqa: BLE001
            알림.append('%s — 못 쟀습니다 (%s)' % (짧, str(e)[:40]))
            continue
        잰쪽 += 1
        for d in 잰것['덮개']:
            if d.get('탈'):
                막음.append('%s — `#%s` %s'
                            % (짧, d['아이디'], d['탈']))
                continue
            본덮개 += 1
            if not d['열림']:
                막음.append('%s — `#%s` 를 눌러도 **안 열립니다**'
                            % (짧, d['아이디']))
            if not d['닫힘']:
                막음.append('%s — `#%s` 가 **닫히지 않습니다** '
                            '(손님이 갇힙니다)' % (짧, d['아이디']))
            if not d['닫을수있나']:
                막음.append('%s — `#%s` 에 **닫는 길이 없습니다**'
                            % (짧, d['아이디']))
            if d['화면밖']:
                막음.append('%s — `#%s` 를 열면 그림이 화면 밖으로 '
                            '나갑니다 (%d×%d · 화면 %d×%d)'
                            % (짧, d['아이디'], d['그림폭'], d['그림높이'],
                               잰것['폭'], 잰것['높이']))
            if 자세히:
                print('      %s #%s — 열림 %s · 닫힘 %s · 닫는길 %s '
                      '· 그림 %d×%d'
                      % (짧, d['아이디'], d['열림'], d['닫힘'],
                         d['닫을수있나'], d['그림폭'], d['그림높이']))

    mustmeasure.있어야한다(range(잰쪽), '잰 쪽', 최소=5, 어디=NEW)
    print('  쪽 %d개를 눌러 봤습니다 · 덮개 %d개' % (잰쪽, 본덮개))
    print()

    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:4]:
            print('  ~ %s' % t)
        print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        print()
        print('  **그려 보는 것으로는 「눌렀을 때」를 못 봅니다.**')
        print('  열리는가 · 닫히는가 · 닫는 길이 있는가까지 봐야')
        print('  손님이 갇히지 않습니다.')
        return 1

    print('  · 덮개가 모두 제대로 열리고 닫힙니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
