/* Keep the original desktop loop; phones and reduced-motion use its first frame. */
(function () {
  'use strict';
  // Below-fold typefaces need not compete with the first-screen Inter subsets.
  var siteFonts = document.querySelector('link[data-site-fonts]');
  function enableSiteFonts() { if (siteFonts) siteFonts.rel = 'stylesheet'; }
  if (document.readyState === 'complete') enableSiteFonts();
  else window.addEventListener('load', function () {
    if (window.requestIdleCallback) window.requestIdleCallback(enableSiteFonts, { timeout: 2000 });
    else enableSiteFonts();
  }, { once: true });
  var video = document.querySelector('.hero-video video[data-video-src]');
  if (!video) return;
  var desktop = window.matchMedia('(min-width: 901px)');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  function sync() {
    if (desktop.matches && !reduce.matches) {
      if (!video.hasAttribute('src')) {
        video.poster = video.dataset.poster;
        video.src = video.dataset.videoSrc;
        video.load();
        var playback = video.play();
        if (playback) playback.catch(function () { /* The poster remains visible. */ });
      }
    } else if (video.hasAttribute('src')) {
      video.pause();
      video.removeAttribute('src');
      video.removeAttribute('poster');
      video.classList.remove('is-playing');
      video.load();
    }
  }
  video.addEventListener('playing', function () { video.classList.add('is-playing'); });
  video.addEventListener('error', function () { video.classList.remove('is-playing'); });
  [desktop, reduce].forEach(function (query) {
    if (query.addEventListener) query.addEventListener('change', sync);
    else query.addListener(sync);
  });
  sync();
})();
