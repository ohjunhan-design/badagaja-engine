# -*- coding: utf-8 -*-
"""물때가 국립해양조사원 자료와 맞는지 봅니다.

기준은 **공공데이터(해양수산부 국립해양조사원)** 입니다  (주인 지시 2026-09-26)
    스마트 조석예보 https://www.khoa.go.kr/swtc/main.do?obsPostId=<관측소>
    여기서 받은 값과 우리 계산을 그 자리에서 견줍니다.
    남의 사이트 값을 베껴 와 박아 두지 않습니다.

해양조사원은 물때를 세 가지로 함께 보여 줍니다
    이름  턱사리 · 한사리 · 목사리 …     ← 우리가 크게 보여 주는 것
    매식  일곱매 · 여덟매 …              ← 함께 보여 주는 것 (7물때식)
    물식  여덟물 · 아홉물 …              (8물때식)

왜 이 검사가 필요한가
    물때는 이 사이트의 뼈대입니다. 해루질·낚시 갈 날을 이 숫자로 고릅니다.
    그런데 옛 사이트는 **세 값이 제각각**이었습니다.

        국립해양조사원   2026-09-26(음력 8.16) → 턱사리 (일곱매)
        옛 브라우저                            → 목사리   ← 두 칸 어긋남
        옛 서버                                → 또 다른 값

    이름표는 해양조사원과 같았는데 **식이 어긋나** 있었고,
    손님 화면에는 서버 값이 보였습니다. 아무 검사도 없어 몰랐습니다.

막대 길이는 물때 번호가 아니라 **실제 조차**로 그립니다
    달이 사리를 만들어도 바다는 2~3일 늦게 따라옵니다(조석 지연).
    옛 사이트는 번호로 막대를 그려 「물 많이 빠짐」이 엉뚱한 날에 붙었습니다.

쓰는 법
    python engine/check_tide.py
    python engine/check_tide.py --strict     안 맞으면 1 로 끝냅니다
"""
import os
import re
import sys
import json
import tempfile
import shutil
import subprocess
import urllib.request
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만
from engine import tide_reference as 독립   # noqa: E402

ASSETS = os.path.join(ROOT, 'assets')
# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

# 견줄 관측소 — 물때는 음력을 따르므로 전국이 같아야 합니다.
# 서로 먼 곳을 골라 정말 같은지도 함께 봅니다.
관측소들 = [('DT_0050', '태안'), ('DT_0004', '제주'), ('DT_0016', '남해')]

