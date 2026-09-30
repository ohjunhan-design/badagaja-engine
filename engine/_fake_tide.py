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
    그래서 물차가 **큰 쪽**(서해 군산 · 6.6m)으로 만듭니다 —
    숫자가 길어 칸을 가장 많이 밀어내는 경우입니다.
"""

# 진짜 api/marine.php?kind=series 가 주는 꼴을 그대로 흉내 냅니다.
# 서해 군산 기준 — 물차가 커서 숫자가 깁니다(654cm · ▲+660).
가짜물때 = r'''
(function () {
  'use strict';
  var 원래fetch = window.fetch;

  function 시계열() {
    var pts = [];
    for (var m = 0; m <= 1440; m += 10) {
      // 반나절 두 번 — 실제 조석과 같은 꼴
      var v = 375 + 330 * Math.cos((m - 294) / 745 * Math.PI * 2);
      pts.push([m, Math.round(v)]);
    }
    return pts;
  }

  window.fetch = function (주소) {
    var u = String(주소 || '');
    if (u.indexOf('marine.php') >= 0 && u.indexOf('kind=series') >= 0) {
      return Promise.resolve({
        ok: true,
        json: function () {
          return Promise.resolve({
            ok: true,
            station: '군산',
            source: '국립해양조사원 조석예보(시계열)',
            sunrise: 386, sunset: 1088,
            series: 시계열(),
            events: [
              { type: 'high', min: 294, level: 654 },
              { type: 'low', min: 698, level: 45 },
              { type: 'high', min: 1046, level: 705 }
            ]
          });
        }
      });
    }
    if (u.indexOf('tide-cache.php') >= 0) {
      return Promise.resolve({
        ok: true,
        json: function () { return Promise.resolve({ ok: true, days: [] }); }
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
