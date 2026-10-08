# -*- coding: utf-8 -*-
"""**좌표가 없는 포인트의 카드가 비어 있지 않은가** (2026-10-08)

왜 이 검사가 있나

    89곳은 좌표가 아예 없습니다. 그 카드의 단추 자리(`.card-go`)가
    **아무 말 없이 빈 채**로 남아 있었습니다. 어떤 카드에는
    「📍 위치 확인하기」가 있고 어떤 카드에는 없는데, 왜 없는지
    쪽 어디에도 적혀 있지 않았습니다.

    규칙 6-1 — 「사람은 눈으로 봅니다. 쪽에는 보이는 것이 있어야
    합니다」. 빈 자리는 손님에게 「여기 뭔가 있어야 하는데 안 뜬다」로
    읽힙니다.

    좌표를 **짐작해 채우지 않습니다** — 틀린 자리로 손님을 보내는 것이
    비워 두는 것보다 나쁩니다. 대신 없다고 말하고, 이름으로 직접
    찾아볼 길을 줍니다.

무엇을 재나

    HTML 만 읽어서는 모릅니다 — 안내는 `point-list.js` 가 그립니다.
    그래서 크롬으로 **실제로 그려서** 셉니다.

      ① 자료에서 센 「좌표 없는 수」 == 화면의 `.card-nocoord` 수
      ② 그 안내마다 **찾아볼 길**(링크)이 있는가
      ③ 좌표가 다 있는 쪽에는 안내가 **하나도 없는가**
         (아무 카드에나 붙이는 코드를 잡습니다)
      ④ 휴대폰(375px)에서 그 링크가 **44px 이상**인가 (규칙 6-2)
      ⑤ **역방향** — 자료에 좌표가 없는데 지도로 데려가는 단추가
         붙어 있지 않은가 (바깥 검수 2026-10-08 추가 요구 —
         「데이터에는 좌표 없음 → 화면에는 지도 핀 있음,
           이 역방향 오류도 시험하십시오」)

    ③ 이 중요합니다. ①만 재면 「모든 카드에 안내를 붙이는」 코드도
    통과할 수 있습니다 — 수만 맞으면 되니까요.

쓰는 법
    python engine/check_nocoord.py
    python engine/check_nocoord.py --자세히
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
from engine import io           # noqa: E402
from engine import machine      # noqa: E402
from engine import check_render as R   # noqa: E402

자료뿌리 = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
쪽뿌리 = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 휴대폰에서 누를 자리의 최소 높이 (규칙 6-2)
누름최소 = 44

재는스크립트 = """
<script>
(function () {
  function 재자() {
    var 난것 = { 폭: innerWidth, 카드: 0, 안내: 0, 링크없는안내: 0,
                 작은링크: [], 안내밖카드: 0,
                 좌표없는데지도: 0 };
    var 카드들 = document.querySelectorAll('.card');
    난것.카드 = 카드들.length;
    for (var i = 0; i < 카드들.length; i++) {
      var c = 카드들[i];
      var 안 = c.querySelector('.card-nocoord');
      var 좌표있나 = c.getAttribute('data-lat') !== ''
                   && c.getAttribute('data-lat') !== null;
      // ★ **역방향** — 자료에 좌표가 없는데 지도로 데려가는
      //   단추가 붙어 있으면 잘못입니다 (바깥 검수 2026-10-08)
      //   「데이터에는 좌표 없음 → 화면에는 지도 핀 있음」
      if (!좌표있나 && c.querySelector('.maplink--map, .navi'))
        난것.좌표없는데지도++;
      if (안) {
        난것.안내++;
        // ★ 좌표가 **있는** 카드에 안내가 붙었으면 잘못입니다
        if (좌표있나) 난것.안내밖카드++;
        var a = 안.querySelector('a[href]');
        if (!a) 난것.링크없는안내++;
        else {
          var h = a.getBoundingClientRect().height;
          if (h > 0 && h < __누름최소__)
            난것.작은링크.push({ 글: (a.textContent || '').trim().slice(0, 20),
                                 높이: Math.round(h) });
        }
      }
    }
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    // ★ **바깥 틀에** 붙입니다 — `--dump-dom` 은 틀만 찍습니다.
    //   iframe 안에 두면 결과가 영영 안 나옵니다 (2026-10-08에 겪음)
    try { parent.document.body.appendChild(d); }
    catch (e) { document.body.appendChild(d); }
  }
  // point-list.js 는 defer 입니다 — 다 돌고 나서 셉니다
  if (document.readyState === 'complete') setTimeout(재자, 300);
  else addEventListener('load', function () { setTimeout(재자, 300); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=375, 높이=3000):
    """쪽을 그려서 셉니다. check_render 의 틀을 그대로 씁니다."""
    s = io.read(쪽길)
    s = s.replace('</body>',
                  재는스크립트.replace('__누름최소__', str(누름최소)) + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-nocoord-')
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
                '--virtual-time-budget=3500', '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=90)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('재지 못했습니다 — 크롬이 결과를 안 돌려줬습니다')
        import html as _h
        잰것 = json.loads(_h.unescape(m.group(1)))
        if 잰것.get('폭') != 폭:
            raise RuntimeError('틀 폭이 %s 로 잡혔습니다 (바란 폭 %d)'
                               % (잰것.get('폭'), 폭))
        return 잰것
    finally:
        shutil.rmtree(임시, ignore_errors=True)


def 표본고르기():
    """**자료에서 고릅니다** — 쪽 이름을 코드에 박지 않습니다
       (기억 「시험에 이름을 박지 않기」)

    ① 좌표 없는 곳이 가장 많은 권역·갈래 셋
    ② 좌표가 **하나도 안 빠진** 권역·갈래 하나 (안내가 0이어야 합니다)
    """
    셈 = {}
    for p in glob.glob(os.path.join(자료뿌리, 'raw', 'points', '*.json')):
        d = json.loads(io.read(p))
        것들 = d.get('포인트') or d.get('points') or (d if isinstance(d, list) else [])
        for x in 것들:
            키 = (x.get('권역'), x.get('갈래'))
            좌 = x.get('좌표') or {}
            la = 좌.get('위도') if 좌.get('위도') is not None else x.get('위도')
            없음, 모두 = 셈.get(키, (0, 0))
            셈[키] = (없음 + (1 if la is None else 0), 모두 + 1)

    많은것 = sorted((k for k, v in 셈.items() if v[0] > 0),
                    key=lambda k: -셈[k][0])[:3]
    꽉찬것 = [k for k, v in 셈.items() if v[0] == 0 and v[1] >= 10]
    꽉찬것 = sorted(꽉찬것)[:1]
    return 많은것 + 꽉찬것, 셈


def 쪽찾기(권역, 갈래):
    """그 권역·갈래의 포인트 쪽을 **찾습니다** — 주소를 짐작하지
       않습니다 (기억 「쪽 종류는 쪽이 말하게」)"""
    꼬리 = 'fishing' if 갈래 == '낚시' else 'gleaning'
    난것 = []
    for 뿌리, _, 파일들 in os.walk(os.path.join(쪽뿌리, 'point')):
        for f in 파일들:
            if not f.endswith('.html'):
                continue
            if 권역 in f and 꼬리 in f:
                난것.append(os.path.join(뿌리, f))
    # 「busan」이 「busaneast」를 물지 않게 가장 짧은 이름을 고릅니다
    난것.sort(key=lambda p: len(os.path.basename(p)))
    for p in 난것:
        이름 = os.path.basename(p)
        if re.search(r'(^|[_/])%s[_.]' % re.escape(권역), 이름):
            return p
    return 난것[0] if 난것 else None


def main():
    자세히 = '--자세히' in sys.argv
    print('좌표 없는 포인트의 카드가 비어 있지 않은가 (규칙 6-1)')
    표본, 셈 = 표본고르기()
    if not 표본:
        print('  ! 표본을 못 골랐습니다 — 자료를 못 읽었습니다')
        return 4

    탈 = []
    잰쪽 = 0
    for 권역, 갈래 in 표본:
        쪽 = 쪽찾기(권역, 갈래)
        if not 쪽:
            print('  ? %s %s — 쪽을 못 찾았습니다' % (권역, 갈래))
            continue
        바란것 = 셈[(권역, 갈래)][0]
        try:
            잰것 = 쪽재기(쪽)
        except Exception as e:
            print('  ? %s %s — 못 쟀습니다 (%s)' % (권역, 갈래, e))
            continue

        잰쪽 += 1
        이름 = os.path.relpath(쪽, ROOT)
        줄 = ('  %s %-34s 좌표없음 %d · 화면 안내 %d'
              % ('·' if 잰것['안내'] == 바란것 else '✗', 이름, 바란것, 잰것['안내']))
        print(줄)
        if 잰것['안내'] != 바란것:
            탈.append('%s — 좌표 없는 곳 %d 인데 안내는 %d 입니다'
                      % (이름, 바란것, 잰것['안내']))
        if 잰것['안내밖카드']:
            탈.append('%s — **좌표가 있는** 카드 %d곳에 안내가 붙었습니다'
                      % (이름, 잰것['안내밖카드']))
        if 잰것['링크없는안내']:
            탈.append('%s — 안내 %d곳에 찾아볼 길이 없습니다'
                      % (이름, 잰것['링크없는안내']))
        # ★ 역방향 (바깥 검수 2026-10-08)
        if 잰것.get('좌표없는데지도'):
            탈.append('%s — **좌표가 없는** 카드 %d곳에 지도로 가는 '
                      '단추가 붙었습니다 (누르면 아무 데도 못 갑니다)'
                      % (이름, 잰것['좌표없는데지도']))
        for a in 잰것['작은링크']:
            탈.append('%s — 휴대폰에서 누름자리가 %dpx 입니다 (%d 넘어야)'
                      % (이름, a['높이'], 누름최소))
        if 자세히:
            print('      카드 %d · 링크없음 %d · 엉뚱한자리 %d'
                  ' · 좌표없는데지도 %d'
                  % (잰것['카드'], 잰것['링크없는안내'], 잰것['안내밖카드'],
                     잰것.get('좌표없는데지도', 0)))

    print('')
    # ★ **못 잰 것을 통과로 세지 않습니다** (끝난값 계약: 4 = 못잼)
    #   처음에 크롬이 결과를 안 돌려주는데도 「빈 자리 없이 모두
    #   말하고 있습니다」로 통과했습니다. 그 통과는 거짓입니다.
    if 잰쪽 == 0:
        print('  ? 한 쪽도 못 쟀습니다 — 크롬이 없거나 결과를 못 받았습니다.')
        print('    **통과가 아닙니다.**')
        return 4
    if 탈:
        for t in 탈:
            print('  ✗ %s' % t)
        print('')
        print('  좌표가 없으면 **없다고 말합니다.** 짐작한 좌표로 채우지')
        print('  않고, 빈 자리로도 두지 않습니다 (규칙 6-1).')
        return 1
    print('  빈 자리 없이 모두 말하고 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