# 7물때식 통설 — 어느 책에나 나오는 것이라 인터넷이 없을 때 이것만 봅니다
통설 = [('한사리', '음력 17일 무렵이 한사리'),
        ('한조금', '음력 9일·24일 무렵이 한조금')]


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
def 해양조사원물때(관측소='DT_0050'):
    """국립해양조사원 스마트 조석예보에서 음력·물때를 그대로 읽습니다.

    자바스크립트로 채워지는 쪽이라 크롬으로 열어야 보입니다.
    """
    r = subprocess.run(
        machine.크롬앞머리() + [
         '--virtual-time-budget=15000', '--dump-dom',
         'https://www.khoa.go.kr/swtc/main.do?obsPostId=%s' % 관측소],
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    글 = re.sub(r'<[^>]+>', '|', r.stdout)
    글 = re.sub(r'\|+', '|', 글)
    나옴 = []
    본것 = set()
    for m in re.finditer(
            r'\(음\)\s*\|?\s*(\d{2})\.(\d{2})\|[\d:]+\|[\d:]+\|'
            r'([가-힣]+)\|([가-힣]+)\|([가-힣]+)\|', 글):
        음력달, 음력날, 이름, 매, 물 = m.groups()
        키 = (음력달, 음력날)
        if 키 in 본것:
            continue
        본것.add(키)
        나옴.append({'음력달': int(음력달), '음력날': int(음력날),
                     '이름': 이름, '매': 매, '물': 물})
    return 나옴


def 우리물때(날짜들):
    """tide.js 가 그 **날짜**를 무엇이라 하는지.

    검사가 제 식을 베껴 쓰면 소용이 없습니다. **쓰는 파일 그대로**
    브라우저에 올려, 그 파일이 내어 준 셈을 씁니다.

    ★ 날짜를 넣습니다 — 음력날이 아닙니다 (2026-09-26 고침)

        처음에는 음력날을 넣고, 음력날 → 물때번호 셈을 **검사 안에**
        베껴 적었습니다.

            var n = ((날들[i] + 5) % 15) || 15;      ← 베낀 식

        베낀 식이 있으면 tide.js 를 아무렇게나 고쳐도 검사는 모릅니다.
        tests/test_checkers.py 가 식을 한 칸 밀어 보고 잡아냈습니다.

        지금은 **날짜**를 넣어, 음력 셈부터 물때 이름까지 전부
        tide.js 가 하게 합니다. 검사는 받아 적기만 합니다.
    """
    t = tempfile.mkdtemp(prefix='tide-check-')
    try:
        io.write(os.path.join(t, 'tide.js'),
                 io.read(os.path.join(ASSETS, 'js', 'tide.js')))
        쪽 = ("""<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<p id="tideStatus"></p><div id="tideStrip" data-days="1"></div>
<script src="tide.js"></script>
<script>
(function(){
  var 셈 = window.바다가자물때;
  var out = [];
  if (셈) {
    var 날들 = %s;
    for (var i = 0; i < 날들.length; i++) {
      var p = 날들[i].split('-');
      var d = new Date(+p[0], +p[1] - 1, +p[2]);
      // 음력 셈도 물때 번호도 tide.js 가 합니다. 검사는 안 셉니다.
      var n = 셈.물때번호(d);
      out.push({날짜: 날들[i], 음력날: 셈.음력날(d), 번호: n,
                이름: 셈.이름(n), 매: 셈.매(n)});
    }
  }
  var e = document.createElement('div');
  e.id = 'R'; e.style.display = 'none';
  e.textContent = JSON.stringify(out);
  document.body.appendChild(e);
})();
</script></body></html>"""
              % json.dumps([str(x) for x in 날짜들]))
        p2 = os.path.join(t, 'a.html')
        io.write(p2, 쪽)
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--virtual-time-budget=3000', '--dump-dom',
             'file:///' + p2.replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=90)
        m = re.search(r'id="R"[^>]*>(.*?)</div>', r.stdout, re.S)
        if not m:
            raise RuntimeError('셈한 결과를 못 받았습니다')
        나옴 = json.loads(_h.unescape(m.group(1)))
        if not 나옴:
            raise RuntimeError('tide.js 가 셈을 안 내주었습니다 '
                               '(window.바다가자물때 가 있는지 보세요)')
        return 나옴
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 오늘음력():
    """tide.js 가 오늘을 음력 며칠로 보는지"""
    t = tempfile.mkdtemp(prefix='tide-check-')
    try:
        io.write(os.path.join(t, 'tide.js'),
                 io.read(os.path.join(ASSETS, 'js', 'tide.js')))
        io.write(os.path.join(t, 'a.html'),
                 '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
                 '<body><p id="tideStatus"></p>'
                 '<div id="tideStrip" data-days="1"></div>'
                 '<script src="tide.js"></script><script>'
                 '(function(){var 셈=window.바다가자물때;'
                 'var e=document.createElement("div");e.id="R";'
                 'e.style.display="none";'
                 'e.textContent=JSON.stringify(셈?셈.음력날(new Date()):0);'
                 'document.body.appendChild(e);})();</script></body></html>')
        r = subprocess.run(
            machine.크롬앞머리() + [
             '--host-resolver-rules=MAP * 127.0.0.1:1',
             '--virtual-time-budget=3000', '--dump-dom',
             'file:///' + os.path.join(t, 'a.html').replace(os.sep, '/')],
            capture_output=True, text=True, encoding='utf-8', timeout=90)
        m = re.search(r'id="R"[^>]*>(\d+)</div>', r.stdout, re.S)
        return int(m.group(1)) if m else 0
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 조위받기(권역='taean'):
    주소 = 'https://badagaja.com/api/tide-cache.php?region=%s' % 권역
    with urllib.request.urlopen(주소, timeout=30) as f:
        d = json.load(f)
    나옴 = []
    for x in d.get('days', []):
        높이 = [e['level'] for e in (x.get('events') or [])]
        if len(높이) >= 2:
            나옴.append({'키': x['date'], '조차': max(높이) - min(높이)})
    return d.get('point'), 나옴


