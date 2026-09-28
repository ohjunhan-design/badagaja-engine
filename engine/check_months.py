# -*- coding: utf-8 -*-
"""열두 달을 **실제로 넘겨 보며** 화면이 제대로 따라가는지 봅니다.

★ 왜 생겼나 (2026-09-27 바깥 검수 3차)

      「월 변경 검사는 10월만 보지 말고 9→10, 10→11, 11→12, 12→1 을
        전부 순환 테스트하세요. 특히 연말→연초, 음력 연도 경계,
        윤달, 축제 종료, 어종 월 정보 이 네 가지는 별도 회귀군으로」

    `check_calendar.py --next` 는 **다음 달 하나**만 봅니다.
    지금이 9월이니 10월만 보는 셈입니다. 12월에서 1월로 넘어갈 때
    무슨 일이 나는지는 12월이 되어야 압니다. 그때는 늦습니다.

무엇을 하나
    브라우저 시계를 **열두 달로 차례차례 돌려** 놓고, 축제 달력이
    그때마다 제대로 그려지는지 봅니다. 사람이 기다릴 것 없이
    지금 1월도, 12월도 봅니다.

      · 달마다 그 달 단추가 눌리는가
      · 그 달에 열리는 축제만 보이는가
      · 12월 → 1월 로 넘어갈 때 아무것도 안 보이는 일이 없는가
      · 한 해가 바뀌어도(2026-12-31 → 2027-01-01) 그대로인가

    ★ 음력 쪽(윤달·음력 연도 경계)은 engine/check_newmoon.py 가
      2026~2035년 3,652일을 전수로 봅니다. 여기서는 겹쳐 안 봅니다.
      대신 **쪽이 음력 「달」을 내보이지 않는지**만 확인합니다 —
      우리가 내보이는 것은 음력 **날**과 물때뿐이라, 윤달이 와도
      갈릴 것이 없다는 것을 못 박아 둡니다.

쓰는 법
    python engine/check_months.py
    python engine/check_months.py --strict
"""
import os
import re
import sys
import glob
import json
import shutil
import tempfile
import subprocess
import html as _h

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine import machine   # noqa: E402  크롬 자리·메모리는 machine.py 한 곳에서만

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# ★ 크롬 자리는 engine/machine.py 한 곳에서만 봅니다
#   (2026-09-27 — 같은 목록이 검사기 6개에 베껴져 있었습니다.
#    리눅스에서 돌리려면 여섯 곳을 다 고쳐야 했습니다)

막음, 알림 = [], []

# 넘겨 볼 때들 — 달이 바뀌는 열두 자리 + 해가 바뀌는 자리
볼때들 = [('2027-%02d-15 12:00:00' % m, '%d월 한복판' % m)
          for m in range(1, 13)]
볼때들 += [
    ('2026-12-31 23:59:30', '해가 바뀌기 30초 전'),
    ('2027-01-01 00:00:30', '해가 바뀐 30초 뒤'),
    ('2027-02-28 23:59:30', '2월 마지막 밤'),
    ('2028-02-29 12:00:00', '윤년 2월 29일'),
]


def 주석빼기(js):
    """움직임에서 주석을 걷어냅니다.

    ★ 왜 (2026-09-27 — 헛것을 세 번째 냈습니다)
        tide.js 의 주석 한 줄
            //  2026-09-26(음력 8월 16일) 태안·제주·남해 세 관측소를 받아
        때문에 「음력 달을 셈해 내보인다」고 알렸습니다.
        **주석은 화면에 안 나옵니다.** 탈이 아닌 것을 알리면
        검사가 무뎌져 진짜 탈을 놓칩니다.
    """
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)     # /* … */
    js = re.sub(r'(?m)^\s*//.*$', '', js)              # 줄 통째로 주석
    js = re.sub(r'(?m)\s//[^\n]*$', '', js)           # 줄 끝 주석
    return js


def 크롬찾기():
    """크롬 자리. engine/machine.py 가 봅니다.

    ★ 여기에 목록을 따로 두지 않습니다 (2026-09-27)
      전에 크롬 찾기를 셋만 고치고 check_render 를
      빠뜨려서, 「크롬이 없을 때」 시험이 **진짜 크롬을
      찾아 통과**했습니다. 못 잰 것을 통과로 셌습니다.
    """
    return machine.크롬찾기()
