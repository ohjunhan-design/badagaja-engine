# -*- coding: utf-8 -*-
"""시험용 **가짜 물때** — 한 곳에서만 둡니다.

★ 2026-10-01 — 이것이 없어서 **주인이 먼저 찾으셨습니다.**

    주인이 「화면넘침」이라며 화면을 보내 주셨습니다.
    물높이 그래프가 **1490px** 로 커져 문서를 통째로 넓히고
    있었습니다. `.tide-graph svg{width:100%}` 가 빠져 있었습니다.

    그런데 `check_mobile.py` 는 **「넘치는 것이 없습니다」** 했습니다.
    검사가 인터넷을 막고 재기 때문입니다 —
    물때 숫자를 못 불러오니 **그래프가 아예 안 그려진 쪽**을
    재고 있었습니다. 손님이 보는 화면과 다른 것을 잰 것입니다.

★ 인터넷을 막는 것 자체는 **옳습니다**
    바깥이 느린 날 검사가 실패하면 그것은 시험이 아닙니다.
    그래서 여는 대신 **가짜를 넣습니다.**
    · 바깥에 안 흔들립니다
    · 숫자가 늘 같아 결과가 흔들리지 않습니다
    · 그러면서 **실제와 같은 모습**을 잽니다

★ 가짜는 진짜를 **넉넉히** 흉내 내야 합니다
    좁게 만들면 고칠수록 검사가 시끄러워집니다
    (`_fake_coupang.py` 에서 겪은 일입니다).
    그래서 **서해 군산**(물차 6.6m)으로 만듭니다 —
    숫자가 길어 칸을 가장 많이 밀어내는 경우입니다.

★ 응답 꼴은 **진짜를 받아 보고** 맞췄습니다 (2026-10-01)
    `api/marine.php?kind=series&region=gunsan&day=0` 이 주는 것 —
      ok · region · date · station · code · interval · unit ·
      points(["00:00", 120] 꼴 144개) · source
    처음에는 `series`·`events` 라는 이름으로 지어냈다가
    **그래프가 한 번도 안 그려졌습니다.** 짐작하면 헛돕니다.
"""

가짜물때 = r'''
(function () {
  'use strict';
  var 원래fetch = window.fetch;

  function 점들() {
    // 10분 간격 144개 — 진짜와 같은 개수·꼴 ["HH:MM", cm]
    var out = [];
    for (var i = 0; i < 144; i++) {
      var m = i * 10;
      var hh = String(Math.floor(m / 60)).padStart(2, '0');
      var mm = String(m % 60).padStart(2, '0');
      // 서해 군산 — 물차가 큽니다 (45~705cm)
      var v = 375 + 330 * Math.cos((m - 294) / 745 * Math.PI * 2);
      out.push([hh + ':' + mm, Math.round(v)]);
    }
    return out;
  }

  window.fetch = function (주소) {
    var u = String(주소 || '');
    if (u.indexOf('marine.php') >= 0 && u.indexOf('kind=series') >= 0) {
      return Promise.resolve({
        ok: true,
        json: function () {
          return Promise.resolve({
            ok: true,
            region: 'gunsan',
            date: '2026-10-01',
            station: '군산',
            code: 'DT_0018',
            interval: 10,
            unit: 'cm',
            points: 점들(),
            source: '국립해양조사원 조석예보(시계열)'
          });
        }
      });
    }
    if (u.indexOf('tide-cache.php') >= 0) {
      return Promise.resolve({
        ok: true,
        json: function () {
          return Promise.resolve({
            ok: true,
            days: [{
              // ★ type 은 **한글**입니다 (2026-10-01 화면에서 잡음)
              //   tide-graph.js 가 `ev.type === '만조'` 로 봅니다.
              //   영어 'high' 를 주었더니 꿉대기까지 「간조」로
              //   나왔습니다. **가짜가 진짜를 제대로 훌내야** 합니다.
              events: [
                { type: '만조', time: '04:54', level: 654 },
                { type: '간조', time: '11:38', level: 45 },
                { type: '만조', time: '17:26', level: 705 }
              ]
            }]
          });
        }
      });
    }
    return 원래fetch ? 원래fetch.apply(window, arguments)
                     : Promise.reject(new Error('fetch 없음'));
  };
})();
'''


def 심을글():
    """쪽에 심을 <script> 한 덩이를 돌려줍니다."""
    return '<script>' + 가짜물때 + '</script>'
