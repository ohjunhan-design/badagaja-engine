# -*- coding: utf-8 -*-
"""광고를 **실제로 그려서** 봅니다 — 뜰 때와 안 뜰 때 둘 다.

★ 왜 이 검사가 따로 필요한가 (2026-09-26 바깥 검수 요구)

    「광고 슬롯 존재 → 슬롯 크기 정상 → 실제 광고/fixture 렌더링 →
      콘텐츠와 겹치지 않음 → 모바일에서 넘치지 않음 →
      **광고가 없어도 레이아웃이 무너지지 않음**

      특히 마지막이 중요합니다. 광고가 정상적으로 나오는 경우뿐
      아니라 광고가 안 나오는 경우도 봐야 합니다. 광고는 외부
      시스템이라 언제든 빈 공간이 될 수 있으니까요」

    맞는 말입니다. 광고가 뜬 화면만 보면 절반만 본 것입니다.
    쿠팡 서버가 느리거나, 광고 차단기가 막거나, 손님이 지하철
    안이면 광고는 안 옵니다. **그때가 더 흔합니다.**

왜 가짜 광고(fixture)를 쓰나
    진짜 쿠팡 광고를 받아 재면, 쿠팡이 그날 무엇을 보내느냐에 따라
    결과가 달라집니다. 시험이 바깥 것에 흔들리면 시험이 아닙니다.
    그래서 **정해진 크기의 가짜 배너**를 넣어 잽니다.

무엇을 보나
    1. 광고 칸이 쪽에 있는가 · 자료와 맞는가
    2. 광고가 **안 올 때** — 빈 자리가 남는가 (남으면 안 됩니다)
    3. 광고가 **왔을 때** — 가로로 넘치는가 · 글을 가리는가
    4. PC(1280) 와 휴대폰(360·375) 에서 각각 (주인 규칙 23)

★ 이 도구는 **읽기만 합니다** (계약-09)
★ 크롬으로만 봅니다 (주인 규칙 25 — 엣지는 쓰지 않습니다)

쓰는 법
    python engine/check_ads.py
    python engine/check_ads.py --strict
"""
import time
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
from engine._fake_coupang import 가짜쿠팡   # noqa: E402  가짜 쿠팡은 한 곳에만
from engine import io   # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

# 재 볼 폭 (주인 규칙 23 — 휴대폰과 PC 둘 다)
폭들 = [(360, '휴대폰 360'), (375, '휴대폰 375'), (1280, 'PC 1280')]

# 검사 등급 (계약-21)
막음, 알림 = [], []


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
def 광고자료():
    return io.read_json(os.path.join(DATA, 'raw', 'ads.json'), default={})


