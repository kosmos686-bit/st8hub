(function () {
  var s = document.getElementById('pricing');
  if (!s) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var g = s.querySelector('.pricing-grid');
  if (g && window.innerWidth <= 900) {
    var c = g.children[1];
    if (c) g.scrollLeft = c.offsetLeft - (g.clientWidth - c.offsetWidth) / 2;
  }
  if (reduce || !('IntersectionObserver' in window)) return;
  s.classList.add('pr-armed');
  var io = new IntersectionObserver(function (e) {
    if (e[0].isIntersecting) { s.classList.add('pr-in'); io.disconnect(); }
  }, { threshold: .2 });
  io.observe(s);
})();
