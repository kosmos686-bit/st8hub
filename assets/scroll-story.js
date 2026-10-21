/* Story scenes autoplay on a timer once they enter the viewport; no scroll pinning. Only transforms and opacity change. */
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
  var DUR = [3000, 2400, 2000];
  var state = { p1: 0, p2: 0, p3: 0 };
  var inView = [false, false, false];
  var t0 = [0, 0, 0];
  var done = [false, false, false];
  var raf = 0;
  function clamp(x) { return Math.max(0, Math.min(1, x)); }
  function render() {
    var reduced = reduce.matches;
    var p = reduced ? 1 : state.p1;
    tickets.forEach(function (ticket, index) {
      var shown = reduced ? 1 : clamp((p * 1.15 - index / tickets.length * .9 - .04) / .22);
      ticket.style.opacity = String(shown);
      ticket.style.transform = 'translateY(' + (-(1 - shown) * 34) + 'px)';
      ticket.style.setProperty('--ss-marker', clamp((shown - .5) / .5));
      if (steps[index]) steps[index].style.opacity = String(.65 + .35 * shown);
    });
    receipt.style.transform = reduced ? 'none' : 'rotate(2.2deg) translateY(' + (clamp(p) * 8) + 'px)';
    var selected = Math.min(industries.length - 1, Math.floor(state.p2 * industries.length));
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
    p = reduced ? 1 : state.p3;
    words.forEach(function (word, index) {
      word.style.setProperty('--ss-lit', reduced ? 1 : clamp(p * 1.25 * words.length - index));
    });
  }
  function tick(now) {
    raf = 0;
    if (document.hidden || reduce.matches) return;
    var active = false;
    if (inView[0] && !done[0]) { if (!t0[0]) t0[0] = now; state.p1 = clamp((now - t0[0]) / DUR[0]); done[0] = state.p1 >= 1; active = active || !done[0]; }
    if (inView[2] && !done[2]) { if (!t0[2]) t0[2] = now; state.p3 = clamp((now - t0[2]) / DUR[2]); done[2] = state.p3 >= 1; active = active || !done[2]; }
    if (inView[1]) {
      if (!t0[1]) t0[1] = now;
      var n = industries.length;
      state.p2 = (Math.floor((now - t0[1]) / DUR[1]) % n + .01) / n;
      active = true;
    }
    render();
    if (active) raf = requestAnimationFrame(tick);
  }
  function schedule() { if (!raf && !document.hidden && !reduce.matches) raf = requestAnimationFrame(tick); }
  function motionChanged() { root.classList.toggle('ss-motion', !reduce.matches); schedule(); }
  document.addEventListener('visibilitychange', schedule);
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var i = scenes.indexOf(entry.target);
        if (i < 0) return;
        if (entry.isIntersecting && !inView[i]) t0[i] = 0;
        inView[i] = entry.isIntersecting;
      });
      schedule();
    }, { threshold: 0.3 });
    scenes.forEach(function (scene) { io.observe(scene); });
  } else { state.p1 = state.p2 = state.p3 = 1; }
  if (reduce.addEventListener) reduce.addEventListener('change', motionChanged);
  else reduce.addListener(motionChanged);
  root.classList.toggle('ss-motion', !reduce.matches);
  render();
})();
