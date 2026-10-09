/* Delegated tracking also follows links changed by the market selector. */
(function () {
  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[href]');
    if (!link || typeof ym !== 'function') return;
    var url;
    try { url = new URL(link.href, location.href); } catch (_) { return; }
    var goal;
    if (url.hostname === 't.me' && url.pathname.replace(/\/$/, '') === '/Zzima686') goal = 'telegram_click';
    if (url.hostname === 'wa.me' && url.pathname.replace(/\/$/, '') === '/79856905252') goal = 'whatsapp_click';
    if (goal) ym(112836376, 'reachGoal', goal);
  });
})();
