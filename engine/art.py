# -*- coding: utf-8 -*-
"""어종·해루질 쪽에 들어가는 **삽화**를 그립니다.

★ 왜 이 파일이 생겼나 (2026-09-29)

    옛 쪽과 새 쪽을 견주다 **삽화 245개가 통째로 사라진 것**을
    찾았습니다. 해루질 17쪽 · 낚시 18쪽이 저마다 7개씩 잃었습니다.

    자료는 멀쩡했습니다. `data/raw/guide.json` 에 `그림`·`깊이cm`·
    `흔적` 이 17가지 모두 채워져 있었습니다.
    **엔진이 그것으로 그림을 그리지 않았을 뿐입니다.**

    옛 생성기(`build-catch.ps1` · `build-fish.ps1`)에 있던 것을
    파이썬으로 옮겨 왔습니다.

★ 왜 사진이 아니라 그림인가

    주인 규칙 6-1 — 「사람은 눈으로 봅니다. 쪽에는 보이는 것이
    있어야 합니다. 숫자를 글로만 적지 말고 길이·색으로도 보이게
    합니다.」

    바지락 쪽에서 **갯벌 흔적 그림**이 빠지면, 정작 「무엇을 보고
    찾는지」를 글로만 읽게 됩니다. 조개 사진은 흔하지만
    **「숨구멍 두 개가 나란히」를 보여 주는 사진**은 없습니다.
    그래서 그립니다.

    깊이 그림은 `깊이cm` 에 **비례해 위치가 바뀝니다.**
    「18cm」라고 적는 것과, 그만큼 아래에 그려 주는 것은 다릅니다.

쓰는 법
    from engine import art
    art.흔적그림(어종)    갯벌 표면에서 무엇을 찾나 (640×240)
    art.단면그림(어종)    얼마나 깊이 있나 (640×280)
    art.물때그림('해루질')  간조 앞뒤가 왜 중요한가 (640×260)
    art.자리그림(어종)    어디에 서서 노리나 (640×240)
    art.채비그림(어종)    기본 채비 (640×280)
"""
import html

from engine.korean import 조사

# 빛깔 — 옛 쪽과 같게 둡니다. 바꾸면 화면이 달라집니다.
모래 = '#C7B89B'
짙은모래 = '#8d8064'
갯벌글씨 = '#5d5342'
바다 = '#DCE9EE'
짙은바다 = '#BBD3DC'
물빛 = '#EAF1F4'
물글씨 = '#41606b'
짚 = '#C07B22'
짙은짚 = '#8a5312'
붉음 = '#C0522B'
풀빛 = '#2F5D57'
돌 = '#7d8a92'


def 글(x):
    return html.escape(str(x or ''), quote=False)


def 이름of(어종):
    이 = 어종.get('이름')
    if isinstance(이, dict):
        return 이.get('ko') or ''
    return 이 or ''


def 말of(어종, 열쇠):
    v = 어종.get(열쇠)
    if isinstance(v, dict):
        return v.get('ko') or ''
    return v or ''


# ── ① 갯벌 표면 흔적 — 무엇을 보고 찾나 ────────────────────
흔적무늬 = {
    'shell': (
        "<g fill='#6f6350'><circle cx='250' cy='150' r='6'/>"
        "<circle cx='268' cy='146' r='5'/><circle cx='390' cy='166' r='6'/>"
        "<circle cx='408' cy='162' r='5'/></g>"
        "<text x='259' y='196' text-anchor='middle' font-size='14'"
        " fill='%s'>숨구멍 두 개가 나란히</text>" % 짚),
    'razor': (
        "<g fill='#6f6350'><ellipse cx='260' cy='150' rx='6' ry='11'/>"
        "<ellipse cx='392' cy='162' rx='6' ry='11'/></g>"
        "<text x='260' y='196' text-anchor='middle' font-size='14'"
        " fill='%s'>길쭉한 타원 구멍</text>" % 짚),
    'octopus': (
        "<circle cx='300' cy='150' r='13' fill='#5d5342'/>"
        "<text x='300' y='120' text-anchor='middle' font-size='14'"
        " font-weight='700' fill='%s'>부럿(주 구멍)</text>"
        "<g fill='#8b7f6a'><circle cx='352' cy='140' r='7'/>"
        "<circle cx='366' cy='166' r='6'/><circle cx='262' cy='172' r='6'/></g>"
        "<text x='396' y='196' text-anchor='middle' font-size='14'"
        " fill='%s'>주변 위장 구멍</text>"
        "<path d='M300 168 q10 18 40 12' stroke='#8b7f6a' stroke-width='2'"
        " stroke-dasharray='4 4' fill='none'/>" % (붉음, 짚)),
    'worm': (
        "<path d='M300 138 a12 12 0 1 1 0.1 0z' fill='none'"
        " stroke='#5d5342' stroke-width='5'/>"
        "<path d='M300 162 a12 12 0 1 1 0.1 0z' fill='none'"
        " stroke='#5d5342' stroke-width='5'/>"
        "<text x='300' y='204' text-anchor='middle' font-size='14'"
        " fill='%s'>8자 모양 흔적</text>" % 짚),
    'crab': (
        "<circle cx='300' cy='152' r='11' fill='#5d5342'/>"
        "<g fill='#8b7f6a'><circle cx='352' cy='150' r='9'/>"
        "<circle cx='252' cy='160' r='8'/></g>"
        "<text x='300' y='196' text-anchor='middle' font-size='14'"
        " fill='%s'>구멍 주변에 흙덩이</text>" % 짚),
}
흔적기본 = (
    "<path d='M232 140 q40 -26 84 -6 q42 -22 90 12 q22 18 -6 28 h-166"
    " q-20 -12 -2 -34z' fill='%s'/>"
    "<text x='320' y='200' text-anchor='middle' font-size='14'"
    " fill='%s'>돌·바위 표면과 틈을 살핍니다</text>" % (돌, 짚))


