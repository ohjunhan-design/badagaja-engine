# -*- coding: utf-8 -*-
"""시험용 **가짜 쿠팡** — 한 곳에서만 둡니다.

★ 2026-09-30 — 가짜가 **두 곳에 따로** 있어서 탈이 났습니다

    check_ads.py 와 check_console.py 가 저마다 가짜 쿠팡을 갖고
    있었습니다. 둘 다 `getElementById(o.container)` 만 했습니다.

    그런데 진짜 쿠팡 g.js 는 **container 에 요소**를 기대합니다
    (주인이 첫번째도전 코드를 짚어 주셔서 알았습니다).
    진짜 쪽을 요소로 고치자마자 **가짜 둘이 동시에 눈이 멀어**
    「광고를 넣어도 안 뜬다」고 14건을 냈습니다.
    **진짜가 고쳐진 순간 가짜가 틀린 소리를 한 것입니다.**

    가짜는 진짜를 흉내 내야 합니다. 진짜보다 좁으면
    고칠수록 검사가 더 시끄러워집니다.
    그래서 **한 곳에 두고 둘이 함께 씁니다** (계약-01 의 뜻).

왜 가짜를 쓰나
    진짜 쿠팡에 기대면 쿠팡이 느린 날 검사가 실패합니다.
    광고가 실제로 오는지가 아니라 **왔을 때 쪽이 멀쩡한지**를
    재는 것이므로, 정해진 크기의 네모를 넣는 편이 낫습니다.
"""

# container 는 **요소로도, 아이디 글자로도** 옵니다.
# 진짜 g.js 는 요소를 받지만, 옛 코드가 글자를 넘길 수도 있으므로
# 둘 다 받아 줍니다 — 가짜가 진짜보다 좁아선 안 됩니다.
가짜쿠팡 = r"""
window.PartnersCoupang = {
  G: function (o) {
    var 상자 = (o.container && o.container.nodeType === 1)
             ? o.container
             : document.getElementById(o.container);
    if (!상자) return;
    var f = document.createElement('iframe');
    f.width = o.width; f.height = o.height;
    f.style.border = '0'; f.style.display = 'block';
    f.setAttribute('title', '시험용 가짜 광고');
    f.src = 'data:text/html,<body style="margin:0;background:#DDD"></body>';
    상자.appendChild(f);
  }
};
"""
