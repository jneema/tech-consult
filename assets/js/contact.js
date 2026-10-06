/* Corbel — contact page: tabs, multi-step brief, call booking with calendar file. */
(function () {
  const { $, $$, store, esc, toast, reduced } = window.Corbel;
  const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const makeRef = () => 'CRB-' + (1000 + Math.floor(Math.random() * 9000));
  const TICK = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

  /* ---------- Tabs ---------- */
  const tabs = $$('[role=tab]');
  function selectTab(tab, focus) {
    tabs.forEach(t => {
      const on = t === tab;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      $('#' + t.getAttribute('aria-controls')).hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => {
      selectTab(t);
      history.replaceState(null, '', t.id === 'tab-call' ? '#call' : location.pathname + location.search);
    });
    t.addEventListener('keydown', e => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      selectTab(tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length], true);
    });
  });
  const showCall = () => { selectTab($('#tab-call')); };
  if (location.hash === '#call') showCall();
  addEventListener('hashchange', () => { if (location.hash === '#call') showCall(); });

  /* ---------- Field helpers ---------- */
  function check(input, ok, msg) {
    const f = input.closest('.field');
    f.classList.toggle('invalid', !ok);
    f.querySelector('.err').textContent = ok ? '' : msg;
    input.setAttribute('aria-invalid', !ok);
    return ok;
  }

  /* ---------- Brief ---------- */
  const form = $('#briefForm');
  const steps = $$('.form-step', form);
  const NAMES = ['Your project', 'Budget and timing', 'About you'];
  let step = 1;

  function goTo(n) {
    step = n;
    steps.forEach(s => { s.hidden = +s.dataset.step !== n; });
    $$('.progress span', form).forEach((b, i) => b.classList.toggle('on', i < n));
    $('#stepName').textContent = NAMES[n - 1];
    $('#stepCount').textContent = `Step ${n} of ${steps.length}`;
    $('#briefBack').hidden = n === 1;
    $('#briefNext').hidden = n === steps.length;
    $('#briefSubmit').hidden = n !== steps.length;
    const top = form.closest('.panel').getBoundingClientRect().top;
    if (top < 0) form.closest('.panel').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
    const first = steps[n - 1].querySelector('input, select, textarea');
    if (first) first.focus({ preventScroll: true });
  }

  function validStep(n) {
    if (n === 1) {
      const ok = $$('[name=services]:checked', form).length > 0;
      $('#servicesErr').textContent = ok ? '' : 'Choose at least one, or pick the closest match.';
      if (!ok) $('[name=services]', form).focus();
      return ok;
    }
    if (n === 2) {
      const ok = !!$('[name=budget]:checked', form);
      $('#budgetErr').textContent = ok ? '' : 'Choose a range, or "Not sure yet".';
      if (!ok) $('[name=budget]', form).focus();
      return ok;
    }
    const results = [
      check($('#bName'), $('#bName').value.trim().length > 1, 'Enter your name.'),
      check($('#bEmail'), EMAIL.test($('#bEmail').value.trim()), 'Enter an email address like name@company.com.'),
      check($('#bMessage'), $('#bMessage').value.trim().length >= 20, 'A sentence or two is enough. At least 20 characters.')
    ];
    const bad = $('.field.invalid input, .field.invalid textarea', form);
    if (bad) bad.focus();
    return results.every(Boolean);
  }

  $('#briefNext').addEventListener('click', () => { if (validStep(step)) goTo(step + 1); });
  $('#briefBack').addEventListener('click', () => goTo(step - 1));
  form.addEventListener('change', e => {
    if (e.target.name === 'services') $('#servicesErr').textContent = '';
    if (e.target.name === 'budget') $('#budgetErr').textContent = '';
  });
  form.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT' && step < steps.length) {
      e.preventDefault();
      $('#briefNext').click();
    }
  });

  // Prefill from links elsewhere on the site
  const SVC = { software: 'Software development', web: 'Web development', integrations: 'Integrations', cloud: 'Cloud solutions', more: 'Design or data' };
  const tick = v => { const i = form.querySelector(`[name=services][value="${v}"]`); if (i) i.checked = true; };
  const params = new URLSearchParams(location.search);
  const notes = [];
  if (SVC[params.get('service')]) tick(SVC[params.get('service')]);
  const MODEL = { fixed: 'Fixed scope project', team: 'Dedicated team', support: 'Support retainer' };
  if (MODEL[params.get('model')]) {
    notes.push(`Interested in: ${MODEL[params.get('model')]}.`);
    if (params.get('model') === 'support') tick('Consulting or support');
  }
  const ref = window.CORBEL.cases.find(c => c.id === params.get('ref'));
  if (ref) notes.push(`Something similar to the ${ref.client} project.`);
  const est = store.session.get('corbel-estimate', null);
  if (est) {
    if (SVC[est.svc]) tick(SVC[est.svc]);
    const b = form.querySelector(`[name=budget][value="${est.budget}"]`);
    if (b) b.checked = true;
    notes.push(est.summary);
    store.session.del('corbel-estimate');
    toast('Your estimate has been added to the brief');
  }
  if (notes.length) $('#bMessage').value = notes.join('\n') + '\n\n';

  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!validStep(3)) return;
    const data = new FormData(form);
    const brief = {
      ref: makeRef(),
      services: data.getAll('services'),
      stage: data.get('stage'), budget: data.get('budget'), timing: data.get('timing'),
      name: data.get('name').trim(), email: data.get('email').trim(), company: data.get('company').trim(),
      phone: data.get('phone').trim(), message: data.get('message').trim(), source: data.get('source'),
      nda: !!data.get('nda'), created: new Date().toISOString()
    };
    // Prototype: kept in the browser. Replace with a POST to your CRM or form endpoint.
    const all = store.get('corbel-briefs', []);
    all.push(brief);
    store.set('corbel-briefs', all);

    $('#panel-brief').innerHTML = `<div class="success" tabindex="-1" id="briefDone">
        <div class="tick">${TICK}</div>
        <h3>Thanks, ${esc(brief.name.split(' ')[0])}. Your brief is with us.</h3>
        <p>A technical lead will reply to ${esc(brief.email)} within one business day${brief.nda ? ', with a mutual NDA attached' : ''}. Quote this reference if you get in touch before then:</p>
        <p class="ref">${brief.ref}</p>
        <div class="actions">
          <button class="btn btn-primary" type="button" id="toCall">Book a call now</button>
          <a class="btn btn-outline" href="work.html">Browse case studies</a>
        </div></div>`;
    $('#briefDone').focus();
    $('#toCall').addEventListener('click', () => { showCall(); $('#cName').value = brief.name; $('#cEmail').value = brief.email; });
  });

  /* ---------- Call booking ---------- */
  const TIMES = ['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00'];
  const days = [];
  { const d = new Date(); d.setHours(0, 0, 0, 0); while (days.length < 10) { d.setDate(d.getDate() + 1); if (d.getDay() % 6 !== 0) days.push(new Date(d)); } }
  const taken = (d, t) => ((d.getDate() * 7 + TIMES.indexOf(t) * 13) % 5) === 0;
  const toUTC = (d, t) => new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate(), +t.slice(0, 2) - 3, 0));
  const local = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' });
  const longDay = new Intl.DateTimeFormat('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
  const shortDay = new Intl.DateTimeFormat('en-GB', { weekday: 'short' });
  const offsetDiffers = new Date().getTimezoneOffset() !== -180;
  if (offsetDiffers) $('#localHint').textContent = '. Your local time is shown when you pick a slot.';

  let selDay = 0, selTime = null;
  const daysEl = $('#days'), slotsEl = $('#slots');
  daysEl.innerHTML = days.map((d, i) => `<button type="button" class="day" data-i="${i}" aria-pressed="${i === 0}" aria-label="${longDay.format(d)}"><small>${shortDay.format(d)}</small><b>${d.getDate()}</b></button>`).join('');
  daysEl.addEventListener('click', e => {
    const b = e.target.closest('.day');
    if (!b) return;
    selDay = +b.dataset.i; selTime = null;
    [...daysEl.children].forEach(x => x.setAttribute('aria-pressed', x === b));
    renderSlots();
  });
  function renderSlots() {
    const d = days[selDay];
    slotsEl.innerHTML = TIMES.map(t => {
      const x = taken(d, t);
      return `<button type="button" class="slot" data-t="${t}"${x ? ` disabled aria-label="${t}, unavailable"` : ''} aria-pressed="${t === selTime}">${t}</button>`;
    }).join('');
    $('#picked').innerHTML = selTime
      ? `<b>${longDay.format(d)} at ${selTime} EAT</b>, 30 minutes${offsetDiffers ? ` (${local.format(toUTC(d, selTime))} your time)` : ''}`
      : 'No time selected yet.';
  }
  slotsEl.addEventListener('click', e => {
    const b = e.target.closest('.slot');
    if (!b || b.disabled) return;
    selTime = b.dataset.t;
    renderSlots();
    slotsEl.querySelector(`[data-t="${selTime}"]`).focus();
  });
  renderSlots();

  const SVC_TOPIC = { software: 'Software development', web: 'Web development', integrations: 'Integrations', cloud: 'Cloud solutions', more: 'Design, data or support' };
  if (SVC_TOPIC[params.get('service')]) $('#cTopic').value = SVC_TOPIC[params.get('service')];

  function icsFile(rec) {
    const stamp = d => d.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    const start = new Date(rec.startUTC), end = new Date(start.getTime() + 30 * 60000);
    return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Corbel//Discovery call//EN', 'BEGIN:VEVENT',
      `UID:${rec.ref}@corbel.example`, `DTSTAMP:${stamp(new Date())}`, `DTSTART:${stamp(start)}`, `DTEND:${stamp(end)}`,
      'SUMMARY:Discovery call with Corbel',
      `DESCRIPTION:Topic: ${rec.topic}. Reference ${rec.ref}. A meeting link will follow by email.`,
      'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
  }

  $('#callForm').addEventListener('submit', e => {
    e.preventDefault();
    const ok = [
      check($('#cName'), $('#cName').value.trim().length > 1, 'Enter your name.'),
      check($('#cEmail'), EMAIL.test($('#cEmail').value.trim()), 'Enter an email address like name@company.com.'),
      check($('#cTopic'), !!$('#cTopic').value, 'Choose a topic so we can bring the right lead.')
    ].every(Boolean);
    if (!selTime) {
      toast('Choose a time for your call first.');
      slotsEl.scrollIntoView({ block: 'center', behavior: reduced ? 'auto' : 'smooth' });
      return;
    }
    if (!ok) { $('#callForm .field.invalid input, #callForm .field.invalid select').focus(); return; }

    const d = days[selDay];
    const rec = {
      ref: makeRef(), name: $('#cName').value.trim(), email: $('#cEmail').value.trim(), topic: $('#cTopic').value,
      when: `${longDay.format(d)} at ${selTime} EAT`, startUTC: toUTC(d, selTime).toISOString(), created: new Date().toISOString()
    };
    const all = store.get('corbel-calls', []);
    all.push(rec);
    store.set('corbel-calls', all);

    $('#panel-call').innerHTML = `<div class="success" tabindex="-1" id="callDone">
        <div class="tick">${TICK}</div>
        <h3>Call booked for ${esc(rec.when)}</h3>
        <p>Thanks, ${esc(rec.name.split(' ')[0])}. A calendar invite with a meeting link is on its way to ${esc(rec.email)}. Your reference:</p>
        <p class="ref">${rec.ref}</p>
        <div class="actions">
          <button class="btn btn-primary" type="button" id="icsBtn">Add to calendar</button>
          <a class="btn btn-outline" href="estimate.html">Estimate your project</a>
        </div></div>`;
    $('#callDone').focus();
    $('#icsBtn').addEventListener('click', () => {
      const url = URL.createObjectURL(new Blob([icsFile(rec)], { type: 'text/calendar' }));
      const a = Object.assign(document.createElement('a'), { href: url, download: `corbel-call-${rec.ref}.ics` });
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  });
})();