def 흔적그림(어종):
    """갯벌 표면에서 이런 자국을 찾습니다 (640×240)."""
    이름 = 이름of(어종)
    무늬 = 흔적무늬.get(어종.get('그림'), 흔적기본)
    흔적말 = 말of(어종, '흔적')
    return (
        '<figure class="cg-art photo--drawn">\n'
        '<svg viewBox="0 0 640 240" role="img"'
        ' aria-label="%s 찾을 때 보는 갯벌 표면 흔적 그림"'
        ' xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect width="640" height="240" fill="%s"/>\n'
        '  <g opacity=".3" fill="%s"><circle cx="90" cy="70" r="3"/>'
        '<circle cx="520" cy="60" r="2.5"/><circle cx="140" cy="210" r="2.5"/>'
        '<circle cx="560" cy="200" r="3"/><circle cx="430" cy="70" r="2.5"/></g>\n'
        '  <g opacity=".25" stroke="%s" stroke-width="2" fill="none">'
        '<path d="M0 100 q80 -14 160 0 t160 0 t160 0 t160 0"/>'
        '<path d="M0 186 q80 -14 160 0 t160 0 t160 0 t160 0"/></g>\n'
        '  %s\n'
        '  <text x="20" y="34" font-size="15" font-weight="700" fill="%s">'
        '갯벌 표면에서 이런 자국을 찾습니다</text>\n'
        '  <text x="620" y="34" text-anchor="end" font-size="12" fill="%s"'
        ' opacity=".8">바다가자닷컴 · badagaja.com</text>\n'
        '</svg>\n'
        '<figcaption>그림 · %s — 표면에서 이런 자국을 찾습니다: %s</figcaption>\n'
        '</figure>'
        % (조사(글(이름), '를'), 모래, 짙은모래, 짙은모래, 무늬,
           갯벌글씨, 갯벌글씨, 글(이름), 글(흔적말)))


