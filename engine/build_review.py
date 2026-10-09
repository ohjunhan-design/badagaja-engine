# -*- coding: utf-8 -*-
"""AI 검수 전용 읽기 뷰 — `/stats-review/index.html` (2026-10-10 #9 P0)

★ 왜 있나

  최종결정자만 보는 잠금 화면이면 총감독도 감독실도 통계를
  **눈으로 검수할 수 없습니다.** 「고쳤습니다」라고 말해도
  숫자가 든 진짜 화면은 아무도 못 봅니다.

★ 어떤 길을 골랐나 — **후보 B (완전 비식별 집계 스냅샷)**

  총감독이 「ChatGPT 조회 도구는 쿠키·비밀 헤더를 못 싣는
  경우가 많다」고 짚었습니다. 권한으로 막는 후보 A 는 **열리지
  않을 수** 있고, 열리지 않는 화면은 검수에 쓸모가 없습니다.
  그래서 **담는 것 자체를 집계값으로 한정**합니다.
  `noindex` 는 접근통제가 아니라는 말씀 그대로, 주소를 비밀로
  믿지 않습니다.

★ 세 가지를 지킵니다

  ① **없는 것은 안 담습니다.** IP·원시 UA·검색어·연락처·
     토큰·쿠키·열쇠 값·원본 로그·개별 방문자 줄은 자료 구조에
     자리조차 두지 않습니다.
  ② **「없음」과 「0」을 가릅니다.** 세었고 0 인 날, 아예 못 받은
     날, 측정하지 않는 항목을 화면에서 다르게 보입니다.
  ③ **자료가 없으면 쪽을 안 만듭니다.** 가짜 숫자가 생기지
     않습니다.

쓰는 법
    python engine/build_review.py                 진짜 스냅샷으로
    python engine/build_review.py --모의          모의 자료로
"""
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
자료칸 = os.path.join(ROOT, 'data', 'raw')
진짜길 = os.path.join(자료칸, 'stats-review.json')
모의길 = os.path.join(자료칸, 'stats-review.sample.json')
낼길 = os.path.join(NEW, 'stats-review', 'index.html')

KST = timezone(timedelta(hours=9))

# ★ **담으면 안 되는 이름들** — 스냅샷에 섞여 들면 막습니다.
#   「안 담기로 했다」를 말로 두지 않고 **기계가 봅니다.**
못담을것 = ('ip', 'IP', 'ua', 'userAgent', 'user_agent', 'referer',
            'query', '검색어', '연락처', 'email', '메일', 'token',
            '토큰', 'cookie', '쿠키', 'key', '열쇠', 'secret',
            '방문자목록', 'visitors', 'raw', '원본')


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def 수(n):
    try:
        return '{:,}'.format(int(n))
    except Exception:                                   # noqa: BLE001
        return '—'


class 못담을것들어있음(Exception):
    """스냅샷에 개인정보 꼴이 섞였습니다 — 쪽을 안 만듭니다"""


def 몸수색(것, 길=''):
    """자료 속에 **담으면 안 되는 이름**이 있는지 샅샅이 봅니다"""
    찾음 = []
    if isinstance(것, dict):
        for k, v in 것.items():
            if any(x.lower() == str(k).lower() for x in 못담을것):
                찾음.append('%s/%s' % (길, k))
            찾음 += 몸수색(v, '%s/%s' % (길, k))
    elif isinstance(것, list):
        for i, v in enumerate(것):
            찾음 += 몸수색(v, '%s[%d]' % (길, i))
    return 찾음


def 자료읽기(모의):
    길 = 모의길 if 모의 else 진짜길
    if not os.path.exists(길):
        return None, 길
    것 = json.load(io.open(길, encoding='utf-8'))
    샌것 = 몸수색(것)
    if 샌것:
        raise 못담을것들어있음(
            '스냅샷에 담으면 안 되는 것이 %d곳 있습니다 — %s'
            % (len(샌것), ', '.join(샌것[:5])))
    return 것, 길


def 기간합(날짜별, 날수, 오늘):
    """최근 n 일을 더합니다. **못 받은 날을 따로 셉니다.**"""
    더함, 못받음 = 0, []
    for i in range(날수):
        날 = (오늘 - timedelta(days=i)).strftime('%Y-%m-%d')
        v = 날짜별.get(날)
        if v is None:
            못받음.append(날)
        else:
            더함 += int(v.get('방문') or 0)
    return 더함, 못받음