# ── 화면에서 잴 것 ────────────────────────────────────────
재는것 = r"""
(function () {
 try {
  var 나옴 = {폭: 0, 칸: [], 넘침: [], 겹침: []};
  var doc = document.documentElement;
  나옴.폭 = doc.clientWidth;
  나옴.가로스크롤 = doc.scrollWidth > doc.clientWidth + 1;
  나옴.스크롤폭 = doc.scrollWidth;

  var 칸들 = document.querySelectorAll('.ad-slot');
  for (var i = 0; i < 칸들.length; i++) {
    var c = 칸들[i];
    var r = c.getBoundingClientRect();
    var 숨 = c.hasAttribute('hidden');
    var 스타일 = window.getComputedStyle(c);
    나옴.칸.push({
      이름: c.getAttribute('data-ad-slot'),
      기기: c.getAttribute('data-ad-device'),
      숨음: 숨,
      상태: c.getAttribute('data-ad-state') || '',
      폭: Math.round(r.width), 높이: Math.round(r.height),
      왼쪽: Math.round(r.left), 오른쪽: Math.round(r.right),
      보임: 스타일.display !== 'none'
    });
    if (r.height > 4 && r.width > 0) {
      if (r.right > doc.clientWidth + 1 || r.left < -1) {
        나옴.넘침.push({이름: c.getAttribute('data-ad-slot'),
                        왼쪽: Math.round(r.left),
                        오른쪽: Math.round(r.right),
                        화면: doc.clientWidth});
      }
      // 광고가 글을 가리는가 — 같은 자리에 겹친 글이 있는지
      //
      // ★ 화면 **안에 있을 때만** 봅니다 (2026-09-26 겪은 일)
      //   elementFromPoint 는 지금 보이는 화면 기준입니다. 광고가
      //   화면 밖에 있는데 좌표를 화면 안으로 끌어다 물으면,
      //   **엉뚱한 자리의 글**을 집어 「광고가 글을 가린다」고
      //   합니다. 헛것을 다섯 번 냈습니다.
      var 화면안 = r.top >= 0 && r.bottom <= doc.clientHeight;
      if (화면안) {
        var 가운데 = document.elementFromPoint(
          Math.round(r.left + r.width / 2),
          Math.round(r.top + r.height / 2));
        if (가운데 && !c.contains(가운데) && 가운데 !== c) {
          var 덮은글 = (가운데.textContent || '').trim().slice(0, 20);
          if (덮은글) {
            나옴.겹침.push({이름: c.getAttribute('data-ad-slot'), 글: 덮은글});
          }
        }
      }
    }
  }
  var e = document.createElement('div');
  e.id = '_잰것'; e.style.display = 'none';
  e.textContent = JSON.stringify(나옴);
  document.body.appendChild(e);
 } catch (err) {
  // ★ 재다가 넘어져도 조용히 사라지지 않게 합니다.
  //   전에는 오류가 나면 아무것도 안 내놓아, 「못 쟀습니다」만 보고
  //   왜 못 쟀는지 알 수가 없었습니다.
  var e2 = document.createElement('div');
  e2.id = '_잰것'; e2.style.display = 'none';
  e2.textContent = JSON.stringify({오류: String(err && err.message || err)});
  document.body.appendChild(e2);
 }
})();
"""

# 가짜 쿠팡은 engine/_fake_coupang.py 한 곳에만 둡니다 (계약-01)


