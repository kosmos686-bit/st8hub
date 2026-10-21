/* Phones: the three tariffs form a swipeable row; the dots follow the nearest card. */
(function () {
  'use strict';
  var grid = document.querySelector('#pricing .pricing-grid');
  var dots = Array.prototype.slice.call(document.querySelectorAll('#pricing .pricing-dots i'));
  if (!grid || !dots.length) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.pricing-card'));
  var mq = window.matchMedia('(max-width:900px)');
  function nearest() {
    var center = grid.scrollLeft + grid.clientWidth / 2, best = 0, gap = Infinity;
    cards.forEach(function (card, i) {
      var d = Math.abs(card.offsetLeft + card.offsetWidth / 2 - center);
      if (d < gap) { gap = d; best = i; }
    });
    return best;
  }
  function paint() { var n = nearest(); dots.forEach(function (d, i) { d.classList.toggle('on', i === n); }); }
  function center(i) {
    var card = cards[i];
    grid.scrollTo({ left: card.offsetLeft - (grid.clientWidth - card.offsetWidth) / 2, behavior: 'auto' });
  }
  var tick = 0;
  grid.addEventListener('scroll', function () { if (!tick) tick = requestAnimationFrame(function () { tick = 0; paint(); }); }, { passive: true });
  dots.forEach(function (d, i) { d.addEventListener('click', function () { center(i); }); });
  if (mq.matches) center(1);
  paint();
})();