def 카드(이름, 값, 뜻, 못받음=0):
    덧 = ''
    if 못받음:
        덧 = ('<span class="rv-card__miss">%d일은 못 받았습니다</span>'
              % 못받음)
    return ('<article class="rv-card">'
            '<span class="rv-card__t">%s</span>'
            '<strong class="rv-card__v">%s</strong>%s'
            '<span class="rv-card__d">%s</span></article>'
            % (esc(이름), esc(값), 덧, esc(뜻)))


def 막대줄(이름, 값, 모두):
    몫 = round(값 * 100.0 / 모두) if 모두 else 0
    return ('<div class="rv-bar"><span class="rv-bar__t">%s</span>'
            '<span class="rv-bar__g"><i style="width:%d%%"></i></span>'
            '<span class="rv-bar__n">%d%%</span>'
            '<span class="rv-bar__c">%s</span></div>'
            % (esc(이름), 몫, 몫, 수(값)))


def 그리기(d):
    만든때 = d.get('만든때') or ''
    try:
        그때 = datetime.fromisoformat(만든때)
    except Exception:                                   # noqa: BLE001
        그때 = None
    이제 = datetime.now(KST)
    지난날 = (이제 - 그때).days if 그때 else None
    낡음 = (지난날 is not None and 지난날 >= 7)

    날짜별 = d.get('날짜별') or {}
    있는날 = sorted(날짜별)
    오늘키 = 있는날[-1] if 있는날 else None
    오늘값 = 날짜별.get(오늘키) or {}
    끝날 = (datetime.strptime(오늘키, '%Y-%m-%d').date()
            if 오늘키 else 이제.date())

    칠일, 칠못 = 기간합(날짜별, 7, 끝날)
    삼십, 삼십못 = 기간합(날짜별, 30, 끝날)
    달합 = sum(int(v.get('방문') or 0) for k, v in 날짜별.items()
               if k.startswith(d.get('달') or ''))

    유입 = d.get('유입') or {}
    유모두 = sum(int(v or 0) for v in 유입.values())

    정 = d.get('정의') or {}
    카드들 = ''.join([
        카드('그날 방문', 수(오늘값.get('방문')),
             '%s · %s' % (오늘키 or '—', 정.get('방문', ''))),
        카드('최근 7일', 수(칠일),
             정.get('방문', ''), len(칠못)),
        카드('최근 30일', 수(삼십),
             '앞 달까지 이어 더했습니다', len(삼십못)),
        카드('이 달 합', 수(달합),
             '%s 1일부터' % (d.get('달') or '—')),
    ])

    가장큰 = max([int(v.get('조회') or 0) for v in 날짜별.values()] or [1])
    막대 = ''
    for 날 in 있는날:
        v = 날짜별[날]
        조 = int(v.get('조회') or 0)
        높 = round(조 * 100.0 / 가장큰) if 가장큰 else 0
        빈 = ' is-zero' if 조 == 0 else ''
        막대 += ('<div class="rv-day%s" title="%s · 방문 %s · 조회 %s">'
                 '<i style="height:%d%%"></i><b>%s</b></div>'
                 % (빈, 날, 수(v.get('방문')), 수(조), 높, 날[-2:]))

    유입칸 = ''.join(막대줄(k, int(v or 0), 유모두)
                     for k, v in 유입.items()) or \
        '<p class="rv-none">유입 기록이 없습니다</p>'

    인기 = ''.join(
        '<tr><td>%s</td><td class="rv-n">%s</td></tr>'
        % (esc(x.get('주소')), 수(x.get('조회')))
        for x in (d.get('인기쪽') or []))

    못받 = d.get('못받음') or []
    안함 = d.get('측정안함') or []
    수집 = d.get('수집') or {}

    빈날 = [k for k, v in 날짜별.items() if int(v.get('방문') or 0) == 0]

    알림 = []
    if d.get('모의자료'):
        알림.append('<p class="rv-warn rv-warn--mock">이 쪽은 <b>모의 '
                    '자료</b>로 그렸습니다. 진짜 숫자가 아닙니다.</p>')
    if 낡음:
        알림.append('<p class="rv-warn rv-warn--old">스냅샷이 <b>%d일</b> '
                    '지났습니다. 새로 만들어 주세요.</p>' % 지난날)

    로봇 = 수집.get('로봇거르기') or '확인되지 않음'
    로봇꼴 = 'rv-state--unknown' if '확인' in 로봇 else 'rv-state--ok'

    return """<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- ★ 검색에 뜨지 않게 합니다. 다만 **noindex 는 접근통제가
     아닙니다** — 그래서 이 쪽에는 집계값만 담았습니다. -->
<meta name="robots" content="noindex,nofollow,noarchive">
<title>방문 집계 — 검수용</title>
<link rel="stylesheet" href="../assets/css/site.css">
<style>
.rv{max-width:960px;margin:0 auto;padding:28px 16px 60px}
.rv h1{margin:0 0 6px;font-size:clamp(22px,2.6vw,30px);font-weight:900;
  letter-spacing:-.03em;color:var(--stats-text,#263432)}
.rv__sub{margin:0 0 18px;font-size:14px;color:var(--stats-muted,#62716E)}
.rv-warn{margin:0 0 12px;padding:12px 15px;border-radius:12px;
  font-size:14px;font-weight:700;line-height:1.6;word-break:keep-all}
.rv-warn--mock{background:#FFF4E0;color:#8A5E14;
  border:1px solid #F0D9A8}
.rv-warn--old{background:#FDECEA;color:#A93E32;border:1px solid #F3C9C3}
.rv-state{display:inline-flex;align-items:center;gap:6px;margin:0 0 16px;
  padding:7px 12px;border-radius:999px;font-size:13px;font-weight:700}
.rv-state--unknown{background:#F1F3F2;color:#5A6865}
.rv-state--ok{background:#E6F0EE;color:#235A53}
.rv-cards{display:grid;
  grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;
  margin:0 0 22px}
.rv-card{display:flex;flex-direction:column;min-height:120px;padding:16px;
  border:1px solid var(--stats-line,#DCE6E3);border-radius:14px;
  background:#fff}
.rv-card__t{font-size:13px;font-weight:700;
  color:var(--stats-muted,#62716E)}
.rv-card__v{margin-top:8px;font-size:28px;font-weight:800;line-height:1;
  letter-spacing:-.02em;color:var(--stats-text,#263432)}
.rv-card__miss{margin-top:7px;font-size:12px;font-weight:800;
  color:var(--stats-danger,#A93E32)}
.rv-card__d{margin-top:auto;padding-top:9px;font-size:11.5px;
  line-height:1.45;color:var(--stats-muted,#62716E);word-break:keep-all}
.rv h2{margin:26px 0 10px;font-size:17px;font-weight:800;
  color:var(--stats-text,#263432)}
.rv-days{display:flex;align-items:flex-end;gap:3px;height:140px;
  padding:12px 10px 0;border:1px solid var(--stats-line,#DCE6E3);
  border-radius:12px;background:#fff;overflow-x:auto}
.rv-day{flex:1 0 14px;display:flex;flex-direction:column;
  align-items:center;justify-content:flex-end;height:100%;gap:4px}
.rv-day i{display:block;width:100%;min-height:2px;border-radius:3px 3px 0 0;
  background:var(--stats-brand,#0F5B59)}
/* ★ **0 인 날**은 빈 날과 다릅니다. 「셌고 0 이었다」를
   한눈에 알도록 **바닥에 또렷한 빗금 칸**을 세웁니다.
   3px 짜리 막대로는 빈 날과 구별이 안 됐습니다. */
.rv-day.is-zero i{min-height:16px;border-radius:3px;
  border:1px dashed #9FB3AF;
  background:repeating-linear-gradient(45deg,
    #DCE6E3,#DCE6E3 3px,#F5F8F7 3px,#F5F8F7 6px)}
.rv-day.is-zero b{color:#8A9B97;font-weight:800}
/* 검수자가 날짜를 읽어야 합니다. 10px 는 작았습니다 */
.rv-day b{font-size:11px;font-weight:700;
  color:var(--stats-muted,#62716E)}
.rv-bar{display:grid;grid-template-columns:72px minmax(0,1fr) 44px 60px;
  align-items:center;gap:10px;margin-bottom:8px}
.rv-bar__t{font-size:13.5px;font-weight:700}
.rv-bar__g{height:14px;border-radius:7px;background:#F1F3F2;overflow:hidden}
.rv-bar__g i{display:block;height:100%;border-radius:7px;
  background:var(--stats-brand,#0F5B59)}
.rv-bar__n{font-size:13px;font-weight:800;text-align:right}
.rv-bar__c{font-size:12px;text-align:right;
  color:var(--stats-muted,#62716E)}
.rv-tbl{width:100%;border-collapse:collapse;border:1px solid
  var(--stats-line,#DCE6E3);border-radius:12px;overflow:hidden;
  background:#fff}
.rv-tbl td{padding:9px 13px;font-size:13.5px;
  border-bottom:1px solid #EEF3F2}
.rv-tbl tr:last-child td{border-bottom:0}
.rv-n{text-align:right;font-variant-numeric:tabular-nums;font-weight:700}
.rv-list{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;
  gap:7px}
.rv-list li{padding:5px 11px;border-radius:999px;background:#F1F3F2;
  font-size:12.5px;font-weight:700;color:#5A6865}
.rv-none{margin:0;padding:16px;text-align:center;font-size:14px;
  color:var(--stats-muted,#62716E)}
.rv-foot{margin-top:30px;padding-top:16px;
  border-top:1px solid var(--stats-line,#DCE6E3);font-size:12.5px;
  line-height:1.7;color:var(--stats-muted,#62716E);word-break:keep-all}
@media (max-width:430px){
  .rv{padding:20px 14px 48px}
  .rv-cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
  .rv-card{min-height:104px;padding:13px}
  .rv-card__v{font-size:23px}
  .rv-bar{grid-template-columns:58px minmax(0,1fr) 38px;gap:8px}
  .rv-bar__c{display:none}
}
</style></head><body>
<main class="rv">
<h1>방문 집계 — 검수용</h1>
<p class="rv__sub">집계값만 담은 <b>읽기 전용</b> 쪽입니다.
  고치거나 지울 수 없고, 개인을 가릴 수 있는 것은 담기지 않습니다.</p>
__알림__
<span class="rv-state __로봇꼴__">로봇 거르기 — __로봇__</span>

<div class="rv-cards">__카드__</div>

<h2>날마다</h2>
<div class="rv-days">__막대__</div>
<p class="rv__sub" style="margin-top:8px">빗금은 <b>세었고 0</b> 인
  날입니다. 아예 빠진 날은 아래에 따로 적었습니다.</p>

<h2>어디서 들어왔나</h2>
__유입__

<h2>많이 본 쪽</h2>
<table class="rv-tbl">__인기__</table>

<h2>못 받은 날</h2>
__못받__

<h2>측정하지 않는 것</h2>
__안함__

<p class="rv-foot">
  스냅샷 기준 __만든때__ (__시간대__) · 수집 원천 __원천__<br>
  담지 않는 것 — IP · 원시 브라우저 정보 · 검색어 · 연락처 ·
  토큰 · 쿠키 · 열쇠 값 · 원본 기록 · 개별 방문자 줄<br>
  이 쪽은 서버로 아무것도 보내지 않습니다. 고치기·지우기 길이
  없습니다.
</p>
</main></body></html>
""".replace('__알림__', ''.join(알림)) \
   .replace('__로봇꼴__', 로봇꼴) \
   .replace('__로봇__', esc(로봇)) \
   .replace('__카드__', 카드들) \
   .replace('__막대__', 막대 or '<p class="rv-none">날짜 기록이 없습니다</p>') \
   .replace('__유입__', 유입칸) \
   .replace('__인기__', 인기 or '<tr><td class="rv-none">없습니다</td></tr>') \
   .replace('__못받__',
            ('<ul class="rv-list">%s</ul>'
             % ''.join('<li>%s</li>' % esc(x) for x in 못받))
            if 못받 else '<p class="rv-none">없습니다</p>') \
   .replace('__안함__',
            ('<ul class="rv-list">%s</ul>'
             % ''.join('<li>%s</li>' % esc(x) for x in 안함))
            if 안함 else '<p class="rv-none">없습니다</p>') \
   .replace('__만든때__', esc(만든때)) \
   .replace('__시간대__', esc(d.get('시간대') or '')) \
   .replace('__원천__', esc(수집.get('원천') or '—'))


def main():
    모의 = '--모의' in sys.argv
    try:
        d, 길 = 자료읽기(모의)
    except 못담을것들어있음 as e:
        print('✗ %s' % e)
        print('  스냅샷에서 그 칸을 빼고 다시 주세요. 쪽을 안 만듭니다.')
        return 1
    if d is None:
        # ★ **자료가 없으면 쪽을 안 만듭니다.** 가짜 숫자를 만들지
        #   않습니다. 있던 쪽이 있으면 치웁니다.
        if os.path.exists(낼길):
            os.remove(낼길)
            print('스냅샷이 없어 옛 쪽을 치웠습니다 — %s' % 낼길)
        else:
            print('스냅샷이 없습니다 (%s) — 쪽을 만들지 않습니다.' % 길)
        return 0
    글 = 그리기(d)
    os.makedirs(os.path.dirname(낼길), exist_ok=True)
    io.open(낼길, 'w', encoding='utf-8', newline='\n').write(글)
    print('만들었습니다 — %s (%s · %.1fKB)'
          % (낼길, '모의 자료' if d.get('모의자료') else '진짜 스냅샷',
             len(글.encode('utf-8')) / 1024.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