# ── ② 갯벌 단면 — 얼마나 깊이 있나 ────────────────────────
def 몸무늬(갈래, y):
    """깊이 y 자리에 그릴 몸 모양."""
    표 = {
        'shell': ("<ellipse cx='320' cy='{y}' rx='26' ry='19' fill='{c}'/>"
                  "<path d='M294 {y} q26 -22 52 0' stroke='{d}'"
                  " stroke-width='2' fill='none'/>"
                  "<path d='M320 {y1} v38' stroke='{d}' stroke-width='1.5'/>"),
        'razor': ("<rect x='310' y='{y34}' width='20' height='68' rx='9'"
                  " fill='{c}'/><path d='M313 {y28} v56' stroke='{d}'"
                  " stroke-width='1.5'/>"),
        'octopus': (
            "<circle cx='320' cy='{y}' r='22' fill='{c}'/>"
            "<g stroke='{c}' stroke-width='5' stroke-linecap='round'"
            " fill='none'><path d='M302 {yp12} q-16 16 -30 10'/>"
            "<path d='M338 {yp12} q16 16 30 10'/>"
            "<path d='M312 {yp22} q-6 20 -18 26'/>"
            "<path d='M328 {yp22} q6 20 18 26'/></g>"
            "<circle cx='312' cy='{ym4}' r='3' fill='#fff'/>"
            "<circle cx='328' cy='{ym4}' r='3' fill='#fff'/>"),
        'worm': ("<path d='M286 {y} q34 -22 68 0 q-34 22 -68 0z' fill='{c}'/>"
                 "<path d='M300 {y} h40' stroke='{d}' stroke-width='1.5'/>"),
        # ★ **굴 전용** (2026-09-29 주인 지적 — 「굴사진인데 이게 뭐야」)
        #   굴은 조개가 아닙니다. 갯벌에 묻히지 않고 **바위에 붙어**
        #   삽니다. 껍데기는 회백색이고 울퉁불퉁하며, 여럿이
        #   **다닥다닥** 겹쳐 붙습니다. 그것이 굴을 굴로 보이게 합니다.
        #   전에는 조개 무늬를 그대로 써서 **주황 타원**이 떠 있었습니다.
        'rock': (
            # 바위
            "<path d='M238 {yp30} q18 -46 74 -50 q66 -4 92 20"
            " q22 18 18 30 z' fill='#8A939A'/>"
            "<path d='M262 {yp16} q14 -12 30 -8 M330 {yp20} q16 -10 30 -4'"
            " stroke='#6E7C86' stroke-width='2' fill='none' opacity='.7'/>"
            # 굴 껍데기 다섯 — 회백색, 울퉁불퉁, 겹쳐 붙어 있습니다
            "<g fill='#E4E1D6' stroke='#A9A395' stroke-width='1.6'>"
            "<path d='M272 {ym4} q-6 -16 8 -22 q18 -8 30 2 q10 8 2 18"
            " q-16 10 -40 2 z'/>"
            "<path d='M308 {ym14} q-4 -18 12 -22 q20 -6 30 6 q8 10 -2 18"
            " q-18 8 -40 -2 z'/>"
            "<path d='M348 {ym4} q-4 -16 12 -20 q18 -6 28 4 q8 8 0 16"
            " q-18 8 -40 0 z'/>"
            "<path d='M290 {yp8} q-4 -12 10 -16 q16 -4 24 4 q6 8 -2 12"
            " q-16 6 -32 0 z'/>"
            "<path d='M332 {yp10} q-4 -12 10 -16 q16 -4 24 4 q6 8 -2 12"
            " q-16 6 -32 0 z'/></g>"
            # 껍데기 결 — 굴 특유의 주름
            "<g stroke='#B7B1A2' stroke-width='1.2' fill='none' opacity='.9'>"
            "<path d='M280 {ym10} l6 14 M292 {ym12} l4 16'/>"
            "<path d='M320 {ym20} l4 16 M332 {ym20} l2 16'/>"
            "<path d='M360 {ym10} l4 14 M372 {ym10} l2 14'/></g>"),
        'crab': ("<ellipse cx='320' cy='{y}' rx='22' ry='15' fill='{c}'/>"
                 "<g stroke='{c}' stroke-width='4' stroke-linecap='round'>"
                 "<path d='M300 {yp4} l-16 10'/><path d='M340 {yp4} l16 10'/>"
                 "<path d='M304 {ym6} l-18 -8'/><path d='M336 {ym6} l18 -8'/>"
                 "</g><circle cx='313' cy='{ym6}' r='2.5' fill='#fff'/>"
                 "<circle cx='327' cy='{ym6}' r='2.5' fill='#fff'/>"),
        # ★ **고둥·소라** (2026-09-29 주인 지적 — 그림이 허술함)
        #   나선으로 감긴 껍데기와 **입구**가 있어야 고둥으로 보입니다.
        #   전에는 선 하나로 소용돌이만 그려 달팽이 낙서 같았습니다.
        'snail': (
            "<path d='M300 {yp16} q-10 -30 10 -42 q22 -14 40 0"
            " q16 12 6 26 q-8 12 -22 8 q-12 -4 -8 -14 q4 -8 12 -4'"
            " fill='{c}' stroke='{d}' stroke-width='2'/>"
            "<path d='M300 {yp16} q24 10 46 -4 q-6 12 -24 14"
            " q-16 2 -22 -10 z' fill='{d}'/>"
            "<path d='M322 {ym12} q10 -6 16 2 M316 {ym4} q12 -6 20 2'"
            " stroke='{d}' stroke-width='1.6' fill='none' opacity='.75'/>"),
        # ★ **전복** — 납작한 타원에 **숨구멍이 한 줄**로 뚫려 있습니다.
        #   그 구멍줄이 전복을 전복으로 보이게 합니다 (2026-09-29).
        'abalone': (
            "<path d='M252 {yp30} q20 -44 76 -48 q64 -4 90 20"
            " q22 18 16 28 z' fill='#8A939A'/>"
            "<ellipse cx='324' cy='{ym4}' rx='36' ry='20' fill='{c}'/>"
            "<ellipse cx='324' cy='{ym4}' rx='36' ry='20' fill='none'"
            " stroke='{d}' stroke-width='2'/>"
            "<g fill='{d}'><circle cx='302' cy='{ym12}' r='2.8'/>"
            "<circle cx='313' cy='{ym14}' r='2.8'/>"
            "<circle cx='325' cy='{ym14}' r='2.8'/>"
            "<circle cx='337' cy='{ym12}' r='2.8'/></g>"
            "<path d='M294 {y} q30 12 60 -2' stroke='{d}'"
            " stroke-width='1.6' fill='none' opacity='.8'/>"),
        # ★ **짱뚱어** — 갯벌 위를 기어 다니는 물고기.
        #   **튀어나온 두 눈**과 지느러미로 기는 모습이 특징입니다
        #   (2026-09-29 주인 지적 — 그냥 물고기로 보였습니다).
        'fish': (
            "<path d='M288 {y} q22 -14 48 -10 q26 4 38 10"
            " q-12 8 -38 12 q-26 4 -48 -12 z' fill='{c}'/>"
            "<path d='M374 {y} l16 -12 v26 z' fill='{d}'/>"
            "<circle cx='300' cy='{ym10}' r='6.5' fill='{c}'/>"
            "<circle cx='315' cy='{ym10}' r='6.5' fill='{c}'/>"
            "<circle cx='300' cy='{ym10}' r='3.2' fill='#2B2116'/>"
            "<circle cx='315' cy='{ym10}' r='3.2' fill='#2B2116'/>"
            "<circle cx='299' cy='{ym12}' r='1.2' fill='#fff'/>"
            "<circle cx='314' cy='{ym12}' r='1.2' fill='#fff'/>"
            "<path d='M318 {yp8} q10 16 26 10 M300 {yp8} q-6 14 -18 12'"
            " stroke='{d}' stroke-width='4' fill='none'"
            " stroke-linecap='round'/>"
            "<path d='M318 {ym4} q18 -10 36 -2' stroke='{d}'"
            " stroke-width='2' fill='none' opacity='.8'/>"),
    }
    # ★ **모르는 갈래면 그냥 타원이 나옵니다** — 그것이 오늘
    #   굴이 「주황 타원」으로 보이던 까닭입니다 (2026-09-29).
    #   자료에 있는 그림 값은 여기 **모두** 있어야 합니다.
    #   engine/check_design.py 검사 8이 이것을 봅니다.
    틀 = 표.get(갈래, "<ellipse cx='320' cy='{y}' rx='24' ry='17' fill='{c}'/>")
    return 틀.format(y=y, y1=y - 19, y34=y - 34, y28=y - 28,
                     yp4=y + 4, yp12=y + 12, yp16=y + 16, yp22=y + 22,
                     ym4=y - 4, ym6=y - 6, ym10=y - 10,
                     ym12=y - 12, ym14=y - 14, ym20=y - 20,
                     yp8=y + 8, yp10=y + 10,
                     yp20=y + 20, yp30=y + 30, c=짚, d=짙은짚)


