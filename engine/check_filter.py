# -*- coding: utf-8 -*-
"""**걸러내기 단추를 누르면 정말 걸러지는가** (2026-10-08 밤)

★ 왜 이 검사가 있나

    바깥 검수 — 「`check_interact.py`·`check_visual.py` 는 지금 쪽에
    좋습니다. 특히 **「실제로 눌러 본다」**는 렌더 결과를 본다는
    기존 정적 검사와 역할이 다르기 때문에 충분히 가치가 있습니다.
    밤샘 중 새 checker 를 계속 늘리기보다는, **지금 있는 검사기로
    실제 결함을 더 많이 잡는 쪽을 우선하세요.**」

    그래서 **같은 방식**을 한 걸음 더 씁니다. 걸러내기 단추는
    이 사이트에서 손님이 가장 많이 누르는 것입니다. 포인트 쪽마다
    지형·대상 어종으로 거르고, 축제 쪽은 달로 거릅니다.

    그런데 **정말 걸러지는지**는 아무도 안 봤습니다. 자바스크립트가
    조용히 죽으면 단추는 눌리는데 목록이 그대로입니다. 손님은
    「이 권역엔 갯바위가 이렇게 많구나」 하고 잘못 압니다.

무엇을 하나

    크롬으로 쪽을 그린 뒤 걸러내기 단추를 **실제로 클릭**합니다.

      ① 누르기 전 — 보이는 카드 수
      ② 누른 뒤 — 수가 **줄었는가** (「전체」가 아닌 단추라면)
      ③ 그 단추가 말한 수와 **맞는가** (「감성돔 67」이면 67곳)
      ④ 「전체」를 다시 누르면 **원래대로** 돌아오는가

    ★ ③ 이 핵심입니다. 단추에 적힌 숫자와 실제로 걸러진 수가
      다르면, 손님은 **없는 것을 있다고 믿습니다.**

쓰는 법
    python engine/check_filter.py          표본
    python engine/check_filter.py --all    전수
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

재는스크립트 = r"""
<script>
(function () {
  function 보이나(e) {
    var s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    var r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function 센다(들) {
    var n = 0;
    for (var i = 0; i < 들.length; i++) if (보이나(들[i])) n++;
    return n;
  }
  function 재자() {
    var 난것 = { 폭: innerWidth, 걸러내기: [] };
    var 칸 = document.querySelector('.filter, .filters--fish, #filter');
    var 카드들 = document.querySelectorAll('.card, .fest-card, article.card');
    if (!칸 || !카드들.length) { 내자(난것); return; }

    var 단추들 = [].slice.call(칸.querySelectorAll('button'))
                   .filter(function (b) { return 보이나(b); });
    var 처음 = 센다(카드들);
    난것.처음 = 처음;

    for (var i = 0; i < 단추들.length && 난것.걸러내기.length < 4; i++) {
      var b = 단추들[i];
      var 글 = (b.textContent || '').trim();
      if (글 === '전체' || /^전체/.test(글)) continue;
      // 단추가 말하는 수 — `<b>67</b>` 이나 `<i>67</i>`
      var 숫 = b.querySelector('b, i');
      var 말한수 = 숫 ? parseInt((숫.textContent || '').replace(/[^\d]/g, ''), 10)
                      : null;
      b.click();
      var 뒤 = 센다(카드들);
      난것.걸러내기.push({
        글: 글.slice(0, 20), 말한수: 말한수, 처음: 처음, 뒤: 뒤
      });
    }
    // 「전체」로 되돌아오는가
    var 전체 = 단추들.filter(function (b) {
      return /^전체/.test((b.textContent || '').trim());
    })[0];
    if (전체) { 전체.click(); 난것.되돌림 = 센다(카드들); }
    내자(난것);
  }
  function 내자(난것) {
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    try { parent.document.body.appendChild(d); }
    catch (e) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 500);
  else addEventListener('load', function () { setTimeout(재자, 500); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=1280, 높이=3000):
    글 = _io.read(쪽길)
    글 = 글.replace('</body>', 재는스크립트 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-filter-')
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
                '--virtual-time-budget=4000', '--allow-file-access-from-files',
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
    """**걸러내기가 있는 쪽**을 자료에서 찾습니다."""
    난것 = []
    for p in _io.쪽들(NEW):
        글 = _io.read(p, default='')
        if ('class="filter"' in 글 or 'filters--fish' in 글
                or 'id="filter"' in 글):
            난것.append(p)
    난것.sort()
    if 전부:
        return 난것
    # 칸마다 둘씩 — 쪽 **종류**를 고루 봅니다
    칸별 = {}
    for p in 난것:
        칸 = os.path.dirname(os.path.relpath(p, NEW)) or '.'
        칸별.setdefault(칸, []).append(p)
    난것2 = []
    for 칸 in sorted(칸별):
        난것2 += 칸별[칸][:2]
    return 난것2


def main():
    전부 = '--all' in sys.argv
    자세히 = '--자세히' in sys.argv
    print()
    print('  걸러내기 단추를 누르면 정말 걸러지는가')
    print('  (2026-10-08 밤 — 「실제로 눌러 본다」를 한 걸음 더)')
    print()

    것들 = 볼쪽들(전부)
    mustmeasure.있어야한다(것들, '걸러내기가 있는 쪽', 최소=5, 어디=NEW)

    막음, 알림 = [], []
    잰쪽, 본단추 = 0, 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        try:
            잰것 = 쪽재기(p)
        except Exception as e:                        # noqa: BLE001
            알림.append('%s — 못 쟀습니다 (%s)' % (짧, str(e)[:40]))
            continue
        잰쪽 += 1
        for x in 잰것.get('걸러내기') or []:
            본단추 += 1
            if x['뒤'] == x['처음'] and x['처음'] > 1:
                막음.append('%s — 「%s」를 눌러도 **그대로** 입니다 '
                            '(%d → %d)'
                            % (짧, x['글'], x['처음'], x['뒤']))
            elif x['말한수'] is not None and x['뒤'] != x['말한수']:
                막음.append('%s — 「%s」가 **%d곳이라 했는데 %d곳** 입니다'
                            % (짧, x['글'], x['말한수'], x['뒤']))
            if 자세히:
                print('      %s 「%s」 %d → %d (말한 수 %s)'
                      % (짧, x['글'], x['처음'], x['뒤'], x['말한수']))
        되 = 잰것.get('되돌림')
        처 = 잰것.get('처음')
        if 되 is not None and 처 is not None and 되 != 처:
            막음.append('%s — 「전체」를 눌러도 **안 돌아옵니다** (%d → %d)'
                        % (짧, 처, 되))

    mustmeasure.있어야한다(range(잰쪽), '잰 쪽', 최소=5, 어디=NEW)
    print('  쪽 %d개 · 단추 %d개를 눌러 봤습니다 (%s)'
          % (잰쪽, 본단추, '전수' if 전부 else '표본 — 전수는 --all'))
    print()

    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:3]:
            print('  ~ %s' % t)
        print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        print()
        print('  단추에 적힌 수와 실제로 걸러진 수가 다르면,')
        print('  손님은 **없는 것을 있다고 믿습니다.**')
        return 1

    print('  · 누르면 걸러지고, 수도 단추 말과 맞습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
