/* =====================================================================
   바닷가 명소 카드 그림 — 사진이 아직 없는 카드에만 벡터 그림을 넣습니다 (2026-09-19)

   전국 확대 권역 25곳은 아직 공공누리·CC 사진을 못 구해 명소 카드가 글자만 있었습니다.
   제주 사진 명소 카드(tools/photo-art.ps1 의 PaScene)와 같은 방식으로, 명소 이름에서
   장면을 골라 그림을 그려 넣습니다.

   - 사진이 있는 카드(.spot-photo)는 건드리지 않습니다. data/coast-photos.json 에 사진이
     들어와 build-coast.ps1 을 다시 돌리면 그림은 저절로 사라지고 사진이 자리를 잡습니다.
   - 사진처럼 보이면 안 되므로 그림마다 '그림' 이라고 적힌 딱지를 붙이고, 읽어 주는
     기기에도 '안내 그림' 으로 알립니다. 없는 사진을 있는 것처럼 보이게 하지 않습니다.
   ===================================================================== */
(function () {
  // 한국어 쪽은 #spotGrid, 중국어 쪽은 .spot-grid 입니다.
  var grid = document.getElementById('spotGrid') || document.querySelector('.spot-grid');
  if (!grid) return;
  var zh = (document.documentElement.getAttribute('lang') || '').indexOf('zh') === 0;

  var SKY = {
    sunset:  ['#3B4A6B', '#C9736A', '#F2B65C', '#E98A4F'],
    sunrise: ['#2E4F6E', '#9FB6D0', '#F6D39A', '#F2B65C'],
    day:     ['#4E9BC0', '#9FD0E6', '#E8F4F8', '#FFF4D6']
  };

  // 앞자리는 한국어, 뒤는 중국어 쪽 카드에서도 같은 장면이 나오도록 함께 넣었습니다.
  function scene(text, name, id) {
    var t = text;
    var nm = name;
    var time = /일몰|노을|석양|낙조|日落|晚霞/.test(t) ? 'sunset'
             : /일출|해돋이|日出/.test(t) ? 'sunrise' : 'day';
    var c = SKY[time];
    var sunY = time === 'day' ? 46 : 96;
    var sea = time === 'sunset' ? '#6A6F8E' : time === 'sunrise' ? '#5C84A0' : '#3E9BB0';
    var base =
      "<defs><linearGradient id='g" + id + "' x1='0' y1='0' x2='0' y2='1'>" +
      "<stop offset='0' stop-color='" + c[0] + "'/><stop offset='.6' stop-color='" + c[1] + "'/>" +
      "<stop offset='1' stop-color='" + c[2] + "'/></linearGradient></defs>" +
      "<rect width='320' height='200' fill='url(#g" + id + ")'/>" +
      "<circle cx='236' cy='" + sunY + "' r='20' fill='" + c[3] + "' opacity='.9'/>" +
      "<rect y='120' width='320' height='80' fill='" + sea + "'/>" +
      "<path d='M0 132 q20 -5 40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0 t40 0' fill='none' " +
      "stroke='#fff' stroke-opacity='.35' stroke-width='1.6'/>";

    var fg;
    if (/등대|灯塔/.test(t)) {
      var col = /빨강|빨간|말|红/.test(t) ? '#D9534F' : '#FFFFFF';
      fg = "<path d='M40 150 h140 v50 H40z' fill='#5f6a70'/>" +
           "<path d='M150 150 l6 -70 h16 l6 70z' fill='" + col + "'/>" +
           "<rect x='154' y='70' width='24' height='12' fill='#2F5D57'/>" +
           "<path d='M150 110 h28' stroke='#fff' stroke-width='5' opacity='.8'/>";
    } else if (/주상절리|절벽|기암|바위|촛대|柱状节理|悬崖|岩/.test(t)) {
      fg = "<path d='M0 200 V96 l20 -10 v-10 l22 -6 v10 l20 -4 v14 l22 -8 v118z' fill='#3b4145'/>" +
           "<g stroke='#565e63' stroke-width='2'><path d='M20 86 V200M42 80 V200M62 82 V200'/></g>" +
           "<path d='M200 200 q20 -80 50 -86 q10 -30 22 -2 q30 10 48 88z' fill='#4a4f4a'/>";
    } else if (/케이블카|스카이|索道|缆车/.test(t)) {
      fg = "<path d='M0 200 V150 l70 -40 v90z' fill='#3F6B4E'/>" +
           "<path d='M320 200 V140 l-70 -34 v94z' fill='#4E7D5C'/>" +
           "<path d='M60 104 L258 96' stroke='#6b747a' stroke-width='2.5'/>" +
           "<rect x='146' y='100' width='34' height='22' rx='5' fill='#E5A94F'/>" +
           "<path d='M163 100 v-8' stroke='#6b747a' stroke-width='2.5'/>";
    } else if (/방파제|항|포구|어항|부두|선착장|码头|港/.test(t)) {
      fg = "<path d='M0 176 h210 v24 H0z' fill='#6b747a'/>" +
           "<path d='M210 176 h40 v10 h-40z' fill='#8d959a'/>" +
           "<path d='M246 176 q14 -46 30 -46 q16 0 30 46z' fill='#E9EDEF'/>" +
           "<path d='M262 130 h28' stroke='#D9534F' stroke-width='6'/>" +
           "<path d='M60 176 v-30 h44 l-44 30z' fill='#fff' opacity='.85'/>";
    } else if (/갯벌|해루질|조개|滩涂|赶海/.test(t)) {
      fg = "<rect y='150' width='320' height='50' fill='#9A8F76'/>" +
           "<g stroke='#7d735d' stroke-width='2' fill='none'>" +
           "<path d='M0 162 q40 8 80 0 t80 0 t80 0 t80 0'/>" +
           "<path d='M0 178 q40 8 80 0 t80 0 t80 0 t80 0'/></g>" +
           "<g fill='#6f6753'><circle cx='70' cy='186' r='4'/><circle cx='150' cy='192' r='3'/>" +
           "<circle cx='232' cy='184' r='4'/></g>";
    } else if (/다랭이|논|계단식|마을|벽화|가옥|시장|村|市场|壁画/.test(t)) {
      fg = "<path d='M0 200 V140 q80 -18 160 -6 q80 12 160 -4 v70z' fill='#6E8C63'/>" +
           "<g stroke='#4E6B58' stroke-width='2' fill='none'>" +
           "<path d='M0 152 q80 -14 160 -4 q80 10 160 -2'/>" +
           "<path d='M0 168 q80 -12 160 -3 q80 9 160 -2'/>" +
           "<path d='M0 184 q80 -10 160 -2 q80 8 160 -2'/></g>" +
           "<g fill='#EDE3C8'><path d='M40 138 h26 v16 H40z'/><path d='M36 138 l17 -12 l17 12z' fill='#B4674B'/>" +
           "<path d='M240 134 h24 v16 h-24z'/><path d='M236 134 l16 -11 l16 11z' fill='#B4674B'/></g>";
    } else if (/절$|사$|사찰|보리암|보문사|낙산사|암자|寺|庵/.test(nm)) {
      fg = "<path d='M60 130 q30 -74 100 -74 q70 0 100 74z' fill='#3F6B4E' opacity='.9'/>" +
           "<path d='M110 176 h100 v24 H110z' fill='#C9A06A'/>" +
           "<path d='M96 176 l64 -30 l64 30z' fill='#8E5B3A'/>" +
           "<path d='M150 176 h20 v24 h-20z' fill='#7A4A2E'/>";
    } else if (/성$|보$|진$|요새|성곽|城|堡/.test(nm)) {
      fg = "<path d='M40 200 V132 h30 v-12 h24 v12 h30 v-12 h24 v12 h30 v-12 h24 v12 h30 v68z' fill='#7C7468'/>" +
           "<g fill='#5f5950'><path d='M96 160 h22 v40 h-22z'/><path d='M180 160 h22 v40 h-22z'/></g>" +
           "<path d='M0 200 q70 -16 150 -6 q80 10 170 -2 v8z' fill='#6E8C63'/>";
    } else if (/수목원|공원|숲|솔밭|방조어부림|공원|林|园/.test(t)) {
      fg = "<path d='M0 200 V158 q80 -14 160 -4 q80 10 160 -2 v48z' fill='#4E7D5C'/>" +
           "<g fill='#2E5039'><path d='M50 158 q14 -44 28 0z'/><path d='M96 158 q16 -52 32 0z'/>" +
           "<path d='M210 158 q14 -46 28 0z'/><path d='M254 158 q12 -38 24 0z'/></g>";
    } else if (/섬|도$|島|岛/.test(nm) || /섬/.test(t)) {
      fg = "<path d='M180 124 q40 -40 90 -4 q20 -8 40 4z' fill='#3F6B4E'/>" +
           "<path d='M0 170 q60 -30 150 -10 q60 10 170 10 v30 H0z' fill='#E9DDBE'/>";
    } else if (/산|봉|악$|언덕|오름|山|峰/.test(nm) || /전망|언덕|观景/.test(t)) {
      fg = "<path d='M60 130 q30 -80 100 -80 q70 0 100 80z' fill='#3F6B4E'/>" +
           "<path d='M126 58 q34 -10 68 0' fill='none' stroke='#2E5039' stroke-width='3'/>" +
           "<path d='M0 140 q60 -14 120 0 v60 H0z' fill='#4E7D5C' opacity='.9'/>";
    } else {
      // 해수욕장·해변을 비롯한 나머지 — 모래사장과 곶
      fg = "<path d='M0 152 q80 -22 160 -4 q80 16 160 -4 v56 H0z' fill='#EDE3C8'/>" +
           "<path d='M230 124 q20 -24 50 -4 z' fill='#3F6B4E' opacity='.8'/>" +
           "<g fill='#fff' opacity='.7'><circle cx='60' cy='176' r='3'/><circle cx='104' cy='186' r='2.5'/>" +
           "<circle cx='186' cy='180' r='3'/></g>";
    }
    return base + fg;
  }

  var n = 0;
  [].forEach.call(grid.querySelectorAll('.spot-card'), function (card) {
    if (card.querySelector('.spot-photo')) return;      // 사진이 이미 있으면 그대로 둡니다
    var h3 = card.querySelector('h3');
    if (!h3) return;
    var kind = card.querySelector('.spot-kind');
    var name = h3.textContent.trim();
    // 중국어 쪽 카드에는 한국어 이름이 함께 적혀 있습니다. 그걸 쓰면 같은 명소에
    // 한국어·중국어 쪽 모두 같은 그림이 나옵니다.
    var ko = card.querySelector('.zr-ko b');
    var koName = ko ? ko.textContent.trim() : name;   // 끝 글자 규칙(섬·산·절)은 한국어 이름에 겁니다
    var text = (ko ? koName + ' ' : '') + name + ' ' + (kind ? kind.textContent.trim() : '');
    n++;
    var label = zh ? '示意图' : '그림';
    var fig = document.createElement('figure');
    fig.className = 'spot-photo sp-art';
    fig.innerHTML =
      "<svg viewBox='0 0 320 200' preserveAspectRatio='xMidYMid slice' role='img' aria-label='" +
      name.replace(/'/g, '') + ' ' + (zh ? '示意图' : '안내 그림') + "' xmlns='http://www.w3.org/2000/svg'>" +
      scene(text, koName, 'sa' + n) +
      '</svg><figcaption>' + label + '</figcaption>';
    card.insertBefore(fig, card.firstChild);
  });
})();