def 단면그림(어종):
    """얼마나 깊이 있나 (640×280). **깊이에 비례해 자리가 바뀝니다.**"""
    이름 = 이름of(어종)
    깊이 = int(어종.get('깊이cm') or 0)
    y = 92 + min(150, round(깊이 * 3.4))
    몸 = 몸무늬(어종.get('그림'), y)
    if 깊이 > 0:
        깊이표 = (
            "<g stroke='%s' stroke-width='1.6' stroke-dasharray='5 4'>"
            "<path d='M200 92 V%d'/></g>"
            "<g stroke='%s' stroke-width='1.6'><path d='M194 92 h12'/>"
            "<path d='M194 %d h12'/></g>"
            "<text x='188' y='%d' text-anchor='end' font-size='15'"
            " fill='%s' font-weight='700'>약 %dcm</text>"
            % (풀빛, y, 풀빛, y, round((y + 92) / 2) + 5, 풀빛, 깊이))
        설명 = ('갯벌 표면에서 대략 %dcm 아래에 있습니다. '
                '파 내려갈 깊이를 가늠해 보세요.' % 깊이)
    else:
        깊이표 = ("<text x='188' y='108' text-anchor='end' font-size='15'"
                  " fill='%s' font-weight='700'>표면·바위</text>" % 풀빛)
        설명 = ('갯벌 속이 아니라 바위와 돌 표면에 붙어 있습니다. '
                '물이 빠진 뒤 바위틈을 살펴보세요.')
    return (
        '<figure class="cg-art photo--drawn">\n'
        '<svg viewBox="0 0 640 280" role="img"'
        ' aria-label="%s 있는 깊이와 갯벌 단면 그림"'
        ' xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect width="640" height="92" fill="#DCE6EA"/>\n'
        '  <path d="M0 78 q40 -10 80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0'
        ' t80 0 V92 H0z" fill="#B9D0DA"/>\n'
        '  <rect y="92" width="640" height="188" fill="%s"/>\n'
        '  <rect y="92" width="640" height="9" fill="#A9997D"/>\n'
        '  <g opacity=".35" fill="%s"><circle cx="90" cy="150" r="3"/>'
        '<circle cx="150" cy="200" r="2.5"/><circle cx="470" cy="160" r="3"/>'
        '<circle cx="540" cy="210" r="2.5"/><circle cx="240" cy="235" r="2.5"/>'
        '<circle cx="410" cy="245" r="3"/></g>\n'
        '  <g stroke="#7b6a4d" stroke-width="2" fill="none">'
        '<path d="M296 92 q4 -8 8 0"/><path d="M336 92 q4 -8 8 0"/></g>\n'
        '  %s\n  %s\n'
        '  <text x="640" y="26" text-anchor="end" font-size="14" fill="%s"'
        ' opacity=".9">바다가자닷컴 · badagaja.com</text>\n'
        '</svg>\n'
        '<figcaption>그림 · %s — %s</figcaption>\n'
        '</figure>'
        % (조사(글(이름), '가'), 모래, 짙은모래, 깊이표, 몸, 물글씨,
           글(이름), 설명))


# ── ③ 물때 곡선 — 간조 앞뒤가 왜 중요한가 ─────────────────
def 물때그림(누구='해루질'):
    """간조 앞뒤 1~2시간이 핵심임을 곡선으로 보입니다 (640×260)."""
    return (
        '<figure class="cg-art photo--drawn">\n'
        '<svg viewBox="0 0 640 290" role="img"'
        ' aria-label="물때 곡선과 %s 하기 좋은 시간대 그림"'
        ' xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect width="640" height="290" fill="%s"/>\n'
        '  <rect x="232" y="40" width="176" height="150" fill="%s"'
        ' opacity=".14"/>\n'
        '  <text x="320" y="62" text-anchor="middle" font-size="14"'
        ' font-weight="700" fill="%s">여기가 좋은 시간</text>\n'
        '  <path d="M40 70 Q140 70 190 130 T320 190 T450 130 T600 70"'
        ' fill="none" stroke="#3a7ca5" stroke-width="4"/>\n'
        '  <g stroke="#9fb6c0" stroke-width="1.2"><path d="M40 190 H600"/>'
        '<path d="M40 70 H600"/></g>\n'
        '  <text x="34" y="74" text-anchor="end" font-size="13" fill="%s">'
        '만조</text>\n'
        '  <text x="34" y="194" text-anchor="end" font-size="13" fill="%s">'
        '간조</text>\n'
        '  <circle cx="320" cy="190" r="7" fill="%s"/>\n'
        '  <text x="320" y="216" text-anchor="middle" font-size="14"'
        ' font-weight="700" fill="%s">간조(물이 가장 많이 빠진 때)</text>\n'
        '  <g stroke="%s" stroke-width="2" fill="none">'
        '<path d="M232 236 v14"/><path d="M408 236 v14"/>'
        '<path d="M232 243 H408"/></g>\n'
        '  <text x="232" y="270" text-anchor="middle" font-size="13"'
        ' fill="%s">간조 2시간 전</text>\n'
        '  <text x="408" y="270" text-anchor="middle" font-size="13"'
        ' fill="%s">간조 1~2시간 후</text>\n'
        '  <g stroke="%s" stroke-width="2.4" fill="none">'
        '<path d="M470 150 l26 -22 M470 150 l26 22 M470 150 h64"/></g>\n'
        '  <text x="546" y="146" font-size="13" fill="%s"'
        ' font-weight="700">물이 들어옵니다</text>\n'
        '  <text x="620" y="28" text-anchor="end" font-size="12" fill="%s"'
        ' opacity=".85">바다가자닷컴 · badagaja.com</text>\n'
        '</svg>\n'
        '<figcaption>그림 · 물때 곡선 — 간조 앞뒤 1~2시간이 핵심입니다. '
        '물이 들어오기 시작하면 바로 나오세요. 날짜별 간조 시각은 '
        '권역 쪽 물때표에서 볼 수 있습니다.</figcaption>\n'
        '</figure>'
        % (글(누구), 물빛, 짚, 짙은짚, 물글씨, 물글씨, 붉음, 붉음,
           풀빛, 풀빛, 풀빛, 붉음, 붉음, 물글씨))


