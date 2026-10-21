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
  var backdrops = Array.prototype.slice.call(root.querySelectorAll('.ss-bg'));
  var dots = Array.prototype.slice.call(root.querySelectorAll('.ss-dots i'));
  // Backdrop photos start loading right after the page itself has loaded, so they are ready long before the scene is reached.
  function loadBg(bg) { if (bg && bg.dataset.bg) { bg.style.backgroundImage = 'url(' + bg.dataset.bg + ')'; delete bg.dataset.bg; } }
  function loadAll() { backdrops.forEach(loadBg); }
  if (document.readyState === 'complete') loadAll(); else window.addEventListener('load', loadAll, { once: true });
  var bgScene = root.querySelector('#story-scene-2');
  if (bgScene && 'IntersectionObserver' in window) {
    var bgIo = new IntersectionObserver(function (e) { if (e[0].isIntersecting) { loadAll(); bgIo.disconnect(); } }, { rootMargin: '1500px 0px' });
    bgIo.observe(bgScene);
  }

  var words = Array.prototype.slice.call(root.querySelectorAll('.ss-word'));
  var DUR = [3000, 2400, 2000];
  var state = { p1: 0, p2: 0, p3: 0 };
  var inView = [false, false, false];
  var t0 = [0, 0, 0];
  var done = [false, false, false];
  var raf = 0;
  var paused = false, pausedAt = 0;
  function clamp(x) { return Math.max(0, Math.min(1, x)); }
  function render() {
    var reduced = reduce.matches;
    var p = reduced ? 1 : state.p1;
    tickets.forEach(function (ticket, index) {
      var raw = reduced ? 1 : clamp((p * 1.15 - index / tickets.length * .9 - .04) / .22);
      var shown = reduced ? 1 : 1 - Math.pow(1 - raw, 3);
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
      paper.classList.toggle('ss-click', visible);
      paper.tabIndex = visible ? 0 : -1;
      paper.setAttribute('aria-hidden', String(!visible));
      paper.style.transform = reduced ? 'none' : 'translateY(-50%) rotate(3deg) translateY(' + (visible ? 0 : 36) + 'px) scale(' + (visible ? 1 : .97) + ')';
    });
    backdrops.forEach(function (bg, index) { bg.classList.toggle('ss-on', index === selected); });
    dots.forEach(function (dot, index) { dot.style.opacity = index <= selected || reduced ? '1' : '.2'; });
    p = reduced ? 1 : state.p3;
    words.forEach(function (word, index) {
      word.style.setProperty('--ss-lit', reduced ? 1 : clamp(p * 1.25 * words.length - index));
    });
  }
  function tick(now) {
    raf = 0;
    if (document.hidden || reduce.matches || paused) return;
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

  /* Detail card: clicking a notebook explains it and offers the lead form. */
  var modal = document.getElementById('storyModal');
  var lastFocus = null, current = null;
  function openCard(data, trigger) {
    if (!modal) return;
    current = data; lastFocus = trigger || document.activeElement;
    document.getElementById('storyModalKick').textContent = data.kick;
    document.getElementById('storyModalTitle').textContent = data.title;
    document.getElementById('storyModalText').textContent = data.text;
    var list = document.getElementById('storyModalList'); list.innerHTML = '';
    data.rows.forEach(function (row) { var li = document.createElement('li'); li.innerHTML = '<span></span><b></b>'; li.firstChild.textContent = row[0]; li.lastChild.textContent = row[1]; list.appendChild(li); });
    document.getElementById('storyModalFoot').textContent = data.foot || '';
    modal.hidden = false; paused = true; pausedAt = performance.now();
    document.getElementById('storyModalCta').focus();
  }
  function closeCard(restore) {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    if (paused) { t0[1] += performance.now() - pausedAt; paused = false; schedule(); }
    if (restore !== false && lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  function industryData(i) {
    var big = industries[i];
    return {
      kick: 'Отрасль',
      title: big.querySelector('h3').textContent,
      text: big.querySelector('p').textContent,
      rows: Array.prototype.map.call(big.querySelectorAll('.ss-row span'), function (s) { return [s.lastChild.textContent.trim(), s.querySelector('b').textContent]; }).concat([[ 'Главный показатель', big.querySelector('.ss-num').textContent ]]),
      foot: '* Результаты приведены по конкретным проектам и не являются гарантией одинакового результата для другого бизнеса.',
      lead: 'Интересует автоматизация: ' + big.querySelector('h3').textContent
    };
  }
  var tapeData = {
    kick: 'Как это работает',
    title: 'Цифровой администратор 24/7',
    text: 'Каждое действие фиксируется в ленте: бронь, закупка, отзыв, замена поставщика. Вы видите, что сделала система, и подтверждаете то, что важно. Мы начинаем с одного процесса на одной точке.',
    rows: [['19:12 гость', 'бронь принята'], ['21:40 склад', 'закупка собрана'], ['09:20 отзыв', 'ответ готов'], ['12:30 поставщик', 'замена предложена']],
    foot: 'Иллюстративный сценарий. Данные условные.',
    lead: 'Интересует цифровой администратор 24/7'
  };
  function activate(el, fn) {
    el.addEventListener('click', fn);
    el.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } });
  }
  function selectedIndex() { for (var i = 0; i < industries.length; i++) if (industries[i].style.opacity === '1') return i; return 0; }
  if (modal) {
    if (receipt) activate(receipt, function () { openCard(tapeData, receipt); });
    papers.forEach(function (paper, i) { paper.setAttribute('role', 'button'); paper.setAttribute('aria-haspopup', 'dialog'); activate(paper, function () { if (paper.classList.contains('ss-click') || reduce.matches) openCard(industryData(i), paper); }); });
    var more = document.getElementById('ss-more');
    if (more) more.addEventListener('click', function () { openCard(industryData(selectedIndex()), more); });
    document.getElementById('storyModalClose').addEventListener('click', function () { closeCard(); });
    document.getElementById('storyModalSkip').addEventListener('click', function () { closeCard(); });
    modal.addEventListener('click', function (e) { if (e.target === modal) closeCard(); });
    document.addEventListener('keydown', function (e) {
      if (modal.hidden) return;
      if (e.key === 'Escape') closeCard();
      else if (e.key === 'Tab') {
        var f = modal.querySelectorAll('button'); var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    document.getElementById('storyModalCta').addEventListener('click', function () {
      var lead = current && current.lead;
      closeCard(false);
      if (typeof openLeadForm === 'function') {
        openLeadForm();
        var msg = document.getElementById('leadMessage');
        if (msg && lead) { msg.value = lead + ' (с главной страницы)'; msg.dispatchEvent(new Event('input', { bubbles: true })); }
      }
    });
  }
  root.classList.toggle('ss-motion', !reduce.matches);
  render();
})();
