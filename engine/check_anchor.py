# -*- coding: utf-8 -*-
"""**눌러 뛰면 제목이 머리띠에 묻히는가** (2026-10-09)

★ 어떻게 찾았나

  지피티 실행팀이 「스크롤 앵커가 **하단 내비**에 가리는지
  확인하라」고 했습니다. 재 보니 가리는 쪽은 **아래가 아니라
  위**였습니다.

  머리띠가 `position:sticky` 라 늘 화면 위에 떠 있습니다
  (아래 PC 107px · 휴대폰 98px). 그런데 앵커로 뛰면 브라우저가
  그 칸을 **화면 맨 위**에 맞춥니다. 머리띠가 그 위를 덮으니
  칸 제목이 PC 45px · 휴대폰 48px 묻혔습니다.

  동호회 쪽만의 일이 아니었습니다. 쪽 안 앵커는
  `#tide` 171 · `#points` 144 · `#spot`·`#festival`·`#eat`·
  `#course`·`#catch` 각 57 — **600곳이 넘습니다.**
  사이트 전체가 안고 있던 고장입니다.

  고침은 `assets/css/site.css` 의 `[id]{scroll-margin-top:…}`.

★ 무엇을 재나

  쪽을 그린 뒤 **실제로 앵커마다 뛰어 봅니다.**
  뛴 자리에서 그 칸의 제목이

    · 머리띠 아래보다 위에 있으면  → 묻힙니다 (막습니다)
    · 하단 내비 위보다 아래에 있으면 → 가립니다 (막습니다)

  `scroll-margin-top` 값을 읽어 견주지 않습니다. 값이 맞아도
  머리띠가 더 높아지면 소용없습니다. **뛰어 보고 어디 있나**를
  봅니다. (기억: 증거가 완료 조건)

★ 가리킬 곳이 없는 앵커도 잡습니다
  `href="#없는것"` 은 눌러도 아무 일이 없습니다
  (주인 규칙 — 약속한 것이 거기 있어야).

쓰는 법
    python engine/check_anchor.py
    python engine/check_anchor.py --strict
    python engine/check_anchor.py --all        전수 (느립니다)
"""
import io as _io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io                      # noqa: E402
from engine import machine                 # noqa: E402
from engine import mustmeasure             # noqa: E402
from engine import check_render as R       # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 자바스크립트가 쓰는 자리지킴이는 앵커가 아닙니다
_앵커 = re.compile(r'href="#([A-Za-z][\w\-]*)"')

재는스크립트 = """
<script>
(function(){
 function 네모(e){var r=e.getBoundingClientRect();
   return {위:Math.round(r.top),아래:Math.round(r.bottom)};}
 var 것={앵커:[],없는것:[]};
 var h=document.querySelector('.header');
 var hs=h?getComputedStyle(h).position:'';
 것.머리막음=(h&&(hs==='sticky'||hs==='fixed'))?네모(h).아래:0;
 var n=document.querySelector('.tabbar');
 것.내비위=(n&&getComputedStyle(n).display!=='none')?네모(n).위:0;
 것.폭=window.innerWidth;
 var 본것={};
 var 들=document.querySelectorAll('a[href^="#"]');
 for(var i=0;i<들.length;i++){
   var id=들[i].getAttribute('href').slice(1);
   if(!id||본것[id])continue;
   본것[id]=1;
   var e=document.getElementById(id);
   if(!e){것.없는것.push(id);continue;}
   window.scrollTo(0,0);
   // ★ `scrollIntoView()` 가 아니라 **해시를 바꿉니다.**
   //   손님은 단추를 눌러 해시를 바꿉니다. 그래야 `:target` 으로
   //   모습이 바뀌는 칸(확대 보기)도 **열린 뒤의 모습**을 잽니다.
   //   scrollIntoView 로만 쟀을 때는 아직 `display:none` 이라
   //   네모가 0,0 으로 나와 「머리띠에 107px 묻힘」 여섯 건을
   //   헛잡았습니다 (기억: 거짓 양성부터 걷어내기).
   location.hash='#'+id;
   // ★ **화면을 덮는 칸은 건너뜁니다** — 확대 보기처럼
   //   position:fixed 로 머리띠 위에 뜨는 것은 스크롤과 무관합니다.
   var cs=getComputedStyle(e);
   var 네 =e.getBoundingClientRect();
   if(cs.position==='fixed'||cs.display==='none'||
      (네.width===0&&네.height===0)){
     것.덮는칸=(것.덮는칸||0)+1;continue;}
   // 칸 제목을 찾습니다. 없으면 칸 자신을 봅니다.
   var p=e.querySelector('h1,h2,h3')||e;
   var r=네모(p);
   것.앵커.push({id:id,위:r.위,아래:r.아래,
     글:(p.textContent||'').trim().slice(0,22)});
 }
 // ★ 결과는 **바깥 문서**에 붙입니다 — `--dump-dom` 은 맨 바깥
 //   문서만 주고 iframe 속은 주지 않습니다. 안에 붙였다가
 //   「크롬이 결과를 안 돌려줬습니다」로 헛돌았습니다.
 var d=document.createElement('div');
 d.id='__잰결과__';d.textContent=JSON.stringify(것);
 d.style.display='none';
 try{parent.document.body.appendChild(d);}
 catch(e){document.body.appendChild(d);}
})();
</script>
"""


