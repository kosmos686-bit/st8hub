/* Reuses the existing public Web3Forms access key; no server credentials. */
(function () {
  'use strict';
  var PUBLIC_FORM_ACCESS_KEY = "97c53ebb-40b7-4389-ad3c-09d8fc6f6fdc";
  var modal = document.getElementById('leadFormModal');
  if (!modal) return;
  var form = document.getElementById('leadForm');
  var submit = document.getElementById('leadSubmitBtn');
  var consent = document.getElementById('leadConsent');
  var step = document.getElementById('leadFormStep1');
  var success = document.getElementById('leadFormSuccess');
  var error = document.getElementById('leadFormError');
  var focusBefore = null;
  var overflowBefore = '';
  var sending = false;

  function open() {
    if (!modal.hidden) return;
    focusBefore = document.activeElement;
    overflowBefore = document.body.style.overflow;
    form.reset();
    step.hidden = false;
    success.hidden = true;
    error.hidden = true;
    submit.disabled = true;
    sending = false;
    document.getElementById('leadMessage').value = document.title + '\n' + location.origin + location.pathname;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('leadName').focus();
  }

  function close() {
    // Keep an in-flight request in view rather than enabling an accidental resend.
    if (sending) return;
    modal.hidden = true;
    document.body.style.overflow = overflowBefore;
    if (focusBefore) focusBefore.focus();
  }

  document.addEventListener('click', function (event) {
    if (event.target.closest('[data-open-lead]')) open();
    else if (event.target.closest('[data-close-lead]') || event.target === modal) close();
  });
  consent.addEventListener('change', function () { submit.disabled = sending || !consent.checked; });
  document.addEventListener('keydown', function (event) {
    if (modal.hidden) return;
    if (event.key === 'Escape') close();
    if (event.key !== 'Tab') return;
    var items = Array.from(modal.querySelectorAll('a[href],button:not([disabled]),input:not([type="hidden"]),textarea'))
      .filter(function (item) { return item.getClientRects().length; });
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (sending || !form.reportValidity()) return;
    sending = true;
    submit.disabled = true;
    var data = new FormData(form);
    data.append('access_key', PUBLIC_FORM_ACCESS_KEY);
    data.append('subject', 'ST8 AI international enquiry: ' + document.title);
    data.append('from_name', 'ST8 AI Website');
    var controller = new AbortController();
    var timeout = setTimeout(function () { controller.abort(); }, 20000);
    fetch('https://api.web3forms.com/submit', {
      method: 'POST', headers: { Accept: 'application/json' }, body: data, signal: controller.signal
    }).then(function (response) {
      if (!response.ok) throw new Error('Submission not confirmed');
      return response.json();
    }).then(function (result) {
      if (!result || result.success !== true) throw new Error('Submission not confirmed');
      step.hidden = true;
      success.hidden = false;
      success.focus();
      try { if (typeof ym === 'function') ym(112836376, 'reachGoal', 'lead_form'); } catch (_) {}
      try { if (typeof gtag === 'function') gtag('event', 'generate_lead', { form_id: 'lead_form', method: 'form' }); } catch (_) {}
    }).catch(function () {
      step.hidden = true;
      error.hidden = false;
      error.focus();
    }).finally(function () { clearTimeout(timeout); sending = false; });
  });
})();
