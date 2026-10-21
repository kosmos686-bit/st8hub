/* Accessible tabs are scoped to industries; the FAQ keeps its existing accordion. */
(function () {
  'use strict';
  var section = document.getElementById('solutions');
  if (!section) return;
  var tabs = Array.prototype.slice.call(section.querySelectorAll('[role="tab"]'));
  var panels = Array.prototype.slice.call(section.querySelectorAll('[role="tabpanel"]'));
  if (!tabs.length) return;
  function selectTab(tab, focus) {
    tabs.forEach(function (item) {
      var selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
    });
    panels.forEach(function (panel) { panel.hidden = panel.id !== tab.getAttribute('aria-controls'); });
    if (focus) tab.focus({ preventScroll: true });
  }
  tabs.forEach(function (tab, index) {
    tab.addEventListener('click', function () { selectTab(tab, false); });
    tab.addEventListener('keydown', function (event) {
      var next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      selectTab(tabs[next], true);
    });
  });
})();