def 잘잡히는자리(어디):
    """★ **잘 잡히는 자리**를 자료에서 고릅니다 (2026-09-29 주인 지시)

    자료의 「어디서」 글에 적힌 바닥·지형으로 고릅니다.
    **없는 말을 지어내지 않습니다** — 맞는 것이 없으면 일반 안내를 냅니다.
    """
    개펄 = ('모래' in 어디 or '펄' in 어디)
    구조물 = ('방파제' in 어디 or '선착장' in 어디 or '항' in 어디)
    돌밭 = ('갯바위' in 어디 or '여' in 어디 or '암초' in 어디)
    if 돌밭:
        return {'x': 300, 'y': 196,
                '글': '바위와 모래가 만나는 자리'}
    if 개펄 and 구조물:
        return {'x': 320, 'y': 196,
                '글': '벽 아래 바닥을 끌어 노립니다'}
    if 개펄:
        return {'x': 300, 'y': 196, '글': '모래·펄 바닥을 끌어 노립니다'}
    if 구조물:
        return {'x': 340, 'y': 196, '글': '벽 모서리와 기둥 둘레'}
    return {'x': 300, 'y': 196, '글': '물살이 부딪히는 자리'}


# ── ④ 어디에 서서 노리나 (낚시) ───────────────────────────
def 자리그림(어종):
    """서는 자리를 그립니다 (640×240). 「어디서」 글을 보고 고릅니다."""
    이름 = 이름of(어종)
    어디 = 말of(어종, '어디서')
    if '선상' in 어디:
        장면 = (
            "<path d='M150 96 q70 -18 140 0 l-26 34 h-88z' fill='%s'/>"
            "<rect x='206' y='72' width='8' height='26' fill='%s'/>"
            "<path d='M300 120 V200' stroke='%s' stroke-width='2'/>"
            "<circle cx='300' cy='206' r='9' fill='%s'/>"
            "<text x='220' y='92' text-anchor='middle' font-size='13'"
            " fill='#fff'>배 위</text>"
            "<text x='360' y='210' font-size='14' fill='%s'"
            " font-weight='700'>바닥 근처를 노립니다</text>"
            % (물글씨, 물글씨, 물글씨, 붉음, 붉음))
    elif '갯바위' in 어디:
        장면 = (
            "<path d='M60 200 q60 -80 140 -70 q70 -50 140 6 q60 -26 96 30"
            " v34 H60z' fill='%s'/>"
            "<circle cx='250' cy='118' r='9' fill='%s'/>"
            "<path d='M250 110 l60 -34' stroke='%s' stroke-width='3'/>"
            "<text x='250' y='100' text-anchor='middle' font-size='13'"
            " fill='%s' font-weight='700'>서는 자리</text>"
            "<path d='M330 150 q26 16 52 6' stroke='%s' stroke-width='2.4'"
            " fill='none' stroke-dasharray='5 4'/>"
            "<text x='430' y='150' font-size='14' fill='%s'"
            " font-weight='700'>물살이 도는 쪽</text>"
            % (돌, 풀빛, 풀빛, 풀빛, 붉음, 붉음))
    elif '하구' in 어디:
        장면 = (
            "<path d='M0 150 q160 -30 320 0 t320 0 V240 H0z' fill='#9fb6c0'/>"
            "<rect y='196' width='640' height='44' fill='%s'/>"
            "<text x='120' y='140' font-size='14' fill='%s'"
            " font-weight='700'>강물</text>"
            "<text x='520' y='140' font-size='14' fill='%s'"
            " font-weight='700'>바닷물</text>"
            "<circle cx='320' cy='150' r='8' fill='%s'/>"
            "<text x='320' y='128' text-anchor='middle' font-size='14'"
            " fill='%s' font-weight='700'>물이 섞이는 자리</text>"
            % (모래, 물글씨, 물글씨, 붉음, 붉음))
    else:
        # ★ **어디가 잘 잡히는지 표시합니다** (2026-09-29 주인 지시)
        #   「이 그림도 구체적으로 어떤 포인트가 더 잘 잡히는지
        #     표시해 줬으면 좋겠어요」
        #
        #   전에는 「안쪽(초보) · 끝자락(물살) · 테트라포드(위험)」만
        #   있었습니다. **서도 되는 자리**만 말하고 **잘 잡히는 자리**는
        #   말하지 않았습니다. 낚시하러 온 분이 알고 싶은 것은 뒤쪽입니다.
        #
        #   ★ 자리는 **어종마다 다릅니다.** 자료의 「어디서」를 읽어
        #     고릅니다 — 지어내지 않습니다.
        어디잘 = 잘잡히는자리(어디)
        장면 = (
            "<rect x='60' y='120' width='420' height='34' fill='#9aa3a8'/>"
            "<rect x='60' y='154' width='420' height='46' fill='%s'/>"
            "<g fill='#6d787e'><path d='M480 200 l24 -30 24 30z'/>"
            "<path d='M516 200 l24 -30 24 30z'/>"
            "<path d='M552 200 l24 -30 24 30z'/></g>"
            "<text x='560' y='224' text-anchor='middle' font-size='13'"
            " fill='%s' font-weight='700'>테트라포드(위험)</text>"
            "<circle cx='150' cy='108' r='9' fill='%s'/>"
            "<text x='150' y='92' text-anchor='middle' font-size='13'"
            " fill='%s' font-weight='700'>안쪽(초보)</text>"
            "<circle cx='430' cy='108' r='9' fill='%s'/>"
            "<text x='430' y='92' text-anchor='middle' font-size='13'"
            " fill='%s' font-weight='700'>끝자락(물살)</text>"
            "<path d='M430 116 l40 40' stroke='%s' stroke-width='2.6'/>"
            # ── 잘 잡히는 자리 — 물속에 별표와 설명
            "<g>"
            "<path d='M%d 162 l4.6 9.4 10.4 1.5 -7.5 7.3 1.8 10.3"
            " -9.3 -4.9 -9.3 4.9 1.8 -10.3 -7.5 -7.3 10.4 -1.5z'"
            " fill='#E3A008' stroke='#fff' stroke-width='1.2'/>"
            "<text x='%d' y='%d' text-anchor='middle' font-size='12.5'"
            " fill='#fff' font-weight='700'"
            " style='paint-order:stroke' stroke='#3C5460'"
            " stroke-width='3.2'>%s</text>"
            "</g>"
            % (돌, 붉음, 풀빛, 풀빛, 붉음, 붉음, 붉음,
               어디잘['x'] - 9, 어디잘['x'], 어디잘['y'], 어디잘['글']))
    return (
        '<figure class="cg-art photo--drawn">\n'
        '<svg viewBox="0 0 640 240" role="img"'
        ' aria-label="%s 노리는 장소 그림"'
        ' xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect width="640" height="240" fill="%s"/>\n'
        '  <rect y="150" width="640" height="90" fill="%s"/>\n'
        '  <g opacity=".5" stroke="#9fb6c0" stroke-width="1.4">'
        '<path d="M40 176 h50"/><path d="M560 168 h50"/></g>\n'
        '  %s\n'
        '  <text x="20" y="32" font-size="15" font-weight="700" fill="%s">'
        '어디에 서서 노리나</text>\n'
        '  <text x="620" y="32" text-anchor="end" font-size="12" fill="%s"'
        ' opacity=".85">바다가자닷컴 · badagaja.com</text>\n'
        '</svg>\n'
        '<figcaption>그림 · %s — %s</figcaption>\n'
        '</figure>'
        % (조사(글(이름), '를'), 바다, 짙은바다, 장면, 물글씨, 물글씨,
           글(이름), 글(어디)))