def 재기여럿(쪽길, 폭들, 광고올까):
    """그 쪽을 **여러 폭으로 한 판에** 그려 잽니다 → {폭: 잰것}

    ★ 왜 (2026-10-07 바깥 검수)
      옛 `재기()` 는 **폭마다 크롬을 새로 띄웁니다.**
      5쪽 × 3폭 × 광고 2상태 = **크롬 30번** · 20.6초였습니다.
      크롬 한 번이 **0.65초**이니 띄우는 횟수가 거의 전부입니다.

      `check_mobile` 이 이미 같은 수를 씁니다 —
        「쪽 하나를 **일곱 번 다시 그리느라 15분**이 걸렸습니다.
          한 쪽에 iframe 일곱을 나란히 두면 크롬은 **38번**이면 됩니다」

    ★ **광고 있음/없음은 안 섞습니다** (바깥 검수)
      쪽이 **뜨기 전에** 가짜 쿠팡을 끼워야 하므로, 한 판에 섞으면
      한쪽이 다른 쪽의 스크립트를 봅니다. 그래서 **폭만** 묶습니다.

    ★ 옛 `재기()` 와 **같은 답**을 내야 합니다 — `--ab` 로 견줍니다.
    """
    t = tempfile.mkdtemp(prefix='ads-many-')
    try:
        바탕 = ('file:///'
                + os.path.dirname(os.path.abspath(쪽길)).replace(os.sep, '/')
                + '/')
        글 = io.read(쪽길, default='')
        끼울것 = '<base href="%s">' % 바탕
        if 광고올까:
            끼울것 += '<script>%s</script>' % 가짜쿠팡
        낮은 = 글.lower()
        자리 = 낮은.find('<head>')
        if 자리 >= 0:
            새글 = 글[:자리 + 6] + 끼울것 + 글[자리 + 6:]
        else:
            새글 = 끼울것 + 글
        속 = os.path.join(t, '속.html')
        io.write(속, 새글)
        속주소 = 'file:///' + 속.replace(os.sep, '/')

        틀 = ''.join(
            '<iframe id="F%d" src="%s" width="%d" height="2400"></iframe>'
            % (i, 속주소, 폭) for i, 폭 in enumerate(폭들))
        목록 = '[' + ','.join('["F%d",%d]' % (i, 폭)
                              for i, 폭 in enumerate(폭들)) + ']'

        겉 = ("""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0}iframe{border:0;display:block;float:left}
</style></head><body>
%s
<div id="R" style="display:none">?</div>
<script>
var 틀들 = %s;
var 남은 = 틀들.length;
var 모은것 = {};
function 하나재기(아이디, 폭) {
  var f = document.getElementById(아이디);
  var d = f.contentDocument;
  var s = d.createElement('script');
  s.textContent = %s;
  d.body.appendChild(s);
  var 잰것 = d.getElementById('_잰것');
  모은것[String(폭)] = 잰것 ? 잰것.textContent : '{}';
}
/* ★ **모두 뜬 뒤 한 번에** 잽니다 — iframe 셋이 제각기 끝납니다 */
function 다왔나() {
  남은 -= 1;
  if (남은 > 0) { return; }
  setTimeout(function () {
    for (var i = 0; i < 틀들.length; i++) {
      try { 하나재기(틀들[i][0], 틀들[i][1]); }
      catch (e) { 모은것[String(틀들[i][1])] = null; }
    }
    var R = document.getElementById('R');
    R.textContent = JSON.stringify(모은것);
    /* ★ **계약된 측정이 모두 끝났다**는 신호 (바깥 검수)
       「『무언가 나왔다』가 아니라 『계약된 측정이 모두 끝났다』」 */
    R.setAttribute('data-다잿음', String(틀들.length));
  }, 3200);   /* ads.js 안전망 2초 + 폴링 0.5초 + 여유 — 건드리지 않습니다 */
}
for (var i = 0; i < 틀들.length; i++) {
  document.getElementById(틀들[i][0])
          .addEventListener('load', 다왔나);
}
</script></body></html>""" % (틀, 목록, json.dumps(재는것)))

        p = os.path.join(t, 'z.html')
        io.write(p, 겉)
        빈것 = dict((폭, None) for 폭 in 폭들)
        # ★ **짧게 한 번 · 다 못 쟀으면 길게 한 번** (바깥 검수)
        for 예산 in (6000, 15000):
            r = subprocess.run(
                machine.크롬앞머리() + [
                 '--window-size=%d,1200' % (sum(폭들) + 200),
                 '--allow-file-access-from-files',
                 '--host-resolver-rules=MAP * 127.0.0.1:1',
                 '--virtual-time-budget=%d' % 예산, '--dump-dom',
                 'file:///' + p.replace(os.sep, '/')],
                capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=180)
            글2 = r.stdout or ''
            다잿나 = ('data-다잿음="%d"' % len(폭들)) in 글2
            if 다잿나:
                break
        if not 다잿나:
            return 빈것
        m = re.search(r'id="R"[^>]*>(.*?)</div>', 글2, re.S)
        if not m:
            return 빈것
        import html as _html
        try:
            덩이 = json.loads(_html.unescape(m.group(1)))
        except ValueError:
            return 빈것
        나옴 = {}
        for 폭 in 폭들:
            속글 = 덩이.get(str(폭))
            if not 속글:
                나옴[폭] = None
                continue
            try:
                나옴[폭] = json.loads(_html.unescape(속글))
            except ValueError:
                나옴[폭] = None
        return 나옴
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 볼쪽들():
    """갈래마다 하나씩. 416쪽을 다 그릴 수는 없습니다."""
    나옴 = []
    for 이름, 길 in (('첫화면', 'index.html'),
                     ('권역', 'taean.html'),
                     # ★ 2026-09-30 — 제주만 다른 광고(제주패스)가 뚜니다.
                     #   표본이 태안 하나만이면 그것을 영영 못 봅니다.
                     ('권역·제주', 'aewol.html'),
                     ('포인트목록', None),
                     ('어종', None)):
        if 길:
            p = os.path.join(NEW, 길)
            if os.path.exists(p):
                나옴.append((이름, p))
            continue
        if 이름 == '포인트목록':
            것 = sorted(glob.glob(os.path.join(NEW, 'point', '**', '*.html'),
                                  recursive=True))
        else:
            것 = sorted(glob.glob(os.path.join(NEW, 'fish', '*.html')))
            것 = [x for x in 것 if not x.endswith('index.html')]
        if 것:
            나옴.append((이름, 것[0]))
    return 나옴