def 한쪽재기(쪽길, 폭, 높이=2400):
    """쪽을 그린 뒤 **앵커마다 실제로 뛰어** 잽니다."""
    s = io.read(쪽길).replace('</body>', 재는스크립트 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-anchor-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        io.write(사본, s)
        R._자산옮기기(임시)
        틀 = os.path.join(임시, '틀.html')
        io.write(틀, (R.틀쪽.replace('__쪽__', R._틀에서부를길(임시, 사본))
                      .replace('__폭__', str(폭))
                      .replace('__높이__', str(높이))))
        나옴 = subprocess.run(
            machine.크롬앞머리() + [
                '--hide-scrollbars',
                '--window-size=%d,%d' % (max(폭 + 40, 900), 높이 + 60),
                '--virtual-time-budget=2500',
                '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--dump-dom', 'file:///' + 틀.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=90)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('크롬이 결과를 안 돌려줬습니다')
        잰것 = json.loads(_h.unescape(m.group(1)))
        if 잰것.get('폭') != 폭:
            raise RuntimeError('틀 폭이 %s 로 잡혔습니다 (바란 폭 %d)'
                               % (잰것.get('폭'), 폭))
        return 잰것
    finally:
        shutil.rmtree(임시, ignore_errors=True)


def 볼쪽들(전부):
    """쪽 안 앵커를 **가진** 쪽만 봅니다. 표본은 칸마다 둘."""
    가진것 = []
    for p in sorted(io.쪽들(NEW)):
        글 = _io.open(p, encoding='utf-8', errors='replace').read()
        if _앵커.search(글):
            가진것.append(p)
    if 전부:
        return 가진것
    칸별 = {}
    for p in 가진것:
        칸 = os.path.dirname(os.path.relpath(p, NEW)) or '.'
        칸별.setdefault(칸, []).append(p)
    난것 = []
    for 칸 in sorted(칸별):
        난것 += 칸별[칸][:2]
    return 난것


def main():
    엄격 = '--strict' in sys.argv
    전부 = '--all' in sys.argv

    print()
    print('  눌러 뛰면 제목이 머리띠에 묻히는가')
    print('  (2026-10-09 — 지피티가 아래를 물었는데 위가 고장이었습니다)')
    print()

    쪽들 = 볼쪽들(전부)
    mustmeasure.있어야한다(쪽들, '쪽 안 앵커를 가진 쪽', 최소=3, 어디=NEW)

    막음, 잰번, 덮는칸 = [], 0, 0
    for 쪽길 in 쪽들:
        짧 = os.path.relpath(쪽길, NEW).replace(os.sep, '/')
        for 폭, 이름 in ((1280, 'PC'), (390, '휴대폰')):
            try:
                잰것 = 한쪽재기(쪽길, 폭)
            except Exception as e:                      # noqa: BLE001
                print('  ✗ %s %s — **못 쟀습니다**: %s' % (짧, 이름, e))
                return 4                                # 못잼
            잰번 += 1
            덮는칸 += 잰것.get('덮는칸') or 0
            for id in 잰것['없는것']:
                막음.append('%s — `#%s` 로 가는 단추가 있는데 **그런 칸이 '
                            '없습니다**' % (짧, id))
            for a in 잰것['앵커']:
                if a['위'] < 잰것['머리막음'] - 1:
                    막음.append('%s %s — `#%s` 로 뛰면 「%s」가 머리띠에 '
                                '%dpx 묻힙니다'
                                % (짧, 이름, a['id'], a['글'],
                                   잰것['머리막음'] - a['위']))
                elif 잰것['내비위'] and a['아래'] > 잰것['내비위'] + 1:
                    막음.append('%s %s — `#%s` 로 뛰면 「%s」가 아래 차림에 '
                                '가립니다' % (짧, 이름, a['id'], a['글']))

    print('  쪽 %d개 × 두 폭 = **%d번** 그려 앵커마다 뛰어 봤습니다 (%s)'
          % (len(쪽들), 잰번, '전수' if 전부 else '표본 — 전수는 --all'))
    if 덮는칸:
        print('  (화면을 덮는 칸 %d곳은 건너뛰었습니다 — 확대 보기처럼'
              ' 머리띠 위에 뜨는 것들입니다)' % 덮는칸)
    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:14]:
            print('  ✗ %s' % t)
        if len(막음) > 14:
            print('  … 그 밖 %d가지' % (len(막음) - 14))
        print()
        print('  **머리띠는 늘 떠 있습니다.** 앵커 대상에')
        print('  `scroll-margin-top` 을 머리띠 높이보다 크게 줍니다')
        print('  (assets/css/site.css 의 `[id]{scroll-margin-top:…}`).')
        return 1
    print('  · 눌러 뛴 자리에서 제목이 머리띠에 묻히지 않습니다')
    print('  · 가리킬 칸이 없는 앵커도 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
