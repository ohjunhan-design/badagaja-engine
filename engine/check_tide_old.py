# -*- coding: utf-8 -*-
"""**옛 물때 계산과 새 물때 계산이 같은 답을 내는가** — 전수로 봅니다.

★ 왜 필요한가 (2026-09-28 바깥 검수 6차 지시)

    새 틀이 안 만드는 쪽이 셋 있습니다. 옛 쪽을 그대로 남깁니다.

        guide/index.html     js/tide-graph.js
        tide/index.html      js/tide-14.js · tide-graph.js · tide-map.js
        travel/index.html    js/tide-graph.js

    이 셋은 **옛 계산**(`js/app.js`)을 쓰고,
    새 쪽 416개는 **새 계산**(`assets/js/tide.js`)을 씁니다.

    ★ 견주는 것은 **음력 날짜**입니다 — 물때 번호가 아닙니다 (2026-09-28)

      처음에는 물때 번호를 견주다 「2물 틀렸다」고 놀랐습니다.
      알고 보니 **축이 다른 것**이었습니다.
      해양조사원은 셋을 함께 보여 줍니다.

          이름  목사리        ← 새 쪽이 씁니다
          매식  여덟매        (7물때식)
          물식  10물          ← 옛 쪽이 씁니다

      둘 다 맞습니다. 그대로 고쳤으면 **맞는 것을 망가뜨릴 뻔**했습니다.

      진짜로 같아야 하는 것은 **그 아래 깔린 음력 날짜**입니다.
      음력이 하루 틀리면 이름이든 물식이든 다 하루 틀립니다.

    바깥 검수가 이렇게 말했습니다.

        물때 계산은 사이트 핵심 기능 중 하나이므로
        모든 입력 조건을 실제 데이터로 전수 비교하는 것이 좋습니다.

    맞는 말입니다. **같은 사이트 안에서 같은 날의 물때가 두 가지로
    나오면** 손님이 어느 쪽을 믿어야 할지 모릅니다.

★ 어떻게 재나
    옛 코드와 새 코드를 **한 크롬 화면에 같이 올려** 놓고,
    날짜를 하루씩 밀며 둘의 답을 견줍니다. 베끼지 않습니다 —
    **진짜 파일을 그대로 읽어** 돌립니다.

★ 다르면 그게 다 탈은 아닙니다
    옛 것이 7물때식(1물~15물), 새 것이 이름(한물·두메…)을 내므로
    **번호**로 견줍니다. 번호가 다르면 진짜 탈입니다.

쓰는 법
    python engine/check_tide_old.py            두 해치 (730일)
    python engine/check_tide_old.py --날 3650  열 해치
    python engine/check_tide_old.py --strict
"""
import os
import re
import sys
import json
import shutil
import tempfile
import datetime
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io        # noqa: E402
from engine import machine   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# 검사 등급 (계약-21)
막음 = []
알림 = []

# 옛 계산을 그대로 쓰는 쪽 — keep.json 이 남기기로 한 것들
옛계산쪽 = ('guide/index.html', 'tide/index.html', 'travel/index.html')


틀 = """<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<!-- ★ 새 물때 코드는 이 칸이 없으면 **바로 나갑니다** (tide.js 21줄).
     칸이 없으면 window.바다가자물때 도 안 붙어 「새 계산 없음」이 납니다.
     그래서 진짜 쪽에 있는 것과 같은 칸을 놓아 줍니다. -->
<div id="tideStrip" data-region="taean" data-days="7"></div>
<script>%s</script>
<script>%s</script>
<script>
(function () {
  var 나옴 = {잰날: 0, 다른것: [], 못잰것: [], 차이들: {}};
  var 옛 = window.BADAGAJA_TIDE;
  var 새 = window.바다가자물때;
  if (!옛 || !새) {
    나옴.못잰것.push((옛 ? '' : '옛 계산(BADAGAJA_TIDE) 없음 ')
                     + (새 ? '' : '새 계산(바다가자물때) 없음'));
  } else {
    var 시작 = new Date(%d, %d - 1, %d);
    for (var i = 0; i < %d; i++) {
      var d = new Date(시작.getTime());
      d.setDate(시작.getDate() + i);
      var a = null, b = null;
      try { a = 옛.lunarDay(d); } catch (e) { a = '탈:' + e.message; }
      try { b = 새.음력날(d); } catch (e) { b = '탈:' + e.message; }
      나옴.잰날++;
      if (a !== b) {
        var 차 = ((a - b) %% 30 + 30) %% 30;
        나옴.차이들[차] = (나옴.차이들[차] || 0) + 1;
        if (나옴.다른것.length < 2000) {
          나옴.다른것.push({날: d.getFullYear() + '-'
                            + (d.getMonth() + 1) + '-' + d.getDate(),
                            옛: a, 새: b});
        }
      }
    }
    나옴.다른수 = 나옴.잰날 - (나옴.잰날 - 나옴.다른것.length);
  }
  var e = document.createElement('div');
  e.id = '__잰것__'; e.style.display = 'none';
  e.textContent = JSON.stringify(나옴);
  document.body.appendChild(e);
})();
</script></body></html>"""