# ── ⑤ 기본 채비 (낚시) ────────────────────────────────────
채비무늬 = {
    'bottom': (
        "<path d='M320 60 V196' stroke='{선}' stroke-width='2'/>"
        "<g stroke='{바늘}' stroke-width='2.4' fill='none'>"
        "<path d='M320 110 h32 q10 0 10 10 q0 12 -12 12 q-8 0 -8 -8'/>"
        "<path d='M320 150 h32 q10 0 10 10 q0 12 -12 12 q-8 0 -8 -8'/></g>"
        "<ellipse cx='320' cy='206' rx='13' ry='17' fill='{짚}'/>"
        "<text x='372' y='118' font-size='14' fill='{선}'>바늘</text>"
        "<text x='372' y='158' font-size='14' fill='{선}'>바늘</text>"
        "<text x='340' y='212' font-size='14' fill='{짙짚}'>봉돌</text>"),
    'float': (
        "<path d='M320 96 V210' stroke='{선}' stroke-width='2'/>"
        "<ellipse cx='320' cy='92' rx='15' ry='20' fill='{짚}'/>"
        "<path d='M320 66 v-14' stroke='{짚}' stroke-width='3'/>"
        "<circle cx='320' cy='150' r='6' fill='#7d8a92'/>"
        "<g stroke='{바늘}' stroke-width='2.4' fill='none'>"
        "<path d='M320 206 q0 12 12 12 q10 0 10 -10'/></g>"
        "<text x='344' y='96' font-size='14' fill='{짙짚}'>찌</text>"
        "<text x='334' y='154' font-size='14' fill='{선}'>봉돌</text>"
        "<text x='352' y='214' font-size='14' fill='{선}'>바늘·미끼</text>"),
    # ★ **실제 지그헤드 모양으로 다시 그렸습니다** (2026-09-29 주인 지적)
    #   「이미지가 현실성이 좀 떨어져 … 너무 허술하고」
    #
    #   전에는 주황 동그라미에 초록 나뭇잎이 붙은 꼴이라
    #   **바늘이 보이지 않았습니다.** 지그헤드의 핵심은
    #     ① 납 머리(무게)  ② 거기서 뻗은 바늘  ③ 꿰운 웜
    #   셋입니다. 셋이 다 보여야 「왜 가벼우면 천천히 가라앉나」가
    #   이해됩니다.
    'jighead': (
        # 원줄
        "<path d='M290 66 L322 142' stroke='{선}' stroke-width='2'/>"
        # 웜 — 길쭉한 몸통 + 물결 꼬리 (바늘을 덮습니다)
        "<path d='M336 146 q40 0 54 8 q-14 10 -54 10 z' fill='#8FB98A'/>"
        "<path d='M390 154 q16 -12 24 -4 q-6 12 -24 8 z' fill='#7AA27F'/>"
        # 웜 몸통에 난 마디 (고무 미끼 느낌)
        "<g stroke='#6E9A72' stroke-width='1.2' opacity='.8'>"
        "<path d='M352 148 l-2 14'/><path d='M364 149 l-2 14'/>"
        "<path d='M376 151 l-2 12'/></g>"
        # 바늘 — 머리에서 뒤로 뻗어 **웜 등 위로** 굽어 나옵니다
        "<g stroke='#5A6670' stroke-width='2.6' fill='none'"
        " stroke-linecap='round'>"
        "<path d='M330 158 q26 22 44 6 q10 -8 2 -18'/>"
        "<path d='M376 146 l-6 -7 m6 7 l-8 2'/></g>"      # 미늘
        # 납 머리 — 은회색 구슬. 눈이 있어 진짜처럼 보입니다
        "<circle cx='328' cy='150' r='12' fill='#93A0A8'/>"
        "<circle cx='328' cy='150' r='12' fill='none'"
        " stroke='#6E7C86' stroke-width='1.4'/>"
        "<circle cx='324' cy='146' r='3.4' fill='#2B2116'/>"
        "<circle cx='323' cy='145' r='1.2' fill='#fff'/>"
        # 줄을 매는 고리
        "<path d='M322 142 q-4 -8 2 -10' stroke='#6E7C86'"
        " stroke-width='2' fill='none'/>"
        "<text x='300' y='184' font-size='14' fill='{짙짚}'"
        " text-anchor='end'>납 머리</text>"
        "<text x='396' y='186' font-size='14' fill='{선}'>웜</text>"
        "<text x='372' y='128' font-size='13' fill='#5A6670'>바늘</text>"),
    # ★ **실제 에기 모양으로 다시 그렸습니다** (2026-09-29 주인 지적)
    #   「쭈꾸미도 이런에기는 시중에 없어 이게 에기인지도 모르고」
    #
    #   전에는 회전한 타원에 삼각형을 붙여 **물고기처럼** 보였습니다.
    #   진짜 에기는
    #     ① 새우를 닮은 통통한 몸    ② 등의 줄무늬
    #     ③ 꼬리 쪽 **왕관 바늘**(침이 빙 둘러 여러 개)
    #     ④ 배 앞쪽 봉돌(가라앉는 자세를 만듭니다)
    #   입니다. 특히 왕관 바늘이 에기를 에기로 보이게 합니다.
    'egi': (
        "<path d='M296 64 L332 128' stroke='{선}' stroke-width='2'/>"
        "<g transform='rotate(-18 360 154)'>"
        # 몸통 — 새우처럼 등이 굽고 배가 통통합니다
        "<path d='M326 150 q10 -20 38 -20 q34 0 50 20"
        " q-16 20 -50 20 q-28 0 -38 -20 z' fill='{짚}'/>"
        # 등 줄무늬
        "<g stroke='{짙짚}' stroke-width='2' opacity='.85'>"
        "<path d='M346 134 l-4 32'/><path d='M360 132 l-4 36'/>"
        "<path d='M374 133 l-4 34'/><path d='M388 137 l-4 28'/></g>"
        # 머리 쪽 눈
        "<circle cx='334' cy='150' r='4' fill='#2B2116'/>"
        "<circle cx='333' cy='149' r='1.4' fill='#fff'/>"
        # 배 앞 봉돌 — 이것이 가라앉는 자세를 만듭니다
        "<ellipse cx='340' cy='166' rx='9' ry='6' fill='#8A939A'/>"
        # 꼬리 쪽 **왕관 바늘** — 침이 빙 둘러 있습니다
        "<g stroke='#5A6670' stroke-width='2.2' fill='none'"
        " stroke-linecap='round'>"
        "<path d='M414 150 l16 -12'/><path d='M414 150 l18 -2'/>"
        "<path d='M414 152 l18 8'/><path d='M414 154 l14 16'/>"
        "<path d='M414 148 l10 -18'/></g>"
        "<path d='M410 138 v28' stroke='#5A6670' stroke-width='3'/>"
        "</g>"
        "<text x='306' y='196' font-size='14' fill='{짙짚}'"
        " text-anchor='end'>에기</text>"
        "<text x='418' y='196' font-size='13' fill='#5A6670'>왕관 바늘</text>"
        "<text x='330' y='206' font-size='13' fill='{선}'>봉돌</text>"),
    'sabiki': (
        "<path d='M320 60 V200' stroke='{선}' stroke-width='2'/>"
        "<g stroke='{바늘}' stroke-width='2' fill='none'>"
        "<path d='M320 94 h24 q8 0 8 8'/><path d='M320 124 h24 q8 0 8 8'/>"
        "<path d='M320 154 h24 q8 0 8 8'/><path d='M320 184 h24 q8 0 8 8'/>"
        "</g><g fill='#e8dcc4'><circle cx='356' cy='104' r='4'/>"
        "<circle cx='356' cy='134' r='4'/><circle cx='356' cy='164' r='4'/>"
        "<circle cx='356' cy='194' r='4'/></g>"
        "<ellipse cx='320' cy='212' rx='12' ry='15' fill='{짚}'/>"
        "<text x='380' y='140' font-size='14' fill='{선}'>여러 바늘</text>"
        "<text x='338' y='218' font-size='14' fill='{짙짚}'>봉돌</text>"),
    'lure': (
        "<path d='M286 70 L330 130' stroke='{선}' stroke-width='2'/>"
        "<g transform='rotate(-16 348 146)'>"
        "<ellipse cx='348' cy='146' rx='34' ry='13' fill='{짚}'/>"
        "<circle cx='326' cy='142' r='3.4' fill='#fff'/>"
        "<path d='M382 146 l16 -8 v16z' fill='{짙짚}'/>"
        "<g stroke='{바늘}' stroke-width='2.2' fill='none'>"
        "<path d='M338 160 q-4 12 6 14'/>"
        "<path d='M364 160 q4 12 -6 14'/></g></g>"
        "<text x='272' y='140' font-size='14' fill='{짙짚}'"
        " text-anchor='end'>루어</text>"),
    'boat': (
        "<path d='M150 60 q60 -16 120 0 l-22 34 h-76z' fill='{선}'/>"
        "<path d='M320 96 V210' stroke='{선}' stroke-width='2'/>"
        "<ellipse cx='320' cy='214' rx='16' ry='20' fill='{짚}'/>"
        "<path d='M320 232 q-10 16 -22 20 M320 232 q10 16 22 20'"
        " stroke='{짚}' stroke-width='3' fill='none'/>"
        "<text x='352' y='222' font-size='14' fill='{짙짚}'>타이라바</text>"
        "<text x='210' y='84' font-size='14' fill='#fff'"
        " text-anchor='middle'>배</text>"),
}