# 검사 등급 (계약-21)
#   막음 — 물때가 해양조사원과 다름. 잘못된 날을 알려 주게 됩니다
#   알림 — 바깥에서 못 받아옴. 막지 않습니다 (계약-23)
막음, 알림 = [], []


def 알리기(글):
    알림.append(글)
    print('  ~ %s' % 글)


def 음력날이든날(음력날, 기준=None):
    """그 음력날이 든 **달력 날짜**를 찾습니다.

    해양조사원은 음력날로 물때를 알려 줍니다. 그런데 tide.js 는
    달력 날짜를 받습니다. 그래서 오늘 앞뒤를 훑어 그 음력날이 든
    날을 찾습니다. 찾는 일은 **독립 셈**이 합니다 — tide.js 에게
    「네가 셈한 음력날로 네 물때를 말해 보라」고 하면 또 메아리입니다.
    """
    import datetime as _d
    기준 = 기준 or _d.date.today()
    for i in range(-5, 35):
        날 = 기준 + _d.timedelta(days=i)
        if 독립.음력날(날) == 음력날:
            return 날
    return None


def main():
    문제 = 막음
    print('물때가 국립해양조사원 자료와 맞는지')
    print('  기준: 해양수산부 국립해양조사원 스마트 조석예보 (공공데이터)')
    print('')

    # ── 0. 독립 셈과 화면 값이 같은가  ★ 가장 먼저 봅니다
    print('[0] 독립 셈과 화면 값이 같은가')
    print('      tide_reference(파이썬·삭 표) ↔ tide.js(자바스크립트·천문 계산)')
    import datetime as _dt
    볼날 = [(_dt.date.today() + _dt.timedelta(days=i)) for i in range(14)]
    화면 = dict((x['날짜'], x) for x in 우리물때(볼날))
    어긋 = []
    for 날 in 볼날:
        기준 = 독립.물때(날)
        것 = 화면.get(str(날))
        if not 것:
            어긋.append('%s — 화면 값을 못 받음' % 날)
            continue
        if 것['음력날'] != 기준['음력날']:
            어긋.append('%s — 음력이 다릅니다: 독립 %d일 ↔ 화면 %d일'
                        % (날, 기준['음력날'], 것['음력날']))
        if 것['이름'] != 기준['이름'] or 것['매'] != 기준['매']:
            어긋.append('%s 음력%d일 — 독립 %s(%s) ↔ 화면 %s(%s)'
                        % (날, 기준['음력날'], 기준['이름'], 기준['매'],
                           것['이름'], 것['매']))
    print('      견준 날 %d개' % len(볼날))
    if 어긋:
        막음.append('독립 셈과 화면 값이 다름 %d건' % len(어긋))
        print('  ✗ 독립 셈과 화면 값이 다릅니다 %d건' % len(어긋))
        for x in 어긋[:5]:
            print('      %s' % x)
        print('    어느 한쪽이 틀렸습니다. 사람이 봐야 합니다.')
    else:
        print('  · 열나흘이 하나도 안 틀립니다 — 서로 다른 방식으로 셈했는데도')
    print('')

    # ── 1. 해양조사원에서 받아 그 자리에서 대조
    print('[1] 해양조사원 물때와 맞는가')
    받은것 = None
    관측소이름 = None
    전국같나 = True
    앞선것 = None
    for 코드, 이름 in 관측소들:
        try:
            것 = 해양조사원물때(코드)
        except Exception as e:
            알리기('%s(%s) 에서 못 받았습니다 (%s)' % (이름, 코드, str(e)[:40]))
            continue
        if not 것:
            print('      %s(%s) — 물때를 못 읽었습니다' % (이름, 코드))
            continue
        print('      %s(%s) 날 %d개' % (이름, 코드, len(것)))
        if 받은것 is None:
            받은것, 관측소이름 = 것, 이름
        if 앞선것 is not None:
            맞대기 = [(a['음력날'], a['이름']) for a in 것]
            앞것 = [(a['음력날'], a['이름']) for a in 앞선것]
            if 맞대기 != 앞것:
                전국같나 = False
        앞선것 = 것

    if not 받은것:
        알리기('해양조사원에서 받지 못했습니다 — 막지는 않습니다 (계약-23)')
        print('')
    else:
        if not 전국같나:
            문제.append('관측소마다 물때가 다릅니다 — 물때는 음력을 따르므로 '
                        '전국이 같아야 합니다')
        else:
            print('      · 관측소가 달라도 물때는 같습니다 (음력을 따릅니다)')
        # 해양조사원은 음력날로 알려 줍니다. tide.js 는 달력 날짜를 받습니다.
        # 그 음력날이 든 날짜를 찾아 넣습니다 — 식을 베끼지 않습니다.
        날짜로 = {}
        for x in 받은것:
            날 = 음력날이든날(x['음력날'])
            if 날:
                날짜로[x['음력날']] = 날
        우리 = dict((x['날짜'], x) for x in 우리물때(list(날짜로.values())))
        print('')
        print('      음력  해양조사원   독립 셈     화면(tide.js)')
        for x in 받은것:
            날 = 날짜로.get(x['음력날'])
            c = 우리.get(str(날)) if 날 else None
            기준이름 = 독립.물때(날)['이름'] if 날 else '?'
            맞나 = bool(c) and c['이름'] == x['이름']
            기준맞나 = 기준이름 == x['이름']
            매맞나 = bool(c) and c['매'] == x['매']
            print('      %2d일  %-8s %-8s%s %-8s%s'
                  % (x['음력날'], x['이름'],
                     기준이름, '·' if 기준맞나 else '✗',
                     c['이름'] if c else '?',
                     '·' if (맞나 and 매맞나) else '✗'))
            if not 맞나:
                문제.append('음력 %d일 — 우리 %s / 해양조사원 %s'
                            % (x['음력날'], c['이름'] if c else '?', x['이름']))
            elif not 매맞나:
                문제.append('음력 %d일 매식 — 우리 %s / 해양조사원 %s'
                            % (x['음력날'], c['매'] if c else '?', x['매']))
        if not 문제:
            print('  · %d일이 하나도 안 틀립니다' % len(받은것))
        print('')

    # ── 2. 음력 계산이 맞는가
    print('[2] 음력 날짜가 맞는가')
    if 받은것:
        해양조사원오늘 = 받은것[0]['음력날']
        우리오늘 = 오늘음력()
        맞나 = 우리오늘 == 해양조사원오늘
        print('      오늘 — 우리 음력 %d일 · 해양조사원 %d일  %s'
              % (우리오늘, 해양조사원오늘, '·' if 맞나 else '✗'))
        if not 맞나:
            문제.append('음력 날짜가 어긋납니다 — 우리 %d일 / 해양조사원 %d일'
                        % (우리오늘, 해양조사원오늘))
    else:
        print('      ~ 견줄 값이 없어 건너뜁니다')
    print('')

    # ── 3. 막대는 실제 조차로 그리는가
    print('[3] 막대 길이가 실제 조차를 따라가는가')
    try:
        관측소, 조위 = 조위받기()
    except Exception as e:
        알리기('조위를 못 받았습니다 (%s) — 건너뜁니다 (계약-23)'
               % str(e)[:40])
        조위 = []
    if 조위:
        큰날 = max(조위, key=lambda v: v['조차'])
        작은날 = min(조위, key=lambda v: v['조차'])
        print('      기준 관측소 %s · 날 %d개' % (관측소, len(조위)))
        print('      물이 가장 많이 빠지는 날 %s (%dcm)'
              % (큰날['키'], 큰날['조차']))
        print('      물이 가장 적게 빠지는 날 %s (%dcm)'
              % (작은날['키'], 작은날['조차']))
        print('  · 막대는 이 조차로 그립니다 — 물때 이름과 며칠 어긋나는 것이')
        print('    정상입니다 (달보다 바다가 2~3일 늦게 따라옵니다)')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        print('')
    if 문제:
        print('손볼 곳 %d건' % len(문제))
        for x in 문제:
            print('  ✗ %s' % x)
        print('')
        print('  assets/js/tide.js 의 물때번호() 와 물때이름 을 보세요.')
        return 1 if '--strict' in sys.argv else 0
    print('물때가 국립해양조사원 자료와 맞습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