def 옛코드():
    p = os.path.join(OLD, 'js', 'app.js')
    if not os.path.isfile(p):
        return None
    return io.read(p, default='')


def 새코드():
    p = os.path.join(ASSETS, 'js', 'tide.js')
    if not os.path.isfile(p):
        return None
    return io.read(p, default='')


def 재기(시작, 날수):
    옛, 새 = 옛코드(), 새코드()
    if 옛 is None:
        return None, '옛 계산을 못 찾았습니다: %s' % os.path.join(OLD, 'js', 'app.js')
    if 새 is None:
        return None, '새 계산을 못 찾았습니다: %s' % os.path.join(ASSETS, 'js', 'tide.js')

    s = 틀 % (옛, 새, 시작.year, 시작.month, 시작.day, 날수)
    t = tempfile.mkdtemp(prefix='tide-old-')
    try:
        p = os.path.join(t, 'z.html')
        io.write(p, s)
        try:
            크롬 = machine.크롬찾기()
        except RuntimeError as e:
            return None, str(e)
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--user-data-dir=' + os.path.join(t, 'prof'),
             '--virtual-time-budget=30000',
             # 바깥으로 안 나갑니다 — 인터넷에 흔들리면 시험이 아닙니다
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--dump-dom', 'file:///' + p.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=300)
        m = re.search(r'id="__잰것__"[^>]*>(.*?)</div>', r.stdout or '', re.S)
        if not m:
            return None, '크롬이 결과를 안 돌려줬습니다'
        import html as _h
        return json.loads(_h.unescape(m.group(1))), ''
    finally:
        shutil.rmtree(t, ignore_errors=True)


def main():
    날수 = 730
    if '--날' in sys.argv:
        try:
            날수 = int(sys.argv[sys.argv.index('--날') + 1])
        except (IndexError, ValueError):
            pass

    print('옛 물때 계산과 새 물때 계산이 같은가 (바깥 검수 6차)')
    print('  옛 계산  %s' % os.path.join(OLD, 'js', 'app.js'))
    print('  새 계산  %s' % os.path.join(ASSETS, 'js', 'tide.js'))
    print('')

    # ── 1. 어느 쪽이 옛 계산을 쓰는가
    print('[1] 옛 계산을 그대로 쓰는 쪽')
    있는쪽 = []
    for k in 옛계산쪽:
        p = os.path.join(OLD, k.replace('/', os.sep))
        if os.path.isfile(p):
            있는쪽.append(k)
            print('      %s' % k)
    if not 있는쪽:
        print('  · 옛 계산을 쓰는 쪽이 없습니다 — 잴 것이 없습니다')
        return 0
    print('      %d쪽이 옛 계산을 씁니다' % len(있는쪽))
    print('')

    # ── 2. 날마다 견주기
    시작 = datetime.date.today()
    print('[2] %s 부터 %d일을 하루씩 견줍니다' % (시작, 날수))
    잰것, 탈 = 재기(시작, 날수)
    if 잰것 is None:
        print('  ✗ 못 쟀습니다 — %s' % 탈)
        print('      (재지 못한 것은 「같다」가 아닙니다)')
        return 2                      # NOT_TESTED
    if 잰것.get('못잰것'):
        for x in 잰것['못잰것']:
            print('  ✗ %s' % x)
        print('      (재지 못한 것은 「같다」가 아닙니다)')
        return 2

    잰날 = 잰것.get('잰날', 0)
    다른것 = 잰것.get('다른것') or []
    print('      잰 날 %d일' % 잰날)
    if 잰날 < 날수:
        알림.append('바란 %d일 중 %d일만 쟀습니다' % (날수, 잰날))
    if 다른것:
        막음.append('옛 계산과 새 계산이 다른 날 %d일' % len(다른것))
        print('  ✗ 답이 다른 날이 있습니다 %d일 (앞 40일까지만 모읍니다)'
              % len(다른것))
        print('')
        print('      날짜            옛 계산   새 계산')
        for x in 다른것[:12]:
            print('      %-14s %-8s %s' % (x['날'], x['옛'], x['새']))
        if len(다른것) > 12:
            print('      … 그 밖 %d일' % (len(다른것) - 12))
        print('')
        print('      **같은 사이트에서 같은 날의 물때가 둘로 나옵니다.**')
        print('      손님이 어느 쪽을 믿어야 할지 모릅니다.')
    else:
        print('  · %d일이 하나도 안 다릅니다 — 옛 쪽과 새 쪽이 같은 답을 냅니다'
              % 잰날)
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1
    print('옛 계산과 새 계산이 같은 답을 냅니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
