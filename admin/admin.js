/* Corbel admin — inbox for website enquiries, and posting case studies and job openings.
   Talks to server.py. Each save rewrites a file in build/content and rebuilds the site.
   Page wording, layout and service pages are changed by developers in code, not here. */
(function () {
  const $ = (s, r = document) => r.querySelector(s);

  /* ---------- Tiny DOM helper: never uses innerHTML for data ---------- */
  function h(tag, props, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else if (k in el && k !== 'list' && k !== 'form') el[k] = v;
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid);
    return el;
  }
  const ICON = {
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    up: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 15l6-6 6 6"/></svg>',
    down: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
  };
  const icon = (name, label) => {
    const b = h('button', { type: 'button', class: 'icon-btn', 'aria-label': label, title: label });
    b.innerHTML = ICON[name];   // static markup only
    return b;
  };

  const toast = msg => {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._h);
    t._h = setTimeout(() => t.classList.remove('show'), 3200);
  };

  /* ---------- API ---------- */
  async function api(method, path, body) {
    const res = await fetch(path, {
      method, credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-Corbel-Admin': '1' },
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 && path !== '/api/login') { showLogin(); throw new Error('Your session has ended. Please sign in again.'); }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status}).`);
    return data;
  }

  /* ---------- Theme (shared with the site) ---------- */
  document.querySelectorAll('[data-theme-toggle]').forEach(b => b.addEventListener('click', () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('corbel-theme', root.dataset.theme); } catch (e) {}
  }));

  /* ---------- Build status ---------- */
  let build = {};
  const ago = iso => {
    if (!iso) return '';
    const s = (Date.now() - new Date(iso)) / 1000;
    if (s < 60) return 'just now';
    if (s < 3600) return Math.round(s / 60) + ' min ago';
    if (s < 86400) return Math.round(s / 3600) + ' h ago';
    return new Date(iso).toLocaleDateString();
  };
  function setBuild(b, busy) {
    if (b) build = b;
    const el = $('#buildStatus');
    el.className = 'status' + (busy ? ' busy' : build.ok === false ? ' fail' : build.ok ? ' ok' : '');
    el.textContent = busy ? 'Publishing…' : build.ok === false ? 'Build failed: view log' : build.at ? 'Site published ' + ago(build.at) : 'Not built yet';
  }
  setInterval(() => setBuild(), 30000);
  $('#buildStatus').addEventListener('click', () => {
    $('#logText').textContent = build.log || 'No build output yet.';
    $('#logDialog').showModal();
  });
  $('#logDialog [data-close]').addEventListener('click', () => $('#logDialog').close());
  function afterSave(res) {
    setBuild(res.build);
    if (res.build && res.build.ok === false) {
      toast('Saved, but the site did not rebuild. See the log.');
      $('#buildStatus').click();
    } else toast('Saved and published');
  }

  /* ---------- Sign in / out ---------- */
  function showLogin() {
    $('#app').hidden = true;
    $('#login').hidden = false;
    $('#password').focus();
  }
  $('#loginForm').addEventListener('submit', async e => {
    e.preventDefault();
    $('#loginErr').textContent = '';
    try {
      await api('POST', '/api/login', { password: $('#password').value });
      $('#password').value = '';
      start();
    } catch (err) { $('#loginErr').textContent = err.message; }
  });
  $('#logout').addEventListener('click', async () => {
    if (!(await confirmLeave())) return;
    await api('POST', '/api/logout').catch(() => {});
    dirtyCheck = null;
    showLogin();
  });

  /* ---------- Routing with an unsaved-changes guard ---------- */
  let dirtyCheck = null;     // set by the active editor: returns true when there are unsaved edits
  let currentView = null;
  const confirmLeave = async () => !(dirtyCheck && dirtyCheck()) || confirm('You have unsaved changes. Leave without saving?');
  addEventListener('beforeunload', e => { if (dirtyCheck && dirtyCheck()) { e.preventDefault(); e.returnValue = ''; } });

  const VIEWS = {
    inbox: ['Inbox', viewInbox],
    cases: ['Case studies', viewCases],
    roles: ['Careers', viewRoles]
  };
  async function route() {
    const name = (location.hash.slice(1) || 'inbox');
    const [title, fn] = VIEWS[name] || VIEWS.inbox;
    if (currentView && currentView !== name && !(await confirmLeave())) {
      history.replaceState(null, '', '#' + currentView);
      return;
    }
    currentView = name in VIEWS ? name : 'inbox';
    dirtyCheck = null;
    document.querySelectorAll('.side-nav a').forEach(a => a.toggleAttribute('aria-current', a.dataset.view === currentView));
    document.querySelectorAll('.side-nav a[aria-current]').forEach(a => a.setAttribute('aria-current', 'page'));
    $('#viewTitle').textContent = title;
    document.title = title + ' · Corbel admin';
    const root = $('#view');
    root.replaceChildren(h('p', { class: 'muted' }, 'Loading…'));
    try { await fn(root); } catch (err) { root.replaceChildren(h('p', { class: 'empty' }, err.message)); }
  }
  addEventListener('hashchange', route);

  async function start() {
    const s = await api('GET', '/api/session');
    if (!s.admin) return showLogin();
    $('#login').hidden = true;
    $('#app').hidden = false;
    setBuild(s.build);
    refreshCount();
    route();
  }

  /* =====================================================================
     Inbox
     ===================================================================== */
  const STATUSES = ['new', 'contacted', 'proposal', 'won', 'lost', 'archived'];
  const BUDGET = { u10: 'Under $10k', '10-25': '$10k – $25k', '25-50': '$25k – $50k', '50-100': '$50k – $100k', '100+': '$100k+', unsure: 'Not sure yet' };
  const KIND = { brief: 'Project brief', call: 'Call booking', newsletter: 'Newsletter' };
  const fmtDate = iso => new Date(iso).toLocaleString(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

  async function refreshCount(list) {
    try {
      const subs = list || await api('GET', '/api/submissions');
      const n = subs.filter(s => s.status === 'new' && s.type !== 'newsletter').length;
      const c = $('#newCount');
      c.hidden = !n;
      c.textContent = n;
    } catch (e) { /* count is cosmetic */ }
  }

  async function viewInbox(root) {
    let subs = (await api('GET', '/api/submissions')).sort((a, b) => b.created.localeCompare(a.created));
    let type = 'all', status = 'active', q = '', selected = null;

    const title = s => s.type === 'newsletter' ? s.email : s.name + (s.company ? ' · ' + s.company : '');
    const meta = s => s.type === 'brief' ? [s.services.join(', '), BUDGET[s.budget]].filter(Boolean).join(' · ')
      : s.type === 'call' ? `${s.when} · ${s.topic}` : 'Newsletter signup';
    const visible = () => subs.filter(s =>
      (type === 'all' || s.type === type) &&
      (status === 'all' || (status === 'active' ? !['lost', 'archived'].includes(s.status) : s.status === status)) &&
      (!q || JSON.stringify(s).toLowerCase().includes(q)));

    const chips = h('div', { class: 'chips', role: 'group', 'aria-label': 'Type' },
      [['all', 'All'], ['brief', 'Briefs'], ['call', 'Calls'], ['newsletter', 'Newsletter']].map(([v, l]) =>
        h('button', { type: 'button', class: 'chip', 'aria-pressed': String(v === type), onclick: () => { type = v; draw(); } }, l)));
    const statusSel = h('select', { 'aria-label': 'Status', onchange: e => { status = e.target.value; draw(); } },
      h('option', { value: 'active' }, 'Open'), h('option', { value: 'all' }, 'All statuses'),
      STATUSES.map(s => h('option', { value: s }, s[0].toUpperCase() + s.slice(1))));
    const search = h('input', { type: 'search', placeholder: 'Search name, email, message…', 'aria-label': 'Search', oninput: e => { q = e.target.value.toLowerCase(); draw(); } });
    const exportBtn = h('button', { type: 'button', class: 'btn btn-outline', onclick: () => exportCsv(visible()) }, 'Export CSV');
    const list = h('ul', { class: 'rows panel-box' });
    const detail = h('div', { class: 'detail panel-box', hidden: true });

    root.replaceChildren(
      h('div', { class: 'toolbar' }, chips, statusSel, h('div', { class: 'grow' }, search), exportBtn),
      h('div', { class: 'inbox' }, list, detail));
    const layout = list.parentElement;

    function draw() {
      [...chips.children].forEach(b => b.setAttribute('aria-pressed', String(b.textContent === { all: 'All', brief: 'Briefs', call: 'Calls', newsletter: 'Newsletter' }[type])));
      const items = visible();
      if (!subs.length) {
        list.replaceChildren(h('li', { class: 'empty' }, 'Nothing yet. Briefs, call bookings and newsletter signups from the website will appear here.'));
      } else if (!items.length) {
        list.replaceChildren(h('li', { class: 'empty' }, 'No submissions match these filters.'));
      } else {
        list.replaceChildren(...items.map(s => h('li', {},
          h('button', { type: 'button', class: 'row' + (s.status === 'new' ? ' is-new' : ''), 'aria-current': String(selected && selected.id === s.id), onclick: () => { selected = s; draw(); } },
            h('span', { class: 'dot', 'aria-hidden': 'true' }),
            h('b', {}, title(s)),
            h('time', { datetime: s.created }, fmtDate(s.created)),
            h('span', { class: 'meta' }, `${KIND[s.type]} · ${meta(s)}`),
            h('span', { class: 'badge ' + s.status }, s.status)))));
      }
      drawDetail();
    }

    function drawDetail() {
      layout.classList.toggle('has-detail', !!selected);   // list is full width until a submission is opened
      if (!selected) { detail.hidden = true; return; }
      const s = selected;
      detail.hidden = false;
      const rows = s.type === 'brief' ? [
        ['Email', s.email], ['Company', s.company], ['Phone', s.phone], ['Services', s.services.join(', ')],
        ['Starting from', s.stage], ['Budget', BUDGET[s.budget]], ['Timing', s.timing], ['Heard via', s.source],
        ['NDA', s.nda ? 'Requested' : 'No'], ['Message', s.message]]
        : s.type === 'call' ? [['Email', s.email], ['When', s.when], ['Topic', s.topic]]
        : [['Email', s.email]];
      const statusSel = h('select', { id: 'dStatus' }, STATUSES.map(v => h('option', { value: v, selected: v === s.status }, v[0].toUpperCase() + v.slice(1))));
      const note = h('textarea', { id: 'dNote', placeholder: 'Internal notes: who is following up, next steps…' });
      note.value = s.note || '';
      const save = async () => {
        try {
          const upd = await api('PATCH', '/api/submissions/' + s.id, { status: statusSel.value, note: note.value });
          Object.assign(s, upd);
          toast('Updated');
          refreshCount(subs);
          draw();
        } catch (err) { toast(err.message); }
      };
      const del = async () => {
        if (!confirm(`Delete this ${KIND[s.type].toLowerCase()} from ${title(s)}? This cannot be undone.`)) return;
        try {
          await api('DELETE', '/api/submissions/' + s.id);
          subs = subs.filter(x => x.id !== s.id);
          selected = null;
          toast('Deleted');
          refreshCount(subs);
          draw();
        } catch (err) { toast(err.message); }
      };
      const close = icon('x', 'Close');
      close.classList.add('close-detail');
      close.addEventListener('click', () => { selected = null; draw(); });
      detail.replaceChildren(
        h('div', { class: 'detail-head' },
          h('div', {}, h('h2', {}, title(s)), h('p', { class: 'sub' }, `${KIND[s.type]} · ${s.ref} · received ${fmtDate(s.created)}`)),
          close),
        h('dl', { class: 'kv' }, rows.filter(([, v]) => v).map(([k, v]) => [h('dt', {}, k), h('dd', {}, v)])),
        h('div', { class: 'field' }, h('label', { for: 'dStatus' }, 'Status'), statusSel),
        h('div', { class: 'field' }, h('label', { for: 'dNote' }, 'Notes'), note),
        h('div', { class: 'detail-actions' },
          h('button', { type: 'button', class: 'btn btn-primary', onclick: save }, 'Save'),
          h('a', { class: 'btn btn-outline', href: `mailto:${encodeURIComponent(s.email)}?subject=${encodeURIComponent('Your Corbel enquiry ' + s.ref)}` }, 'Reply by email'),
          h('button', { type: 'button', class: 'btn btn-danger', onclick: del }, 'Delete')));
    }

    draw();
    refreshCount(subs);
  }

  function exportCsv(rows) {
    if (!rows.length) return toast('Nothing to export');
    const cols = ['created', 'type', 'ref', 'status', 'name', 'email', 'company', 'phone', 'services', 'stage', 'budget', 'timing', 'when', 'topic', 'source', 'nda', 'message', 'note'];
    const cell = v => {
      let s = Array.isArray(v) ? v.join('; ') : v == null ? '' : String(v);
      if (/^[=+\-@]/.test(s)) s = "'" + s;              // stop spreadsheets running it as a formula
      return '"' + s.replace(/"/g, '""') + '"';
    };
    const csv = [cols.join(','), ...rows.map(r => cols.map(c => cell(r[c])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const a = h('a', { href: url, download: `corbel-submissions-${new Date().toISOString().slice(0, 10)}.csv` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  /* =====================================================================
     Generic form fields
     ===================================================================== */
  let uid = 0;
  function fields(specs, obj, onChange) {
    return h('div', { class: 'form-grid' }, specs.map(f => field(f, obj, onChange)));
  }

  function field(f, obj, onChange) {
    const id = 'f' + (++uid);
    const type = f.type || 'text';
    const hint = f.hint ? h('span', { class: 'hint' }, f.hint) : null;
    const wrap = (control, labelFor = id) => h('div', { class: 'field' + (f.wide ? ' wide' : '') },
      h('label', { for: labelFor }, f.label), control, hint);
    const set = v => { obj[f.key] = v; onChange(); };

    if (type === 'text' || type === 'number' || type === 'slug') {
      const input = h('input', { id, type: type === 'number' ? 'number' : 'text', value: obj[f.key] ?? '', readOnly: !!f.readonly, required: !!f.required });
      input.addEventListener('input', () => {
        if (type === 'slug') {
          const v = input.value.toLowerCase().replace(/[^a-z0-9-]/g, '-');
          if (v !== input.value) input.value = v;
          set(v);
        } else set(type === 'number' ? (input.value === '' ? '' : +input.value) : input.value);
      });
      return wrap(input);
    }
    if (type === 'textarea') {
      const ta = h('textarea', { id, rows: f.rows || 4, readOnly: !!f.readonly });
      ta.value = obj[f.key] ?? '';
      ta.addEventListener('input', () => set(ta.value));
      return wrap(ta);
    }
    if (type === 'select') {
      const sel = h('select', { id }, f.options().map(o => h('option', { value: o.value, selected: o.value === obj[f.key] }, o.label)));
      sel.addEventListener('change', () => set(sel.value));
      return wrap(sel);
    }
    if (type === 'tags' || type === 'lines' || type === 'paras') {
      const sep = { tags: ', ', lines: '\n', paras: '\n\n' }[type];
      const split = { tags: /,/, lines: /\n/, paras: /\n\s*\n/ }[type];
      const el = type === 'tags' ? h('input', { id, type: 'text' }) : h('textarea', { id, rows: f.rows || 5 });
      el.value = (obj[f.key] || []).join(sep);
      el.addEventListener('input', () => set(el.value.split(split).map(s => s.trim()).filter(Boolean)));
      return wrap(el);
    }
    if (type === 'checkbox') {
      const cb = h('input', { id, type: 'checkbox', checked: obj[f.key] !== false });
      cb.addEventListener('change', () => set(cb.checked));
      return h('div', { class: 'field' + (f.wide ? ' wide' : '') }, h('label', { class: 'inline', for: id }, cb, f.label), hint);
    }
    if (type === 'checks') {
      const current = new Set(obj[f.key] || []);
      return h('fieldset', { class: 'sub' + (f.wide ? ' wide' : '') }, h('legend', {}, f.label),
        h('div', { class: 'check-row' }, f.options().map(o => {
          const cb = h('input', { type: 'checkbox', checked: current.has(o.value) });
          cb.addEventListener('change', () => {
            cb.checked ? current.add(o.value) : current.delete(o.value);
            set(f.options().map(x => x.value).filter(v => current.has(v)));
          });
          return h('label', {}, cb, o.label);
        })), hint);
    }
    if (type === 'group') {
      // Optional object, e.g. a testimonial. Stored as null when every field is empty.
      const temp = { ...(obj[f.key] || {}) };
      const sync = () => { obj[f.key] = f.fields.some(sf => String(temp[sf.key] || '').trim()) ? { ...temp } : null; onChange(); };
      return h('fieldset', { class: 'sub wide' }, h('legend', {}, f.label), hint, fields(f.fields, temp, sync));
    }
    if (type === 'list' || type === 'pairs') {
      // Repeating rows. "pairs" stores [value, label] arrays, "list" stores objects.
      const box = h('fieldset', { class: 'sub wide' });
      const draw = () => {
        const arr = obj[f.key] = obj[f.key] || [];
        box.replaceChildren(h('legend', {}, f.label), ...(hint ? [hint] : []),
          ...arr.map((item, i) => {
            let inner;
            if (type === 'pairs') {
              const proxy = { a: item[0], b: item[1] };
              inner = fields([{ key: 'a', label: f.labels[0] }, { key: 'b', label: f.labels[1] }], proxy, () => { arr[i] = [proxy.a, proxy.b]; onChange(); });
            } else inner = fields(f.fields, item, onChange);
            const rm = icon('x', 'Remove');
            rm.classList.add('remove');
            rm.addEventListener('click', () => { arr.splice(i, 1); onChange(); draw(); });
            return h('div', { class: 'repeat' }, inner, rm);
          }),
          h('button', { type: 'button', class: 'btn btn-outline btn-sm add-row', onclick: () => {
            arr.push(type === 'pairs' ? ['', ''] : Object.fromEntries(f.fields.map(sf => [sf.key, ''])));
            onChange(); draw();
          } }, '+ ' + (f.addLabel || 'Add')));
      };
      draw();
      return box;
    }
    throw new Error('Unknown field type ' + type);
  }

  /* =====================================================================
     Collection editor: list of items on the left, form on the right
     ===================================================================== */
  async function collection(root, cfg) {
    let saved = await api('GET', '/api/content/' + cfg.name);
    let work = structuredClone(saved);
    let index = 0;
    const isDirty = () => JSON.stringify(work) !== JSON.stringify(saved);
    dirtyCheck = isDirty;

    const listBox = h('nav', { class: 'item-list panel-box', 'aria-label': cfg.title });
    const formBox = h('div', { class: 'form-card panel-box' });
    const state = h('span', { class: 'state' });
    const saveBtn = h('button', { type: 'button', class: 'btn btn-accent', onclick: save }, 'Save and publish');
    const discardBtn = h('button', { type: 'button', class: 'btn btn-outline', onclick: () => {
      if (!confirm('Discard all unsaved changes?')) return;
      work = structuredClone(saved); index = Math.min(index, work.length - 1); drawList(); drawForm(); changed();
    } }, 'Discard');
    const bar = h('div', { class: 'savebar' }, state, h('div', { class: 'actions' }, discardBtn, saveBtn));

    root.replaceChildren(h('div', { class: 'editor' }, listBox, h('div', {}, formBox, bar)));

    let heading = null;
    function changed() {
      if (heading && work[index]) heading.textContent = cfg.label(work[index]) || 'Untitled';
      const d = isDirty();
      state.className = 'state' + (d ? ' dirty' : '');
      state.textContent = d ? 'Unsaved changes' : 'All changes published';
      saveBtn.disabled = discardBtn.disabled = !d;
      drawList();
    }

    function drawList() {
      listBox.replaceChildren(
        ...(cfg.blank ? [h('button', { type: 'button', class: 'btn btn-outline btn-sm add', onclick: () => {
          work.unshift(cfg.blank()); index = 0; drawForm(); changed();
        } }, '+ ' + cfg.addLabel)] : []),
        ...work.map((item, i) => h('button', { type: 'button', class: 'item', 'aria-current': String(i === index), onclick: () => { index = i; drawList(); drawForm(); } },
          h('b', {}, cfg.label(item) || 'Untitled'), h('small', {}, cfg.sub(item) || ''))));
    }

    function drawForm() {
      const item = work[index];
      if (!item) { formBox.replaceChildren(h('p', { class: 'empty' }, 'Nothing here yet.')); return; }
      const tools = h('div', { class: 'detail-actions' });
      if (cfg.blank) {
        const up = icon('up', 'Move up'), down = icon('down', 'Move down');
        up.disabled = index === 0; down.disabled = index === work.length - 1;
        const move = d => { const [it] = work.splice(index, 1); index += d; work.splice(index, 0, it); drawForm(); changed(); };
        up.addEventListener('click', () => move(-1));
        down.addEventListener('click', () => move(1));
        tools.append(up, down, h('button', { type: 'button', class: 'btn btn-danger btn-sm', onclick: () => {
          if (!confirm(`Remove "${cfg.label(item) || 'this item'}"? It is deleted from the site when you save.`)) return;
          work.splice(index, 1); index = Math.max(0, index - 1); drawForm(); changed();
        } }, 'Remove'));
      }
      if (cfg.preview) tools.append(h('a', { class: 'btn btn-outline btn-sm', href: cfg.preview(item), target: '_blank', rel: 'noopener' }, 'View on site ↗'));
      heading = h('h2', {}, cfg.label(item) || 'Untitled');
      formBox.replaceChildren(
        h('div', { class: 'form-top' }, heading, tools),
        fields(cfg.fields, item, changed));
    }

    async function save() {
      for (const [i, item] of work.entries()) {
        const missing = cfg.fields.find(f => f.required && !String(item[f.key] ?? '').trim());
        if (missing) { index = i; drawList(); drawForm(); return toast(`"${missing.label}" is required.`); }
      }
      saveBtn.disabled = true;
      setBuild(null, true);
      try {
        const res = await api('PUT', '/api/content/' + cfg.name, work);
        saved = structuredClone(work);
        afterSave(res);
      } catch (err) { toast(err.message); setBuild(); }
      changed();
    }

    drawList(); drawForm(); changed();
  }

  /* ---------- Content definitions ---------- */
  let serviceList = [];
  const serviceOptions = () => serviceList.map(s => ({ value: s.id, label: s.name }));

  async function viewCases(root) {
    serviceList = await api('GET', '/api/content/services');
    await collection(root, {
      name: 'cases', title: 'Case studies', addLabel: 'New case study',
      label: c => c.client, sub: c => c.title,
      preview: c => '../work.html#' + c.id,
      blank: () => ({ id: '', client: '', svc: serviceList[0].id, ind: '', year: new Date().getFullYear(), title: '', metric: '', mlabel: '', problem: '', approach: '', stats: [['', ''], ['', ''], ['', '']], stack: [], quote: null }),
      fields: [
        { key: 'client', label: 'Client', required: true },
        { key: 'id', label: 'URL ID', type: 'slug', required: true, hint: 'Lowercase, used in links such as work.html#harbourline.' },
        { key: 'svc', label: 'Service', type: 'select', options: serviceOptions, required: true },
        { key: 'ind', label: 'Industry', required: true, hint: 'Used for the industry filter, e.g. Logistics.' },
        { key: 'year', label: 'Year', type: 'number' },
        { key: 'title', label: 'Title', required: true, wide: true },
        { key: 'metric', label: 'Headline number', required: true, hint: 'Shown large on the card, e.g. 38%.' },
        { key: 'mlabel', label: 'Number caption', required: true, hint: 'e.g. less time to dispatch a truck' },
        { key: 'problem', label: 'The problem', type: 'textarea', wide: true },
        { key: 'approach', label: 'What we built', type: 'textarea', wide: true },
        { key: 'stats', label: 'Key results', type: 'pairs', labels: ['Value', 'Label'], addLabel: 'Add result', hint: 'Three work best.' },
        { key: 'stack', label: 'Built with', type: 'tags', wide: true, hint: 'Separate with commas.' },
        { key: 'quote', label: 'Client quote (optional)', type: 'group', hint: 'Quotes also appear in the home page testimonials.', fields: [
          { key: 'text', label: 'Quote', type: 'textarea', wide: true, rows: 3 },
          { key: 'who', label: 'Name' }, { key: 'role', label: 'Role and company' }] }
      ]
    });
  }

  async function viewRoles(root) {
    await collection(root, {
      name: 'roles', title: 'Open roles', addLabel: 'New role',
      label: r => r.title, sub: r => [r.open === false ? 'Hidden' : '', r.team, r.location].filter(Boolean).join(' · '),
      preview: () => '../careers.html#roles',
      blank: () => ({ title: '', team: '', location: '', type: 'Full time', salary: '', description: [], open: true }),
      fields: [
        { key: 'title', label: 'Job title', required: true },
        { key: 'team', label: 'Team', required: true },
        { key: 'location', label: 'Location', required: true },
        { key: 'type', label: 'Type', hint: 'e.g. Full time, Contract' },
        { key: 'salary', label: 'Salary range', wide: true, hint: 'Published on the site, e.g. KES 300k–450k / month.' },
        { key: 'description', label: 'Description', type: 'paras', rows: 8, wide: true, hint: 'Leave a blank line between paragraphs.' },
        { key: 'open', label: 'Show this role on the careers page', type: 'checkbox', wide: true }
      ]
    });
  }

  start().catch(() => showLogin());
})();
