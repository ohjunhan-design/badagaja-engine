# -*- coding: utf-8 -*-
"""tide.js 의 삭 시각이 천문 기준과 **몇 분 어긋나는지 잽니다.**

★ 왜 생겼나 (2026-09-27 바깥 검수 3차)

    보고서에 「지금 항 다섯 개로 몇 분 수준입니다」라고 적었더니
    검수가 이렇게 답했습니다.

      「이 문장은 현재 자료만으로는 PASS 를 줄 수 없습니다.
        간략 달 계산식은 생각보다 작은 항들이 결과에 영향을 줍니다.
        공식의 모양만 보고 내리면 안 되고 **실제 오차를 측정해야**
        합니다」

    옳은 지적입니다. 「몇 분일 것이다」는 잰 값이 아니라 짐작입니다.

무엇을 재나
    2026~2035년 삭 124회쯤을 모두 견줍니다.

        천문 기준   engine/meeus.py   (Meeus 49장 · 보정 39항)
        쓰는 것     assets/js/tide.js (황경 차이 · 25항) — 브라우저에서 그대로

    내는 것
        가장 큰 어긋남 · 95% 어긋남 · 평균 어긋남
        자정 ±2시간에 든 삭만 따로 (여기서 하루가 갈립니다)
        ★ 음력 **날짜**가 갈린 횟수 — 이것이 진짜 통과 조건입니다

★ 시각보다 날짜가 중요합니다 (검수가 짚은 것)
    우리는 천문대가 아닙니다. 손님에게 필요한 것은
    「오늘이 음력 며칠인가 → 물때가 무엇인가」입니다.
    삭이 17분 어긋나도 날짜가 같으면 손님은 아무 탈이 없습니다.
    그러나 삭이 자정 언저리면 1분 차이로 **하루가 갈립니다.**
    2026-10-10 사건이 바로 그것이었습니다.

★ 메아리가 아닙니다
    기준(meeus.py)은 tide.js 를 한 줄도 안 봅니다. 셈하는 길이
    다릅니다. 브라우저에는 **쓰는 파일 그대로**를 올립니다.

쓰는 법
    python engine/check_newmoon.py                 2026~2035
    python engine/check_newmoon.py 2026 2040       그 해들
    python engine/check_newmoon.py --strict        어긋나면 1 을 냅니다
"""
import os
import re
import sys
import json
import shutil
import datetime
import tempfile
import subprocess
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io        # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만
from engine import meeus     # noqa: E402

ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

막음, 알림 = [], []

