/* 중국어판 공유 막대 — 푸터 바로 위에 "복사·공유" 버튼을 넣는다.
 * 위챗·샤오훙수 안에서는 브라우저 공유창이 없는 경우가 많아 "링크 복사"를 기본으로 두고,
 * 공유창(navigator.share)이 있는 기기에서만 "分享" 버튼을 함께 보여 준다.
 */
(function () {
  var foot = document.querySelector('footer.site-footer');
  if (!foot || document.querySelector('.zshare')) return;
  var url = (document.querySelector('link[rel="canonical"]') || {}).href || location.href.split('#')[0];
  var title = document.title.replace(/｜Badagaja$/, '');
  var inWx = /MicroMessenger/i.test(navigator.userAgent);

  var box = document.createElement('section');
  box.className = 'zshare';
  box.setAttribute('aria-label', '分享本页');
  box.innerHTML =
    '<div class="wrap zshare-in">' +
      '<div class="zshare-txt"><b>觉得有用？转给一起在韩国的朋友</b>' +
      '<small>' + (inWx ? '在微信里：点右上角「···」即可发送给朋友或分享到朋友圈。' : '复制链接后，可粘贴到微信、小红书或QQ。') + '</small></div>' +
      '<div class="zshare-btns">' +
        '<button type="button" class="zshare-copy">复制链接</button>' +
        (navigator.share ? '<button type="button" class="zshare-sys">分享…</button>' : '') +
      '</div>' +
      '<p class="zshare-msg" role="status" aria-live="polite"></p>' +
    '</div>';
  foot.parentNode.insertBefore(box, foot);

  var msg = box.querySelector('.zshare-msg');
  function say(t) { msg.textContent = t; clearTimeout(say.t); say.t = setTimeout(function () { msg.textContent = ''; }, 4000); }
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    var ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }
  box.querySelector('.zshare-copy').addEventListener('click', function () {
    var text = title + ' ' + url;
    function done() { say('已复制：' + url); }
    function fail() { say(fallbackCopy(text) ? '已复制：' + url : '复制失败，请长按地址栏手动复制。'); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fail);
    else fail();
  });
  var sys = box.querySelector('.zshare-sys');
  if (sys) sys.addEventListener('click', function () {
    navigator.share({ title: title, url: url }).catch(function () {});
  });
})();