def 시계돌려보기(쪽길, 때들):
    """그 쪽을 **시계를 돌려 놓고** 열어, 무엇이 보이는지 받아옵니다.

    ★ 쪽과 움직임 파일은 **그대로** 씁니다. 검사가 새로 만들지
      않습니다. 바꾸는 것은 시계 하나뿐입니다.
    """
    t = tempfile.mkdtemp(prefix='months-')
    try:
        # ★ 쪽을 **원래 있던 깊이 그대로** 놓습니다 (2026-09-27)
        #   전에는 임시 자리 뿌리에 놓았더니, 쪽이 부르는
        #   ../assets/js/festival-list.js 가 임시 자리 밖을 가리켜
        #   움직임이 아예 안 읽혔습니다. 그래 놓고 「달 단추가
        #   안 눌린다」고 알렸습니다 — **헛것**이었습니다.
        깊이 = os.path.relpath(os.path.dirname(쪽길), NEW)
        안쪽 = t if 깊이 in ('.', '') else os.path.join(t, 깊이)
        os.makedirs(안쪽, exist_ok=True)
        사본 = os.path.join(안쪽, 'a.html')
        원글 = io.read(쪽길)
        # 시계를 돌리는 코드를 **맨 앞에** 넣습니다. 그래야 쪽이
        # 읽히기 전에 Date 가 바뀝니다.
        돌리개 = """<script>
(function(){
  var 때 = new Date(%s);
  var 원래 = Date;
  function 가짜(){
    if (arguments.length === 0) return new 원래(때.getTime());
    return new (Function.prototype.bind.apply(
      원래, [null].concat([].slice.call(arguments))))();
  }
  가짜.prototype = 원래.prototype;
  가짜.now = function(){ return 때.getTime(); };
  가짜.parse = 원래.parse;
  가짜.UTC = 원래.UTC;
  window.Date = 가짜;
})();
</script>"""
        결과 = []
        for 때글, 이름 in 때들:
            y, rest = 때글.split('-', 1)
            m, rest2 = rest.split('-', 1)
            d, 시분초 = rest2.split(' ')
            시, 분, 초 = 시분초.split(':')
            인자 = '%s, %d, %s, %s, %s, %s' % (y, int(m) - 1, d, 시, 분, 초)
            글 = 원글.replace('<head>', '<head>' + (돌리개 % 인자), 1)
            글 += """
<script>
(function(){
  setTimeout(function(){
    var 답 = {달: null, 보이는카드: 0, 보이는달: [], 온카드: 0};
    var 칸 = document.getElementById('monthFilter');
    if (칸) {
      var 눌린 = 칸.querySelector('button[aria-pressed="true"]');
      답.달 = 눌린 ? 눌린.getAttribute('data-month') : null;
    }
    var 카드 = [].slice.call(document.querySelectorAll('[data-month]'));
    카드 = 카드.filter(function(c){ return c.tagName !== 'BUTTON'; });
    답.온카드 = 카드.length;
    카드.forEach(function(c){
      if (!c.hidden && c.offsetParent !== null) {
        답.보이는카드 += 1;
        var mm = c.getAttribute('data-month');
        if (답.보이는달.indexOf(mm) < 0) 답.보이는달.push(mm);
      }
    });
    var e = document.createElement('div');
    e.id = 'R2'; e.style.display = 'none';
    e.textContent = JSON.stringify(답);
    document.body.appendChild(e);
  }, 300);
})();
</script>"""
            io.write(사본, 글)
            # 움직임·차림표를 옆에 둡니다 — 쪽이 부르는 그대로
            for 갈래, 이름들 in (('js', ('festival-list.js', 'tide.js',
                                         'ads.js', 'ads-data.js',
                                         'point-list.js')),
                                 ('css', ('site.css',))):
                뒤 = os.path.join(t, 'assets', 갈래)
                os.makedirs(뒤, exist_ok=True)
                for nm in 이름들:
                    바탕 = os.path.join(ASSETS, 갈래, nm)
                    if os.path.exists(바탕):
                        io.write(os.path.join(뒤, nm), io.read(바탕))
            r = subprocess.run(
                [크롬찾기(), '--headless=new', '--disable-gpu',
                 '--host-resolver-rules=MAP * 127.0.0.1:1',
                 '--virtual-time-budget=4000', '--dump-dom',
                 'file:///' + 사본.replace(os.sep, '/')],
                capture_output=True, text=True, encoding='utf-8', timeout=120)
            m2 = re.search(r'id="R2"[^>]*>(.*?)</div>', r.stdout, re.S)
            if not m2:
                결과.append((때글, 이름, None))
                continue
            결과.append((때글, 이름, json.loads(_h.unescape(m2.group(1)))))
        return 결과
    finally:
        shutil.rmtree(t, ignore_errors=True)


