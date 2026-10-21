/* Pause receipt motion outside the viewport and when the page is hidden. */
(function () {
  'use strict';
  var hero = document.querySelector('.receipt-home .hero');
  var tape = hero && hero.querySelector('.rt-printer');
  var nav = hero && hero.querySelector('.navbar');
  if (!tape || !nav) return;
  var inView = false;
  function updateMotion() {
    tape.style.setProperty('--receipt-play-state', inView && !document.hidden ? 'running' : 'paused');
  }
  function updateNavHeight() {
    hero.style.setProperty('--receipt-nav-height', nav.getBoundingClientRect().height + 'px');
  }
  new IntersectionObserver(function (entries) {
    inView = entries[0].isIntersecting;
    updateMotion();
  }, { threshold: 0 }).observe(tape);
  document.addEventListener('visibilitychange', updateMotion);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(updateNavHeight).observe(nav);
  else window.addEventListener('resize', updateNavHeight);
  var burger = hero.querySelector('#hamburger');
  if (burger) {
    burger.setAttribute('aria-label', (window.SS_I18N && window.SS_I18N.menu) || 'Меню');
    burger.setAttribute('aria-controls', 'mobileMenu');
    burger.setAttribute('aria-expanded', 'false');
    burger.addEventListener('click', function () {
      burger.setAttribute('aria-expanded', document.getElementById('mobileMenu').classList.contains('open') ? 'true' : 'false');
    });
  }
  updateNavHeight();
})();
