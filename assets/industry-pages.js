/* Shared one-shot entrance observer; no timers or scroll handler. */
(function () {
 'use strict';
 var root = document.querySelector('.industry-page');
 if (!root || !('IntersectionObserver' in window)) return;
 var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
 var observer = new IntersectionObserver(function (entries) {
  entries.forEach(function (entry) {
   if (entry.isIntersecting) { entry.target.classList.add('ip-visible'); observer.unobserve(entry.target); }
  });
 }, { threshold: .06 });
 root.querySelectorAll('.ip-section,.ip-module,.ip-terms li,.related-card,.market-page .card,.market-page .term').forEach(function (el) {
  el.classList.add('ip-enter'); observer.observe(el);
 });
 function sync() { root.classList.toggle('ip-motion', !reduce.matches); }
 if (reduce.addEventListener) reduce.addEventListener('change', sync);
 else reduce.addListener(sync);
 sync();
})();