# ── 얼마나 어긋나도 봐줄 것인가 ─────────────────────────────
#
# ★ 짐작이 아니라 **잰 값**에 맞춰 조였습니다 (2026-09-27)
#
#   2026~2035년 삭 124회를 실제로 재니 이랬습니다.
#
#       흔들림 5항일 때   가장 큼 35.9분 · 95% 28.9분 · 평균 12.7분
#                         **음력 날짜가 30일 갈림** (2029년 12월 한 달)
#       흔들림 25항일 때  가장 큼  3.8분 · 95%  2.7분 · 평균  1.6분
#                         음력 날짜 갈림 0일
#
#   그래서 10분으로 둡니다. 지금 값(3.8분)의 두 배 남짓이라
#   자잘한 흔들림은 봐주면서, **나빠지면 바로 걸립니다.**
#   느슨하게 두면 나빠져도 모릅니다.
봐줄시각 = 10        # 분 — 가장 큰 어긋남
봐줄날짜 = 0         # 건 — 음력 날짜가 갈리는 것은 하나도 안 됩니다


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
def 우리삭과음력(k들, 날들):
    """tide.js 가 내어 주는 삭 시각과 음력날.

    **쓰는 파일 그대로**를 브라우저에 올립니다. 검사는 받아 적기만
    합니다. 여기서 식을 베끼면 메아리가 됩니다.
    """
    t = tempfile.mkdtemp(prefix='newmoon-')
    try:
        io.write(os.path.join(t, 'tide.js'),
                 io.read(os.path.join(ASSETS, 'js', 'tide.js')))
        쪽 = ("""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<p id="tideStatus"></p><div id="tideStrip" data-days="1"></div>
<script src="tide.js"></script>
<script>
(function(){
  var 셈 = window.바다가자물때;
  var 답 = {삭: [], 음력: [], 열렸나: false};
  if (셈 && typeof 셈.삭시각 === 'function') {
    답.열렸나 = true;
    var ks = %s;
    for (var i = 0; i < ks.length; i++) {
      // tide.js 가 내는 삭 시각 (밀리초, UTC 기준의 순간)
      답.삭.push(셈.삭시각(ks[i]));
    }
  }
  if (셈) {
    var 날들 = %s;
    for (var j = 0; j < 날들.length; j++) {
      var p = 날들[j].split('-');
      답.음력.push(셈.음력날(new Date(+p[0], +p[1] - 1, +p[2])));
    }
  }
  var e = document.createElement('div');
  e.id = 'R'; e.style.display = 'none';
  e.textContent = JSON.stringify(답);
  document.body.appendChild(e);
})();
</script></body></html>""" % (json.dumps(k들), json.dumps(날들)))
        p2 = os.path.join(t, 'a.html')
        io.write(p2, 쪽)
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--virtual-time-budget=20000', '--dump-dom',
             'file:///' + p2.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=300)
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout, re.S)
        if not m:
            # ★ **왜 못 받았는지 적습니다** (2026-09-28 바깥 검수 11차)
            #
            #   전에는 「셈한 결과를 못 받았습니다」만 말했습니다.
            #   크롬이 안 떴는지, 떴는데 글을 못 그렸는지,
            #   오류를 뱉었는지 하나도 알 수 없었습니다.
            #   클라우드에서만 나는 일이라 더 답답했습니다.
            까닭 = []
            까닭.append('끝난값 %s' % r.returncode)
            까닭.append('내놓은 글 %d자' % len(r.stdout or ''))
            탈 = (r.stderr or '').strip()
            if 탈:
                줄들 = [x.strip() for x in 탈.split('\n') if x.strip()]
                # ★ FATAL 줄이 길어 잘렸습니다 — 넉넉히 적습니다
                까닭.append('크롬이 한 말: '
                          + ' / '.join(줄들[-3:])[:400])
            if r.stdout and 'id="R"' not in r.stdout:
                까닭.append('쪽은 그렸는데 R 칸이 없습니다'
                            ' (스크립트가 안 돌았습니다)')
            raise RuntimeError('셈한 결과를 못 받았습니다 — '
                               + ' · '.join(까닭))
        답 = json.loads(_h.unescape(m.group(1)))
        if not 답.get('열렸나'):
            raise RuntimeError('tide.js 가 삭시각을 안 내어 줍니다 '
                               '(window.바다가자물때.삭시각 을 보세요)')
        return 답
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 백분위(값들, 몇):
    if not 값들:
        return 0.0
    ㅅ = sorted(값들)
    i = int(round((몇 / 100.0) * (len(ㅅ) - 1)))
    return ㅅ[i]


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    첫해 = int(args[0]) if args else 2026
    끝해 = int(args[1]) if len(args) > 1 else (첫해 + 9 if not args else 첫해)
    if not args:
        첫해, 끝해 = 2026, 2035

    print('tide.js 의 삭 시각이 천문 기준과 몇 분 어긋나는가')
    print('  기준  engine/meeus.py (Meeus 49장 · 보정 39항 · 한국시)')
    print('  쓰는 것  assets/js/tide.js (황경 차이 · 25항) — 브라우저에서 그대로')
    print('  기간  %d-01-01 ~ %d-12-31' % (첫해, 끝해))
    print('')

    기준 = meeus.삭목록(첫해, 끝해)
    if not 기준:
        막음.append('기준 삭을 못 냈습니다')
        print('  ✗ 기준 삭을 못 냈습니다')
        return 1

    # 견줄 날 — 기간 안 모든 날
    첫날 = datetime.date(첫해, 1, 1)
    끝날 = datetime.date(끝해, 12, 31)
    날들 = []
    d = 첫날
    while d <= 끝날:
        날들.append(d.isoformat())
        d += datetime.timedelta(days=1)

    try:
        답 = 우리삭과음력([k for k, _ in 기준], 날들)
    except (RuntimeError, OSError, subprocess.SubprocessError,
            ValueError) as e:
        # ★ 못 쟀으면 **통과가 아닙니다** — 「안 잰 것」으로 냅니다
        print('  ? 못 쟀습니다: %s' % e)
        print('    (크롬이 있어야 잽니다 — 주인 규칙 25)')
        print('')
        print('NOT_TESTED')
        return 2

    # ── 1. 삭 시각 어긋남
    print('[1] 삭 시각이 몇 분 어긋나는가')
    어긋남, 자정어긋남, 큰것 = [], [], []
    for (k, 기준때), 우리ms in zip(기준, 답['삭']):
        우리때 = (datetime.datetime(1970, 1, 1)
                  + datetime.timedelta(milliseconds=우리ms)
                  + datetime.timedelta(hours=9))     # 한국시로
        분 = abs((우리때 - 기준때).total_seconds()) / 60.0
        어긋남.append(분)
        if 기준때.hour < 2 or 기준때.hour >= 22:
            자정어긋남.append(분)
        큰것.append((분, k, 기준때, 우리때))

    print('      견준 삭        %d회' % len(어긋남))
    print('      가장 큰 어긋남 %6.1f 분' % max(어긋남))
    print('      95%% 어긋남     %6.1f 분' % 백분위(어긋남, 95))
    print('      평균 어긋남    %6.1f 분' % (sum(어긋남) / len(어긋남)))
    if 자정어긋남:
        print('')
        print('      자정 ±2시간에 든 삭 %d회 — 여기서 하루가 갈립니다'
              % len(자정어긋남))
        print('        가장 큰 어긋남 %6.1f 분' % max(자정어긋남))
    print('')
    큰것.sort(reverse=True)
    print('      가장 많이 어긋난 다섯')
    for 분, k, 기준때, 우리때 in 큰것[:5]:
        print('        %s  기준 %s · 우리 %s  (%.1f 분)'
              % (기준때.strftime('%Y-%m-%d'),
                 기준때.strftime('%H:%M'), 우리때.strftime('%H:%M'), 분))
    if max(어긋남) > 봐줄시각:
        막음.append('삭 시각이 %.1f 분 어긋납니다 (%d 분까지 봐줍니다)'
                    % (max(어긋남), 봐줄시각))
    print('')

    # ── 2. ★ 음력 날짜가 갈린 적이 있는가 — 진짜 통과 조건
    print('[2] 음력 **날짜**가 갈린 적이 있는가  ← 진짜로 중요한 것')
    갈린것 = []
    for 날글, 우리 in zip(날들, 답['음력']):
        y, m, dd = (int(x) for x in 날글.split('-'))
        기준음력 = meeus.음력날(datetime.date(y, m, dd))
        if 기준음력 is not None and 기준음력 != 우리:
            갈린것.append((날글, 기준음력, 우리))
    print('      견준 날  %d일' % len(날들))
    print('      갈린 날  %d일' % len(갈린것))
    if 갈린것:
        for 날글, 기준음력, 우리 in 갈린것[:10]:
            print('        %s  기준 음력 %2d일 · 우리 %2d일'
                  % (날글, 기준음력, 우리))
        if len(갈린것) > 10:
            print('        … 그 밖 %d일' % (len(갈린것) - 10))
    if len(갈린것) > 봐줄날짜:
        막음.append('음력 날짜가 %d일 갈립니다 (하나도 안 됩니다)'
                    % len(갈린것))
    print('')

    # ── 3. 자정 언저리 위험군을 따로 못 박아 둡니다
    print('[3] 자정 언저리 삭 — 앞으로도 여기를 봅니다')
    위험 = [(k, t) for k, t in 기준 if t.hour < 2 or t.hour >= 22]
    print('      %d회' % len(위험))
    for k, t in 위험[:8]:
        print('        %s  (k=%d)' % (t.strftime('%Y-%m-%d %H:%M'), k))
    if len(위험) > 8:
        print('        … 그 밖 %d회' % (len(위험) - 8))
    print('      2026-10-11 00:49 이 바로 이 갈래였습니다.')
    print('')

    # ── 4. ★ 바깥 천문 자료에 못 박기 — 두 셈이 나란히 틀릴 때를 위해
    print('[4] 바깥 천문 자료와 맞는가  (두 셈이 나란히 틀릴 때를 위해)')
    기준표 = io.read_json(os.path.join(DATA, 'raw', '삭-기준.json'),
                          default=None)
    if not 기준표:
        # ★ 없으면 **통과가 아닙니다** — 「안 잰 것」입니다
        막음.append('data/raw/삭-기준.json 이 없습니다 — 못 박을 데가 없습니다')
        print('      ✗ data/raw/삭-기준.json 이 없습니다')
    else:
        봐줄 = 기준표.get('_봐줄어긋남_분', 10)
        못박은것 = [x for x in (기준표.get('삭') or []) if x.get('한국시')]
        if not 못박은것:
            막음.append('삭-기준.json 에 확인된 값이 하나도 없습니다')
            print('      ✗ 확인된 값이 하나도 없습니다')
        print('      못 박은 삭 %d개 (봐줄 어긋남 %d분)'
              % (len(못박은것), 봐줄))
        어김 = []
        for x in 못박은것:
            y, m, rest = x['한국시'].split('-', 2)
            dd, 시분 = rest.split(' ')
            시, 분 = 시분.split(':')
            바깥 = datetime.datetime(int(y), int(m), int(dd),
                                     int(시), int(분))
            # 그 삭에 가장 가까운 k 를 찾아 견줍니다
            가까운 = min(기준, key=lambda kt: abs((kt[1] - 바깥)
                                                  .total_seconds()))
            k, 우리기준 = 가까운
            차기준 = abs((우리기준 - 바깥).total_seconds()) / 60.0
            i위 = [kk for kk, _ in 기준].index(k)
            우리때 = (datetime.datetime(1970, 1, 1)
                      + datetime.timedelta(milliseconds=답['삭'][i위])
                      + datetime.timedelta(hours=9))
            차우리 = abs((우리때 - 바깥).total_seconds()) / 60.0
            날짜만 = x.get('날짜만본다')
            탈 = []
            if 날짜만:
                if 우리기준.date() != 바깥.date():
                    탈.append('재는 셈이 날짜가 다릅니다')
                if 우리때.date() != 바깥.date():
                    탈.append('쓰는 것이 날짜가 다릅니다')
            else:
                if 차기준 > 봐줄:
                    탈.append('재는 셈이 %.1f분' % 차기준)
                if 차우리 > 봐줄:
                    탈.append('쓰는 것이 %.1f분' % 차우리)
            표시 = '✗' if 탈 else '·'
            print('        %s %s  바깥 %s · 재는 셈 %s(%.1f분) '
                  '· 쓰는 것 %s(%.1f분)'
                  % (표시, 바깥.strftime('%Y-%m-%d'),
                     바깥.strftime('%H:%M'),
                     우리기준.strftime('%H:%M'), 차기준,
                     우리때.strftime('%H:%M'), 차우리))
            if x.get('왜중요한가'):
                print('            %s' % x['왜중요한가'])
            if 탈:
                어김.append('%s — %s' % (x['한국시'], ' · '.join(탈)))
        if 어김:
            for e in 어김:
                막음.append('바깥 자료와 어긋남: %s' % e)
    print('')

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0

    print('삭 시각은 가장 크게 %.1f 분 어긋나고, '
          '음력 날짜는 %d일 가운데 한 번도 갈리지 않습니다.'
          % (max(어긋남), len(날들)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
