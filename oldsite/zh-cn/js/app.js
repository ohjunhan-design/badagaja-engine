(function(){
  var REGION = document.body.getAttribute('data-region') || 'boseong';
  var DAY_NAMES = ['日','一','二','三','四','五','六'];
  var RAD = Math.PI / 180;
  var SYNODIC = 29.530588853;   // 삭망월(달이 같은 모양으로 돌아오는 주기)

  // 15개 물때 이름 — 서남해에서 쓰는 7물때식.
  // 7물(한사리)에 물이 가장 많이 빠지고, 15물(한조금)에 가장 적게 빠집니다.
  var MULDAE_NAMES = ['第1水','第2水','第3水','第4水','第5水','第6水','第7水','第8水','第9水','第10水','第11水','第12水','第13水','第14水','第15水'];

  // 권역별 대표 좌표 — 일출·일몰 계산용. 없으면 보성 좌표를 씁니다.
  var COORDS = {
    boseong:    [34.72, 127.13],  // 보성(율포항)
    sinan:      [34.99, 126.15],  // 신안(증도)
    muan:       [35.05, 126.31],  // 무안(톱머리항)
    mokpo:      [34.78, 126.38],  // 목포(목포항)
    yeonggwang: [35.32, 126.42],  // 영광(백수해안)
    hampyeong:  [35.10, 126.44],  // 함평(돌머리)
    jindo:      [34.42, 126.35],  // 진도(신비의 바닷길)
    haenam:     [34.30, 126.52],  // 해남(땅끝)
    wando:      [34.31, 126.75],  // 완도(완도항)
    gangjin:    [34.55, 126.72],  // 강진(가우도)
    jangheung:  [34.55, 126.94],  // 장흥(수문항)
    goheung:    [34.51, 127.28],  // 고흥(녹동항)
    yeosu:      [34.74, 127.75],  // 여수(돌산대교)
    suncheon:   [34.86, 127.49],  // 순천(순천만)
    gwangyang:  [34.95, 127.76],  // 광양(망덕포구)
    jejusi:     [33.52, 126.53],  // 제주시내(제주항)
    aewol:      [33.46, 126.31],  // 애월·한림(애월항)
    jocheon:    [33.54, 126.67],  // 조천·구좌(함덕)
    seongsan:   [33.46, 126.93],  // 성산·표선(성산항)
    seogwipo:   [33.24, 126.56],  // 서귀포·중문(서귀포항)
    daejeong:   [33.21, 126.25],  // 대정·안덕(모슬포항)
    chuja:      [33.96, 126.30]   // 추자도
  };
  var IS_JEJU = /^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(REGION);
  // 전국 확대 권역(충남·전북 등)은 한국어 쪽과 같게 좌표를 페이지에서 받고, 날씨도 좌표로 찾는 쪽을 씁니다.
  var IS_COAST = document.body.getAttribute('data-coast') === '1';
  if (IS_COAST) {
    var _la = parseFloat(document.body.getAttribute('data-lat')), _ln = parseFloat(document.body.getAttribute('data-lng'));
    if (!isNaN(_la) && !isNaN(_ln)) COORDS[REGION] = [_la, _ln];
  }

  /* ---------- 달·음력 ----------
     달의 황경에서 태양의 황경을 뺀 값(위상각)으로 달 나이를 구합니다.
     평균 삭망월만 쓰는 방식보다 정확해 실제 음력과 대개 하루 안쪽으로 맞습니다. */
  function moonAge(ms){
    var d = (ms - Date.UTC(2000, 0, 1, 12, 0, 0)) / 86400000;
    var M = 357.5291 + 0.98560028 * d;
    var L = 280.459 + 0.98564736 * d;
    var lsun = L + 1.915 * Math.sin(M * RAD) + 0.020 * Math.sin(2 * M * RAD);
    var Lm = 218.316 + 13.176396 * d;
    var Mm = 134.963 + 13.064993 * d;
    var lmoon = Lm + 6.289 * Math.sin(Mm * RAD);
    var phase = ((lmoon - lsun) % 360 + 360) % 360;
    return phase / 360 * SYNODIC;
  }

  function dayStart(ms){ var d = new Date(ms); d.setHours(0,0,0,0); return d.getTime(); }

  // 알려진 삭(달이 완전히 사라지는 순간) 하나를 기준으로 삼습니다 — 2000-01-06 18:14 UTC
  var REF_NEW_MOON = Date.UTC(2000, 0, 6, 18, 14, 0);

  // moonAge가 0이 되는 지점까지 되짚어 삭 시각을 정밀화합니다.
  function refineNewMoon(t){
    for (var i = 0; i < 4; i++){
      var e = moonAge(t);
      if (e > SYNODIC / 2) e -= SYNODIC;
      t -= e * 86400000;
    }
    return t;
  }

  // k번째 삭 시각. 같은 달 안에서는 어느 날에 물어봐도 항상 같은 값이 나옵니다
  // (날짜마다 다시 계산하면 자정 경계에서 음력이 하루씩 건너뛰는 문제가 생깁니다).
  function newMoonAt(k){
    return refineNewMoon(REF_NEW_MOON + k * SYNODIC * 86400000);
  }

  // 음력 며칠인지. 삭이 든 날을 1일로 셉니다.
  function lunarDay(date){
    var today = dayStart(date.getTime());
    var k = Math.floor((today + 43200000 - REF_NEW_MOON) / (SYNODIC * 86400000));
    var nm = newMoonAt(k);
    if (dayStart(nm) > today) nm = newMoonAt(k - 1);
    if (dayStart(newMoonAt(k + 1)) <= today) nm = newMoonAt(k + 1);
    return Math.round((today - dayStart(nm)) / 86400000) + 1;
  }

  // 물때 번호(7물때식) — 음력 8일·23일이 조금, 15일·30일이 사리가 되도록 맞춘 식입니다.
  function calcMuldae(date){
    var m = (lunarDay(date) + 7) % 15;
    return m === 0 ? 15 : m;
  }

  // 물이 얼마나 많이 빠지는지 0~100. 7물에서 최대, 15물에서 최소.
  function calcIntensity(muldae){
    return Math.round((Math.cos((muldae - 7) * (2 * Math.PI / 15)) + 1) / 2 * 100);
  }

  // 음력 날짜(八月十四) — 중국어판은 물때 번호 대신 음력으로 표기
  function lunarText(date){
    var CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
    function dayCn(n){ return n <= 10 ? '初' + CN[n] : n < 20 ? '十' + CN[n - 10] : n === 20 ? '二十' : n < 30 ? '廿' + CN[n - 20] : '三十'; }
    try {
      var mo = '', dy = '';
      new Intl.DateTimeFormat('zh-CN-u-ca-chinese', { month: 'long', day: 'numeric' }).formatToParts(date).forEach(function(p){ if (p.type === 'month') mo = p.value; if (p.type === 'day') dy = p.value; });
      var n = parseInt(dy, 10);
      return mo + (isNaN(n) ? dy : dayCn(n));
    } catch (e) { return ''; }
  }

  function tideLabel(intensity){
    if (intensity >= 68) return { text: '大潮', cls: 'spring' };
    if (intensity <= 32) return { text: '小潮', cls: 'neap' };
    return { text: '中潮', cls: 'mid' };
  }

  /* ---------- 일출·일몰 ---------- */
  function sunTimes(date, lat, lng){
    var J2000 = 2451545, J1970 = 2440588;
    var lw = -lng * RAD, phi = lat * RAD;
    var d = (dayStart(date.getTime()) + 43200000) / 86400000 + 2440587.5 - J2000;
    var n = Math.round(d - 0.0009 - lw / (2 * Math.PI));
    var ds = 0.0009 + lw / (2 * Math.PI) + n;
    var M = RAD * (357.5291 + 0.98560028 * ds);
    var C = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
    var L = M + C + RAD * 102.9372 + Math.PI;
    var transit = J2000 + ds + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
    var dec = Math.asin(Math.sin(L) * Math.sin(RAD * 23.4397));
    var cosw = (Math.sin(RAD * -0.833) - Math.sin(phi) * Math.sin(dec)) / (Math.cos(phi) * Math.cos(dec));
    if (cosw > 1 || cosw < -1) return null;   // 백야·극야
    var w = Math.acos(cosw);
    var set = transit + w / (2 * Math.PI);
    return {
      rise: hhmm((transit - (set - transit) + 0.5 - J1970) * 86400000),
      set:  hhmm((set + 0.5 - J1970) * 86400000)
    };
  }

  // 기기 시간대가 무엇이든 한국 시각으로 표기합니다 (해외에서 열어도 값이 흔들리지 않도록)
  function hhmm(ms){
    var d = new Date(ms + 9 * 3600000);
    return ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2);
  }

  // 메인페이지(오늘의 바다)에서 같은 계산을 쓰도록 공개합니다
  window.BADAGAJA_TIDE = { calcMuldae: calcMuldae, calcIntensity: calcIntensity, tideLabel: tideLabel,
    sunTimes: sunTimes, lunarDay: lunarDay, names: MULDAE_NAMES, coords: COORDS };

  /* ---------- 달 모양 아이콘 ----------
     원의 한쪽은 반원, 다른 쪽은 위상에 따라 납작해지는 타원으로 그려 초승달~보름달을 표현합니다. */
  function moonSvg(age){
    var p = age / SYNODIC;                    // 0=삭, 0.5=보름
    var angle = p * 2 * Math.PI;
    var rx = (6.5 * Math.abs(Math.cos(angle))).toFixed(2);
    var big = p < 0.5 ? 1 : 0;
    var small = Math.cos(angle) > 0 ? big : 1 - big;
    return '<svg viewBox="0 0 16 16" aria-hidden="true">' +
      '<circle cx="8" cy="8" r="6.5" fill="#B9C6CC"/>' +
      '<path d="M8 1.5A6.5 6.5 0 0 ' + big + ' 8 14.5A' + rx + ' 6.5 0 0 ' + small + ' 8 1.5Z" fill="#E8B94A"/>' +
      '</svg>';
  }

  var SUN_SVG = '<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="#D9873A" stroke-width="1.3">' +
    '<circle cx="8" cy="8" r="3"/><path d="M8 1v1.6M8 13.4V15M2 8h1.6M12.4 8H14M3.8 3.8l1.1 1.1M11.1 11.1l1.1 1.1M3.8 12.2l1.1-1.1M11.1 4.9l1.1-1.1" stroke-linecap="round"/></svg>';

  /* ---------- 2주(14일)치 기본 데이터 ---------- */
  var TIDE_DAYS = 14;
  function buildDays(){
    var out = [], today = new Date();
    today.setHours(0,0,0,0);
    for (var i = 0; i < TIDE_DAYS; i++){
      var d = new Date(today);
      d.setDate(d.getDate() + i);
      out.push({
        dateObj: d,
        date: (d.getMonth()+1) + '/' + d.getDate(),
        day: DAY_NAMES[d.getDay()],
        muldae: calcMuldae(d),
        events: [],
        isToday: i === 0
      });
    }
    return out;
  }

  function render(days, sourceLabel){
    var coord = COORDS[REGION] || COORDS.boseong;
    var strip = document.getElementById('tideStrip');
    strip.innerHTML = days.map(function(d, idx){
      var weekLabel = '';
      if (days.length > 7 && (idx === 0 || idx === 7)) {
        var last = days[Math.min(idx + 6, days.length - 1)];
        weekLabel = '<div class="tide-week-label' + (idx === 7 ? ' wk2' : '') + '">' + (idx === 0 ? '本周' : '下周') +
                    ' <span>' + d.date + ' ~ ' + last.date + '</span></div>';
      }
      var intensity = calcIntensity(d.muldae);
      var label = tideLabel(intensity);
      var sun = sunTimes(d.dateObj, coord[0], coord[1]);

      var events = (d.events && d.events.length)
        ? d.events.map(function(e){
            var high = e.type === '만조';   // 서버 값(한국어) 비교
            return '<div class="td-ev' + (high ? ' high' : '') + '">' +
                     '<span class="k">' + (high ? '满' : '干') + '</span>' +
                     '<span class="t">' + e.time + '</span>' +
                     '<span class="h">' + (e.level != null ? e.level : '') + '</span>' +
                   '</div>';
          }).join('')
        : '<p class="pending">干潮·满潮数据准备中</p>';

      return weekLabel +
        '<div class="tide-day' + (d.isToday ? ' is-today' : '') + (idx >= 7 ? ' wk2' : '') + '" data-date="' + d.date + '">' +
          '<div class="td-top">' +
            '<span class="d-label">' + d.day + '</span>' +
            '<span class="d-date">' + d.date + '</span>' +
            '<span class="d-weather" id="w-' + d.date.replace('/','-') + '"></span>' +
          '</div>' +
          '<div class="td-astro">' +
            (sun ? '<span class="row">' + SUN_SVG + sun.rise + ' · ' + sun.set + '</span>' : '') +
          '</div>' +
          '<div class="d-muldae ' + label.cls + '"><span class="num">' + lunarText(d.dateObj) + '</span> · ' + label.text + '</div>' +
          '<div class="d-gauge"><div class="d-gauge-fill ' + label.cls + '" style="width:' + intensity + '%"></div></div>' +
          '<div class="td-events">' + events + '</div>' +
        '</div>';
    }).join('');
    // 휴대폰에서는 다음 주를 접어두고 버튼으로 펼침
    if (days.length > 7 && !document.getElementById('tideMoreBtn') && strip.parentNode) {
      var more = document.createElement('button');
      more.type = 'button'; more.id = 'tideMoreBtn'; more.className = 'tide-more';
      more.textContent = '查看下周潮汐 ▾';
      more.addEventListener('click', function(){
        var open = strip.classList.toggle('show-wk2');
        more.textContent = open ? '收起下周 ▴' : '查看下周潮汐 ▾';
      });
      strip.parentNode.insertBefore(more, strip.nextSibling);
    }
    document.getElementById('tideStatus').textContent = sourceLabel;
    applyWeatherToDays();
  }

  // 1) 계산값으로 즉시 표시 (빈 화면 방지)
  var fbDays = buildDays();
  render(fbDays, '潮汐与日出日落为推算值，正在加载干潮·满潮时间。');
  document.getElementById('headerMuldae').textContent =
    '今日 农历' + lunarText(fbDays[0].dateObj) + ' · ' + tideLabel(calcIntensity(fbDays[0].muldae)).text;

  // 2) 서버(api/tide.php)에서 실제 공공데이터를 가져올 수 있으면 간만조를 채웁니다
  fetch('../api/tide-cache.php?region=' + REGION, { cache: 'no-store' })
    .then(function(res){ if(!res.ok) throw new Error('no proxy'); return res.json(); })
    .then(function(data){
      if (!data || !data.days || !data.days.length) return;
      var days = fbDays.map(function(d, i){
        var src = data.days[i];
        if (src && src.events) d.events = src.events;
        return d;
      });
      var hasTime = days.some(function(d){ return d.events && d.events.length; });
      var note;
      if (hasTime) {
        var org = (data.source === 'beach') ? '韩国气象厅海水浴场潮汐' : '韩国国立海洋调查院潮汐预报';
        note = '干潮·满潮数据来源：' + org + ' · ' + (data.updated || '');
      } else {
        // 왜 비었는지를 서버가 알려주므로 그대로 보여줍니다.
        // 사이트가 미완성인 것처럼 읽히지 않게 하려는 것입니다.
        note = '潮汐与日出日落为推算值。干潮·满潮时间暂时无法显示。';
      }
      render(days, note);
    })
    .catch(function(){ /* 연동 전이면 계산값을 그대로 유지합니다 */ });

  var WEATHER_ICONS = {
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg>',
    cloudsun: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><circle cx="8" cy="8" r="3"/><path d="M8 2v1.5M8 12.5V14M2 8h1.5M12.5 8H14M3.8 3.8l1 1M11.2 4.8l1-1"/><path d="M9 20a4 4 0 010-8 5 5 0 019.5 1.5A3.5 3.5 0 0118 20H9z"/></svg>',
    cloud: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><path d="M6.5 19a4.5 4.5 0 010-9 6 6 0 0111.4 1.8A4 4 0 0117.5 19h-11z"/></svg>',
    rain: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><path d="M6.5 14a4.5 4.5 0 010-9 6 6 0 0111.4 1.8A4 4 0 0117.5 14h-11z"/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3"/></svg>',
    sleet: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><path d="M6.5 14a4.5 4.5 0 010-9 6 6 0 0111.4 1.8A4 4 0 0117.5 14h-11z"/><path d="M8 17l-1 3M12 17v3M16 17l-1 3"/></svg>',
    snow: '<svg viewBox="0 0 24 24" fill="none" stroke="#E5A94F" stroke-width="1.6"><path d="M6.5 14a4.5 4.5 0 010-9 6 6 0 0111.4 1.8A4 4 0 0117.5 14h-11z"/><path d="M8 18v2M12 18v2M16 18v2M7 19h2M11 19h2M15 19h2"/></svg>'
  };

  var latestWeatherDays = null;

  function setStat(id, text){
    var el = document.getElementById(id);
    if (!el) return;
    var box = el.closest ? el.closest('.w-stat') : null;
    if (text === null) { if (box) box.style.display = 'none'; return; }
    if (box) box.style.display = '';
    el.textContent = text;
  }

  function applyWeatherToDays(){
    if (!latestWeatherDays) return;
    latestWeatherDays.forEach(function(d){
      var slot = document.getElementById('w-' + d.date.replace('/', '-'));
      if (!slot) return;
      var icon = WEATHER_ICONS[d.icon] || WEATHER_ICONS.cloud;
      var temp = (d.temp !== null && d.temp !== undefined) ? '<span class="d-w-temp">' + d.temp + '°</span>' : '';
      slot.innerHTML = icon + temp;
    });
  }

  fetch(((IS_JEJU || IS_COAST) ? '../api/weather-jeju.php?region=' : '../api/weather.php?region=') + REGION, { cache: 'no-store' })
    .then(function(res){ if(!res.ok) throw new Error('no weather proxy'); return res.json(); })
    .then(function(w){
      if (!w) return;

      // 관측지점이 없는 권역은 다른 지역 날씨를 대신 보여주지 않고 띄를 감춥니다.
      if (w.available === false) {
        var card = document.getElementById('weatherCard');
        if (card) card.style.display = 'none';
        return;
      }

      document.getElementById('weatherIcon').innerHTML = WEATHER_ICONS[w.icon] || WEATHER_ICONS.cloud;
      document.getElementById('weatherTemp').textContent = (w.temp !== null && w.temp !== undefined) ? w.temp + '°C' : '–';
      document.getElementById('weatherLabel').textContent = (({'맑음':'晴','구름많음':'多云','흐림':'阴','비':'雨','비/눈':'雨夹雪','눈':'雪','소나기':'阵雨','빗방울':'毛毛雨','빗방울눈날림':'雨雪纷飞','눈날림':'飘雪'})[w.label] || '天气');
      // 파고·수온은 값이 없으면 칸 자체를 감춥니다.
      // 줄표를 띄워두면 고장처럼 보이기 때문입니다.
      setStat('weatherWave', (w.wave !== null && w.wave !== undefined && w.wave !== '') ? w.wave + 'm' : null);
      setStat('weatherWatertemp', (w.watertemp !== null && w.watertemp !== undefined) ? w.watertemp + '°C' : null);
      if (w.days && w.days.length){ latestWeatherDays = w.days; applyWeatherToDays(); }
    })
    .catch(function(){
      document.getElementById('weatherIcon').innerHTML = WEATHER_ICONS.cloud;
      var wc = document.getElementById('weatherCard');
      if (wc) wc.style.display = 'none';
    });
})();


