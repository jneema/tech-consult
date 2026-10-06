/* Corbel — work page: filters and case study dialog with shareable links. */
(function () {
  const { $, esc, caseCard, serviceName, ARROW } = window.Corbel;
  const { services, cases } = window.CORBEL;

  const params = new URLSearchParams(location.search);
  let svcF = services.some(s => s.id === params.get('service')) ? params.get('service') : 'all';
  let indF = 'all';

  /* ---------- Filters ---------- */
  const chips = $('#svcFilter');
  const opts = [{ id: 'all', name: 'All work' }, ...services.map(s => ({ id: s.id, name: s.id === 'more' ? 'Data and design' : s.name }))];
  chips.innerHTML = opts.map(o => `<button type="button" class="chip" data-f="${o.id}" aria-pressed="${o.id === svcF}">${o.name}</button>`).join('');
  chips.addEventListener('click', e => {
    const b = e.target.closest('[data-f]');
    if (!b) return;
    svcF = b.dataset.f;
    render();
  });

  const indSel = $('#indFilter');
  [...new Set(cases.map(c => c.ind))].sort().forEach(i => indSel.insertAdjacentHTML('beforeend', `<option>${esc(i)}</option>`));
  indSel.addEventListener('change', () => { indF = indSel.value; render(); });

  function render() {
    [...chips.children].forEach(b => b.setAttribute('aria-pressed', b.dataset.f === svcF));
    const list = cases.filter(c => (svcF === 'all' || c.svc === svcF) && (indF === 'all' || c.ind === indF));
    $('#resultCount').textContent = `Showing ${list.length} of ${cases.length} projects`;
    const grid = $('#caseGrid');
    if (!list.length) {
      grid.innerHTML = `<div class="empty-state"><p>No published projects match both filters yet. We have likely done similar work under NDA.</p>
        <button class="btn btn-outline btn-sm" type="button" id="clearFilters">Show all projects</button></div>`;
      $('#clearFilters').addEventListener('click', () => { svcF = 'all'; indF = 'all'; indSel.value = 'all'; render(); });
      return;
    }
    grid.innerHTML = list.map(caseCard).join('');
  }
  render();

  /* ---------- Dialog ---------- */
  const dialog = $('#caseDialog');
  let opener = null;

  function open(id) {
    const c = cases.find(x => x.id === id);
    if (!c) return;
    $('#caseKicker').textContent = `${c.client} · ${c.ind} · ${c.year}`;
    $('#caseBody').innerHTML = `
      <h2 id="caseTitle">${esc(c.title)}</h2>
      <div class="dialog-stats">${c.stats.map(([a, b]) => `<div><b>${esc(a)}</b><span>${esc(b)}</span></div>`).join('')}</div>
      <h3>The problem</h3><p>${esc(c.problem)}</p>
      <h3>What we built</h3><p>${esc(c.approach)}</p>
      <h3>Service</h3><p>${esc(serviceName(c.svc))}</p>
      <h3>Built with</h3><ul class="tags">${c.stack.map(t => `<li class="tag">${esc(t)}</li>`).join('')}</ul>
      ${c.quote ? `<blockquote class="dialog-quote"><p>“${esc(c.quote.text)}”</p><footer>${esc(c.quote.who)}, ${esc(c.quote.role)}</footer></blockquote>` : ''}
      <div class="dialog-actions">
        <a class="btn btn-accent" href="contact.html?service=${c.svc}&ref=${c.id}">Discuss a similar project ${ARROW}</a>
        <button class="btn btn-outline" type="button" id="copyLink">Copy link</button>
      </div>`;
    $('#copyLink').addEventListener('click', () => {
      const url = location.origin + location.pathname + '#' + c.id;
      (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject())
        .then(() => window.Corbel.toast('Link copied'), () => window.Corbel.toast('Copy failed. Use the address bar instead.'));
    });
    if (!dialog.open) {
      dialog.showModal();
      document.body.classList.add('dialog-open');
    }
    dialog.scrollTop = 0;
    if (location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
  }

  function close() { if (dialog.open) dialog.close(); }
  dialog.addEventListener('close', () => {
    document.body.classList.remove('dialog-open');
    history.replaceState(null, '', location.pathname + location.search);
    if (opener) opener.focus();
  });
  $('#caseClose').addEventListener('click', close);
  dialog.addEventListener('click', e => { if (e.target === dialog) close(); });

  $('#caseGrid').addEventListener('click', e => {
    const a = e.target.closest('[data-case]');
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    opener = a;
    open(a.dataset.case);
  });

  const fromHash = () => { const id = location.hash.slice(1); if (cases.some(c => c.id === id)) open(id); };
  addEventListener('hashchange', fromHash);
  fromHash();
})();