def 채비그림(어종):
    """기본 채비를 그립니다 (640×280)."""
    이름 = 이름of(어종)
    틀 = 채비무늬.get(어종.get('그림'),
                      "<path d='M320 60 V200' stroke='{선}' stroke-width='2'/>")
    부품 = 틀.format(선=물글씨, 바늘=풀빛, 짚=짚, 짙짚=짙은짚)
    return (
        '<figure class="cg-art photo--drawn">\n'
        '<svg viewBox="0 0 640 280" role="img" aria-label="%s 기본 채비 그림"'
        ' xmlns="http://www.w3.org/2000/svg">\n'
        '  <rect width="640" height="280" fill="%s"/>\n'
        '  <path d="M0 40 q40 -10 80 0 t80 0 t80 0 t80 0 t80 0 t80 0 t80 0'
        ' t80 0 V56 H0z" fill="#CFE0E7"/>\n'
        '  <rect y="56" width="640" height="224" fill="%s"/>\n'
        '  <rect y="246" width="640" height="34" fill="%s"/>\n'
        '  <g opacity=".5" stroke="#9fb6c0" stroke-width="1.4">'
        '<path d="M40 120 h60"/><path d="M540 96 h60"/>'
        '<path d="M60 190 h50"/></g>\n'
        '  %s\n'
        '  <text x="20" y="34" font-size="15" fill="%s" font-weight="700">'
        '%s 기본 채비</text>\n'
        '  <text x="620" y="34" text-anchor="end" font-size="13" fill="%s"'
        ' opacity=".85">바다가자닷컴 · badagaja.com</text>\n'
        '</svg>\n'
        '<figcaption>그림 · %s — %s</figcaption>\n'
        '</figure>'
        % (글(이름), 물빛, 바다, 모래, 부품, 물글씨, 글(이름), 물글씨,
           글(이름), 글(말of(어종, '채비')) or '기본 채비입니다.'))


