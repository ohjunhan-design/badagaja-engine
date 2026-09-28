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

# 가짜 쿠팡 — 정해진 크기의 네모를 그립니다. 바깥에 안 나갑니다.
가짜쿠팡 = r"""
window.PartnersCoupang = {
  G: function (o) {
    var 상자 = document.getElementById(o.container);
    if (!상자) return;
    var f = document.createElement('iframe');
    f.width = o.width; f.height = o.height;
    f.style.border = '0'; f.style.display = 'block';
    f.setAttribute('title', '시험용 가짜 광고');
    f.src = 'data:text/html,<body style="margin:0;background:#DDD"></body>';
    상자.appendChild(f);
  }
};
"""


def 재기(쪽길, 폭, 광고올까):
    """그 쪽을 그 폭으로 그려 잽니다.

    ★ iframe 으로 폭을 잡습니다 (2026-09-24 에 겪은 일)
      윈도우 크롬은 창을 500px 아래로 못 줄입니다. --window-size=375
      로 열어도 뷰포트가 485 가 나옵니다. 그것을 모르고 **멀쩡한
      CSS 를 두 번 고쳤습니다.** iframe 안에 넣으면 정확합니다.
    """
    t = tempfile.mkdtemp(prefix='ads-check-')
    try:
        # ★ 가짜 쿠팡은 쪽이 **뜨기 전에** 넣어야 합니다 (2026-09-26)
        #   처음에는 iframe 의 load 를 기다렸다 넣었는데, 그때는 이미
        #   ads.js 가 진짜 쿠팡을 받으려다 실패한 뒤였습니다.
        #   그래서 가짜를 넣어도 광고가 하나도 안 떴습니다.
        #
        #   쪽을 임시 자리에 베끼고 head 맨 앞에 끼웁니다.
        #   상대 주소가 깨지지 않게 <base> 로 원래 자리를 가리킵니다.
        #   진짜 site/ 는 한 글자도 안 건드립니다 (계약-09).
        바탕 = ('file:///'
                + os.path.dirname(os.path.abspath(쪽길)).replace(os.sep, '/')
                + '/')
        글 = io.read(쪽길, default='')
        끼울것 = '<base href="%s">' % 바탕
        if 광고올까:
            끼울것 += '<script>%s</script>' % 가짜쿠팡
        if '<head>' in 글:
            글 = 글.replace('<head>', '<head>' + 끼울것, 1)
        else:
            글 = 끼울것 + 글
        속 = os.path.join(t, 'p.html')
        io.write(속, 글)
        속주소 = 'file:///' + 속.replace(os.sep, '/')

        # ★ 손님처럼 **훑어 내립니다** (2026-09-26 겪은 일)
        #   처음에는 iframe 을 2400px 로 길게 늘여 한눈에 보려 했습니다.
        #   그런데 크롬은 **화면 밖에 있는 iframe 안의 관찰을 멈춥니다.**
        #   아래쪽 광고가 영영 관찰되지 않아 「안 뜬다」로 나왔습니다.
        #   창을 키워 봤지만 이번엔 느려져 결과를 못 받았습니다.
        #
        #   실제 손님은 화면 한 칸씩 스크롤해 내려갑니다. 그대로 합니다.
        #   광고를 늦게 부르는 것이 제대로 도는지도 이렇게 재야 맞습니다.
        # ★ 스크롤로 훑지 않습니다 (2026-09-26 겪은 일)
        #   처음에는 손님처럼 한 칸씩 훑어 내리게 했는데,
        #   setInterval 이 **가상 시간 예산을 다 써 버려** 결과를
        #   한 번도 못 받았습니다. 헤드리스 크롬의 가상 시간은
        #   타이머를 빨리 감는 대신 예산을 소모합니다.
        #
        #   ads.js 에 안전망(2초 뒤 그리기)이 있으니 스크롤이
        #   없어도 광고는 뜹니다. 기다리기만 합니다.
        #
        #   ※ 이 방식은 「화면에 다가오면 그리기」(관찰) 경로를
        #     재지 못합니다. 안전망 경로만 잽니다. 실제 브라우저에서
        #     관찰이 도는지는 눈으로 확인해야 합니다.
        겉 = ("""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0}iframe{border:0;display:block}</style>
</head><body>
<iframe id="F" src="%s" width="%d" height="2400"></iframe>
<script>
var f = document.getElementById('F');
f.addEventListener('load', function () {
  var d = f.contentDocument;
  setTimeout(function () {
    var s = d.createElement('script');
    s.textContent = %s;
    d.body.appendChild(s);
    var 잰것 = d.getElementById('_잰것');
    var out = document.createElement('div');
    out.id = 'R'; out.style.display = 'none';
    out.textContent = 잰것 ? 잰것.textContent : '{}';
    document.body.appendChild(out);
  }, 3200);          // ads.js 안전망 2초 + 들어왔나 폴링 0.5초 + 여유
});
</script></body></html>"""
              % (속주소, 폭, json.dumps(재는것)))
        p = os.path.join(t, 'z.html')
        io.write(p, 겉)
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--window-size=%d,1200' % max(폭 + 120, 1400),
             '--allow-file-access-from-files',
             # 바깥으로 안 나갑니다 — 시험이 인터넷에 흔들리면 안 됩니다
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--virtual-time-budget=10000', '--dump-dom',
             'file:///' + p.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=180)
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout or '', re.S)
        if not m:
            return None
        import html as _h
        return json.loads(_h.unescape(m.group(1)) or '{}')
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 볼쪽들():
    """갈래마다 하나씩. 416쪽을 다 그릴 수는 없습니다."""
    나옴 = []
    for 이름, 길 in (('첫화면', 'index.html'),
                     ('권역', 'taean.html'),
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

    # ── 1. ★ 광고가 안 올 때 — 가장 흔한 경우입니다
    print('[1] 광고가 **안 올 때** — 빈 자리가 남는가')
    print('      쿠팡이 느리거나 광고 차단기가 막으면 이렇게 됩니다')
    빈자리 = []
    for 이름, p in 볼것:
        for 폭, 폭이름 in 폭들:
            것 = 재기(p, 폭, 광고올까=False)
            if not 것:
                막음.append('%s %s — 못 쟀습니다 (광고 없는 경우)'
                            % (이름, 폭이름))
                continue
            편것 = [c for c in 것['칸'] if c['보임'] and c['높이'] > 4]
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
        for 폭, 폭이름 in 폭들:
            것 = 재기(p, 폭, 광고올까=True)
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
