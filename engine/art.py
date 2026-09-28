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
        '<figure class="cg-art">\n'
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
        '<figcaption>%s — 표면에서 이런 자국을 찾습니다: %s</figcaption>\n'
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
        'crab': ("<ellipse cx='320' cy='{y}' rx='22' ry='15' fill='{c}'/>"
                 "<g stroke='{c}' stroke-width='4' stroke-linecap='round'>"
                 "<path d='M300 {yp4} l-16 10'/><path d='M340 {yp4} l16 10'/>"
                 "<path d='M304 {ym6} l-18 -8'/><path d='M336 {ym6} l18 -8'/>"
                 "</g><circle cx='313' cy='{ym6}' r='2.5' fill='#fff'/>"
                 "<circle cx='327' cy='{ym6}' r='2.5' fill='#fff'/>"),
        'snail': ("<path d='M320 {yp16} a20 20 0 1 1 14 -34 a13 13 0 1 1"
                  " -9 22 a7 7 0 1 1 5 -12' fill='none' stroke='{c}'"
                  " stroke-width='7' stroke-linecap='round'/>"),
        'rock': ("<path d='M250 116 q40 -34 88 -12 q46 -26 92 14 q26 22 -6 34"
                 " h-176 q-24 -14 2 -36z' fill='#7d8a92'/><g fill='{c}'>"
                 "<ellipse cx='300' cy='112' rx='16' ry='10'"
                 " transform='rotate(-12 300 112)'/>"
                 "<ellipse cx='348' cy='106' rx='14' ry='9'"
                 " transform='rotate(8 348 106)'/>"
                 "<ellipse cx='386' cy='118' rx='13' ry='8'"
                 " transform='rotate(-6 386 118)'/></g>"),
        'abalone': ("<path d='M250 116 q40 -34 88 -12 q46 -26 92 14 q26 22 -6"
                    " 34 h-176 q-24 -14 2 -36z' fill='#7d8a92'/>"
                    "<ellipse cx='330' cy='106' rx='30' ry='16' fill='{c}'/>"
                    "<g fill='{d}'><circle cx='316' cy='102' r='2.5'/>"
                    "<circle cx='326' cy='100' r='2.5'/>"
                    "<circle cx='336' cy='101' r='2.5'/>"
                    "<circle cx='346' cy='104' r='2.5'/></g>"),
        'fish': ("<ellipse cx='324' cy='84' rx='30' ry='13' fill='{c}'/>"
                 "<path d='M354 84 l22 -12 v24z' fill='{c}'/>"
                 "<circle cx='306' cy='80' r='4' fill='#fff'/>"
                 "<circle cx='306' cy='80' r='2' fill='#2A1B08'/>"
                 "<path d='M300 95 l10 12 M330 95 l8 12' stroke='{c}'"
                 " stroke-width='4' stroke-linecap='round'/>"),
    }
    틀 = 표.get(갈래, "<ellipse cx='320' cy='{y}' rx='24' ry='17' fill='{c}'/>")
    return 틀.format(y=y, y1=y - 19, y34=y - 34, y28=y - 28,
                     yp4=y + 4, yp12=y + 12, yp16=y + 16, yp22=y + 22,
                     ym4=y - 4, ym6=y - 6, c=짚, d=짙은짚)


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
        '<figure class="cg-art">\n'
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
        '<figcaption>%s — %s</figcaption>\n'
        '</figure>'
        % (조사(글(이름), '가'), 모래, 짙은모래, 깊이표, 몸, 물글씨,
           글(이름), 설명))


# ── ③ 물때 곡선 — 간조 앞뒤가 왜 중요한가 ─────────────────
def 물때그림(누구='해루질'):
    """간조 앞뒤 1~2시간이 핵심임을 곡선으로 보입니다 (640×260)."""
    return (
        '<figure class="cg-art">\n'
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
        '<figcaption>물때 곡선 — 간조 앞뒤 1~2시간이 핵심입니다. '
        '물이 들어오기 시작하면 바로 나오세요. 날짜별 간조 시각은 '
        '권역 쪽 물때표에서 볼 수 있습니다.</figcaption>\n'
        '</figure>'
        % (글(누구), 물빛, 짚, 짙은짚, 물글씨, 물글씨, 붉음, 붉음,
           풀빛, 풀빛, 풀빛, 붉음, 붉음, 물글씨))


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
            % (돌, 붉음, 풀빛, 풀빛, 붉음, 붉음, 붉음))
    return (
        '<figure class="cg-art">\n'
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
        '<figcaption>%s — %s</figcaption>\n'
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
    'jighead': (
        "<path d='M300 70 L330 150' stroke='{선}' stroke-width='2'/>"
        "<circle cx='332' cy='156' r='11' fill='{짚}'/>"
        "<path d='M332 156 q26 6 44 -6 q-10 16 -30 20' fill='#7aa27f'/>"
        "<g stroke='{바늘}' stroke-width='2.4' fill='none'>"
        "<path d='M340 164 q6 16 -6 20 q-10 4 -12 -6'/></g>"
        "<text x='268' y='160' font-size='14' fill='{짙짚}'"
        " text-anchor='end'>지그헤드</text>"
        "<text x='384' y='176' font-size='14' fill='{선}'>웜</text>"),
    'egi': (
        "<path d='M300 66 L336 140' stroke='{선}' stroke-width='2'/>"
        "<g transform='rotate(24 340 160)'>"
        "<ellipse cx='340' cy='160' rx='18' ry='34' fill='{짚}'/>"
        "<path d='M340 126 l14 -12 -6 16z' fill='{짙짚}'/>"
        "<g stroke='{바늘}' stroke-width='2.2' fill='none'>"
        "<path d='M330 196 q-6 12 4 14'/>"
        "<path d='M350 196 q6 12 -4 14'/></g></g>"
        "<text x='286' y='154' font-size='14' fill='{짙짚}'"
        " text-anchor='end'>에기</text>"
        "<text x='384' y='206' font-size='14' fill='{선}'>바늘(간)</text>"),
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
        '<figure class="cg-art">\n'
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
        '<figcaption>%s — %s</figcaption>\n'
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