def main():
    a = 광고자료()
    print('광고를 실제로 그려서 봅니다')
    print('  가짜 배너로 잽니다 — 쿠팡 서버에 기대면 시험이 아닙니다')
    print('')

    if not a.get('켬'):
        print('광고가 꺼져 있습니다 (data/raw/ads.json 의 "켬": false)')
        print('  자리만 확인하고 마칩니다.')

    # ── 0. 자료와 쪽이 맞는가
    print('[0] 자료에 적은 자리가 쪽에 있는가')
    적은자리 = set(k for k, v in (a.get('자리') or {}).items()
                   if not k.startswith('_') and v.get('켬'))
    쪽에있는자리 = set()
    쪽수 = 0
    for p in glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True):
        s = io.read(p, default='')
        것 = re.findall(r'data-ad-slot="([^"]+)"', s)
        if 것:
            쪽수 += 1
            쪽에있는자리.update(것)
    print('      자료에 켠 자리 %d개 · 쪽에 있는 자리 %d개 (쪽 %d개)'
          % (len(적은자리), len(쪽에있는자리), 쪽수))
    없는것 = sorted(적은자리 - 쪽에있는자리)
    남는것 = sorted(쪽에있는자리 - 적은자리)
    if 없는것:
        막음.append('자료에 켰는데 쪽에 없는 자리 %d개' % len(없는것))
        print('  ✗ 자료에 켰는데 쪽에 없습니다: %s' % ' · '.join(없는것))
    if 남는것:
        막음.append('쪽에 있는데 자료에 없는 자리 %d개' % len(남는것))
        print('  ✗ 쪽에 있는데 자료에 없습니다: %s' % ' · '.join(남는것))
    if not (없는것 or 남는것):
        print('  · 자료와 쪽이 맞습니다')
    print('')

    볼것 = 볼쪽들()
    if not 볼것:
        print('볼 쪽이 없습니다. 먼저 build.py 로 만드세요.')
        return 1

    # ── 0-2. 쿠팡을 **부르는 꼴**이 맞는가
    #
    #   ★ 2026-09-30 주인 지적 — 「이 부분에 쿠팡 광고 사라짐」
    #
    #     배너 번호는 첫번째도전과 **똑같았는데도**(PC 1032048 ·
    #     휴대폰 1032049) 이쪽에서만 광고가 한 장도 안 떴습니다.
    #     옛 js/ads.js 와 견주니 **부르는 꼴**이 달랐습니다.
    #
    #       옛것 : width: String(W)         container: slot(요소)
    #       내것 : width: 배너['가로'](수)    container: 아이디(글자)
    #
    #     쿠팡 g.js 는 앞의 꼴을 기대합니다. 뒤의 꼴로 부르면
    #     **예외를 던지고 조용히 아무것도 안 그립니다.**
    #     오류 화면도 없고 쪽도 멀쩡해 보여, 사람이 「광고가
    #     사라졌네」 하고 알아차릴 때까지 아무도 모릅니다.
    #
    #   아래 시험들은 **가짜 배너**로 그려 보므로 이것을 못 잡습니다 —
    #   진짜 쿠팡을 안 부르니까요. 그래서 **코드를 글자로** 봅니다.
    print('[0-2] 쿠팡을 부르는 꼴이 맞는가 ★')
    광고js = io.read(os.path.join(NEW, 'assets', 'js', 'ads.js'), default='')
    꼴탈 = []
    if 'PartnersCoupang' in 광고js:
        m = re.search(r'new\s+window\.PartnersCoupang\.G\s*\(\s*\{(.*?)\}\s*\)',
                      광고js, re.S)
        if not m:
            꼴탈.append('PartnersCoupang.G 를 부르는 곳을 못 찾았습니다')
        else:
            속 = m.group(1)
            if not re.search(r'width\s*:\s*String\(', 속):
                꼴탈.append('width 를 String() 으로 안 감쌌습니다')
            if not re.search(r'height\s*:\s*String\(', 속):
                꼴탈.append('height 를 String() 으로 안 감쌌습니다')
            if not re.search(r'container\s*:\s*[^,}]*querySelector', 속):
                꼴탈.append('container 에 **요소**를 안 넘겼습니다 '
                            '(아이디 글자를 주면 안 그려집니다)')
    if 꼴탈:
        막음.append('쿠팡을 부르는 꼴 %d가지' % len(꼴탈))
        print('  ✗ 부르는 꼴이 틀렸습니다 — 광고가 한 장도 안 뜹니다')
        for x in 꼴탈:
            print('      %s' % x)
        print('      → 첫번째도전 js/ads.js 와 같은 꼴로 부릅니다.')
    else:
        print('  · width·height 는 글자로, container 는 요소로 넘깁니다')
    print('')

    def _링크배너인가(자리이름):
        """그 자리가 **링크 배너**(제공: link)인가.

        ★ 2026-10-01 — 링크 배너는 바깥에 안 기대므로
          「광고가 안 올 때」 시험에서 봐줍니다.
        """
        자리 = (광고자료().get('자리') or {}).get(자리이름 or '')
        if not 자리:
            return False
        배너 = (광고자료().get('배너') or {}).get(자리.get('배너') or '')
        return bool(배너) and 배너.get('제공') == 'link'

    # ── 1. ★ 광고가 안 올 때 — 가장 흔한 경우입니다
    print('[1] 광고가 **안 올 때** — 빈 자리가 남는가')
    print('      쿠팡이 느리거나 광고 차단기가 막으면 이렇게 됩니다')
    빈자리 = []
    for 이름, p in 볼것:
        # ★ **폭 3개를 한 판에** 그립니다 (2026-10-07 바깥 검수)
        #   전에는 폭마다 크롬을 새로 띄워 쪽 하나에 크롬 3번,
        #   모두 **30번** · 20.6초였습니다. 크롬 한 번이 0.65초라
        #   **띄우는 횟수가 거의 전부**입니다. iframe 셋을 나란히
        #   두어 **10번**으로 줄였습니다 (A/B 로 같은 답 확인).
        한판 = 재기여럿(p, [폭 for 폭, _ in 폭들], False)
        for 폭, 폭이름 in 폭들:
            것 = 한판.get(폭)
            if not 것:
                막음.append('%s %s — 못 쟀습니다 (광고 없는 경우)'
                            % (이름, 폭이름))
                continue
            # ★ **링크 배너는 봐줍니다** (2026-10-01)
            #   이 시험은 「바깥(쿠팡)이 안 올 때」를 봅니다.
            #   제주패스 같은 **링크 배너는 우리가 직접 그립니다** —
            #   바깥 스크립트를 안 받으니 「안 올 때」가 없습니다.
            #   광고 차단기도 잘 안 막습니다. 늘 떠 있는 것이 맞습니다.
            편것 = [c for c in 것['칸']
                    if c['보임'] and c['높이'] > 4
                    and not _링크배너인가(c.get('이름'))]
            if 편것:
                빈자리.append('%s %s — %s (높이 %dpx)'
                              % (이름, 폭이름, 편것[0]['이름'],
                                 편것[0]['높이']))
            if 것.get('가로스크롤'):
                막음.append('%s %s — 광고 없이도 가로로 넘칩니다'
                            % (이름, 폭이름))
    if 빈자리:
        막음.append('광고가 안 왔는데 자리가 남음 %d건' % len(빈자리))
        print('  ✗ 광고가 없는데 빈 자리가 남습니다 %d건' % len(빈자리))
        for x in 빈자리[:4]:
            print('      %s' % x)
    else:
        print('  · 광고가 안 오면 자리를 아예 안 씁니다 — 쪽이 멀쩡합니다')
    print('')

    # ── 2. 광고가 왔을 때
    print('[2] 광고가 **왔을 때** — 넘치는가 · 글을 가리는가')
    안뜬것 = []
    for 이름, p in 볼것:
        # ★ **폭 3개를 한 판에** 그립니다 (2026-10-07 바깥 검수)
        #   전에는 폭마다 크롬을 새로 띄워 쪽 하나에 크롬 3번,
        #   모두 **30번** · 20.6초였습니다. 크롬 한 번이 0.65초라
        #   **띄우는 횟수가 거의 전부**입니다. iframe 셋을 나란히
        #   두어 **10번**으로 줄였습니다 (A/B 로 같은 답 확인).
        한판 = 재기여럿(p, [폭 for 폭, _ in 폭들], True)
        for 폭, 폭이름 in 폭들:
            것 = 한판.get(폭)
            if not 것:
                # ★ 못 쟀으면 **막습니다** (2026-09-26)
                #   알림으로 두었더니 12건 전부 못 쟀는데도
                #   「광고가 뜰 때도 안 뜰 때도 멀쩡합니다」라고
                #   통과시켰습니다. 안 재고 통과하는 것이 가장 나쁩니다.
                막음.append('%s %s — 못 쟀습니다 (재지 못한 것은 '
                            '「멀쩡하다」가 아닙니다)' % (이름, 폭이름))
                continue
            뜬것 = [c for c in 것['칸'] if c['높이'] > 4]
            기대 = [c for c in 것['칸']
                    if (c['기기'] == 'pc') == (폭 >= 768)]
            if 기대 and not 뜬것:
                안뜬것.append('%s %s' % (이름, 폭이름))
            for c in 뜬것:
                print('      %-8s %-10s %-22s %4dx%-4d'
                      % (이름, 폭이름, c['이름'], c['폭'], c['높이']))
            if 것.get('넘침'):
                for x in 것['넘침']:
                    막음.append('%s %s — %s 가 화면 밖으로 (%d > %d)'
                                % (이름, 폭이름, x['이름'],
                                   x['오른쪽'], x['화면']))
            if 것.get('가로스크롤'):
                막음.append('%s %s — 광고 때문에 가로로 넘칩니다 (%d > %d)'
                            % (이름, 폭이름, 것['스크롤폭'], 것['폭']))
            for x in (것.get('겹침') or []):
                막음.append('%s %s — %s 가 글을 가립니다 (%s)'
                            % (이름, 폭이름, x['이름'], x['글']))
    if 안뜬것:
        # ★ 이것은 **막음**입니다 (2026-09-26)
        #   처음에는 알림으로 두었더니, 광고가 한 번도 안 뜨는데도
        #   「광고가 뜰 때도 안 뜰 때도 멀쩡합니다」라고 통과시켰습니다.
        #   안 뜬 것을 안 잡으면, 광고가 영영 안 떠도 모릅니다.
        막음.append('가짜 광고를 넣었는데 안 뜬 곳 %d건' % len(안뜬것))
        print('  ✗ 가짜 광고를 넣었는데 안 떴습니다 %d건' % len(안뜬것))
        for x in 안뜬것[:4]:
            print('      %s' % x)
        print('      → 광고를 넣어도 안 뜬다는 뜻입니다. 수입이 0 이 됩니다.')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림[:6]:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음[:10]:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0
    print('광고가 뜰 때도 안 뜰 때도 쪽이 멀쩡합니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