// 맨 위로 버튼 — 모든 페이지에 공통으로 따라다니는 스크롤-탑 버튼.
// 페이지를 어느 정도 내렸을 때만 부드럽게 나타나고, 누르면 맨 위로 스무스 스크롤됩니다.
(function(){
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'to-top-btn';
  btn.setAttribute('aria-label', '回到顶端');
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="M6 11l6-6 6 6"/></svg>';
  document.body.appendChild(btn);

  var ticking = false;
  function updateVisibility(){
    ticking = false;
    if (window.scrollY > window.innerHeight * 0.6){
      btn.classList.add('show');
    } else {
      btn.classList.remove('show');
    }
  }
  window.addEventListener('scroll', function(){
    if (!ticking){
      window.requestAnimationFrame(updateVisibility);
      ticking = true;
    }
  }, { passive: true });
  updateVisibility();

  btn.addEventListener('click', function(){
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

/* =====================================================================
   컬러 벡터 아이콘 세트 (2026-09-09 추가) — 전 권역 공용
   HTML에는 <span class="ico" data-icon="kkomak"></span> 한 줄만 쓰고,
   실제 SVG는 여기서 넣어줍니다. 아이콘을 고치면 15개 권역에 한 번에 반영됩니다.
   ===================================================================== */
(function(){
  // 조개류 — 경첩이 위, 부챗살이 아래로 퍼지는 이매패 실루엣
  function shell(body, rib, ribs){
    var lines = ribs !== false
      ? '<path d="M24 15v23M15.5 15.5 12.5 32M32.5 15.5 35.5 32M9.5 16 8.5 24M38.5 16 39.5 24" stroke="' + rib + '" stroke-width="1.5" stroke-linecap="round" fill="none"/>'
      : '<path d="M24 15v23" stroke="' + rib + '" stroke-width="1.4" stroke-linecap="round"/><circle cx="17" cy="26" r="1.5" fill="' + rib + '"/><circle cx="30" cy="29" r="1.5" fill="' + rib + '"/><circle cx="25" cy="21" r="1.3" fill="' + rib + '"/>';
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M6 17a2 2 0 0 1 2-2h32a2 2 0 0 1 2 2c0 12.4-8 22-18 22S6 29.4 6 17Z" fill="' + body + '"/>' +
      lines + '</svg>';
  }

  // 물고기 — depth(d)로 몸통 높이를 바꿔 어종별 체형을 구분합니다.
  // 감성돔처럼 체고가 높은 어종은 d를 키우고, 학공치·전어처럼 납작한 어종은 줄입니다.
  function fish(body, fin, d){
    var top = 24 - d, bot = 24 + d;
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M34 24 46 ' + (24 - d * 0.85) + 'V' + (24 + d * 0.85) + 'Z" fill="' + fin + '"/>' +
      '<path d="M17 ' + (top + 2) + 'Q22 ' + (top - 6) + ' 28 ' + (top + 4) + 'Z" fill="' + fin + '"/>' +
      '<path d="M3 24Q20 ' + top + ' 37 24Q20 ' + bot + ' 3 24Z" fill="' + body + '"/>' +
      '<path d="M20 ' + (bot - 2) + 'q4 5 8 4" stroke="' + fin + '" stroke-width="2.4" stroke-linecap="round" fill="none"/>' +
      '<circle cx="11" cy="23" r="2.6" fill="#FFFDF6"/><circle cx="11" cy="23" r="1.3" fill="#243029"/>' +
      '</svg>';
  }

  // 문어·낙지 — 둥근 머리에 다리가 흘러내리는 형태
  function octopus(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M24 6c7.5 0 13.5 5.8 13.5 13 0 3.4-1.2 5.4-1.2 8 0 2.4 2.7 3 2.7 5.6 0 2.2-2.4 3.6-4.4 2.2-1.3-.9-1.4-2.8-2.6-2.8-1.3 0-1.3 3.2-3.3 3.2s-1.6-3.2-2.7-3.2-1 3.4-3.4 3.4-2-3.2-3.4-3.2-1.7 3.2-4.3 3.2-3.4-2-3.4-3.9c0-2.6 2.1-3.4 2.1-6.4 0-2.9-1.1-4.3-1.1-6.1C10.5 11.8 16.5 6 24 6Z" fill="' + body + '"/>' +
      '<circle cx="19" cy="18" r="2.6" fill="#FFFDF6"/><circle cx="29" cy="18" r="2.6" fill="#FFFDF6"/>' +
      '<circle cx="19.4" cy="18.4" r="1.3" fill="' + dark + '"/><circle cx="29.4" cy="18.4" r="1.3" fill="' + dark + '"/>' +
      '</svg>';
  }

  // 게 — 몸통 + 집게 + 다리
  function crab(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M12 32 7 37M16 35l-2 5M32 35l2 5M36 32l5 5" stroke="' + body + '" stroke-width="2.4" stroke-linecap="round" fill="none"/>' +
      '<path d="M12 22 7 16m0 0 3.4-.6M7 16l-.6 3.4M36 22l5-6m0 0-3.4-.6M41 16l.6 3.4" stroke="' + body + '" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>' +
      '<ellipse cx="24" cy="27" rx="13" ry="8.6" fill="' + body + '"/>' +
      '<circle cx="19.5" cy="24" r="2.2" fill="#FFFDF6"/><circle cx="28.5" cy="24" r="2.2" fill="#FFFDF6"/>' +
      '<circle cx="19.5" cy="24" r="1.1" fill="' + dark + '"/><circle cx="28.5" cy="24" r="1.1" fill="' + dark + '"/>' +
      '</svg>';
  }

  // 넙치·도다리류 — 한쪽으로 눈이 몰린 납작한 몸
  function flatfish(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M24 7c11 0 18 8 18 17s-7 17-18 17S6 33 6 24 13 7 24 7Z" fill="' + body + '"/>' +
      '<path d="M24 7c-3 5-4 11-4 17s1 12 4 17" stroke="' + dark + '" stroke-width="1.4" fill="none"/>' +
      '<path d="M6 24 1 19v10z" fill="' + dark + '"/>' +
      '<circle cx="15" cy="19" r="2.6" fill="#FFFDF6"/><circle cx="21" cy="17.5" r="2.6" fill="#FFFDF6"/>' +
      '<circle cx="15" cy="19" r="1.3" fill="' + dark + '"/><circle cx="21" cy="17.5" r="1.3" fill="' + dark + '"/>' +
      '<path d="M30 15c4 2 6 5 6 9s-2 7-6 9" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>';
  }

  // 장어류 — 길게 굽이치는 몸
  function eel(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M4 30c6 0 7-9 13-9s7 9 13 9 7-8 14-8" stroke="' + body + '" stroke-width="7" stroke-linecap="round" fill="none"/>' +
      '<path d="M4 30c6 0 7-9 13-9s7 9 13 9 7-8 14-8" stroke="' + dark + '" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.55"/>' +
      '<circle cx="43" cy="21" r="2.1" fill="#FFFDF6"/><circle cx="43" cy="21" r="1" fill="' + dark + '"/></svg>';
  }

  // 갈치류 — 은빛 띠 모양의 긴 몸
  function ribbon(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M3 33c10-2 18-6 24-11s10-8 18-9c-4 5-6 9-11 13s-16 8-31 7Z" fill="' + body + '"/>' +
      '<path d="M7 32c9-2 16-6 22-11" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round"/>' +
      '<circle cx="39" cy="16" r="1.9" fill="#FFFDF6"/><circle cx="39" cy="16" r="0.9" fill="' + dark + '"/></svg>';
  }

  // 오징어류 — 삼각 지느러미 + 다리
  function squid(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M24 3 34 13H14L24 3Z" fill="' + dark + '"/>' +
      '<path d="M24 8c6 0 9 4 9 10v9c0 4-4 6-9 6s-9-2-9-6v-9c0-6 3-10 9-10Z" fill="' + body + '"/>' +
      '<path d="M17 32c-1 5-2 8-4 11M21 33c-1 5-1 8-2 11M27 33c1 5 1 8 2 11M31 32c1 5 2 8 4 11" stroke="' + body + '" stroke-width="2.2" stroke-linecap="round" fill="none"/>' +
      '<circle cx="20" cy="20" r="2.4" fill="#FFFDF6"/><circle cx="28" cy="20" r="2.4" fill="#FFFDF6"/>' +
      '<circle cx="20" cy="20" r="1.2" fill="' + dark + '"/><circle cx="28" cy="20" r="1.2" fill="' + dark + '"/></svg>';
  }

  // 굴·석화 — 겹겹이 쌓인 거친 껍데기
  function oyster(body, dark, inner){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M11 16c3-7 11-11 20-9 7 1.6 11 7 11 13 0 9-8 17-19 17C13 37 6 31 6 24c0-3 2-6 5-8Z" fill="' + body + '"/>' +
      '<path d="M15 20c3-5 9-8 15-7 5 1 8 4 8 8 0 6-6 11-13 11-6 0-11-4-11-8 0-1.4.3-2.7 1-4Z" fill="' + inner + '"/>' +
      '<path d="M13 17c5 2 9 5 12 9s4 8 4 11M20 13c4 3 7 7 9 12s2 8 2 10M28 12c2 4 4 8 4 13" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round" opacity="0.55"/>' +
      '</svg>';
  }

  // 전복 — 타원 껍데기에 호흡공이 줄지어 있음
  function abalone(body, dark, inner){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<ellipse cx="24" cy="25" rx="19" ry="14" transform="rotate(-12 24 25)" fill="' + body + '"/>' +
      '<ellipse cx="26" cy="26" rx="12" ry="8.5" transform="rotate(-12 26 26)" fill="' + inner + '"/>' +
      '<circle cx="13" cy="20" r="1.5" fill="' + dark + '"/><circle cx="17.5" cy="17.5" r="1.5" fill="' + dark + '"/>' +
      '<circle cx="22" cy="15.6" r="1.5" fill="' + dark + '"/><circle cx="26.6" cy="14.4" r="1.5" fill="' + dark + '"/>' +
      '<path d="M9 28c4 5 12 8 20 7" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>';
  }

  // 소라·고둥 — 나선형 껍데기
  function conch(body, dark, spike){
    var spikes = spike !== false
      ? '<path d="M20 11 17.5 5M28 12l3-5.5M35 18l6-3M37.5 26l6 1" stroke="' + dark + '" stroke-width="2.4" stroke-linecap="round" fill="none"/>'
      : '';
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      spikes +
      '<path d="M25 7c9 0 16 7 16 16S32 43 21 43c-6 0-13-3-15-8 6 1 11 0 15-3 5-4 6-10 4-15-1-4-1-8 0-10Z" fill="' + body + '"/>' +
      '<path d="M25 7c-2 4-2 8-1 12 1 5 0 10-4 14-3 3-8 5-14 5" stroke="' + dark + '" stroke-width="1.5" fill="none" stroke-linecap="round"/>' +
      '<path d="M33 12c-2 4-2 9-1 13 1 5 0 10-4 14" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round" opacity="0.6"/>' +
      '</svg>';
  }

  // 해조류 — 물속에서 흔들리는 잎
  function seaweed(body, dark, wide){
    var blade = wide === true
      ? '<path d="M24 44c-2-10-2-20 0-30 5 2 9 8 9 16s-4 13-9 14Z" fill="' + body + '"/>' +
        '<path d="M24 44c2-10 2-20 0-30-5 2-9 8-9 16s4 13 9 14Z" fill="' + dark + '"/>'
      : '<path d="M24 45c-4-9-6-19-4-29 4 4 7 10 7 17 0 5-1 9-3 12Z" fill="' + body + '"/>' +
        '<path d="M24 45c4-8 8-16 9-25-5 2-9 7-11 13-1 4-1 8 2 12Z" fill="' + dark + '"/>' +
        '<path d="M24 45c-6-5-11-11-13-18 5 1 10 5 12 10 1 3 2 6 1 8Z" fill="' + body + '" opacity="0.75"/>';
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      blade + '<path d="M8 45h32" stroke="' + dark + '" stroke-width="2.2" stroke-linecap="round"/></svg>';
  }

  // 해삼 — 돌기가 솟은 원통형 몸
  function cucumber(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M8 30c0-6 7-9 16-9s16 3 16 9-7 9-16 9S8 36 8 30Z" fill="' + body + '"/>' +
      '<path d="M12 23l-2-5M19 20l-1-6M26 20l1-6M33 23l3-5M40 29l5-3" stroke="' + dark + '" stroke-width="2.2" stroke-linecap="round" fill="none"/>' +
      '<path d="M14 32c3 2 7 3 10 3s7-1 10-3" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>';
  }

  // 키조개 — 길쭉한 삼각 껍데기
  function penshell(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M24 4c7 4 12 16 12 28 0 6-5 12-12 12s-12-6-12-12C12 20 17 8 24 4Z" fill="' + body + '"/>' +
      '<path d="M24 6v37M18 12c-2 8-3 17-3 24M30 12c2 8 3 17 3 24" stroke="' + dark + '" stroke-width="1.4" fill="none" stroke-linecap="round"/></svg>';
  }

  // 홍합 — 한쪽이 뾰족한 타원 껍데기
  function mussel(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M6 34c0-11 13-24 30-26 2 7-2 18-10 25-7 6-15 8-20 1Z" fill="' + body + '"/>' +
      '<path d="M9 33C12 24 22 14 33 10" stroke="' + dark + '" stroke-width="1.5" fill="none" stroke-linecap="round"/>' +
      '<path d="M14 36c3-9 12-19 22-24" stroke="' + dark + '" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.7"/></svg>';
  }

  // 개불 — 굵고 매끈한 원통형 몸
  function worm(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M8 24c0-5 7-8 16-8s16 3 16 8-7 8-16 8S8 29 8 24Z" fill="' + body + '"/>' +
      '<path d="M13 19c1 3 1 7 0 10M20 17c1 4 1 10 0 14M28 17c-1 4-1 10 0 14M35 19c-1 3-1 7 0 10" stroke="' + dark + '" stroke-width="1.3" fill="none" stroke-linecap="round"/>' +
      '<path d="M40 24c3 0 5-1 6-3M8 24c-3 0-5 1-6 3" stroke="' + body + '" stroke-width="3" stroke-linecap="round" fill="none"/></svg>';
  }

  // 새우·쏙 — 말린 몸통에 더듬이
  function shrimp(body, dark){
    return '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
      '<path d="M38 14c-13 0-22 7-22 15 0 6 5 10 11 10 5 0 9-3 9-7 0-3-2-5-5-5-2 0-4 1-4 3" stroke="' + body + '" stroke-width="7" stroke-linecap="round" fill="none"/>' +
      '<path d="M38 14c-4 0-8 1-11 2M38 14c-3-2-6-3-9-3" stroke="' + dark + '" stroke-width="1.8" stroke-linecap="round" fill="none"/>' +
      '<path d="M40 11l6-4M40 17l7 1" stroke="' + dark + '" stroke-width="1.6" stroke-linecap="round" fill="none"/>' +
      '<circle cx="37" cy="15" r="1.7" fill="#FFFDF6"/><circle cx="37" cy="15" r="0.8" fill="' + dark + '"/></svg>';
  }

  var ICONS = {
    /* --- 해루질 대상 --- */
    kkomak:   shell('#A8542B', '#6E3416', true),                  // 참꼬막
    bajirak:  shell('#C9A46B', '#8A6A34', false),                 // 바지락
    dongjuk:  shell('#9A8459', '#61502E', false),                 // 동죽
    matjogae: '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<rect x="18" y="4" width="12" height="40" rx="6" transform="rotate(14 24 24)" fill="#B98A55"/>' +
              '<path d="M19 7 27 41" stroke="#7C5629" stroke-width="1.6" stroke-linecap="round"/></svg>',
    nakji:    octopus('#7E5A86', '#3A2740'),                      // 뻘낙지
    dolmuneo: octopus('#9C4B45', '#4E211E'),                      // 돌문어
    chilge:   crab('#8C7A3E', '#3F3616'),                         // 칠게
    kkotge:   crab('#BC5330', '#5A2211'),                         // 민꽃게
    jjangttungeo: '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M40 28c-4 7-10 9-17 9s-14-2-19-9c4-5 9-8 15-8 8 0 17 3 21 8Z" fill="#5E6B45"/>' +
              '<path d="M39 28l7-6v12z" fill="#3E4A2C"/>' +
              '<path d="M14 34c-2 3-5 4-7 3M31 34c2 3 5 4 7 3" stroke="#3E4A2C" stroke-width="2.2" stroke-linecap="round" fill="none"/>' +
              '<circle cx="12" cy="17" r="4" fill="#5E6B45"/><circle cx="20" cy="16" r="4" fill="#5E6B45"/>' +
              '<circle cx="12" cy="16.5" r="2.2" fill="#FFFDF6"/><circle cx="20" cy="15.5" r="2.2" fill="#FFFDF6"/>' +
              '<circle cx="12" cy="16.5" r="1.1" fill="#243029"/><circle cx="20" cy="15.5" r="1.1" fill="#243029"/></svg>',

    /* --- 낚시 대상 --- */
    gamseongdom: fish('#5A6B78', '#33414B', 14),   // 감성돔 — 체고가 높음
    bollak:      fish('#8A4F5C', '#542E38', 12),   // 볼락
    ureok:       fish('#6B6250', '#403A2C', 12),   // 우럭
    noraemi:     fish('#8A7238', '#54451D', 10),   // 노래미
    sungeo:      fish('#7A8B93', '#4A575E', 9),   // 숭어
    jeoneo:      fish('#9AA7AE', '#5E6A70', 11),    // 전어
    hakgongchi:  '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M2 24 16 21c8-1 15 0 21 3-6 3-13 4-21 3z" fill="#9FB0B8"/>' +
              '<path d="M36 24l8-5v10z" fill="#61727A"/>' +
              '<path d="M2 24 15 23.4" stroke="#61727A" stroke-width="2" stroke-linecap="round"/>' +
              '<circle cx="19" cy="23" r="1.8" fill="#FFFDF6"/><circle cx="19" cy="23" r="0.9" fill="#243029"/></svg>',


    /* --- 2026-09-10 전 권역 전파: 보성 외 14개 권역에서 쓰는 어종 추가 --- */
    /* 패류 */
    saekkomak: shell('#B4794A', '#77492A', true),
    baekhap:   shell('#E0D2B0', '#A2905F', false),
    gaejogae:  shell('#B0A183', '#6F6349', false),
    gamurak:   shell('#7B6E55', '#463D2C', false),
    saejogae:  shell('#D9A08C', '#96604F', true),
    jaecheop:  shell('#8E9A86', '#4F5A48', false),
    jogae:     shell('#C2B393', '#83765A', false),
    kijogae:   penshell('#7E6640', '#4B3A22'),
    honghap:   mussel('#3E3A4A', '#211E2A'),
    gul:       oyster('#B9AE95', '#6E6550', '#EFE7D3'),
    beotgul:   oyster('#C9C0A8', '#7A7259', '#F6F0E0'),
    jeonbok:   abalone('#4C5B4A', '#2A332A', '#B7C0A2'),
    sora:      conch('#A98A5C', '#6A5333', true),
    godong:    conch('#9A7F63', '#5C4933', false),
    haesam:    cucumber('#6B4A45', '#3A2523'),
    gaebul:    worm('#D0937F', '#8A5646'),
    ssok:      shrimp('#C08A63', '#754E33'),

    /* 두족류 */
    muneo:     octopus('#9C4B45', '#4E211E'),
    sebalnakji: octopus('#8C6D93', '#42304A'),
    nakjial:   octopus('#A98CAF', '#4E3B55'),
    gapojingeo: squid('#C9BBA4', '#6E6250'),
    munuiojingeo: squid('#B9A488', '#61533D'),

    /* 갑각류 */
    chamge:    crab('#6E6A43', '#33301B'),

    /* 어류 */
    nongeo:      fish('#7C8A8E', '#48545A', 12),
    chamdom:     fish('#C4816F', '#7A4636', 14),
    doldom:      fish('#8E8B7E', '#3E3C33', 14),
    bengedom:    fish('#5F6E63', '#33403A', 13),
    jeongaengi:  fish('#7E9099', '#4A5A62', 10),
    godeungeo:   fish('#5E7382', '#33454F', 11),
    samchi:      fish('#8FA2A8', '#54666C', 10),
    mineo:       fish('#A08E72', '#5F5340', 13),
    byeongeo:    fish('#C3C6BC', '#75786D', 15),
    mangdungeo:  fish('#8A7A5A', '#514734', 10),
    dodari:      flatfish('#8A7B58', '#4E4530'),
    galchi:      ribbon('#C6CCD2', '#77808A'),
    bungjangeo:  eel('#8A7358', '#4E4130'),
    baemjangeo:  eel('#6E6250', '#3B342A'),
    gaetjangeo:  eel('#9A8B70', '#57503F'),

    /* 해조류 */
    gim:       seaweed('#3B4A3A', '#22301F', true),
    miyeok:    seaweed('#4A5C3E', '#2B3823', false),
    dasima:    seaweed('#4E5C36', '#2E3820', true),
    tot:       seaweed('#5A4A32', '#33291B', false),
    maesaengi: seaweed('#3F5940', '#233524', false),
    gamtae:    seaweed('#57703F', '#334224', false),

    /* --- 방식 배지 --- */
    foraging: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M9 3h6v2H9z" fill="#8A6428"/><path d="M7 6h10l-1.4 11.5A2 2 0 0 1 13.6 19h-3.2a2 2 0 0 1-2-1.5L7 6Z" fill="#E5A94F"/>' +
              '<circle cx="12" cy="11.5" r="2.6" fill="#FFF6E0"/><path d="M5 21h14" stroke="#8A6428" stroke-width="1.6" stroke-linecap="round"/></svg>',
    fishing:  '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M3 3 15 15" stroke="#2F5D57" stroke-width="1.8" stroke-linecap="round"/>' +
              '<path d="M15 15v3a3 3 0 0 1-5 2" stroke="#2F5D57" stroke-width="1.6" fill="none" stroke-linecap="round"/>' +
              '<path d="M2 21c2-1.6 4-1.6 6 0s4 1.6 6 0 4-1.6 6 0" stroke="#4F8A83" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>',

    /* --- 향토 먹거리 --- */
    jeongsik: '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<rect x="3" y="14" width="42" height="24" rx="3" fill="#7C5A33"/>' +
              '<rect x="6" y="17" width="36" height="18" rx="2" fill="#E9D9B6"/>' +
              '<circle cx="15" cy="26" r="6.5" fill="#FFFDF6"/><circle cx="15" cy="26" r="3.4" fill="#C0762E"/>' +
              '<circle cx="30" cy="23" r="4.6" fill="#FFFDF6"/><circle cx="30" cy="23" r="2.3" fill="#8C4A2A"/>' +
              '<circle cx="36" cy="31" r="3.6" fill="#FFFDF6"/><circle cx="36" cy="31" r="1.7" fill="#5E7A46"/>' +
              '<path d="M22 8c0 3-2 3-2 6M28 8c0 3-2 3-2 6" stroke="#C9B48A" stroke-width="1.8" stroke-linecap="round" fill="none"/></svg>',
    tang:     '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M16 6c0 4-3 4-3 8M24 4c0 4-3 4-3 8M32 6c0 4-3 4-3 8" stroke="#C9B48A" stroke-width="2" stroke-linecap="round" fill="none"/>' +
              '<path d="M5 19h38l-3 15a6 6 0 0 1-6 5H14a6 6 0 0 1-6-5L5 19Z" fill="#8A5A2E"/>' +
              '<path d="M8 21h32l-1.4 7H9.4L8 21Z" fill="#C4762C"/>' +
              '<circle cx="18" cy="24.5" r="1.8" fill="#5E7A46"/><circle cx="27" cy="24.5" r="1.8" fill="#5E7A46"/></svg>',
    yeonpo:   '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M4 18h40v6a16 16 0 0 1-16 16h-8A16 16 0 0 1 4 24v-6Z" fill="#6E6A5E"/>' +
              '<path d="M2 15h44v4H2z" fill="#4E4A40"/>' +
              '<path d="M20 18c-2-4 0-8 4-8s6 4 4 8" fill="#7E5A86"/>' +
              '<path d="M14 22c3 2 5 6 4 9M34 22c-3 2-5 6-4 9" stroke="#7E5A86" stroke-width="2.4" stroke-linecap="round" fill="none"/></svg>',
    hoe:      '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<ellipse cx="24" cy="30" rx="21" ry="10" fill="#E9D9B6"/><ellipse cx="24" cy="28" rx="17" ry="7.5" fill="#FFFDF6"/>' +
              '<path d="M13 28c2-4 6-5 9-3-2 4-6 5-9 3Z" fill="#D98A78"/>' +
              '<path d="M22 30c2-4 6-5 9-3-2 4-6 5-9 3Z" fill="#C8705E"/>' +
              '<path d="M28 24c2-3 5-3 7-1-2 3-5 3-7 1Z" fill="#D98A78"/>' +
              '<circle cx="17" cy="23" r="2.4" fill="#5E7A46"/></svg>',
    kalguksu: '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M5 20h38l-3 14a6 6 0 0 1-6 5H14a6 6 0 0 1-6-5L5 20Z" fill="#B8B0A0"/>' +
              '<path d="M8 22h32l-1.2 6H9.2L8 22Z" fill="#F0E7D2"/>' +
              '<path d="M11 24.5h26M11.6 26.6h24.8" stroke="#D8CBAA" stroke-width="1.4" stroke-linecap="round"/>' +
              '<path d="M18 17a1.4 1.4 0 0 1 1.4-1.4h8.2A1.4 1.4 0 0 1 29 17c0 5-2.5 8-5.5 8S18 22 18 17Z" fill="#C9A46B"/></svg>',
    gui:      '<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
              '<path d="M13 40c-1-3 1-5 1-8 0-2-2-3-2-5 4 1 5 4 5 6 1-3 0-6 2-8 0 3 2 4 2 7" stroke="#D9762E" stroke-width="2.2" fill="none" stroke-linecap="round"/>' +
              '<path d="M28 40c-1-2 1-4 1-6 0-2-1-2-1-4 3 1 4 3 4 5" stroke="#E5A94F" stroke-width="2.2" fill="none" stroke-linecap="round"/>' +
              '<path d="M10 20a1.8 1.8 0 0 1 1.8-1.8h24.4A1.8 1.8 0 0 1 38 20c0 8-6.3 14-14 14s-14-6-14-14Z" fill="#C9A46B"/>' +
              '<path d="M24 18.2v15M17 19 15 30M31 19l2 11" stroke="#8A6A34" stroke-width="1.5" stroke-linecap="round"/>' +
              '<path d="M6 44h36" stroke="#6E6353" stroke-width="2" stroke-linecap="round"/></svg>'
  };

  document.querySelectorAll('.ico[data-icon]').forEach(function(el){
    var svg = ICONS[el.getAttribute('data-icon')];
    if (svg) el.innerHTML = svg;
  });
})();

/* =====================================================================
   바다지수 — 국립해양조사원 갯벌체험지수 / 바다낚시지수 (2026-09-09 추가)
   .sea-index[data-index="mudflat"|"fishing"] 요소를 찾아 api/seaidx.php로 채웁니다.
   API가 아직 연동되지 않았거나 해당 지점 데이터가 없으면 요소를 조용히 감춥니다.
   ===================================================================== */
(function(){
  var REGION = document.body.getAttribute('data-region') || 'boseong';
  var boxes = document.querySelectorAll('.sea-index[data-index]');
  if (!boxes.length) return;

  boxes.forEach(function(box){
    var type = box.getAttribute('data-index');
    // seaindex.php 가 부르는 해양조사원 API 가 폐기되어 비어 있던 것 — seaidx.php 로 (2026-09-22)
    fetch('../api/seaidx.php?type=' + type + '&region=' + REGION, { cache: 'no-store' })
      .then(function(res){ if(!res.ok) throw new Error('no index proxy'); return res.json(); })
      .then(function(d){
        if (!d || !d.available || !d.grade) throw new Error('no data');
        box.setAttribute('data-grade', String(d.grade));
        box.classList.remove('is-loading');
        box.querySelector('.si-grade').textContent = d.label || '';
        var when = box.querySelector('.si-when');
        if (when) {
          // 어느 지점 값인지 함께 밝힙니다. 권역에 지점이 없어 옆 지점을 끌어온
          // 경우(10km 초과)에는 거리도 같이 적어 오해가 없게 합니다.
          var parts = [];
          if (d.point) parts.push(d.point);
          if (d.distance && d.distance > 10) parts.push(Math.round(d.distance) + 'km');
          if (d.when) parts.push(d.when);
          when.textContent = parts.join(' · ');
        }
      })
      .catch(function(){
        // 연동 전이거나 그 지점에 오늘 예보가 없는 경우.
        // 미완성 표시를 남기지 않고 게이지를 통째로 감춥니다.
        // (마크업·CSS·PHP는 그대로 있으니, 연동되면 자동으로 다시 나타납니다)
        box.style.display = 'none';
      });
  });
})();

/* =====================================================================
   해안가 관광지 4곳 — 전라남도관광재단 해안가마을 관광자원 (2026-09-09 추가)
   #spotGrid가 있는 페이지에서만 동작하고, 실패하면 HTML에 적힌 기본 카드를 그대로 둡니다.
   ===================================================================== */
(function(){
  // 2026-09-15: 해안가마을 API가 폐기되어 js/region-extra.js 가 한국관광공사 관광지로 채웁니다.
  return;
  var grid = document.getElementById('spotGrid');
  if (!grid) return;
  var REGION = document.body.getAttribute('data-region') || 'boseong';

  fetch('../api/coastspot.php?region=' + REGION + '&limit=4', { cache: 'no-store' })
    .then(function(res){ if(!res.ok) throw new Error('no spot proxy'); return res.json(); })
    .then(function(d){
      if (!d || !d.spots || d.spots.length < 4) throw new Error('not enough');
      grid.innerHTML = d.spots.slice(0,4).map(function(s){
        return '<div class="spot-card">' +
          '<div class="spot-kind">' + (s.kind || '') + '</div>' +
          '<h3>' + s.name + '</h3>' +
          (s.addr ? '<div class="spot-addr">' + s.addr + '</div>' : '') +
          (s.desc ? '<p class="spot-desc">' + s.desc + '</p>' : '') +
        '</div>';
      }).join('');
      var note = document.getElementById('spotNote');
      if (note && d.updated) note.textContent = d.updated;
    })
    .catch(function(){
      // 연동 전이면 HTML에 미리 적어둔 카드가 그대로 보입니다.
    });
})();

/* =====================================================================
   옆으로 더 있어요 표시 (2026-09-20)
   가로로 밀어 보는 줄 — 여행지 띠(.h-site), 위쪽 메뉴, 권역 줄, 카드 줄 —
   에서 아직 못 본 쪽이 남아 있으면 그 가장자리를 어둡게 하고,
   여행지 띠에는 눌러서 넘길 수 있는 화살표 단추까지 띄웁니다.
   ===================================================================== */
(function () {
  var SEL = '.h-site,.navlinks,.ts-regions,.ts-groups,.hc-track,.rn-list,.cr-wrap';
  var ZH = (document.documentElement.getAttribute('lang') || '').toLowerCase().indexOf('zh') === 0;

  function mark(el) {
    var max = el.scrollWidth - el.clientWidth;
    if (max < 8) { el.classList.remove('xs-l', 'xs-r'); return; }
    el.classList.toggle('xs-l', el.scrollLeft > 4);
    el.classList.toggle('xs-r', el.scrollLeft < max - 4);
  }

  function arrow(el, dir) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'xs-go xs-go-' + (dir > 0 ? 'r' : 'l');
    b.setAttribute('aria-label', dir > 0
      ? (ZH ? '查看右边更多' : '옆으로 더 보기')
      : (ZH ? '查看左边' : '앞쪽 보기'));
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' +
      (dir > 0 ? 'M9 5l7 7-7 7' : 'M15 5l-7 7 7 7') +
      '" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    b.addEventListener('click', function () {
      var step = Math.max(160, Math.round(el.clientWidth * 0.7));
      try { el.scrollBy({ left: dir * step, behavior: 'smooth' }); }
      catch (e) { el.scrollLeft += dir * step; }
    });
    return b;
  }

  var seen = [];
  function scan() {
    var list = document.querySelectorAll(SEL);
    for (var i = 0; i < list.length; i++) {
      var el = list[i];
      if (el.getAttribute('data-xs')) continue;
      el.setAttribute('data-xs', '1');
      if (el.classList.contains('h-site')) {
        el.insertBefore(arrow(el, -1), el.firstChild);
        el.appendChild(arrow(el, 1));
      }
      (function (n) {
        n.addEventListener('scroll', function () { mark(n); }, { passive: true });
      })(el);
      seen.push(el);
    }
    for (var j = 0; j < seen.length; j++) mark(seen[j]);
  }

  function start() {
    scan();
    window.addEventListener('resize', function () { for (var j = 0; j < seen.length; j++) mark(seen[j]); });
    setTimeout(scan, 700);
    setTimeout(scan, 2200);
    if (window.MutationObserver) {
      var t = null;
      new MutationObserver(function () {
        clearTimeout(t); t = setTimeout(scan, 200);
      }).observe(document.body, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
