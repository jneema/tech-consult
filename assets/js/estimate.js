/* Corbel — project estimator. */
(function () {
  const { $, $$, store } = window.Corbel;

  const TYPES = [
    { v: 'software', b: 'Custom software', base: 18000, w: 12 },
    { v: 'mobile', b: 'Mobile app', base: 22000, w: 14 },
    { v: 'web', b: 'Website or portal', base: 9000, w: 7 },
    { v: 'integrations', b: 'Integration', base: 7000, w: 6 },
    { v: 'cloud', b: 'Cloud migration', base: 8000, w: 6 },
    { v: 'data', b: 'Data and dashboards', base: 10000, w: 8 }
  ];
  const SIZES = [
    { v: 's', b: 'Small', s: 'A focused tool or a handful of screens', m: 1, w: 1 },
    { v: 'm', b: 'Medium', s: 'Several user roles and workflows', m: 1.9, w: 1.6 },
    { v: 'l', b: 'Large', s: 'Many modules and complex rules', m: 3.4, w: 2.5 }
  ];
  const EXTRAS = [
    { v: 'design', b: 'UX and visual design', s: 'Research, wireframes, interface', c: 4500, w: 2 },
    { v: 'admin', b: 'Admin dashboard', s: 'Manage users and content', c: 5000, w: 1.5 },
    { v: 'pay', b: 'Online payments', s: 'Cards and mobile money', c: 3500, w: 1 },
    { v: 'i18n', b: 'Multiple languages', s: 'Translation-ready interface', c: 2000, w: 0.5 }
  ];
  const PACE = [
    { v: 'std', b: 'Standard', s: 'Steady pace, best value', m: 1, w: 1 },
    { v: 'fast', b: 'Accelerated', s: 'Larger team, about 30% sooner', m: 1.22, w: 0.7 }
  ];
  const money = n => '$' + n.toLocaleString('en-US');
  const option = (name, v, b, s, checked, type = 'radio') =>
    `<label class="option"><input type="${type}" name="${name}" value="${v}"${checked ? ' checked' : ''}><span><b>${b}</b><small>${s}</small></span></label>`;

  $('#estType').innerHTML = TYPES.map((t, i) => option('type', t.v, t.b, 'From ' + money(t.base), i === 0)).join('');
  $('#estSize').innerHTML = SIZES.map((s, i) => option('size', s.v, s.b, s.s, i === 1)).join('');
  $('#estExtras').innerHTML = EXTRAS.map((e, i) => option('extra', e.v, e.b, e.s, i === 0, 'checkbox')).join('');
  $('#estPace').innerHTML = PACE.map((p, i) => option('pace', p.v, p.b, p.s, i === 0)).join('');

  const form = $('#estForm');
  const fmtK = n => '$' + (Math.round(n / 500) * 500 / 1000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, '') + 'k';

  function calc() {
    const type = TYPES.find(t => t.v === form.querySelector('[name=type]:checked').value);
    const size = SIZES.find(s => s.v === form.querySelector('[name=size]:checked').value);
    const pace = PACE.find(p => p.v === form.querySelector('[name=pace]:checked').value);
    const ints = +$('#estInt').value;
    const extras = $$('[name=extra]:checked', form).map(i => EXTRAS.find(e => e.v === i.value));

    $('#estIntVal').textContent = ints === 1 ? '1 system' : ints + ' systems';

    const core = type.base * size.m, intC = ints * 2600, exC = extras.reduce((a, e) => a + e.c, 0);
    const total = (core + intC + exC) * pace.m;
    const weeks = (type.w * size.w + ints * 0.8 + extras.reduce((a, e) => a + e.w, 0)) * pace.w;
    const lo = total * 0.87, hi = total * 1.15;
    const wLo = Math.max(3, Math.round(weeks * 0.9)), wHi = Math.round(weeks * 1.2) + 1;
    const eng = Math.max(1, Math.round(size.m * (pace.v === 'fast' ? 1.6 : 1.1)));
    const hasDesign = extras.some(e => e.v === 'design');
    const people = 1 + eng + (hasDesign ? 1 : 0);
    const teamText = ['1 lead', eng + (eng > 1 ? ' engineers' : ' engineer')].concat(hasDesign ? ['1 designer'] : []).join(', ');

    const range = fmtK(lo) + ' – ' + fmtK(hi);
    $('#sumCost').textContent = range;
    $('#sumWeeks').textContent = wLo + '–' + wHi + ' weeks';
    $('#sumTeam').textContent = people + ' people';

    const rows = [[`${type.b} (${size.b.toLowerCase()})`, '~' + fmtK(core * pace.m)]];
    if (ints) rows.push([ints + ' integration' + (ints > 1 ? 's' : ''), '~' + fmtK(intC * pace.m)]);
    extras.forEach(e => rows.push([e.b, '~' + fmtK(e.c * pace.m)]));
    rows.push(['Team', teamText]);
    $('#sumLines').innerHTML = rows.map(([k, v]) => `<li><span>${k}</span><span>${v}</span></li>`).join('');

    const svc = { software: 'software', mobile: 'software', web: 'web', integrations: 'integrations', cloud: 'cloud', data: 'more' }[type.v];
    const budget = hi < 10000 ? 'u10' : hi < 25000 ? '10-25' : hi < 50000 ? '25-50' : hi < 100000 ? '50-100' : '100+';
    return {
      svc, budget,
      summary: `Estimator: ${type.b}, ${size.b.toLowerCase()} size, ${ints} integration${ints === 1 ? '' : 's'}` +
        (extras.length ? ', plus ' + extras.map(e => e.b.toLowerCase()).join(', ') : '') +
        `. ${pace.b} timeline. Estimated ${range} over ${wLo}–${wHi} weeks with ${teamText}.`
    };
  }

  const TYPE_FROM_SERVICE = { software: 'software', web: 'web', integrations: 'integrations', cloud: 'cloud', more: 'data' };
  const wanted = new URLSearchParams(location.search).get('type');
  const pre = wanted && form.querySelector(`[name=type][value="${TYPE_FROM_SERVICE[wanted] || wanted}"]`);
  if (pre) pre.checked = true;

  form.addEventListener('input', calc);
  calc();

  $('#estSend').addEventListener('click', () => store.session.set('corbel-estimate', calc()));
})();
