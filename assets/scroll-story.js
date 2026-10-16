/* A single scroll scheduler drives only transforms and opacity in story scenes. */
(function () {
  'use strict';
  var root = document.getElementById('scroll-story');
  if (!root) return;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var scenes = [1, 2, 3].map(function (n) { return root.querySelector('#story-scene-' + n); });
  var tickets = Array.prototype.slice.call(root.querySelectorAll('#story-scene-1 .ss-tk'));
  var steps = Array.prototype.slice.call(root.querySelectorAll('.ss-steps li'));
  var receipt = root.querySelector('.ss-rc');
  var industries = Array.prototype.slice.call(root.querySelectorAll('.ss-big'));
  var papers = Array.prototype.slice.call(root.querySelectorAll('.ss-art .ss-sh'));
  var dots = Array.prototype.slice.call(root.querySelectorAll('.ss-dots i'));
  var words = Array.prototype.slice.call(root.querySelectorAll('.ss-word'));
  var pending = false;
  function clamp(x) { return Math.max(0, Math.min(1, x)); }
  function progress(scene) {
    var bounds = scene.getBoundingClientRect();
    var distance = scene.offsetHeight - window.innerHeight;
    return distance <= 0 ? 1 : clamp(-bounds.top / distance);
  }
  function render() {
    var reduced = reduce.matches;
    var p = reduced ? 1 : progress(scenes[0]);
    tickets.forEach(function (ticket, index) {
      var shown = reduced ? 1 : clamp((p * 1.15 - index / tickets.length * .9 - .04) / .22);
      ticket.style.opacity = String(shown);
      ticket.style.transform = 'translateY(' + (-(1 - shown) * 34) + 'px)';
      ticket.style.setProperty('--ss-marker', clamp((shown - .5) / .5));
      if (steps[index]) steps[index].style.opacity = String(.65 + .35 * shown);
    });
    receipt.style.transform = reduced ? 'none' : 'rotate(2.2deg) translateY(' + (clamp(p) * 8) + 'px)';
    var selected = Math.min(industries.length - 1, Math.floor(progress(scenes[1]) * industries.length));
    industries.forEach(function (card, index) {
      var visible = reduced || index === selected;
      card.style.opacity = visible ? '1' : '0';
      card.style.transform = visible ? 'none' : 'translateY(36px)';
      card.setAttribute('aria-hidden', String(!visible));
    });
    papers.forEach(function (paper, index) {
      var visible = reduced || index === selected;
      paper.style.opacity = visible ? '1' : '0';
      paper.style.transform = reduced ? 'none' : 'translateY(-50%) rotate(3deg) translateY(' + (visible ? 0 : 36) + 'px)';
    });
    dots.forEach(function (dot, index) { dot.style.opacity = index <= selected || reduced ? '1' : '.2'; });
    p = reduced ? 1 : progress(scenes[2]);
    words.forEach(function (word, index) {
      word.style.setProperty('--ss-lit', reduced ? 1 : clamp(p * 1.25 * words.length - index));
    });
  }
  function schedule() {
    if (pending || document.hidden) return;
    pending = true;
    requestAnimationFrame(function () { pending = false; if (!document.hidden) render(); });
  }
  function motionChanged() { root.classList.toggle('ss-motion', !reduce.matches); schedule(); }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  document.addEventListener('visibilitychange', schedule);
  if (reduce.addEventListener) reduce.addEventListener('change', motionChanged);
  else reduce.addListener(motionChanged);
  root.classList.toggle('ss-motion', !reduce.matches);
  render();
})();