def 그림들(어종):
    """한 어종 쪽에 들어갈 삽화를 차례대로 냅니다.

    해루질이면 흔적 → 단면 → 물때,
    낚시면 자리 → 채비 → 물때 입니다.
    """
    갈래 = 어종.get('갈래')
    if 갈래 == '해루질':
        return [흔적그림(어종), 단면그림(어종), 물때그림('해루질')]
    return [자리그림(어종), 채비그림(어종), 물때그림('낚시')]


# ── ⑥ 배우는 차례 — 그림 넉 장으로 가르칩니다 ─────────────
#
#   ★ 2026-09-29 — 이것이 가장 값진 손실이었습니다.
#
#     옛 쪽에는 「그림으로 보는 바지락 잡는 법 · 그림 4장」이
#     있었습니다. 장식이 아니라 **배우는 차례**입니다.
#
#         ① 모래 섞인 단단한 갯벌 vs 무른 뻘   어디로 갈지
#         ② 작은 구멍이 나란히 두 개           무엇을 볼지
#         ③ 10cm, 옆으로 긁듯이               어떻게 팔지
#         ④ 3cm 아래는 돌려보냅니다            무엇을 지킬지
#
#     35갈래 141단계를 손으로 그린 것입니다. 파이썬으로 옮기다
#     틀리느니, 옛 생성기를 그대로 돌려 완성된 그림을 뽑아
#     `data/raw/lessons.json` 에 자료로 두었습니다.
def 배우는차례(어종, 차례자료, 기초주소=None):
    """그림 넉 장으로 잡는 법을 보입니다 (320×220 씩).

    차례자료 는 `data/raw/lessons.json` 의 '차례' 입니다.
    그 어종 것이 없으면 빈 글을 냅니다 — 없는 것을 지어내지
    않습니다.
    """
    단계들 = (차례자료 or {}).get(어종.get('id')) or []
    if not 단계들:
        return ''
    이름 = 이름of(어종)
    갈래 = 어종.get('갈래')
    찾는말 = '찾습니다' if 갈래 == '해루질' else '잡습니다'

    칸들 = []
    for i, 단 in enumerate(단계들, 1):
        칸들.append(
            '<figure class="ls-card">\n'
            '<svg viewBox="0 0 320 220" role="img" aria-label="%s 그림"'
            ' xmlns="http://www.w3.org/2000/svg">\n'
            '<rect width="320" height="220" fill="%s"/>\n%s\n</svg>\n'
            '<figcaption><b><i class="ls-no">%d</i>%s</b>'
            '<span>%s</span></figcaption>\n'
            '</figure>'
            % (글(단.get('제목')), 물빛, 단.get('그림') or '', i,
               글(단.get('제목')), 단.get('설명') or ''))

    머리 = ['<div class="ls-head">',
            '<p class="ls-kicker">그림으로 보는 %s %s 법 · 그림 %d장</p>'
            % (글(이름), 찾는말[:-3] + '는', len(단계들)),
            '<h2 class="serif">%s, 이렇게 %s</h2>' % (글(이름), 찾는말)]
    흔적말 = 말of(어종, '흔적')
    깊이 = 어종.get('깊이cm') or 0
    잔말 = []
    if 흔적말:
        잔말.append('<b>찾는 표시</b> — %s.' % 글(흔적말))
    if 깊이:
        잔말.append('%s은 갯벌 표면에서 <b>약 %dcm</b> 아래에 있습니다.'
                    % (글(이름), 깊이))
    if 잔말:
        머리.append('<p class="ls-lede">%s</p>' % ' '.join(잔말))
    머리.append('</div>')

    # 넉 장이면 2x2 로 둡니다 - 셋에 하나가 남으면 외롭습니다
    칸모양 = 'ls-grid ls-grid--2' if len(칸들) == 4 else 'ls-grid'
    return ('<section class="ls" id="lesson">\n%s\n'
            '<div class="%s">\n%s\n</div>\n</section>'
            % ('\n'.join(머리), 칸모양, '\n'.join(칸들)))