def main():
    print('열두 달을 넘겨 보며 화면이 따라가는가 (바깥 검수 3차)')
    print('')

    달력쪽 = os.path.join(NEW, 'festival', 'index.html')
    if not os.path.exists(달력쪽):
        달력쪽 = os.path.join(NEW, 'festival.html')
    if not os.path.exists(달력쪽):
        print('  ? 축제 달력 쪽을 못 찾았습니다 — 아직 안 만들었습니다')
        print('')
        print('NOT_TESTED')
        return 2

    # ── 1. 열두 달 · 해 넘김
    print('[1] 달마다 그 달 축제가 제대로 보이는가')
    try:
        결과 = 시계돌려보기(달력쪽, 볼때들)
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        # ★ 못 쟀으면 통과가 아닙니다
        print('  ? 못 쟀습니다: %s' % e)
        print('    (크롬이 있어야 잽니다 — 주인 규칙 25)')
        print('')
        print('NOT_TESTED')
        return 2

    못본것, 어긋남, 빈달 = [], [], []
    for 때글, 이름, 답 in 결과:
        if 답 is None:
            못본것.append('%s (%s)' % (때글, 이름))
            print('      %-22s %-18s ✗ 못 봤습니다' % (때글, 이름))
            continue
        그달 = str(int(때글[5:7]))
        고른달 = 답.get('달')
        보이는 = 답.get('보이는카드', 0)
        보이는달 = 답.get('보이는달') or []
        탈 = []
        # 그 달에 열리는 축제가 있으면 그 달 단추가 눌려야 합니다
        if 고른달 is not None and 고른달 != '전체' and 고른달 != 그달:
            탈.append('%s월인데 %s월이 눌렸습니다' % (그달, 고른달))
        # 다른 달 축제가 섞여 보이면 안 됩니다
        섞임 = [x for x in 보이는달 if x and x != 고른달
                and 고른달 not in (None, '전체')]
        if 섞임:
            탈.append('다른 달이 섞임: %s' % ' '.join(섞임[:3]))
        if 보이는 == 0 and 답.get('온카드', 0) > 0:
            빈달.append('%s (%s)' % (때글, 이름))
            탈.append('보이는 축제가 하나도 없습니다')
        print('      %-22s %-18s 고른달 %-4s 보임 %3d개 %s'
              % (때글, 이름, 고른달 or '-', 보이는,
                 '✗ ' + ' · '.join(탈) if 탈 else '·'))
        if 탈:
            어긋남.append('%s — %s' % (때글, ' · '.join(탈)))

    if 못본것:
        막음.append('열어 보지 못한 때 %d가지' % len(못본것))
    if 어긋남:
        막음.append('달이 어긋나는 때 %d가지' % len(어긋남))
    if not (못본것 or 어긋남):
        print('  · 열두 달과 해 넘김까지 모두 제대로 따라갑니다')
    print('')

    # ── 2. 음력 — 윤달이 와도 갈릴 것이 없는가
    print('[2] 윤달·음력 연도 경계에 걸릴 것이 있는가')
    # ★ 무엇을 보아야 하나 (2026-09-27 — 헛것을 한 번 냈습니다)
    #
    #   처음에는 쪽에서 「음력 ○월」이라는 글자를 찾았습니다. 그랬더니
    #     강릉단오제  「음력 5월 5일 앞뒤로 여드레 동안 열리며」
    #     한산대첩축제 「1592년 음력 7월, 조선 수군이 …」
    #   가 걸렸습니다. 둘 다 **옛 날짜를 설명하는 글**입니다.
    #   윤달과 아무 상관이 없습니다.
    #
    #   갈릴 수 있는 것은 우리가 **셈해서 내보이는** 음력 달뿐입니다.
    #   그것을 만드는 것은 움직임 파일입니다. 거기를 봅니다.
    셈해서내는곳 = []
    for jp in sorted(glob.glob(os.path.join(ASSETS, 'js', '*.js'))):
        js = 주석빼기(io.read(jp, default=''))
        # 음력 **달**을 셈해 글자로 내놓는 자리가 있는가
        if re.search(r'음력[^\n]{0,40}월', js) or '윤달' in js:
            셈해서내는곳.append(os.path.basename(jp))
    if 셈해서내는곳:
        막음.append('음력 달을 셈해 내보이는 움직임 %d개 — 윤달에 갈립니다'
                    % len(셈해서내는곳))
        print('  ✗ %d개 움직임이 음력 **달**을 셈해 내보입니다'
              % len(셈해서내는곳))
        for x in 셈해서내는곳:
            print('      assets/js/%s' % x)
        print('      → 음력 달은 윤달 때문에 셈이 까다롭습니다.')
        print('        우리가 필요한 것은 음력 **날**과 물때뿐입니다.')
    else:
        print('  · 음력 **날**과 물때만 내보입니다 — 윤달이 와도')
        print('    갈릴 것이 없습니다.')
        print('    (음력 날짜는 engine/check_newmoon.py 가 2026~2035년')
        print('     3,652일을 전수로 봅니다)')
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
        print('')
        print('  ★ 12월에서 1월로 넘어갈 때 탈이 나면, 그것을 아는 것은')
        print('    12월 31일 밤입니다. 지금 미리 넘겨 봐야 합니다.')
        return 1 if '--strict' in sys.argv else 0

    print('열두 달과 해 넘김을 모두 넘겨 봤고, 탈이 없습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
