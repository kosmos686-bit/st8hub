(function () {
  var s = document.getElementById('pricing');
  if (!s) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var g = s.querySelector('.pricing-grid');
  if (g && window.innerWidth <= 900) {
    var c = g.children[1];
    if (c) g.scrollLeft = c.offsetLeft - (g.clientWidth - c.offsetWidth) / 2;
  }
  if (reduce) return;
  s.classList.add('pr-armed');
  var done = false;
  function show() {
    if (done) return;
    done = true;
    s.classList.add('pr-in');
    window.removeEventListener('scroll', check);
    window.removeEventListener('resize', check);
    window.removeEventListener('hashchange', check);
    window.removeEventListener('load', check);
  }
  function check() {
    if (done) return;
    var r = s.getBoundingClientRect(), vh = window.innerHeight || document.documentElement.clientHeight;
    if (r.top < vh * 0.85 && r.bottom > 0) show();
  }
  window.addEventListener('scroll', check, { passive: true });
  window.addEventListener('resize', check);
  window.addEventListener('hashchange', check);
  window.addEventListener('load', check);
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (e) { if (e[0].isIntersecting) { show(); io.disconnect(); } }, { threshold: 0 });
    io.observe(s);
  }
  check();
  [200, 600, 1200, 2500].forEach(function (t) { setTimeout(check, t); });
  // safety net: if the section is anywhere in view after 4s, never leave tariffs hidden
  setTimeout(function () { var r = s.getBoundingClientRect(); if (r.bottom > 0 && r.top < (window.innerHeight || 800)) show(); }, 4000);
})();
